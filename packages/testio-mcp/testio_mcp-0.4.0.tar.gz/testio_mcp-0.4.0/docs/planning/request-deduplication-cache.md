# Request Deduplication Cache - Planning Document

**Date:** 2025-11-27
**Author:** Ricardo Leon (with Claude Code)
**Status:** Planning
**Epic:** TBD (candidate for Epic 008: MCP Layer Optimization)

---

## Problem Statement

### Current Behavior

When multiple MCP clients call `sync_data()` in rapid succession, each sync operation makes identical API calls even though the data hasn't changed:

```
Time: 0s     - Request 1: sync_data() → Lock acquired
Time: 0.5s   - Request 2: sync_data() → Waiting for lock
Time: 0.7s   - Request 3: sync_data() → Waiting for lock
Time: 1.8s   - Request 1: Complete (3 API calls: /products, /features, /tests)
Time: 1.85s  - Request 2: Lock acquired → Makes SAME 3 API calls
Time: 4.5s   - Request 2: Complete
Time: 4.55s  - Request 3: Lock acquired → Makes SAME 3 API calls again
Time: 6.2s   - Request 3: Complete

Total: 6.2s, 9 API calls (6 redundant)
```

### Evidence

**Live testing results** (2025-11-27):
- 3 rapid `sync_data()` calls to product 25043
- Event IDs: 65, 66, 67
- Each made fresh API calls within 2-5 seconds of previous call
- Server logs show: "0/1 from SQLite (0.0% hit rate), 1 from API" for each request
- Total time: 6.3s (1.8s + 2.7s + 1.7s)

**Wasted resources:**
- 66% of API calls were redundant (6 out of 9)
- 67% slower than optimal (6.3s vs ~2s if cached)
- Unnecessary API load (rate limit risk, infrastructure cost)

### When This Occurs

**Common scenarios:**
1. **Multiple MCP clients** syncing simultaneously
2. **AI agent workflows** that retry operations on lock timeout
3. **Background sync + manual MCP sync** happening close together (within seconds)
4. **Development/testing** with frequent manual sync commands
5. **Thundering herd** scenarios (many users triggering sync at once)

---

## Proposed Solution: In-Memory Request Cache

### High-Level Design

Add a **short-lived in-memory cache** (10-30 second TTL) at the SyncService layer to deduplicate identical API requests.

**Key principles:**
- **Cache scope:** API responses only (not DB queries)
- **TTL:** 15 seconds (configurable via environment variable)
- **Storage:** In-memory dictionary (no Redis/persistence needed)
- **Invalidation:** Time-based expiration only (simple, predictable)
- **Thread-safety:** Not required (asyncio single-threaded event loop)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ MCP Client Request: sync_data()                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ SyncService.execute_sync()                              │
│  1. Acquire lock (cross-process)                        │
│  2. Acquire asyncio lock (in-process)                   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Sync Products                                  │
│  ┌──────────────────────────────────────────┐           │
│  │ RequestCache.get("products:list")        │           │
│  │   ├─ Hit (< 15s old) → Return cached     │ ← NEW     │
│  │   └─ Miss → Fetch from API → Cache       │           │
│  └──────────────────────────────────────────┘           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 2: Sync Features                                  │
│  ┌──────────────────────────────────────────┐           │
│  │ RequestCache.get("features:{pid}")       │           │
│  │   ├─ Hit → Return cached                 │ ← NEW     │
│  │   └─ Miss → Fetch from API → Cache       │           │
│  └──────────────────────────────────────────┘           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3: Sync Tests                                     │
│  ┌──────────────────────────────────────────┐           │
│  │ RequestCache.get("tests:{pid}:page:{n}") │           │
│  │   ├─ Hit → Return cached                 │ ← NEW     │
│  │   └─ Miss → Fetch from API → Cache       │           │
│  └──────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

### Implementation Components

#### 1. RequestCache Class

**Location:** `src/testio_mcp/utilities/request_cache.py`

```python
"""In-memory request cache for API call deduplication."""

from datetime import UTC, datetime, timedelta
from typing import Any


class RequestCache:
    """Short-lived in-memory cache to prevent redundant API calls.

    Used by SyncService to cache API responses for 10-30 seconds,
    preventing repeated identical requests when multiple sync operations
    happen in rapid succession.

    Thread-safety: Not required (asyncio is single-threaded).
    Persistence: In-memory only (ephemeral, per-process).
    Invalidation: Time-based expiration only (no explicit invalidation).
    """

    def __init__(self, ttl_seconds: int = 15):
        """Initialize cache with TTL.

        Args:
            ttl_seconds: Time-to-live for cached entries (default: 15s)
        """
        self._cache: dict[str, tuple[datetime, Any]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Any | None:
        """Get cached value if not expired.

        Args:
            key: Cache key (e.g., "products:list", "features:598")

        Returns:
            Cached value if fresh, None if expired or missing
        """
        if key in self._cache:
            timestamp, value = self._cache[key]
            age = datetime.now(UTC) - timestamp

            if age < self._ttl:
                # Still fresh
                return value
            else:
                # Expired, cleanup
                del self._cache[key]

        return None

    def set(self, key: str, value: Any) -> None:
        """Cache value with current timestamp.

        Args:
            key: Cache key
            value: Value to cache (typically API response dict)
        """
        self._cache[key] = (datetime.now(UTC), value)

    def clear(self) -> None:
        """Clear all cached entries (for testing/debugging)."""
        self._cache.clear()

    def size(self) -> int:
        """Return number of cached entries (for monitoring)."""
        return len(self._cache)
```

#### 2. SyncService Integration

**Changes to `src/testio_mcp/services/sync_service.py`:**

```python
class SyncService(BaseService):
    """Unified sync orchestration service."""

    def __init__(
        self,
        client: TestIOClient,
        cache: PersistentCache,
        product_repo_factory: Any | None = None,
        feature_repo_factory: Any | None = None,
        test_repo_factory: Any | None = None,
    ) -> None:
        super().__init__(client)
        self.cache = cache
        self._product_repo_factory = product_repo_factory
        self._feature_repo_factory = feature_repo_factory
        self._test_repo_factory = test_repo_factory

        # NEW: Request deduplication cache
        self.request_cache = RequestCache(
            ttl_seconds=settings.REQUEST_CACHE_TTL_SECONDS
        )
```

**Wrap API calls in each phase:**

```python
async def _execute_phase_products(
    self, scope: SyncScope, session: AsyncSession
) -> SyncResult:
    """Phase 1: Sync products with request deduplication."""
    result = SyncResult()

    # NEW: Check request cache
    product_ids_key = tuple(sorted(scope.product_ids)) if scope.product_ids else None
    cache_key = f"products:list:{hash(product_ids_key)}"

    cached_products = self.request_cache.get(cache_key)
    if cached_products is not None:
        logger.debug(f"Request cache hit: {cache_key}")
        # Use cached response instead of API call
        # Still need to upsert to DB (other clients might not have it)
        product_repo = self._get_product_repo(session)
        for product_data in cached_products:
            await product_repo.upsert_product(product_data)
        result.products_synced = len(cached_products)
        return result

    # Cache miss - fetch from API as before
    logger.debug(f"Request cache miss: {cache_key}")
    product_repo = self._get_product_repo(session)
    products = await product_repo.sync_products(scope.product_ids)

    # NEW: Cache the API response
    self.request_cache.set(cache_key, products)

    result.products_synced = len(products)
    return result
```

#### 3. Configuration

**Add to `src/testio_mcp/config.py`:**

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Request deduplication cache (prevents redundant API calls)
    REQUEST_CACHE_TTL_SECONDS: int = Field(
        default=15,
        description=(
            "Time-to-live for in-memory request cache (seconds). "
            "Prevents redundant API calls when multiple sync operations "
            "happen within this window. Set to 0 to disable caching."
        ),
        ge=0,
        le=60,
    )
```

**Add to `.env.example`:**

```bash
# Request deduplication cache (prevents redundant API calls)
# Caches API responses for this many seconds
# Set to 0 to disable (default: 15)
REQUEST_CACHE_TTL_SECONDS=15
```

---

## Expected Performance Impact

### Benchmarks (Projected)

**Scenario: 3 rapid sync_data() calls (same product)**

| Metric | Without Cache | With Cache (15s TTL) | Improvement |
|--------|---------------|----------------------|-------------|
| Total time | 6.3s | ~2.0s | **68% faster** |
| API calls | 9 | 3 | **66% reduction** |
| Request 1 | 1.8s (3 API) | 1.8s (3 API) | Same (cache miss) |
| Request 2 | 2.7s (3 API) | ~0.1s (0 API) | **96% faster** |
| Request 3 | 1.7s (3 API) | ~0.1s (0 API) | **94% faster** |

**Key insight:** First request always hits API (cold cache), subsequent requests within 15s are near-instant.

### Impact by Use Case

| Use Case | Frequency | Impact |
|----------|-----------|--------|
| Single isolated sync | Low (baseline) | None (first call always hits API) |
| Multiple MCP clients | Medium | High (67% faster, 66% fewer API calls) |
| AI agent retries | Medium | High (near-instant on retry) |
| Background + manual sync | High | Medium (if within 15s window) |
| Development/testing | High | High (frequent manual syncs) |

---

## Trade-offs and Risks

### Benefits

✅ **Performance:** 67% faster for rapid repeated calls
✅ **API load reduction:** 66% fewer API calls (reduces rate limit risk)
✅ **Simple implementation:** Just dict + timestamp, no persistence
✅ **Short TTL:** 15s keeps data very fresh (acceptable staleness)
✅ **No correctness impact:** Lock still prevents concurrent DB writes
✅ **Graceful degradation:** If disabled (TTL=0), behaves exactly as before

### Risks and Mitigations

❌ **Stale data risk**
- **Concern:** Cached data might be up to 15s old
- **Mitigation:** 15s is very short (acceptable for sync operations)
- **Mitigation:** Only caches API responses, not DB queries (DB is source of truth)

❌ **Memory overhead**
- **Concern:** Cached API responses consume memory
- **Mitigation:** Ephemeral (15s TTL), small payloads (products/features/tests JSON)
- **Mitigation:** Typical cache size: ~10-50 entries × ~5-50KB = ~250KB-2.5MB max

❌ **Cache invalidation complexity**
- **Concern:** Explicit invalidation is hard (cache coherence problem)
- **Mitigation:** Use time-based expiration only (simple, predictable)
- **Mitigation:** Short TTL (15s) reduces risk of stale data

❌ **Testing complexity**
- **Concern:** Cache makes tests non-deterministic (timing-dependent)
- **Mitigation:** Clear cache in test setup (`request_cache.clear()`)
- **Mitigation:** Make TTL configurable (can disable for tests)

---

## Testing Strategy

### Unit Tests

**Location:** `tests/unit/test_request_cache.py`

```python
@pytest.mark.unit
def test_cache_hit_within_ttl():
    """Verify cache returns value if not expired."""
    cache = RequestCache(ttl_seconds=10)
    cache.set("key1", {"data": "value"})

    result = cache.get("key1")
    assert result == {"data": "value"}

@pytest.mark.unit
def test_cache_miss_after_ttl():
    """Verify cache returns None after expiration."""
    cache = RequestCache(ttl_seconds=0.1)  # 100ms TTL
    cache.set("key1", {"data": "value"})

    time.sleep(0.2)  # Wait for expiration

    result = cache.get("key1")
    assert result is None

@pytest.mark.unit
def test_cache_cleanup_on_expiration():
    """Verify expired entries are removed from cache."""
    cache = RequestCache(ttl_seconds=0.1)
    cache.set("key1", {"data": "value"})

    assert cache.size() == 1

    time.sleep(0.2)
    cache.get("key1")  # Triggers cleanup

    assert cache.size() == 0
```

### Integration Tests

**Location:** `tests/integration/test_sync_service_request_cache.py`

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rapid_syncs_use_cached_responses():
    """Verify multiple rapid syncs use cached API responses."""
    # Clear cache
    sync_service.request_cache.clear()

    # First sync - should hit API
    result1 = await sync_service.execute_sync(...)

    # Second sync within TTL - should use cache
    result2 = await sync_service.execute_sync(...)

    # Verify both syncs succeeded
    assert result1.products_synced == result2.products_synced

    # Verify cache was used (check metrics or logs)
    assert sync_service.request_cache.size() > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_cache_disabled_when_ttl_zero():
    """Verify cache can be disabled via TTL=0."""
    settings.REQUEST_CACHE_TTL_SECONDS = 0
    sync_service = SyncService(...)  # Creates cache with TTL=0

    # Both syncs should hit API (no caching)
    result1 = await sync_service.execute_sync(...)
    result2 = await sync_service.execute_sync(...)

    assert sync_service.request_cache.size() == 0
```

### Manual Testing

**Test plan:**
1. Enable request cache (`REQUEST_CACHE_TTL_SECONDS=15`)
2. Call `sync_data()` 3 times rapidly via MCP inspector
3. Verify server logs show cache hits on requests 2 and 3
4. Verify total time is ~2s (vs 6s without cache)
5. Verify API call count is 3 (vs 9 without cache)

---

## Implementation Checklist

**Phase 1: Core Implementation**
- [ ] Create `RequestCache` class in `utilities/request_cache.py`
- [ ] Add `REQUEST_CACHE_TTL_SECONDS` to config
- [ ] Inject `RequestCache` into `SyncService.__init__()`
- [ ] Wrap Products phase API calls with cache
- [ ] Wrap Features phase API calls with cache
- [ ] Wrap Tests phase API calls with cache

**Phase 2: Testing**
- [ ] Write unit tests for `RequestCache` class
- [ ] Write integration tests for `SyncService` with cache
- [ ] Manual testing with MCP inspector (3 rapid calls)
- [ ] Verify performance improvement (measure before/after)

**Phase 3: Documentation**
- [ ] Update `.env.example` with new config
- [ ] Update `README.md` with cache behavior explanation
- [ ] Add cache metrics to `get_database_stats` tool (optional)
- [ ] Document in ADR if architecture decision is significant

**Phase 4: Polish**
- [ ] Add observability (log cache hits/misses at DEBUG level)
- [ ] Add cache size monitoring (`request_cache.size()`)
- [ ] Consider cache statistics endpoint (hit rate, size, etc.)

---

## Alternative Approaches Considered

### Alternative 1: Redis Cache

**Description:** Use Redis for shared cache across processes

**Pros:**
- ✅ Shared across MCP server processes
- ✅ TTL built-in
- ✅ Battle-tested, mature technology

**Cons:**
- ❌ Requires external dependency (Redis)
- ❌ Network overhead for cache hits
- ❌ More complex deployment
- ❌ Overkill for 15-second ephemeral cache

**Verdict:** ❌ Rejected - too complex for short-lived cache

### Alternative 2: Extend PersistentCache (SQLite)

**Description:** Add TTL-based caching to existing SQLite cache

**Pros:**
- ✅ Reuses existing infrastructure
- ✅ No new dependencies

**Cons:**
- ❌ Disk I/O slower than in-memory
- ❌ Adds write load to SQLite
- ❌ TTL management in SQL is complex
- ❌ Mixes concerns (long-term storage + short-term deduplication)

**Verdict:** ❌ Rejected - wrong tool for the job

### Alternative 3: Lock-and-Wait Pattern

**Description:** Second request waits for first to complete, then reads from DB

**Pros:**
- ✅ No cache needed
- ✅ Simple implementation

**Cons:**
- ❌ Still makes redundant API calls if data isn't in DB
- ❌ Doesn't help with features/tests (not all stored in DB immediately)
- ❌ Complex coordination logic

**Verdict:** ❌ Rejected - doesn't fully solve the problem

---

## Future Enhancements

### Short-term (Nice-to-have)

1. **Cache statistics endpoint**
   - Add `get_cache_stats()` tool to report hit rate, size, etc.
   - Useful for monitoring and debugging

2. **Configurable TTL per entity type**
   - Products: 30s (rarely change)
   - Features: 20s (change occasionally)
   - Tests: 10s (change frequently)

3. **Cache warming on startup**
   - Pre-populate cache during initial sync
   - Reduces first-call latency

### Long-term (Future stories)

1. **Distributed cache** (if multi-process deployment)
   - Use Redis/Memcached for shared cache
   - Only if running multiple MCP server instances

2. **Adaptive TTL**
   - Increase TTL if API is slow/rate-limited
   - Decrease TTL if data is changing rapidly

3. **Cache invalidation on mutations**
   - If we ever add write operations (create tests, update features)
   - Invalidate cache when data changes

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-27 | Use in-memory dict cache | Simple, fast, sufficient for single-process server |
| 2025-11-27 | TTL = 15 seconds | Balance between freshness and deduplication |
| 2025-11-27 | Time-based expiration only | Explicit invalidation is complex, short TTL mitigates staleness |
| 2025-11-27 | Defer to separate story | Not blocking STORY-051, optimization can be added later |

---

## References

**Related Stories:**
- STORY-051: sync_data MCP Tool (trigger for this optimization)
- Epic 008: MCP Layer Optimization (potential home for this work)

**Related Code:**
- `src/testio_mcp/services/sync_service.py` - Sync orchestration
- `src/testio_mcp/repositories/feature_repository.py` - Feature sync with staleness checks
- `src/testio_mcp/repositories/test_repository.py` - Test sync with pagination

**External Resources:**
- [Caching Strategies and How to Choose the Right One](https://codeahoy.com/2017/08/11/caching-strategies-and-how-to-choose-the-right-one/)
- [Cache Stampede Problem](https://en.wikipedia.org/wiki/Cache_stampede)
- [Python TTL Cache Patterns](https://realpython.com/lru-cache-python/)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-27
**Next Review:** Before implementing (story creation phase)
