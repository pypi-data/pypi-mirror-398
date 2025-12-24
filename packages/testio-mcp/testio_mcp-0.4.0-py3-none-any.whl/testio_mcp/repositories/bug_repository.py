"""Bug Repository - Data access layer for bug-related database operations.

This repository handles all SQL queries for bugs and API refresh operations.
Intelligent bug caching (STORY-024): Immutable tests (archived/cancelled) are
always served from cache. Mutable tests check staleness and refresh if needed.

Reference: STORY-023c (SQLite-First Foundation - Repository Layer)
Reference: STORY-024 (Intelligent Bug Caching)
Reference: STORY-032C (ORM Refactor - BugRepository)
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import delete, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.config import settings
from testio_mcp.models.orm.bug import Bug
from testio_mcp.repositories.base_repository import BaseRepository
from testio_mcp.transformers.bug_transformers import transform_api_bug_to_orm
from testio_mcp.utilities.progress import BatchProgressCallback, safe_batch_callback

if TYPE_CHECKING:
    from testio_mcp.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of a batch refresh operation.

    Used for collecting results from concurrent batch operations to report
    both successes and failures to the caller.
    """

    succeeded: list[int] = field(default_factory=list)  # Successfully refreshed test_ids
    failed: list[int] = field(default_factory=list)  # Failed test_ids
    error: str | None = None  # Error message if any


def _enrich_bug_status(api_status: str | None, auto_accepted: bool | None) -> str | None:
    """Enrich bug status for storage, distinguishing auto_accepted from active acceptance.

    This function normalizes the API's status/auto_accepted combination into a single
    enriched status value for SQL-friendly queries and analytics.

    Status Mapping:
        | API status | auto_accepted | Storage status   |
        |------------|---------------|------------------|
        | "accepted" | True          | "auto_accepted"  |
        | "accepted" | False/None    | "accepted"       |
        | "rejected" | any           | "rejected"       |
        | "forwarded"| any           | "forwarded"      |
        | other      | any           | unchanged        |

    Args:
        api_status: Bug status from TestIO API ("accepted", "rejected", "forwarded")
        auto_accepted: Auto acceptance flag from API (True if auto-accepted after 10 days)

    Returns:
        Enriched status value for database storage

    Note:
        Original API response is preserved in raw_data JSON for reference.
        STORY-047: Normalize Bug Auto-Accepted Status
    """
    if api_status == "accepted" and auto_accepted is True:
        return "auto_accepted"
    return api_status


class BugRepository(BaseRepository):
    """Repository for bug-related database operations.

    Handles ORM queries and API refresh operations with no business logic.
    All queries are scoped to a specific customer for data isolation.
    """

    def __init__(
        self,
        session: AsyncSession,
        client: TestIOClient,
        customer_id: int,
        user_repo: "UserRepository | None" = None,
        cache: Any | None = None,
    ) -> None:
        """Initialize repository with database session and API client.

        Args:
            session: AsyncSession for ORM-based database operations
            client: TestIO API client for refresh operations
            customer_id: Stable customer identifier from TestIO system
            user_repo: Optional UserRepository for tester extraction (STORY-036)
            cache: Optional PersistentCache for per-entity refresh locks (STORY-046, AC6)
        """
        super().__init__(session, client, customer_id, cache)
        self.user_repo = user_repo

    async def get_bugs(self, test_id: int) -> list[dict[str, Any]]:
        """Get all bugs for a test from SQLite.

        Returns bug dictionaries with enriched status from database column.
        The status field is overwritten with the enriched value (STORY-047):
        - "auto_accepted" for bugs that were auto-accepted (vs "accepted" in raw API response)
        - Other statuses remain unchanged

        STORY-071: The known field is also overwritten with the column value (authoritative source).

        Args:
            test_id: Test identifier

        Returns:
            List of bug dictionaries with enriched status and known fields.
            Original raw_data preserved for reference, but status and known are enriched.
        """
        from sqlmodel import col, desc

        statement = select(Bug).where(Bug.test_id == test_id, Bug.customer_id == self.customer_id)
        # Note: created_at is TEXT in SQLite, so we can't use .desc() method
        # Order by ID descending as proxy (newer bugs have higher IDs)
        statement = statement.order_by(desc(col(Bug.id)))
        result = await self.session.exec(statement)  # type: ignore[union-attr]
        bugs_orm = result.all()

        # Deserialize JSON data and inject enriched status (STORY-047) and known (STORY-071)
        bugs: list[dict[str, Any]] = []
        for bug_orm in bugs_orm:
            bug_dict = json.loads(bug_orm.raw_data)
            # Override status with enriched value from database column
            # This ensures classify_bugs() sees "auto_accepted" instead of "accepted"
            bug_dict["status"] = bug_orm.status
            # STORY-071: Override known with column value (authoritative source)
            bug_dict["known"] = bug_orm.known
            bugs.append(bug_dict)

        return bugs

    async def get_bug_stats(self, test_id: int) -> dict[str, Any]:
        """Get bug statistics (counts by status and severity).

        Args:
            test_id: Test identifier

        Returns:
            Dictionary with bug count aggregations:
                {
                    "total": 10,
                    "by_status": {"accepted": 5, "rejected": 2, "pending": 3},
                    "by_severity": {"critical": 2, "high": 3, "medium": 5}
                }
        """
        # Count by status
        statement = (
            select(Bug.status, func.count(Bug.id))  # type: ignore[arg-type]
            .where(Bug.test_id == test_id, Bug.customer_id == self.customer_id)
            .group_by(Bug.status)
        )
        result = await self.session.exec(statement)  # type: ignore[union-attr]
        status_rows = result.all()
        by_status = {row[0]: row[1] for row in status_rows if row[0]}

        # Count by severity
        statement = (
            select(Bug.severity, func.count(Bug.id))  # type: ignore[arg-type]
            .where(Bug.test_id == test_id, Bug.customer_id == self.customer_id)
            .group_by(Bug.severity)
        )
        result = await self.session.exec(statement)  # type: ignore[union-attr]
        severity_rows = result.all()
        by_severity = {row[0]: row[1] for row in severity_rows if row[0]}

        # Total count
        count_statement = select(func.count(Bug.id)).where(  # type: ignore[arg-type]
            Bug.test_id == test_id, Bug.customer_id == self.customer_id
        )
        count_result = await self.session.exec(count_statement)  # type: ignore[union-attr]
        total = count_result.one()

        return {
            "total": total,
            "by_status": by_status,
            "by_severity": by_severity,
        }

    async def get_bug_aggregates_for_tests(
        self,
        test_ids: list[int],
    ) -> dict[str, Any]:
        """Get aggregate bug metrics for multiple tests (for PQR summary).

        Computes total bugs, bugs by status, and bugs by severity using SQL
        aggregates without fetching individual bug records.

        Args:
            test_ids: List of test IDs to aggregate bugs for

        Returns:
            Dictionary with:
                - total_bugs: Total count of bugs
                - bugs_by_status: {status: count} mapping
                - bugs_by_severity: {severity: count} mapping
        """
        if not test_ids:
            return {
                "total_bugs": 0,
                "bugs_by_status": {},
                "bugs_by_severity": {},
            }

        from sqlmodel import col

        # Total count
        count_stmt = select(func.count(Bug.id)).where(  # type: ignore[arg-type]
            col(Bug.test_id).in_(test_ids),
            Bug.customer_id == self.customer_id,
        )
        count_result = await self.session.exec(count_stmt)  # type: ignore[union-attr]
        total_bugs = count_result.one()

        # Group by status
        status_stmt = (
            select(Bug.status, func.count(Bug.id))  # type: ignore[arg-type]
            .where(
                col(Bug.test_id).in_(test_ids),
                Bug.customer_id == self.customer_id,
            )
            .group_by(Bug.status)
        )
        status_result = await self.session.exec(status_stmt)  # type: ignore[union-attr]
        bugs_by_status = {row[0]: row[1] for row in status_result.all() if row[0]}

        # Group by severity
        severity_stmt = (
            select(Bug.severity, func.count(Bug.id))  # type: ignore[arg-type]
            .where(
                col(Bug.test_id).in_(test_ids),
                Bug.customer_id == self.customer_id,
            )
            .group_by(Bug.severity)
        )
        severity_result = await self.session.exec(severity_stmt)  # type: ignore[union-attr]
        bugs_by_severity = {row[0]: row[1] for row in severity_result.all() if row[0]}

        return {
            "total_bugs": total_bugs,
            "bugs_by_status": bugs_by_status,
            "bugs_by_severity": bugs_by_severity,
        }

    async def get_bug_aggregates_grouped_by_product(
        self,
        product_ids: list[int],
    ) -> dict[int, dict[str, Any]]:
        """Get bug aggregates grouped by product_id in a single query.

        Optimized version that avoids N+1 queries when building per-product
        breakdown for multi-product reports. Joins bugs with tests to get
        product association.

        Args:
            product_ids: List of product IDs to aggregate bugs for

        Returns:
            Dictionary mapping product_id to aggregates:
            {
                598: {"total_bugs": 50, "bugs_by_status": {...}, "bugs_by_severity": {...}},
                599: {"total_bugs": 30, "bugs_by_status": {...}, "bugs_by_severity": {...}},
            }
        """
        from sqlmodel import col

        from testio_mcp.models.orm import Test

        # Initialize result with empty aggregates for all products
        result: dict[int, dict[str, Any]] = {
            pid: {"total_bugs": 0, "bugs_by_status": {}, "bugs_by_severity": {}}
            for pid in product_ids
        }

        if not product_ids:
            return result

        # Join Bug with Test to get product_id
        # Base WHERE clause
        base_where = [
            Bug.customer_id == self.customer_id,
            Bug.test_id == Test.id,
            col(Test.product_id).in_(product_ids),
        ]

        # Count grouped by product_id
        count_stmt = (
            select(Test.product_id, func.count(Bug.id))  # type: ignore[arg-type]
            .where(*base_where)  # type: ignore[arg-type]
            .group_by(Test.product_id)  # type: ignore[arg-type]
        )
        count_result = await self.session.exec(count_stmt)  # type: ignore[union-attr]
        for row in count_result.all():
            pid, cnt = row[0], row[1]
            if pid in result:
                result[pid]["total_bugs"] = cnt

        # Status counts grouped by product_id
        status_stmt = (
            select(Test.product_id, Bug.status, func.count(Bug.id))  # type: ignore[arg-type]
            .where(*base_where)  # type: ignore[arg-type]
            .group_by(Test.product_id, Bug.status)  # type: ignore[arg-type]
        )
        status_result = await self.session.exec(status_stmt)  # type: ignore[union-attr]
        for row in status_result.all():
            pid, status, cnt = row[0], row[1], row[2]
            if pid in result and status:
                result[pid]["bugs_by_status"][status] = cnt

        # Severity counts grouped by product_id
        severity_stmt = (
            select(Test.product_id, Bug.severity, func.count(Bug.id))  # type: ignore[arg-type]
            .where(*base_where)  # type: ignore[arg-type]
            .group_by(Test.product_id, Bug.severity)  # type: ignore[arg-type]
        )
        severity_result = await self.session.exec(severity_stmt)  # type: ignore[union-attr]
        for row in severity_result.all():
            pid, severity, cnt = row[0], row[1], row[2]
            if pid in result and severity:
                result[pid]["bugs_by_severity"][severity] = cnt

        return result

    async def get_bugs_cached_or_refresh(
        self,
        test_ids: list[int],
        force_refresh: bool = False,
        on_batch_progress: BatchProgressCallback | None = None,
    ) -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
        """Get bugs with intelligent caching based on test mutability.

        Batch-aware method: Pass single test ID or multiple for efficient batch processing.

        Decision Logic (per test, priority order):
        1. Check bugs_synced_at and test status from tests table
        2. If BUG_CACHE_BYPASS=true → mark for refresh (debug mode)
        3. If force_refresh=True → mark for refresh (user override)
        4. If BUG_CACHE_ENABLED=false → mark for refresh (global toggle)
        5. If bugs_synced_at IS NULL → mark for refresh (never synced!)
        6. If test is immutable (archived/cancelled) → use cache (bugs won't change)
        7. If test is mutable (locked/running/etc.) → check staleness
           - If stale (>TTL seconds) → mark for refresh
           - If fresh → use cache
        8. Batch refresh all tests marked for refresh (single API call per batch)
        9. Return bugs for all test IDs from SQLite

        Args:
            test_ids: List of test identifiers (single or multiple)
            force_refresh: Bypass cache and fetch from API for all tests (default: False)
            on_batch_progress: Optional callback invoked after each batch completes.
                Args: (current_completed: int, total_batches: int). Best-effort (errors swallowed).

        Returns:
            Tuple of (bugs_dict, cache_stats):
                - bugs_dict: Dictionary mapping test_id -> list of bug dicts
                  Example: {123: [{bug1}, {bug2}], 124: [{bug3}]}
                - cache_stats: Cache efficiency metrics dict with:
                  - total_tests: int
                  - cache_hits: int
                  - api_calls: int
                  - cache_hit_rate: float (0-100)
                  - breakdown: dict with decision category counts

        Performance:
            - Single test cache hit: ~10ms (SQLite query)
            - Batch (295 tests, 80% cache hit): ~12 seconds vs ~45 seconds (4x faster)
            - Immutable tests: Always cache hit (no API calls)

        Logging:
            - DEBUG: Per-test decisions (SQLite vs API, with reason)
            - INFO: Summary stats (cache hit rate, breakdown by category)
            Example logs:
                Test 123: SQLite (immutable (archived))
                Test 124: SQLite (mutable (running), fresh (0.5h))
                Test 125: API (mutable (running), stale (2.3h))
                Bug cache: 236/295 from SQLite (80.0% hit rate), 59 from API
                Breakdown: 236 immutable, 40 mutable fresh, 19 mutable stale
        """
        if not test_ids:
            return {}, {
                "total_tests": 0,
                "cache_hits": 0,
                "api_calls": 0,
                "cache_hit_rate": 0.0,
                "breakdown": {},
            }

        # 1. Bulk query: Get test statuses and bugs_synced_at for all test IDs
        # Import Test model and col for querying (avoid circular import at module level)
        from sqlmodel import col

        from testio_mcp.models.orm.test import Test

        statement = select(Test.id, Test.status, Test.bugs_synced_at).where(
            col(Test.id).in_(test_ids), Test.customer_id == self.customer_id
        )
        test_result = await self.session.exec(statement)  # type: ignore[union-attr]
        rows = test_result.all()
        test_metadata: dict[int, dict[str, Any]] = {
            row[0]: {"status": row[1], "bugs_synced_at": row[2]}
            for row in rows
            if row[0] is not None
        }

        # 2. Determine which tests need refreshing
        tests_to_refresh: list[int] = []
        now = datetime.now(UTC)

        # Track decision stats for logging
        cache_decisions = {
            "immutable_cached": 0,
            "mutable_fresh": 0,
            "mutable_stale": 0,
            "never_synced": 0,
            "force_refresh": 0,
            "cache_disabled": 0,
            "cache_bypass": 0,
            "not_in_db": 0,
        }

        for test_id in test_ids:
            metadata = test_metadata.get(test_id)

            if not metadata:
                # Test not in DB - need to refresh (will likely 404 from API)
                tests_to_refresh.append(test_id)
                cache_decisions["not_in_db"] += 1
                logger.debug(f"Test {test_id}: API (not in database)")
                continue

            test_status = metadata["status"]
            bugs_synced_at_str = metadata["bugs_synced_at"]

            # Parse bugs_synced_at timestamp (ISO format with timezone)
            bugs_synced_at: datetime | None = None
            if bugs_synced_at_str:
                try:
                    # bugs_synced_at_str can be str, datetime, or None from DB
                    if isinstance(bugs_synced_at_str, str):
                        bugs_synced_at = datetime.fromisoformat(bugs_synced_at_str)
                    elif isinstance(bugs_synced_at_str, datetime):
                        bugs_synced_at = bugs_synced_at_str

                    # Ensure timezone awareness (assume UTC if naive)
                    if bugs_synced_at and bugs_synced_at.tzinfo is None:
                        bugs_synced_at = bugs_synced_at.replace(tzinfo=UTC)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid bugs_synced_at for test {test_id}, will refresh")

            # Apply decision logic (same priority order as before)
            should_refresh = False
            decision_reason = ""

            if settings.BUG_CACHE_BYPASS:
                should_refresh = True
                decision_reason = "BUG_CACHE_BYPASS active"
                cache_decisions["cache_bypass"] += 1
            elif force_refresh:
                should_refresh = True
                decision_reason = "force_refresh=True"
                cache_decisions["force_refresh"] += 1
            elif not settings.BUG_CACHE_ENABLED:
                should_refresh = True
                decision_reason = "BUG_CACHE_ENABLED=false"
                cache_decisions["cache_disabled"] += 1
            elif bugs_synced_at is None:
                # Never synced - MUST fetch
                should_refresh = True
                decision_reason = "never synced"
                cache_decisions["never_synced"] += 1
            elif test_status in settings.IMMUTABLE_TEST_STATUSES:
                # Immutable (archived/cancelled) - use cache
                should_refresh = False
                decision_reason = f"immutable ({test_status})"
                cache_decisions["immutable_cached"] += 1
            elif test_status in settings.MUTABLE_TEST_STATUSES:
                # Mutable - check staleness
                seconds_since_sync = (now - bugs_synced_at).total_seconds()
                hours_since_sync = seconds_since_sync / 3600

                if seconds_since_sync > settings.CACHE_TTL_SECONDS:
                    should_refresh = True
                    decision_reason = f"mutable ({test_status}), stale ({hours_since_sync:.1f}h)"
                    cache_decisions["mutable_stale"] += 1
                else:
                    should_refresh = False
                    decision_reason = f"mutable ({test_status}), fresh ({hours_since_sync:.1f}h)"
                    cache_decisions["mutable_fresh"] += 1
            else:
                # Unknown status - default to refresh (defensive)
                should_refresh = True
                decision_reason = f"unknown status '{test_status}'"
                logger.warning(f"Test {test_id} has unknown status '{test_status}'")

            # Log decision
            source = "API" if should_refresh else "SQLite"
            logger.debug(f"Test {test_id}: {source} ({decision_reason})")

            if should_refresh:
                tests_to_refresh.append(test_id)

        # 3. Log cache efficiency summary
        cache_hits = len(test_ids) - len(tests_to_refresh)
        cache_hit_rate = (cache_hits / len(test_ids) * 100) if test_ids else 0

        logger.info(
            f"Bug cache decisions: {cache_hits}/{len(test_ids)} from SQLite "
            f"({cache_hit_rate:.1f}% hit rate), {len(tests_to_refresh)} from API"
        )

        # Log breakdown by category (non-zero only)
        breakdown_parts = []
        if cache_decisions["immutable_cached"]:
            breakdown_parts.append(f"{cache_decisions['immutable_cached']} immutable (cached)")
        if cache_decisions["mutable_fresh"]:
            breakdown_parts.append(f"{cache_decisions['mutable_fresh']} mutable fresh (cached)")
        if cache_decisions["mutable_stale"]:
            breakdown_parts.append(f"{cache_decisions['mutable_stale']} mutable stale (API)")
        if cache_decisions["never_synced"]:
            breakdown_parts.append(f"{cache_decisions['never_synced']} never synced (API)")
        if cache_decisions["force_refresh"]:
            breakdown_parts.append(f"{cache_decisions['force_refresh']} force refresh (API)")
        if cache_decisions["cache_disabled"]:
            breakdown_parts.append(f"{cache_decisions['cache_disabled']} cache disabled (API)")
        if cache_decisions["cache_bypass"]:
            breakdown_parts.append(f"{cache_decisions['cache_bypass']} cache bypass (API)")
        if cache_decisions["not_in_db"]:
            breakdown_parts.append(f"{cache_decisions['not_in_db']} not in DB (API)")

        if breakdown_parts:
            logger.info(f"Breakdown: {', '.join(breakdown_parts)}")

        # 4. Batch refresh tests that need it (with per-entity locks, STORY-046 AC6,
        #    STORY-062 async session management, decoupled API/DB pattern)
        #
        # Architecture (decoupled API/DB):
        # - API fetch: OUTSIDE semaphore (~10 concurrent via HTTP client)
        # - DB write: INSIDE semaphore (default 1, serialized; configurable 2-5
        #   via MAX_CONCURRENT_DB_WRITES)
        # - Timestamp update: INSIDE same session as bug write (incremental persistence)
        #
        # This allows ~10 concurrent API calls while serializing DB writes to ~5,
        # and ensures partial failures preserve completed batches.
        all_succeeded: list[int] = []
        all_failed: list[int] = []
        errors: list[str] = []

        if tests_to_refresh:
            # STORY-062: Per-operation session pattern for batch operations
            # WARNING: asyncio.gather() with shared session causes "Cannot operate on a closed
            # database" errors. Each concurrent task MUST get its own session.
            # See CLAUDE.md "Async Session Management" section for details.

            # Batch API calls with multi-lock protection (AC6 fix)
            # Strategy: Acquire all locks for a batch, then make single batch API call
            # This preserves both lock protection AND batch API efficiency
            BATCH_SIZE = 15
            batches = [
                tests_to_refresh[i : i + BATCH_SIZE]
                for i in range(0, len(tests_to_refresh), BATCH_SIZE)
            ]

            # Thread-safe counter for progress reporting (PEP 703 future-proof)
            counter_lock = asyncio.Lock()
            completed_batches = 0

            async def refresh_batch_with_locks(batch: list[int]) -> BatchResult:
                """Refresh batch with decoupled API/DB and incremental persistence.

                Architecture:
                - Step 1: API fetch OUTSIDE semaphore (~10 concurrent via HTTP client)
                - Step 2: DB write INSIDE semaphore (~5 concurrent to prevent locks)
                - Step 3: Update timestamps in SAME transaction (incremental persistence)

                Returns BatchResult with succeeded/failed test_ids and optional error.
                """
                nonlocal completed_batches  # For progress tracking

                if not self.cache:
                    # Cache is required for safe concurrent operations
                    raise RuntimeError(
                        "BugRepository.get_bugs_cached_or_refresh requires cache "
                        "for concurrent batch operations"
                    )

                # Get all locks for this batch
                locks = [self.cache.get_refresh_lock("bug", test_id) for test_id in batch]

                # Acquire all locks concurrently with timeout to prevent head-of-line blocking
                # (Fix for Issue #6: Lock Acquisition Timeout)
                # Track acquired locks to ensure cleanup on timeout/error
                acquired_locks: list[asyncio.Lock] = []

                async def acquire_lock_with_timeout(
                    lock: asyncio.Lock, timeout: float = 30.0
                ) -> asyncio.Lock:
                    """Acquire lock with timeout to prevent indefinite blocking."""
                    try:
                        await asyncio.wait_for(lock.acquire(), timeout=timeout)
                        acquired_locks.append(lock)  # Track for cleanup
                        return lock
                    except TimeoutError:
                        logger.error(f"Lock acquisition timeout after {timeout}s")
                        # Release any locks acquired so far before failing
                        for acquired in acquired_locks:
                            acquired.release()
                        raise RuntimeError(
                            f"Failed to acquire bug refresh lock after {timeout}s. "
                            "Another operation may be stuck."
                        ) from None

                try:
                    await asyncio.gather(*[acquire_lock_with_timeout(lock) for lock in locks])
                except RuntimeError:
                    # Lock acquisition failed and cleanup already done
                    return BatchResult(succeeded=[], failed=batch, error="Lock timeout")

                try:
                    logger.debug(f"Acquired {len(acquired_locks)} bug refresh locks for batch")

                    # Step 1: API fetch OUTSIDE semaphore (~10 concurrent via HTTP client)
                    # This allows many concurrent API calls while only serializing DB writes
                    bugs_data, _ = await self._fetch_bugs_from_api(batch)

                    # Step 2: DB write INSIDE semaphore (~5 concurrent to prevent SQLite locks)
                    async with self.cache._write_semaphore:
                        async with self.cache.async_session_maker() as isolated_session:
                            try:
                                # Create isolated user_repo with same session for user upserts
                                from testio_mcp.repositories.user_repository import UserRepository

                                isolated_user_repo = UserRepository(
                                    session=isolated_session,
                                    client=self.client,
                                    customer_id=self.customer_id,
                                )

                                # Create isolated bug_repo with isolated session
                                isolated_repo = BugRepository(
                                    session=isolated_session,
                                    client=self.client,
                                    customer_id=self.customer_id,
                                    user_repo=isolated_user_repo,
                                    cache=self.cache,
                                )

                                # Write bugs to DB
                                await isolated_repo._write_bugs_to_db(bugs_data, batch)

                                # Step 3: Update timestamps in SAME transaction
                                # (incremental persistence - bugs + timestamps commit atomically)
                                await isolated_repo._update_synced_at_in_session(batch)

                                # Atomic commit: bugs + timestamps together
                                await isolated_session.commit()

                            except Exception:
                                # Explicit rollback to release pending transactions immediately
                                # (Fix for Issue #5: Missing Explicit Rollback)
                                await isolated_session.rollback()
                                raise

                    # Progress callback after successful batch (thread-safe counter)
                    async with counter_lock:
                        completed_batches += 1
                        current = completed_batches
                    await safe_batch_callback(on_batch_progress, current, len(batches))

                    return BatchResult(succeeded=batch, failed=[], error=None)

                except Exception as e:
                    error_msg = f"{type(e).__name__}: {e!s}"
                    logger.error(f"Batch refresh failed for {batch[:3]}...: {error_msg}")

                    # Increment counter even on failure so progress reaches 100%
                    # (Codex review finding: stalled progress bars)
                    async with counter_lock:
                        completed_batches += 1
                        current = completed_batches
                    await safe_batch_callback(on_batch_progress, current, len(batches))

                    return BatchResult(succeeded=[], failed=batch, error=error_msg)

                finally:
                    # Release all locks
                    for lock in acquired_locks:
                        lock.release()

            # Process all batches concurrently
            # Each task has its own isolated session - safe for concurrent execution
            batch_results = await asyncio.gather(
                *[refresh_batch_with_locks(batch) for batch in batches]
            )

            # Aggregate results for reporting (collect & report pattern)
            for batch_result in batch_results:
                all_succeeded.extend(batch_result.succeeded)
                all_failed.extend(batch_result.failed)
                if batch_result.error:
                    errors.append(batch_result.error)

            # Log summary
            if all_failed:
                logger.warning(
                    f"Bug refresh: {len(all_succeeded)} succeeded, {len(all_failed)} failed"
                )
            else:
                logger.info(f"Refreshed {len(all_succeeded)}/{len(tests_to_refresh)} tests")

            # NOTE: Removed post-gather timestamp update - now done inside each batch
            # This enables incremental persistence (partial failures preserve progress)

        # 5. Return bugs for ALL requested test IDs from SQLite
        # Use fresh session if we just did concurrent refreshes (prevents stale reads)
        # (Fix for Issue #2: Stale Read Bug from async-session-concurrency-review)
        result: dict[int, list[dict[str, Any]]] = {}

        # Only use fresh session if we actually refreshed any tests (stale read risk)
        # Otherwise use existing get_bugs() method with long-lived session (safe)
        needs_fresh_session = self.cache and len(tests_to_refresh) > 0

        for test_id in test_ids:
            if needs_fresh_session:
                # Use fresh session to avoid stale reads after concurrent refresh
                async with self.cache.async_session_maker() as fresh_session:  # type: ignore[union-attr]
                    from sqlmodel import col, desc

                    query = select(Bug).where(
                        Bug.test_id == test_id, Bug.customer_id == self.customer_id
                    )
                    query = query.order_by(desc(col(Bug.id)))
                    bug_result = await fresh_session.exec(query)
                    bugs_orm = bug_result.all()

                    # Deserialize JSON data and inject enriched status (STORY-047)
                    # and known (STORY-071)
                    bugs: list[dict[str, Any]] = []
                    for bug_orm in bugs_orm:
                        bug_dict = json.loads(bug_orm.raw_data)
                        # Override status with enriched value from database column
                        bug_dict["status"] = bug_orm.status
                        # STORY-071: Override known with column value (authoritative source)
                        bug_dict["known"] = bug_orm.known
                        bugs.append(bug_dict)

                    result[test_id] = bugs
            else:
                # No refresh happened - safe to use long-lived session via get_bugs()
                result[test_id] = await self.get_bugs(test_id)

        # 6. Build cache stats for transparency (includes failed test reporting)
        cache_stats = {
            "total_tests": len(test_ids),
            "cache_hits": cache_hits,
            "api_calls": len(tests_to_refresh),
            "api_succeeded": len(all_succeeded),
            "api_failed": len(all_failed),
            "failed_test_ids": all_failed,  # For transparency
            "errors": errors,  # Error messages for debugging
            "cache_hit_rate": cache_hit_rate,
            "breakdown": {
                k: v
                for k, v in cache_decisions.items()
                if v > 0  # Only non-zero counts
            },
        }

        return result, cache_stats

    async def _update_bugs_synced_at_batch(
        self, test_ids: list[int], session: AsyncSession | None = None
    ) -> None:
        """Update bugs_synced_at timestamp for multiple tests (bulk update).

        STORY-062: Updated to optionally accept session parameter for use with
        per-operation session pattern in batch operations.

        Args:
            test_ids: List of test identifiers to update
            session: Optional session to use; if None, uses cache.async_session_maker()
                    or falls back to self.session
        """
        if not test_ids:
            return

        # Import Test model and col for updating (avoid circular import at module level)
        from sqlmodel import col

        from testio_mcp.models.orm.test import Test

        # STORY-062: Use isolated session for batch timestamp updates
        # This ensures timestamps are updated consistently after concurrent operations
        if session is not None:
            # Use provided session
            target_session = session
            should_commit = False  # Caller manages commit
        elif self.cache:
            # Create isolated session via cache
            async with self.cache.async_session_maker() as isolated_session:
                now_utc = datetime.now(UTC)
                statement = select(Test).where(
                    col(Test.id).in_(test_ids), Test.customer_id == self.customer_id
                )
                update_result = await isolated_session.exec(statement)
                tests = update_result.all()

                for test in tests:
                    test.bugs_synced_at = now_utc
                    isolated_session.add(test)

                await isolated_session.commit()
            return
        else:
            # Fallback to self.session (legacy behavior)
            target_session = self.session  # type: ignore[assignment]
            should_commit = True

        # Bulk update using SQLModel
        now_utc = datetime.now(UTC)
        statement = select(Test).where(
            col(Test.id).in_(test_ids), Test.customer_id == self.customer_id
        )
        update_result = await target_session.exec(statement)
        tests = update_result.all()

        for test in tests:
            test.bugs_synced_at = now_utc
            target_session.add(test)

        if should_commit:
            await target_session.commit()

    async def _fetch_bugs_from_api(
        self, test_ids: list[int]
    ) -> tuple[list[dict[str, Any]], dict[int, int]]:
        """Fetch bugs from API only (no DB operations).

        This method is used by the decoupled API/DB pattern to fetch bugs
        concurrently while serializing DB writes.

        Args:
            test_ids: List of test identifiers to fetch bugs for

        Returns:
            Tuple of (bugs_data, bug_counts) where:
            - bugs_data: Raw API response list of bug dictionaries
            - bug_counts: Dict mapping test_id -> bug_count
        """
        if not test_ids:
            return [], {}

        test_ids_str = ",".join(str(tid) for tid in test_ids)
        response = await self.client.get(f"bugs?filter_test_cycle_ids={test_ids_str}")
        bugs_data: list[dict[str, Any]] = response.get("bugs", [])

        # Initialize bug counts for all test IDs (even if no bugs)
        bug_counts: dict[int, int] = dict.fromkeys(test_ids, 0)

        # Count bugs per test
        for bug in bugs_data:
            test_obj = bug.get("test", {})
            test_id = test_obj.get("id")
            if test_id in bug_counts:
                bug_counts[test_id] += 1

        return bugs_data, bug_counts

    async def _write_bugs_to_db(
        self, bugs_data: list[dict[str, Any]], test_ids: list[int]
    ) -> dict[int, int]:
        """Write bugs to DB using self.session (no API calls, no commit).

        This method handles:
        - User extraction and bulk upsert
        - Bug row construction with enriched status
        - Batch UPSERT to bugs table

        Caller must commit the transaction.

        Args:
            bugs_data: Raw bug data from API
            test_ids: List of test identifiers (for initializing counts)

        Returns:
            Dictionary mapping test_id -> bug_count
        """
        # Initialize bug counts for all test IDs (even if no bugs)
        bug_counts: dict[int, int] = dict.fromkeys(test_ids, 0)

        if not bugs_data:
            logger.debug(f"No bugs to write for {len(test_ids)} tests")
            return bug_counts

        # Step 1: Extract all unique usernames and raw_data from ALL bugs
        usernames: set[str] = set()
        raw_data_map: dict[str, dict[str, Any]] = {}

        for bug in bugs_data:
            author = bug.get("author", {})
            if author and isinstance(author, dict):
                username = author.get("name")
                if username:
                    usernames.add(username)
                    raw_data_map[username] = author

        # Step 2: Bulk upsert users (single IN query + single flush)
        user_id_map: dict[str, int] = {}
        if self.user_repo and usernames:
            user_id_map = await self.user_repo.bulk_upsert_users(
                usernames=usernames,
                user_type="tester",
                raw_data_map=raw_data_map,
            )

        # Step 3: Build bug rows with pre-known user IDs
        now_utc = datetime.now(UTC)
        bug_rows = []

        for bug in bugs_data:
            # Transform base fields (including rejection_reason)
            bug_orm_data = transform_api_bug_to_orm(bug)

            # Extract test_id from nested test object
            test_obj = bug.get("test", {})
            test_id = test_obj.get("id")

            # Extract test_feature_id for direct attribution (STORY-041)
            test_feature_data = bug.get("test_feature", {})
            test_feature_id = test_feature_data.get("id") if test_feature_data else None

            # Track count for this test
            if test_id in bug_counts:
                bug_counts[test_id] += 1

            # Get user ID from pre-computed map (no DB query needed)
            reported_by_user_id: int | None = None
            author = bug.get("author", {})
            if author and isinstance(author, dict):
                username = author.get("name")
                if username:
                    reported_by_user_id = user_id_map.get(username)

            # Enrich status for storage (STORY-047)
            api_status = bug.get("status")
            auto_accepted_flag = bug.get("auto_accepted")
            storage_status = _enrich_bug_status(api_status, auto_accepted_flag)
            bug_orm_data["status"] = storage_status

            # Add FKs and metadata
            bug_orm_data["customer_id"] = self.customer_id
            bug_orm_data["test_id"] = test_id
            bug_orm_data["test_feature_id"] = test_feature_id
            bug_orm_data["reported_by_user_id"] = reported_by_user_id
            bug_orm_data["synced_at"] = now_utc

            bug_rows.append(bug_orm_data)

        # Step 4: Batch UPSERT bugs (no nested queries)
        if bug_rows:
            stmt = sqlite_insert(Bug).values(bug_rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "customer_id": stmt.excluded.customer_id,
                    "test_id": stmt.excluded.test_id,
                    "test_feature_id": stmt.excluded.test_feature_id,
                    "title": stmt.excluded.title,
                    "severity": stmt.excluded.severity,
                    "status": stmt.excluded.status,
                    "actual_result": stmt.excluded.actual_result,
                    "expected_result": stmt.excluded.expected_result,
                    "rejection_reason": stmt.excluded.rejection_reason,
                    "steps": stmt.excluded.steps,
                    "reported_at": stmt.excluded.reported_at,
                    "raw_data": stmt.excluded.raw_data,
                    "synced_at": stmt.excluded.synced_at,
                    "reported_by_user_id": stmt.excluded.reported_by_user_id,
                    "known": stmt.excluded.known,
                },
            )
            await self.session.exec(stmt)  # type: ignore[union-attr]

        logger.debug(f"Wrote {len(bug_rows)} bugs for {len(test_ids)} tests to DB")
        return bug_counts

    async def _update_synced_at_in_session(self, test_ids: list[int]) -> None:
        """Update bugs_synced_at for tests in current session (no commit).

        Uses self.session directly - caller manages transaction.
        This is used for incremental persistence where bugs and timestamps
        are committed together atomically per batch.

        Args:
            test_ids: List of test identifiers to update
        """
        if not test_ids:
            return

        from sqlmodel import col

        from testio_mcp.models.orm.test import Test

        now_utc = datetime.now(UTC)
        statement = select(Test).where(
            col(Test.id).in_(test_ids), Test.customer_id == self.customer_id
        )
        result = await self.session.exec(statement)  # type: ignore[union-attr]
        tests = result.all()

        for test in tests:
            test.bugs_synced_at = now_utc
            self.session.add(test)  # type: ignore[union-attr]

        # No commit - caller manages transaction

    async def refresh_bugs(self, test_id: int) -> int:
        """Fetch fresh bugs from API, upsert to SQLite, return count.

        Uses UPSERT (merge) to update existing bugs or insert new ones.
        This prevents database lock contention with concurrent analytics queries.

        Pattern: Pre-fetch users to avoid nested flush issues (Codex review feedback).
        1. Fetch bugs from API
        2. Extract all unique usernames
        3. Bulk upsert users (single transaction, single flush)
        4. Build bug rows with pre-known user IDs
        5. Execute bug UPSERT

        Note: Caller must commit the transaction after this method.

        Args:
            test_id: Test identifier

        Returns:
            Number of bugs upserted

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        # Step 1: Fetch bugs from API
        response = await self.client.get(f"bugs?filter_test_cycle_ids={test_id}")
        bugs_data: list[dict[str, Any]] = response.get("bugs", [])

        # Use shared write logic (STORY-070 Refactor)
        # This ensures consistent field extraction (known, reported_at, etc.)
        counts = await self._write_bugs_to_db(bugs_data, [test_id])

        count = counts.get(test_id, 0)
        logger.debug(f"Refreshed {count} bugs for test {test_id}")
        return count

    async def refresh_bugs_batch(self, test_ids: list[int]) -> dict[int, int]:
        """Fetch fresh bugs for multiple tests in a single API call.

        More efficient than calling refresh_bugs() individually when processing
        multiple tests (e.g., EBR generation with 295 tests).

        Pattern: Pre-fetch users to avoid nested flush issues (Codex review feedback).
        1. Fetch bugs from API (single batch call)
        2. Extract all unique usernames from all bugs
        3. Bulk upsert users (single IN query + single flush)
        4. Build bug rows with pre-known user IDs
        5. Execute bug UPSERT (no nested queries)

        Note: Caller must commit the transaction after this method.

        Args:
            test_ids: List of test identifiers (10-15 recommended for optimal batching)

        Returns:
            Dictionary mapping test_id -> bug_count

        Raises:
            httpx.HTTPStatusError: If API request fails

        Example:
            >>> counts = await repo.refresh_bugs_batch([123, 124, 125])
            >>> counts
            {123: 5, 124: 12, 125: 3}
        """
        if not test_ids:
            return {}

        # Step 1: Fetch bugs from API (single batch call)
        test_ids_str = ",".join(str(tid) for tid in test_ids)
        response = await self.client.get(f"bugs?filter_test_cycle_ids={test_ids_str}")
        bugs_data: list[dict[str, Any]] = response.get("bugs", [])

        # Use shared write logic (STORY-070 Refactor)
        # This ensures consistent field extraction (known, reported_at, etc.)
        counts = await self._write_bugs_to_db(bugs_data, test_ids)

        logger.debug(
            f"Batch refreshed bugs for {len(test_ids)} tests: "
            f"total_bugs={len(bugs_data)}, counts={counts}"
        )
        return counts

    async def get_bug_by_id(self, bug_id: int) -> dict[str, Any] | None:
        """Get bug by ID with related entities (user, test, feature).

        STORY-085: Added for get_bug_summary tool.

        Fetches bug from SQLite with joins for:
        - reported_by_user (User table via reported_by_user_id FK)
        - test (Test table via test_id FK)
        - feature (TestFeature table via test_feature_id FK)

        Args:
            bug_id: Bug identifier

        Returns:
            Bug dictionary with core fields, detail fields, and related entities,
            or None if not found

        Example:
            >>> await repo.get_bug_by_id(12345)
            {
                "id": 12345,
                "title": "Login button not clickable",
                "severity": "critical",
                "status": "rejected",
                "known": False,
                "actual_result": "Button does not respond",
                "expected_result": "Button should navigate",
                "steps": "1. Navigate to login\\n2. Click button",
                "rejection_reason": "test_is_invalid",
                "reported_at": "2025-11-28T10:30:00Z",
                "reported_by_user": {"id": 123, "username": "john_doe"},
                "test": {"id": 109363, "title": "Homepage Test"},
                "feature": {"id": 456, "title": "User Login"}
            }
        """
        from testio_mcp.models.orm import Test, TestFeature, User

        # Query with joins for related entities
        stmt = (
            select(Bug, User, Test, TestFeature)
            .outerjoin(User, Bug.reported_by_user_id == User.id)  # type: ignore[arg-type]
            .join(Test, Bug.test_id == Test.id)  # type: ignore[arg-type]
            .outerjoin(TestFeature, Bug.test_feature_id == TestFeature.id)  # type: ignore[arg-type]
            .where(Bug.id == bug_id, Bug.customer_id == self.customer_id)
        )

        result = await self.session.exec(stmt)  # type: ignore[union-attr]
        row = result.first()

        if not row:
            return None

        # Unpack row (Bug, User | None, Test, TestFeature | None)
        bug, user, test, feature = row

        # Build response with core fields, detail fields, and related entities
        bug_dict: dict[str, Any] = {
            "id": bug.id,
            "title": bug.title,
            "severity": bug.severity,
            "status": bug.status,
            "known": bug.known,
            "actual_result": bug.actual_result,
            "expected_result": bug.expected_result,
            "steps": bug.steps,
            "rejection_reason": bug.rejection_reason,
            "reported_at": bug.reported_at.isoformat() if bug.reported_at else None,
        }

        # Add related entities (AC2)
        if user:
            bug_dict["reported_by_user"] = {"id": user.id, "username": user.username}
        else:
            bug_dict["reported_by_user"] = None

        # Test is always present (INNER JOIN)
        # Deserialize test.data JSON string to access title
        test_data = json.loads(test.data) if isinstance(test.data, str) else test.data
        bug_dict["test"] = {
            "id": test.id,
            "title": test_data.get("title", "Untitled Test"),
        }

        # Feature may be None
        if feature:
            bug_dict["feature"] = {"id": feature.id, "title": feature.title}
        else:
            bug_dict["feature"] = None

        return bug_dict

    async def list_bugs(
        self,
        test_ids: list[int],
        status: list[str] | None = None,
        severity: list[str] | None = None,
        rejection_reason: list[str] | None = None,
        reported_by_user_id: int | None = None,
        page: int = 1,
        per_page: int = 100,
        offset: int = 0,
        sort_by: str = "reported_at",
        sort_order: str = "desc",
    ) -> tuple[list[dict[str, Any]], int]:
        """Query bugs for specified tests with filtering, pagination, and sorting.

        Scoped to specific test_ids to prevent mass data fetch. Filters are combined
        with AND logic. Returns minimal bug representation for quick listing.

        Args:
            test_ids: List of test identifiers to scope query (required)
            status: Optional filter by bug status (accepted, rejected, forwarded, etc.)
            severity: Optional filter by bug severity level
            rejection_reason: Optional filter by rejection reason
            reported_by_user_id: Optional filter by reporting user ID
            page: Page number (1-indexed) for pagination
            per_page: Number of items per page
            offset: Starting offset (0-indexed)
            sort_by: Field to sort by (reported_at, severity, status, title)
            sort_order: Sort order (asc or desc)

        Returns:
            Tuple of (bugs_list, total_count):
                - bugs_list: List of bug dicts with id, title, severity, status, test_id,
                  reported_at
                - total_count: Total number of bugs matching query (across all pages)
        """
        from sqlmodel import col, desc

        # Build base query
        statement = select(Bug).where(
            col(Bug.test_id).in_(test_ids),
            Bug.customer_id == self.customer_id,
        )

        # Apply filters with AND logic
        if status:
            statement = statement.where(col(Bug.status).in_(status))
        if severity:
            statement = statement.where(col(Bug.severity).in_(severity))
        if rejection_reason:
            statement = statement.where(col(Bug.rejection_reason).in_(rejection_reason))
        if reported_by_user_id is not None:
            statement = statement.where(Bug.reported_by_user_id == reported_by_user_id)

        # Get total count before pagination
        count_statement = select(func.count("*")).where(
            col(Bug.test_id).in_(test_ids),
            Bug.customer_id == self.customer_id,
        )
        if status:
            count_statement = count_statement.where(col(Bug.status).in_(status))
        if severity:
            count_statement = count_statement.where(col(Bug.severity).in_(severity))
        if rejection_reason:
            count_statement = count_statement.where(col(Bug.rejection_reason).in_(rejection_reason))
        if reported_by_user_id is not None:
            count_statement = count_statement.where(Bug.reported_by_user_id == reported_by_user_id)

        count_result = await self.session.exec(count_statement)  # type: ignore[union-attr]
        total_count = count_result.one()

        # Apply sorting
        if sort_by == "severity":
            order_expr: Any = Bug.severity
        elif sort_by == "status":
            order_expr = Bug.status
        elif sort_by == "title":
            order_expr = Bug.title
        else:
            # Default to reported_at
            order_expr = Bug.reported_at

        if sort_order == "desc":
            statement = statement.order_by(desc(order_expr))
        else:
            statement = statement.order_by(order_expr)

        # Apply pagination
        actual_offset = offset + (page - 1) * per_page
        statement = statement.offset(actual_offset).limit(per_page)

        # Execute query
        result = await self.session.exec(statement)  # type: ignore[union-attr]
        bugs_orm = result.all()

        # Transform ORM models to dictionaries with minimal fields
        bugs: list[dict[str, Any]] = []
        for bug_orm in bugs_orm:
            bugs.append(
                {
                    "id": str(bug_orm.id),
                    "title": bug_orm.title,
                    "severity": bug_orm.severity,
                    "status": bug_orm.status,
                    "test_id": bug_orm.test_id,
                    "reported_at": bug_orm.reported_at.isoformat() if bug_orm.reported_at else None,
                }
            )

        return bugs, total_count

    async def delete_bugs_for_test(self, test_id: int) -> None:
        """Delete all bugs for a specific test.

        Note: Caller must commit the transaction after this method.

        Args:
            test_id: Test identifier
        """
        del_statement = delete(Bug).where(
            Bug.test_id == test_id,  # type: ignore[arg-type]
            Bug.customer_id == self.customer_id,  # type: ignore[arg-type]
        )
        await self.session.exec(del_statement)  # type: ignore[union-attr]
        # Caller commits (transaction management delegated)
