# TestIO Customer API - Capabilities and Limitations

**Version:** 1.0
**Last Updated:** 2025-11-20
**Source:** Empirical testing (2025-11-06), extracted from ADR-014

---

## Overview

This document captures empirical findings about TestIO Customer API behavior, limitations, and capabilities. It serves as a reference for developers working with the API.

**Testing Environment:**
- **Staging API:** `https://api.stage-a.space/customer/v2` (pagination broken)
- **Production API:** `https://api.test.io/customer/v2` (pagination works)
- **Test Product:** ID 598 (test IO - HALO) with 89 tests

---

## Pagination Behavior

### Production API: ✅ Working

```bash
# Unpaginated baseline
GET /products/598/exploratory_tests
→ Returns: All tests (89 tests for test product)

# Paginated page 1
GET /products/598/exploratory_tests?page=1&per_page=10
→ Returns: 10 tests (IDs: 109363, 104779, 104777, ...)

# Paginated page 2
GET /products/598/exploratory_tests?page=2&per_page=10
→ Returns: 10 tests (IDs: 96941, 96078, 94853, ...)
→ DIFFERENT tests from page 1 ✓
```

**Key Findings:**
- Pagination works correctly on production API
- Pages return different test sets (no duplication)
- Results sorted by most recent first (reverse chronological)

### Staging API: ❌ Broken

- Staging API ignores `page` and `per_page` parameters
- Always returns full dataset regardless of pagination params
- **Recommendation:** Use production API for testing pagination

---

## Server-Side Filtering

### Status Filtering: ❌ Not Supported

```bash
GET /products/598/exploratory_tests?status=archived
→ Returns: ALL tests (all statuses: archived, initialized, running, etc.)
→ Query parameter ignored
```

**Implication:** To filter by status, must fetch data and filter client-side (or use SQLite queries in local database).

**Current Implementation:** SQLite database stores all tests, filtering done via SQL queries for efficiency.

---

## Pagination Metadata

### Response Structure: ❌ No Metadata

```json
{
  "exploratory_tests": [...]
  // No total_count, total_pages, has_next fields
}
```

### Response Headers: ❌ No Pagination Headers

```bash
cache-control: no-cache
# No X-Total-Count, X-Page, Link, or ETag headers
```

**Implications:**
- Cannot display "Showing 1-25 of 250 tests" without counting locally
- Cannot determine if more pages exist without fetching
- Must fetch pages until empty array returned
- No conditional GET optimization possible (no ETags)

---

## Delta Query Support

### Incremental Sync: ❌ Not Supported

- No `?since_id=X` parameter
- No `?updated_after=YYYY-MM-DD` parameter
- No way to fetch only changed tests

**Implication:** Cannot implement watermark-based caching optimization. Must use SQLite-based incremental sync (STORY-021) instead.

**Current Implementation:** Local database tracks last sync position, fetches new tests by stopping at first known test.

---

## API Endpoints Used

| Endpoint | Method | Purpose | Pagination | Filtering |
|----------|--------|---------|------------|-----------|
| `/products` | GET | List all products | ✅ Yes | ❌ No |
| `/products/{id}/exploratory_tests` | GET | List tests for product | ✅ Yes | ❌ No |
| `/exploratory_tests/{id}` | GET | Get single test details | N/A | N/A |
| `/exploratory_tests/{id}/bugs` | GET | Get bugs for test | ✅ Yes | ❌ No |

---

## Rate Limits

**Status:** Unknown (not documented in API)

**Current Mitigation:**
- Global semaphore: 10 concurrent requests (configurable via `MAX_CONCURRENT_API_REQUESTS`)
- Connection pooling: 20 connections max
- Retry with exponential backoff on 429 errors
- Connection keep-alive: 20 seconds

**Recommendation:** Monitor for 429 responses, adjust semaphore if needed.

---

## Known Limitations

1. **No ETags:** API does not support conditional requests (`If-None-Match`)
2. **No Delta Queries:** Cannot request "changes since timestamp"
3. **No Server-Side Filtering:** Status filtering must be done client-side or via local database
4. **No Pagination Metadata:** Responses don't include total count or pagination info
5. **Staging Pagination Broken:** Use production API for testing pagination features
6. **No Sorting Options:** Results always sorted by most recent first (cannot customize)

---

## Performance Characteristics

### Typical Response Times
- **Single test fetch:** ~200-500ms
- **Product list (unpaginated):** ~300-800ms
- **Test list (25 tests, paginated):** ~400-900ms
- **Bug list (100 bugs):** ~500-1200ms

**Note:** Times vary based on network latency and API load.

### Concurrency
- **Max concurrent requests:** 10 (configurable)
- **Connection pool size:** 20 connections
- **Keep-alive:** 20 seconds

---

## Testing Script

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

**Expected Results (as of 2025-11-06):**
- Test 1: Returns 89 tests (full dataset)
- Test 2: Returns 10 tests, page 1 IDs
- Test 3: Returns 10 tests, page 2 IDs (different from page 1)
- Test 4: Returns 89 tests with all statuses (filter ignored)
- Test 5: No pagination headers found

---

## References

- **ADR-014:** [Pagination-Ready Caching Strategy](adrs/ADR-014-pagination-ready-caching-strategy.md) (superseded, historical context)
- **ARCHITECTURE.md:** [API Client Design](ARCHITECTURE.md#api-client-design)
- **STORY-021:** [Local Data Store](../stories/done/story-021-local-data-store.md) (current implementation)
- **Empirical Testing:** 2025-11-06 (Product 598 - test IO HALO)

---

**Document Status:** ✅ Active Reference
**Next Review:** After API version changes or new endpoint additions
