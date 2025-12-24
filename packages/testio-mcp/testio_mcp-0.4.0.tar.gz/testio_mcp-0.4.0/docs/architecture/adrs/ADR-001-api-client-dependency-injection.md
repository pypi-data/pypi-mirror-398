# ADR-001: API Client Dependency Injection Pattern

**Status:** Accepted

**Date:** 2025-11-04

**Context:** API Client Lifecycle and Testing Strategy

---

## Context

The TestIO MCP server needs an HTTP client to communicate with the TestIO Customer API. We need to decide:

1. How to manage the HTTP client lifecycle (creation, reuse, cleanup)
2. How to make the client available to MCP tools
3. How to ensure the design is testable and follows Python async best practices

### Initial Design Consideration

The initial story implementation suggested creating a new `httpx.AsyncClient` for each request:

```python
async def get(self, endpoint: str, **kwargs) -> dict:
    async with httpx.AsyncClient() as client:  # New client per request
        response = await client.get(...)
        return response.json()
```

**Problems with this approach:**
- No connection pooling → higher latency (50-200ms overhead per request)
- Resource inefficiency (opening/closing TCP connections repeatedly)
- Difficult to configure client behavior globally (timeouts, retries, headers)
- Doesn't leverage httpx's built-in connection pool

### Alternative Patterns Considered

1. **Singleton Pattern**
   - Single global `httpx.AsyncClient` instance
   - **Pros:** Simple, connection pooling works
   - **Cons:** Global state, hard to test, lifecycle management unclear, not thread-safe in some contexts

2. **App-Level Instance**
   - Create client at app startup, store in FastMCP server context
   - **Pros:** Connection pooling, clear lifecycle
   - **Cons:** Tightly coupled to FastMCP server initialization

3. **Dependency Injection (via FastMCP context)**
   - Pass client instance to tools via FastMCP's dependency injection system
   - **Pros:** Clean, testable, follows FastAPI patterns, explicit dependencies
   - **Cons:** Slightly more setup code

4. **Connection Pool Manager**
   - Custom manager class wrapping httpx.Client
   - **Pros:** Full control over pooling behavior
   - **Cons:** Reinventing httpx's wheel

---

## Decision

**Use dependency injection via FastMCP context to provide the `TestIOClient` instance to MCP tools.**

The `TestIOClient` will:
- Wrap an `httpx.AsyncClient` instance with connection pooling
- Be created during FastMCP server startup (lifespan event)
- Be passed to tools via FastMCP's dependency injection mechanism
- Be properly closed during server shutdown

---

## Implementation

### 1. TestIOClient Wrapper

```python
# src/testio_mcp/client.py

import asyncio
import httpx
from typing import Any, Dict, Optional


class TestIOClient:
    """HTTP client wrapper for TestIO Customer API with connection pooling and concurrency control."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        max_concurrent_requests: int = 10,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 30.0,
    ):
        """
        Initialize TestIO API client.

        Args:
            base_url: Base URL for TestIO Customer API
            api_token: Authentication token
            max_concurrent_requests: Maximum concurrent API requests (semaphore limit, see ADR-002)
            max_connections: Maximum number of concurrent connections
            max_keepalive_connections: Maximum number of idle connections to maintain
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._config = {
            "base_url": base_url,
            "headers": {"Authorization": f"Token {api_token}"},
            "timeout": httpx.Timeout(timeout),
            "limits": httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            ),
        }

    async def __aenter__(self) -> "TestIOClient":
        """Create the HTTP client on context enter."""
        self._client = httpx.AsyncClient(**self._config)
        return self

    async def __aexit__(self, *args) -> None:
        """Clean up the HTTP client on context exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make GET request to TestIO API with concurrency control.

        Args:
            endpoint: API endpoint (e.g., "products" or "exploratory_tests/123")
            **kwargs: Additional arguments for httpx.get()

        Returns:
            JSON response as dictionary

        Raises:
            RuntimeError: If client not initialized (use 'async with' context manager)
            httpx.HTTPStatusError: If response status is 4xx or 5xx
        """
        if not self._client:
            raise RuntimeError(
                "TestIOClient not initialized. Use 'async with TestIOClient(...) as client:'"
            )

        # Acquire semaphore slot before making request (ADR-002)
        async with self._semaphore:
            response = await self._client.get(endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
```

### 2. FastMCP Server Initialization

```python
# src/testio_mcp/server.py

from contextlib import asynccontextmanager
from fastmcp import FastMCP
from .client import TestIOClient
from .config import settings


# Lifespan context manager for client lifecycle
@asynccontextmanager
async def lifespan(server: FastMCP):
    """Manage TestIO client lifecycle during server startup/shutdown."""
    # Startup: Create client
    async with TestIOClient(
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
    ) as client:
        # Store client in server context for dependency injection
        server.context["testio_client"] = client

        # Server runs here
        yield

        # Shutdown: Client is automatically closed by __aexit__


# Create FastMCP server with lifespan
mcp = FastMCP("TestIO MCP Server", lifespan=lifespan)
```

### 3. Tool Implementation with Dependency Injection

**Updated (2025-11-04):** Tools now delegate to service layer (see ADR-006).

```python
# src/testio_mcp/tools/get_test_status.py

from fastmcp import Context
from ..services.test_service import TestService
from ..exceptions import TestNotFoundException


@mcp.tool()
async def get_test_status(test_id: str, ctx: Context) -> dict:
    """
    Get comprehensive status of a single exploratory test.

    Args:
        test_id: Exploratory test ID
        ctx: FastMCP context (injected automatically)

    Returns:
        Structured test status information
    """
    # Extract dependencies from context (dependency injection)
    client = ctx["testio_client"]
    cache = ctx["cache"]

    # Create service instance (delegates business logic)
    service = TestService(client=client, cache=cache)

    # Delegate to service
    try:
        return await service.get_test_status(test_id)
    except TestNotFoundException:
        # Convert service exception to MCP error format
        return {
            "error": f"❌ Test ID '{test_id}' not found",
            "context": "ℹ️ The test may have been deleted or you may not have access",
            "hint": "💡 Use list_active_tests to see available tests"
        }
```

**Pattern explanation:**
1. **Extract dependencies** from FastMCP Context (client, cache)
2. **Create service** instance with dependencies
3. **Delegate** business logic to service
4. **Convert errors** from domain exceptions to MCP format

This pattern separates transport-specific concerns (MCP protocol) from business logic (service layer).

### 4. Testing with Dependency Injection

**Preferred: Test services directly (see ADR-006)**

```python
# tests/services/test_test_service.py

import pytest
from unittest.mock import AsyncMock
from src.testio_mcp.services.test_service import TestService


@pytest.mark.asyncio
async def test_get_test_status():
    """Test TestService.get_test_status with mocked dependencies."""
    # Create mock dependencies
    mock_client = AsyncMock()
    mock_cache = AsyncMock()

    # Setup mock responses
    mock_client.get.side_effect = [
        {"id": "123", "title": "Test", "status": "running"},
        {"bugs": [], "meta": {"record_count": 0}}
    ]
    mock_cache.get.return_value = None  # Cache miss

    # Create service
    service = TestService(client=mock_client, cache=mock_cache)

    # Test business logic
    result = await service.get_test_status(test_id="123")

    # Verify behavior
    assert mock_client.get.call_count == 2
    assert result["test"]["id"] == "123"
    mock_cache.set.assert_called_once()  # Verify caching
```

**Alternative: Test MCP tools (integration test)**

```python
# tests/integration/test_get_test_status_tool.py

import pytest
from fastmcp import Context
from src.testio_mcp.tools import get_test_status


@pytest.mark.asyncio
async def test_get_test_status_tool():
    """Integration test: Tool + Service + Mock Client."""
    mock_client = AsyncMock()
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None

    ctx = Context({"testio_client": mock_client, "cache": mock_cache})
    result = await get_test_status(test_id="123", ctx=ctx)

    # Tool delegates to service, service calls client
    assert mock_client.get.call_count == 2
```

**Testing strategy:**
- **Prefer testing services** (faster, no FastMCP overhead)
- **Test tools for error conversion** (domain exception → MCP format)
- **Integration tests** verify full flow (tool → service → client)

---

## Consequences

### Positive

1. **Connection Pooling**
   - httpx reuses TCP connections across requests
   - Reduces latency by 50-200ms per request
   - Better resource utilization

2. **Testability**
   - Easy to inject mock clients for testing
   - No global state to manage
   - Clear dependency boundaries

3. **Lifecycle Management**
   - Client created on server startup
   - Properly cleaned up on server shutdown
   - No resource leaks

4. **Configuration Centralization**
   - Timeouts, headers, connection limits configured once
   - Consistent behavior across all API calls
   - Easy to adjust for different environments (dev, staging, prod)

5. **Follows Framework Patterns**
   - FastMCP's context is designed for this pattern
   - Similar to FastAPI's dependency injection
   - Familiar to Python web developers

### Negative

1. **Slightly More Setup Code**
   - Requires lifespan context manager
   - Tools must accept `ctx: Context` parameter
   - Slightly more boilerplate than global client

2. **Learning Curve**
   - Developers must understand FastMCP's context system
   - Requires familiarity with async context managers

### Neutral

1. **No Multi-Tenancy Support (Yet)**
   - Single client instance shared across all requests
   - If multi-tenancy needed in future, will need per-user clients
   - Acceptable for MVP (single-tenant use case)

---

## Related Decisions

- **ADR-002: Concurrency Limits** - Connection pool size affects concurrent request handling
- **ADR-006: Service Layer Pattern** - Services receive client via same DI pattern
- **Story 1: Project Setup** - Implementation details for client initialization
- **Story 8: Error Handling** - Client-level error handling and retries

---

## References

- [httpx Connection Pooling Docs](https://www.python-httpx.org/advanced/#connection-pooling)
- [FastMCP Dependency Injection](https://github.com/jlowin/fastmcp#dependency-injection)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/) (similar pattern)

---

## Notes

- Connection pool limits (max_connections=100, max_keepalive_connections=20) are configurable and can be tuned based on observed API behavior
- TestIO API rate limits are unknown, so we start conservatively and make limits configurable
- Client is thread-safe due to httpx's internal locking mechanisms
