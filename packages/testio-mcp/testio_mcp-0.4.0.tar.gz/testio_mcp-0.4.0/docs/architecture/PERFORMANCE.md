# Performance Guidelines - TestIO MCP Server

**Version:** 2.0 (SQLite-First Architecture)
**Last Updated:** 2025-11-18
**Previous Version:** Archived (InMemoryCache-based v1.0)

---

## Performance Targets

### From Project Brief

**Primary Goal:** 99% of queries respond in < 5 seconds (P99 latency)

**Why 5 seconds?**
- AI clients (Claude/Cursor) timeout at 30-60 seconds
- User attention span for conversational AI is ~5-10 seconds
- Reduces perceived lag in interactive sessions

**No Hard Error Rate Target for MVP**
- Monitor and optimize based on real usage
- Acceptable errors: Transient API failures, network timeouts
- Unacceptable errors: Bugs, validation failures, crashes

---

## Architecture Overview

### SQLite-First Data Access Pattern

```
MCP Tool Call
    ↓
Service Layer
    ↓
    ├─ Query Local SQLite (PersistentCache) ← FAST (~10ms)
    │  └─ If data exists → Return immediately
    │
    └─ Fallback to API (TestIOClient) ← SLOWER (~200ms+)
       └─ Store in SQLite → Available for next query
```

**Key Characteristics:**
- **No TTL management** - Data stays fresh via background sync
- **No cache eviction** - SQLite database persists across restarts
- **No stampede protection** - Local queries don't cause contention
- **Transparent to MCP tools** - Tools query services, services decide data source

---

## Performance Optimization Strategies

### 1. Local SQLite Datastore (Primary Strategy)

**Expected Impact:** 95%+ reduction in API calls for repeat queries

**Performance Characteristics:**
```python
# Local SQLite query (PersistentCache)
service.list_tests(product_id=598)
→ SQLite query (~10ms at our scale)
→ Return results ✨ FAST

# vs. Direct API call
client.get("products/598/exploratory_tests")
→ HTTP request (~200ms+ network latency)
→ Parse JSON, normalize timestamps
→ Return results ✨ SLOWER
```

**Database Size Metrics:**
- **~25MB for 1000 tests** (lightweight)
- **WAL mode** - Concurrent reads during background writes
- **VACUUM on startup** - Compact database, reclaim space
- **Indexed queries** - product_id, test_id, status, dates

**When Local Data is Used:**
- ✅ list_products - All products cached locally
- ✅ list_tests - Tests for product cached locally
- ✅ get_test_status - Individual test cached locally
- ✅ get_database_stats - Pure SQLite metadata query
- ✅ get_problematic_tests - Sync failure tracking

**When API is Called:**
- ⚠️ Data doesn't exist locally (first query after fresh install)
- ⚠️ Forced refresh requested (--force, --refresh flags in CLI)
- ⚠️ Background sync discovers new tests (incremental sync)

---

### 2. Background Sync (Keeps Data Fresh)

**Expected Impact:** Users always see fresh data without API latency

**Sync Mechanisms:**

**1. Initial Sync (Server Startup)**
```
Server starts
    ↓
Background task: sync_all_products()
    ↓
Fetch all products → Store in SQLite
    ↓
For each product:
    ├─ Incremental sync (fetch only new tests)
    └─ Stop at first known test + 2 safety pages
```

**2. Background Refresh (Periodic)**
```
Every 5 minutes (configurable via TESTIO_REFRESH_INTERVAL_SECONDS)
    ↓
Check staleness (last_refresh_at > interval)
    ↓
Refresh active products (tests created within 7 days)
    ↓
Update mutable tests only (status != 'locked'/'cancelled')
```

**3. Manual Sync (CLI Command)**
```bash
# Incremental sync (default) - Discovers new tests only
testio-mcp sync

# Force refresh - Updates ALL tests for product
testio-mcp sync --force --product-ids 598

# Hybrid refresh - Discover new + update mutable tests
testio-mcp sync --refresh --product-ids 598

# Nuclear rebuild - Delete + resync from scratch
testio-mcp sync --nuke --yes
```

**Sync Performance:**
- **Incremental sync:** Fast (stops at known boundary + 2 pages)
- **Force refresh:** Slower (re-fetches all tests)
- **Hybrid refresh:** Medium (new tests + mutable only)
- **Page size:** 25 tests per page (API default)
- **Boundary detection:** Newest test ID + safety margin

**Configuration:**
```bash
# .env
TESTIO_REFRESH_INTERVAL_SECONDS=300  # 5 minutes (0=disabled)
TESTIO_PRODUCT_IDS=598,1024          # Filter products to sync
```

---

### 3. Connection Pooling (Secondary Strategy)

**Expected Impact:** 50-200ms reduction per API request

**Without Pooling:**
```
Request → TCP handshake (50ms) → TLS handshake (100ms) → HTTP request (50ms) = 200ms overhead
```

**With Pooling:**
```
Request → Reuse connection → HTTP request (50ms) = 150ms saved ✨
```

**Configuration:**
```python
# src/testio_mcp/client.py
httpx.Limits(
    max_connections=100,             # Total connections
    max_keepalive_connections=20,    # Idle connections to keep
)
```

**Tuning:**
- Increase if semaphore wait times are high
- Decrease if running out of file descriptors
- Default (100/20) is good for most workloads

---

### 4. Concurrency Control (Prevent Overload)

**Expected Impact:** Prevents catastrophic slowdowns

**Without Limits:**
```
100 requests → All hit API → API overwhelmed → 503 errors → All fail
```

**With Semaphore (10 concurrent):**
```
100 requests → 10 active, 90 queued → Graceful queueing → All succeed (slowly)
```

**Semaphore Wait Time:**
- **<10ms:** Excellent (limit not constraining)
- **10-100ms:** Good (some queueing, acceptable)
- **>100ms:** Consider increasing `MAX_CONCURRENT_API_REQUESTS`

**Tuning:**
```bash
# .env
MAX_CONCURRENT_API_REQUESTS=10   # Default: safe
MAX_CONCURRENT_API_REQUESTS=20   # If no 429 errors observed
MAX_CONCURRENT_API_REQUESTS=50   # If TestIO confirms high limits
```

---

### 5. Pagination (Reduce Response Size)

**Expected Impact:** Prevents slow queries for large datasets

**Client-Side Pagination (Current):**
```python
# list_tests - Query SQLite, paginate results in-memory
result = await service.list_tests(
    product_id=598,
    page=1,
    per_page=100  # Default
)
```

**Server-Side Pagination (API Calls):**
```python
# sync_product_tests - Fetch paginated data from API
while has_more_pages:
    page_data = await client.get(
        f"products/{product_id}/exploratory_tests",
        params={"page": page, "per_page": 25}  # API default
    )
    await cache.insert_tests(page_data)
```

**Pagination Strategy:**
- **SQLite queries:** Fast enough to query all, paginate in-memory
- **API sync:** Use API pagination (25 tests/page)
- **Future optimization:** Add LIMIT/OFFSET to SQLite queries if needed

---

### 6. Parallel Fetching (When Appropriate)

**Use Cases:**
- Background sync: Fetch multiple products concurrently
- Multi-test reports: Fetch test status for multiple tests in parallel

**Example:**
```python
# Sequential (slow)
for product_id in product_ids:
    await sync_product_tests(product_id)  # 2s each
= 10s for 5 products

# Parallel (fast)
await asyncio.gather(*[
    sync_product_tests(product_id)
    for product_id in product_ids
])
= 2s for 5 products ✨ 5x faster (limited by semaphore)
```

**When NOT to use:**
- Requests have dependencies (need result of first to make second)
- Risk of overwhelming API (semaphore provides protection)

---

## Performance Monitoring

### Key Metrics to Track

**Database Metrics (PersistentCache):**
```python
@dataclass
class DatabaseStats:
    database_size_mb: float          # Current SQLite file size
    total_tests: int                 # Tests stored in database
    total_products: int              # Products tracked
    products_synced: int             # Products with at least one sync
    oldest_test_date: str | None     # Earliest test in database
    newest_test_date: str | None     # Most recent test in database
    last_sync_at: datetime           # Last successful sync timestamp
```

**Sync Performance Metrics:**
```python
@dataclass
class SyncResult:
    new_tests_count: int             # New tests discovered
    skipped_tests: int               # Tests skipped (known boundary)
    completed: bool                  # Sync completed successfully
    boundary_info: dict              # Pagination metadata
    recovery_attempts: int           # 500 error recovery attempts
```

**API Metrics:**
```python
@dataclass
class APIMetrics:
    api_requests: int                # Total API calls
    api_errors: int                  # Failed requests
    api_latency_p50: float          # Median API response time
    api_latency_p95: float          # 95th percentile latency
    api_latency_p99: float          # 99th percentile latency
    semaphore_wait_time_p95: float  # Concurrency queueing delay
```

**Tool Metrics:**
```python
@dataclass
class ToolMetrics:
    tool_calls: dict[str, int]       # Calls per tool
    tool_errors: dict[str, int]      # Errors per tool
    tool_latency_p99: dict[str, float]  # P99 latency per tool
```

### Accessing Metrics

```bash
# Database statistics (via MCP tool)
get_database_stats()

# Sync history (via MCP tool)
get_sync_history(limit=10)

# Problematic tests (500 errors during sync)
get_problematic_tests(product_id=598)

# CLI sync status
testio-mcp sync --status
```

---

## Performance Testing

### Unit Test Performance (~0.5s for 138 tests)

**Characteristics:**
- Mock all external dependencies (API, database)
- Focus on business logic performance
- Target: <1ms per test

**Example:**
```python
@pytest.mark.unit
async def test_filter_products_performance():
    """Verify in-memory filtering is fast (<1ms)."""
    products = [{"id": i, "name": f"Product {i}"} for i in range(1000)]

    start = time.time()
    filtered = service._apply_filters(products, search="500")
    duration = time.time() - start

    assert duration < 0.001, f"Filtering took {duration}s (should be <1ms)"
```

### Integration Test Performance (~30s for 20+ tests)

**Characteristics:**
- Real API calls (with credentials)
- Real database operations (temp SQLite file)
- Target: <2s per test (API latency dominated)

**Example:**
```python
@pytest.mark.integration
async def test_sync_product_tests_performance(test_cache):
    """Verify incremental sync completes quickly."""
    start = time.time()
    result = await test_cache.sync_product_tests(product_id=598)
    duration = time.time() - start

    # Should complete in <5s (depends on network)
    assert duration < 5.0, f"Sync took {duration}s"
    assert result.completed is True
```

### Load Testing (Future: Story 9)

**Test Scenario: Concurrent MCP Tool Calls**
```python
@pytest.mark.performance
async def test_100_concurrent_tool_calls():
    """Simulate 100 users querying simultaneously."""
    tasks = [
        list_tests(product_id=598, ctx=mock_ctx)
        for _ in range(100)
    ]

    start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start

    # All queries hit local SQLite (should be VERY fast)
    assert duration < 1.0, f"100 queries took {duration}s (should be <1s)"

    # Verify success rate
    failures = sum(1 for r in results if isinstance(r, Exception))
    success_rate = (100 - failures) / 100 * 100
    assert success_rate > 99, f"Success rate {success_rate}% < 99%"
```

---

## Performance Troubleshooting

### Symptom: Queries taking >5 seconds

**Diagnosis:**
1. Check if data exists locally: `get_database_stats()`
2. Check API latency: Are API calls being made? (log level DEBUG)
3. Check semaphore wait time: Are requests queuing?
4. Check database size: Is SQLite file >100MB?

**Solutions:**
- **No local data:** Run initial sync: `testio-mcp sync`
- **Slow API:** Check TestIO API health, reduce concurrent requests
- **High semaphore wait:** Increase `MAX_CONCURRENT_API_REQUESTS`
- **Large database:** This is normal! SQLite handles GB files efficiently

---

### Symptom: Stale data (not seeing recent tests)

**Diagnosis:**
1. Check last sync time: `get_database_stats()` → `last_sync_at`
2. Check refresh interval: `TESTIO_REFRESH_INTERVAL_SECONDS` in .env
3. Check product filter: Is product excluded via `TESTIO_PRODUCT_IDS`?

**Solutions:**
- **Last sync >1 hour ago:** Enable background refresh (`TESTIO_REFRESH_INTERVAL_SECONDS=300`)
- **Background refresh disabled:** Set non-zero interval
- **Product filtered:** Add product ID to `TESTIO_PRODUCT_IDS`
- **Force immediate refresh:** `testio-mcp sync --refresh --product-ids 598`

---

### Symptom: High memory usage

**Diagnosis:**
1. Check database size: `get_database_stats()` → `database_size_mb`
2. Check connection pool: Are connections being closed?
3. Check SQLite WAL file: Is it growing unbounded?

**Solutions:**
- **Large database:** Normal for 1000+ tests (~25MB). Not a concern unless >500MB.
- **Connection leaks:** Verify `async with` context managers used everywhere
- **Large WAL:** Run `VACUUM` manually or restart server (auto-VACUUM on startup)

---

### Symptom: Failed sync (500 errors from API)

**Diagnosis:**
1. Check problematic tests: `get_problematic_tests(product_id=598)`
2. Check sync history: `get_sync_history(limit=10)`
3. Identify boundary info: Which page/position failed?

**Solutions:**
- **Specific test failing:** Map test ID to event: `testio-mcp problematic map-tests <event_id> <test_id>`
- **Retry after TestIO fixes:** `testio-mcp problematic retry 598`
- **Clear after resolution:** `testio-mcp problematic clear --yes`

**Example Workflow:**
```bash
# 1. Sync fails at page 5, position 100-124
testio-mcp sync --product-ids 598
# Error: API returned 500 at page 5

# 2. View failed events
testio-mcp problematic list
# Event abc-123: Product 598, Page 5, Boundary ID 123455

# 3. Contact TestIO support to identify problematic test IDs
# Support identifies: Test IDs 123456, 123457, 123458

# 4. Map test IDs to event
testio-mcp problematic map-tests abc-123 123456 123457 123458

# 5. After TestIO fixes the issue, retry
testio-mcp problematic retry 598

# 6. Clear resolved events
testio-mcp problematic clear --yes
```

---

## Performance Best Practices

### DO ✅

1. **Query local SQLite first** - Services handle fallback to API automatically
2. **Enable background refresh** - Keep data fresh without user intervention
3. **Use incremental sync** - Default sync mode is efficient
4. **Batch independent requests** - Use `asyncio.gather` for parallel operations
5. **Respect semaphore limits** - Don't bypass concurrency control
6. **Monitor database stats** - Track growth, sync freshness
7. **Use connection pooling** - Reuse HTTP connections
8. **Profile with real data** - Test with production workloads

### DON'T ❌

1. **Don't bypass local data** - Trust the sync process
2. **Don't disable background refresh "just because"** - Data becomes stale
3. **Don't run `--nuke` without confirmation** - Destructive, deletes all data
4. **Don't create new clients per request** - Use dependency injection
5. **Don't disable semaphore for "speed"** - Protects from overload
6. **Don't query API when local data exists** - Defeats purpose of SQLite-first
7. **Don't ignore sync failures** - File tickets with TestIO support
8. **Don't guess at performance** - Measure with real metrics

---

## Performance Tuning Checklist

Before declaring performance issue:

- [ ] Checked if local data exists: `get_database_stats()`
- [ ] Checked last sync time (should be <5 minutes if refresh enabled)
- [ ] Checked API response times (TestIO API latency via DEBUG logs)
- [ ] Checked semaphore wait times (queueing delays)
- [ ] Checked database size (normal: ~25MB per 1000 tests)
- [ ] Checked error logs (sync failures? API errors?)
- [ ] Tested with realistic data (not just small test sets)
- [ ] Verified background refresh is enabled (`TESTIO_REFRESH_INTERVAL_SECONDS > 0`)

---

## Benchmarks (Current Architecture)

### Pre-ORM Baseline (aiosqlite - Before Epic 006)

**Baseline Methodology Note (STORY-030):**
The performance values below represent approximate observed latencies in the pre-ORM architecture (aiosqlite direct queries). These served as the baseline for Epic-006 ORM refactor regression testing. Precise p50/p95/p99 percentile measurements were not captured pre-ORM; values shown are representative averages from development observations.

**Regression Threshold:** Post-ORM p95 must stay < 20ms for critical queries (20% tolerance from ~10-15ms baseline).

```
Operation: list_products (local SQLite)
└─ Query all products: ~10ms (avg) ✅ Excellent (imperceptible)

Operation: list_tests (local SQLite)
├─ Query 10 tests: ~10ms (avg) ✅ Excellent
├─ Query 100 tests: ~15ms (avg) ✅ Excellent
├─ Query 500 tests: ~25ms (avg) ✅ Excellent
└─ Query 1000+ tests: ~50ms (avg) ✅ Very Good

Operation: get_test_status (local SQLite)
├─ Single test (cached): ~5ms ✅ Excellent
└─ Single test (with joins): ~10ms ✅ Excellent

Operation: get_database_stats (pure SQLite metadata)
└─ Stats query: <5ms ✅ Excellent
```

---

### Post-ORM Performance (SQLModel + AsyncSession - After Epic 006)

**Measured:** 2025-11-23 (Epic 006 Retrospective)
**Architecture:** SQLModel ORM with AsyncSession, Alembic migrations
**Baseline Revision:** `0965ad59eafa`
**Methodology:** 100 iterations, warm cache, p50/p95/p99 percentiles
**Benchmark Scripts:** `scripts/benchmark_list_products.py`, `scripts/benchmark_list_tests.py`

#### Critical Query Performance (Measured)

**list_products() - Service Layer Query:**
```
Iterations: 100 (warm cache)
Database: ~/.testio-mcp/cache.db

Results:
  Min:  2.19 ms
  p50:  2.29 ms
  Mean: 2.35 ms
  p95:  2.69 ms ✅ (threshold: < 15ms)
  p99:  2.90 ms
  Max:  2.90 ms

Verdict: ✅ PASSED - 82% faster than threshold (2.69ms vs 15ms)
```

**list_tests() - Service Layer Query:**
```
Iterations: 100 (warm cache)
Product: 25073
Database: ~/.testio-mcp/cache.db

Results:
  Min:  1.58 ms
  p50:  1.66 ms
  Mean: 1.88 ms
  p95:  1.93 ms ✅ (threshold: < 20ms)
  p99:  19.93 ms
  Max:  19.93 ms

Verdict: ✅ PASSED - 90% faster than threshold (1.93ms vs 20ms)
```

#### Performance Analysis

**Pre-ORM vs Post-ORM Comparison:**

| Operation | Pre-ORM (Avg) | Post-ORM (p95) | Change | Status |
|-----------|---------------|----------------|--------|--------|
| list_products | ~10ms | 2.69ms | **73% faster** | ✅ Improved |
| list_tests | ~10-15ms | 1.93ms | **81-87% faster** | ✅ Improved |

**Key Findings:**
- ✅ **No performance regression** - ORM refactor improved performance vs baseline
- ✅ **Significant headroom** - Both operations well under regression thresholds
- ✅ **Consistent performance** - Low variance (p95 close to p50)
- ✅ **Epic 005 readiness** - Ample headroom for feature sync (< 30s), user story sync (< 45s)

**Performance Improvements Attributed To:**
1. SQLModel query optimization (compiled query plans)
2. Proper AsyncSession lifecycle management (no resource leaks)
3. Efficient ORM model serialization (Pydantic integration)
4. Maintained database indexes from pre-ORM architecture
5. WAL mode concurrent reads (unchanged)

### API Sync Performance

```
Operation: Initial sync (first time)
├─ 1 product, 25 tests: ~2s ✅ Good
├─ 3 products, 100 tests: ~5s ✅ Acceptable
└─ 10 products, 500 tests: ~15s ⚠️ Slow but one-time cost

Operation: Incremental sync (finds new tests)
├─ No new tests (stops immediately): ~200ms ✅ Excellent
├─ 10 new tests: ~1s ✅ Good
└─ 100 new tests: ~5s ✅ Acceptable

Operation: Force refresh (--force)
├─ 25 tests: ~2s ✅ Good
├─ 100 tests: ~8s ⚠️ Acceptable (comprehensive update)
└─ 500 tests: ~30s ⚠️ Slow but comprehensive

Operation: Hybrid refresh (--refresh, mutable only)
├─ 50 mutable tests: ~4s ✅ Good
└─ 200 mutable tests: ~15s ⚠️ Acceptable
```

### MCP Tool Performance (with local data)

```
Tool: health_check
└─ Response time: <50ms ✅ Excellent (API ping only)

Tool: list_products
└─ Response time: ~10ms ✅ Excellent (pure SQLite)

Tool: list_tests
├─ Product with 25 tests: ~10ms ✅ Excellent
├─ Product with 100 tests: ~15ms ✅ Excellent
└─ Product with 500+ tests: ~30ms ✅ Very Good

Tool: get_test_status
├─ Local data: ~10ms ✅ Excellent
└─ API fallback: ~500ms ⚠️ Acceptable (rare)

Tool: get_database_stats
└─ Response time: <5ms ✅ Excellent (metadata only)

Tool: get_problematic_tests
└─ Response time: ~10ms ✅ Excellent (pure SQLite)
```

**Note:** Benchmarks measured at current scale (~700 tests, 3 products). Performance remains excellent due to:
- SQLite efficiency (indexed queries)
- WAL mode (concurrent reads)
- Normalized timestamps (UTC, fast comparisons)
- Proper schema design (primary keys, foreign keys, indexes)

---

## HTTP Transport Mode Performance (STORY-023a)

### stdio vs HTTP Mode

**stdio mode (single client):**
```
Client → stdin/stdout → Server (same process)
└─ Latency: <1ms (IPC)
└─ Concurrency: Single client only
└─ Logging: Hidden by stdio transport
```

**HTTP mode (multiple clients):**
```
Client 1 → HTTP → Server (port 8080)
Client 2 → HTTP → Server (port 8080)
Client 3 → HTTP → Server (port 8080)
└─ Latency: ~5ms (localhost HTTP)
└─ Concurrency: Multiple clients (shared SQLite, single sync process)
└─ Logging: Visible in terminal
```

**Performance Comparison:**
- **stdio mode:** Slightly faster (<1ms IPC), but only one client
- **HTTP mode:** Slightly slower (~5ms HTTP overhead), but:
  - ✅ No database lock conflicts (single process)
  - ✅ No redundant API calls (single sync process)
  - ✅ Better resource utilization
  - ✅ Logs visible for debugging

**Recommendation:** Use HTTP mode when running multiple MCP clients (Claude Code + Cursor + Inspector)

---

## References

- [ADR-002: Concurrency Limits](adrs/ADR-002-concurrency-limits.md)
- [ADR-003: Pagination Strategy](adrs/ADR-003-pagination-strategy.md)
- [STORY-021: Local Data Store](../stories/done/story-021-local-data-store.md) - PersistentCache implementation
- [STORY-023a: HTTP Transport](../stories/done/story-023a-http-transport.md) - HTTP mode for multiple clients
- [STORY-023c: Architecture Simplification](../stories/done/story-023c-architecture-simplification.md) - Repository pattern
- [E2E Testing Results](../qa/gates/post-refactoring-e2e-testing.yml) - Performance validation

---

**Document History:**
- **v2.0 (2025-11-18):** Complete rewrite for SQLite-first architecture
- **v1.0 (2025-11-04):** Original version (InMemoryCache-based, archived)
