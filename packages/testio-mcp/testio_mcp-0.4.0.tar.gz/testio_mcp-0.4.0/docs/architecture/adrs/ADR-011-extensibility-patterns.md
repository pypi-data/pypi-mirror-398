# ADR-011: Extensibility Infrastructure Patterns

**Status:** ✅ Active

**Date:** 2025-11-06

**Updated:** 2025-11-20 (Code examples updated for PersistentCache)

**Context:** Reducing boilerplate and establishing patterns for adding new services and tools

**Note:** Code examples in this ADR originally used `InMemoryCache` (v0.1.x). The patterns remain valid with `PersistentCache` (v0.2.0+) and repository pattern - simply replace `cache` with repository dependencies.

---

## Context

After implementing 5 services (Test, Product, Bug, Activity, Report) and 7 MCP tools, we identified significant code duplication:

### Observed Pain Points

1. **Service Boilerplate** (~30 lines per service):
   - Identical `__init__` constructors for dependency injection
   - Repeated cache key formatting logic
   - Duplicated cache-or-fetch patterns
   - Manual TTL constant definitions

2. **Tool Boilerplate** (~5 lines per tool):
   - Identical context extraction code in every tool
   - Verbose dependency injection from lifespan context
   - Inconsistent error handling (dict returns vs exceptions)
   - Manual tool registration via imports

3. **Inconsistent Patterns**:
   - Some services cached filtered results (cache key explosion)
   - Some services used different cache key formats
   - Error handling varied between tools (dicts vs exceptions)

### Requirements

From STORY-012:
- Reduce boilerplate by ~40% (target: eliminate 220-250 lines)
- Establish consistent service creation pattern
- Simplify tool creation for contributors
- Maintain strict type safety (mypy --strict)
- No runtime performance degradation

---

## Decision

### 1. BaseService Class for Shared Patterns

Create abstract base class with common service infrastructure:

```python
# src/testio_mcp/services/base_service.py

class BaseService:
    """Base class for all service layer classes.

    Provides:
    - Standard dependency injection constructor
    - Cache key formatting helpers
    - Cache-or-fetch pattern with 404 transformation
    - TTL constants
    """

    # Cache TTL constants (in seconds)
    CACHE_TTL_PRODUCTS = 3600  # 1 hour
    CACHE_TTL_TESTS = 300      # 5 minutes
    CACHE_TTL_BUGS = 60        # 1 minute

    def __init__(self, client: TestIOClient, test_repo: TestRepository, bug_repo: BugRepository) -> None:
        """Initialize service with injected dependencies."""
        self.client = client
        self.test_repo = test_repo
        self.bug_repo = bug_repo
        self.cache = cache

    def _make_cache_key(self, *parts: str | int | None) -> str:
        """Create consistent cache key from parts."""
        return ":".join(str(part) for part in parts)

    async def _get_cached_or_fetch(
        self,
        cache_key: str,
        fetch_fn: Callable[[], Awaitable[dict[str, Any]]],
        ttl_seconds: int,
        transform_404: Exception | None = None,
    ) -> dict[str, Any]:
        """Get data from cache or fetch from API if not cached."""
        # Check cache
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cast(dict[str, Any], cached)

        # Fetch from API
        try:
            result = await fetch_fn()
        except TestIOAPIError as e:
            if e.status_code == 404 and transform_404:
                raise transform_404 from e
            raise

        # Cache result
        await self.cache.set(cache_key, result, ttl_seconds=ttl_seconds)
        return result
```

**Benefits:**
- Eliminates ~30 lines of boilerplate per service
- Consistent cache key formatting across all services
- Standardized 404 error transformation
- Single source of truth for TTL values

**Usage:**
```python
class TestService(BaseService):
    async def get_test_status(self, test_id: int) -> dict:
        return await self._get_cached_or_fetch(
            cache_key=self._make_cache_key("test", test_id, "status"),
            fetch_fn=lambda: self.client.get(f"tests/{test_id}"),
            ttl_seconds=self.CACHE_TTL_TESTS,
            transform_404=TestNotFoundException(test_id)
        )
```

### 2. get_service() Helper for Tool Simplification

Create utility function to extract dependencies from FastMCP context:

```python
# src/testio_mcp/utilities/service_helpers.py

def get_service[ServiceT: BaseService](
    ctx: Context,
    service_class: type[ServiceT]
) -> ServiceT:
    """Extract dependencies from FastMCP context and create service instance.

    Reduces tool boilerplate from 5 lines to 1 line while maintaining
    full type safety for mypy strict mode.
    """
    lifespan_ctx = cast("ServerContext", ctx.request_context.lifespan_context)
    client = lifespan_ctx["testio_client"]
    cache = lifespan_ctx["cache"]
    return service_class(client=client, cache=cache)
```

**Benefits:**
- Reduces 5 lines → 1 line per tool (80% reduction)
- Full type inference via PEP 695 generics
- No type: ignore needed
- Centralizes context extraction logic

**Usage:**
```python
@mcp.tool()
async def get_test_status(test_id: int, ctx: Context) -> dict:
    service = get_service(ctx, TestService)  # Fully typed!
    return await service.get_test_status(test_id)
```

### 3. FastMCP ToolError Exception Pattern

Replace dict-based error returns with FastMCP's ToolError exceptions:

```python
# ❌ BEFORE: Dict returns (inconsistent, not FastMCP idiomatic)
@mcp.tool()
async def get_test_status(test_id: int, ctx: Context) -> dict:
    try:
        service = get_service(ctx, TestService)
        return await service.get_test_status(test_id)
    except TestNotFoundException:
        return {
            "error": "❌ Test not found",
            "context": "ℹ️ May be deleted",
            "hint": "💡 Verify test ID"
        }

# ✅ AFTER: ToolError exceptions (FastMCP best practice)
from fastmcp.exceptions import ToolError

@mcp.tool()
async def get_test_status(test_id: int, ctx: Context) -> dict:
    service = get_service(ctx, TestService)
    try:
        return await service.get_test_status(test_id)
    except TestNotFoundException:
        raise ToolError(
            "❌ Test not found\n"
            "ℹ️ May be deleted\n"
            "💡 Verify test ID"
        ) from None
```

**Benefits:**
- FastMCP best practice (proper exception handling)
- Better UX (displays correctly in Claude UI)
- Removes error dict boilerplate (~20 lines per tool)
- Consistent error format across all tools

### 4. Auto-Discovery via pkgutil

Replace manual tool imports with automatic discovery:

```python
# ❌ BEFORE: Manual imports (must update on every new tool)
from .tools import (
    test_status_tool,
    get_test_bugs_tool,
    list_products_tool,
    list_tests_tool,
    timeframe_activity_tool,
    generate_status_report_tool,
)

# ✅ AFTER: Auto-discovery (no updates needed for new tools)
import pkgutil
import testio_mcp.tools

for module_info in pkgutil.iter_modules(testio_mcp.tools.__path__):
    __import__(f"testio_mcp.tools.{module_info.name}")

logger.info(f"Auto-discovery complete: {len(mcp._tool_manager._tools)} tools registered")
```

**Benefits:**
- No manual import updates when adding new tools
- Automatic tool registration (just create `*_tool.py` file)
- Reduces server.py maintenance burden
- Logs total tools registered for debugging

**Trade-offs:**
- All `*_tool.py` modules are imported (minimal overhead)
- Tools must use `@mcp.tool()` decorator (already required)

---

## Implementation

### Phase 1: BaseService Foundation
1. Create `base_service.py` with `_make_cache_key()` and `_get_cached_or_fetch()`
2. Add .env-configurable TTL constants to Settings
3. Migrate existing services to inherit from BaseService
4. Update shared test fixtures to inject Settings

**Metrics:**
- 4 services migrated (Test, Product, Activity, Bug)
- ~120 lines of boilerplate eliminated
- All tests passing (no behavior changes)

### Phase 2: Cache-Raw Pattern
1. Refactor BugService to cache raw API responses (not filtered results)
2. Add `_paginate()` helper method
3. Fix continuation token cache-bypass bug
4. Update tests to verify cache usage during pagination

**Metrics:**
- Cache key explosion eliminated (1 key per test vs N filter combos)
- Cache hit rate: 95%+ (up from ~20%)
- HIGH severity bug fixed (continuation tokens bypassing cache)

### Phase 3: Tool Layer Refactoring
1. Create `get_service()` helper in utilities/service_helpers.py
2. Migrate 6 tools to use get_service() + ToolError pattern
3. Implement auto-discovery in server.py
4. Add unit tests for service_helpers module

**Metrics:**
- 6 tools refactored (~165 lines eliminated)
- Auto-discovery: 7 tools registered automatically
- Full type safety maintained (mypy --strict passing)

---

## Consequences

### Positive

1. **Reduced Boilerplate** (~300+ lines eliminated)
   - Services: ~30 lines per service → 0 lines
   - Tools: ~5 lines per tool → 1 line
   - Error handling: ~20 lines per tool → 4-6 lines
   - Server imports: ~10 lines → 5 lines (auto-discovery)

2. **Consistency**
   - All services use same cache key format (`_make_cache_key()`)
   - All tools use same error handling (ToolError)
   - All services use same DI pattern (inherit BaseService)

3. **Developer Experience**
   - Adding new service: Just inherit BaseService
   - Adding new tool: Just create `*_tool.py` with `@mcp.tool()`
   - No manual registration needed

4. **Type Safety**
   - Full mypy --strict compliance
   - PEP 695 generics for get_service()
   - No type: ignore needed anywhere

5. **Performance**
   - Cache-raw pattern: 95%+ hit rate
   - In-memory filtering: <1ms overhead
   - Eliminated redundant API calls

### Negative

1. **Additional Abstraction**
   - New developers must understand BaseService
   - Less explicit (magic in base class)
   - Debugging may require understanding inheritance

2. **Coupling**
   - All services depend on BaseService
   - Changes to BaseService affect all services
   - Migration to different pattern requires touching all services

3. **Auto-Discovery Surprises**
   - All modules in tools/ are imported (can't selectively disable)
   - Import errors break entire server startup
   - Less explicit than manual imports

### Neutral

1. **Testing**
   - Services still test the same way (mock client/cache)
   - Tools still test the same way (integration tests)
   - No test complexity added

2. **Documentation**
   - Need to document BaseService pattern
   - Need to document get_service() usage
   - Need to update CLAUDE.md with new patterns

---

## Alternatives Considered

### 1. Decorator Pattern Instead of BaseService

```python
@cache_or_fetch(cache_key="test:{test_id}", ttl=300)
async def get_test_status(test_id: int) -> dict:
    return await client.get(f"tests/{test_id}")
```

**Rejected because:**
- PEP 612 ParamSpec cannot capture Context parameter
- Would need to pass context explicitly (verbose)
- Loses type information through decorator
- More complex than inheritance

### 2. Manual Tool Registration (Keep Explicit Imports)

```python
# Keep manual imports for clarity
from .tools import test_status_tool, get_test_bugs_tool, ...
```

**Rejected because:**
- Developer must remember to add imports for new tools
- Easy to forget (silently broken)
- Auto-discovery is standard in other frameworks (Django, Flask)

### 3. Mixin Classes Instead of BaseService

```python
class CacheMixin:
    def _make_cache_key(...): ...

class TestService(CacheMixin):
    ...
```

**Rejected because:**
- Multiple inheritance complexity
- Still need to inject client/cache
- Doesn't reduce boilerplate as much

---

## Related Decisions

- **ADR-004:** Cache Strategy MVP - Cache-raw pattern documented here
- **ADR-006:** Service Layer Pattern - BaseService extends this pattern
- **ADR-007:** FastMCP Context Injection - get_service() uses this pattern

---

## References

- [PEP 695: Type Parameter Syntax](https://peps.python.org/pep-0695/)
- [FastMCP ToolError Documentation](https://gofastmcp.com/tools/errors)
- [Python pkgutil Module](https://docs.python.org/3/library/pkgutil.html)
- [Service Layer Pattern (Fowler)](https://martinfowler.com/eaaCatalog/serviceLayer.html)

---

## Migration Guide

### Adding a New Service

```python
# 1. Inherit from BaseService
from testio_mcp.services.base_service import BaseService

class NewService(BaseService):
    async def get_resource(self, resource_id: int) -> dict:
        # 2. Use _get_cached_or_fetch helper
        return await self._get_cached_or_fetch(
            cache_key=self._make_cache_key("resource", resource_id),
            fetch_fn=lambda: self.client.get(f"resources/{resource_id}"),
            ttl_seconds=self.CACHE_TTL_TESTS,  # Use appropriate TTL
            transform_404=ResourceNotFoundException(resource_id)
        )
```

### Adding a New Tool

```python
# 1. Create new file: src/testio_mcp/tools/new_tool.py
from fastmcp import Context
from fastmcp.exceptions import ToolError
from testio_mcp.server import mcp
from testio_mcp.services.new_service import NewService
from testio_mcp.utilities import get_service

@mcp.tool()
async def get_resource(resource_id: int, ctx: Context) -> dict:
    # 2. Use get_service helper (1 line!)
    service = get_service(ctx, NewService)

    # 3. Use ToolError for exceptions
    try:
        return await service.get_resource(resource_id)
    except ResourceNotFoundException:
        raise ToolError("❌ Resource not found") from None

# 4. No registration needed! Auto-discovery handles it.
```

Tool will be automatically discovered and registered on server startup.

---

## Success Metrics

**Achieved (STORY-012):**
- ✅ Boilerplate reduction: ~300+ lines eliminated
- ✅ Services migrated: 4/4 (100%)
- ✅ Tools migrated: 6/6 (100%)
- ✅ Auto-discovery: 7 tools registered
- ✅ Type safety: mypy --strict passing
- ✅ Tests passing: 186 passed, 11 skipped
- ✅ Cache performance: 95%+ hit rate (BugService)

**Future Improvements:**
- Add BaseService usage examples to CLAUDE.md
- Document cache-raw pattern decision criteria
- Add performance monitoring for cache hit rates
