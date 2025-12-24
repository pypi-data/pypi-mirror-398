# ADR-017: Background Sync Optimization - Pull Model Architecture

**Date:** 2025-11-26
**Status:** Accepted
**Affects:** STORY-046 (Epic 007 - Generic Analytics Framework)
**Supersedes:** Portions of ADR-015 (sync phases)
**Related:** ADR-015 (Feature Staleness), ADR-004 (Cache Strategy)

## Context

The background sync process had grown to 4 phases, proactively refreshing all mutable tests and their bugs every 15 minutes. This resulted in:

1. **~1000 API calls per cycle** - Many unnecessary because data was not being actively queried
2. **Long sync cycles** - 15+ minutes to complete full refresh
3. **API quota pressure** - Consuming quota for data nobody was looking at
4. **Complexity** - 4 phases with different refresh logic

**Problem:** How do we keep data fresh efficiently without wasting API calls on unqueried data?

## Decision

**Shift from Push Model to Pull Model (Read-Through Caching)**

### Before (Push Model - 4 Phases)

```
Background Sync (every 15 minutes):
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Refresh product metadata (always)                      │
│ Phase 2: Refresh features (staleness check)                     │
│ Phase 3: Discover new tests (incremental)                       │
│ Phase 4: Refresh mutable tests + bugs (proactive)  ← EXPENSIVE  │
└─────────────────────────────────────────────────────────────────┘
```

### After (Pull Model - 3 Phases)

```
Background Sync (every 15 minutes):              On-Demand (when queried):
┌────────────────────────────────────────┐      ┌──────────────────────────────────┐
│ Phase 1: Refresh product metadata      │      │ BugRepository                    │
│ Phase 2: Refresh features (TTL-gated)  │      │   .get_bugs_cached_or_refresh()  │
│ Phase 3: Discover new tests            │      │                                  │
│ Phase 4: REMOVED                       │      │ TestRepository                   │
└────────────────────────────────────────┘      │   .get_tests_cached_or_refresh() │
                                                │                                  │
                                                │ FeatureRepository                │
                                                │   .get_features_cached_or_refresh│
                                                └──────────────────────────────────┘
```

### Key Changes

| Aspect | Before (Push) | After (Pull) |
|--------|---------------|--------------|
| **Bug Refresh** | Background sync proactively refreshes | On-demand when queried via analytics/tools |
| **Test Metadata Refresh** | Background sync proactively refreshes | On-demand when `list_tests` or analytics query |
| **Feature Refresh** | Background sync (Phase 2) | **Unchanged** - still background + on-demand |
| **API Calls/Cycle** | ~1000 (all mutable tests + bugs) | ~50 (products + features + new tests only) |
| **Sync Duration** | 15+ minutes | 2-5 minutes |
| **Data Freshness** | Always fresh (pushed) | Fresh within TTL when queried (pulled) |

### Unified TTL Configuration

**Before:** 3 separate TTL settings
```python
BUG_CACHE_TTL_SECONDS = 3600      # Bug staleness
FEATURE_CACHE_TTL_SECONDS = 3600  # Feature staleness
TEST_CACHE_TTL_SECONDS = 3600     # Test metadata staleness
```

**After:** Single unified TTL
```python
CACHE_TTL_SECONDS = 3600  # Unified staleness threshold for all entities
```

**Migration:** Breaking change - users with custom TTL values must update to `CACHE_TTL_SECONDS`.

### Per-Entity Refresh Locks

To prevent duplicate API calls when concurrent requests target the same entity:

```python
# In PersistentCache
_refresh_locks: dict[tuple[int, str, int], asyncio.Lock] = {}

def get_refresh_lock(self, entity_type: str, entity_id: int) -> asyncio.Lock:
    """Get or create lock for specific entity.

    Key: (customer_id, entity_type, entity_id)
    Uses setdefault() for thread-safe creation.
    """
    key = (self.customer_id, entity_type, entity_id)
    return self._refresh_locks.setdefault(key, asyncio.Lock())

# Usage in BugRepository
async def get_bugs_cached_or_refresh(self, test_ids: list[int], ...):
    for test_id in test_ids:
        lock = self.cache.get_refresh_lock("bug", test_id)
        async with lock:
            # Only one request refreshes at a time
            await self.refresh_bugs_batch([test_id])
```

**Why per-entity locks in PersistentCache?**
- Repository objects are short-lived (created per request)
- Instance-level `asyncio.Lock` won't serialize across requests
- Shared lock registry in `PersistentCache` survives across requests

**Lock cleanup:** Not required per architect review - memory footprint negligible (~5MB max for 50K entities), locks persist for reuse.

## Rationale

### Why Pull Model?

**Efficiency principle:** Don't pay API cost for data nobody is looking at.

```
Scenario: 1000 tests, 100 mutable, only 10 queried per hour

Push Model:
- Refreshes ALL 100 mutable tests every cycle
- 100 API calls × 4 cycles/hour = 400 calls/hour
- 90% wasted on unqueried data

Pull Model:
- Refreshes ONLY 10 queried tests
- 10 API calls (when queried) + 0 background
- 100% efficient - no wasted calls
```

### Why Keep Feature Refresh in Background?

Features are **catalog data** that users expect to be current:
- Product feature lists should be available immediately
- Feature names/descriptions change rarely but should reflect current state
- Features are lightweight (dozens per product, not thousands)

### Why Unified TTL?

**Simplicity over configurability:**
- All staleness thresholds were set to 1 hour anyway
- Reduces configuration surface area
- Single mental model for cache behavior
- Breaking change is acceptable for simplification

### Why Per-Entity Locks?

**Concurrent analytics queries** can trigger duplicate refreshes:

```
Without locks:
  Query 1: "bugs by severity for Test 123" → triggers refresh
  Query 2: "bugs by feature for Test 123"  → triggers DUPLICATE refresh

With locks:
  Query 1: "bugs by severity for Test 123" → triggers refresh
  Query 2: "bugs by feature for Test 123"  → WAITS for Query 1, uses cached data
```

**Benefits:**
- Prevents duplicate API calls during overlap windows
- Per-entity granularity avoids head-of-line blocking
- Serializes refreshes → no "last writer wins" race conditions
- Standard asyncio pattern (low complexity)

**Tradeoff:** Queries may wait 2-5 seconds if another refresh for same entity is in progress.

## Consequences

### Positive

✅ **95% reduction in API calls** - Only refresh queried data
✅ **Faster sync cycles** - 3 phases instead of 4
✅ **Simpler configuration** - Single `CACHE_TTL_SECONDS`
✅ **Predictable freshness** - Data fresh within TTL when accessed
✅ **Concurrent safety** - Per-entity locks prevent duplicate refreshes
✅ **Future-proof** - Frontend dashboard can poll local API efficiently

### Negative

❌ **First-query latency** - Stale data triggers refresh, user waits 2-5s
   - **Mitigation:** Staleness warning in response, data still usable
   - **Mitigation:** TTL of 1 hour means most data is fresh

❌ **Breaking change** - TTL configuration changed
   - **Mitigation:** Clear migration instructions in .env.example
   - **Mitigation:** Single config simpler than remembering 3

❌ **Dual lock patterns** - Instance locks + registry locks coexist
   - **Mitigation:** Serve different purposes (integrity vs caching)
   - **Mitigation:** Minor complexity, well-documented

## Implementation

### Background Sync (3 Phases)

```python
async def _run_background_refresh_cycle(self):
    """Execute background refresh (3 phases)."""

    # Phase 1: Refresh product metadata (always)
    for product in products:
        await product_repo.upsert_product(product)

    # Phase 2: Refresh features (staleness check)
    for product in products:
        await cache.refresh_features(product.id)  # Respects TTL

    # Phase 3: Discover new tests (incremental)
    for product in products:
        await cache.sync_product_tests(product.id)

    # Phase 4: REMOVED - bugs/tests refresh on-demand

    logger.info(
        f"Background sync: 3 phases (products, features, new tests) complete"
    )
```

### Read-Through Caching Pattern

```python
# In AnalyticsService.query_metrics()
async def query_metrics(self, query):
    # 1. Get tests for query scope
    tests = await test_repo.get_tests_for_scope(query)

    # 2. Read-through caching: refresh if stale
    bugs, cache_stats = await bug_repo.get_bugs_cached_or_refresh(
        test_ids=[t.id for t in tests]
    )

    # 3. Include staleness warning if data was refreshed
    if cache_stats["api_calls"] > 0:
        warnings.append(f"Refreshed {cache_stats['api_calls']} stale tests")

    return results, warnings
```

### TestService Integration

```python
# In TestService.list_tests()
async def list_tests(self, product_id: int, ...):
    # Staleness check: Refresh mutable test metadata if stale (AC10)
    test_ids = await test_repo.get_test_ids_for_product(product_id)
    if test_ids:
        _, cache_stats = await test_repo.get_tests_cached_or_refresh(test_ids)

        # Log warning if cache hit rate < 50%
        if cache_stats["cache_hit_rate"] < 50.0:
            logger.warning(f"Low cache hit rate for product {product_id}")

    return await test_repo.query_tests(product_id, ...)
```

## Files Changed

| File | Change |
|------|--------|
| `src/testio_mcp/config.py` | Unified `CACHE_TTL_SECONDS`, removed separate TTLs |
| `src/testio_mcp/database/cache.py` | `_refresh_locks`, `get_refresh_lock()`, Phase 4 removal |
| `src/testio_mcp/repositories/base_repository.py` | Added optional `cache` parameter |
| `src/testio_mcp/repositories/bug_repository.py` | Per-entity locks in `get_bugs_cached_or_refresh()` |
| `src/testio_mcp/repositories/feature_repository.py` | Per-entity locks, timestamp bug fix |
| `src/testio_mcp/repositories/test_repository.py` | Per-entity locks, `get_test_ids_for_product()` |
| `src/testio_mcp/services/test_service.py` | Staleness check in `list_tests()` |
| `.env.example` | Updated configuration documentation |

## References

- **STORY-046:** Background Sync Optimization (implementation)
- **ADR-015:** Feature Staleness and Sync Strategy (partial supersession)
- **STORY-044B:** Analytics Staleness Warnings (foundation)
- **Epic 007:** Generic Analytics Framework (parent epic)

## Decision Log

- **2025-11-26:** Identified sync inefficiency (1000 API calls/cycle)
- **2025-11-26:** Evaluated push vs pull models
- **2025-11-26:** **ACCEPTED** - Pull model with read-through caching
- **2025-11-26:** Implemented in STORY-046 (10 ACs, 484 tests passing)
- **2025-11-26:** Architecture documented in ADR-017

---

**Summary:** This ADR documents the shift from proactive background refresh (push model) to on-demand refresh (pull model) for bug and test metadata, reducing API calls by ~95% while maintaining data freshness through intelligent TTL-based staleness checks.
