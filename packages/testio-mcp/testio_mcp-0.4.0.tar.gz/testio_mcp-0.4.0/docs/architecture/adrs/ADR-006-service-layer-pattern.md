# ADR-006: Service Layer Pattern

**Status:** ✅ Active

**Date:** 2025-11-04

**Updated:** 2025-11-20 (Code examples updated for PersistentCache)

**Context:** Separation of Business Logic from Transport Mechanisms

**Note:** Code examples in this ADR originally used `InMemoryCache` (v0.1.x). The service layer pattern remains valid with `PersistentCache` (v0.2.0+) - simply replace `InMemoryCache` with `PersistentCache` and add repository pattern for data access.

---

## Context

The TestIO MCP server needs to make architectural decisions about where business logic lives. We face a critical fork in the road:

1. **Current trajectory:** Embed business logic directly in MCP tools
2. **Alternative:** Extract business logic into a service layer

This decision is being made **before implementation begins** (ground zero), making the incremental cost minimal (2-3 hours of documentation) compared to refactoring later (6-8 days of rework).

### The Future Flexibility Question

During architecture review, a key question emerged:

> "Does our architecture fit well for a future where we may want to expose tools not within the MCP server context but as standalone REST endpoints?"

**Current architecture analysis:**
- ✅ **Infrastructure layer** (TestIOClient, PersistentCache, Repositories) is fully framework-agnostic
- ✅ **Data models** (Pydantic) are portable across transports
- ⚠️ **Business logic** would be embedded in MCP tools (tight coupling to FastMCP)
- ⚠️ **Dependency injection** is FastMCP Context-based (not reusable)

### Research Findings

Research into Python service layer patterns revealed consistent recommendations:

**From "Cosmic Python" (Architecture Patterns with Python):**
- Service layer sits between presentation and domain model
- Encapsulates use cases and orchestration logic
- Enables fast unit tests without framework overhead
- "Web stuff" stays in controllers; business logic stays in services

**From FastAPI Community Best Practices:**
- Layered architecture: Controller → Service → Repository
- Dependency injection chains span multiple layers
- Services are stateless, created per-request with dependencies
- Testing improved by mocking only at repository layer

**From Hexagonal Architecture (Ports and Adapters):**
- Ports define contracts (interfaces)
- Adapters implement transport-specific logic (MCP, REST, CLI)
- Core business logic remains in the center (domain + services)
- Enables multi-transport architectures

### Why This Matters for TestIO MCP

**MVP Scope:** MCP-only, single-tenant, read-only operations

**Future Scenarios:**
1. **REST API for web dashboard** - Same business logic, different transport
2. **CLI tool for automation** - Same queries, different interface
3. **Webhook handlers** - Process TestIO events, reuse service logic
4. **Background jobs** - Report generation, data sync
5. **Multi-tenant SaaS** - Different authentication, same business rules

Without a service layer, each scenario requires duplicating or untangling business logic from MCP-specific code.

---

## Decision

**Implement a service layer that separates business logic from transport mechanisms.**

### Architecture Pattern

```
┌─────────────────────────┐
│   Transport Layer       │  ← MCP Tools (thin wrappers)
│   - Extract deps        │  ← Future: REST endpoints, CLI
│   - Handle protocol    │  ← Future: Webhooks, jobs
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│   Service Layer         │  ← Business logic (NEW)
│   - Domain operations   │
│   - Orchestration       │
│   - Caching decisions   │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│   Infrastructure        │  ← Framework-agnostic
│   - TestIOClient        │
│   - PersistentCache     │
│   - Repositories        │
└─────────────────────────┘
```

### Service Boundaries

**One service per domain area:**

1. **TestService** - Test status, test listing, test lifecycle
2. **BugService** - Bug retrieval, filtering, aggregation
3. **ActivityService** - Activity tracking, timeframe analysis
4. **ReportService** - Multi-test reports, status summaries

**Why domain-based (not tool-based)?**
- Services may be reused by multiple tools
- Domain logic naturally groups together
- Easier to test complete domains
- Aligns with potential future feature organization

---

## Implementation

### 1. Service Class Structure

Services are **stateless classes** that receive dependencies in the constructor:

```python
# src/testio_mcp/services/test_service.py

from typing import Optional
from ..client import TestIOClient
from ..repositories import TestRepository, BugRepository


class TestService:
    """Service for test-related operations.

    This service encapsulates business logic for querying, filtering,
    and aggregating test data. It is framework-agnostic and can be
    used from MCP tools, REST endpoints, CLI, or background jobs.
    """

    def __init__(self, client: TestIOClient, test_repo: TestRepository, bug_repo: BugRepository):
        """Initialize test service with dependencies.

        Args:
            client: HTTP client for TestIO Customer API
            test_repo: Repository for test data access
            bug_repo: Repository for bug data access
        """
        self.client = client
        self.cache = cache

    async def get_test_status(self, test_id: str) -> dict:
        """Get comprehensive test status with bug summary.

        This method orchestrates multiple API calls, applies caching,
        and aggregates data into a unified response.

        Args:
            test_id: Exploratory test ID

        Returns:
            Comprehensive test status with bug summary

        Raises:
            ValueError: If test_id is invalid
            TestNotFoundException: If test not found (404)
            TestIOAPIError: If API call fails
        """
        # Check cache first
        cache_key = f"test:{test_id}:status"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Fetch test details and bugs concurrently
        import asyncio
        test_data, bugs_data = await asyncio.gather(
            self.client.get(f"exploratory_tests/{test_id}"),
            self.client.get(f"bugs?filter_test_cycle_ids={test_id}")
        )

        # Aggregate bug summary
        bug_summary = self._aggregate_bug_summary(bugs_data.get("bugs", []))

        # Build response
        result = {
            "test": {
                "id": test_data["id"],
                "title": test_data["title"],
                "status": test_data["status"],
                "review_status": test_data.get("review_status"),
                "testing_type": test_data.get("testing_type"),
                "start_date": test_data.get("start_date"),
                "end_date": test_data.get("end_date"),
            },
            "bugs": bug_summary,
            "cached": False
        }

        # Cache result (5 min TTL for test status)
        await self.cache.set(cache_key, result, ttl_seconds=300)

        return result

    def _aggregate_bug_summary(self, bugs: list) -> dict:
        """Private helper: Aggregate bug statistics.

        Args:
            bugs: List of bug dictionaries from API

        Returns:
            Bug summary with counts by severity and status
        """
        summary = {
            "total_count": len(bugs),
            "by_severity": {"critical": 0, "high": 0, "low": 0},
            "by_status": {"accepted": 0, "rejected": 0, "new": 0},
            "recent_bugs": []
        }

        for bug in bugs:
            severity = bug.get("severity", "").lower()
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1

            status = bug.get("status", "").lower()
            if status in summary["by_status"]:
                summary["by_status"][status] += 1

        # Get 3 most recent bugs
        sorted_bugs = sorted(bugs, key=lambda b: b.get("created_at", ""), reverse=True)
        summary["recent_bugs"] = [
            {
                "id": bug["id"],
                "title": bug["title"],
                "severity": bug["severity"]
            }
            for bug in sorted_bugs[:3]
        ]

        return summary
```

### 2. MCP Tool as Thin Wrapper

MCP tools become **thin adapters** that delegate to services:

```python
# src/testio_mcp/tools/get_test_status.py

from fastmcp import Context
from ..services.test_service import TestService
from ..exceptions import TestNotFoundException, TestIOAPIError


@mcp.tool()
async def get_test_status(test_id: str, ctx: Context) -> dict:
    """Get comprehensive status of a single exploratory test.

    Returns test configuration, bug summary, current status, review
    information, and timeline data for the specified test.

    Args:
        test_id: The exploratory test ID (e.g., "109363")
        ctx: FastMCP context (injected automatically)

    Returns:
        Dictionary with test details and bug summary
    """
    # Extract dependencies from FastMCP context
    client = ctx["testio_client"]
    cache = ctx["cache"]

    # Create service instance (stateless, created per-request)
    service = TestService(client=client, cache=cache)

    # Delegate to service
    try:
        return await service.get_test_status(test_id)
    except TestNotFoundException:
        # Convert to MCP-friendly error format
        return {
            "error": f"❌ Test ID '{test_id}' not found",
            "context": "ℹ️ The test may have been deleted or you may not have access",
            "hint": "💡 Use list_active_tests to see available tests"
        }
    except TestIOAPIError as e:
        return {
            "error": f"❌ API error: {e.message}",
            "context": f"ℹ️ Status code: {e.status_code}",
            "hint": "💡 Check your API token and try again"
        }
```

**What tools should do:**
- Extract dependencies from context (MCP-specific)
- Create service instance
- Delegate to service method
- Convert service exceptions to MCP error format (❌ℹ️💡)
- Handle transport-level concerns (logging, metrics)

**What tools should NOT do:**
- Business logic (filtering, aggregation, classification)
- Caching decisions (service's responsibility)
- Direct API calls (use service)
- Complex orchestration (service's responsibility)

### 3. Service with Complex Logic (Pagination Example)

```python
# src/testio_mcp/services/bug_service.py

from typing import Optional
from ..client import TestIOClient
from ..repositories import BugRepository
from ..pagination import encode_continuation_token, decode_continuation_token


class BugService:
    """Service for bug-related operations."""

    def __init__(self, client: TestIOClient, bug_repo: BugRepository):
        self.client = client
        self.bug_repo = bug_repo

    async def get_bugs(
        self,
        test_id: str,
        bug_type: str = "all",
        severity: str = "all",
        status: str = "all",
        page_size: int = 100,
        continuation_token: Optional[str] = None
    ) -> dict:
        """Get paginated bugs with filtering.

        Args:
            test_id: Test ID to filter bugs
            bug_type: Filter by bug type (functional, visual, content, all)
            severity: Filter by severity (low, high, critical, all)
            status: Filter by status (accepted, rejected, new, all)
            page_size: Items per page (1-1000)
            continuation_token: Token from previous page (optional)

        Returns:
            Paginated bug response with results and next token

        Raises:
            ValueError: If parameters invalid
        """
        # Validate page_size
        if not 1 <= page_size <= 1000:
            raise ValueError("page_size must be between 1 and 1000")

        # Decode continuation token or start from beginning
        start_index = 0
        if continuation_token:
            token_data = decode_continuation_token(continuation_token)
            start_index = token_data.get("start_index", 0)

        # Fetch all bugs for test (cached)
        cache_key = f"bugs:test:{test_id}:all"
        all_bugs = await self.cache.get(cache_key)

        if not all_bugs:
            response = await self.client.get(f"bugs?filter_test_cycle_ids={test_id}")
            all_bugs = response.get("bugs", [])
            await self.cache.set(cache_key, all_bugs, ttl_seconds=60)  # 1 min TTL

        # Apply filters
        filtered_bugs = self._filter_bugs(all_bugs, bug_type, severity, status)

        # Paginate
        end_index = start_index + page_size
        page_bugs = filtered_bugs[start_index:end_index]
        has_more = end_index < len(filtered_bugs)

        # Generate continuation token
        next_token = None
        if has_more:
            next_token = encode_continuation_token({
                "test_id": test_id,
                "start_index": end_index,
                "filters": {
                    "bug_type": bug_type,
                    "severity": severity,
                    "status": status
                }
            })

        return {
            "results": page_bugs,
            "total_count": len(filtered_bugs),
            "page_size": len(page_bugs),
            "has_more": has_more,
            "continuation_token": next_token
        }

    def _filter_bugs(
        self,
        bugs: list,
        bug_type: str,
        severity: str,
        status: str
    ) -> list:
        """Private helper: Filter bugs by criteria."""
        filtered = bugs

        if bug_type != "all":
            filtered = [b for b in filtered if b.get("bug_type") == bug_type]

        if severity != "all":
            filtered = [b for b in filtered if b.get("severity") == severity]

        if status != "all":
            filtered = [b for b in filtered if b.get("status") == status]

        return filtered
```

### 4. Testing Services (Without MCP Framework)

Services can be tested directly without FastMCP overhead:

```python
# tests/unit/services/test_test_service.py

import pytest
from unittest.mock import AsyncMock
from src.testio_mcp.services.test_service import TestService


@pytest.mark.asyncio
async def test_get_test_status_caches_result():
    """Test that service caches API responses."""
    # Create mock dependencies
    mock_client = AsyncMock()
    mock_cache = AsyncMock()

    # Setup mock responses
    mock_client.get.side_effect = [
        {"id": "123", "title": "Test", "status": "running"},  # test data
        {"bugs": [{"id": "1", "severity": "high"}]}  # bugs data
    ]
    mock_cache.get.return_value = None  # Cache miss

    # Create service
    service = TestService(client=mock_client, cache=mock_cache)

    # Call service method
    result = await service.get_test_status(test_id="123")

    # Verify API calls
    assert mock_client.get.call_count == 2
    assert mock_client.get.call_args_list[0][0][0] == "exploratory_tests/123"

    # Verify caching
    mock_cache.set.assert_called_once()
    cache_key = mock_cache.set.call_args[0][0]
    assert cache_key == "test:123:status"
    assert mock_cache.set.call_args[0][2] == 300  # 5 min TTL

    # Verify result structure
    assert result["test"]["id"] == "123"
    assert result["bugs"]["total_count"] == 1


@pytest.mark.asyncio
async def test_get_test_status_returns_cached_data():
    """Test that service returns cached data when available."""
    mock_client = AsyncMock()
    mock_cache = AsyncMock()

    # Setup cached response
    cached_data = {
        "test": {"id": "123", "title": "Cached Test"},
        "bugs": {"total_count": 5},
        "cached": True
    }
    mock_cache.get.return_value = cached_data

    service = TestService(client=mock_client, cache=mock_cache)
    result = await service.get_test_status(test_id="123")

    # Should return cached data without API calls
    assert mock_client.get.call_count == 0
    assert result == cached_data
```

**Testing benefits:**
- No FastMCP mocking required
- Fast tests (no framework initialization)
- Test business logic in isolation
- Easy to test edge cases and error paths

### 5. Future REST Endpoint (Documentation Only - NOT MVP)

This shows how the same service would be reused in a future REST API:

```python
# Future: src/testio_api/routers/tests.py (NOT IN MVP)

from fastapi import APIRouter, Depends, HTTPException
from src.testio_mcp.services.test_service import TestService
from .dependencies import get_test_service

router = APIRouter(prefix="/api/v1/tests", tags=["tests"])


@router.get("/{test_id}/status")
async def get_test_status(
    test_id: str,
    service: TestService = Depends(get_test_service)
):
    """REST endpoint: Get test status.

    Uses the same TestService as MCP tool, demonstrating
    business logic reuse across transports.
    """
    try:
        return await service.get_test_status(test_id)
    except TestNotFoundException:
        raise HTTPException(status_code=404, detail="Test not found")
    except TestIOAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


# Dependency provider for FastAPI
def get_test_service(
    client: TestIOClient = Depends(get_testio_client),
    test_repo: TestRepository = Depends(get_test_repository),
    bug_repo: BugRepository = Depends(get_bug_repository)
) -> TestService:
    """Dependency injection provider for TestService.

    FastAPI's Depends() works similarly to FastMCP's Context,
    allowing the same service pattern in both frameworks.
    """
    return TestService(client=client, cache=cache)
```

**Key insight:** Same `TestService` class, different dependency injection mechanism (FastAPI `Depends` vs FastMCP `Context`).

---

## Consequences

### Positive

1. **Future Flexibility** ✅
   - Business logic can be reused across MCP, REST, CLI, webhooks
   - No code duplication when adding new transports
   - Clean migration path to multi-transport architecture

2. **Testability** ✅
   - Services tested without FastMCP framework overhead
   - Unit tests are fast (<1ms per test)
   - Easy to mock dependencies (client, cache)
   - Clear separation of transport vs business logic testing

3. **Maintainability** ✅
   - Business logic changes don't affect transport layer
   - Single responsibility: tools handle protocol, services handle domain
   - Easier onboarding (clear layer boundaries)

4. **Parallel Development** ✅
   - Service interfaces can be defined early
   - Tools and services can be developed independently
   - Service developers don't need MCP expertise

5. **Better Error Handling** ✅
   - Services raise domain exceptions (TestNotFoundException)
   - Tools convert to transport format (MCP error, HTTP status, CLI message)
   - Separation of concerns for error contexts

### Negative

1. **More Files** ⚠️
   - Adds `src/testio_mcp/services/` directory
   - ~5 service files (test, bug, activity, report, base)
   - More navigation for developers

2. **Extra Indirection** ⚠️
   - Tool → Service → Client (3 hops instead of 2)
   - Slightly more code to read/trace
   - Learning curve for pattern

3. **Minimal Boilerplate** ⚠️
   - Each tool extracts deps and creates service
   - ~5 lines of boilerplate per tool
   - Could be abstracted with base class (future)

### Neutral

1. **No Performance Impact**
   - Service instantiation is negligible (<1μs)
   - Stateless services have no memory overhead
   - Async patterns remain unchanged

2. **No Change to Dependencies**
   - Still uses FastMCP Context for DI
   - Still uses TestIOClient and PersistentCache/Repositories
   - Infrastructure layer unchanged

3. **MVP Timeline Unaffected**
   - Documentation adds ~2 hours (this ADR)
   - Implementation is similar complexity
   - Testing may be slightly faster (no MCP mocking)

---

## Related Decisions

- **ADR-001: API Client Dependency Injection** - Services receive client via DI, same pattern as tools
- **ADR-004: Cache Strategy MVP** - Services make caching decisions, tools delegate
- **Story 2-7: Tool Implementation** - All tools will follow service delegation pattern

---

## Migration Path (If Needed)

If we need to undo this decision (unlikely), the migration is straightforward:

1. Move service methods into tool functions
2. Remove service classes
3. Tools call client directly
4. Update tests to use FastMCP test client

Estimated effort: 4-6 hours (simple mechanical refactoring).

---

## References

### Research Sources

1. **Cosmic Python (Architecture Patterns with Python)**
   - https://www.cosmicpython.com/book/chapter_04_service_layer.html
   - Service layer pattern, orchestration logic, testing benefits

2. **FastAPI Layered Architecture**
   - https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo
   - Controller → Service → Repository pattern
   - Dependency injection across layers

3. **FastAPI Dependency Injection + Service Layer**
   - https://blog.dotcs.me/posts/fastapi-dependency-injection-x-layers
   - Combining FastAPI Depends with service pattern
   - Testing with dependency overrides

4. **Hexagonal Architecture in Python**
   - https://medium.com/@miks.szymon/hexagonal-architecture-in-python-e16a8646f000
   - Ports and adapters pattern
   - Multi-transport architecture examples

5. **Clean Architecture with Python**
   - https://medium.com/@shaliamekh/clean-architecture-with-python-d62712fd8d4f
   - Separation of concerns
   - Layer dependencies and testing

### Industry Best Practices

- **Martin Fowler: Service Layer Pattern** - Encapsulate business logic, provide stable API
- **Robert C. Martin: Clean Architecture** - Dependency rule, framework independence
- **FastAPI Best Practices** - https://github.com/zhanymkanov/fastapi-best-practices

---

## Decision Log

**Date:** 2025-11-04
**Decided By:** Architect (Winston)
**Reviewed By:** Pending
**Status:** Approved for MVP implementation

**Key Insight:** Since we're at ground zero (no code written), adding service layer now costs ~2 hours vs 6-8 days of refactoring later. The ROI is clear.

---

## Appendix: Service Lifecycle FAQs

### Q: Should services be singletons or created per-request?

**A: Created per-request (stateless).**

Services have no state beyond their constructor dependencies. Creating per-request is negligible overhead (<1μs) and keeps the pattern simple.

### Q: How do services handle async initialization?

**A: They don't.**

Services receive already-initialized dependencies (client, cache). Async initialization happens in the lifespan manager (FastMCP startup).

### Q: When should I create a new service vs add to existing?

**A: Domain boundaries.**

- Same domain (tests) → Add to `TestService`
- Different domain (bugs) → New `BugService`
- Cross-domain (reports) → New `ReportService` that uses multiple services

### Q: Can services call other services?

**A: Yes, with constructor injection.**

```python
class ReportService:
    def __init__(
        self,
        test_service: TestService,
        bug_service: BugService,
        client: TestIOClient,
        test_repo: TestRepository,
        bug_repo: BugRepository
    ):
        self.test_service = test_service
        self.bug_service = bug_service
        # ...
```

### Q: Where do custom exceptions live?

**A: `src/testio_mcp/exceptions.py`**

```python
class TestIOException(Exception):
    """Base exception for TestIO errors."""

class TestNotFoundException(TestIOException):
    """Test not found (404)."""

class TestIOAPIError(TestIOException):
    """API error (4xx/5xx)."""
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
```

Services raise these; tools catch and convert to transport format.
