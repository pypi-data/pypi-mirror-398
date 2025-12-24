# ADR-014: Pagination-Ready Caching Strategy

## Status
❌ SUPERSEDED

**Superseded By:** [STORY-023d: Service Refactoring](../../stories/done/story-023d-service-refactoring.md)

**Superseded Date:** 2025-11-18 (v2.0 - SQLite-first refactoring)

**Historical Context:** This ADR was written on 2025-11-06 to plan pagination strategies for InMemoryCache. However, it was superseded before implementation when the project moved to SQLite-based PersistentCache (STORY-021) and service layer refactoring (STORY-023d).

**Current Implementation:**
- **Pagination:** Standard page/offset pattern via SQLite queries (no cache key explosion)
- **Filtering:** Server-side SQL queries (no fetch-all-then-filter)
- **API Investigation:** Valuable findings extracted to [API_CAPABILITIES.md](../API_CAPABILITIES.md)

**Why Superseded:**
- InMemoryCache no longer exists (replaced by PersistentCache)
- Cache-raw pattern no longer needed (SQLite handles filtering efficiently)
- Pagination implemented differently (SQL queries vs. cached pages)
- Phase 2 planning obsolete (never implemented)

---

## Original ADR Content (Historical Reference)

## Original Context

The TestIO Customer API supports pagination for the exploratory tests endpoint, but our current implementation only uses the unpaginated mode (last 150 tests). With customers having 1000+ tests, we need a strategy that:

1. Fixes the current cache-raw bug in `list_tests()`
2. Designs caching patterns that will work when we add pagination
3. Handles client-side filtering efficiently (API has no server-side filters)
4. Accounts for API limitations (no ETags, no metadata, no delta queries)

### API Capabilities Investigation

**Empirical Testing Performed (2025-11-06):**
- Staging API: `https://api.stage-a.space/customer/v2` (pagination broken)
- Production API: `https://api.test.io/customer/v2` (pagination works)
- Test Product: ID 598 (test IO - HALO) with 89 tests

**Key Findings:**

#### ✅ Pagination Works (Production Only)
```bash
# Unpaginated baseline
GET /products/598/exploratory_tests
→ Returns: 89 tests (full dataset)

# Paginated page 1
GET /products/598/exploratory_tests?page=1&per_page=10
→ Returns: 10 tests (IDs: 109363, 104779, 104777, ...)

# Paginated page 2
GET /products/598/exploratory_tests?page=2&per_page=10
→ Returns: 10 tests (IDs: 96941, 96078, 94853, ...)
→ DIFFERENT tests from page 1 ✓
```

**Staging Issue:** Staging API ignores `page` and `per_page` parameters entirely (returns all tests regardless). This caused initial confusion during testing.

#### ❌ No Server-Side Status Filtering
```bash
GET /products/598/exploratory_tests?status=archived
→ Returns: 89 tests (ALL statuses: archived, initialized)
→ Query parameter ignored
```

**Implication:** To filter by status, must fetch ALL pages and filter in-memory.

#### ❌ No Pagination Metadata
```bash
# Response structure
{
  "exploratory_tests": [...]  // No total_count, total_pages, has_next
}

# Response headers
cache-control: no-cache
# No X-Total-Count, X-Page, Link, or ETag headers
```

**Implications:**
- Cannot display "Showing 1-25 of 250 tests"
- Cannot determine if more pages exist without fetching
- Must fetch pages until empty array returned
- No conditional GET optimization possible

#### ❌ No Delta Query Support
- No `?since_id=X` parameter
- No `?updated_after=YYYY-MM-DD` parameter
- No way to fetch only changed tests

**Implication:** Cannot implement watermark-based caching optimization.

### Current Cache-Raw Bug

The `list_tests()` method violates the cache-raw pattern (ADR-004) by creating separate cache entries per status filter:

```python
# CURRENT (BUG) - Multiple cache entries for same data
list_tests(123, statuses=["running"])   → Cache: "product:123:tests:running"
list_tests(123, statuses=["archived"])  → Cache: "product:123:tests:archived" (MISS)
list_tests(123, statuses=None)          → Cache: "product:123:tests:all" (MISS)

# Result: 25-30% cache hit rate (3 separate caches for same API data)
```

**Expected (cache-raw pattern):**
```python
# FIX - Single cache entry, filter in-memory
list_tests(123, statuses=["running"])   → Cache: "product:123:tests:raw"
list_tests(123, statuses=["archived"])  → Cache: "product:123:tests:raw" (HIT!)
list_tests(123, statuses=None)          → Cache: "product:123:tests:raw" (HIT!)

# Result: 75%+ cache hit rate (1 cache entry serves all filter queries)
```

### Pagination + Filtering Challenges

#### Challenge 1: Page Shift Problem
```
Time T0 (60 tests, per_page=25):
  Page 1: Tests 51-60 (10 tests, most recent)
  Page 2: Tests 26-50 (25 tests)

Time T1 (5 new tests added, now 65 tests):
  Page 1: Tests 56-65 (10 tests) ← DIFFERENT TESTS!
  Page 2: Tests 31-55 (25 tests) ← SHIFTED!

Cached page 1 now shows wrong tests (51-60 instead of 56-65)
```

**Mitigation:** Short TTL (30s) for paginated queries without filters.

#### Challenge 2: Filtering Requires Full Dataset
```
User: "Show me running tests, page 1"
Problem: API doesn't support ?status=running

Required workflow:
1. Fetch ALL pages (page 1, 2, 3, ... N)
2. Filter in-memory by status
3. Paginate filtered results
4. Return requested page

Cost: Product with 1000 tests = 40 API calls (1000 / 25 per_page)
```

**Mitigation:** Very short TTL (10s) + clear performance warnings in docs.

#### Challenge 3: No Total Count Metadata

Without `total_count` in API response, cannot determine:
- How many pages exist
- When to stop fetching pages
- "Showing X-Y of Z" UI text

**Required approach:** Fetch pages until empty array returned.

## Decision

**Implement a two-phase approach:**

### Phase 1: Fix Cache-Raw Bug (Immediate - This PR)
Fix the existing cache violation in `list_tests()` without adding pagination yet.

- ✅ Changes cache key from status-specific to "raw" sentinel
- ✅ Maintains current API behavior (unpaginated, last 150 tests)
- ✅ Improves cache hit rate: 25% → 75%+
- ✅ Consistent with `list_products()` (uses cache-raw pattern)
- ⏱️ Estimated effort: 1 hour (15 min implementation + 30 min tests + 15 min docs)

### Phase 2: Add Pagination Support (Future - When Needed)
Add pagination when users hit the 150 test limit or request it.

- ⏸️ Deferred until clear user need established
- ⏸️ Requirements will be clearer from real usage patterns
- ⏸️ Can decide on filtering strategy with user feedback
- ⏱️ Estimated effort: 2-3 hours (when implemented)

**Rationale for deferral:**
- Current 150 test limit isn't blocking users yet
- Typical products have 50-200 tests (well within limit)
- Pagination adds complexity (page shift, fetch-all-for-filtering, no metadata)
- YAGNI principle: Don't solve problems that don't exist yet
- When needed, design will be informed by actual usage patterns

## Consequences

### Positive

**Phase 1 (Immediate):**
- ✅ Cache hit rate: 25% → 75%+ for list_tests()
- ✅ Consistency: Same cache-raw pattern as list_products()
- ✅ Simplicity: No new complexity, just fix existing bug
- ✅ Performance: Fewer API calls for filtered queries
- ✅ Foundation: Cache key design ready for pagination

**Phase 2 (When Implemented):**
- ✅ Can browse all tests (>150 limit removed)
- ✅ Scalable for customers with 1000+ tests
- ✅ Client-side filtering works with pagination
- ✅ Cache strategy already designed and documented

### Negative

**Phase 1:**
- ⚠️ Still limited to 150 most recent tests (unpaginated mode)
- ⚠️ Cannot browse full historical test catalog if >150 tests

**Phase 2 (When Implemented):**
- ⚠️ Page shift problem (30s TTL mitigates but doesn't eliminate)
- ⚠️ Slow filtered queries for large products (fetch-all expensive)
- ⚠️ No "total count" UI (no metadata from API)
- ⚠️ Cannot determine page boundaries without fetching

### Mitigation Strategies

**Phase 1: 150 Test Limit**
- Document limitation clearly in tool docstrings
- Monitor user feedback for pagination requests
- Log products exceeding 150 tests (future metrics)

**Phase 2: Page Shift**
- Use short TTL (30s) for paginated cache entries
- Document that pages may shift as new tests are added
- Alternative: Disable caching for paginated queries

**Phase 2: Filtered Query Performance**
- Use very short TTL (10s) to avoid repeated expensive operations
- Warn users in docs: "Filtering on products with >500 tests may take 10-30s"
- Future optimization: Request API team to add server-side filters

**Phase 2: No Metadata**
- Implement "fetch until empty" pattern
- Return `has_more: boolean` based on result count
- Document that total count is unavailable

## Pagination-Ready Caching Strategy

### Cache Key Design (Supports Future Pagination)

```python
# Unpaginated (current behavior)
"product:{id}:tests:raw"  # TTL: 5 minutes

# Paginated (no filter) - FUTURE
"product:{id}:tests:page:{page}:per_page:{per_page}"  # TTL: 30 seconds

# Filtered (any status) - FUTURE
"product:{id}:tests:filtered:{status1}:{status2}:page:{page}"  # TTL: 10 seconds
```

**Key design principles:**
1. **"raw" sentinel:** Unpaginated queries always use "raw" (no filter in key)
2. **Page-specific keys:** Paginated keys include page number (page shift acceptable)
3. **Filter-specific keys:** Filtered keys include sorted status list (stable key)
4. **TTL hierarchy:** Shorter TTL for more volatile data (paginated < filtered)

### TTL Strategy

```python
# Unpaginated (complete dataset for small products)
CACHE_TTL_TESTS_UNPAGINATED = 300  # 5 minutes
# - Stable data (last 150 tests rarely change)
# - High cache hit rate
# - Serves all filter queries from one cache entry

# Paginated (no filter, single page)
CACHE_TTL_TESTS_PAGINATED = 30  # 30 seconds
# - Mitigates page shift problem
# - Still useful for rapid pagination browsing
# - Acceptable staleness window

# Filtered (requires fetch-all, then paginate)
CACHE_TTL_TESTS_FILTERED = 10  # 10 seconds
# - Expensive to generate (multiple API calls)
# - Short TTL avoids repeated expensive operations
# - Still provides benefit for dashboard refreshes
```

### Cache Behavior Matrix

| Query Type | API Calls | Cache Key | TTL | Use Case |
|-----------|----------|-----------|-----|----------|
| Unpaginated, no filter | 1 | `product:123:tests:raw` | 5min | Dashboard widgets, quick overview |
| Unpaginated, filter | 1 | `product:123:tests:raw` | 5min | Status-filtered views (≤150 tests) |
| Paginated, no filter | 1/page | `product:123:tests:page:1:per_page:25` | 30s | Browse all tests UI |
| Paginated, filter | ALL pages | `product:123:tests:filtered:running:page:1` | 10s | Status-filtered with pagination |

## Implementation Blueprint

### Phase 1: Fix Cache-Raw Bug (Current PR)

**File: `src/testio_mcp/services/product_service.py`**

```python
async def list_tests(
    self,
    product_id: int,
    statuses: list[str] | None = None,
    include_bug_counts: bool = False,
) -> dict[str, Any]:
    """List tests with cache-raw pattern."""

    # BEFORE (BUG):
    # cache_suffix = (
    #     "all" if statuses is None or len(statuses) == 0
    #     else ":".join(sorted(statuses))
    # )

    # AFTER (FIX):
    cache_suffix = "raw"  # Always use raw sentinel

    cache_key = self._make_cache_key("product", product_id, "tests", cache_suffix)

    # Fetch raw data (cache or API)
    raw_tests = await self._get_cached_or_fetch(
        cache_key=cache_key,
        fetch_fn=lambda: self.client.get(
            f"products/{product_id}/exploratory_tests"
        ),
        ttl_seconds=self.CACHE_TTL_TESTS,
    )

    # Filter in-memory if statuses provided
    tests = raw_tests.get("exploratory_tests", [])
    if statuses and len(statuses) > 0:
        tests = [t for t in tests if t.get("status") in statuses]

    # Build response with filtered tests
    return {
        "product": await self._get_product_info(product_id),
        "statuses_filter": statuses,
        "total_tests": len(tests),
        "tests": tests,
    }
```

**Changes:**
- Line 233-235: Replace status-based cache key with "raw"
- Cache key now: `product:123:tests:raw` (consistent with products)
- Filter logic unchanged (still filters in-memory)

### Phase 2: Add Pagination Support (Future)

**Signature changes:**

```python
async def list_tests(
    self,
    product_id: int,
    statuses: list[str] | None = None,
    page: int | None = None,          # NEW: None = unpaginated
    per_page: int = 25,                # NEW: default 25
    include_bug_counts: bool = False,
) -> dict[str, Any]:
```

**Response format additions:**

```python
{
    "product": {...},
    "tests": [...],
    "statuses_filter": [...],
    "pagination": {           # NEW FIELD
        "page": 2,
        "per_page": 25,
        "has_more": true,     # Based on result count, not metadata
    }
}
```

**Implementation logic:**

```python
# Case 1: Unpaginated (backward compatible)
if page is None:
    cache_key = self._make_cache_key("product", product_id, "tests", "raw")
    # ... fetch and filter as before

# Case 2: Paginated, no filter (efficient)
elif statuses is None or len(statuses) == 0:
    cache_key = self._make_cache_key(
        "product", product_id, "tests", "page", page, "per_page", per_page
    )
    # Fetch single page from API
    tests = await self._get_cached_or_fetch(
        cache_key=cache_key,
        fetch_fn=lambda: self.client.get(
            f"products/{product_id}/exploratory_tests",
            params={"page": page, "per_page": per_page}
        ),
        ttl_seconds=self.CACHE_TTL_TESTS_PAGINATED,  # 30s
    )

# Case 3: Paginated + filter (expensive)
else:
    cache_key = self._make_cache_key(
        "product", product_id, "tests", "filtered",
        ":".join(sorted(statuses)), "page", page
    )

    # Check cache first
    cached = await self.cache.get(cache_key)
    if cached:
        return cached

    # Fetch ALL pages (no cache bypass)
    all_tests = await self._fetch_all_test_pages(product_id, per_page)

    # Filter in-memory
    filtered = [t for t in all_tests if t["status"] in statuses]

    # Paginate filtered results
    start = (page - 1) * per_page
    end = start + per_page
    page_tests = filtered[start:end]

    result = {
        "tests": page_tests,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "has_more": end < len(filtered),
        }
    }

    # Cache filtered page
    await self.cache.set(cache_key, result, self.CACHE_TTL_TESTS_FILTERED)
    return result
```

**Helper method:**

```python
async def _fetch_all_test_pages(
    self, product_id: int, per_page: int = 25
) -> list[dict[str, Any]]:
    """Fetch all test pages until empty array returned.

    No metadata available, so must fetch until empty.
    """
    all_tests = []
    page = 1

    while True:
        response = await self.client.get(
            f"products/{product_id}/exploratory_tests",
            params={"page": page, "per_page": per_page}
        )

        tests = response.get("exploratory_tests", [])
        if not tests:  # Empty array = no more pages
            break

        all_tests.extend(tests)
        page += 1

        # Safety limit (prevent infinite loop)
        if page > 100:  # 100 pages * 25 = 2500 tests max
            break

    return all_tests
```

## Performance Characteristics

### Phase 1: Unpaginated (Current)

**Scenario: Browse tests (no filter)**
- Request: `list_tests(123, statuses=None)`
- API Calls: 1 (GET `/exploratory_tests`)
- Cache: 5min TTL, `product:123:tests:raw`
- Performance: ⚡ Fast (single API call)

**Scenario: Filter by status**
- Request: `list_tests(123, statuses=["running"])`
- API Calls: 1 (GET `/exploratory_tests`)
- Cache: 5min TTL, same key `product:123:tests:raw` (cache HIT!)
- Performance: ⚡ Fast (cache hit, in-memory filter)

### Phase 2: With Pagination (Future)

**Scenario A: Browse all tests (no filter)**
- Request: `list_tests(123, page=1, per_page=25, statuses=None)`
- API Calls: 1 per page
- Cache: 30s TTL, `product:123:tests:page:1:per_page:25`
- Performance: ⚡ Fast (single API call per page)
- Risk: Page shift after 30s

**Scenario B: Filter by status (small product, <150 tests)**
- Request: `list_tests(123, page=1, per_page=25, statuses=["running"])`
- API Calls: 1 (only need page 1 to get all data)
- Cache: 10s TTL, `product:123:tests:filtered:running:page:1`
- Performance: ⚡ Fast (single page fetch, then filter)

**Scenario C: Filter by status (large product, 1000 tests)**
- Request: `list_tests(123, page=1, per_page=25, statuses=["running"])`
- API Calls: 40 (must fetch all 40 pages to filter completely)
- Cache: 10s TTL (avoids repeated expensive operations)
- Performance: 🐌 Slow on first call (40 API calls), fast for 10s
- User Impact: 10-30 second delay for large products

## Testing Strategy

### Phase 1: Cache-Raw Fix

**Unit Tests (tests/unit/test_product_service.py):**
- ✅ `test_list_tests_cache_key_no_filter` - Verify "raw" key
- ✅ `test_list_tests_cache_key_with_filter` - Verify same "raw" key
- ✅ `test_list_tests_filter_in_memory` - Verify filtering works
- ✅ `test_list_tests_cache_hit_across_filters` - Verify single cache entry

**Integration Tests (tests/integration/test_cache_integration.py):**
- ✅ `test_cache_raw_pattern_list_tests` - Verify 1 API call serves multiple filters

### Phase 2: Pagination Support (Future)

**Unit Tests:**
- ✅ `test_list_tests_paginated_no_filter` - Single page API call
- ✅ `test_list_tests_paginated_with_filter` - Fetch all pages + filter
- ✅ `test_list_tests_unpaginated_backward_compat` - Existing behavior preserved
- ✅ `test_list_tests_pagination_metadata` - Verify pagination response fields
- ✅ `test_list_tests_fetch_all_pages` - Verify multi-page fetch stops on empty
- ✅ `test_list_tests_filter_then_paginate` - Verify filter → paginate order

**Integration Tests:**
- ✅ `test_list_tests_pagination_real_api` - Verify pagination works (production only!)
- ✅ `test_list_tests_filtered_pagination_real_api` - Verify filter + page works
- ✅ `test_list_tests_page_shift` - Document page shift behavior (not a bug)

**Important:** Integration tests should use production API (`api.test.io`), not staging (`stage-a.space`), since staging has broken pagination.

## Documentation Requirements

### User-Facing Warnings

**Phase 1: Current Limitation**
```
⚠️ **Test List Limitation**

The `list_tests` tool returns the last 150 tests in reverse chronological order
(most recent first). Products with more than 150 tests will not show full history.

This limitation is due to using the unpaginated API endpoint. Pagination support
is planned for a future release (ADR-014 Phase 2).
```

**Phase 2: Pagination Warnings (Future)**
```
⚠️ **Pagination + Filtering Performance Warning**

When combining status filters with pagination, the system must fetch ALL pages
from the API to perform accurate filtering (API does not support server-side
status filtering). For products with many tests:

- 500 tests: ~5 seconds first request
- 1000 tests: ~10-15 seconds first request
- 2000 tests: ~20-30 seconds first request

Results are cached for 10 seconds to improve subsequent requests.

Recommendations:
- Use status filters sparingly on large products
- Consider unpaginated queries for filtered views (limited to 150 tests)
- For browsing all tests, omit status filters (pagination is fast)
```

```
⚠️ **Page Stability**

Test lists are sorted by most recent first. When new tests are created, page
contents shift (e.g., test #26 on page 2 becomes #27). Cached pages have a
30-second TTL to balance performance vs. freshness.

For stable ordering, use unpaginated queries (returns last 150 tests).
```

### Tool Docstring Updates

**Phase 1:**
```python
"""List exploratory tests for a product.

Returns the last 150 tests in reverse chronological order (most recent first).
Products with >150 tests will not show full historical data.

Args:
    product_id: Product identifier
    statuses: Filter by test status (running, locked, archived, etc.)
              Filtering is performed in-memory after fetching data.
    include_bug_counts: Include bug summary counts per test

Returns:
    Dictionary with product info, filtered tests, and metadata

Note: Pagination support is not yet implemented. See ADR-014 for roadmap.
"""
```

**Phase 2 (Future):**
```python
"""List exploratory tests for a product with optional pagination.

Args:
    product_id: Product identifier
    statuses: Filter by test status (server-side filtering not supported,
              filtering performed in-memory after fetching all pages)
    page: Page number (1-indexed). If None, returns unpaginated (last 150).
    per_page: Results per page (default: 25, max: 100)
    include_bug_counts: Include bug summary counts per test

Returns:
    Dictionary with product info, filtered tests, and pagination metadata

Performance Notes:
    - No filter: Fast (1 API call per page)
    - With filter: Slow for large products (must fetch all pages to filter)
      Products with 1000+ tests may take 10-30 seconds on first request.
      Results cached for 10 seconds.

Page Stability:
    Pages may shift as new tests are added. Use unpaginated mode for
    stable ordering (limited to 150 most recent tests).
"""
```

## Migration Path

### Phase 1: Cache-Raw Fix (This PR - Immediate)

**Implementation:**
1. Update `list_tests()` cache key (5 lines changed)
2. Update 7 unit tests (cache key assertions)
3. Add cache-raw integration test (verify 1 API call → multiple filters)
4. Update tool docstring (document 150 test limitation)

**Deployment:**
- No breaking changes (same API contract)
- Cache keys change (old cache entries become stale, re-fetched once)
- Performance improvement immediate (cache hit rate increases)

**Monitoring:**
- Track cache hit rate for `list_tests()` (expect 25% → 75%+)
- Log products with >150 tests (identify pagination need)

### Phase 2: Pagination Support (Future - When Needed)

**Triggers for implementation:**
1. User complaints about 150 test limit
2. >10% of products exceed 150 tests
3. Performance issues with unpaginated queries (>5s response times)
4. Cache hit rate drops below 70% (indicates data too volatile for 5min TTL)

**Pre-implementation checklist:**
- [ ] Confirm production API pagination still works (re-test)
- [ ] Gather usage metrics (% queries with filters, typical product size)
- [ ] Decide on filtering strategy (fetch-all vs. disable filters when paginated)
- [ ] User acceptance: Are they okay with 30s page shift or prefer no cache?

**Implementation steps:**
1. Add `page` and `per_page` parameters to `list_tests()` signature
2. Implement conditional logic (unpaginated vs. paginated vs. filtered)
3. Add `_fetch_all_test_pages()` helper method
4. Update cache key generation for pagination
5. Add pagination metadata to response
6. Write 6 new unit tests (pagination scenarios)
7. Write 3 new integration tests (production API)
8. Update tool docstrings (performance warnings)
9. Create user documentation (when to use pagination, performance expectations)

**Deployment:**
- Breaking change: New response format (add `pagination` field)
- Consider versioning if external integrations exist
- Monitor filtered query performance (alert if >30s p95 latency)

## Alternatives Considered

### Alternative 1: Implement Pagination Now
**Rejected because:**
- YAGNI: No evidence of user need yet
- Adds complexity: Page shift, fetch-all-for-filtering, no metadata
- Watermark research showed 5.7x code complexity for 0% benefit
- Current 150 test limit isn't blocking users
- Requirements unclear (page shift tolerance? disable filtering when paginated?)

**When to reconsider:** User complaints or metrics show >10% products exceed 150 tests.

### Alternative 2: Watermark-Based Caching
**Rejected because:**
- Requires delta queries (`?since_id=X`) - API doesn't support
- Would add 85 LOC vs. 15 LOC for cache-raw fix
- 8 new edge cases (test unlocks, watermark shifts, duplicates)
- 0% API call reduction (still fetch all tests on cache miss without delta support)
- Massive complexity for theoretical benefit

**When to reconsider:** API team adds delta query support.

### Alternative 3: Disable Caching for Paginated Queries
**Rejected because:**
- Poor user experience (every page navigation = API call)
- Contradicts ADR-004 (cache-first strategy)
- Page shift is acceptable with 30s TTL (rapid browsing within window)

**When to reconsider:** Page shift complaints from users.

### Alternative 4: Implement Server-Side Filtering
**Not possible:**
- API doesn't support server-side status filtering (confirmed by testing)
- Only option: Request API team to add filtering support

**When to reconsider:** API team adds `?status=running` support.

## References

- **ADR-004:** Cache Strategy MVP (cache-raw pattern)
- **ADR-006:** Service Layer Pattern (business logic separation)
- **ADR-007:** FastMCP Context Injection Pattern
- **TestIO Customer API:** `/products/{id}/exploratory_tests` endpoint
- **API Documentation:** `docs/apis/customer-api.apib` lines 552-710
- **Empirical Testing Results:** This document, "API Capabilities Investigation" section

## Appendix: API Test Script

For future reference or re-validation:

```bash
#!/bin/bash
# Test TestIO API pagination capabilities
# Usage: ./test_api_pagination.sh

TOKEN="your-token-here"
BASE_URL="https://api.test.io/customer/v2"
PRODUCT_ID=598

echo "=== Test 1: Unpaginated baseline ==="
curl -s -H "Authorization: Token $TOKEN" \
  "${BASE_URL}/products/${PRODUCT_ID}/exploratory_tests" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print(f'Total: {len(data[\"exploratory_tests\"])}')"

echo ""
echo "=== Test 2: Paginated (page=1, per_page=10) ==="
curl -s -H "Authorization: Token $TOKEN" \
  "${BASE_URL}/products/${PRODUCT_ID}/exploratory_tests?page=1&per_page=10" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print(f'Total: {len(data[\"exploratory_tests\"])}'); print(f'IDs: {[t[\"id\"] for t in data[\"exploratory_tests\"]]}')"

echo ""
echo "=== Test 3: Paginated (page=2, per_page=10) ==="
curl -s -H "Authorization: Token $TOKEN" \
  "${BASE_URL}/products/${PRODUCT_ID}/exploratory_tests?page=2&per_page=10" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); print(f'Total: {len(data[\"exploratory_tests\"])}'); print(f'IDs: {[t[\"id\"] for t in data[\"exploratory_tests\"]]}')"

echo ""
echo "=== Test 4: Status filter test ==="
curl -s -H "Authorization: Token $TOKEN" \
  "${BASE_URL}/products/${PRODUCT_ID}/exploratory_tests?status=archived" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); tests = data['exploratory_tests']; print(f'Total: {len(tests)}'); print(f'Statuses: {set(t[\"status\"] for t in tests)}')"

echo ""
echo "=== Test 5: Check for pagination metadata ==="
curl -sI -H "Authorization: Token $TOKEN" \
  "${BASE_URL}/products/${PRODUCT_ID}/exploratory_tests?page=1&per_page=10" | \
  grep -i "etag\|x-total\|x-page\|link"
```

**Expected results (as of 2025-11-06):**
- Test 1: Returns 89 tests (full dataset)
- Test 2: Returns 10 tests, page 1 IDs
- Test 3: Returns 10 tests, page 2 IDs (different from page 1)
- Test 4: Returns 89 tests with all statuses (filter ignored)
- Test 5: No pagination headers found

---

## Recommendation

**Proceed with Phase 1 immediately:**
- Fix cache-raw bug (1 hour effort)
- Document pagination deferral rationale
- Monitor for user feedback

**Defer Phase 2 until triggered:**
- User complaints about 150 test limit
- Metrics show >10% products exceed 150 tests
- Clear requirements from real usage patterns

This approach:
- ✅ Fixes real bug now
- ✅ Improves performance immediately
- ✅ Avoids premature optimization
- ✅ Keeps codebase simple
- ✅ Preserves optionality for future
- ✅ Evidence-based decision making
