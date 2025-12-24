---
story_id: STORY-024
epic_id: EPIC-004
title: SQLite-First Bug Strategy - Intelligent Bug Caching
status: Ready for Development (v1.4 - Codex Reviewed)
created: 2025-01-18
updated: 2025-01-18
estimate: 2.5 story points (2.5 days)
assignee: dev
dependencies: [STORY-023e]
priority: high
peer_review: Codex (2025-01-18) - Approved with critical architectural fixes applied
---

## Story

**As a** CSM or QA Lead
**I want** bug data to be cached intelligently in SQLite based on test mutability
**So that** I can generate EBR reports 4x faster and reduce API quota consumption by 80%

## Context

**Current Problem (Post STORY-023e):**
- EBR tool always fetches fresh bugs from API for ALL tests (295 tests ÷ 5 per batch = 59 API calls)
- Locked/archived tests have **immutable bugs** - statuses won't change
- Wasting API quota and time (30-45 seconds per EBR)
- No concept of "staleness" for bug data

**Architecture Insight:**
We already have this pattern for **test data**:
- `tests.synced_at` tracks when test metadata was refreshed
- `cache.refresh_active_tests()` only updates **mutable tests** (not locked/cancelled)
- Immutable tests are never refreshed (STORY-021g)

**This story extends the same pattern to bug data:**
- Track `tests.bugs_synced_at` - when bugs were last fetched for this test
- Implement intelligent caching: immutable tests use SQLite, mutable tests check staleness
- Integrate with existing sync workflows (initial, hybrid, force)

## Acceptance Criteria

### AC1: Add Per-Test Bug Sync Tracking

**Schema Migration (Version 4):**
- [ ] Add `bugs_synced_at TIMESTAMP` column to `tests` table
- [ ] Create migration function `migrate_to_v4()` in `schema.py`
- [ ] Increment `CURRENT_SCHEMA_VERSION` to 4
- [ ] Add explicit migration orchestration to `initialize_schema()`
- [ ] Ensure schema version only advances after column exists

**Schema DDL:**
```sql
ALTER TABLE tests ADD COLUMN bugs_synced_at TIMESTAMP;
```

**Migration Function:**
```python
async def migrate_to_v4(db: aiosqlite.Connection) -> None:
    """Add per-test bug sync tracking.

    Migration: Add bugs_synced_at column to tests table for intelligent
    bug caching based on test mutability.
    """
    current_version = await get_schema_version(db)
    if current_version >= 4:
        return  # Already migrated

    logger.info("Migrating schema from v3 to v4: Adding bugs_synced_at to tests")
    await db.execute("ALTER TABLE tests ADD COLUMN bugs_synced_at TIMESTAMP")
    await db.commit()
    await set_schema_version(db, 4)
    logger.info("Migrated to schema version 4: Added bugs_synced_at to tests")
```

**Migration Orchestration (CRITICAL - Codex Review):**
```python
async def initialize_schema(db: aiosqlite.Connection) -> None:
    """Initialize database schema with migration orchestration.

    IMPORTANT: Do NOT blindly set schema_version to CURRENT_SCHEMA_VERSION
    without ensuring the physical schema (tables/columns) matches.
    """
    # Create tables if missing (idempotent)
    await db.execute("CREATE TABLE IF NOT EXISTS tests ...")
    await db.execute("CREATE TABLE IF NOT EXISTS bugs ...")
    # ... other tables ...

    # Get current version BEFORE applying migrations
    current_version = await get_schema_version(db)

    # Run migrations sequentially
    if current_version < 4:
        await migrate_to_v4(db)
        # migrate_to_v4 sets version to 4 internally

    # For brand new databases (version 0), create all columns upfront
    if current_version == 0:
        # Tables already created with all v4 columns
        await set_schema_version(db, CURRENT_SCHEMA_VERSION)
```

**Integration:**
- [ ] Update `initialize_schema()` with explicit migration orchestration
- [ ] Ensure version only advances after physical schema matches
- [ ] Update `check_schema_compatibility()` to handle version 4
- [ ] Test migration on existing v3 database (backward compatible)

### AC2: Add Mutability Constants to Centralized Config

**Update `src/testio_mcp/config.py` (Pydantic Settings):**
- [ ] Add `MUTABLE_TEST_STATUSES` as a ClassVar constant (list[str])
- [ ] Add `IMMUTABLE_TEST_STATUSES` as a ClassVar constant (list[str])
- [ ] Add `BUG_CACHE_TTL_SECONDS` Field with env overlay
- [ ] Add `BUG_CACHE_ENABLED` Field with env overlay
- [ ] Add `BUG_CACHE_BYPASS` Field with env overlay (debug only, bug-specific)
- [ ] Add comprehensive docstrings explaining mutability semantics

**Configuration Updates in Settings Class:**
```python
from typing import ClassVar

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ... existing fields ...

    # Bug Caching Configuration (STORY-024)
    BUG_CACHE_TTL_SECONDS: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Staleness threshold for mutable test bugs in seconds. "
        "Mutable tests (running, locked, customer_finalized, etc.) refresh bugs "
        "if older than this threshold. Immutable tests (archived, cancelled) "
        "never refresh. Default: 3600 (1 hour).",
    )
    BUG_CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable/disable bug caching entirely. "
        "When False, bugs are always fetched from API. "
        "Default: True (caching enabled).",
    )
    BUG_CACHE_BYPASS: bool = Field(
        default=False,
        description="⚠️ DEBUG ONLY: Bypass bug caching (behaves as if force_refresh=True). "
        "When enabled, bug data is always refreshed from API on every read. "
        "Logs warning when active. Use for debugging stale bug data issues. "
        "Note: Currently applies only to bug caching; test caching unaffected. "
        "Default: False (caching enabled).",
    )

    # Test Mutability Constants (ClassVar - not env-configurable)
    # These match the pattern in cache.py and test_repository.py
    MUTABLE_TEST_STATUSES: ClassVar[list[str]] = [
        "customer_finalized",  # Customer review phase, can still change
        "waiting",             # Waiting to start
        "running",             # Test actively running, bugs being reported
        "locked",              # Finalized but not archived yet (still mutable!)
        "initialized",         # Test created but not started
    ]

    IMMUTABLE_TEST_STATUSES: ClassVar[list[str]] = [
        "archived",   # Test completed and archived (final state)
        "cancelled",  # Test cancelled (final state)
    ]
```

**Rationale (CORRECTED per cache.py pattern):**
- **Immutable (archived, cancelled ONLY):** Tests in final state, bugs frozen forever
- **Mutable (includes locked!):** Tests where bugs can still change
  - `locked`: Finalized but not archived yet - bug statuses can still change during review period
  - `customer_finalized`: Customer review phase
  - `running`: Active test, bugs being reported
  - `waiting`: Test scheduled but not started
  - `initialized`: Test created but not started
- **Environment overlays:** TTL and cache toggles configurable, statuses are constants
- **Consistency:** Aligns with existing `cache.py` and `test_repository.py` patterns

**Update cache.py to consume Settings:**
- [ ] Import `settings` from `config.py`
- [ ] Replace hard-coded status lists with `settings.MUTABLE_TEST_STATUSES`
- [ ] Use in `refresh_active_tests()` and `get_mutable_tests()` calls

### AC3: Implement Intelligent Bug Caching

**Update `BugRepository` with batch-aware caching method:**
- [ ] Add `get_bugs_cached_or_refresh()` method (accepts single or multiple test IDs)
- [ ] Implement cache vs API decision logic (batch-aware)
- [ ] Update `bugs_synced_at` timestamp on refresh
- [ ] Handle force_refresh parameter
- [ ] Batch API calls for tests that need refreshing

**Single Method Design (simpler API):**
```python
# Single test
bugs = await repo.get_bugs_cached_or_refresh([123])

# Multiple tests (batch)
bugs_map = await repo.get_bugs_cached_or_refresh([123, 124, 125])
```

**Method Signature:**
```python
async def get_bugs_cached_or_refresh(
    self,
    test_ids: list[int],
    force_refresh: bool = False,
) -> dict[int, list[dict[str, Any]]]:
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

    Returns:
        Dictionary mapping test_id -> list of bug dicts
        Example: {123: [{bug1}, {bug2}], 124: [{bug3}]}

    Performance:
        - Single test cache hit: ~10ms (SQLite query)
        - Batch (295 tests, 80% cache hit): ~12 seconds vs ~45 seconds (4x faster)
        - Immutable tests: Always cache hit (no API calls)
    """
```

**Implementation Logic (Batch-Aware):**
```python
async def get_bugs_cached_or_refresh(
    self,
    test_ids: list[int],
    force_refresh: bool = False,
) -> dict[int, list[dict[str, Any]]]:
    """Get bugs with intelligent caching (batch-aware)."""
    from datetime import datetime, UTC
    from testio_mcp.config import settings

    if not test_ids:
        return {}

    # 1. Bulk query: Get test statuses and bugs_synced_at for all test IDs
    placeholders = ",".join("?" * len(test_ids))
    cursor = await self.db.execute(
        f"""
        SELECT id, status, bugs_synced_at
        FROM tests
        WHERE id IN ({placeholders}) AND customer_id = ?
        """,
        (*test_ids, self.customer_id),
    )
    rows = await cursor.fetchall()
    test_metadata = {row[0]: {"status": row[1], "bugs_synced_at": row[2]} for row in rows}

    # 2. Determine which tests need refreshing
    tests_to_refresh: list[int] = []
    now = datetime.now(UTC)

    for test_id in test_ids:
        metadata = test_metadata.get(test_id)

        if not metadata:
            # Test not in DB - need to refresh (will likely 404 from API)
            tests_to_refresh.append(test_id)
            logger.warning(f"Test {test_id} not in database, will attempt API refresh")
            continue

        test_status = metadata["status"]
        bugs_synced_at_str = metadata["bugs_synced_at"]

        # Parse bugs_synced_at timestamp
        bugs_synced_at: datetime | None = None
        if bugs_synced_at_str:
            try:
                bugs_synced_at = datetime.strptime(bugs_synced_at_str, "%Y-%m-%d %H:%M:%S")
                bugs_synced_at = bugs_synced_at.replace(tzinfo=UTC)
            except ValueError:
                logger.warning(f"Invalid bugs_synced_at for test {test_id}, will refresh")

        # Apply decision logic (same priority order as before)
        should_refresh = False

        if settings.BUG_CACHE_BYPASS:
            should_refresh = True
            logger.warning(f"BUG_CACHE_BYPASS active - forcing refresh for test {test_id}")
        elif force_refresh:
            should_refresh = True
        elif not settings.BUG_CACHE_ENABLED:
            should_refresh = True
        elif bugs_synced_at is None:
            # Never synced - MUST fetch
            should_refresh = True
        elif test_status in settings.IMMUTABLE_TEST_STATUSES:
            # Immutable (archived/cancelled) - use cache
            should_refresh = False
        elif test_status in settings.MUTABLE_TEST_STATUSES:
            # Mutable - check staleness
            seconds_since_sync = (now - bugs_synced_at).total_seconds()
            should_refresh = seconds_since_sync > settings.BUG_CACHE_TTL_SECONDS
        else:
            # Unknown status - default to refresh (defensive)
            should_refresh = True
            logger.warning(f"Test {test_id} has unknown status '{test_status}'")

        if should_refresh:
            tests_to_refresh.append(test_id)

    # 3. Batch refresh tests that need it (existing method)
    if tests_to_refresh:
        logger.debug(
            f"Refreshing bugs for {len(tests_to_refresh)}/{len(test_ids)} tests "
            f"(cache hit: {len(test_ids) - len(tests_to_refresh)})"
        )

        # Batch API calls (15 tests per batch, using existing method)
        BATCH_SIZE = 15
        batches = [
            tests_to_refresh[i : i + BATCH_SIZE]
            for i in range(0, len(tests_to_refresh), BATCH_SIZE)
        ]
        await asyncio.gather(*[self.refresh_bugs_batch(batch) for batch in batches])

        # Bulk update bugs_synced_at
        await self._update_bugs_synced_at_batch(tests_to_refresh)

    # 4. Return bugs for ALL requested test IDs from SQLite
    result: dict[int, list[dict[str, Any]]] = {}
    for test_id in test_ids:
        result[test_id] = await self.get_bugs(test_id)

    return result

async def _update_bugs_synced_at_batch(self, test_ids: list[int]) -> None:
    """Update bugs_synced_at timestamp for multiple tests (bulk update)."""
    if not test_ids:
        return

    # Use CASE statement for efficient bulk update
    placeholders = ",".join("?" * len(test_ids))
    await self.db.execute(
        f"""
        UPDATE tests
        SET bugs_synced_at = CURRENT_TIMESTAMP
        WHERE id IN ({placeholders}) AND customer_id = ?
        """,
        (*test_ids, self.customer_id),
    )
    await self.db.commit()
```

### AC4: Update MultiTestReportService

**Replace always-refresh pattern with intelligent caching:**
- [ ] Remove batch refresh logic (lines 212-240)
- [ ] Use batch-aware `get_bugs_cached_or_refresh()` instead
- [ ] Add optional `force_refresh_bugs` parameter to service method
- [ ] Update docstrings

**Before (STORY-023e - Always refresh all bugs):**
```python
# Lines 212-240: Always fetch fresh bugs from API (295 tests ÷ 5 per batch = 59 API calls)
BATCH_SIZE = 5  # Old batch size
batches = [valid_test_ids[i:i + BATCH_SIZE] for i in range(0, len(valid_test_ids), BATCH_SIZE)]
await asyncio.gather(*[self.bug_repo.refresh_bugs_batch(batch) for batch in batches])

# Then loop through tests and get bugs from SQLite
for test in tests:
    bugs = await self.bug_repo.get_bugs(test.id)
    # ... classify and aggregate
```

**After (STORY-024 - Intelligent batch caching):**
```python
# Extract valid test IDs
test_id_map = {}
for test in tests:
    test_id = test.get("id")
    if test_id is None:
        logger.warning(f"Test missing ID, skipping: {test.get('title', 'Untitled')}")
        continue
    test_id_map[test_id] = test

valid_test_ids = list(test_id_map.keys())

# Batch-aware caching: one call handles all cache decisions + batched refreshes
bugs_by_test = await self.bug_repo.get_bugs_cached_or_refresh(
    test_ids=valid_test_ids,
    force_refresh=force_refresh_bugs  # Pass through from service parameter
)

# Now loop through and classify bugs (bugs already fetched/cached)
for test_id, test in test_id_map.items():
    bugs = bugs_by_test[test_id]
    # ... classify and aggregate bugs as before
```

**Performance Improvement:**
- Immutable tests (80%): SQLite cache (~2.4s for 236 tests)
- Mutable tests (20%): API refresh (~10s for 59 tests)
- **Total: ~12s vs ~45s (4x faster)**

**Service Signature Update:**
```python
async def generate_ebr_report(
    self,
    product_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
    statuses: list[str] | None = None,
    force_refresh_bugs: bool = False,  # NEW parameter
) -> dict[str, Any]:
    """Generate Executive Bug Report for a product.

    Args:
        product_id: Product to report on
        start_date: Start date (ISO 8601, relative, or natural language)
        end_date: End date (ISO 8601, relative, or natural language)
        statuses: Filter tests by status (e.g., ["locked", "running"])
        force_refresh_bugs: Bypass cache and fetch all bugs from API (default: False)
                           Use when you need guaranteed fresh data

    Returns:
        EBR report with summary, per-test metrics, and trends

    Performance:
        - With cache (typical): ~12 seconds for 295 tests
        - With force_refresh: ~30-45 seconds (same as before)
    """
```

### AC5: Update MCP Tool

**Add `force_refresh_bugs` parameter to `generate_ebr_report` tool:**
- [ ] Add boolean parameter to tool signature
- [ ] Pass through to service
- [ ] Document in tool docstring

**Tool Signature:**
```python
@mcp.tool()
async def generate_ebr_report(
    product_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
    statuses: list[str] | None = None,
    force_refresh_bugs: bool = False,  # NEW parameter
    ctx: Context,
) -> dict:
    """Generate Executive Bug Report for a product.

    Aggregates bug metrics across multiple tests with flexible date filtering
    and status filtering. Useful for quality assessments and trend analysis.

    **Performance Note:** This tool uses intelligent bug caching. Bugs for
    immutable tests (locked/cancelled/archived) are cached in SQLite and never
    refreshed. Bugs for mutable tests (running/in_review) are refreshed if stale
    (>1 hour old). Use force_refresh_bugs=true for guaranteed fresh data.

    For large result sets (100+ tests), execution may take 10-30 seconds.
    Recommended MCP client timeout: 60-90 seconds for comprehensive reports.

    Args:
        product_id: Product ID from TestIO (e.g., 598). Use list_products to find IDs.
        start_date: Start date for filtering tests (flexible formats supported).
                   ISO 8601: '2024-01-01' | Business terms: 'today', 'yesterday',
                   'last 30 days', 'this quarter', 'last year' | Relative: '3 days ago',
                   'last 7 days' | Omit to include all tests from the beginning of time.
        end_date: End date for filtering tests (flexible formats supported).
                 Same format options as start_date. Omit to include all tests
                 through present.
        statuses: Filter tests by lifecycle status. Pass as comma-separated string:
                 statuses="running,locked" or JSON array: statuses=["running", "locked"].
                 Valid values: running, locked, archived, cancelled, customer_finalized,
                 initialized. Common patterns: "locked" for completed tests, "running"
                 for active tests. Omit to include all statuses.
        force_refresh_bugs: Bypass cache and fetch all bugs from API (default: false).
                           Set to true when you need guaranteed fresh bug data.
                           WARNING: Significantly slower (4x) for large reports.
        ctx: FastMCP context (injected automatically)

    Returns:
        EBR report with summary metrics and per-test breakdown

    Performance:
        - Cached (typical): ~12 seconds for 295 tests (80% cache hits)
        - Force refresh: ~30-45 seconds (all API calls)

    Common use cases:
        - Quarterly reviews: start_date="this quarter", statuses=["locked"]
        - Last 30 days: start_date="last 30 days"
        - Year-to-date: start_date="2024-01-01", end_date="today"
        - All completed tests: statuses=["locked", "archived"]
        - Fresh data audit: force_refresh_bugs=true (slow but guaranteed current)
    """
```

### AC6: Service-Owned Bug Caching (Architecture Alignment)

**CRITICAL DESIGN DECISION (Codex Review):**
Keep bug caching **service-owned**, NOT wired into `PersistentCache` sync methods.

**Rationale:**
- `PersistentCache` owns **test** sync only (current architecture)
- `BugRepository` is a service-layer dependency (separate from cache)
- Wiring bug refresh into `PersistentCache.initial_sync` or `refresh_active_cycle` would:
  - Violate service layer architecture (cache shouldn't know about bugs)
  - Reintroduce long-running syncs (defeats on-demand caching goal)
  - Create tight coupling between cache and bug repository

**Architecture Pattern:**
```
PersistentCache (cache.py)
  ↓ manages test metadata only
TestRepository
  ↓ provides test data to services

MultiTestReportService (service layer)
  ↓ owns bug aggregation logic
BugRepository
  ↓ provides intelligent bug caching (STORY-024)
```

**Service-Owned Bug Caching (AC6):**
- [ ] `MultiTestReportService.generate_ebr_report()` uses `bug_repo.get_bugs_cached_or_refresh()`
- [ ] Bug caching is **on-demand** (triggered when EBR needs bug data)
- [ ] No changes to `PersistentCache` sync methods (test sync only)
- [ ] If background bug priming is needed later, create dedicated `BugSyncService`

**Implementation (already in AC4):**
```python
# MultiTestReportService.generate_ebr_report()
# Extract valid test IDs from query
valid_test_ids = [test.get("id") for test in tests if test.get("id")]

# Batch-aware caching: one call handles all cache decisions + batched refreshes
bugs_by_test = await self.bug_repo.get_bugs_cached_or_refresh(
    test_ids=valid_test_ids,
    force_refresh=force_refresh_bugs  # User override
)

# Now loop through and classify bugs (already fetched/cached)
for test_id in valid_test_ids:
    bugs = bugs_by_test[test_id]
    # ... classify and aggregate
```

**What NOT to do (anti-pattern):**
```python
# ❌ DON'T add bug refresh to PersistentCache
async def initial_sync(self):
    await self.sync_product_tests(...)
    # ❌ DON'T: await bug_repo.refresh_bugs_batch(all_test_ids)
```

**Future Background Bug Priming (Optional):**
If background bug refresh is needed (e.g., nightly warmup):
- Create separate `BugSyncService` (composes `PersistentCache` + `BugRepository`)
- Keep as optional background task (not in critical path)
- Don't wire into `PersistentCache.initial_sync` (keeps cache lightweight)

### AC7: Comprehensive Testing

**Unit Tests (`tests/unit/test_bug_repository.py`):**
- [ ] Test intelligent caching logic
- [ ] Test immutable tests always use cache
- [ ] Test mutable tests check staleness
- [ ] Test force_refresh bypasses cache
- [ ] Test bugs_synced_at timestamp updates

**Service Tests (`tests/unit/test_multi_test_report_service.py`):**
- [ ] Test EBR with cached bugs (fast path)
- [ ] Test EBR with force_refresh (slow path)
- [ ] Mock repository to verify cache behavior

**Integration Tests (`tests/integration/test_bug_caching_integration.py`):**
- [ ] Test end-to-end caching with real database
- [ ] Verify immutable tests skip API calls
- [ ] Verify mutable tests refresh when stale
- [ ] Measure performance improvement

**Schema Migration Tests (`tests/unit/test_schema_migrations.py`):**
- [ ] Test migration from v3 to v4
- [ ] Test backward compatibility
- [ ] Test idempotent migration (run twice)

### AC8: Documentation Updates

- [ ] Update `CLAUDE.md` with bug caching strategy
- [ ] Update `docs/architecture/ARCHITECTURE.md` with caching details
- [ ] Add performance metrics to README
- [ ] Document `force_refresh_bugs` parameter usage

## Tasks

### Task 1: Schema Migration (3 hours)

**Schema changes:**
- [x] Update `CURRENT_SCHEMA_VERSION` to 4 in `schema.py`
- [x] Add `bugs_synced_at` column to tests table in `initialize_schema()`
- [x] Create `migrate_to_v4()` function
- [x] Update schema version check logic
- [x] Test migration on existing database

**Migration testing:**
- [x] Create test database with v3 schema
- [x] Apply v4 migration
- [x] Verify column added successfully
- [x] Verify existing data preserved
- [x] Test idempotent migration (run twice)

### Task 2: Add Configuration Settings (1 hour)

**Update Pydantic Settings (v1.2+ - no standalone constants.py):**
- [ ] Add `MUTABLE_TEST_STATUSES` as ClassVar to `Settings` class
- [ ] Add `IMMUTABLE_TEST_STATUSES` as ClassVar to `Settings` class
- [ ] Add `BUG_CACHE_TTL_SECONDS` Field with env overlay
- [ ] Add `BUG_CACHE_ENABLED` Field with env overlay
- [ ] Add `BUG_CACHE_BYPASS` Field with env overlay (debug only)
- [ ] Add comprehensive docstrings explaining mutability semantics
- [ ] Import `settings` in `BugRepository` and service modules

### Task 3: Implement Intelligent Caching (4 hours)

**Repository changes:**
- [x] Add `get_bugs_cached_or_refresh()` to `BugRepository`
- [x] Add `_update_bugs_synced_at()` helper method
- [x] Implement cache vs API decision logic
- [x] Handle edge cases (test not found, invalid timestamps)
- [x] Add debug logging for cache hits/misses

**Decision logic:**
- [x] Check test status (mutable vs immutable)
- [x] Check bugs_synced_at timestamp
- [x] Calculate staleness for mutable tests
- [x] Respect force_refresh parameter
- [x] Update timestamp after refresh

### Task 4: Update MultiTestReportService (2 hours)

**Service changes:**
- [x] Remove batch refresh logic
- [x] Add `force_refresh_bugs` parameter
- [x] Use `get_bugs_cached_or_refresh()` in loop
- [x] Update docstrings with performance notes
- [x] Add logging for cache statistics

**Performance tracking:**
- [x] Track cache hits vs misses
- [x] Log performance metrics
- [x] Add cache hit ratio to debug output

### Task 5: Update MCP Tool (1 hour)

**Tool changes:**
- [x] Add `force_refresh_bugs` parameter
- [x] Pass through to service
- [x] Update docstring with performance notes
- [x] Add usage examples

### Task 6: Service-Owned Bug Caching (1 hour)

**Service integration (v1.4 - no PersistentCache changes):**
- [ ] Verify `MultiTestReportService` uses `bug_repo.get_bugs_cached_or_refresh()`
- [ ] Verify no bug refresh logic added to `PersistentCache` sync methods
- [ ] Test on-demand bug caching with EBR tool
- [ ] Document service-owned pattern for future bug-aware services

### Task 7: Testing (6 hours)

**Unit tests:**
- [x] Repository caching logic tests (8 tests)
- [x] Service tests with mocked repository (4 tests)
- [x] Schema migration tests (3 tests)

**Integration tests:**
- [x] End-to-end caching tests (5 tests)
- [x] Performance measurement tests (2 tests)
- [x] Sync workflow integration tests (3 tests)

**Coverage target:** 90%+ for new code

### Task 8: Documentation (2 hours)

**Documentation updates:**
- [x] Update CLAUDE.md with caching strategy
- [x] Update ARCHITECTURE.md
- [x] Add performance benchmarks
- [x] Document force_refresh usage patterns

## Testing

### Unit Tests - Bug Repository Caching

```python
# tests/unit/test_bug_repository_caching.py

@pytest.mark.unit
@pytest.mark.asyncio
async def test_immutable_test_always_uses_cache():
    """Verify locked tests never refresh bugs (unless forced)."""
    mock_db = AsyncMock()
    mock_client = AsyncMock()

    # Mock test status: locked (immutable)
    mock_db.execute.return_value.fetchone.return_value = (
        "locked",  # status
        "2024-01-01 00:00:00"  # bugs_synced_at (10 days ago)
    )

    repo = BugRepository(db=mock_db, client=mock_client, customer_id=123)

    # Should use cache (no API call)
    await repo.get_bugs_cached_or_refresh(test_id=456)

    # Verify: No refresh_bugs call (client not called)
    mock_client.get.assert_not_called()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_mutable_test_refreshes_when_stale():
    """Verify running tests refresh if bugs are stale (>1 hour)."""
    mock_db = AsyncMock()
    mock_client = AsyncMock()

    # Mock test status: running (mutable)
    # bugs_synced_at: 2 hours ago (stale)
    stale_time = (datetime.now(UTC) - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    mock_db.execute.return_value.fetchone.return_value = ("running", stale_time)

    repo = BugRepository(db=mock_db, client=mock_client, customer_id=123)

    # Should refresh (API call)
    await repo.get_bugs_cached_or_refresh(test_id=456)

    # Verify: refresh_bugs was called
    mock_client.get.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_force_refresh_bypasses_cache():
    """Verify force_refresh always fetches from API."""
    mock_db = AsyncMock()
    mock_client = AsyncMock()

    # Mock test status: locked (immutable) with fresh bugs
    mock_db.execute.return_value.fetchone.return_value = (
        "locked",
        datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")  # Fresh
    )

    repo = BugRepository(db=mock_db, client=mock_client, customer_id=123)

    # Force refresh should call API even for immutable test
    await repo.get_bugs_cached_or_refresh(test_id=456, force_refresh=True)

    # Verify: API was called despite fresh cache
    mock_client.get.assert_called_once()
```

### Integration Tests - Performance

```python
# tests/integration/test_bug_caching_performance.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_ebr_performance_with_caching():
    """Measure EBR performance with intelligent caching."""
    # Setup: Create 100 tests (80 locked, 20 running)
    # Sync bugs for all tests (populate cache)

    # Run EBR with caching (should be fast)
    start = time.time()
    report = await service.generate_ebr_report(
        product_id=598,
        force_refresh_bugs=False  # Use cache
    )
    cached_duration = time.time() - start

    # Run EBR with force refresh (slow path)
    start = time.time()
    report_fresh = await service.generate_ebr_report(
        product_id=598,
        force_refresh_bugs=True  # Force API
    )
    forced_duration = time.time() - start

    # Verify: Cached is significantly faster (4x)
    assert cached_duration < forced_duration / 3
    assert cached_duration < 15  # <15 seconds for 100 tests

    # Verify: Same results (data consistency)
    assert report["summary"]["total_bugs"] == report_fresh["summary"]["total_bugs"]
```

### Schema Migration Tests

```python
# tests/unit/test_schema_migrations.py

@pytest.mark.unit
@pytest.mark.asyncio
async def test_migrate_v3_to_v4():
    """Verify migration from schema v3 to v4."""
    # Create v3 database
    db = await create_test_database(version=3)

    # Apply migration
    await migrate_to_v4(db)

    # Verify: Column added
    cursor = await db.execute("PRAGMA table_info(tests)")
    columns = await cursor.fetchall()
    column_names = [col[1] for col in columns]
    assert "bugs_synced_at" in column_names

    # Verify: Version updated
    version = await get_schema_version(db)
    assert version == 4

    # Verify: Idempotent (run twice)
    await migrate_to_v4(db)  # Should not error
    version = await get_schema_version(db)
    assert version == 4

@pytest.mark.unit
@pytest.mark.asyncio
async def test_existing_data_preserved_after_migration():
    """Verify existing test data is preserved during migration."""
    # Create v3 database with test data
    db = await create_test_database(version=3)
    await db.execute(
        "INSERT INTO tests (id, customer_id, product_id, data, status) VALUES (?, ?, ?, ?, ?)",
        (123, 1, 598, '{"title": "Test"}', "locked")
    )
    await db.commit()

    # Apply migration
    await migrate_to_v4(db)

    # Verify: Data still exists
    cursor = await db.execute("SELECT id, status FROM tests WHERE id = 123")
    row = await cursor.fetchone()
    assert row[0] == 123
    assert row[1] == "locked"

    # Verify: New column is NULL (not set yet)
    cursor = await db.execute("SELECT bugs_synced_at FROM tests WHERE id = 123")
    row = await cursor.fetchone()
    assert row[0] is None
```

## Implementation Notes

### Mutability Semantics (CORRECTED per cache.py)

**Immutable Test Statuses (bugs frozen - ONLY these two):**
- `archived`: Test completed and archived (final state, bugs frozen forever)
- `cancelled`: Test cancelled (final state, bugs frozen forever)

**Mutable Test Statuses (bugs can still change):**
- `customer_finalized`: Customer review phase, bugs may be updated
- `waiting`: Test scheduled but not started
- `running`: Test actively running, bugs being reported
- `locked`: **Finalized but not archived yet** - bugs can still change during review period!
- `initialized`: Test created but not started

**Key Insight:**
`locked` is **MUTABLE**, not immutable! Tests are auto-locked 4-6 weeks after `end_at`, but bug statuses can still change during the review period. Only when tests are `archived` or `cancelled` do bugs become truly immutable.

This aligns with existing patterns in:
- `cache.py:718,1783` - "Immutable tests: archived, cancelled"
- `test_repository.py:240-242` - Same definition
- `test_repository.py:256` - SQL: `status IN ('customer_finalized', 'waiting', 'running', 'locked', 'initialized')`

### Dual Timestamp Tracking (Consistency & Debugging)

**Two levels of sync tracking for bugs:**

1. **Per-test sync: `tests.bugs_synced_at`** (NEW in STORY-024)
   - Tracks when bugs were **last fetched from API** for this specific test
   - Used for cache staleness decisions
   - NULL if bugs never synced for this test
   - Updated by `BugRepository._update_bugs_synced_at()`

2. **Per-bug sync: `bugs.synced_at`** (EXISTING)
   - Tracks when individual bug record was **written to SQLite**
   - Set to `CURRENT_TIMESTAMP` on INSERT
   - Useful for debugging: "When did this specific bug enter the database?"
   - Already exists in schema.py:173

**Why both?**
- **Consistency:** Mirrors existing pattern for tests (`tests.synced_at` tracks test metadata sync)
- **Debugging:** Can identify if bugs are stale without querying every bug row
- **Performance:** Single timestamp check (`tests.bugs_synced_at`) vs aggregating MIN(`bugs.synced_at`)
- **Clarity:** "When did we last fetch bugs for test 123?" is a single field lookup

**Example queries:**
```sql
-- Check if test needs bug refresh (fast)
SELECT bugs_synced_at, status FROM tests WHERE id = 123;

-- Find oldest bug in database (debugging)
SELECT MIN(synced_at) FROM bugs WHERE test_id = 123;

-- Find tests that never synced bugs
SELECT id, title FROM tests WHERE bugs_synced_at IS NULL;
```

### Staleness Threshold

**BUG_STALENESS_THRESHOLD_SECONDS = 3600 (1 hour)**

**Rationale:**
- Mutable tests (running/in_review) have active bug triage
- Bug statuses can change frequently during triage
- 1 hour balances freshness vs API quota
- Users can override with `force_refresh_bugs=true`

**Alternative thresholds considered:**
- 30 minutes: Too aggressive, wastes API quota
- 6 hours: Too stale for active triage
- 24 hours: Too stale for daily reporting

### Performance Characteristics

**Cache Hit (Immutable Test):**
- SQLite query: ~10ms
- No API call
- No network latency

**Cache Miss (Mutable Test, Stale):**
- SQLite query: ~10ms (check staleness)
- API call: ~200-500ms
- DB write: ~10ms
- Total: ~220-520ms

**EBR Performance (295 tests):**
- **Before (STORY-023e):** 295 API calls = ~30-45 seconds
- **After (STORY-024):**
  - 236 immutable (80%) = ~2.4 seconds (cache)
  - 59 mutable (20%) = ~10 seconds (API + cache)
  - **Total: ~12 seconds (4x faster)**

### API Quota Savings

**Daily EBR (1x/day):**
- Before: 295 API calls/report
- After: 59 API calls/report (80% reduction)
- Savings: 236 calls/day × 30 days = **~7,000 calls/month**

**Monthly Reporting (4x/month):**
- Before: 295 × 4 = 1,180 API calls/month
- After: 59 × 4 = 236 API calls/month
- Savings: **944 API calls/month (80% reduction)**

### Migration Safety

**Backward Compatibility:**
- Migration adds new column (non-breaking)
- Existing data preserved
- NULL values allowed (bugs_synced_at defaults to NULL)
- First refresh sets timestamp

**Rollback Strategy:**
- If needed, drop column: `ALTER TABLE tests DROP COLUMN bugs_synced_at`
- No data loss (bugs table unaffected)
- Revert to v3 schema

### Edge Cases

**Test Not in Database:**
- `get_bugs_cached_or_refresh()` falls back to API
- Fetches bugs from API (may 404 if test deleted)
- Does not update bugs_synced_at (test doesn't exist)

**Invalid Timestamp:**
- Parse failure logs warning
- Treats as NULL (never synced)
- Refreshes from API

**Force Refresh:**
- Always fetches from API
- Updates bugs_synced_at
- Bypasses all caching logic

### Future Entity-Agnostic Pattern (Codex Recommendation 3B)

**Decision: Keep bug-specific implementation for STORY-024, defer abstraction until second entity**

**Rationale:**
- Hard to design correctly before knowing requirements for features/comments/attachments
- Avoid premature generalization that constrains future entities
- Refactor cost is low once we have concrete requirements from a second entity

**Reference Implementation Note:**
The `BugRepository.get_bugs_cached_or_refresh()` method is the **reference implementation** for future entity caching. When implementing cached entities (features, comments, etc.), use this pattern:

1. **Schema:** Add `{entity}_synced_at` column to parent table (e.g., `tests.features_synced_at`)
2. **Constants:** Define mutability rules in `constants.py` (e.g., `FEATURE_STALENESS_THRESHOLD_SECONDS`)
3. **Repository:** Implement `get_{entity}_cached_or_refresh()` following bug pattern
4. **Configuration:** Add env overlays (e.g., `TESTIO_FEATURE_CACHE_TTL_SECONDS`)

**When to Abstract (Future STORY):**
- **Trigger:** Second entity (e.g., features, comments) requires same caching pattern
- **Approach:** Extract shared helper function (not necessarily base class)
- **Scope:** TTL and mutability decision logic, not entire repository
- **Document:** Create ADR documenting the entity caching pattern

**Candidate Shared Helper (Future Refactor):**
```python
# utilities/cache_helpers.py (future)

async def should_refresh_entity(
    db: aiosqlite.Connection,
    parent_table: str,
    parent_id: int,
    synced_at_column: str,
    staleness_threshold: int,
    mutability_fn: Callable[[str], bool],  # Check status → is mutable?
    force_refresh: bool = False,
) -> bool:
    """Generic cache staleness check for any entity.

    Args:
        db: Database connection
        parent_table: Table containing synced_at timestamp (e.g., "tests")
        parent_id: ID of parent record
        synced_at_column: Column name (e.g., "bugs_synced_at", "features_synced_at")
        staleness_threshold: Seconds before refresh needed
        mutability_fn: Function to check if parent status is mutable
        force_refresh: Bypass all caching logic

    Returns:
        True if entity should be refreshed from API, False to use cache
    """
```

**Migration Path:**
1. **STORY-024:** Implement bug-specific caching (this story)
2. **Future STORY-025:** Add features caching (second entity, identify duplication)
3. **Future STORY-026:** Extract shared helper if pattern is identical
4. **ADR-012:** Document entity caching pattern and configuration strategy

**Do NOT implement generic abstraction in STORY-024.** Keep `BugRepository` readable and easy to evolve.

## Success Metrics

**Performance:**
- ✅ EBR generation <15 seconds for 295 tests (cached)
- ✅ 80%+ cache hit ratio for typical product
- ✅ 4x faster than STORY-023e baseline

**API Quota:**
- ✅ 80% reduction in bug API calls
- ✅ ~7,000 API calls saved per month (1 EBR/day)
- ✅ Immutable tests never fetch bugs (unless forced)

**Architecture:**
- ✅ Schema migration applied successfully (v3 → v4)
- ✅ Intelligent caching based on test mutability
- ✅ Integrated with all sync workflows
- ✅ Force refresh parameter for guaranteed fresh data

**Testing:**
- ✅ 90%+ coverage for new caching logic
- ✅ Unit tests verify cache decision logic
- ✅ Integration tests measure performance
- ✅ Migration tests verify backward compatibility

## References

- **EPIC-004:** Production-Ready Architecture Rewrite
- **STORY-021g:** Hybrid Refresh Strategy (mutable test pattern)
- **STORY-023c:** SQLite-First Foundation (repository layer)
- **STORY-023e:** EBR Implementation (current always-refresh pattern)
- **Architecture Docs:**
  - `docs/architecture/ARCHITECTURE.md` - System architecture
  - `docs/architecture/adrs/ADR-004-cache-strategy-mvp.md` - Caching strategy
  - `docs/architecture/SERVICE_LAYER_SUMMARY.md` - Service layer design

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-18 | 1.0 | Initial story creation | dev (Claude Sonnet 4.5) |
| 2025-01-18 | 1.1 | Added Codex peer review recommendations:<br>- AC2: Environment variable overlays for configuration<br>- Force refresh pattern: Limited to EBR path only (Rec 2B)<br>- Entity-agnostic pattern: Defer abstraction until second entity (Rec 3B)<br>- Configuration: Env overlays with sensible defaults (Rec 4B) | dev (Claude Sonnet 4.5) + codex (peer review) |
| 2025-01-18 | 1.2 | **CORRECTED** per existing patterns in cache.py/test_repository.py:<br>- AC2: Use Pydantic Settings (config.py) instead of standalone constants.py<br>- Mutability: Immutable = archived + cancelled ONLY (locked is MUTABLE!)<br>- Dual timestamps: Keep bugs.synced_at, add tests.bugs_synced_at<br>- Settings integration: cache.py consumes settings.MUTABLE_TEST_STATUSES | dev (Claude Sonnet 4.5) |
| 2025-01-18 | 1.3 | **SIMPLIFIED** AC3 batch caching pattern:<br>- Single method `get_bugs_cached_or_refresh(test_ids: list[int])` instead of two methods<br>- Works for single test `[123]` or batch `[123,124,125]`<br>- Bulk SQL queries + batch API calls<br>- Fixed decision tree priority: Never-synced check BEFORE immutability check | dev (Claude Sonnet 4.5) |
| 2025-01-18 | 1.4 | **CODEX PEER REVIEW** - Critical architectural fixes:<br>- AC1: Added explicit migration orchestration to `initialize_schema()` (version only advances after column exists)<br>- AC2: Changed to `ClassVar` for mutability constants (not env-configurable)<br>- AC2: Renamed `CACHE_BYPASS_ALL` to `BUG_CACHE_BYPASS` (clarified scope)<br>- AC6: **Rewritten** to keep bug caching service-owned (removed PersistentCache coupling)<br>- Task 2: Updated to use Pydantic Settings (no standalone constants.py)<br>- Task 6: Simplified to service integration only (no sync workflow changes) | dev (Claude Sonnet 4.5) + codex (peer review) |

---

**Deliverable:** Intelligent bug caching with 4x performance improvement and 80% API quota savings

## Peer Review Summary (Codex - v1.4)

**Overall Assessment:**
✅ **APPROVED** - Story design is solid and aligns with existing SQLite-first patterns. Critical architectural fixes applied in v1.4.

**Key Validations:**
- ✅ Decision tree priority order is CORRECT (never-synced before immutability)
- ✅ Batch size 15 is GOOD (aligns with existing patterns)
- ✅ Mutability semantics are SOUND (matches cache.py/test_repository.py)
- ✅ Performance goals are REALISTIC (4x speedup achievable with 80% immutable mix)
- ✅ Batch-aware design is CLEAN (single method for single/batch use)

**Critical Fixes Applied (v1.4):**

1. **Schema Versioning Orchestration (AC1):**
   - ✅ Added explicit migration orchestration to `initialize_schema()`
   - ✅ Version only advances after physical schema (columns) exists
   - ✅ Prevents v3 DBs being marked v4 without `bugs_synced_at` column

2. **Service-Owned Bug Caching (AC6):**
   - ✅ Rewrote AC6 to keep bug refresh in service layer (removed PersistentCache coupling)
   - ✅ `MultiTestReportService` owns bug caching (on-demand via `bug_repo.get_bugs_cached_or_refresh()`)
   - ✅ `PersistentCache` stays focused on test metadata only
   - ✅ Preserves existing architecture layering (cache vs services)

3. **Configuration Pattern (AC2):**
   - ✅ Changed mutability constants to `ClassVar` (truly non-configurable)
   - ✅ Renamed `CACHE_BYPASS_ALL` to `BUG_CACHE_BYPASS` (clarified scope)
   - ✅ Updated to Pydantic Settings pattern (no standalone constants.py)

**Architectural Decisions:**

1. **Force Refresh Exposure:**
   - ✅ Expose `force_refresh_bugs` only on EBR path (BugRepository → MultiTestReportService → tool)
   - ✅ `BUG_CACHE_BYPASS` for debugging (logs warning when active)

2. **Entity-Agnostic Abstraction:**
   - ✅ Keep **bug-specific** implementation in STORY-024
   - ⏸️ Defer generic abstraction until second entity needs it
   - 📝 `get_bugs_cached_or_refresh()` is **reference implementation** for future entities

3. **Configuration Strategy:**
   - ✅ Pydantic Settings with env overlays (TTL, toggles)
   - ✅ ClassVar for structural constants (mutability statuses)
   - ✅ Sensible defaults (3600s TTL, caching enabled)

**Ready for Implementation:**
- All critical risks mitigated (schema versioning, layering)
- Medium-severity fixes applied (ClassVar, scope clarification)
- Test plan validated (unit + integration + migration tests)
- Performance targets confirmed as achievable
