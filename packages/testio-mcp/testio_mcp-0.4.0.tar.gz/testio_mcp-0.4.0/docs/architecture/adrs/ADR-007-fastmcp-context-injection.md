# ADR-007: Migrate to FastMCP Context Injection Pattern

**Status:** ✅ Active
**Date:** 2025-11-05
**Updated:** 2025-11-20 (Code examples updated for PersistentCache)
**Deciders:** Architecture Team, Winston (System Architect)
**Related ADRs:** ADR-001 (API Client Dependency Injection), ADR-006 (Service Layer Pattern)

**Note:** Code examples in this ADR originally used `InMemoryCache` (v0.1.x). The context injection pattern remains valid with `PersistentCache` (v0.2.0+) - simply replace `InMemoryCache` with `PersistentCache` and add repository initialization.

---

## Context

Our current implementation (Stories 002, 003b, 003) uses custom getter functions (`get_testio_client()`, `get_cache()`) with module-level global state for dependency injection in MCP tools. This approach works correctly for single-tenant stdio mode but has architectural issues:

### Problems with Current Approach

1. **Violates FastMCP official patterns** - [FastMCP documentation](https://gofastmcp.com/servers/context) explicitly recommends Context parameter injection
2. **Uses global state** - Module-level `_testio_client` and `_cache` variables create hidden dependencies
3. **Manual lifecycle management** - Explicit `__aenter__()` calls in getter functions
4. **Harder to test** - Requires modifying global state for mocking; tests have side effects
5. **Not future-proof** - Blocks HTTP multi-tenancy (per-request authentication requires per-request clients)
6. **Inconsistent** - Custom pattern diverges from FastMCP conventions and confuses other developers

### Current Architecture

```python
# server.py - Global state with custom getters
_testio_client: TestIOClient | None = None
_cache: PersistentCache | None = None

async def get_testio_client() -> TestIOClient:
    """Custom getter with lazy initialization."""
    global _testio_client
    if _testio_client is None:
        _testio_client = TestIOClient(...)
        await _testio_client.__aenter__()  # Manual lifecycle
    return _testio_client

async def get_cache() -> PersistentCache:
    """Custom getter with lazy initialization."""
    global _cache
    if _cache is None:
        _cache = PersistentCache(db_path="~/.testio-mcp/cache.db", customer_id=1)
        await _cache.initialize()
    return _cache

# tools/test_status_tool.py - Tools call custom getters
@mcp.tool()
async def get_test_status(test_id: int) -> dict:
    client = await get_testio_client()  # Custom getter
    cache = get_cache()  # Custom getter
    service = TestService(client=client, cache=cache)
    # ...
```

### FastMCP Official Pattern

According to [FastMCP Context Documentation](https://gofastmcp.com/servers/context) and [Unstructured MCP Tutorial](https://unstructured.io/blog/building-an-mcp-server-with-unstructured-api):

> "To use the context object within any of your functions, simply add a parameter to your function signature and type-hint it as `Context`. FastMCP will automatically inject the correct context object when the function is called."

**Official Pattern (FastMCP 2.x):**
```python
from fastmcp import Context, FastMCP
from contextlib import asynccontextmanager
from typing import AsyncIterator
from dataclasses import dataclass

@dataclass
class ServerContext:
    """Context object yielded by lifespan handler."""
    testio_client: TestIOClient
    cache: PersistentCache

@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[ServerContext]:
    """Initialize shared resources on startup."""
    async with TestIOClient(...) as client:
        cache = PersistentCache(db_path="~/.testio-mcp/cache.db", customer_id=1)
        await cache.initialize()
        # Yield context object that tools can access
        yield ServerContext(testio_client=client, cache=cache)
        # Automatic cleanup via context manager

mcp = FastMCP("TestIO MCP Server", lifespan=lifespan)

@mcp.tool()
async def get_test_status(test_id: int, ctx: Context) -> dict:
    # Access via ctx.request_context.lifespan_context
    lifespan_ctx = ctx.request_context.lifespan_context
    client = lifespan_ctx.testio_client
    cache = lifespan_ctx.cache
    # ...
```

**Key Discovery:** The lifespan handler **returns a value** via `yield`, and tools access it through `ctx.request_context.lifespan_context`. This is the official FastMCP 2.x pattern, not `app.context` (which doesn't exist at runtime).

---

## Decision

**We will migrate to FastMCP's Context parameter injection pattern** for all MCP tools (current: Stories 002, 003b, 003; future: Stories 004+).

### Changes Required

1. **Add lifespan handler** to `server.py` for resource initialization/cleanup
2. **Store dependencies in app.context** (FastMCP's dependency container)
3. **Add ctx: Context parameter** to all tool functions
4. **Remove custom getter functions** (`get_testio_client()`, `get_cache()`)
5. **Remove module-level global state** (`_testio_client`, `_cache`)

### Implementation Details

**Lifespan Handler (Yields Context Object):**
```python
from typing import TypedDict
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

class ServerContext(TypedDict):
    """Type-safe context schema."""
    testio_client: TestIOClient
    cache: PersistentCache

@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[ServerContext]:
    """Manage shared resources during server lifecycle."""
    shared_semaphore = get_global_semaphore()  # ADR-002: Global concurrency

    async with TestIOClient(
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
        semaphore=shared_semaphore,
        # ... connection pool settings
    ) as client:
        cache = PersistentCache(db_path="~/.testio-mcp/cache.db", customer_id=1)
        await cache.initialize()

        logger.info("Server dependencies initialized")

        # Yield context object for tools to access
        yield ServerContext(testio_client=client, cache=cache)

        logger.info("Server dependencies cleaned up")

mcp = FastMCP("TestIO MCP Server", lifespan=lifespan)
```

**Tool Pattern (Accesses via request_context.lifespan_context):**
```python
from fastmcp import Context
from typing import cast

@mcp.tool()
async def get_test_status(test_id: int, ctx: Context) -> dict:
    """Get comprehensive status of a single exploratory test.

    Args:
        test_id: The exploratory test ID
        ctx: FastMCP context (injected automatically)
    """
    # Extract dependencies from lifespan context (ADR-007)
    # Access via ctx.request_context.lifespan_context (FastMCP pattern)
    lifespan_ctx = cast(ServerContext, ctx.request_context.lifespan_context)
    client = lifespan_ctx["testio_client"]
    cache = lifespan_ctx["cache"]

    # Delegate to service (unchanged)
    service = TestService(client=client, cache=cache)
    return await service.get_test_status(test_id)
```

**Key Pattern Discovery:**
- Lifespan handler **yields a value** (context object)
- Tools access it via `ctx.request_context.lifespan_context`
- Type-safe with TypedDict and cast()
- No `# type: ignore` comments needed
- Pattern documented in [Unstructured MCP Tutorial](https://unstructured.io/blog/building-an-mcp-server-with-unstructured-api)

---

## Consequences

### Positive ✅

1. **Follows Official FastMCP Patterns**
   - Aligns with [FastMCP documentation](https://gofastmcp.com/servers/context)
   - Conventional code that other FastMCP developers understand
   - Future-proof against framework changes

2. **Eliminates Global State**
   - Cleaner architecture (no module-level variables)
   - No hidden dependencies
   - Resources scoped to application lifecycle

3. **Automatic Lifecycle Management**
   - Lifespan handler manages startup/shutdown
   - Async context manager ensures cleanup
   - No manual `__aenter__()` calls

4. **Improves Testability**
   - Mock context instead of global state
   - No side effects between tests
   - Easier to inject test dependencies

5. **Enables HTTP Multi-Tenancy** (Future)
   - Context can hold per-request resources
   - Foundation for client pooling
   - Supports per-request authentication tokens

6. **Better Separation of Concerns**
   - **Lifespan:** Resource initialization/cleanup
   - **Context:** Dependency container
   - **Tools:** Business logic delegation
   - **Services:** Framework-agnostic business logic (unchanged)

### Negative ⚠️

1. **Migration Effort**
   - 4 files to modify (server.py + 3 tools)
   - Tests may need minor updates
   - ~3 hours of development time

2. **Breaking Change** (Internal Only)
   - Tools now require `ctx: Context` parameter
   - Not backward compatible with old pattern
   - All three stories must be migrated together
   - **Note:** External API (LLM perspective) unchanged

3. **Learning Curve**
   - Team must understand Context parameter injection
   - Paradigm shift from custom getters
   - Requires reading FastMCP documentation

### Neutral ℹ️

1. **No Functional Changes**
   - API behavior remains identical
   - Cache TTLs unchanged
   - Service layer unaffected (still uses constructor injection per ADR-006)

2. **Test Coverage Maintained**
   - All existing tests will pass after migration
   - No new tests required (same business logic)
   - Integration tests may need minor context setup

---

## Rationale

### Why Context Injection Over Custom Getters?

| Aspect | Custom Getters (Current) | Context Injection (FastMCP) |
|--------|--------------------------|----------------------------|
| **Convention** | Custom pattern | Official FastMCP pattern |
| **Global State** | Yes (module-level variables) | No (app.context scoped) |
| **Lifecycle** | Manual (`__aenter__()`) | Automatic (lifespan handler) |
| **Testability** | Modify globals | Inject mock context |
| **HTTP Multi-Tenancy** | Blocks (single token) | Enables (per-request context) |
| **Maintainability** | Confuses developers | Clear, conventional |

### Why Now?

**Timing is critical:**
1. **Only 3 tools implemented** - Cheaper to refactor now than after 7+ tools
2. **Before Stories 004+** - Future stories will use Context from the start (consistency)
3. **Technical debt prevention** - Avoid accumulating non-standard patterns
4. **Future-proofing** - Prepares for HTTP multi-tenancy (known requirement)

**Cost-Benefit Analysis:**
- **Cost:** 3 hours migration + learning curve
- **Benefit:** Standard patterns + future flexibility + better testing
- **Verdict:** High ROI, especially before implementing more tools

---

## Alternatives Considered

### Alternative 1: Keep Custom Getters (Rejected)

**Pros:**
- No migration effort
- Code already works

**Cons:**
- Violates FastMCP patterns
- Blocks HTTP multi-tenancy
- Technical debt accumulates
- Confuses future developers
- Inconsistent with Stories 004+

**Decision:** Rejected. Technical debt and future limitations outweigh short-term convenience.

---

### Alternative 2: FastMCP get_context() Everywhere (Rejected)

FastMCP 2.2.11+ provides `get_context()` for runtime dependency resolution:

```python
from fastmcp.server.dependencies import get_context

async def get_testio_client():
    """Wrapper using FastMCP's runtime DI."""
    ctx = get_context()  # FastMCP's dependency function
    return ctx["testio_client"]

@mcp.tool()
async def get_test_status(test_id: int):
    client = await get_testio_client()  # Still uses getter
    # ...
```

**Pros:**
- Minimal code changes (keep getters, change implementation)
- Uses FastMCP infrastructure

**Cons:**
- Still anti-pattern (FastMCP docs recommend parameter injection)
- Runtime dependency resolution (harder to test, less explicit)
- Hides dependencies (same problem as current approach)
- Not conventional FastMCP pattern

**Decision:** Rejected. Parameter injection is clearer, more testable, and conventional.

---

### Alternative 3: Hybrid - Getters Call get_context() (Rejected)

Combine custom getters with FastMCP's `get_context()`:

```python
async def get_testio_client() -> TestIOClient:
    """Wrapper over FastMCP context."""
    ctx = get_context()
    return ctx["testio_client"]

@mcp.tool()
async def get_test_status(test_id: int):
    client = await get_testio_client()  # Custom getter
    # ...
```

**Pros:**
- Minimal code changes in tools
- Uses FastMCP context internally

**Cons:**
- Adds unnecessary indirection layer
- Still hides dependencies from function signature
- Not conventional FastMCP pattern
- Defeats purpose of explicit dependency injection

**Decision:** Rejected. Goes against FastMCP's explicit dependency injection philosophy.

---

## Implementation Plan

### Phase 1: Add Lifespan (Backward Compatible)

Add lifespan handler while keeping custom getters:

```python
@asynccontextmanager
async def lifespan(app: FastMCP):
    async with TestIOClient(...) as client:
        cache = PersistentCache(db_path="~/.testio-mcp/cache.db", customer_id=1)
        await cache.initialize()
        app.context["testio_client"] = client
        app.context["cache"] = cache
        yield

mcp = FastMCP("TestIO MCP Server", lifespan=lifespan)

# Keep existing getters temporarily (still work)
async def get_testio_client():
    # ... unchanged
```

**Result:** Server runs, tools still use getters (backward compatible).

---

### Phase 2: Update Tools (Parallel Operation)

Add Context parameter while getters still exist:

```python
@mcp.tool()
async def get_test_status(test_id: int, ctx: Context):
    client = ctx["testio_client"]  # Use context
    # ... rest unchanged
```

**Result:** Tools use Context, getters exist but unused (still works).

---

### Phase 3: Remove Getters (Clean Architecture)

Delete custom getters and global state:

```python
# DELETE these
# async def get_testio_client(): ...
# async def get_cache(): ...
# _testio_client: TestIOClient | None = None
# _cache: PersistentCache | None = None
```

**Result:** Clean architecture, Context-only pattern.

---

## Future Considerations

### HTTP Multi-Tenancy (Future ADR)

This migration prepares infrastructure for per-request authentication:

```python
# Future: Per-request client creation
@asynccontextmanager
async def http_lifespan(app: FastMCP):
    """HTTP mode: Create client pool for multi-tenancy."""
    client_pool = ClientPool(max_clients=100)
    cache = PersistentCache(db_path="~/.testio-mcp/cache.db", customer_id=1)
    await cache.initialize()

    app.context["client_pool"] = client_pool
    app.context["cache"] = cache

    yield

    await client_pool.cleanup()

@mcp.tool()
async def get_test_status(
    test_id: int,
    api_token: str,  # Per-request authentication
    ctx: Context
):
    client_pool = ctx["client_pool"]
    client = await client_pool.get_client(api_token)
    service = TestService(client=client, cache=cache)
    # ...
```

**Tenant-Scoped Cache Keys:**
```python
tenant_id = hashlib.sha256(api_token.encode()).hexdigest()[:16]
cache_key = f"tenant:{tenant_id}:product:{product_id}:tests:running"
```

### FastMCP Advanced Patterns

**get_context() for Nested Functions:**

For deeply nested code where parameter injection is impractical:

```python
from fastmcp.server.dependencies import get_context

async def helper_function_deeply_nested():
    """Access context without parameter injection."""
    ctx = get_context()  # Runtime dependency resolution
    client = ctx["testio_client"]
    # ...
```

**Use sparingly:** Prefer parameter injection for clarity and testability.

---

## References

### FastMCP Documentation
- [Context - FastMCP](https://gofastmcp.com/servers/context)
- [Tools - FastMCP](https://gofastmcp.com/servers/tools)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)

### Industry Best Practices
- [Building Scalable MCP Servers with DDD](https://medium.com/@chris.p.hughes10/building-scalable-mcp-servers-with-domain-driven-design-fb9454d4c726)
- [MCP Best Practices](https://modelcontextprotocol.info/docs/best-practices/)
- [Building Production-Ready MCP Servers](https://thinhdanggroup.github.io/mcp-production-ready/)

### Project Documentation
- ADR-001: API Client Dependency Injection
- ADR-006: Service Layer Pattern
- STORY-003c: Migrate to FastMCP Context Injection (implementation story)
- `docs/architecture/FASTMCP_ARCHITECTURE_EVALUATION.md` (architectural review)

---

## Approval

- **Proposed by:** Winston (System Architect)
- **Date:** 2025-11-05
- **Status:** Accepted
- **Implementation Story:** STORY-003c

---

## Summary

Migrating from custom getter functions to FastMCP Context injection provides:
- ✅ Alignment with official FastMCP patterns
- ✅ Elimination of global state
- ✅ Automatic lifecycle management
- ✅ Improved testability
- ✅ Foundation for HTTP multi-tenancy

The migration is low-risk (backward compatible during transition), low-effort (3 hours), and high-value (prevents technical debt, enables future features).

**Recommendation:** Implement STORY-003c before continuing with Stories 004+.
