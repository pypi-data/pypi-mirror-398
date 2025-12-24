"""SyncService - Unified sync orchestration service (Epic-009).

This module provides the SyncService class for unified sync orchestration
across background sync, CLI manual sync, and MCP tool sync.

Key Components:
- SyncPhase: Enum for the 3-phase sync model (PRODUCTS, FEATURES, NEW_TESTS)
- SyncScope: Dataclass for filtering parameters (product_ids, since_date)
- SyncOptions: Dataclass for mode configuration (force_refresh, incremental_only, nuke)
- SyncResult: Dataclass for return value with stats and diagnostics
- SyncService: Main service class with execute_sync() method

Architecture:
- Inherits from BaseService for standard dependency injection
- Uses dual-layer locking: file lock (cross-process) + asyncio lock (in-process)
- Delegates to repositories for actual data operations
- Logs sync events to sync_events table for observability

STORY-048: SyncService Foundation
Epic: EPIC-009 (Sync Consolidation)
"""

from __future__ import annotations

import asyncio
import logging
import math
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import psutil
from filelock import FileLock, Timeout
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.models.orm.sync_event import SyncEvent
from testio_mcp.services.base_service import BaseService
from testio_mcp.utilities.progress import ProgressReporter

if TYPE_CHECKING:
    from testio_mcp.database.cache import PersistentCache
    from testio_mcp.repositories.feature_repository import FeatureRepository
    from testio_mcp.repositories.product_repository import ProductRepository
    from testio_mcp.repositories.test_repository import TestRepository

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models (AC2)
# =============================================================================


class SyncPhase(str, Enum):
    """Sync phases from ADR-017 3-phase model.

    The phases execute in order:
    1. PRODUCTS: Refresh product metadata
    2. FEATURES: Refresh features (TTL-gated)
    3. NEW_TESTS: Discover new tests (incremental)
    """

    PRODUCTS = "products"  # Phase 1: Refresh product metadata
    FEATURES = "features"  # Phase 2: Refresh features (TTL-gated)
    NEW_TESTS = "new_tests"  # Phase 3: Discover new tests (incremental)


@dataclass
class SyncScope:
    """Filtering parameters for sync scope.

    Attributes:
        product_ids: Limit sync to specific products (None = all products)
        since_date: Date filter for test discovery (None = no date filter)
        entity_types: Future-proofing for entity-level filtering
    """

    product_ids: list[int] | None = None
    since_date: datetime | None = None
    entity_types: list[str] | None = None


@dataclass
class SyncOptions:
    """Sync mode configuration.

    Attributes:
        force_refresh: Re-sync all tests (non-destructive upsert)
        incremental_only: Fast mode - discover new tests only, skip staleness checks
        nuke: Destructive mode - delete DB and full resync (CLI only, not MCP)
    """

    force_refresh: bool = False
    incremental_only: bool = False
    nuke: bool = False


@dataclass
class SyncResult:
    """Unified sync result with stats and diagnostics.

    Attributes:
        phases_completed: List of phases that completed successfully
        products_synced: Number of products synced
        features_refreshed: Number of features refreshed
        tests_discovered: Number of new tests discovered
        tests_updated: Number of existing tests updated
        duration_seconds: Total sync duration (REQUIRED - always populated)
        warnings: Non-fatal issues encountered during sync
        errors: Fatal errors that stopped sync (partial failure)
    """

    phases_completed: list[SyncPhase] = field(default_factory=list)
    products_synced: int = 0
    features_refreshed: int = 0
    tests_discovered: int = 0
    tests_updated: int = 0
    duration_seconds: float = 0.0  # REQUIRED (AC2)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# =============================================================================
# Exceptions
# =============================================================================


class SyncLockError(Exception):
    """Raised when sync lock cannot be acquired."""

    pass


class SyncTimeoutError(SyncLockError):
    """Raised when lock acquisition times out."""

    pass


# =============================================================================
# SyncService (AC1, AC3, AC4, AC5, AC6, AC7)
# =============================================================================


class SyncService(BaseService):
    """Unified sync orchestration service (Epic-009).

    Provides a single implementation for sync orchestration used by:
    - Background sync (server.py lifespan)
    - CLI manual sync (cli/sync.py)
    - MCP sync_data tool (tools/sync_data_tool.py)

    Features:
    - Phase orchestration (PRODUCTS -> FEATURES -> NEW_TESTS)
    - Dual-layer locking (file lock for cross-process, asyncio lock for in-process)
    - Stale lock recovery (PID check + 1-hour mtime threshold)
    - Sync event logging for observability
    - Partial failure handling (continue with next product if one fails)

    Attributes:
        client: TestIO API client (inherited from BaseService)
        cache: PersistentCache for async session creation and locks
        product_repo_factory: Factory for creating ProductRepository instances
        feature_repo_factory: Factory for creating FeatureRepository instances
        test_repo_factory: Factory for creating TestRepository instances

    Example:
        >>> service = SyncService(
        ...     client=client,
        ...     cache=cache,
        ...     product_repo_factory=lambda s: ProductRepository(s, client, customer_id),
        ...     feature_repo_factory=lambda s: FeatureRepository(s, client, customer_id),
        ...     test_repo_factory=lambda s: TestRepository(s, client, customer_id),
        ... )
        >>> result = await service.execute_sync(
        ...     phases=[SyncPhase.PRODUCTS, SyncPhase.NEW_TESTS],
        ...     scope=SyncScope(product_ids=[598]),
        ...     options=SyncOptions(force_refresh=True),
        ... )
    """

    # Lock file configuration (cross-process, AC4)
    LOCK_FILE = Path.home() / ".testio-mcp" / "sync.lock"
    LOCK_TIMEOUT_SECONDS = 30.0
    STALE_LOCK_THRESHOLD_SECONDS = 3600  # 1 hour (AC5)

    # In-process lock registry (AC6)
    _sync_locks: dict[str, asyncio.Lock] = {}

    def __init__(
        self,
        client: TestIOClient,
        cache: PersistentCache,
        product_repo_factory: Any | None = None,
        feature_repo_factory: Any | None = None,
        test_repo_factory: Any | None = None,
    ) -> None:
        """Initialize SyncService with dependencies.

        Args:
            client: TestIO API client for HTTP requests
            cache: PersistentCache for async session creation and entity locks
            product_repo_factory: Optional factory callable (session) -> ProductRepository
            feature_repo_factory: Optional factory callable (session) -> FeatureRepository
            test_repo_factory: Optional factory callable (session) -> TestRepository

        Note:
            Repository factories are optional for testing. If not provided,
            execute_sync() will create repositories using the cache's session.
        """
        super().__init__(client)
        self.cache = cache
        self._product_repo_factory = product_repo_factory
        self._feature_repo_factory = feature_repo_factory
        self._test_repo_factory = test_repo_factory

    # =========================================================================
    # Main Entry Point (AC3)
    # =========================================================================

    async def execute_sync(
        self,
        phases: list[SyncPhase] | None = None,
        scope: SyncScope | None = None,
        options: SyncOptions | None = None,
        trigger_source: str = "unknown",
        progress: ProgressReporter | None = None,
    ) -> SyncResult:
        """Execute sync with specified phases, scope, and options.

        This is the main entry point for all sync operations.

        Args:
            phases: Which phases to run (default: all 3 in order)
            scope: Filtering parameters (product_ids, since_date)
            options: Mode flags (force_refresh, incremental_only, nuke)
            trigger_source: Source that triggered sync (startup, scheduled, manual, mcp)
            progress: Optional ProgressReporter for status updates (MCP clients)

        Returns:
            SyncResult with stats and diagnostics

        Raises:
            SyncLockError: Another sync in progress (couldn't acquire lock)
            SyncTimeoutError: Lock acquisition timed out

        Note:
            Locking order (deadlock prevention, AC6):
            1. Acquire file lock (cross-process)
            2. Acquire asyncio lock (in-process)
            This order MUST be maintained to prevent deadlocks.
        """
        # Default to all phases in order
        if phases is None:
            phases = [SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS]

        # Default scope and options
        if scope is None:
            scope = SyncScope()
        if options is None:
            options = SyncOptions()

        # Default progress reporter (no-op if not provided)
        if progress is None:
            progress = ProgressReporter.noop()

        start_time = time.time()
        result = SyncResult()

        # Log sync start event (AC7)
        sync_event_id = await self._log_sync_start(phases, scope, trigger_source)

        try:
            # Acquire file lock (cross-process, AC4)
            # NOTE: File lock acquired BEFORE asyncio lock (deadlock prevention, AC6)
            async with self._acquire_file_lock():
                # Acquire asyncio lock (in-process, AC6)
                asyncio_lock = self._get_sync_lock()
                async with asyncio_lock:
                    # Execute phases in order
                    result = await self._execute_phases(phases, scope, options, progress)

        except SyncTimeoutError:
            # Lock timeout - another sync in progress
            result.errors.append("Sync lock timeout - another sync may be in progress")
            await self._log_sync_error(sync_event_id, result.errors[0], start_time)
            raise

        except Exception as e:
            # Unexpected error
            result.errors.append(str(e))
            await self._log_sync_error(sync_event_id, str(e), start_time)
            raise

        # Calculate duration (AC2 - REQUIRED)
        result.duration_seconds = time.time() - start_time

        # Log sync completion (AC7)
        await self._log_sync_completion(sync_event_id, result)

        # STORY-065: Optimize FTS5 search index after nuke or full refresh
        # This reduces fragmentation after bulk operations (triggers fired many times)
        if options.nuke or options.force_refresh:
            try:
                await self._optimize_search_index()
            except Exception as e:
                # Non-fatal - sync succeeded, index optimization is optional
                logger.warning(f"FTS5 index optimization failed (non-fatal): {e}")

        # Report completion progress
        await progress.complete(
            f"Sync complete: {result.products_synced} products, "
            f"{result.features_refreshed} features, "
            f"{result.tests_discovered} tests discovered, "
            f"{result.tests_updated} tests updated. "
            f"Duration: {result.duration_seconds:.1f}s"
        )

        # Log summary (AC7 - duration always included)
        logger.info(
            f"Sync completed in {result.duration_seconds:.1f}s "
            f"({len(result.phases_completed)} phases: "
            f"products={result.products_synced}, "
            f"features={result.features_refreshed}, "
            f"tests={result.tests_discovered} new / {result.tests_updated} updated)"
        )

        return result

    # =========================================================================
    # Phase Execution (AC3)
    # =========================================================================

    async def _execute_phases(
        self,
        phases: list[SyncPhase],
        scope: SyncScope,
        options: SyncOptions,
        progress: ProgressReporter,
    ) -> SyncResult:
        """Execute sync phases in order.

        Phase order is enforced: PRODUCTS -> FEATURES -> NEW_TESTS
        Even if phases are passed out of order, they execute correctly.

        STORY-062: Session Management Strategy
        --------------------------------------
        This method creates a single session for orchestrating phases. This is SAFE because:
        1. Phases execute SEQUENTIALLY (no concurrent phase execution)
        2. Each phase either:
           - Does sequential operations (Products, NewTests phases)
           - Or delegates to repositories that create ISOLATED sessions for
             concurrent operations (Features → FeatureRepository.get_features_cached_or_refresh)

        WARNING: Do NOT add asyncio.gather() here to run phases concurrently.
        If you need concurrent operations, ensure each task creates its own session
        via cache.async_session_maker(). See CLAUDE.md "Async Session Management".

        Args:
            phases: List of phases to execute
            scope: Filtering parameters
            options: Mode configuration
            progress: ProgressReporter for status updates

        Returns:
            SyncResult with aggregated stats
        """
        result = SyncResult()

        # Ensure correct phase order
        all_phases = [SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS]
        ordered_phases = [p for p in all_phases if p in phases]
        total_phases = len(ordered_phases)

        # Session shared across phases (sequential execution - SAFE)
        # Repositories handle concurrent operations with isolated sessions internally
        async with self.cache.async_session_maker() as session:
            for i, phase in enumerate(ordered_phases):
                # Report phase progress (force=True to bypass throttle - phases are milestones)
                await progress.report(
                    progress=i,
                    total=total_phases,
                    message=f"Phase {i + 1}/{total_phases}: {phase.value}...",
                    force=True,
                )

                try:
                    phase_result = await self._execute_single_phase(
                        phase, scope, options, session, progress
                    )
                    result = self._merge_phase_result(result, phase_result, phase)
                    result.phases_completed.append(phase)

                except Exception as e:
                    # Partial failure - log warning but continue with next phase
                    warning = f"Phase {phase.value} failed: {e}"
                    result.warnings.append(warning)
                    logger.warning(warning)
                    # Don't add to phases_completed since it failed

            # STORY-062: Update last_synced for all products after sync completes
            # This single timestamp controls staleness checks for background sync
            if result.phases_completed:
                try:
                    await self._update_products_last_synced(session, scope)
                except Exception as e:
                    # Non-fatal - sync still succeeded, just timestamp update failed
                    logger.warning(f"Failed to update last_synced timestamps: {e}")

        return result

    async def _execute_single_phase(
        self,
        phase: SyncPhase,
        scope: SyncScope,
        options: SyncOptions,
        session: AsyncSession,
        progress: ProgressReporter,
    ) -> SyncResult:
        """Execute a single sync phase.

        Delegates to appropriate repository methods based on phase.

        Args:
            phase: Phase to execute
            scope: Filtering parameters
            options: Mode configuration
            session: Active async session for database operations
            progress: ProgressReporter for status updates

        Returns:
            SyncResult with phase-specific stats
        """
        result = SyncResult()

        if phase == SyncPhase.PRODUCTS:
            result = await self._execute_products_phase(scope, options, session)
        elif phase == SyncPhase.FEATURES:
            result = await self._execute_features_phase(scope, options, session)
        elif phase == SyncPhase.NEW_TESTS:
            result = await self._execute_new_tests_phase(scope, options, session, progress)

        return result

    async def _execute_products_phase(
        self,
        scope: SyncScope,
        options: SyncOptions,
        session: AsyncSession,
    ) -> SyncResult:
        """Execute Phase 1: Refresh product metadata.

        Fetches product list from API and upserts to database.

        Args:
            scope: Filtering parameters (product_ids limits which to sync)
            options: Mode configuration
            session: Active async session

        Returns:
            SyncResult with products_synced count
        """
        result = SyncResult()

        # Get product repository
        product_repo = self._get_product_repo(session)

        try:
            # Fetch products from API
            response = await self.client.get("products")
            products = response.get("products", [])

            # Filter by scope if specified
            if scope.product_ids:
                products = [p for p in products if p.get("id") in scope.product_ids]

            # Upsert products
            for product_data in products:
                try:
                    await product_repo.upsert_product(product_data)
                    result.products_synced += 1
                except Exception as e:
                    warning = f"Failed to upsert product {product_data.get('id')}: {e}"
                    result.warnings.append(warning)
                    logger.warning(warning)

            await session.commit()

        except Exception as e:
            result.errors.append(f"Products phase failed: {e}")
            logger.error(f"Products phase failed: {e}")

        return result

    async def _update_products_last_synced(
        self,
        session: AsyncSession,
        scope: SyncScope,
    ) -> None:
        """Update last_synced timestamp for all synced products.

        STORY-062: Single timestamp to track background sync freshness.
        Called after all phases complete successfully.

        Args:
            session: Active async session
            scope: Filtering parameters (product_ids limits which to update)
        """
        from datetime import UTC, datetime

        from sqlmodel import col, select

        from testio_mcp.models.orm.product import Product

        now_utc = datetime.now(UTC)

        # Build query for products to update
        customer_id = self.cache.customer_id
        if scope.product_ids:
            statement = select(Product).where(
                col(Product.id).in_(scope.product_ids),
                Product.customer_id == customer_id,
            )
        else:
            statement = select(Product).where(Product.customer_id == customer_id)

        result = await session.exec(statement)
        products = result.all()

        for product in products:
            product.last_synced = now_utc
            session.add(product)

        await session.commit()
        logger.debug(f"Updated last_synced for {len(products)} products")

    async def _execute_features_phase(
        self,
        scope: SyncScope,
        options: SyncOptions,
        session: AsyncSession,
    ) -> SyncResult:
        """Execute Phase 2: Refresh features (TTL-gated).

        Syncs features for products using get_features_cached_or_refresh().
        Respects staleness TTL unless force_refresh is set.

        Args:
            scope: Filtering parameters (product_ids limits which to sync)
            options: Mode configuration (force_refresh bypasses TTL)
            session: Active async session

        Returns:
            SyncResult with features_refreshed count
        """
        result = SyncResult()

        # Get feature repository
        feature_repo = self._get_feature_repo(session)

        try:
            # Get product IDs to sync features for
            if scope.product_ids:
                product_ids = scope.product_ids
            else:
                # Get all product IDs from database
                product_repo = self._get_product_repo(session)
                products = await product_repo.get_all_products()
                product_ids = [p_id for p in products if (p_id := p.get("id")) is not None]

            if not product_ids:
                logger.info("No products found for feature sync")
                return result

            # Always refresh features during background sync (ignore staleness)
            # Rationale: Features have no pagination (fetch-all or nothing), cheap to fetch
            # Background sync should keep them fresh; staleness checks are for on-demand reads
            # This prevents the scenario where features never refresh if TTL never expires
            features_dict, cache_stats = await feature_repo.get_features_cached_or_refresh(
                product_ids=product_ids,
                force_refresh=True,  # Always refresh in sync operations
            )

            # Count actual features synced across all products
            total_features = sum(len(features) for features in features_dict.values())
            result.features_refreshed = total_features

        except Exception as e:
            result.errors.append(f"Features phase failed: {e}")
            logger.error(f"Features phase failed: {e}")

        return result

    async def _execute_new_tests_phase(
        self,
        scope: SyncScope,
        options: SyncOptions,
        session: AsyncSession,
        progress: ProgressReporter,
    ) -> SyncResult:
        """Execute Phase 3: Discover new tests (incremental with pagination).

        Algorithm:
        1. Fetch tests sorted by -end_at (newest first from API)
        2. For each test, upsert to database (INSERT OR REPLACE)
        3. Track when we hit first known test (by existence check)
        4. Stop after hitting known test + 1 safety page (catch stragglers)
        5. Multi-pass recovery: reduce page size on 500 errors (25→10→5→2→1)

        Upsert Behavior:
        - ALL tests fetched from API are upserted (both new and existing)
        - This ensures any test we see has fresh data in the database
        - Only truly new tests (not previously in DB) increment tests_discovered
        - Known test detection determines when to stop fetching, not what to update

        Args:
            scope: Filtering parameters (product_ids, since_date)
            options: Mode configuration (force_refresh = full resync)
            session: Active async session
            progress: ProgressReporter for status updates

        Returns:
            SyncResult with tests_discovered count
        """
        result = SyncResult()

        # Get test repository
        test_repo = self._get_test_repo(session)

        try:
            # Get product IDs to sync tests for
            if scope.product_ids:
                product_ids = scope.product_ids
            else:
                # Get all product IDs from database
                product_repo = self._get_product_repo(session)
                products = await product_repo.get_all_products()
                product_ids = [p_id for p in products if (p_id := p.get("id")) is not None]

            if not product_ids:
                logger.info("No products found for test sync")
                return result

            total_products = len(product_ids)

            # Sync tests for each product using pagination
            for i, product_id in enumerate(product_ids):
                # Report global progress (Phase 3 is index 2, so 2.0 to 3.0)
                # Use floats to map product iteration to the final 3rd of the progress bar
                current_progress = 2.0 + (i / total_products)

                # Report per-product progress (force=True - product boundaries are milestones)
                idx = i + 1
                product_msg = f"Discovering tests: product {product_id} ({idx}/{total_products})..."
                await progress.report(
                    progress=current_progress,
                    total=3.0,
                    message=product_msg,
                    force=True,
                )

                try:
                    product_result = await self._sync_product_tests_paginated(
                        product_id=product_id,
                        test_repo=test_repo,
                        session=session,
                        scope=scope,
                        options=options,
                        progress=progress,
                        current_progress=current_progress,
                    )
                    result.tests_discovered += product_result["new_tests_count"]
                    result.tests_updated += product_result["tests_updated"]
                    if product_result.get("warnings"):
                        result.warnings.extend(product_result["warnings"])

                except Exception as e:
                    warning = f"Failed to sync tests for product {product_id}: {e}"
                    result.warnings.append(warning)
                    logger.warning(warning)

        except Exception as e:
            result.errors.append(f"New tests phase failed: {e}")
            logger.error(f"New tests phase failed: {e}")

        return result

    async def _sync_product_tests_paginated(
        self,
        product_id: int,
        test_repo: TestRepository,
        session: AsyncSession,
        scope: SyncScope,
        options: SyncOptions,
        progress: ProgressReporter,
        current_progress: float = 0.0,
    ) -> dict[str, Any]:
        """Sync tests for a single product using paginated incremental algorithm.

        Algorithm:
        1. Fetch pages of tests (newest first by end_at from API)
        2. Upsert ALL tests fetched (keeps data fresh)
        3. Track when we hit a known test (exists in DB before this sync)
        4. Stop after 1 safety page past the first known test
        5. Use multi-pass recovery for 500 errors (25→10→5→2→1 page sizes)

        Args:
            product_id: Product to sync tests for
            test_repo: TestRepository instance
            session: Active async session
            scope: Filtering parameters (since_date)
            options: Mode configuration (force_refresh)
            options: Mode configuration (force_refresh)
            progress: ProgressReporter for per-page status updates
            current_progress: Current global progress (base for this product)

        Returns:
            Dict with new_tests_count, tests_updated, warnings
        """
        new_tests_count = 0
        tests_updated = 0
        warnings: list[str] = []
        page = 1
        page_size = 25  # Default page size for API requests
        safety_pages_remaining = 1  # Pages to fetch AFTER hitting known ID
        hit_known_test = False
        hit_known_test_this_page = False
        total_recovery_attempts = 0

        # Track tests inserted during THIS sync to prevent false positives
        tests_inserted_this_sync: set[int] = set()

        # Track oldest test date seen (for logging)
        oldest_test_date: datetime | None = None

        # Track successfully synced tests in this page's batch (for boundary detection)
        current_batch_tests: list[dict[str, Any]] = []  # Tests synced in current page

        # Track skipped pages to log after processing
        skipped_pages_to_log: list[int] = []

        # Track last successfully synced test globally (for completely failed pages)
        last_successful_test: dict[str, Any] | None = None

        # Safety limit to prevent infinite loops
        MAX_PAGES = 50

        logger.info(f"Starting paginated sync for product {product_id}")

        total_tests_fetched = 0
        while page <= MAX_PAGES:
            hit_known_test_this_page = False

            # Report per-page progress (throttled - rapid pages won't spam)
            # Use current_progress (static for this product) and total=3.0 to keep global context
            await progress.report(
                progress=current_progress,
                total=3.0,
                message=f"Discovering tests: page {page} ({total_tests_fetched} found so far)...",
                force=False,  # Throttle (0.5s minimum between updates)
            )

            # Fetch page with multi-pass recovery for 500 errors
            page_data, recovery_attempts, skipped_pages = await self._fetch_page_with_recovery(
                product_id=product_id,
                page=page,
                page_size=page_size,
            )

            total_recovery_attempts += recovery_attempts

            # Accumulate skipped pages (will log after processing tests)
            skipped_pages_to_log.extend(skipped_pages)

            # Clear batch tracking for this page
            current_batch_tests.clear()

            # Extract tests from response (process them first to get boundary info)
            tests = page_data.get("exploratory_tests", [])
            total_tests_fetched += len(tests)
            recovery_failed = page_data.get("recovery_failed", False)

            # If recovery failed completely with no data, skip this page
            if recovery_failed and not tests:
                warnings.append(f"Page {page} unrecoverable for product {product_id}")
                logger.warning(
                    f"Skipping page {page} (no salvaged tests), moving to page {page + 1}"
                )

                # Log problematic test event for retry later
                # (no salvaged tests, no "after" boundary)
                await self._log_problematic_page(
                    test_repo=test_repo,
                    product_id=product_id,
                    page=page,
                    page_size=page_size,
                    recovery_attempts=recovery_attempts,
                    before_id=(last_successful_test.get("id") if last_successful_test else None),
                    before_end_at=(
                        last_successful_test.get("end_at") if last_successful_test else None
                    ),
                    after_id=None,
                    after_end_at=None,
                    options=options,
                )

                page += 1
                continue

            # Log if we're processing salvaged tests from partial recovery
            if recovery_failed and tests:
                logger.info(
                    f"Processing {len(tests)} salvaged tests from page {page} "
                    f"(partial recovery, some chunks failed)"
                )

            if not tests:
                logger.info(f"No more tests found at page {page}, stopping sync")
                break

            # Client-side date filtering (API doesn't support date filtering)
            # Apply filter regardless of force_refresh mode
            if scope.since_date:
                filtered_tests = []
                for test in tests:
                    test_end_at_str = test.get("end_at")
                    if test_end_at_str:
                        try:
                            test_end_at = datetime.fromisoformat(
                                test_end_at_str.replace("Z", "+00:00")
                            )
                            since_utc = scope.since_date
                            if since_utc.tzinfo is None:
                                since_utc = since_utc.replace(tzinfo=UTC)
                            if test_end_at < since_utc:
                                continue  # Skip tests older than cutoff
                        except (ValueError, TypeError):
                            pass  # Include test if date parsing fails
                    filtered_tests.append(test)

                # If all tests filtered out (older than cutoff), stop fetching
                if len(filtered_tests) == 0 and len(tests) > 0:
                    logger.info(
                        f"Page {page}: All tests older than {scope.since_date}, stopping sync"
                    )
                    break

                tests = filtered_tests

            # Insert/update tests and check for known IDs
            duplicates_skipped = 0
            for test in tests:
                test_id = test.get("id")

                # Track oldest test date for logging
                test_end_at_str = test.get("end_at")
                if test_end_at_str:
                    try:
                        test_end_at = datetime.fromisoformat(test_end_at_str.replace("Z", "+00:00"))
                        if oldest_test_date is None or test_end_at < oldest_test_date:
                            oldest_test_date = test_end_at
                    except (ValueError, TypeError):
                        pass  # Skip if date parsing fails

                # Skip if already processed this sync (deduplication for overlapping chunks)
                if test_id and test_id in tests_inserted_this_sync:
                    duplicates_skipped += 1
                    continue  # Already processed from salvaged chunks, skip duplicate

                # Check if we've hit a known test (for stop-early optimization)
                # Skip this check if force_refresh=True (fetch all tests)
                is_new_test = True
                if test_id:
                    exists = await test_repo.test_exists(test_id, product_id)
                    if exists:
                        is_new_test = False
                        # Only trigger early exit if test existed BEFORE this sync
                        # AND force_refresh is not enabled (incremental mode only)
                        if (
                            not options.force_refresh
                            and not hit_known_test
                            and test_id not in tests_inserted_this_sync
                        ):
                            logger.info(
                                f"Hit known test_id={test_id} at page {page}, "
                                f"will continue for {safety_pages_remaining} more pages"
                            )
                            hit_known_test = True
                            hit_known_test_this_page = True

                # Always upsert test (keeps data fresh)
                try:
                    await test_repo.insert_test(test, product_id)

                    # Track that we inserted this test during this sync
                    if test_id:
                        tests_inserted_this_sync.add(test_id)

                    # Count appropriately
                    if is_new_test:
                        new_tests_count += 1
                    else:
                        tests_updated += 1

                    # Track this test for boundary detection
                    current_batch_tests.append(test)

                except Exception as e:
                    warnings.append(f"Failed to upsert test {test_id}: {e}")
                    logger.warning(f"Failed to upsert test {test_id}: {e}")

            # Log deduplication stats if any duplicates were skipped
            if duplicates_skipped > 0:
                logger.info(
                    f"Page {page}: Skipped {duplicates_skipped} duplicate(s) "
                    f"(already processed from salvaged chunks or previous pages)"
                )

            # Commit the batch for this page
            await session.commit()

            # Log skipped pages with proper boundaries (after processing tests)
            if skipped_pages_to_log and current_batch_tests:
                # Sort batch tests by end_at DESC to reconstruct API pagination order
                sorted_batch = sorted(
                    current_batch_tests,
                    key=lambda t: t.get("end_at", ""),
                    reverse=True,  # Newest first (API order)
                )

                # Get boundaries from sorted batch
                # Newest (comes first in API)
                before_test = sorted_batch[0] if sorted_batch else None
                # Oldest (comes last in API)
                after_test = sorted_batch[-1] if sorted_batch else None

                # Log each skipped page with boundaries
                for skipped_page in skipped_pages_to_log:
                    await self._log_problematic_page(
                        test_repo=test_repo,
                        product_id=product_id,
                        page=skipped_page,
                        page_size=1,
                        recovery_attempts=5,
                        before_id=before_test.get("id") if before_test else None,
                        before_end_at=before_test.get("end_at") if before_test else None,
                        after_id=after_test.get("id") if after_test else None,
                        after_end_at=after_test.get("end_at") if after_test else None,
                        options=options,
                    )

                # Clear for next page
                skipped_pages_to_log.clear()

            # Update global last successful test (newest test from this batch)
            if current_batch_tests:
                newest_test = max(
                    current_batch_tests, key=lambda t: t.get("end_at", ""), default=None
                )
                if newest_test:
                    last_successful_test = newest_test

            # Check if there are more pages (API doesn't return "next" field)
            has_more = len(tests) >= page_size

            # Check stop condition AFTER processing current page
            if hit_known_test and not hit_known_test_this_page:
                safety_pages_remaining -= 1
                if safety_pages_remaining <= 0:
                    logger.info("Completed safety margin (1 page after known ID), stopping sync")
                    break

            if not has_more:
                logger.info("Reached end of available pages, sync complete")
                break

            page += 1

        if page > MAX_PAGES:
            warnings.append(f"Hit {MAX_PAGES}-page safety limit for product {product_id}")
            logger.warning(f"Hit {MAX_PAGES}-page safety limit for product {product_id}")

        # Build summary message with oldest test date
        summary_parts = [
            f"new={new_tests_count}",
            f"updated={tests_updated}",
            f"pages={page}",
            f"recovery_attempts={total_recovery_attempts}",
        ]

        if oldest_test_date:
            summary_parts.append(f"oldest_test={oldest_test_date.date()}")

        logger.info(f"Sync complete for product {product_id}: {', '.join(summary_parts)}")

        return {
            "new_tests_count": new_tests_count,
            "tests_updated": tests_updated,
            "warnings": warnings,
            "pages_fetched": page,
            "recovery_attempts": total_recovery_attempts,
        }

    async def _fetch_page_with_recovery(
        self,
        product_id: int,
        page: int,
        page_size: int,
    ) -> tuple[dict[str, Any], int, list[int]]:
        """Fetch page with multi-pass recovery for 500 errors.

        Algorithm:
        - Try with page_size=25
        - If 500 error, retry with smaller page sizes (10→5→2→1)
        - Combine results from multiple chunks to cover the original range
        - ADAPTIVE: When a chunk fails, update the offset/range to only retry the failed portion

        Args:
            product_id: Product identifier
            page: Page number (1-indexed)
            page_size: Initial page size (25)

        Returns:
            Tuple of (page_data, recovery_attempts, skipped_pages)
            - page_data: {"exploratory_tests": [...], "recovery_failed": bool}
            - recovery_attempts: Number of 500 errors encountered
            - skipped_pages: List of page numbers that failed at page_size=1
        """
        recovery_attempts = 0
        skipped_pages: list[int] = []
        sizes_to_try = [25, 10, 5, 2, 1]

        # Calculate absolute offset and range size from original request
        # IMPORTANT: These are updated during recovery to focus on failed ranges
        original_offset = (page - 1) * page_size
        original_range_size = page_size

        # Preserve tests across recovery attempts (deduplicate by test ID)
        combined_results_by_id: dict[int, dict[str, Any]] = {}

        for attempt_size in sizes_to_try:
            try:
                # Calculate how many chunks needed to cover current range
                num_chunks = math.ceil(original_range_size / attempt_size)

                if recovery_attempts > 0:
                    logger.info(
                        f"[RECOVERY] Trying page_size={attempt_size}, "
                        f"num_chunks={num_chunks}, offset={original_offset}, "
                        f"range_size={original_range_size}, attempts={recovery_attempts}"
                    )

                all_chunks_succeeded = True

                # Calculate starting page that CONTAINS original_offset with new attempt_size
                # Page N covers offsets [(N-1)*size, N*size)
                # We want the page that contains original_offset:
                #   (N-1)*size <= original_offset < N*size
                #   N = (original_offset // size) + 1
                # Example: offset 75 with size 10:
                #   Page 8 covers [70, 80) - contains 75 ✓
                #   75 // 10 = 7, so page = 7 + 1 = 8
                start_page = (original_offset // attempt_size) + 1

                # Fetch all chunks at this size level
                for chunk_idx in range(num_chunks):
                    chunk_page = start_page + chunk_idx

                    try:
                        params: dict[str, Any] = {
                            "page": chunk_page,
                            "per_page": attempt_size,
                        }

                        response = await self.client.get(
                            f"products/{product_id}/exploratory_tests",
                            params=params,
                        )

                        # Collect results (deduplicate by ID)
                        chunk_tests = response.get("exploratory_tests", [])
                        for test in chunk_tests:
                            test_id = test.get("id")
                            if test_id is not None:
                                combined_results_by_id[test_id] = test

                    except Exception as e:
                        error_str = str(e)
                        if "500" in error_str or "Internal Server Error" in error_str:
                            recovery_attempts += 1
                            logger.warning(
                                f"API 500 error at page={chunk_page}, size={attempt_size}"
                            )
                            all_chunks_succeeded = False

                            # At page_size=1, skip this single test and continue
                            if attempt_size == 1:
                                logger.warning("Skipping offset at page_size=1")
                                skipped_pages.append(chunk_page)
                                continue

                            # ADAPTIVE RECOVERY: Update offset/range to only retry
                            # the failed portion
                            # The failed page covers: (chunk_page - 1) * attempt_size
                            failed_page_start = (chunk_page - 1) * attempt_size

                            # Calculate the end of the range we're currently trying to cover
                            current_range_end = original_offset + original_range_size - 1

                            # Next recovery should start from where the failed page starts
                            # and cover up to the end of our current range
                            original_offset = failed_page_start
                            original_range_size = current_range_end - failed_page_start + 1

                            logger.info(
                                f"[RECOVERY UPDATE] Failed page covered "
                                f"[{failed_page_start}-{failed_page_start + attempt_size - 1}], "
                                f"salvaged {len(combined_results_by_id)} tests, "
                                f"next attempt will cover [{original_offset}-{current_range_end}]"
                            )

                            break  # Try smaller size
                        else:
                            # Non-500 error, re-raise
                            raise

                # If all chunks succeeded, return combined results
                if all_chunks_succeeded:
                    combined_results = list(combined_results_by_id.values())

                    if recovery_attempts > 0:
                        logger.info(
                            f"Recovery successful: {len(combined_results)} tests "
                            f"across {num_chunks} chunks at size={attempt_size}"
                        )

                    return (
                        {
                            "exploratory_tests": combined_results,
                            "recovery_failed": False,
                        },
                        recovery_attempts,
                        skipped_pages,
                    )

            except Exception as e:
                error_str = str(e)
                if "500" not in error_str and "Internal Server Error" not in error_str:
                    raise

        # All recovery attempts failed, but return salvaged tests
        combined_results = list(combined_results_by_id.values())
        logger.error(
            f"Failed to fetch page {page} after {recovery_attempts} recovery attempts. "
            f"Salvaged {len(combined_results)} tests from successful chunks before failure."
        )

        if combined_results:
            logger.info(
                f"Recovery partial success: Returning {len(combined_results)} salvaged tests "
                f"from page {page} (some chunks succeeded, will continue with next page)"
            )
        else:
            logger.warning(
                f"Recovery complete failure: No tests salvaged from page {page} "
                f"(all chunks failed, skipping this page range)"
            )

        return (
            {
                "exploratory_tests": combined_results,
                "recovery_failed": True,
            },
            recovery_attempts,
            skipped_pages,
        )

    async def _log_problematic_page(
        self,
        test_repo: TestRepository,
        product_id: int,
        page: int,
        page_size: int,
        recovery_attempts: int,
        before_id: int | None,
        before_end_at: str | None,
        after_id: int | None,
        after_end_at: str | None,
        options: SyncOptions,
    ) -> None:
        """Log a problematic page that failed recovery to sync_metadata.

        Args:
            test_repo: TestRepository instance
            product_id: Product identifier
            page: Failed page number
            page_size: Page size used
            recovery_attempts: Number of recovery attempts made
            before_id: ID of test before the failed range
            before_end_at: end_at timestamp of test before the failed range
            after_id: ID of test after the failed range
            after_end_at: end_at timestamp of test after the failed range
            options: Sync options (for sync_mode)
        """
        from datetime import datetime

        # Calculate position range for the failed page
        start_offset = (page - 1) * page_size
        end_offset = start_offset + page_size - 1
        position_range = f"{start_offset}-{end_offset}"

        # Determine sync mode
        sync_mode = "force_refresh" if options.force_refresh else "incremental"

        test_info = {
            "product_id": product_id,
            "position_range": position_range,
            "recovery_attempts": recovery_attempts,
            "boundary_before_id": before_id,
            "boundary_before_end_at": before_end_at,
            "boundary_after_id": after_id,
            "boundary_after_end_at": after_end_at,
            "sync_mode": sync_mode,
            "command_run_at": datetime.now(UTC).isoformat(),
        }

        await test_repo.log_problematic_test(test_info)

    def _merge_phase_result(
        self, total: SyncResult, phase_result: SyncResult, phase: SyncPhase
    ) -> SyncResult:
        """Merge phase result into total result.

        Args:
            total: Accumulated result
            phase_result: Result from single phase
            phase: Phase that was executed

        Returns:
            Updated total result
        """
        total.products_synced += phase_result.products_synced
        total.features_refreshed += phase_result.features_refreshed
        total.tests_discovered += phase_result.tests_discovered
        total.tests_updated += phase_result.tests_updated
        total.warnings.extend(phase_result.warnings)
        total.errors.extend(phase_result.errors)
        return total

    # =========================================================================
    # Repository Factory Methods
    # =========================================================================

    def _get_product_repo(self, session: AsyncSession) -> ProductRepository:
        """Get ProductRepository instance.

        Uses factory if provided, otherwise creates directly.
        """
        if self._product_repo_factory:
            repo: ProductRepository = self._product_repo_factory(session)
            return repo

        from testio_mcp.repositories.product_repository import ProductRepository

        return ProductRepository(session, self.client, self.cache.customer_id)

    def _get_feature_repo(self, session: AsyncSession) -> FeatureRepository:
        """Get FeatureRepository instance.

        Uses factory if provided, otherwise creates directly.
        """
        if self._feature_repo_factory:
            repo: FeatureRepository = self._feature_repo_factory(session)
            return repo

        from testio_mcp.repositories.feature_repository import FeatureRepository

        return FeatureRepository(session, self.client, self.cache.customer_id, self.cache)

    def _get_test_repo(self, session: AsyncSession) -> TestRepository:
        """Get TestRepository instance.

        Uses factory if provided, otherwise creates directly.
        """
        if self._test_repo_factory:
            repo: TestRepository = self._test_repo_factory(session)
            return repo

        from testio_mcp.repositories.test_repository import TestRepository

        return TestRepository(session, self.client, self.cache.customer_id, cache=self.cache)

    # =========================================================================
    # FTS5 Index Optimization (STORY-065)
    # =========================================================================

    async def _optimize_search_index(self) -> None:
        """Optimize FTS5 search index after bulk operations.

        Called after nuke or force_refresh syncs to reduce index fragmentation.
        Non-blocking - failures are logged but don't fail the sync.

        STORY-065: Search MCP Tool integration.
        """
        from testio_mcp.repositories.search_repository import SearchRepository

        async with self.cache.async_session_maker() as session:
            search_repo = SearchRepository(
                session=session, client=self.client, customer_id=self.cache.customer_id
            )
            await search_repo.optimize_index()
            logger.info("FTS5 search index optimized after bulk sync operation")

    # =========================================================================
    # File Lock (AC4, AC5)
    # =========================================================================

    class _FileLockContext:
        """Async context manager for file lock acquisition with stale recovery."""

        def __init__(self, service: SyncService) -> None:
            self.service = service
            self.file_lock: FileLock | None = None

        async def __aenter__(self) -> SyncService._FileLockContext:
            """Acquire file lock with stale recovery."""
            # Ensure lock directory exists
            self.service.LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Check for stale lock before attempting acquisition (AC5)
            if self.service._is_lock_stale(self.service.LOCK_FILE):
                logger.warning(
                    f"Detected stale lock file at {self.service.LOCK_FILE}, reclaiming..."
                )
                try:
                    self.service.LOCK_FILE.unlink()
                except OSError:
                    pass  # File might have been removed by another process

            # Create file lock
            lock_path = str(self.service.LOCK_FILE)
            timeout = self.service.LOCK_TIMEOUT_SECONDS
            self.file_lock = FileLock(lock_path, timeout=timeout)

            try:
                # Acquire lock (blocking with timeout)
                self.file_lock.acquire()

                # Write PID to lock file for stale detection (AC5)
                self.service._write_lock_pid()

                logger.debug(f"Acquired sync lock at {self.service.LOCK_FILE}")
                return self

            except Timeout as e:
                raise SyncTimeoutError(
                    f"Failed to acquire sync lock within {self.service.LOCK_TIMEOUT_SECONDS}s. "
                    f"Another sync may be in progress. Lock file: {self.service.LOCK_FILE}"
                ) from e

        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            """Release file lock."""
            if self.file_lock and self.file_lock.is_locked:
                self.file_lock.release()
                logger.debug(f"Released sync lock at {self.service.LOCK_FILE}")

    def _acquire_file_lock(self) -> _FileLockContext:
        """Acquire cross-process file lock with stale recovery.

        Returns:
            Async context manager for lock acquisition

        Usage:
            async with self._acquire_file_lock():
                # Lock is held
                ...
            # Lock is released

        Note:
            Uses stale lock recovery (AC5):
            - Checks if PID in lock file is still alive
            - Checks if lock file mtime > 1 hour
            - If stale, reclaims lock and logs warning
        """
        return self._FileLockContext(self)

    def _is_lock_stale(self, lock_path: Path) -> bool:
        """Check if lock file is stale (AC5).

        A lock is considered stale if:
        1. The PID in the lock file is no longer running, OR
        2. The lock file's mtime is older than STALE_LOCK_THRESHOLD_SECONDS

        Args:
            lock_path: Path to lock file

        Returns:
            True if lock is stale and can be reclaimed
        """
        if not lock_path.exists():
            return False

        try:
            # Check 1: PID validation
            content = lock_path.read_text().strip()
            if content:
                # Parse PID from lock file (format: "PID: 12345\nSTARTED: ...")
                for line in content.split("\n"):
                    if line.startswith("PID:"):
                        pid_str = line.split(":")[1].strip()
                        try:
                            pid = int(pid_str)
                            if not psutil.pid_exists(pid):
                                logger.debug(f"Lock file PID {pid} is not running - stale")
                                return True
                        except (ValueError, TypeError):
                            pass

            # Check 2: mtime threshold
            mtime = lock_path.stat().st_mtime
            age_seconds = time.time() - mtime
            if age_seconds > self.STALE_LOCK_THRESHOLD_SECONDS:
                logger.debug(
                    f"Lock file is {age_seconds:.0f}s old "
                    f"(threshold: {self.STALE_LOCK_THRESHOLD_SECONDS}s) - stale"
                )
                return True

        except OSError as e:
            # If we can't read the lock file, assume not stale (safer)
            logger.debug(f"Could not check lock file staleness: {e}")
            return False

        return False

    def _write_lock_pid(self) -> None:
        """Write PID to lock file for stale detection (AC5).

        Format:
            PID: 12345
            STARTED: 2025-11-26T10:30:00Z
        """
        try:
            content = f"PID: {os.getpid()}\nSTARTED: {datetime.now(UTC).isoformat()}\n"
            self.LOCK_FILE.write_text(content)
        except OSError as e:
            logger.warning(f"Failed to write PID to lock file: {e}")

    # =========================================================================
    # Asyncio Lock (AC6)
    # =========================================================================

    def _get_sync_lock(self) -> asyncio.Lock:
        """Get asyncio lock for in-process sync serialization (AC6).

        Reuses PersistentCache.get_refresh_lock() pattern with setdefault()
        to avoid race conditions during lock creation.

        Returns:
            asyncio.Lock for sync operations

        Note:
            This lock prevents thundering herd within the same process.
            Multiple MCP calls or concurrent async tasks will serialize here.
        """
        key = f"sync_{self.cache.customer_id}"
        if key not in self._sync_locks:
            self._sync_locks[key] = asyncio.Lock()
        return self._sync_locks[key]

    # =========================================================================
    # Sync Event Logging (AC7)
    # =========================================================================

    async def _log_sync_start(
        self,
        phases: list[SyncPhase],
        scope: SyncScope,
        trigger_source: str,
    ) -> int:
        """Log sync start event (AC7).

        Args:
            phases: Phases being executed
            scope: Sync scope parameters
            trigger_source: What triggered the sync

        Returns:
            Sync event ID for later update
        """
        async with self.cache.async_session_maker() as session:
            event = SyncEvent(
                event_type="sync",
                started_at=datetime.now(UTC).isoformat(),
                status="running",
                trigger_source=trigger_source,
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)

            logger.info(
                f"Sync started (event_id={event.id}, "
                f"phases={[p.value for p in phases]}, "
                f"trigger={trigger_source})"
            )

            return event.id or 0

    async def _log_sync_completion(
        self,
        event_id: int,
        result: SyncResult,
    ) -> None:
        """Log sync completion event (AC7).

        Args:
            event_id: ID of sync event to update
            result: Sync result with stats
        """
        async with self.cache.async_session_maker() as session:
            from sqlmodel import select

            stmt = select(SyncEvent).where(SyncEvent.id == event_id)
            db_result = await session.exec(stmt)
            event = db_result.first()

            if event:
                event.status = "success" if not result.errors else "partial_failure"
                event.completed_at = datetime.now(UTC).isoformat()
                event.duration_seconds = result.duration_seconds
                event.products_synced = result.products_synced
                event.features_refreshed = result.features_refreshed
                event.tests_discovered = result.tests_discovered

                session.add(event)
                await session.commit()

    async def _log_sync_error(
        self,
        event_id: int,
        error_message: str,
        start_time: float,
    ) -> None:
        """Log sync error event (AC7).

        Args:
            event_id: ID of sync event to update
            error_message: Error description
            start_time: When sync started (for duration calculation)
        """
        async with self.cache.async_session_maker() as session:
            from sqlmodel import select

            stmt = select(SyncEvent).where(SyncEvent.id == event_id)
            db_result = await session.exec(stmt)
            event = db_result.first()

            if event:
                event.status = "failure"
                event.completed_at = datetime.now(UTC).isoformat()
                event.duration_seconds = time.time() - start_time
                event.error_message = error_message

                session.add(event)
                await session.commit()

                logger.error(f"Sync failed in {event.duration_seconds:.1f}s: {error_message}")
