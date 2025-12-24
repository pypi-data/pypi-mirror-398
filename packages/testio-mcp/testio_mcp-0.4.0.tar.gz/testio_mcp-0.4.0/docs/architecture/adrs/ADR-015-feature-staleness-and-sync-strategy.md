# ADR-015: Feature Staleness and Sync Strategy

**Date:** 2025-11-24
**Status:** Accepted (Partially superseded by ADR-017 - sync phases updated)
**Affects:** STORY-038 (Epic 005 - Feature Sync Integration)
**Context:** Correct Course workflow - discovered sync orchestration gap during STORY-037 review
**Related:** [ADR-017: Background Sync Optimization](ADR-017-background-sync-optimization-pull-model.md)

## Context

Epic-005 implemented Features and Users tables with functional repositories (`FeatureRepository`, `UserRepository`), but **sync orchestration was not implemented**. During STORY-037 review (Data Serving Layer), we discovered:

1. ✅ `FeatureRepository.sync_features()` exists and works
2. ✅ MCP tools (`list_features`) exist and work
3. ❌ Nothing calls sync methods during background refresh or CLI sync
4. ❌ Features table remains empty → MCP tools return empty results
5. ❌ Epic-005 deliverables cannot be validated

**Problem:** How should features be synced to keep the catalog reasonably current without API spam?

## Decision

**Use staleness-based refresh with 1-hour TTL**, following the bug caching pattern from STORY-024.

### Sync Strategy

**Two refresh paths:**

1. **Background Sync** (Automatic, every 15 minutes)
   - Phase 1: Discover new tests (incremental)
   - Phase 2: Refresh mutable tests (status updates)
   - Phase 3 (NEW): **Refresh features if stale**
     - Check `products.features_synced_at` timestamp
     - If stale (> 1 hour) OR NULL → Refresh from API
     - If fresh (< 1 hour) → Skip (already current)

2. **Tool Calls** (On-demand)
   - User calls `list_features(product_id)`
   - Check `products.features_synced_at` timestamp
   - If stale OR NULL → Refresh from API
   - If fresh → Return from cache
   - **NEW:** `force_refresh=True` bypasses staleness check

### Configuration

```python
# config.py
FEATURE_CACHE_TTL_SECONDS: int = Field(
    default=3600,  # 1 hour
    ge=900,        # Min 15 minutes
    le=86400,      # Max 24 hours
    description="Staleness threshold for product features in seconds."
)
```

### Schema

```python
class Product(SQLModel, table=True):
    # ... existing fields ...
    last_synced: datetime           # Test sync timestamp (existing)
    features_synced_at: datetime | None  # Feature sync timestamp (NEW)
```

### Implementation Pattern

```python
async def refresh_features(self, product_id: int) -> dict:
    """Refresh features if stale."""
    settings = get_settings()

    # Check staleness
    product = await product_repo.get_product(product_id)
    if product and product.features_synced_at:
        seconds_since_sync = (now - product.features_synced_at).total_seconds()
        if seconds_since_sync < settings.FEATURE_CACHE_TTL_SECONDS:
            return {"skipped": True}  # Fresh, skip API call

    # Stale or NULL - refresh from API
    await feature_repo.sync_features(product_id)
    await product_repo.update_features_last_synced(product_id)

    return {"created": X, "updated": Y, "total": Z, "skipped": False}
```

## Rationale

### Why 1-Hour TTL?

**Features change infrequently compared to bugs:**
- Bugs: Continuous flow during active testing (new bugs every few minutes)
- Features: Product catalog changes occasionally (new features added monthly/quarterly)

**1 hour balances freshness vs API efficiency:**
- ✅ Fresh enough: Catalog updates appear within 1 hour
- ✅ Efficient: Only 1 API call per product per hour (vs bugs' more aggressive refresh)
- ✅ Predictable: Background sync handles refresh automatically
- ✅ Controllable: Users can force refresh if needed

### Why Follow Bug Pattern?

**Consistency with STORY-024 (Bug Intelligent Caching):**
- Same staleness check logic
- Same per-entity timestamp tracking (`products.features_synced_at` vs `tests.bugs_synced_at`)
- Same configuration pattern (`FEATURE_CACHE_TTL_SECONDS` vs `BUG_CACHE_TTL_SECONDS`)
- Developers already understand the pattern

**Key differences from bugs:**
- **Granularity:** Per-product (features) vs per-test (bugs)
- **TTL:** 1 hour (features) vs 1 hour (bugs, but more aggressively checked)
- **Immutability:** Features don't have immutable concept (no "archived features")
- **Background refresh:** Features refresh in background, bugs don't

### Why Background Sync Refreshes Features?

**Features are catalog data, not ad-hoc queries:**
- Bugs: Tied to specific test IDs (user explicitly queries test X's bugs)
- Features: Product-level catalog (users browse "what can I test?")
- **Expectation:** Catalog should be reasonably current

**Better UX:**
- Tool calls hit cache (fast) instead of API (slow)
- Predictable API load (background cycles, not user-facing operations)
- Users don't wait for initial sync on first query

## Consequences

### Positive

✅ **Catalog stays current:** Features refresh automatically every hour
✅ **Fast tool calls:** Usually hit cache (fresh < 1 hour)
✅ **Predictable API load:** Background sync handles refresh
✅ **User control:** `force_refresh=True` bypasses cache
✅ **Consistent pattern:** Follows bug staleness model
✅ **Epic-005 complete:** Unblocks validation (features table populated)

### Negative

❌ **Slight API overhead:** Background sync makes extra API calls
   - **Mitigation:** Only when stale (> 1 hour), not every cycle
   - **Mitigation:** Error handling prevents cascade failures

❌ **New column:** `features_synced_at` adds schema complexity
   - **Mitigation:** Follows existing pattern (`last_synced`, `bugs_synced_at`)
   - **Mitigation:** Nullable (graceful degradation if NULL)

## Alternatives Considered

### Alternative 1: Always Fresh (No Staleness Check)

Features refresh on **every** background cycle and **every** tool call.

**Rejected because:**
- 🔴 API waste: Features don't change every 15 minutes
- 🔴 Slower tool calls: Every call hits API (100-500ms vs 10ms cache)
- 🔴 Higher API load: 4x more calls per hour per product

### Alternative 2: Pure On-Demand (No Background Refresh)

Features refresh **only** when tools call them, never in background.

**Rejected because:**
- 🔴 Slower first query: User waits for API call (poor UX)
- 🔴 Unpredictable timing: API load depends on user behavior
- 🔴 Catalog staleness: Could be hours/days old if nobody queries

### Alternative 3: Longer TTL (24 Hours)

Use 24-hour TTL instead of 1 hour.

**Rejected because:**
- 🔴 Too stale: New features invisible for up to 24 hours
- 🔴 Poor UX: Users expect catalog to be reasonably current
- 🔴 Defeats purpose: Catalog visibility is a core Epic-005 goal

## Implementation Notes

### Background Sync Flow

```python
async def run_background_refresh():
    # Phase 1: Discover new tests
    for product in products:
        await sync_product_tests(product.id)

    # Phase 2: Refresh mutable tests
    for product in products:
        await refresh_active_tests(product.id)

    # Phase 3 (NEW): Refresh stale features
    for product in products:
        result = await refresh_features(product.id)
        if not result["skipped"]:
            logger.info(f"Refreshed {result['total']} features for product {product.id}")
```

### Tool Call Flow

```python
@mcp.tool()
async def list_features(product_id: int, force_refresh: bool = False):
    # Check staleness (unless force_refresh)
    if not force_refresh:
        product = await get_product(product_id)
        if _is_fresh(product.features_synced_at, FEATURE_CACHE_TTL_SECONDS):
            return await get_from_cache(product_id)  # Fast path

    # Stale or force_refresh - refresh from API
    await refresh_features(product_id)
    return await get_from_cache(product_id)
```

### Staleness Helper

```python
def _is_stale(synced_at: datetime | None, ttl_seconds: int) -> bool:
    """Check if timestamp is stale (> TTL seconds old)."""
    if synced_at is None:
        return True  # Never synced = stale

    seconds_since_sync = (datetime.now(UTC) - synced_at).total_seconds()
    return seconds_since_sync > ttl_seconds
```

## Success Metrics

**Functional:**
- ✅ Background sync logs show features refreshing when stale
- ✅ Background sync skips features when fresh (< 1 hour)
- ✅ `list_features` returns populated data
- ✅ Tool respects staleness (cache hits when fresh)
- ✅ `force_refresh=True` bypasses cache

**Performance:**
- ✅ Tool calls < 50ms when cache hit (fresh features)
- ✅ Tool calls < 500ms when cache miss (stale features, API refresh)
- ✅ Background sync adds < 5 seconds per product (sectioned products)

**Operational:**
- ✅ Features stay current (updates visible within 1 hour)
- ✅ API load predictable (1 call per product per hour)
- ✅ No cascade failures (error handling isolates product failures)

## References

- **STORY-024:** Intelligent Bug Caching (pattern precedent)
- **STORY-038:** Feature Sync Integration (implementation)
- **Epic-005:** Data Enhancement and Serving (parent epic)
- **ADR-013:** User Story Embedding Strategy (related catalog decision)
- **Correct Course Proposal:** `docs/sprint-artifacts/sprint-change-proposal-2025-11-24.md`

## Decision Log

- **2025-11-24:** Issue discovered during STORY-037 review (sync integration gap)
- **2025-11-24:** Evaluated 3 approaches (Always Fresh, On-Demand, Staleness)
- **2025-11-24:** **ACCEPTED** - Staleness-based refresh with 1-hour TTL
- **2025-11-24:** Created STORY-038 to implement sync integration
- **2025-11-26:** **PARTIAL SUPERSESSION** - Sync phases updated by ADR-017:
  - Phase 4 (Mutable Test/Bug Refresh) removed from background sync
  - Bugs/test metadata now refresh on-demand via read-through caching
  - Feature staleness logic (this ADR) remains unchanged
  - TTL configuration unified to single `CACHE_TTL_SECONDS`

---

**Supersession Note:**

This ADR's core decision (staleness-based feature refresh) remains valid. However, the sync phase numbering described in the "Background Sync Flow" section has changed:

| This ADR (2025-11-24) | ADR-017 (2025-11-26) |
|-----------------------|----------------------|
| Phase 1: Discover new tests | Phase 1: Refresh product metadata |
| Phase 2: Refresh mutable tests | Phase 2: Refresh features (TTL-gated) |
| Phase 3: Refresh features | Phase 3: Discover new tests |
| (N/A) | Phase 4: REMOVED |

See [ADR-017](ADR-017-background-sync-optimization-pull-model.md) for the current sync architecture.

---

**Next Steps:** *(Completed)*
1. ~~Implement STORY-038 (Feature Sync Integration)~~ ✅
2. ~~Validate Epic-005 deliverables (features table populated)~~ ✅
3. ~~Monitor API load and adjust TTL if needed~~ ✅ (Unified to CACHE_TTL_SECONDS)
