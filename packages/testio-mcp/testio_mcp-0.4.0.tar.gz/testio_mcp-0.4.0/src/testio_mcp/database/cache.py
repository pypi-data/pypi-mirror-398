"""
Persistent SQLite-based cache with incremental sync support.

This module provides a persistent cache implementation using SQLite with:
- Incremental sync algorithm (stops at first known test ID + 1 page)
- Multi-tenant design (customer_id isolation)
- WAL mode for concurrent reads during background writes
- Async operations via aiosqlite
- Query interface with filtering and pagination

**Performance:** ~10ms queries at our scale, imperceptible to users.
**Simplicity:** No TTL management, no memory overhead, no stampede protection needed.

Reference: STORY-021 (Local Data Store with Incremental Sync), AC5
"""

import asyncio
import json
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil
from filelock import FileLock, Timeout
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import select

from testio_mcp.client import TestIOClient
from testio_mcp.config import Settings
from testio_mcp.models.orm.product import Product
from testio_mcp.models.orm.sync_event import SyncEvent
from testio_mcp.models.orm.sync_metadata import SyncMetadata
from testio_mcp.repositories.test_repository import TestRepository

logger = logging.getLogger(__name__)

# STORY-034B: Removed aiosqlite import - all operations now use AsyncEngine and AsyncSession


@contextmanager
def suppress_httpx_logs() -> Iterator[None]:
    """Temporarily suppress httpx INFO logs during bulk operations.

    Use this context manager during refresh operations to avoid flooding
    logs with individual HTTP request lines. Summary statistics are shown
    instead after the operation completes.

    Example:
        with suppress_httpx_logs():
            # Perform bulk refresh - no individual request logs
            result = await cache.refresh_active_tests(product_id)
        # Summary shown here
    """
    httpx_logger = logging.getLogger("httpx")
    original_level = httpx_logger.level

    try:
        # Suppress httpx logs (only show WARNING and above)
        httpx_logger.setLevel(logging.WARNING)
        yield
    finally:
        # Restore original level
        httpx_logger.setLevel(original_level)


class PersistentCache:
    """SQLite-based persistent cache with ORM data access layer.

    Performance: ~10ms queries at our scale, imperceptible to users.

    Architecture:
    - SQLite: Single source of truth for all data (products, tests, bugs, sync events)
    - ORM: SQLModel/SQLAlchemy for type-safe data access (STORY-034B)
    - Repositories: Clean data access layer (no caching logic)
    - Background sync: Keeps SQLite fresh (incremental sync every 5 minutes)

    MVP: Uses self.customer_id for all DB operations (single customer).
    Future (STORY-010): Will accept customer_id parameter for multi-customer support.

    Attributes:
        db_path: Path to SQLite database file
        engine: AsyncEngine for database operations (STORY-034B)
        async_session_maker: Session factory for creating AsyncSession instances
        client: TestIO API client for fetching data
        customer_id: Stable customer identifier (from TestIO/Cirro system)
        customer_name: Optional customer name for display purposes
        repo: TestRepository for test/product/bug data access

    Note (STORY-023c):
        In-memory cache removed. All data access now goes through SQLite via repositories.
        Services use repositories directly instead of cache.get/set pattern.

    Note (STORY-034B):
        Removed aiosqlite.Connection - all operations now use AsyncEngine and AsyncSession.
        Sync events and metadata queries converted to ORM patterns.
    """

    # File lock configuration (STORY-021e)
    LOCK_FILE = Path.home() / ".testio-mcp" / "sync.lock"

    def __init__(
        self,
        db_path: str,
        client: TestIOClient,
        customer_id: int,
        customer_name: str | None = None,
    ) -> None:
        """Initialize persistent cache.

        Args:
            db_path: Path to SQLite database (e.g., "~/.testio-mcp/cache.db")
            client: TestIO API client for fetching data
            customer_id: Stable customer identifier from TestIO/Cirro system
            customer_name: Optional customer name for display purposes

        STORY-034B: Removed db: aiosqlite.Connection attribute.
        """
        self.db_path = Path(db_path).expanduser()
        self.client = client
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.repo: TestRepository | None = None

        # ORM infrastructure (STORY-030/034B: ORM Infrastructure Setup)
        # AsyncEngine and session factory for SQLModel/SQLAlchemy operations
        self.engine: AsyncEngine | None = None
        self.async_session_maker: Any = None  # Type: async_sessionmaker[AsyncSession]

        # Per-entity refresh locks (STORY-046, AC6)
        # Prevents duplicate API calls when concurrent requests target same entity
        # Key: (customer_id, entity_type, entity_id)
        # Value: asyncio.Lock for that specific entity
        self._refresh_locks: dict[tuple[int, str, int], asyncio.Lock] = {}

        # DB write semaphore (STORY-062 follow-up)
        # Limits concurrent DB writes to prevent "database is locked" errors
        # SQLite serializes writes internally, so this primarily limits
        # memory/connection pressure from queued sessions.
        # Configurable via MAX_CONCURRENT_DB_WRITES (default: 1 for SQLite)
        from testio_mcp.config import settings

        self._write_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DB_WRITES)
        logger.info(f"Created DB write semaphore with limit: {settings.MAX_CONCURRENT_DB_WRITES}")

    @property
    def _engine(self) -> AsyncEngine:
        """Get database engine (raises if not initialized).

        Returns:
            Active AsyncEngine instance

        Raises:
            AssertionError: If engine not initialized (call initialize() first)

        STORY-034B: Replaced _db property (aiosqlite.Connection) with _engine (AsyncEngine).
        """
        assert self.engine is not None, "Engine not initialized. Call initialize() first."
        return self.engine

    @property
    def _repo(self) -> TestRepository:
        """Get repository (raises if not initialized).

        Returns:
            Active test repository

        Raises:
            AssertionError: If repository not initialized (call initialize() first)
        """
        assert self.repo is not None, "Repository not initialized. Call initialize() first."
        return self.repo

    def get_refresh_lock(self, entity_type: str, entity_id: int) -> asyncio.Lock:
        """Get or create a lock for a specific entity (STORY-046, AC6).

        Uses setdefault() to avoid race condition during lock creation.
        Locks persist for reuse across requests (no cleanup needed per architect review).

        Args:
            entity_type: Type of entity being refreshed ('bug', 'test', 'feature')
            entity_id: ID of the entity (test_id, feature_id, etc.)

        Returns:
            asyncio.Lock for the specified entity

        Example:
            lock = cache.get_refresh_lock("bug", test_id=123)
            async with lock:
                # Refresh bugs for test 123
                # Only one request can refresh at a time
        """
        key = (self.customer_id, entity_type, entity_id)
        return self._refresh_locks.setdefault(key, asyncio.Lock())

    def _acquire_sync_lock(self) -> FileLock:
        """Acquire cross-process sync lock with stale detection (STORY-021e).

        Returns:
            Acquired file lock

        Raises:
            RuntimeError: If lock is held by another active process
        """
        # Ensure directory exists
        self.LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

        lock = FileLock(self.LOCK_FILE, timeout=1)  # Non-blocking check

        try:
            lock.acquire(timeout=1)
            # Write current PID to lock file for stale detection
            with open(self.LOCK_FILE, "w") as f:
                f.write(str(os.getpid()))
            return lock
        except Timeout:
            # Lock exists - check if stale
            if self._is_stale_lock(self.LOCK_FILE):
                logger.warning("Removing stale lock from crashed process")
                self.LOCK_FILE.unlink()
                return self._acquire_sync_lock()  # Retry
            else:
                raise RuntimeError("⚠️ Sync in progress. Retry in a few minutes.") from None

    def _is_stale_lock(self, lock_file: Path) -> bool:
        """Check if lock holder process is still alive (STORY-021e).

        Args:
            lock_file: Path to lock file containing PID

        Returns:
            True if lock is stale (process dead), False if process alive
        """
        if not lock_file.exists():
            return False

        try:
            with open(lock_file) as f:
                pid = int(f.read().strip())

            # Check if process exists
            return not psutil.pid_exists(pid)
        except (ValueError, FileNotFoundError):
            # Invalid PID or file deleted - treat as stale
            return True

    async def initialize(self) -> None:
        """Initialize SQLite database with ORM infrastructure.

        Creates database directory if missing, establishes AsyncEngine,
        enables WAL mode for concurrent reads, and initializes repository.
        Logs database statistics on startup.

        STORY-034B: Removed aiosqlite.Connection - all operations now use AsyncEngine.
        Schema initialization handled by Alembic migrations in server.py.

        Reference: STORY-021 AC8 (Database Maintenance), STORY-030 AC3, STORY-034B AC2
        """
        from testio_mcp.database.engine import (
            create_async_engine_for_sqlite,
            create_session_factory,
        )
        from testio_mcp.database.utils import (
            configure_wal_mode,
            vacuum_database,
        )

        # Create parent directory if missing
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # STORY-034B: Create AsyncEngine and session factory for ORM operations
        # No more aiosqlite.connect() - AsyncEngine handles all database access
        logger.debug(f"Creating AsyncEngine for database: {self.db_path}")
        self.engine = create_async_engine_for_sqlite(self.db_path)
        self.async_session_maker = create_session_factory(self.engine)
        logger.debug("AsyncEngine and session factory created successfully")

        # Configure WAL mode (STORY-034B: now uses AsyncEngine instead of aiosqlite)
        await configure_wal_mode(self._engine)

        # STORY-034A: Schema initialization now handled by Alembic migrations in server.py
        # No need for manual schema creation

        # Compact database on startup (AC8)
        # STORY-034B: now uses AsyncEngine instead of aiosqlite
        await vacuum_database(self._engine)

        # Initialize repository with AsyncSession for ORM operations (STORY-032B/034B)
        # Note: Cache manages a long-lived session for its repository
        # Services will create their own short-lived sessions
        self._cache_session = self.async_session_maker()

        # Create UserRepository for user extraction during sync (STORY-036)
        from testio_mcp.repositories.user_repository import UserRepository

        self.user_repo = UserRepository(
            session=self._cache_session, client=self.client, customer_id=self.customer_id
        )

        self.repo = TestRepository(
            session=self._cache_session,
            client=self.client,
            customer_id=self.customer_id,
            user_repo=self.user_repo,
        )

        # Log database statistics on startup (AC8)
        try:
            db_size_mb = await self.get_db_size_mb()
            test_count = await self.count_tests()
            product_count = await self.count_products()
            bug_count = await self.count_bugs()
            feature_count = await self.count_features()
            test_feature_count = await self.count_test_features()
            user_count = await self.count_users()

            logger.info(
                f"Initialized persistent cache at {self.db_path} for customer_id={self.customer_id}"
            )
            logger.info(f"  Database size: {db_size_mb}MB")
            logger.info(
                f"  Entity counts: Products={product_count} | Tests={test_count} | "
                f"Bugs={bug_count} | Features={feature_count} | "
                f"TestFeatures={test_feature_count} | Users={user_count}"
            )
        except Exception as e:
            logger.warning(f"Could not collect DB stats on startup: {e}")

        # CRITICAL: Rollback the implicit transaction started by SELECT queries above
        # to allow other sessions to be created without blocking (STORY-034B)
        # This prevents database locks during startup when should_run_initial_sync()
        # tries to create its own session
        await self._cache_session.rollback()

    async def close(self) -> None:
        """Close database connection, session, and dispose of AsyncEngine.

        STORY-030: Also disposes of AsyncEngine to cleanly release resources.
        STORY-032B: Also closes AsyncSession for TestRepository.

        CRITICAL: Commit any pending transactions before closing to prevent
        database locks and connection pool hangs (STORY-034A bug fix).
        """
        # Close AsyncSession for repository (STORY-032B)
        # IMPORTANT: Commit before closing to prevent database locks
        if hasattr(self, "_cache_session") and self._cache_session:
            try:
                # Commit any pending transactions to prevent locks
                await self._cache_session.commit()
            except Exception as e:
                # Rollback on error to clean up transaction state
                logger.warning(f"Session commit failed during close, rolling back: {e}")
                await self._cache_session.rollback()
            finally:
                # Always close session even if commit/rollback fails
                await self._cache_session.close()
                logger.debug("Closed cache AsyncSession")

        # STORY-034B: Dispose AsyncEngine to release connection pool
        # No more aiosqlite connection to close
        if self.engine:
            await self.engine.dispose()
            logger.info(f"Closed persistent cache at {self.db_path} (disposed AsyncEngine)")

    async def _get_sync_metadata(self, key: str) -> str | None:
        """Get metadata value from sync_metadata table (ORM helper).

        Args:
            key: Metadata key to retrieve

        Returns:
            Metadata value as string, or None if not found

        STORY-034B: Helper method for sync_metadata queries using AsyncSession.
        """
        from sqlmodel import col

        async with self.async_session_maker() as session:
            result = await session.exec(select(SyncMetadata).where(col(SyncMetadata.key) == key))
            metadata = result.first()
            return metadata.value if metadata else None

    async def _set_sync_metadata(self, key: str, value: str) -> None:
        """Set metadata value in sync_metadata table (ORM helper).

        Args:
            key: Metadata key
            value: Metadata value (typically JSON string)

        STORY-034B: Helper method for sync_metadata updates using AsyncSession.
        """
        async with self.async_session_maker() as session:
            # Use merge to INSERT OR REPLACE
            metadata = SyncMetadata(key=key, value=value)
            await session.merge(metadata)
            await session.commit()

    # Public metadata accessors (STORY-051 AC4)

    async def get_metadata_value(self, key: str) -> str | None:
        """Get metadata value from sync_metadata table.

        Args:
            key: Metadata key to retrieve

        Returns:
            Metadata value as string, or None if not found

        Example:
            >>> last_sync = await cache.get_metadata_value("last_sync_completed")
            >>> if last_sync:
            ...     timestamp = datetime.fromisoformat(last_sync)

        STORY-051: Public accessor for last_sync_completed timestamp.
        """
        return await self._get_sync_metadata(key)

    async def set_metadata_value(self, key: str, value: str) -> None:
        """Set metadata value in sync_metadata table.

        Args:
            key: Metadata key
            value: Metadata value (typically ISO 8601 string)

        Example:
            >>> from datetime import UTC, datetime
            >>> await cache.set_metadata_value(
            ...     "last_sync_completed",
            ...     datetime.now(UTC).isoformat()
            ... )

        STORY-051: Public accessor for last_sync_completed timestamp.
        """
        await self._set_sync_metadata(key, value)

    def _make_cache_key(self, *parts: Any) -> str:
        """Create cache key from parts (for compatibility with existing patterns).

        Args:
            *parts: Key components (e.g., "test", 123, "status")

        Returns:
            Cache key string (e.g., "test:123:status")
        """
        return ":".join(str(p) for p in parts)

    def _is_features_stale(self, product: Product | None, settings: Settings) -> bool:
        """Check if product features are stale and need refresh.

        STORY-062: Simplified - uses last_synced instead of features_synced_at.

        Args:
            product: Product ORM instance (or None if not found)
            settings: Settings instance with CACHE_TTL_SECONDS

        Returns:
            True if features should be refreshed (stale or never synced)
            False if features are fresh (< TTL)
        """
        from datetime import UTC, datetime

        if not product:
            return True  # Product not found - needs sync

        if not product.last_synced:
            return True  # Never synced - needs sync

        now = datetime.now(UTC)

        # Ensure last_synced is timezone-aware (SQLite stores as naive)
        synced_at = product.last_synced
        if synced_at.tzinfo is None:
            synced_at = synced_at.replace(tzinfo=UTC)

        seconds_since_sync = (now - synced_at).total_seconds()

        return seconds_since_sync >= settings.CACHE_TTL_SECONDS

    async def get_db_size_mb(self) -> float:
        """Get database file size in megabytes.

        Returns:
            Database file size in MB
        """
        if not self.db_path.exists():
            return 0.0
        size_bytes = self.db_path.stat().st_size
        return round(size_bytes / (1024 * 1024), 2)

    async def count_tests(self) -> int:
        """Count total tests in database for current customer.

        Returns:
            Total number of tests
        """
        if not self.repo:
            return 0
        return await self._repo.count_tests()

    async def count_products(self) -> int:
        """Count total products in database for current customer.

        Returns:
            Total number of products
        """
        if not self._cache_session:
            return 0

        from testio_mcp.repositories.product_repository import ProductRepository

        # Use cache's session to avoid lock during initialization
        repo = ProductRepository(self._cache_session, self.client, self.customer_id)
        return await repo.count_products()

    async def count_bugs(self) -> int:
        """Count total bugs in database for current customer.

        Returns:
            Total number of bugs
        """
        if not self._cache_session:
            return 0

        from sqlmodel import func, select

        from testio_mcp.models.orm.bug import Bug

        result = await self._cache_session.exec(
            select(func.count(Bug.id)).where(Bug.customer_id == self.customer_id)  # type: ignore[arg-type]
        )
        return result.one()  # type: ignore[no-any-return]

    async def count_features(self) -> int:
        """Count total features in database for current customer.

        Features don't have customer_id directly, but belong to products which do.
        Count all features for products owned by this customer.

        Returns:
            Total number of features
        """
        if not self._cache_session:
            return 0

        from sqlmodel import func, select

        from testio_mcp.models.orm.feature import Feature
        from testio_mcp.models.orm.product import Product

        result = await self._cache_session.exec(
            select(func.count(Feature.id))  # type: ignore[arg-type]
            .join(Product, Feature.product_id == Product.id)  # type: ignore[arg-type]
            .where(Product.customer_id == self.customer_id)
        )
        return result.one()  # type: ignore[no-any-return]

    async def count_test_features(self) -> int:
        """Count total test-feature associations in database for current customer.

        Returns:
            Total number of test-feature links
        """
        if not self._cache_session:
            return 0

        from sqlmodel import func, select

        from testio_mcp.models.orm.test_feature import TestFeature

        result = await self._cache_session.exec(
            select(func.count(TestFeature.id)).where(  # type: ignore[arg-type]
                TestFeature.customer_id == self.customer_id
            )
        )
        return result.one()  # type: ignore[no-any-return]

    async def count_users(self) -> int:
        """Count total users in database for current customer.

        Returns:
            Total number of users (testers + customers)
        """
        if not self._cache_session:
            return 0

        from sqlmodel import func, select

        from testio_mcp.models.orm.user import User

        result = await self._cache_session.exec(
            select(func.count(User.id)).where(User.customer_id == self.customer_id)  # type: ignore[arg-type]
        )
        return result.one()  # type: ignore[no-any-return]

    async def get_oldest_test_date(self) -> str | None:
        """Get oldest test end date for current customer.

        Returns:
            ISO 8601 timestamp of oldest test end date, or None if no tests
        """
        if not self.repo:
            return None
        return await self._repo.get_oldest_test_date()

    async def get_newest_test_date(self) -> str | None:
        """Get newest test end date for current customer.

        Returns:
            ISO 8601 timestamp of newest test end date, or None if no tests
        """
        if not self.repo:
            return None
        return await self._repo.get_newest_test_date()

    async def query_tests(
        self,
        product_id: int,
        statuses: list[str] | None = None,
        start_date: Any | None = None,
        end_date: Any | None = None,
        date_field: str = "start_at",
        page: int = 1,
        per_page: int = 100,
    ) -> list[dict[str, Any]]:
        """Query tests from local database with filtering and pagination (AC3).

        MVP: Uses self.customer_id internally for WHERE clause.
        Future (STORY-010): Will accept customer_id parameter.

        Args:
            product_id: Product identifier
            statuses: Optional list of status values to filter by
            start_date: Optional start date for date range filter (datetime or str)
            end_date: Optional end date for date range filter (datetime or str)
            date_field: Field to use for date filtering (start_at, end_at)
            page: Page number (1-indexed)
            per_page: Number of results per page

        Returns:
            List of test dictionaries (deserialized from JSON data column)
        """
        if not self.repo:
            return []
        return await self._repo.query_tests(
            product_id=product_id,
            statuses=statuses,
            start_date=start_date,
            end_date=end_date,
            date_field=date_field,
            page=page,
            per_page=per_page,
        )

    async def clear_database(self) -> None:
        """Clear all data from database (for current customer only).

        Deletes all tests and products for current customer, then vacuums to reclaim space.
        """
        from testio_mcp.database.utils import vacuum_database

        if not self.repo:
            return

        await self._repo.delete_all_tests()

        from testio_mcp.repositories.product_repository import ProductRepository

        async with self.async_session_maker() as session:
            repo = ProductRepository(session, self.client, self.customer_id)
            await repo.delete_all_products()
        await vacuum_database(self._engine)

        logger.info(f"Cleared database for customer_id={self.customer_id}")

    async def delete_product_tests(self, product_id: int) -> None:
        """Delete all tests for a specific product.

        Args:
            product_id: Product identifier
        """
        if not self.repo:
            return

        await self._repo.delete_product_tests(product_id)

        logger.info(f"Deleted tests for product_id={product_id}, customer_id={self.customer_id}")

    async def get_synced_products_info(self) -> list[dict[str, Any]]:
        """Get information about synced products for current customer.

        Returns:
            List of product info dictionaries with id, name, last_synced, test_count
        """
        if not self.async_session_maker:
            return []

        from testio_mcp.repositories.product_repository import ProductRepository

        async with self.async_session_maker() as session:
            repo = ProductRepository(session, self.client, self.customer_id)
            return await repo.get_synced_products_info()

    async def get_product_info(self, product_id: int) -> dict[str, Any] | None:
        """Get product information from database.

        Args:
            product_id: Product identifier

        Returns:
            Product info dictionary with id, name, type, or None if not found
        """
        from testio_mcp.repositories.product_repository import ProductRepository

        async with self.async_session_maker() as session:
            repo = ProductRepository(session, self.client, self.customer_id)
            return await repo.get_product_info(product_id)

    async def should_run_initial_sync(self, refresh_interval_seconds: int) -> bool:
        """Check if initial sync should run based on last sync time (STORY-046, AC3).

        Decision logic:
        - Circuit breaker: If 3+ sync failures in last 5 minutes, skip (restart loop protection)
        - Force sync: If TESTIO_FORCE_INITIAL_SYNC=true, always run sync
        - If database is empty (no products): Run sync (first run)
        - Check oldest product sync and oldest feature sync
        - If either is > refresh_interval ago: Run sync (data stale)
        - Otherwise: Skip sync (data fresh)

        AC3 (STORY-046): Removed mutable test staleness check. Test metadata refreshed
        on-demand via repository staleness checks when queried.

        Args:
            refresh_interval_seconds: Refresh interval from settings

        Returns:
            True if sync should run, False to skip
        """
        from datetime import datetime, timedelta

        from testio_mcp.config import Settings

        # Circuit breaker: Check recent failures (restart loop protection)
        recent_failures = await self.count_sync_failures_since(
            datetime.now(UTC) - timedelta(minutes=5)
        )

        if recent_failures >= 3:
            logger.error(
                "🛑 Circuit breaker: 3+ sync failures in last 5 minutes. "
                "Server may be in restart loop. Skipping initial sync. "
                "Check logs and fix issues before retrying."
            )
            return False

        # Force sync check (bypass staleness checks if flag is set)
        settings = Settings()
        if settings.TESTIO_FORCE_INITIAL_SYNC:
            logger.info("Force sync enabled (--force-sync flag), initial sync needed")
            return True

        # Check if database has any products
        product_count = await self.count_products()
        if product_count == 0:
            logger.info("Database empty (first run), initial sync needed")
            return True

        # Get products with last_synced timestamps
        products_info = await self.get_synced_products_info()
        if not products_info:
            logger.info("No synced products found, initial sync needed")
            return True

        now = datetime.now(UTC)

        # STORY-062: Check last_synced for background sync staleness
        # SyncService updates Product.last_synced after all phases complete.
        # This is the single timestamp that controls background sync freshness.
        oldest_sync: datetime | None = None
        for product in products_info:
            last_synced_str = product.get("last_synced")
            if not last_synced_str:
                # Product never synced - need initial sync
                logger.info(
                    f"Product {product['id']} has no last_synced timestamp, initial sync needed"
                )
                return True

            try:
                last_synced = datetime.fromisoformat(last_synced_str)
                # Ensure timezone-aware
                if last_synced.tzinfo is None:
                    last_synced = last_synced.replace(tzinfo=UTC)

                if oldest_sync is None or last_synced < oldest_sync:
                    oldest_sync = last_synced
            except ValueError as e:
                logger.warning(f"Failed to parse last_synced '{last_synced_str}': {e}")
                continue

        if oldest_sync is None:
            logger.info("No valid last_synced timestamps found, initial sync needed")
            return True

        # Check if data is stale based on last_synced
        time_since_sync = (now - oldest_sync).total_seconds()

        logger.info(
            f"Last sync {time_since_sync:.0f} seconds ago "
            f"(interval: {refresh_interval_seconds} seconds)"
        )

        return time_since_sync > refresh_interval_seconds

    async def get_problematic_tests(self, product_id: int | None = None) -> list[dict[str, Any]]:
        """Get tests that failed to sync due to API 500 errors.

        Args:
            product_id: Optional filter for specific product

        Returns:
            List of problematic test records with boundary information
        """
        if not self.repo:
            return []
        return await self._repo.get_problematic_tests(product_id)

    async def log_problematic_test(self, test_info: dict[str, Any]) -> None:
        """Append problematic test info to sync_metadata.

        Args:
            test_info: Test information dict with boundary data
        """
        if not self.repo:
            return
        await self._repo.log_problematic_test(test_info)

        # Format boundary information for logging
        boundary_before = (
            f"boundary_before=(id={test_info.get('boundary_before_id')}, "
            f"end_at={test_info.get('boundary_before_end_at')})"
        )

        # Include boundary_after if available
        boundary_after_id = test_info.get("boundary_after_id")
        if boundary_after_id:
            boundary_after = (
                f", boundary_after=(id={boundary_after_id}, "
                f"end_at={test_info.get('boundary_after_end_at')})"
            )
        else:
            boundary_after = ""

        logger.warning(
            f"Logged problematic test: product_id={test_info.get('product_id')}, "
            f"position_range={test_info.get('position_range')}, "
            f"recovery_attempts={test_info.get('recovery_attempts')}, "
            f"{boundary_before}{boundary_after}"
        )

    async def get_problematic_events(self, product_id: int | None = None) -> list[dict[str, Any]]:
        """Get all failed sync events with their mapped test IDs.

        Args:
            product_id: Filter by product, or None for all products

        Returns:
            List of event dicts with:
            - event_id: UUID of failed sync event
            - product_id: Product identifier
            - position_range: Page positions that failed
            - recovery_attempts: Number of retry attempts
            - boundary_before_id: Test ID before failed range
            - boundary_before_end_at: End timestamp of boundary test
            - mapped_test_ids: List of test IDs mapped to this event
        """
        if not self.repo:
            return []

        # Get failed events from problematic_tests
        events = await self._repo.get_problematic_tests(product_id)

        # Get test ID mappings from sync_metadata (STORY-034B: using ORM helper)
        mappings_json = await self._get_sync_metadata("problematic_test_mappings")
        mappings: dict[str, list[int]] = {}
        if mappings_json:
            mappings = json.loads(mappings_json)

        # Merge mapped test IDs into events
        for event in events:
            event_id = event.get("event_id", "")
            event["mapped_test_ids"] = mappings.get(event_id, [])

        return events

    async def map_test_ids_to_event(self, event_id: str, test_ids: list[int]) -> None:
        """Map test IDs to a specific failed sync event.

        Simple metadata write - no API calls, no validation.
        User decides which test IDs belong to which event.

        Args:
            event_id: UUID of failed sync event (from get_problematic_events)
            test_ids: One or more test IDs to map to this event

        Raises:
            ValueError: If event_id doesn't exist
        """
        if not self.repo:
            return

        # Validate event_id exists
        events = await self._repo.get_problematic_tests(product_id=None)
        event_ids = {e.get("event_id") for e in events}
        if event_id not in event_ids:
            raise ValueError(f"Event ID '{event_id}' not found in problematic tests")

        # Get existing mappings (STORY-034B: using ORM helper)
        mappings_json = await self._get_sync_metadata("problematic_test_mappings")
        mappings: dict[str, list[int]] = {}
        if mappings_json:
            mappings = json.loads(mappings_json)

        # Add new test IDs to event (append to existing if any)
        if event_id not in mappings:
            mappings[event_id] = []

        # Merge new test IDs (avoid duplicates)
        existing_ids = set(mappings[event_id])
        for test_id in test_ids:
            if test_id not in existing_ids:
                mappings[event_id].append(test_id)

        # Update metadata (STORY-034B: using ORM helper)
        await self._set_sync_metadata("problematic_test_mappings", json.dumps(mappings))

        logger.info(f"Mapped {len(test_ids)} test IDs to event {event_id}: {test_ids}")

    async def retry_problematic_tests(self, product_id: int) -> dict[str, Any]:
        """Retry fetching all mapped test IDs for a product.

        Fetches each test individually via GET /tests/{id}.
        Removes from event mapping on success, keeps on failure.

        Args:
            product_id: Product ID to retry

        Returns:
            Dict with tests_retried, tests_succeeded, tests_failed, errors
        """
        if not self.repo:
            return {
                "tests_retried": 0,
                "tests_succeeded": 0,
                "tests_failed": 0,
                "errors": [],
            }

        # Get all events for this product with their mapped test IDs
        events = await self.get_problematic_events(product_id=product_id)

        # Collect all mapped test IDs for this product
        test_ids_to_retry: list[int] = []
        for event in events:
            test_ids_to_retry.extend(event.get("mapped_test_ids", []))

        results: dict[str, Any] = {
            "tests_retried": len(test_ids_to_retry),
            "tests_succeeded": 0,
            "tests_failed": 0,
            "errors": [],
        }

        # Retry each test ID individually
        for test_id in test_ids_to_retry:
            try:
                # Fetch individual test from API
                test_data = await self.client.get(f"exploratory_tests/{test_id}")

                # Insert to database (INSERT OR REPLACE handles duplicates)
                await self._repo.insert_test(test_data, product_id)
                await self._repo.commit()

                # Remove from ALL event mappings on success
                await self._remove_test_id_from_mappings(test_id)
                results["tests_succeeded"] = results["tests_succeeded"] + 1

                logger.info(f"Successfully retried test_id={test_id}")

            except Exception as e:
                # Keep in mapping on failure
                results["tests_failed"] = results["tests_failed"] + 1
                error_msg = f"Test {test_id}: {type(e).__name__} - {str(e)}"
                results["errors"].append(error_msg)
                logger.warning(f"Failed to retry test_id={test_id}: {e}")

        return results

    async def _remove_test_id_from_mappings(self, test_id: int) -> None:
        """Remove a test ID from all event mappings after successful fetch.

        Args:
            test_id: Test ID to remove from mappings

        STORY-034B: Refactored to use ORM helpers instead of raw aiosqlite.
        """
        if not self.repo:
            return

        # Get existing mappings (STORY-034B: using ORM helper)
        mappings_json = await self._get_sync_metadata("problematic_test_mappings")
        if not mappings_json:
            return

        mappings: dict[str, list[int]] = json.loads(mappings_json)

        # Remove test_id from all events
        updated = False
        for _event_id, test_ids in mappings.items():
            if test_id in test_ids:
                test_ids.remove(test_id)
                updated = True

        # Remove events with empty test ID lists
        mappings = {k: v for k, v in mappings.items() if v}

        if updated:
            # Update metadata (STORY-034B: using ORM helper)
            await self._set_sync_metadata("problematic_test_mappings", json.dumps(mappings))

    async def clear_problematic_tests(self) -> dict[str, Any]:
        """Clear all problematic records (position ranges AND tracked test IDs).

        Returns:
            Dict with position_ranges_cleared and test_ids_cleared counts
        """
        if not self.repo:
            return {"position_ranges_cleared": 0, "test_ids_cleared": 0}

        # Get counts before clearing
        events = await self._repo.get_problematic_tests(product_id=None)
        position_ranges_cleared = len(events)

        # Get test ID mappings count (STORY-034B: using ORM helper)
        mappings_json = await self._get_sync_metadata("problematic_test_mappings")
        test_ids_cleared = 0
        if mappings_json:
            mappings: dict[str, list[int]] = json.loads(mappings_json)
            test_ids_cleared = sum(len(ids) for ids in mappings.values())

        # Clear both metadata keys (STORY-034B: using AsyncSession with delete() construct)
        from sqlalchemy import delete
        from sqlmodel import col

        async with self.async_session_maker() as session:
            await session.exec(
                delete(SyncMetadata).where(
                    col(SyncMetadata.key).in_(["problematic_tests", "problematic_test_mappings"])
                )
            )
            await session.commit()

        logger.info(
            f"Cleared {position_ranges_cleared} position ranges "
            f"and {test_ids_cleared} test ID mappings"
        )

        return {
            "position_ranges_cleared": position_ranges_cleared,
            "test_ids_cleared": test_ids_cleared,
        }

    # Sync event logging for observability and circuit breaker

    async def log_sync_event_start(self, event_type: str, trigger_source: str) -> int:
        """Create sync event record with status='running'.

        Args:
            event_type: Type of sync ('initial_sync' or 'background_refresh')
            trigger_source: What triggered the sync ('startup', 'background_task', 'cli_command')

        Returns:
            Event ID for updating later with complete/failed status

        STORY-034B: Refactored to use ORM (SyncEvent model) instead of raw aiosqlite.
        """
        if not self.repo:
            return -1

        now = datetime.now(UTC).isoformat()

        # Create new sync event (STORY-034B: using ORM)
        async with self.async_session_maker() as session:
            sync_event = SyncEvent(
                event_type=event_type,
                started_at=now,
                status="running",
                trigger_source=trigger_source,
            )
            session.add(sync_event)
            await session.commit()
            await session.refresh(sync_event)  # Get the auto-generated ID

            event_id = sync_event.id if sync_event.id else -1
            logger.debug(
                f"Sync event started: id={event_id}, type={event_type}, source={trigger_source}"
            )
            return event_id

    async def log_sync_event_complete(
        self,
        event_id: int,
        products_synced: int,
        tests_discovered: int,
        tests_refreshed: int,
        features_refreshed: int,  # NEW parameter (STORY-038)
        duration_seconds: float,
    ) -> None:
        """Update sync event with status='completed' and statistics.

        Args:
            event_id: Event ID from log_sync_event_start()
            products_synced: Number of products synced
            tests_discovered: Number of new tests discovered
            tests_refreshed: Number of tests refreshed
            features_refreshed: Number of features refreshed (STORY-038)
            duration_seconds: Time taken for sync

        STORY-034B: Refactored to use ORM (SyncEvent model) instead of raw aiosqlite.
        """
        if not self.repo or event_id < 0:
            return

        now = datetime.now(UTC).isoformat()

        # Update sync event (STORY-034B: using ORM)
        from sqlmodel import col

        async with self.async_session_maker() as session:
            result = await session.exec(select(SyncEvent).where(col(SyncEvent.id) == event_id))
            sync_event = result.first()
            if sync_event:
                sync_event.completed_at = now
                sync_event.status = "completed"
                sync_event.products_synced = products_synced
                sync_event.tests_discovered = tests_discovered
                sync_event.tests_refreshed = tests_refreshed
                sync_event.features_refreshed = features_refreshed  # NEW (STORY-038)
                sync_event.duration_seconds = duration_seconds
                await session.commit()

        logger.debug(
            f"Sync event completed: id={event_id}, "
            f"products={products_synced}, discovered={tests_discovered}, "
            f"refreshed={tests_refreshed}, duration={duration_seconds:.2f}s"
        )

    async def log_sync_event_failed(
        self, event_id: int, error_message: str, duration_seconds: float
    ) -> None:
        """Update sync event with status='failed' and error message.

        Args:
            event_id: Event ID from log_sync_event_start()
            error_message: Error description
            duration_seconds: Time taken before failure

        STORY-034B: Refactored to use ORM (SyncEvent model) instead of raw aiosqlite.
        """
        if not self.repo or event_id < 0:
            return

        now = datetime.now(UTC).isoformat()

        # Update sync event (STORY-034B: using ORM)
        from sqlmodel import col

        async with self.async_session_maker() as session:
            result = await session.exec(select(SyncEvent).where(col(SyncEvent.id) == event_id))
            sync_event = result.first()
            if sync_event:
                sync_event.completed_at = now
                sync_event.status = "failed"
                sync_event.error_message = error_message
                sync_event.duration_seconds = duration_seconds
                await session.commit()

        logger.debug(f"Sync event failed: id={event_id}, error={error_message}")

    async def log_sync_event_cancelled(self, event_id: int, duration_seconds: float) -> None:
        """Update sync event with status='cancelled' (server shutdown).

        Args:
            event_id: Event ID from log_sync_event_start()
            duration_seconds: Time elapsed before cancellation

        STORY-034B: Refactored to use ORM (SyncEvent model) instead of raw aiosqlite.
        """
        if not self.repo or event_id < 0:
            return

        now = datetime.now(UTC).isoformat()

        # Update sync event (STORY-034B: using ORM)
        from sqlmodel import col

        async with self.async_session_maker() as session:
            result = await session.exec(select(SyncEvent).where(col(SyncEvent.id) == event_id))
            sync_event = result.first()
            if sync_event:
                sync_event.completed_at = now
                sync_event.status = "cancelled"
                sync_event.error_message = "Task cancelled (server shutdown)"
                sync_event.duration_seconds = duration_seconds
                await session.commit()

        logger.debug(
            f"Sync event cancelled: id={event_id}, duration={duration_seconds:.2f}s "
            f"(server shutdown)"
        )

    async def get_sync_events(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent sync events for observability.

        Args:
            limit: Maximum number of events to return (default: 10)

        Returns:
            List of sync event dicts ordered by started_at DESC

        STORY-034B: Refactored to use ORM (SyncEvent model) instead of raw aiosqlite.
        """
        if not self.repo:
            return []

        # Query sync events (STORY-034B: using ORM)
        from sqlmodel import col

        async with self.async_session_maker() as session:
            result = await session.exec(
                select(SyncEvent).order_by(col(SyncEvent.started_at).desc()).limit(limit)
            )
            sync_events = result.all()

            # Convert to dict format for compatibility
            events = []
            for event in sync_events:
                events.append(
                    {
                        "id": event.id,
                        "event_type": event.event_type,
                        "started_at": event.started_at,
                        "completed_at": event.completed_at,
                        "status": event.status,
                        "products_synced": event.products_synced,
                        "tests_discovered": event.tests_discovered,
                        "tests_refreshed": event.tests_refreshed,
                        "duration_seconds": event.duration_seconds,
                        "error_message": event.error_message,
                        "trigger_source": event.trigger_source,
                    }
                )

        return events

    async def count_sync_failures_since(self, since: datetime) -> int:
        """Count sync failures since given time for circuit breaker.

        Args:
            since: Count failures after this timestamp

        Returns:
            Number of failed sync events

        STORY-034B: Refactored to use ORM (SyncEvent model) instead of raw aiosqlite.
        """
        if not self.repo:
            return 0

        since_iso = since.isoformat()

        # Count failed events (STORY-034B: using ORM)
        from sqlalchemy import func
        from sqlmodel import col

        async with self.async_session_maker() as session:
            result = await session.exec(
                select(func.count())
                .select_from(SyncEvent)
                .where(
                    (col(SyncEvent.status) == "failed") & (col(SyncEvent.started_at) >= since_iso)
                )
            )
            count = result.one()  # exec() returns scalar directly for aggregate functions

        return count if count else 0

    async def get_last_destructive_timestamp(self) -> datetime | None:
        """Get timestamp of last destructive operation for rate limiting (STORY-022a).

        Returns:
            Datetime of last destructive operation, or None if never executed

        STORY-034B: Refactored to use ORM helper instead of raw aiosqlite.
        """
        if not self.repo:
            return None

        # Get metadata value (STORY-034B: using ORM helper)
        value = await self._get_sync_metadata("last_destructive_op")
        if value:
            # Parse ISO 8601 timestamp
            return datetime.fromisoformat(value)

        return None

    async def set_last_destructive_timestamp(self, timestamp: datetime) -> None:
        """Set timestamp of last destructive operation for rate limiting (STORY-022a).

        Args:
            timestamp: Datetime of destructive operation (should be UTC)

        STORY-034B: Refactored to use ORM helper instead of raw aiosqlite.
        """
        if not self.repo:
            return

        # Store as ISO 8601 string (STORY-034B: using ORM helper)
        await self._set_sync_metadata("last_destructive_op", timestamp.isoformat())

    async def refresh_active_tests(self, product_id: int) -> dict[str, Any]:
        """Refresh status for mutable tests (can still change).

        Implements AC4: Batch fetch fresh status from API with concurrency control.

        Mutable tests: customer_finalized, waiting, running, locked, initialized
        Immutable tests: archived, cancelled (skipped, never change)

        Args:
            product_id: Product identifier

        Returns:
            Dict with refresh statistics (tests_checked, tests_updated, errors)
        """
        if not self.repo:
            return {"tests_checked": 0, "tests_updated": 0, "status_changed": 0, "errors": []}

        logger.info(f"Starting mutable test refresh for product {product_id}")

        # Get mutable tests from database
        mutable_tests = await self._repo.get_mutable_tests(product_id)
        mutable_test_ids = [t["id"] for t in mutable_tests]

        if not mutable_test_ids:
            logger.info(f"No mutable tests found for product {product_id}")
            # Still update last_synced to mark that we checked (prevents staleness on restart)
            from testio_mcp.repositories.product_repository import ProductRepository

            async with self.async_session_maker() as session:
                repo = ProductRepository(session, self.client, self.customer_id)
                await repo.update_product_last_synced(product_id)
                await repo.commit()

            return {"tests_checked": 0, "tests_updated": 0, "status_changed": 0, "errors": []}

        # Create status map (before refresh) and test title map
        status_before = {t["id"]: t["status"] for t in mutable_tests}

        # Query titles from database (stored in data JSON column)
        # STORY-034B: Refactored to use ORM instead of raw SQL
        from testio_mcp.models.orm.test import Test

        test_titles = {}
        async with self.async_session_maker() as session:
            for test_id in mutable_test_ids:
                result = await session.exec(
                    select(Test).where(
                        (Test.id == test_id)
                        & (Test.product_id == product_id)
                        & (Test.customer_id == self.customer_id)
                    )
                )
                test = result.first()
                if test and test.data:
                    test_data = json.loads(test.data)
                    test_titles[test_id] = test_data.get("title", f"Test {test_id}")
                else:
                    test_titles[test_id] = f"Test {test_id}"

        print(f"\n🔄 Refreshing {len(mutable_test_ids)} mutable tests for product {product_id}...")

        # Batch fetch from API with concurrency control
        tests_updated = 0  # Successfully refreshed from API
        status_changed = 0  # Status actually changed
        errors: list[dict[str, Any]] = []
        updated_tests: list[dict[str, Any]] = []

        # Split fetch and update to avoid session concurrency issues (STORY-034A)
        # 1. Fetch concurrently from API
        async def fetch_test_data(test_id: int) -> tuple[int, dict[str, Any] | Exception]:
            try:
                response = await self.client.get(f"exploratory_tests/{test_id}")
                return test_id, response.get("exploratory_test", {})
            except Exception as e:
                return test_id, e

        with suppress_httpx_logs():
            tasks = [fetch_test_data(tid) for tid in mutable_test_ids]
            results = await asyncio.gather(*tasks)

        # 2. Update database sequentially
        for index, (test_id, result) in enumerate(results):
            try:
                if isinstance(result, Exception):
                    raise result

                test_data = result

                # Get old status
                old_status = status_before.get(test_id)

                # Extract product_id
                prod_id = test_data.get("product", {}).get("id")
                if not prod_id:
                    logger.warning(f"Test {test_id} missing product_id, skipping upsert")
                    continue

                # Update or insert test
                if await self._repo.test_exists(test_id, prod_id):
                    await self._repo.update_test(test_data, prod_id)
                else:
                    await self._repo.insert_test(test_data, prod_id)

                # Flush to make changes visible to subsequent queries in same transaction
                await self._repo.session.flush()

                # Count as successfully updated
                tests_updated += 1

                # Query new status after refresh
                new_status = await self._repo.get_test_status(test_id)

                # Track if status actually changed
                if old_status != new_status:
                    status_changed += 1
                    updated_tests.append(
                        {
                            "id": test_id,
                            "title": test_titles[test_id],
                            "old_status": old_status,
                            "new_status": new_status,
                        }
                    )

                # Show progress every 10 tests
                if (index + 1) % 10 == 0 or (index + 1) == len(mutable_test_ids):
                    print(
                        f"  Progress: {index + 1}/{len(mutable_test_ids)} tests checked "
                        f"({status_changed} changed, "
                        f"{tests_updated - status_changed} unchanged, {len(errors)} errors)"
                    )

            except Exception as e:
                logger.warning(f"Failed to refresh test {test_id}: {e}")
                errors.append({"test_id": test_id, "title": test_titles[test_id], "error": str(e)})

        # Commit all changes at once (STORY-032B)
        await self._repo.commit()

        # Print summary
        print("\n✅ Refresh complete:")
        print(f"   Total checked: {len(mutable_test_ids)}")
        print(f"   Successfully refreshed: {tests_updated}")
        print(f"   Status changed: {status_changed}")
        print(f"   Status unchanged: {tests_updated - status_changed}")
        print(f"   Errors: {len(errors)}")

        # Show updated test cycles (if any changed)
        if updated_tests:
            print("\n📊 Test cycles with status changes:")
            for test in updated_tests[:10]:  # Show first 10
                status_change = f"{test['old_status']} → {test['new_status']}"
                print(f"   • {test['title']} (ID: {test['id']}): {status_change}")
            if len(updated_tests) > 10:
                print(f"   ... and {len(updated_tests) - 10} more")

        # Show errors (if any)
        if errors:
            print(f"\n⚠️  Failed to refresh {len(errors)} tests:")
            for err in errors[:5]:  # Show first 5 errors
                print(f"   • {err['title']} (ID: {err['test_id']}): {err['error']}")
            if len(errors) > 5:
                print(f"   ... and {len(errors) - 5} more errors")

        logger.info(
            f"Mutable test refresh complete: product_id={product_id}, "
            f"checked={len(mutable_test_ids)}, updated={tests_updated}, "
            f"status_changed={status_changed}, errors={len(errors)}"
        )

        # Update product's last_synced timestamp (mark data as fresh)
        # This ensures staleness check knows we just refreshed the data
        from testio_mcp.repositories.product_repository import ProductRepository

        async with self.async_session_maker() as session:
            repo = ProductRepository(session, self.client, self.customer_id)
            await repo.update_product_last_synced(product_id)
            await repo.commit()

        return {
            "tests_checked": len(mutable_test_ids),
            "tests_updated": tests_updated,  # Successfully refreshed from API
            "status_changed": status_changed,  # Status actually changed
            "errors": errors,
            "updated_tests": updated_tests,
        }
