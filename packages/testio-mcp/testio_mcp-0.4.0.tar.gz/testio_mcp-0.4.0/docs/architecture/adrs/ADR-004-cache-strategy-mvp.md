# ADR-004: In-Memory Cache Strategy for MVP (No Redis Abstraction)

**Status:** ❌ SUPERSEDED

**Date:** 2025-11-04

**Superseded By:** [STORY-021: Local Data Store](../../stories/done/story-021-local-data-store.md)

**Superseded Date:** 2025-11-18 (v2.0 - SQLite-first refactoring)

**Historical Context:** This ADR describes the original InMemoryCache implementation used from v0.1.0 to v0.1.1. It was replaced by PersistentCache (SQLite) in v0.2.0 for better performance, persistence, and multi-query support.

**Current Implementation:** See [ARCHITECTURE.md - Local Data Store Strategy](../ARCHITECTURE.md#local-data-store-strategy)

---

## Original ADR Content (Historical Reference)

**Original Context:** Caching strategy for reducing API load and improving response times

---

## Context

The TestIO MCP server makes frequent API calls for:
- Product listings (rarely changes)
- Test listings (changes moderately)
- Bug data (changes frequently)

### Problem

Without caching:
1. **Repeated API calls** for same data waste quota and increase latency
2. **Poor user experience** when AI makes similar queries in rapid succession
3. **API load** increases unnecessarily

### Caching Requirements

From project brief and stories:
- **Products list**: TTL 1 hour (rarely changes)
- **Test lists**: TTL 5 minutes (moderate updates)
- **Bug data**: TTL 1 minute (changes frequently)

### Epic's Original Guidance

Project epic suggested:

> **Caching Strategy (In-Memory with TTL)**
> - Simple dictionary-based cache with expiration
> - **Future**: Upgrade to Redis/file-based if performance requires

### Alternative Approaches Considered

1. **No Caching**
   - Every request hits API
   - **Pros:** Always fresh data, no complexity
   - **Cons:** High latency, API abuse, poor UX

2. **In-Memory Cache (Simple)**
   - Python dict with TTL tracking
   - **Pros:** Fast, simple, no external dependencies
   - **Cons:** Lost on restart, no persistence, no sharing across instances

3. **In-Memory with Abstraction Layer**
   - `CacheBackend` interface with `InMemoryBackend` and future `RedisBackend`
   - **Pros:** Future-proofed, easy to migrate
   - **Cons:** Premature optimization (YAGNI), added complexity

4. **Redis from Start**
   - Use Redis for all caching
   - **Pros:** Production-ready, persistent, sharable
   - **Cons:** Adds dependency, deployment complexity, overkill for MVP

5. **File-Based Cache**
   - Serialize cache to disk
   - **Pros:** Persistent across restarts
   - **Cons:** I/O overhead, concurrency issues, cleanup complexity

---

## Decision

**Use simple in-memory caching for MVP. No abstraction layer. No Redis.**

**Rationale:**
1. **YAGNI Principle** - We don't need Redis until we have evidence we need it
2. **MVP Scope** - Single-instance deployment, read-only operations, limited users
3. **Simplicity** - Fewer moving parts, faster development
4. **Migration Path** - Can add Redis later if/when needed without breaking clients

**When to Reconsider (Migration Triggers):**
- Cache size exceeds 100MB
- Hit rate drops below 50%
- Need multi-instance deployment
- Need cache persistence across restarts
- Production deployment with high load

---

## Implementation

### 1. Simple In-Memory Cache

**CRITICAL WARNING: DO NOT create a synchronous wrapper for the cache.**

All interactions with the cache MUST be `async` to prevent event loop conflicts. Creating a synchronous wrapper (e.g., using `asyncio.get_event_loop().run_until_complete()`) will cause "Event loop is closed" errors and other hard-to-debug asyncio issues.

**Always use:** `await cache.get(...)` and `await cache.set(...)`
**Never create:** `SyncCacheWrapper` or similar patterns

```python
# src/testio_mcp/cache.py

from datetime import datetime, timedelta
from typing import Any, Optional
import asyncio


class InMemoryCache:
    """
    Simple TTL-based in-memory cache.

    Thread-safe for async operations via asyncio.Lock.
    Not suitable for multi-process deployments.
    """

    def __init__(self):
        """Initialize empty cache with async lock."""
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """
        Get cached value if exists and not expired.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        async with self._lock:
            if key not in self._cache:
                return None

            value, expires_at = self._cache[key]

            # Check expiration
            if datetime.utcnow() > expires_at:
                del self._cache[key]
                return None

            return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds
        """
        async with self._lock:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            self._cache[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        """
        Remove value from cache.

        Args:
            key: Cache key to remove
        """
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    async def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache size, entry count, etc.
        """
        async with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for _, expires_at in self._cache.values()
                if datetime.utcnow() > expires_at
            )

            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_entries,
                "expired_entries": expired_entries,
            }
```

### 2. Cache Integration in Tools

```python
# src/testio_mcp/tools/list_active_tests.py

from fastmcp import Context


@mcp.tool()
async def list_active_tests(
    product_id: str,
    status: str = "running",
    include_bug_counts: bool = False,
    ctx: Context = None,
) -> dict:
    """List active tests for a product with caching."""
    testio_client = ctx["testio_client"]
    cache = ctx["cache"]

    # Generate cache key
    cache_key = f"tests:product:{product_id}:status:{status}"

    # Try cache first
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result

    # Cache miss - fetch from API
    tests_data = await testio_client.get(f"products/{product_id}/exploratory_tests")
    tests = tests_data.get("exploratory_tests", [])

    # Filter by status
    if status != "all":
        tests = [t for t in tests if t.get("status") == status]

    # Build response
    result = {
        "product_id": product_id,
        "tests": tests,
        "count": len(tests),
    }

    # Cache result (5 minute TTL for test lists)
    await cache.set(cache_key, result, ttl_seconds=300)

    return result
```

### 3. Server Initialization with Cache

```python
# src/testio_mcp/server.py

from contextlib import asynccontextmanager
from fastmcp import FastMCP
from .client import TestIOClient
from .cache import InMemoryCache
from .config import settings


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Manage client and cache lifecycle."""
    # Initialize cache
    cache = InMemoryCache()

    # Initialize API client
    async with TestIOClient(
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
        max_concurrent_requests=settings.MAX_CONCURRENT_API_REQUESTS,
    ) as client:
        # Store in server context
        server.context["testio_client"] = client
        server.context["cache"] = cache

        # Server runs here
        yield

        # Cleanup (cache is GC'd, client is closed by __aexit__)


mcp = FastMCP("TestIO MCP Server", lifespan=lifespan)
```

### 4. Cache TTL Configuration

```python
# src/testio_mcp/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    TESTIO_CUSTOMER_API_BASE_URL: str
    TESTIO_CUSTOMER_API_TOKEN: str
    MAX_CONCURRENT_API_REQUESTS: int = 10

    # Cache TTLs (in seconds)
    CACHE_TTL_PRODUCTS: int = 3600      # 1 hour
    CACHE_TTL_TESTS: int = 300          # 5 minutes
    CACHE_TTL_BUGS: int = 60            # 1 minute

    class Config:
        env_file = ".env"


settings = Settings()
```

### 5. Cache-Raw Pattern (Added in STORY-012 Phase 2)

**Problem:** Cache key explosion from filter combinations

When caching filtered query results, each filter combination creates a separate cache entry:
- `test:123:bugs:functional:critical:accepted`
- `test:123:bugs:functional:high:all`
- `test:123:bugs:visual:all:forwarded`

This causes:
- Low cache hit rates (~20% in BugService)
- Memory waste (duplicate raw data)
- Complexity in cache invalidation

**Solution:** Cache raw entity data once, filter in-memory

```python
# ❌ BEFORE: Cache per filter combination (key explosion)
cache_key = f"test:{test_id}:bugs:{bug_type}:{severity}:{status}"
cached_filtered_bugs = await cache.get(cache_key)

if cached_filtered_bugs:
    return cached_filtered_bugs

# Fetch from API and filter
all_bugs = await client.get(f"bugs?test_id={test_id}")
filtered_bugs = apply_filters(all_bugs, bug_type, severity, status)

# Cache filtered results (separate entry per filter combo)
await cache.set(cache_key, filtered_bugs, ttl_seconds=60)


# ✅ AFTER: Cache raw once, filter in-memory (cache-raw pattern)
cache_key = f"test:{test_id}:bugs:raw"  # NO filters in key
cached_raw_response = await cache.get(cache_key)

if cached_raw_response:
    all_bugs = cached_raw_response["bugs"]
else:
    # Fetch from API
    cached_raw_response = await client.get(f"bugs?test_id={test_id}")
    # Cache RAW API response
    await cache.set(cache_key, cached_raw_response, ttl_seconds=60)
    all_bugs = cached_raw_response["bugs"]

# Filter in-memory (microseconds vs API milliseconds)
filtered_bugs = apply_filters(all_bugs, bug_type, severity, status)
return filtered_bugs
```

**Benefits:**
- **Cache hit rate:** 95%+ (up from ~20%)
- **Memory efficiency:** One cache entry per entity type (not per filter combo)
- **Performance:** In-memory filtering is <1ms (vs 200-500ms API latency)
- **Simplicity:** Single cache key per resource, no key explosion

**Trade-offs:**
- **Memory per entry:** Larger (stores all bugs, not just filtered subset)
- **CPU overhead:** In-memory filtering required (negligible: <1ms)
- **When NOT to use:** Very large result sets (>10k records per entity)

**Implementation:**
- Used in: `BugService`, `ProductService` (test lists)
- Cache keys: `test:{id}:bugs:raw`, `product:{id}:tests:raw`
- See `src/testio_mcp/services/bug_service.py` for reference implementation

---

## Consequences

### Positive

1. **Simplicity**
   - No external dependencies (Redis, memcached)
   - No deployment complexity
   - Easy to understand and debug

2. **Performance**
   - In-memory access is extremely fast (<1ms)
   - Reduces API calls by 50-90% (depending on usage patterns)
   - Improves response times for repeated queries

3. **Development Velocity**
   - No time spent on Redis setup, configuration, or debugging
   - Faster MVP delivery
   - Can iterate quickly

4. **Resource Efficiency**
   - Low memory footprint for typical workloads
   - No network overhead (cache is in same process)

5. **Testing**
   - Easy to test (no need for Redis container)
   - Deterministic behavior
   - Simple to mock

### Negative

1. **No Persistence**
   - Cache lost on server restart
   - First queries after restart are slow (cold cache)
   - No warm-up possible

2. **Single-Instance Only**
   - Can't share cache across multiple server instances
   - Load balancing requires sticky sessions or accepts cache misses
   - Not suitable for horizontal scaling

3. **Memory Limits**
   - Cache grows unbounded (no LRU eviction in MVP)
   - Could exhaust memory if queries are highly diverse
   - No disk overflow option

4. **No Advanced Features**
   - No cache invalidation by pattern (e.g., clear all tests for product X)
   - No distributed locking
   - No pub/sub for cache invalidation

### Neutral

1. **Migration Path Clear**
   - When triggers met (see below), can migrate to Redis
   - Interface change is minimal (async methods stay the same)
   - Tools don't need to know about cache backend

2. **Acceptable for MVP**
   - MVP is read-only, single-tenant, low volume
   - Cache effectiveness doesn't need to be perfect
   - Can gather metrics to inform future decisions

---

## Monitoring & Migration Triggers

### Metrics to Track (Story 8: Error Handling)

```python
class InMemoryCacheWithMetrics(InMemoryCache):
    def __init__(self):
        super().__init__()
        self.hits = 0
        self.misses = 0
        self.sets = 0

    async def get(self, key: str) -> Optional[Any]:
        result = await super().get(key)
        if result is not None:
            self.hits += 1
        else:
            self.misses += 1
        return result

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        await super().set(key, value, ttl_seconds)
        self.sets += 1

    def get_metrics(self) -> dict:
        """Get cache performance metrics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
        }
```

### Migration Triggers (Migrate to Redis When...)

1. **Cache Size Exceeds 100MB**
   - Action: Add memory monitoring to cache stats
   - Threshold: If `sys.getsizeof(cache._cache) > 100 * 1024 * 1024`
   - Why: Risk of OOM errors, need eviction policy

2. **Hit Rate Below 50%**
   - Action: Log cache hit/miss rates
   - Threshold: If `hit_rate < 50%` over 1 hour
   - Why: Cache not effective, may need different strategy

3. **Multi-Instance Deployment Needed**
   - Action: Deploy load balancer
   - Threshold: When single instance can't handle load
   - Why: Need shared cache for consistency

4. **Persistence Required**
   - Action: User feedback indicates cold start is painful
   - Threshold: Startup latency complaints
   - Why: Need cache to survive restarts

5. **Production Deployment**
   - Action: Moving from staging to production
   - Threshold: When ready for customer use
   - Why: Production requires robustness, monitoring

### When to Add Features (Not Migrate)

**Add LRU Eviction** (Before Redis):
- If cache size is issue but other triggers not met
- Simple to implement (use `collections.OrderedDict` or `cachetools.TTLCache`)
- Buys time before Redis migration

**Add Size Limits** (Before Redis):
- If memory is concern but hit rate is good
- Set max entries (e.g., 10,000)
- Evict oldest when limit reached

---

## Redis Migration Path (Future)

When migration triggers are met, implement this pattern:

### 1. Define Cache Backend Interface

```python
# src/testio_mcp/cache.py

from abc import ABC, abstractmethod


class CacheBackend(ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]: ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def clear(self) -> None: ...


class InMemoryCacheBackend(CacheBackend):
    """In-memory cache implementation."""
    # ... existing InMemoryCache code ...


class RedisCacheBackend(CacheBackend):
    """Redis cache implementation."""

    def __init__(self, redis_url: str):
        import aioredis
        self.redis = aioredis.from_url(redis_url)

    async def get(self, key: str) -> Optional[Any]:
        import json
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        import json
        await self.redis.setex(key, ttl_seconds, json.dumps(value))

    # ... implement other methods ...
```

### 2. Configuration-Based Backend Selection

```python
# .env

CACHE_BACKEND=inmemory  # or "redis"
REDIS_URL=redis://localhost:6379/0  # only used if CACHE_BACKEND=redis
```

```python
# src/testio_mcp/server.py

from .cache import InMemoryCacheBackend, RedisCacheBackend


@asynccontextmanager
async def lifespan(server: FastMCP):
    # Select cache backend based on config
    if settings.CACHE_BACKEND == "redis":
        cache = RedisCacheBackend(settings.REDIS_URL)
    else:
        cache = InMemoryCacheBackend()

    # ... rest of lifespan ...
```

**No tool code changes required!**

---

## Related Decisions

- **ADR-002: Concurrency Limits** - Cache reduces concurrent requests to API
- **ADR-003: Pagination Strategy** - Cached results still respect pagination
- **Story 7: MCP Resources** - Resources heavily use caching
- **Story 8: Error Handling** - Cache metrics inform monitoring

---

## References

- [Python asyncio.Lock](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Lock)
- [cachetools](https://github.com/tkem/cachetools/) - Python caching library with TTL and LRU support
- [Redis Python Client (aioredis)](https://aioredis.readthedocs.io/)
- [YAGNI Principle](https://martinfowler.com/bliki/Yagni.html)

---

## Open Questions

1. **Should we add LRU eviction in MVP?**
   - Current: Unbounded cache (grows indefinitely)
   - Future: Add max_size parameter, evict LRU entries
   - Decision: Defer until we observe memory issues (YAGNI)

2. **Should we persist cache to disk on shutdown?**
   - Current: Cache lost on restart
   - Future: Serialize to JSON file, load on startup
   - Decision: Defer until cold start becomes pain point

3. **Should we add cache warming on startup?**
   - Current: Cold cache, first queries are slow
   - Future: Pre-fetch products list, common queries
   - Decision: Defer until startup time becomes issue

4. **What cache key format should we use?**
   - Current: `f"tests:product:{product_id}:status:{status}"`
   - Future: Define formal key naming convention
   - Decision: Document in implementation guide, enforce in code review
