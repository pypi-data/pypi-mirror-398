---
story_id: STORY-007
epic_id: EPIC-001
title: In-Memory Caching Layer
status: Done
created: 2025-11-04
updated: 2025-11-06
estimate: 3 hours
assignee: James (Dev Agent)
dependencies: [STORY-001, STORY-004, STORY-005, STORY-012]
---

# STORY-007: In-Memory Caching Layer

## Status

**Done** - Implementation complete, QA approved (100/100), ready for production

---

## Story

**As a** developer building TestIO MCP Server
**I want** an in-memory caching layer with TTL support
**So that** redundant API calls are minimized and response times are improved

**And as a** Customer Success Manager using AI tools
**I want** faster response times for repeated queries
**So that** I can work more efficiently without waiting for API calls

---

## Context

### Background

The TestIO MCP Server makes frequent API calls for products, tests, and bugs. Without caching:
1. **Repeated API calls** for same data waste quota and increase latency
2. **Poor user experience** when AI makes similar queries in rapid succession
3. **API load** increases unnecessarily

### Caching Strategy (from Epic)

- **Products list**: 1 hour TTL (rarely changes)
- **Test lists**: 5 minutes TTL (moderate updates)
- **Bug data**: 1 minute TTL (changes frequently)

### Architecture Alignment

**Service Layer Pattern (ADR-006, ADR-011):**
- Cache is injected into services via dependency injection
- Services use cache-raw pattern (cache full API responses, filter in-memory)
- Tools remain thin wrappers that delegate to services

**Example Pattern:**
```python
# Service handles caching internally
class ProductService(BaseService):
    async def list_products(self, search: str | None = None) -> dict:
        # Try cache first (cache-raw pattern)
        cached = await self.cache.get("products:list:raw")
        if cached:
            all_products = cached["products"]
        else:
            # Fetch from API
            response = await self.client.get("products")
            await self.cache.set("products:list:raw", response, ttl=3600)
            all_products = response["products"]

        # Filter in-memory (fast)
        if search:
            all_products = [p for p in all_products if search.lower() in p["name"].lower()]

        return {"products": all_products, "total_count": len(all_products)}
```

### MCP Resources Decision (ADR-012)

**Important Context:** MCP Resources implementation has been **deferred to post-MVP**.

After comprehensive research of MCP specification and real-world patterns, we determined:
- **Tools** (model-controlled) are ideal for AI-driven queries (current use case)
- **Resources** (application-controlled) are valuable for UI-based context loading (not MVP)
- Many production MCP servers implement tools only, adding resources based on user feedback

See [ADR-012: Resources Strategy](../architecture/adrs/ADR-012-resources-strategy-defer-to-post-mvp.md) for full rationale.

**This story now focuses solely on caching infrastructure**, which provides value regardless of MCP primitive type (tools, resources, or prompts).

---

## Acceptance Criteria

### AC1: In-Memory Cache Implementation (ADR-004)

- [ ] **ARCHITECTURE**: Simple async-only cache (NO SyncCacheWrapper - anti-pattern)
- [ ] Simple dictionary-based cache with TTL support
- [ ] Thread-safe for concurrent access (using asyncio.Lock)
- [ ] Automatic expiration checking on get
- [ ] Cache statistics tracking (hits/misses/total requests)
- [ ] **CRITICAL**: All cache interactions MUST be async (await cache.get(), await cache.set())
- [ ] **CRITICAL**: DO NOT create synchronous wrapper (causes "Event loop is closed" errors)
- [ ] **Reference**: [ADR-004: Cache Strategy MVP](../architecture/adrs/ADR-004-cache-strategy-mvp.md)
- [ ] Implementation location: `src/testio_mcp/cache.py`
- [ ] Example implementation:
  ```python
  # src/testio_mcp/cache.py
  import asyncio
  from datetime import datetime, timedelta
  from typing import Any, Optional

  class InMemoryCache:
      """
      Simple in-memory cache with TTL support.

      ASYNC ONLY - all methods are async. Services must use 'await cache.get()'.

      **CRITICAL WARNING: DO NOT create a synchronous wrapper for this cache.**

      All interactions MUST be async to prevent event loop conflicts. Creating
      a sync wrapper (e.g., using asyncio.get_event_loop().run_until_complete())
      will cause "Event loop is closed" errors and other hard-to-debug issues.

      **Always use:** await cache.get(...) / await cache.set(...)
      **Never create:** SyncCacheWrapper or similar patterns

      Reference: ADR-004 (Cache Strategy MVP)
      """

      def __init__(self):
          self._cache: dict[str, tuple[Any, datetime]] = {}
          self._lock = asyncio.Lock()
          self._hits = 0
          self._misses = 0

      async def get(self, key: str) -> Optional[Any]:
          """Get value from cache if not expired.

          Args:
              key: Cache key

          Returns:
              Cached value if exists and not expired, None otherwise
          """
          async with self._lock:
              if key not in self._cache:
                  self._misses += 1
                  return None

              value, expires_at = self._cache[key]

              # Check expiration
              if datetime.utcnow() > expires_at:
                  del self._cache[key]
                  self._misses += 1
                  return None

              self._hits += 1
              return value

      async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
          """Store value in cache with TTL.

          Args:
              key: Cache key
              value: Value to cache
              ttl_seconds: Time-to-live in seconds
          """
          async with self._lock:
              expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
              self._cache[key] = (value, expires_at)

      async def delete(self, key: str) -> None:
          """Remove value from cache.

          Args:
              key: Cache key to remove
          """
          async with self._lock:
              self._cache.pop(key, None)

      async def clear(self) -> None:
          """Clear all cache entries."""
          async with self._lock:
              self._cache.clear()
              # Reset stats
              self._hits = 0
              self._misses = 0

      async def get_stats(self) -> dict:
          """Get cache statistics.

          Returns:
              Dictionary with hits, misses, hit rate, total requests
          """
          async with self._lock:
              total = self._hits + self._misses
              hit_rate = (self._hits / total * 100) if total > 0 else 0
              return {
                  "hits": self._hits,
                  "misses": self._misses,
                  "total_requests": total,
                  "hit_rate_percent": round(hit_rate, 2),
                  "cached_keys": len(self._cache)
              }
  ```

### AC2: Cache Integration in Server Lifespan

- [ ] Cache instance initialized in server lifespan (ADR-007)
- [ ] Cache accessible via dependency injection (FastMCP context)
- [ ] Cache shared across all services
- [ ] Server initialization order: Cache → Client (both before yield)
- [ ] **CRITICAL**: Use ServerContext pattern (ADR-007) - yield context dict, not server.context
- [ ] Example implementation:
  ```python
  # src/testio_mcp/server.py (lifespan handler)
  from contextlib import asynccontextmanager
  from typing import TypedDict
  from fastmcp import FastMCP
  from .client import TestIOClient
  from .cache import InMemoryCache
  from .config import settings

  class ServerContext(TypedDict):
      """Server lifespan context."""
      testio_client: TestIOClient
      cache: InMemoryCache

  @asynccontextmanager
  async def lifespan(server: FastMCP):
      """Manage client and cache lifecycle (ADR-007 pattern)."""
      # Initialize cache first (no async setup needed)
      cache = InMemoryCache()

      # Initialize API client (async context manager)
      async with TestIOClient(
          base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
          api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
          max_concurrent_requests=settings.MAX_CONCURRENT_API_REQUESTS,
      ) as client:
          # Yield context dict (ADR-007 pattern)
          # Tools access via ctx.request_context.lifespan_context
          context: ServerContext = {
              "testio_client": client,
              "cache": cache,
          }
          yield context

          # Cleanup (cache is GC'd, client closed by __aexit__)

  mcp = FastMCP("TestIO MCP Server", lifespan=lifespan)
  ```

### AC3: Cache TTL Configuration

- [ ] TTL values defined in settings (environment variables)
- [ ] Configuration location: `src/testio_mcp/config.py`
- [ ] TTL constants accessible to services
- [ ] **CROSS-CUTTING IMPACT**: BaseService currently hard-codes TTL constants
  - Must refactor `BaseService.CACHE_TTL_*` to read from `settings`
  - Update all service classes that inherit from BaseService
  - Affects: ProductService, TestService, BugService
- [ ] Example implementation:
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

### AC4: Cache Monitoring Tools

- [ ] Add `get_cache_stats` tool for performance monitoring
- [ ] Add `clear_cache` tool for admin operations
- [ ] Tools accessible via MCP protocol
- [ ] Example implementation:
  ```python
  # src/testio_mcp/server.py (or dedicated tools file)
  from fastmcp import Context
  from testio_mcp.server import mcp
  from typing import cast

  @mcp.tool()
  async def get_cache_stats(ctx: Context) -> dict:
      """Get cache performance statistics.

      Returns:
          Dictionary with cache hits, misses, hit rate, and total requests

      Example:
          >>> result = await get_cache_stats()
          >>> print(result["hit_rate_percent"])
          87.5
      """
      # Access cache from lifespan context (ADR-007)
      cache = ctx.request_context.lifespan_context["cache"]
      return await cache.get_stats()

  @mcp.tool()
  async def clear_cache(ctx: Context) -> dict:
      """Clear all cached data (admin tool).

      Use with caution: This will force all subsequent queries to hit the API.
      Useful for testing or when you know data has changed.

      Returns:
          Confirmation message
      """
      cache = ctx.request_context.lifespan_context["cache"]
      await cache.clear()
      return {
          "status": "success",
          "message": "Cache cleared successfully. All subsequent queries will hit the API."
      }
  ```

### AC5: Integration Testing

- [ ] Test cache stores and retrieves values correctly
- [ ] Test cache expiration (wait for TTL, verify re-fetch)
- [ ] Test cache statistics (hits/misses tracking)
- [ ] Test cache clearing works
- [ ] Test concurrent access (multiple simultaneous requests)
- [ ] Example tests:
  ```python
  # tests/unit/test_cache.py
  import pytest
  import asyncio
  from testio_mcp.cache import InMemoryCache

  @pytest.mark.asyncio
  async def test_cache_get_set():
      """Test basic cache get/set operations."""
      cache = InMemoryCache()

      # Set value
      await cache.set("test_key", "test_value", ttl_seconds=60)

      # Get value
      value = await cache.get("test_key")
      assert value == "test_value"

      # Verify stats
      stats = await cache.get_stats()
      assert stats["hits"] == 1
      assert stats["misses"] == 0

  @pytest.mark.asyncio
  async def test_cache_expiration():
      """Test cache expires after TTL."""
      cache = InMemoryCache()

      # Set short TTL for testing
      await cache.set("test_key", "test_value", ttl_seconds=1)

      # Immediate get should work
      value = await cache.get("test_key")
      assert value == "test_value"

      # Wait for expiration
      await asyncio.sleep(2)

      # Should be expired
      value = await cache.get("test_key")
      assert value is None

  @pytest.mark.asyncio
  async def test_cache_statistics():
      """Test cache tracks hits and misses correctly."""
      cache = InMemoryCache()

      # Miss (key doesn't exist)
      await cache.get("nonexistent")

      # Set value
      await cache.set("test_key", "test_value", ttl_seconds=60)

      # Hit (key exists)
      await cache.get("test_key")
      await cache.get("test_key")

      # Check stats
      stats = await cache.get_stats()
      assert stats["hits"] == 2
      assert stats["misses"] == 1
      assert stats["total_requests"] == 3
      assert stats["hit_rate_percent"] == 66.67

  @pytest.mark.asyncio
  async def test_cache_clear():
      """Test cache clearing removes all entries and resets stats."""
      cache = InMemoryCache()

      # Add some data
      await cache.set("key1", "value1", ttl_seconds=60)
      await cache.set("key2", "value2", ttl_seconds=60)
      await cache.get("key1")  # Hit

      # Clear cache
      await cache.clear()

      # Verify data cleared
      value = await cache.get("key1")
      assert value is None

      # Verify stats reset
      stats = await cache.get_stats()
      assert stats["hits"] == 0
      assert stats["misses"] == 1  # From the get after clear
      assert stats["cached_keys"] == 0

  @pytest.mark.asyncio
  async def test_concurrent_access():
      """Test cache handles concurrent access correctly."""
      cache = InMemoryCache()

      # Set initial value
      await cache.set("test_key", "initial_value", ttl_seconds=60)

      # Simulate concurrent access with asyncio.gather
      async def read_cache():
          return await cache.get("test_key")

      async def update_cache(value: str):
          await cache.set("test_key", value, ttl_seconds=60)

      # Run 10 concurrent reads and 5 concurrent writes
      tasks = [read_cache() for _ in range(10)] + [
          update_cache(f"value_{i}") for i in range(5)
      ]
      results = await asyncio.gather(*tasks, return_exceptions=True)

      # Verify no exceptions occurred
      assert all(not isinstance(r, Exception) for r in results if r is not None)

      # Verify final value is one of the written values
      final_value = await cache.get("test_key")
      assert final_value.startswith("value_") or final_value == "initial_value"

      # Verify stats tracked all operations
      stats = await cache.get_stats()
      assert stats["total_requests"] >= 10  # At least the 10 reads

  # tests/integration/test_cache_integration.py
  @pytest.mark.integration
  @pytest.mark.asyncio
  async def test_service_uses_cache(mock_testio_client):
      """Test ProductService properly uses caching."""
      from unittest.mock import AsyncMock
      from testio_mcp.services.product_service import ProductService
      from testio_mcp.cache import InMemoryCache

      # Setup mock client
      mock_client = AsyncMock()
      mock_client.get.return_value = {
          "products": [
              {"id": 1, "name": "Product A"},
              {"id": 2, "name": "Product B"},
          ]
      }

      # Create cache and service
      cache = InMemoryCache()
      service = ProductService(client=mock_client, cache=cache)

      # First call should hit API
      result1 = await service.list_products()
      assert len(result1["products"]) == 2
      assert mock_client.get.call_count == 1

      # Second call should use cache (no additional API call)
      result2 = await service.list_products()
      assert result1 == result2
      assert mock_client.get.call_count == 1  # Still 1 (cached)

      # Verify cache stats
      stats = await cache.get_stats()
      assert stats["hits"] >= 1  # At least one cache hit

  @pytest.mark.integration
  @pytest.mark.asyncio
  async def test_cache_ttl_expiration_integration(mock_testio_client):
      """Test service respects cache TTL expiration."""
      from unittest.mock import AsyncMock
      from testio_mcp.services.product_service import ProductService
      from testio_mcp.cache import InMemoryCache

      # Setup mock client with different responses
      mock_client = AsyncMock()
      mock_client.get.side_effect = [
          {"products": [{"id": 1, "name": "Old Data"}]},
          {"products": [{"id": 1, "name": "New Data"}]},
      ]

      # Create cache and service with short TTL for testing
      cache = InMemoryCache()
      service = ProductService(client=mock_client, cache=cache)

      # Mock short TTL (override service TTL for testing)
      original_ttl = service.CACHE_TTL_PRODUCTS
      service.CACHE_TTL_PRODUCTS = 1  # 1 second

      try:
          # First call - should hit API
          result1 = await service.list_products()
          assert result1["products"][0]["name"] == "Old Data"
          assert mock_client.get.call_count == 1

          # Wait for TTL to expire
          await asyncio.sleep(2)

          # Second call - cache expired, should hit API again
          result2 = await service.list_products()
          assert result2["products"][0]["name"] == "New Data"
          assert mock_client.get.call_count == 2  # API called again
      finally:
          # Restore original TTL
          service.CACHE_TTL_PRODUCTS = original_ttl
  ```

---

## Tasks / Subtasks

- [x] **Task 1: Implement InMemoryCache class** (AC1)
  - [x] Create `src/testio_mcp/cache.py` with async-only interface
  - [x] Implement get/set/delete/clear methods with asyncio.Lock
  - [x] Add TTL expiration logic (datetime.now(UTC) comparison)
  - [x] Add cache statistics tracking (hits/misses/hit_rate/cached_keys)
  - [x] Add comprehensive docstrings with anti-pattern warnings
  - [x] Write unit tests for cache operations

- [x] **Task 2: Integrate cache in server lifespan** (AC2)
  - [x] Update `src/testio_mcp/server.py` lifespan handler (already done in previous story)
  - [x] Create ServerContext TypedDict (testio_client, cache) (already done)
  - [x] Initialize InMemoryCache instance (before client) (already done)
  - [x] Yield context dict from lifespan (ADR-007 pattern) (already done)
  - [x] Verify cache accessible via ctx.request_context.lifespan_context["cache"] (confirmed)
  - [x] Test cache lifecycle (initialization and cleanup) (confirmed working)

- [x] **Task 3: Add TTL configuration** (AC3)
  - [x] Update `src/testio_mcp/config.py` with TTL constants (already existed)
  - [x] CACHE_TTL_PRODUCTS (3600 seconds) (already configured)
  - [x] CACHE_TTL_TESTS (300 seconds) (already configured)
  - [x] CACHE_TTL_BUGS (60 seconds) (already configured)
  - [x] **REFACTOR BaseService**: Updated BaseService to read TTLs from settings in __init__
  - [x] Update ProductService, TestService, BugService (inherit automatically from BaseService)
  - [x] Document TTL values in .env.example (already documented)
  - [x] Update test_base_service.py to check instance attributes (not class attributes)

- [x] **Task 4: Implement cache monitoring tools** (AC4)
  - [x] Create `src/testio_mcp/tools/cache_tools.py` with @mcp.tool() decorators
  - [x] Implement `get_cache_stats` tool with comprehensive docstrings
  - [x] Implement `clear_cache` tool with warning documentation
  - [x] Use ctx.request_context.lifespan_context["cache"] to access cache
  - [x] Add proper type casting with ServerContext
  - [x] Write docstrings with usage examples and typical hit rates
  - [x] **AUTO-REGISTRATION**: Tools auto-discovered successfully via ADR-011
  - [x] Test tools via MCP (user confirmed tools are visible)

- [x] **Task 5: Integration testing** (AC5)
  - [x] Write unit tests for InMemoryCache (tests/unit/test_cache.py) - 12 tests
  - [x] Test basic get/set operations
  - [x] Test TTL expiration behavior
  - [x] Test cache statistics tracking
  - [x] Test cache clearing and deletion
  - [x] Test concurrent access (asyncio.gather with 10 reads + 5 writes)
  - [x] Write integration tests (tests/integration/test_cache_integration.py) - 6 tests
  - [x] Verify all tests pass (212 passed, 11 skipped as expected)

- [x] **Task 6: Documentation updates**
  - [x] Update README.md tool count (7 → 9 tools)
  - [x] Add cache monitoring tools to Available Tools table
  - [x] Update tool description to mention cache monitoring
  - [x] .env.example already documented (lines 12-15)
  - [x] CLAUDE.md already has cache configuration info

---

## Dev Notes

### Testing Standards

**Test Location:**
- Unit tests: `tests/unit/test_cache.py`
- Integration tests: `tests/integration/test_cache_integration.py`

**Test Standards:**
- Use `pytest-asyncio` for async tests
- Mark async tests with `@pytest.mark.asyncio`
- Test both success and error cases
- Verify cache statistics after operations
- Test TTL expiration with `asyncio.sleep()`

**Testing Frameworks:**
- pytest >= 8.4.0
- pytest-asyncio >= 1.2.0
- pytest-cov >= 7.0.0 (for coverage reports)

### Architecture References

**ADR-004: Cache Strategy MVP**
- Defines cache-raw pattern (cache full API responses, filter in-memory)
- Explains why in-memory cache is sufficient for MVP
- Documents migration triggers for Redis (if needed later)
- **CRITICAL**: Anti-pattern warning about synchronous wrappers

**ADR-006: Service Layer Pattern**
- Services handle caching decisions (not tools)
- Tools remain thin wrappers
- Business logic stays in service layer

**ADR-007: FastMCP Context Injection Pattern**
- Cache injected via lifespan context
- Accessed in tools via `ctx.request_context.lifespan_context["cache"]`
- Services receive cache via constructor injection

**ADR-011: Extensibility Infrastructure Patterns**
- BaseService provides cache helper methods
- Services inherit from BaseService for standardized caching
- Cache-raw pattern implemented in service layer

**ADR-012: Resources Strategy - Defer to Post-MVP**
- MCP Resources deferred to post-MVP (focus on tools)
- Caching infrastructure remains valuable for all MCP primitives
- Can support resources in future without architecture changes

### BaseService TTL Refactor Pattern

**Current State (STORY-012):**
BaseService hard-codes TTL constants as class attributes:
```python
class BaseService:
    CACHE_TTL_PRODUCTS = 3600  # Hard-coded
    CACHE_TTL_TESTS = 300
    CACHE_TTL_BUGS = 60
```

**Required Refactor (This Story - AC3):**
BaseService must read TTLs from settings for consistency with ADR-004:

```python
# src/testio_mcp/services/base_service.py
from testio_mcp.config import settings

class BaseService:
    """Base service with caching infrastructure (ADR-011)."""

    def __init__(self, client: TestIOClient, cache: InMemoryCache):
        self.client = client
        self.cache = cache
        # Read TTLs from settings (instead of hard-coding)
        self.CACHE_TTL_PRODUCTS = settings.CACHE_TTL_PRODUCTS
        self.CACHE_TTL_TESTS = settings.CACHE_TTL_TESTS
        self.CACHE_TTL_BUGS = settings.CACHE_TTL_BUGS
```

**Impact:**
- ProductService, TestService, BugService automatically inherit updated TTLs
- All services now respect environment variable configuration
- No changes needed in service implementations (they use `self.CACHE_TTL_*`)
- Tests can override TTLs by modifying service instance attributes

**Testing Pattern:**
```python
# Override TTL for testing (shorter timeouts)
service.CACHE_TTL_PRODUCTS = 1  # 1 second for testing
await service.list_products()
await asyncio.sleep(2)  # Wait for expiration
```

### Source Tree (Relevant Files)

```
src/testio_mcp/
├── cache.py                  # NEW: InMemoryCache implementation
├── config.py                 # UPDATE: Add cache TTL constants
├── server.py                 # UPDATE: Initialize cache in lifespan, add ServerContext
├── tools/
│   └── cache_tools.py        # NEW: get_cache_stats, clear_cache tools
└── services/
    ├── base_service.py       # UPDATE: Read TTLs from settings (refactor)
    ├── product_service.py    # NO CHANGE: Inherits updated TTLs from BaseService
    ├── test_service.py       # NO CHANGE: Inherits updated TTLs from BaseService
    └── bug_service.py        # NO CHANGE: Inherits updated TTLs from BaseService

tests/
├── unit/
│   └── test_cache.py         # NEW: Cache unit tests (get/set/delete/stats/expiration/concurrency)
└── integration/
    └── test_cache_integration.py  # NEW: Service caching integration tests
```

### Cache Key Patterns (from ADR-004)

Services use these cache key formats:

```python
# Products (1 hour TTL)
"products:list:raw"                    # All products

# Tests (5 minute TTL)
"product:{product_id}:tests:raw"       # All tests for product

# Bugs (1 minute TTL)
"test:{test_id}:bugs:raw"              # All bugs for test
```

**Cache-Raw Pattern Benefits:**
- Single cache entry per resource (not per filter combination)
- 95%+ cache hit rate (vs ~20% with filter-specific keys)
- In-memory filtering is <1ms (vs 200-500ms API latency)
- Memory efficient (one copy of data, not duplicated per filter)

### Important Implementation Notes

1. **Async-Only Interface**
   - All cache methods MUST be async
   - Use `await cache.get()` and `await cache.set()` in all code
   - DO NOT create synchronous wrappers (causes event loop errors)

2. **Thread Safety**
   - Use `asyncio.Lock()` for concurrent access protection
   - Lock is acquired automatically in all cache methods
   - Safe for multiple simultaneous requests

3. **TTL Management**
   - Use `datetime.utcnow()` for consistent timezone handling
   - Check expiration on every `get()` operation
   - Automatically delete expired entries

4. **Statistics Tracking**
   - Increment hits/misses on every `get()` operation
   - Calculate hit rate as percentage
   - Reset stats on `clear()` operation

5. **Testing TTL Expiration**
   - Use short TTLs (1-2 seconds) in tests
   - Use `asyncio.sleep()` to wait for expiration
   - Verify cache returns None after expiration

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-04 | 1.0 | Initial story creation (included resources) | Ricardo Leon |
| 2025-11-06 | 2.0 | Revised to focus on caching only (resources deferred per ADR-012) | Sarah (PO) |
| 2025-11-06 | 2.1 | Added all template sections (Tasks, Change Log, Dev Agent Record, QA Results) | Sarah (PO) |
| 2025-11-06 | 2.2 | Fixed context injection pattern (AC2, Task 2) - now uses ADR-007 ServerContext | Sarah (PO) |
| 2025-11-06 | 2.3 | Added concrete integration tests (test_service_uses_cache, test_cache_ttl_expiration_integration) | Sarah (PO) |
| 2025-11-06 | 2.4 | Added concurrency test example (asyncio.gather) | Sarah (PO) |
| 2025-11-06 | 2.5 | Clarified BaseService TTL refactor requirements (AC3, Task 3, Dev Notes) | Sarah (PO) |
| 2025-11-06 | 2.6 | Added tool auto-registration note (Task 4) per ADR-011 | Sarah (PO) |

---

## Dev Agent Record

### Agent Model Used

- Claude Sonnet 4.5 (model ID: claude-sonnet-4-5-20250929)
- Dev Agent: James (Full Stack Developer)

### Debug Log References

- No significant issues encountered during implementation
- Fixed deprecation warning: Changed `datetime.utcnow()` to `datetime.now(UTC)` for Python 3.12 compatibility
- Fixed test failure: Updated `test_base_service.py` to check instance attributes (not class attributes) after TTL refactoring
- **Peer Review Fix (Codex)**: Implemented cache stampede protection - added in-flight fetch tracking in BaseService to prevent concurrent cache misses from making multiple API calls
- **Peer Review Fix**: Enhanced concurrent test to assert API call count == 1 (verifies stampede protection)

### Completion Notes

**Implementation Summary:**
- Enhanced existing InMemoryCache with statistics tracking, delete method, and improved docstrings
- Refactored BaseService to read TTL constants from settings (moved from class to instance attributes)
- Created two new cache monitoring tools (get_cache_stats, clear_cache) with comprehensive documentation
- Wrote 18 new tests (12 unit + 6 integration) covering all cache functionality
- **Peer Review (Codex)**: Fixed cache stampede vulnerability with in-flight fetch coordination
- All 212 tests pass with no regressions

**Key Enhancements:**
- Cache now tracks hits/misses/hit rate for monitoring effectiveness
- Modern datetime.now(UTC) instead of deprecated datetime.utcnow()
- **Stampede protection**: Only one API call per cache key/TTL window, even with concurrent misses
- Proper type hints (mypy --strict compliant)
- Comprehensive docstrings with usage examples and anti-pattern warnings
- Integration tests validate real service behavior with mocked clients

**Performance Verified:**
- Concurrent access tested with asyncio.gather (10 reads + 5 writes)
- **Stampede protection verified**: 5 concurrent requests = 1 API call (test asserts this)
- TTL expiration tested with asyncio.sleep delays
- Cache-or-fetch pattern confirmed working in ProductService

### File List

**Modified Files:**
- `src/testio_mcp/cache.py` - Enhanced with statistics, delete method, UTC datetime
- `src/testio_mcp/services/base_service.py` - Refactored to read TTLs from settings
- `tests/unit/test_base_service.py` - Updated TTL test to check instance attributes
- `README.md` - Added cache monitoring tools to tool list (7 → 9 tools)

**Created Files:**
- `src/testio_mcp/tools/cache_tools.py` - get_cache_stats and clear_cache tools
- `tests/unit/test_cache.py` - 12 comprehensive unit tests
- `tests/integration/test_cache_integration.py` - 6 integration tests with services

**No Changes Needed:**
- `src/testio_mcp/config.py` - TTL configuration already existed from prior story
- `src/testio_mcp/server.py` - ServerContext and lifespan already configured
- `.env.example` - TTL variables already documented (lines 12-15)
- `CLAUDE.md` - Cache configuration already documented

---

## QA Results

### Review Date: 2025-11-06

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Overall Assessment: EXCELLENT**

This implementation demonstrates exceptional engineering quality with comprehensive test coverage, excellent documentation, and thoughtful architecture decisions. The caching layer follows all established patterns (ADR-004, ADR-006, ADR-007, ADR-011) and includes robust stampede protection added during peer review.

**Highlights:**
- **Modern Python practices**: Uses `datetime.now(UTC)` (Python 3.12+), proper async/await patterns
- **Type safety**: Full mypy --strict compliance with no type: ignore needed
- **Documentation excellence**: Every method has comprehensive docstrings with usage examples
- **Stampede protection**: BaseService prevents thundering herd via in-flight fetch coordination
- **Test coverage**: 18 new tests (12 unit + 6 integration) covering all scenarios including edge cases

### Requirements Traceability

All acceptance criteria validated with comprehensive test coverage:

**AC1: InMemoryCache Implementation** ✓
- **Given** an async-only cache interface
- **When** values are stored with TTL
- **Then** expired entries are automatically removed on access
- **Tests**: 12 unit tests in `tests/unit/test_cache.py`
  - Basic get/set operations (test_cache_get_set)
  - Cache misses (test_cache_miss)
  - TTL expiration with asyncio.sleep (test_cache_expiration)
  - Statistics tracking hits/misses (test_cache_statistics)
  - Delete operations (test_cache_delete)
  - Clear operations with stat reset (test_cache_clear)
  - Key overwrites (test_cache_overwrites_existing_key)
  - Complex data structures (test_cache_complex_values)
  - Concurrent access (test_concurrent_access) - 10 reads + 5 writes
  - Zero TTL edge case (test_cache_zero_ttl)
  - Multiple independent keys (test_cache_multiple_keys)
  - Stats with no activity (test_cache_stats_with_no_requests)

**AC2: Cache Integration in Server Lifespan** ✓
- **Given** a FastMCP server with lifespan handler
- **When** server initializes
- **Then** cache is available via dependency injection
- **Evidence**: ServerContext pattern already implemented in prior story, verified working

**AC3: Cache TTL Configuration** ✓
- **Given** BaseService with hard-coded TTL constants
- **When** refactored to read from settings
- **Then** all services respect environment variable configuration
- **Tests**: Updated `test_base_service.py` to verify instance attributes
- **Impact**: ProductService, TestService, BugService automatically inherit updated behavior

**AC4: Cache Monitoring Tools** ✓
- **Given** cache statistics and management needs
- **When** tools are auto-registered (ADR-011)
- **Then** admins can monitor performance and clear cache
- **Tests**: Tools verified via MCP protocol
- **Documentation**: Comprehensive docstrings with usage examples and typical hit rate guidance (90%+ excellent, 70-89% good, 50-69% fair, <50% poor)

**AC5: Integration Testing** ✓
- **Given** service-level cache behavior requirements
- **When** integration tests run
- **Then** caching reduces API calls and respects TTL
- **Tests**: 6 integration tests in `tests/integration/test_cache_integration.py`
  - Service uses cache (test_service_uses_cache)
  - TTL expiration respected (test_cache_ttl_expiration_integration)
  - Filter combinations handled (test_cache_with_different_filters)
  - Service isolation (test_cache_isolation_between_services)
  - Error handling (test_cache_handles_api_errors)
  - **Stampede protection** (test_cache_concurrent_service_requests) - Critical test verifying only 1 API call with 5 concurrent requests

### Refactoring Performed

No refactoring performed during QA review. The implementation quality is excellent as-is.

**Peer Review Improvements (Codex):**
- Added cache stampede protection in BaseService (lines 71-179 in base_service.py)
- Enhanced concurrent test to assert API call count == 1 (verifies stampede protection)

### Compliance Check

- **Coding Standards**: ✓ All code passes ruff format/check, mypy --strict with zero errors
- **Project Structure**: ✓ Files organized per established patterns (services/, tools/, tests/unit/, tests/integration/)
- **Testing Strategy**: ✓ Comprehensive test pyramid with 18 new tests
- **All ACs Met**: ✓ All 5 acceptance criteria fully implemented and tested

### Test Architecture Assessment

**Test Level Appropriateness: EXCELLENT**

- **Unit Tests (12)**: Focus on InMemoryCache behavior in isolation
  - Fast execution (<1 second total)
  - No external dependencies
  - Cover all cache operations and edge cases
  - Proper use of asyncio.sleep for TTL testing

- **Integration Tests (6)**: Verify service-level cache behavior
  - Mock TestIOClient (not real API)
  - Test cache-or-fetch patterns
  - Verify TTL expiration with services
  - Test concurrent access and stampede protection
  - Validate error handling (errors not cached)

**Test Design Quality: EXCELLENT**
- Clear test names describing what's being tested
- Comprehensive edge case coverage (zero TTL, concurrent access, expired entries)
- Proper async/await patterns throughout
- Good use of pytest-asyncio markers
- Assertions verify both functionality and statistics

**Critical Test: Stampede Protection** (test_cache_concurrent_service_requests)
- Makes 5 concurrent requests to trigger cache miss
- Asserts only 1 API call made (stampede protection working)
- Uses asyncio.gather for true concurrency
- Includes clear assertion message explaining the check

### Non-Functional Requirements (NFRs)

**Security**: ✓ PASS
- No security risks identified
- Cache keys are internal (not user-controlled)
- No sensitive data leakage concerns
- Statistics don't expose sensitive information

**Performance**: ✓ PASS
- Cache operations are O(1) with asyncio.Lock protection
- Expected hit rate: 70%+ (per tool documentation)
- Reduces API latency from 200-500ms to <1ms (in-memory access)
- Stampede protection prevents redundant API calls under load

**Reliability**: ✓ PASS
- Thread-safe concurrent access via asyncio.Lock
- Proper error handling (errors not cached)
- Automatic expiration cleanup (lazy removal)
- No background tasks (simpler failure modes)

**Maintainability**: ✓ PASS
- Excellent documentation with usage examples
- Clear separation of concerns (cache vs services)
- Consistent patterns across all services (BaseService)
- Easy to test (no complex mocking required)

### Testability Evaluation

**Controllability**: ✓ EXCELLENT
- Cache TTL can be overridden in tests (instance attributes)
- Mock client allows precise control of API responses
- Async nature allows testing with asyncio.sleep for time-based scenarios

**Observability**: ✓ EXCELLENT
- Cache statistics provide hit/miss/rate visibility
- Tests can inspect cache state directly
- Clear assertion messages explain what's being verified

**Debuggability**: ✓ EXCELLENT
- Comprehensive docstrings explain behavior
- Statistics tracking aids troubleshooting
- No complex state machines or hidden dependencies

### Technical Debt Identification

**None identified.** This implementation follows all established patterns and best practices.

**Proactive Improvements Already Made:**
- Stampede protection added (prevents cache thundering herd)
- Modern datetime handling (UTC-aware, Python 3.12+)
- Instance-level TTL attributes (enables test overrides)
- Comprehensive anti-pattern warnings in docstrings

### Security Review

**No security concerns identified.**

- Cache keys are internal application strings (not user input)
- No SQL injection, XSS, or command injection vectors
- Statistics are safe to expose (don't leak sensitive data)
- Clear cache tool properly documented with caution warnings

### Performance Considerations

**Cache Performance: EXCELLENT**

- Expected hit rate: 70-90% based on TTL settings
- In-memory access: <1ms (vs 200-500ms API latency)
- Stampede protection prevents redundant API calls
- Memory overhead: Minimal (products + tests + bugs for 1-5 users)

**Concurrency Performance: EXCELLENT**

- asyncio.Lock provides efficient coordination
- Stampede protection reduces API load under concurrent requests
- No bottlenecks identified in integration tests

**Migration Path:** ADR-004 defines clear triggers for Redis upgrade (cache >100MB, hit rate <50%, multi-instance deployment)

### Files Modified During Review

**None.** No code changes needed during QA review.

### Gate Status

**Gate: PASS** → docs/qa/gates/1.7-in-memory-caching-layer.yml

**Quality Score: 100/100**

All acceptance criteria met, comprehensive test coverage, excellent code quality, no security concerns, and outstanding documentation. This implementation sets a high bar for future stories.

**Risk Profile:** No significant risks identified
**NFR Assessment:** All NFRs validated as PASS

### Recommended Status

**✓ Ready for Done**

All acceptance criteria validated, tests comprehensive, code quality excellent, no blocking issues identified. This story is complete and ready for production deployment.

**Post-Deployment Monitoring:**
- Monitor cache hit rate via `get_cache_stats` tool
- Expected: 70%+ hit rate under normal usage
- If hit rate drops below 50%, review TTL settings per ADR-004

---

## Definition of Done

- [x] All acceptance criteria met (AC1-AC5)
- [x] InMemoryCache class implemented with async interface
- [x] Cache integrated in server lifespan (already done in prior story)
- [x] TTL configuration added to settings (already done in prior story)
- [x] Cache monitoring tools implemented (get_cache_stats, clear_cache)
- [x] Unit tests for cache logic (12 tests, comprehensive coverage)
- [x] Integration tests for cache behavior (6 tests)
- [x] Cache expiration verified in tests
- [x] Concurrent access tested (asyncio.gather with 15 concurrent tasks)
- [x] Code follows best practices (async/await, type hints, mypy --strict)
- [x] All tests pass locally (212 passed, 11 skipped as expected)
- [x] Peer review completed (Codex peer review + Quinn QA review - 100/100 quality score)
- [x] Documentation updated (README)
- [x] Cache TTLs documented in .env.example (already existed)
- [x] No regression in existing tests (all 212 tests pass)

---

## Dependencies

**Depends On:**
- STORY-001 (TestIO API client with httpx)
- STORY-004 (ProductService - will use caching)
- STORY-005 (BugService - uses cache-raw pattern)
- STORY-012 (BaseService infrastructure - cache helpers)

**Blocks:**
- None (caching is infrastructure improvement, doesn't block features)

**Related ADRs:**
- ADR-004: Cache Strategy MVP (defines cache-raw pattern, TTLs)
- ADR-006: Service Layer Pattern (services handle caching)
- ADR-007: FastMCP Context Injection Pattern (cache injection)
- ADR-011: Extensibility Infrastructure Patterns (BaseService)
- ADR-012: Resources Strategy - Defer to Post-MVP (explains resource removal)

---

## References

### Architecture
- **ADR-004**: `docs/architecture/adrs/ADR-004-cache-strategy-mvp.md`
- **ADR-012**: `docs/architecture/adrs/ADR-012-resources-strategy-defer-to-post-mvp.md`
- **Epic**: `docs/epics/epic-001-testio-mcp-mvp.md`

### Technical Documentation
- **Python asyncio**: https://docs.python.org/3/library/asyncio.html
- **asyncio.Lock**: https://docs.python.org/3/library/asyncio-sync.html#asyncio.Lock
- **FastMCP Context**: https://gofastmcp.com/servers/context
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/

### MCP Specification
- **MCP Resources Spec**: https://modelcontextprotocol.io/specification/2025-03-26/server/resources (for future reference)
- **MCP Server Concepts**: https://modelcontextprotocol.io/docs/learn/server-concepts

---

## Notes

### Why No Resources in This Story?

MCP Resources were originally part of STORY-007 but have been **deferred to post-MVP** (see ADR-012).

**Key Reasons:**
1. Current tools provide excellent query capability (model-controlled)
2. Resources are application-controlled (best for UI-based context loading)
3. No UI currently exists for resource selection
4. Many production MCP servers implement tools only
5. YAGNI principle - defer until clear use case emerges

**Caching Remains Valuable:**
- Benefits all MCP primitives (tools, resources, prompts)
- Improves response times regardless of which primitive is used
- Can support future resources without architecture changes

**When to Add Resources:**
See ADR-012 "Migration Triggers" section for conditions that would justify adding resources post-MVP.
