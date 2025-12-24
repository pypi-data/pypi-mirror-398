# ADR-002: Concurrency Limits via Global Semaphore

**Status:** Accepted

**Date:** 2025-11-04

**Context:** Protecting TestIO API from overwhelming concurrent requests

---

## Context

The TestIO MCP server makes multiple concurrent API requests when:
- Generating status reports for multiple tests (Story 5: up to 20 concurrent fetches)
- Querying test activity across products (Story 6: up to 50+ concurrent fetches)
- Refreshing the `tests://active` resource (Story 7: potentially 225 concurrent fetches for all products)

### Problem

**TestIO API rate limits are unknown.** We have no documentation on:
- Maximum requests per second
- Maximum concurrent connections
- Rate limiting policies (429 responses, backoff requirements)

Without limits, the MCP server could:
1. **Overwhelm the TestIO API** → Service degradation or blocking
2. **Exhaust local resources** → Memory/file descriptor limits
3. **Create poor user experience** → Slow queries due to resource contention

### Alternative Approaches Considered

1. **No Limits (YOLO Mode)**
   - Let users send as many concurrent requests as they want
   - **Pros:** Maximum throughput, simpler code
   - **Cons:** High risk of API abuse, resource exhaustion, poor experience

2. **Per-Tool Limits**
   - Each tool has its own semaphore (e.g., `generate_status_report` max 10, `get_test_activity` max 20)
   - **Pros:** Fine-grained control, tool-specific optimization
   - **Cons:** Complex to configure, limits can interact poorly (user could spawn multiple tools)

3. **Rate Limiting (Token Bucket/Sliding Window)**
   - Track requests per second, enforce rate limit
   - **Pros:** More sophisticated, matches typical API rate limits
   - **Cons:** Requires knowing actual API limits, more complex implementation

4. **Global Semaphore with Configurable Limit**
   - Single semaphore controlling all API requests across all tools
   - **Pros:** Simple, prevents runaway queries, easy to configure
   - **Cons:** May be too conservative for some workloads

---

## Decision

**Use a global `asyncio.Semaphore` to limit concurrent API requests to a configurable maximum (default: 10).**

The semaphore will:
- Apply to all TestIO API requests (GET, POST, PUT, etc.)
- Be shared across all MCP tools
- Be configurable via environment variable (`MAX_CONCURRENT_API_REQUESTS`)
- Default to 10 concurrent requests (conservative starting point)

---

## Implementation

### 1. Configuration

```python
# src/testio_mcp/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    TESTIO_CUSTOMER_API_BASE_URL: str
    TESTIO_CUSTOMER_API_TOKEN: str

    # Concurrency Settings
    MAX_CONCURRENT_API_REQUESTS: int = 10  # Default: 10 concurrent requests

    class Config:
        env_file = ".env"


settings = Settings()
```

### 2. Semaphore in TestIOClient (Dependency Injection Pattern)

**Architecture Pattern**: The client uses **dependency injection** for semaphore sharing.

**Why Dependency Injection?**
- **Production**: Server creates shared semaphore and injects into all client instances (global concurrency control)
- **Testing**: Tests can pass isolated semaphores or None for independent test execution (no test pollution)
- **Flexibility**: Easy to add per-user semaphores in Phase 3 multi-tenant without changing client code

```python
# src/testio_mcp/client.py

import asyncio
import httpx
from typing import Any, Dict, Optional


class TestIOClient:
    """HTTP client wrapper for TestIO Customer API with concurrency control."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        max_concurrent_requests: int = 10,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 30.0,
        semaphore: asyncio.Semaphore | None = None,  # Dependency injection
    ):
        """
        Initialize TestIO API client with concurrency limits.

        Args:
            base_url: Base URL for TestIO Customer API
            api_token: Authentication token
            max_concurrent_requests: Max concurrent requests (used if no semaphore)
            max_connections: Maximum number of HTTP connections in pool
            max_keepalive_connections: Maximum number of idle connections
            timeout: Request timeout in seconds
            semaphore: Optional shared semaphore for global concurrency control (ADR-002).
                      If not provided, creates a new semaphore with max_concurrent_requests limit.
                      For production: server should pass a shared semaphore.
                      For tests: pass None to get isolated semaphores per client.
        """
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None

        # Dependency injection: use provided semaphore or create new one (ADR-002)
        # Production: server passes shared semaphore for global limiting
        # Tests: each client gets its own semaphore (no test pollution)
        self._semaphore = semaphore or asyncio.Semaphore(max_concurrent_requests)

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

        The semaphore ensures that at most MAX_CONCURRENT_API_REQUESTS
        are in-flight at any given time. Additional requests will wait
        until a slot becomes available.

        Args:
            endpoint: API endpoint (e.g., "products" or "exploratory_tests/123")
            **kwargs: Additional arguments for httpx.get()

        Returns:
            JSON response as dictionary

        Raises:
            RuntimeError: If client not initialized
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

### 3. Server Initialization with Dependency Injection

**Pattern**: Server creates shared semaphore and injects it into client instances.

```python
# src/testio_mcp/server.py

import asyncio
from fastmcp import FastMCP
from .client import TestIOClient
from .config import settings


# Shared resources (ADR-002: global concurrency control)
_testio_client: TestIOClient | None = None
_global_semaphore: asyncio.Semaphore | None = None


def get_global_semaphore() -> asyncio.Semaphore:
    """Get or create the shared semaphore for global concurrency control (ADR-002).

    This semaphore is shared across all TestIOClient instances to enforce
    a global limit on concurrent API requests. This prevents overwhelming
    the TestIO API.

    For Story 1 (single client): provides concurrency control.
    For future stories (multiple products): ensures total concurrent requests
    across all products stays within limit.

    Returns:
        Shared semaphore instance with max_concurrent_requests limit
    """
    global _global_semaphore

    if _global_semaphore is None:
        _global_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_API_REQUESTS)
        logger.info(f"Created global semaphore with limit: {settings.MAX_CONCURRENT_API_REQUESTS}")

    return _global_semaphore


async def get_testio_client() -> TestIOClient:
    """Get or create the shared TestIO API client.

    Returns:
        Shared TestIOClient instance

    Note:
        For stdio servers, we use a module-level client that's created
        on first use and reused across all requests.
    """
    global _testio_client

    if _testio_client is None:
        logger.info("Initializing TestIO API client")

        # Get shared semaphore for global concurrency control (ADR-002)
        shared_semaphore = get_global_semaphore()

        _testio_client = TestIOClient(
            base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
            api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
            max_concurrent_requests=settings.MAX_CONCURRENT_API_REQUESTS,
            max_connections=settings.CONNECTION_POOL_SIZE,
            max_keepalive_connections=settings.CONNECTION_POOL_MAX_KEEPALIVE,
            timeout=settings.HTTP_TIMEOUT_SECONDS,
            semaphore=shared_semaphore,  # Inject shared semaphore
        )
        await _testio_client.__aenter__()
        logger.info("TestIO API client initialized successfully")

    return _testio_client


mcp = FastMCP("TestIO MCP Server")
```

### 4. Usage in Tools (No Changes Required)

Tools use the client normally - semaphore is transparent:

```python
@mcp.tool()
async def generate_status_report(test_ids: list[str], ctx: Context) -> dict:
    """Generate status report for multiple tests."""
    testio_client: TestIOClient = ctx["testio_client"]

    # Even though we're fetching 20 tests concurrently,
    # the semaphore ensures only 10 requests are in-flight at once
    results = await asyncio.gather(
        *[get_test_status_helper(tid, testio_client) for tid in test_ids],
        return_exceptions=True
    )

    # ... process results
```

### 5. Environment Configuration

```bash
# .env

# TestIO API Configuration
TESTIO_CUSTOMER_API_BASE_URL=https://api.test.io/customer/v2
TESTIO_CUSTOMER_API_TOKEN=your_token_here

# Concurrency Settings
MAX_CONCURRENT_API_REQUESTS=10  # Start conservative, increase if needed
```

---

## Consequences

### Positive

1. **API Protection**
   - Prevents overwhelming TestIO API with too many concurrent requests
   - Graceful queueing when demand exceeds capacity
   - Reduces risk of 429 rate limit errors

2. **Resource Management**
   - Prevents local resource exhaustion (memory, file descriptors)
   - Predictable resource usage (max N requests in-flight)
   - Better server stability

3. **Configurability**
   - Easy to tune based on observed API behavior
   - Can increase limit if TestIO API proves more robust
   - Environment-specific configuration (dev vs prod)

4. **Transparency**
   - Tools don't need to know about semaphore
   - No changes to tool implementation
   - Centralized control point

5. **User Experience**
   - Prevents "all or nothing" request patterns
   - Progressive loading (first 10 requests complete, then next 10, etc.)
   - Reduces likelihood of total query failure

### Negative

1. **Potential Throughput Reduction**
   - If TestIO API can handle >10 concurrent requests, we're leaving performance on the table
   - May increase query time for large batch operations
   - Users with high-performance needs may need to increase limit

2. **No Fine-Grained Control**
   - All tools share same limit (no per-tool prioritization)
   - High-priority queries can be blocked by low-priority queries
   - No way to express "this query is more important"

3. **Not Rate Limiting**
   - Semaphore controls concurrency, not requests-per-second
   - If API has rate limit (e.g., 100 req/sec), semaphore won't prevent bursts
   - May need to add rate limiting in future

### Neutral

1. **Starting Conservative**
   - Default of 10 is intentionally low
   - Can increase based on monitoring/feedback
   - Better to start safe and scale up than vice versa

2. **Future Extensibility**
   - Can layer rate limiting on top of semaphore
   - Can add per-tool semaphores if needed
   - Can add priority queuing if needed

---

## Monitoring Recommendations

To determine if the semaphore limit should be adjusted, monitor:

1. **Semaphore Wait Time**
   - How long requests wait to acquire semaphore slot
   - If high (>100ms), consider increasing limit

2. **API Error Rates**
   - Track 429 (rate limit) responses
   - If high, decrease limit or add backoff

3. **Query Latency**
   - P50, P95, P99 latency for tools
   - If increasing, may be hitting API limits

4. **Concurrent Request Metrics**
   - Track actual concurrent requests vs limit
   - If consistently maxed out, increase limit

**Example Metrics to Add** (Story 8: Error Handling):

```python
import time
from contextlib import asynccontextmanager


class MetricsClient(TestIOClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.semaphore_wait_times = []
        self.concurrent_requests = 0

    async def get(self, endpoint: str, **kwargs):
        # Measure semaphore wait time
        start = time.time()
        async with self._semaphore:
            wait_time = time.time() - start
            self.semaphore_wait_times.append(wait_time)

            self.concurrent_requests += 1
            try:
                result = await super().get(endpoint, **kwargs)
                return result
            finally:
                self.concurrent_requests -= 1
```

---

## Tuning Guidelines

### When to Increase Limit

Increase `MAX_CONCURRENT_API_REQUESTS` if:
- Semaphore wait times consistently >100ms
- No 429 errors observed
- Query latency is high but API response times are fast
- You have confirmation from TestIO that API can handle more load

**Suggested increments:** 10 → 20 → 50 → 100

### When to Decrease Limit

Decrease `MAX_CONCURRENT_API_REQUESTS` if:
- Seeing 429 rate limit errors
- API response times degrading under load
- TestIO reports abuse/excessive usage
- Local resource issues (memory, file descriptors)

**Suggested decrements:** 10 → 5 → 3 → 1

### Environment-Specific Settings

```bash
# Development: Higher limit for faster iteration
MAX_CONCURRENT_API_REQUESTS=20

# Staging: Match production
MAX_CONCURRENT_API_REQUESTS=10

# Production: Conservative
MAX_CONCURRENT_API_REQUESTS=10

# CI/CD: Very low to avoid overwhelming test APIs
MAX_CONCURRENT_API_REQUESTS=3
```

---

## Related Decisions

- **ADR-001: API Client Dependency Injection** - Semaphore is part of client lifecycle
- **ADR-005: Response Size Limits** - Complements concurrency limits
- **Story 5: Generate Status Report** - Benefits most from semaphore (20 concurrent fetches → 10)
- **Story 6: Test Activity Timeframe** - Prevents 225 concurrent requests to API
- **Story 7: MCP Resources** - Prevents `tests://active` from overwhelming API

---

## References

- [Python asyncio.Semaphore](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Semaphore)
- [httpx Connection Limits](https://www.python-httpx.org/advanced/#pool-limit-configuration)
- [API Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)

---

## Open Questions

1. **What are TestIO's actual rate limits?**
   - Action: Test with increasing concurrency, monitor for 429 errors
   - Update limit based on findings

2. **Should we add request-per-second rate limiting?**
   - Current: Only concurrency control
   - Future: May need token bucket algorithm if API has RPS limits
   - Defer until we observe 429 errors

3. **Should we add per-user rate limiting?**
   - Current: Single-tenant MVP (no per-user limits)
   - Future: If multi-tenant, add per-user semaphores
   - Not needed for MVP
