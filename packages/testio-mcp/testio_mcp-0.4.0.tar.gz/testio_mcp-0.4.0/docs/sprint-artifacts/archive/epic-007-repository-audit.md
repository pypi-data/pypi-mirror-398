# Epic 007 Repository Audit
**Date:** 2025-11-25
**Purpose:** Clarify current vs. needed repository capabilities for staleness + integrity

---

## Current State (Epic 006 Complete)

### BugRepository
**Has:**
- ✅ `get_bugs_cached_or_refresh(test_ids, force_refresh)` - **THE GOLDEN PATTERN**
  - Returns: `tuple[dict[int, list[dict]], dict[str, Any]]` (data + cache_stats)
  - Handles: Staleness check, immutability check, batch refresh, cache stats
  - TTL: `BUG_CACHE_TTL_SECONDS` (default: 3600s / 1 hour)
  - Decision logic: Immutable (always cache) | Mutable (check TTL)

**Needs for Epic 007:**
- ✅ **No changes needed** - Pattern is complete and working

---

### TestRepository
**Has:**
- `insert_test(test_data, product_id)` - Writes test to DB
- `_upsert_test_feature(test_id, feature_data)` - Writes test_feature to DB (STORY-041)
- `refresh_test(test_id)` - Fetches single test from API, upserts to DB
- `query_tests(...)` - Reads tests with filters from DB (no staleness check)
- `get_mutable_tests(product_id)` - Gets mutable tests from DB

**Needs for Epic 007:**
- ❌ **Missing:** `get_tests_cached_or_refresh(test_ids, force_refresh)` - **MUST ADD**
  - Should mirror BugRepository pattern
  - Returns: `tuple[dict[int, dict], dict[str, Any]]` (tests_by_id + cache_stats)
  - Handles: Staleness check (TTL: `TEST_CACHE_TTL_SECONDS`), batch refresh
  - Decision logic: Immutable (archived/cancelled) → cache | Mutable (running/locked) → check TTL
  - Used by: **AnalyticsService (read-time)** - ensures fresh test status/end_at for filters/grouping
- ❌ **Missing:** `tests.synced_at` column - **MUST ADD** (DB migration)
  - Track when test metadata last refreshed
  - Used for staleness check (similar to bugs_synced_at pattern)
- ❌ **Missing:** Integrity check in `_upsert_test_feature()` - **MUST ADD** (covered in STORY-044C)

**Why TestRepository staleness matters for analytics:**
- Analytics filters by `tests.status` (e.g., "completed tests only")
- Analytics filters by `tests.end_at` date range (e.g., "tests from Q4 2024")
- If test status stale ("running" in DB, actually "completed" in API) → **missing data in results**
- If test end_at stale (NULL in DB, actually has timestamp in API) → **wrong time bucketing**

---

### FeatureRepository
**Has:**
- `sync_features(product_id)` - Fetches all features for product from API, upserts to DB
- `get_features_for_product(product_id)` - Reads from DB (no staleness check)
- `count_features(product_id)` - Counts features in DB

**Needs for Epic 007:**
- ❌ **Missing:** `get_features_cached_or_refresh(product_ids, force_refresh)` - **MUST ADD**
  - Should mirror BugRepository pattern
  - Returns: `tuple[dict[int, list[dict]], dict[str, Any]]` (features_by_product + cache_stats)
  - Handles: Staleness check (TTL: `FEATURE_CACHE_TTL_SECONDS`), batch refresh
  - Decision logic: Check `features_synced_at` per product, refresh if stale
  - Used by: **AnalyticsService (read-time)** + **TestRepository (write-time integrity)**

---

### UserRepository
**Has:**
- `upsert_user(user_data)` - Writes user to DB
- `get_user(user_id)` - Reads single user from DB

**Needs for Epic 007:**
- ❌ **Missing:** `get_users_cached_or_refresh(user_ids, force_refresh)` - **NICE TO HAVE (defer?)**
  - Used by: BugRepository integrity check (for `reported_by_user_id`)
  - Alternative: Simple check + fetch pattern (no TTL needed, users rarely change)
  - **Decision:** Start without TTL pattern, add if needed later

---

## Epic 007 Requirements Summary

### STORY-044B: Analytics Staleness Warnings
**Repository Needs:**
1. ✅ `BugRepository.get_bugs_cached_or_refresh()` - Already exists
2. ❌ `TestRepository.get_tests_cached_or_refresh()` - **MUST ADD (read-time)**
3. ❌ `FeatureRepository.get_features_cached_or_refresh()` - **MUST ADD (read-time)**

**Usage in AnalyticsService:**
```python
async def query_metrics(self, metrics, dimensions, ...):
    # 1. Get test IDs in scope (lightweight query)
    test_ids = await self._get_scoped_test_ids(...)

    # 2. Refresh tests (ensures fresh status, end_at for filters)
    test_repo = TestRepository(self.session, self.customer_id, self.client)
    tests, test_stats = await test_repo.get_tests_cached_or_refresh(test_ids)
    if test_stats["cache_hit_rate"] < 50:
        self._add_warning(f"Warning: {test_stats['api_calls']} tests refreshed")

    # 3. Refresh bugs (staleness check)
    bug_repo = BugRepository(self.session, self.customer_id, self.client)
    bugs, bug_stats = await bug_repo.get_bugs_cached_or_refresh(test_ids)
    if bug_stats["cache_hit_rate"] < 50:
        self._add_warning(f"Warning: {bug_stats['api_calls']} tests had stale bugs")

    # 4. Refresh features (staleness check) - NEW METHOD NEEDED
    feature_repo = FeatureRepository(self.session, self.customer_id, self.client)
    product_ids = await self._extract_product_ids(test_ids)
    features, feature_stats = await feature_repo.get_features_cached_or_refresh(product_ids)
    if feature_stats["cache_hit_rate"] < 50:
        self._add_warning(f"Warning: {feature_stats['api_calls']} products refreshed")

    # 5. Execute aggregation query (ALL data guaranteed fresh)
    result = await self._execute_sql_query(...)
```

---

### STORY-044C: Referential Integrity Pattern
**Repository Needs:**
1. ❌ `TestRepository._upsert_test_feature()` integrity check - **MUST ADD (write-time)**
2. ❌ `FeatureRepository.get_features_cached_or_refresh()` - **MUST ADD (read-time)**
3. ❌ Per-key async locks in TestRepository - **MUST ADD**

**Usage in TestRepository (Write-Time Integrity):**
```python
async def _upsert_test_feature(self, test_id: int, feature_data: dict):
    feature_id = feature_data["feature_id"]
    product_id = feature_data["product_id"]

    # Integrity check: Ensure feature exists locally
    feature_exists = await self._check_feature_exists(feature_id)
    if not feature_exists:
        # Fetch all features for product (no single-feature API endpoint)
        await self._fetch_and_store_features_for_product(product_id)

    # Now safe to upsert test_feature (FK constraint satisfied)
    # ... upsert logic ...

async def _fetch_and_store_features_for_product(self, product_id: int):
    # Per-key lock to prevent thundering herd
    if product_id not in self._feature_fetch_locks:
        self._feature_fetch_locks[product_id] = asyncio.Lock()

    async with self._feature_fetch_locks[product_id]:
        # Double-check (another coroutine may have fetched)
        if await self._check_feature_exists(feature_id):
            return

        # Create FeatureRepository (composition, not DI)
        feature_repo = FeatureRepository(self.session, self.customer_id, self.client)

        # Use get_features_cached_or_refresh (respects TTL, no duplicate work)
        features, stats = await feature_repo.get_features_cached_or_refresh([product_id])

        # Log integrity fill
        logger.warning(f"Referential integrity fill: feature {feature_id} missing, "
                      f"fetched {stats['api_calls']} products")
```

---

## Implementation Order

### Phase 1: FeatureRepository.get_features_cached_or_refresh() (STORY-044B + 044C dependency)
**New method signature:**
```python
async def get_features_cached_or_refresh(
    self,
    product_ids: list[int],
    force_refresh: bool = False,
) -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
    """Get features with intelligent caching (mirrors BugRepository pattern).

    Args:
        product_ids: List of product identifiers
        force_refresh: Bypass cache and fetch from API (default: False)

    Returns:
        Tuple of (features_dict, cache_stats):
            - features_dict: Dict mapping product_id -> list of feature dicts
              Example: {598: [{feature1}, {feature2}], 599: [{feature3}]}
            - cache_stats: Cache efficiency metrics dict with:
              - total_products: int
              - cache_hits: int
              - api_calls: int
              - cache_hit_rate: float (0-100)
              - breakdown: dict with decision category counts

    Decision Logic (per product):
        1. If force_refresh=True → mark for refresh
        2. If FEATURE_CACHE_ENABLED=false → mark for refresh
        3. If features_synced_at IS NULL → mark for refresh
        4. If stale (>TTL seconds) → mark for refresh
        5. If fresh → use cache
        6. Batch refresh all products marked for refresh
        7. Return features for all product IDs from SQLite
    """
```

**Database Schema Addition:**
- Add `features_synced_at` column to `products` table (track per-product feature sync time)
- Migration: `alembic revision --autogenerate -m "Add features_synced_at to products"`

**Implementation Pattern:**
- Copy `BugRepository.get_bugs_cached_or_refresh()` structure
- Adapt for product-level granularity (features belong to products)
- Use `FEATURE_CACHE_TTL_SECONDS` for staleness threshold

---

### Phase 2: TestRepository Integrity Checks (STORY-044C)
**Add to TestRepository:**
1. `_feature_fetch_locks: dict[int, asyncio.Lock]` - Per-product-id locks
2. `_check_feature_exists(feature_id)` - Query `features` table
3. `_fetch_and_store_features_for_product(product_id)` - Integrity fill with locking
4. Update `_upsert_test_feature()` - Add integrity check before upsert

---

### Phase 3: AnalyticsService Integration (STORY-044B)
**Add to AnalyticsService:**
1. `_get_scoped_test_ids()` - Pre-query to identify tests in scope
2. `_extract_product_ids()` - From test IDs, get unique product IDs
3. Use `BugRepository.get_bugs_cached_or_refresh()` for bug staleness
4. Use `FeatureRepository.get_features_cached_or_refresh()` for feature staleness
5. Add warnings if cache hit rate < 50%

---

## Repository Method Comparison (Consistency Check)

| Method | BugRepository | FeatureRepository | Pattern Match? |
|--------|---------------|-------------------|----------------|
| `get_*_cached_or_refresh()` | ✅ Exists | ❌ Must add | N/A |
| **Signature** | `(test_ids, force_refresh)` | Should be: `(product_ids, force_refresh)` | ✅ Consistent |
| **Return Type** | `tuple[dict, dict]` | Should be: `tuple[dict, dict]` | ✅ Consistent |
| **Granularity** | Per test | Per product | ✅ Appropriate |
| **TTL Config** | `BUG_CACHE_TTL_SECONDS` | `FEATURE_CACHE_TTL_SECONDS` | ✅ Consistent |
| **Staleness Column** | `tests.bugs_synced_at` | `products.features_synced_at` | ✅ Consistent |
| **Batch Support** | ✅ Yes | ✅ Should support | ✅ Consistent |

---

## Database Schema Requirements

### Existing (Epic 006):
- ✅ `tests.bugs_synced_at` - Tracks bug sync time per test
- ✅ `products.synced_at` - Tracks product metadata sync time
- ✅ `products.customer_id` - Multi-tenant support

### New (Epic 007):
- ❌ **Must add:** `products.features_synced_at` - Track feature sync time per product
  - Type: `TIMESTAMP`
  - Nullable: YES (NULL = never synced)
  - Updated by: `FeatureRepository.get_features_cached_or_refresh()`
  - Used by: Staleness check in `get_features_cached_or_refresh()`

---

## Error Handling Standards

### BugRepository.get_bugs_cached_or_refresh() (Existing Pattern):
- API failures: Log ERROR, return empty dict for failed test_ids
- Partial failures: Continue processing other test_ids
- Empty result: Returns empty dict (not an error)

### FeatureRepository.get_features_cached_or_refresh() (Should Mirror):
- API failures: Log ERROR, skip product, emit metric `repository.feature_refresh_failures`
- Partial failures: Continue processing other product_ids
- Empty result: Returns empty dict (not an error)

### TestRepository Integrity Checks (New Pattern):
- Feature fetch failure: Log ERROR, SKIP test_feature upsert, emit metric `repository.integrity_fill_failures`
- Re-raise exception so caller can handle test-level failures
- Do NOT crash entire sync operation

---

## Testing Strategy

### Unit Tests:
- `test_feature_repository.py::test_get_features_cached_or_refresh_fresh` - Cache hit
- `test_feature_repository.py::test_get_features_cached_or_refresh_stale` - TTL exceeded
- `test_feature_repository.py::test_get_features_cached_or_refresh_force` - force_refresh=True
- `test_feature_repository.py::test_get_features_cached_or_refresh_batch` - Multiple products

- `test_test_repository.py::test_upsert_test_feature_with_missing_feature` - Integrity check triggers
- `test_test_repository.py::test_fetch_and_store_features_concurrent` - Per-key lock works

### Integration Tests:
- `test_epic_007_e2e.py::test_analytics_staleness_end_to_end` - Full flow with stale data
- `test_epic_007_e2e.py::test_integrity_check_end_to_end` - Missing feature triggers fetch

---

## Summary

**Repositories MUST guarantee:**
1. **Freshness:** Data is within TTL or refreshed automatically
2. **Integrity:** All foreign keys resolve locally (no dangling references)
3. **Efficiency:** Use cache when valid, minimize API calls
4. **Consistency:** All repositories follow same `get_*_cached_or_refresh()` pattern

**Key Addition:**
- `FeatureRepository.get_features_cached_or_refresh()` is the **critical missing piece**
- Used by both **AnalyticsService (read-time)** and **TestRepository (write-time integrity)**
- Must be implemented FIRST before STORY-044B and 044C can proceed
