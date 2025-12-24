# Service Layer Architecture - Summary & Deliverables

**Version:** 2.0.0
**Last Updated:** 2025-12-03
**Original Date:** 2025-11-04
**Author:** Architect (Winston)
**Purpose:** Service layer architecture documentation
**Status:** ✅ Production (13 services)

---

## Executive Summary

The TestIO MCP Server architecture has been refined to include a **service layer** that separates business logic from transport mechanisms. This change was made at "ground zero" (before implementation begins) with minimal cost (~3 hours of documentation) compared to refactoring later (6-8 days).

### Key Decision

**Problem:** Current architecture would tightly couple business logic to FastMCP framework, making future multi-transport support difficult.

**Solution:** Add service layer between MCP tools and infrastructure, following industry best practices (Cosmic Python, FastAPI patterns, Clean Architecture).

**Impact:**
- ✅ Future flexibility (REST API, CLI, webhooks can reuse business logic)
- ✅ Better testability (no MCP framework mocking required)
- ✅ Clear separation of concerns (transport vs domain logic)
- ⚠️ More files (13 service classes as of v0.3.0)
- ⚠️ Minimal indirection (tool → service → repository → client)

---

## Deliverables Completed

### 1. ADR-006: Service Layer Pattern ✅

**File:** `docs/architecture/adrs/ADR-006-service-layer-pattern.md`

**Contents:**
- Context and research findings
- Decision rationale
- Complete implementation guide with code examples
- Service boundaries (TestService, ProductService, MultiTestReportService)
- Testing strategy for services
- Future REST API examples (documentation only)
- Migration path if needed
- FAQs on service lifecycle, async initialization, error handling

**Note:** Original design proposed 4 services. Post-refactoring (STORY-023), consolidated to 3 services with repository pattern for data access.

**Key Patterns (Updated for SQLite-First Architecture):**
```python
# Service pattern (with repository pattern)
class TestService:
    def __init__(
        self,
        client: TestIOClient,
        test_repo: TestRepository,
        bug_repo: BugRepository,
    ):
        self.client = client
        self.test_repo = test_repo
        self.bug_repo = bug_repo

    async def get_test_status(self, test_id: int) -> dict:
        # Business logic: SQLite first, API fallback
        test = await self.test_repo.get_test_by_id(test_id)
        if not test:
            # Fallback to API if not in database
            test_data = await self.client.get(f"exploratory_tests/{test_id}")
            await self.test_repo.insert_test(test_data, product_id=test_data["product"]["id"])
            test = test_data

        # Get bugs from database
        bugs = await self.bug_repo.get_bugs_for_test(test_id)
        return {"test": test, "bugs": bugs, "summary": self._aggregate_bugs(bugs)}

# Tool pattern (thin wrapper with get_service helper)
from testio_mcp.utilities import get_service
from fastmcp.exceptions import ToolError

@mcp.tool()
async def get_test_status(test_id: int, ctx: Context) -> dict:
    # Extract dependencies and create service (1 line!)
    service = get_service(ctx, TestService)

    try:
        return await service.get_test_status(test_id)
    except TestNotFoundException:
        raise ToolError(
            f"❌ Test '{test_id}' not found\n"
            f"ℹ️ The test may have been deleted or archived\n"
            f"💡 Verify the test ID is correct"
        ) from None
```

---

### 2. Updated ARCHITECTURE.md (v1.1) ✅

**File:** `docs/architecture/ARCHITECTURE.md`

**Changes:**
- **Component diagram** updated to show service layer
- **Component responsibilities** section updated:
  - MCP Tools: "Thin wrappers" (extract deps, delegate, convert errors)
  - Service Layer: NEW section with 4 services and responsibilities
  - Clear separation of what tools should/shouldn't do
- **Data flow** updated to show tool → service → client flow
- **Testing pyramid** updated:
  - New service tests layer (80 tests, primary focus)
  - Service tests don't require FastMCP mocking
  - Test organization includes `tests/services/` directory
- **ADR list** updated to include ADR-006
- **Version bumped** to 1.1 with changelog

---

### 3. Updated ADR-001 ✅

**File:** `docs/architecture/adrs/ADR-001-api-client-dependency-injection.md`

**Changes:**
- Section 3 (Tool Implementation) updated with service delegation pattern
- Section 4 (Testing) updated to show:
  - Preferred: Test services directly (faster, no FastMCP)
  - Alternative: Test tools for error conversion (integration test)
- Related Decisions updated to link ADR-006
- Code examples show extract deps → create service → delegate pattern

---

### 4. Updated Story 2 (Template for Stories 3-7) ✅

**File:** `docs/stories/story-002-get-test-status.md`

**Changes:**
- **New "Implementation Approach" section** explaining two-part implementation
- **AC0: Service Layer Implementation** - Create TestService first
  - Constructor, methods, caching, error handling
  - Complete code example
- **AC1 updated:** Tool as thin wrapper (extract, delegate, convert errors)
- **AC3 updated:** API calls in service layer (not tool)
- **AC4 updated:** Bug aggregation in service (private method)
- **AC6 updated:** Two-layer error handling (service raises domain exceptions, tool converts to MCP format)
- **AC7 NEW:** Service unit tests (primary testing layer)
  - Test with mocked client/cache
  - No FastMCP overhead
  - Example test included
- **AC8 (formerly AC7):** Integration test (tool → service → API)

**Pattern for Stories 3-7:**
1. Create service class first (business logic)
2. Create MCP tool second (thin wrapper)
3. Write service tests (primary)
4. Write integration tests (secondary)

---

### 5. Concrete Code Examples ✅

**Included in ADR-006 (Updated for SQLite-First):**

**Example 1: SQLite-First Service (TestService.get_test_status)**
- Complete service class with repository dependencies
- SQLite-first pattern with API fallback
- Repository queries for tests and bugs
- Private helper methods for aggregation
- Error handling (raise domain exceptions)

**Example 2: Repository Pattern Integration**
- Service constructor receives repositories (not cache)
- Repository methods: `get_test_by_id()`, `get_bugs_for_test()`, `insert_test()`
- Clear separation: Service = business logic, Repository = data access
- Mock repositories in tests (not SQLite database)

**Example 3: Service Testing (Updated)**
- Test SQLite query scenarios (repository mocking)
- Mock client and repositories setup
- Verify API fallback, data insertion, aggregation
- No FastMCP mocking required
- No database setup needed (mock repositories)

**Example 4: MCP Tool Wrapper (Simplified with get_service)**
- Use `get_service(ctx, ServiceClass)` helper (1 line)
- Automatic dependency injection from context
- Delegate to service
- Convert exceptions to ToolError (not dict returns)

**Example 5: Future REST Endpoint (Documentation Only)**
- Same service reused in FastAPI endpoint
- FastAPI Depends() for DI (similar to FastMCP Context)
- Shows multi-transport architecture

---

### 6. Research Bibliography ✅

**Primary Sources:**

1. **Cosmic Python (Architecture Patterns with Python)**
   - https://www.cosmicpython.com/book/chapter_04_service_layer.html
   - Service layer pattern fundamentals
   - Orchestration logic separation
   - Testing improvements (fake repositories)

2. **FastAPI Layered Architecture (DEV Community)**
   - https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo
   - Controller → Service → Repository pattern
   - Dependency injection chains
   - Testing with dependency overrides

3. **FastAPI DI + Service Layer (blog.dotcs.me)**
   - https://blog.dotcs.me/posts/fastapi-dependency-injection-x-layers
   - Combining Depends() with multi-layer architecture
   - Service testing patterns
   - Selective mocking at repository layer

4. **Hexagonal Architecture in Python (Medium)**
   - https://medium.com/@miks.szymon/hexagonal-architecture-in-python-e16a8646f000
   - Ports and adapters pattern
   - Multi-transport architecture
   - Framework independence

5. **Clean Architecture with Python (Medium)**
   - https://medium.com/@shaliamekh/clean-architecture-with-python-d62712fd8d4f
   - Separation of concerns
   - Layer dependencies
   - Testing strategies

**Supporting Sources:**

6. **FastAPI Best Practices (GitHub)**
   - https://github.com/zhanymkanov/fastapi-best-practices
   - Project structure recommendations
   - Service layer patterns

7. **FastAPI Official Docs: Bigger Applications**
   - https://fastapi.tiangolo.com/tutorial/bigger-applications/
   - Project organization
   - APIRouter patterns

8. **FastAPI Official Docs: Dependencies**
   - https://fastapi.tiangolo.com/tutorial/dependencies/
   - Dependency injection fundamentals

9. **Python HTTPX Async Docs**
   - https://www.python-httpx.org/async/
   - Async client patterns
   - Connection pooling

**Industry Best Practices:**

- **Martin Fowler:** Service Layer Pattern (Patterns of Enterprise Application Architecture)
- **Robert C. Martin:** Clean Architecture (The Clean Architecture book)
- **Eric Evans:** Domain-Driven Design principles

---

## Authentication Architecture Considerations

### Current State (MVP)

**Authentication Model:**
- **Server-side API token** stored in `.env` file
- **Single-tenant** design (one TestIO customer account)
- **No user authentication** (MCP via stdio, no network exposure)
- **Token managed** by lifespan manager, injected into TestIOClient

**Code (SQLite-First Architecture):**
```python
# server.py
async with TestIOClient(
    base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
    api_token=settings.TESTIO_CUSTOMER_API_TOKEN,  # Single server token
) as client:
    # Initialize PersistentCache (SQLite database)
    cache = PersistentCache(
        db_path=settings.TESTIO_DB_PATH,
        customer_id=settings.TESTIO_CUSTOMER_ID,
        customer_name=settings.TESTIO_CUSTOMER_NAME,
    )
    await cache.initialize()

    # Inject into server context
    server.context["testio_client"] = client
    server.context["cache"] = cache  # PersistentCache (SQLite)
```

### Future Multi-Tenant Requirements

**Scenario:** Support multiple TestIO customer accounts (different CSMs, different customers)

**Two Architectural Approaches:**

#### Approach 1: User-Level Authentication (Recommended)

**Pattern:**
```
User → MCP Tool → Service (with user context) → Client (user's API token)
```

**Implementation (Updated for Repository Pattern):**
```python
# Future: User context in MCP tools
@mcp.tool()
async def get_test_status(test_id: int, ctx: Context, user_id: str) -> dict:
    # Get user-specific client from context
    user_auth = ctx["user_auth_service"].get_user(user_id)

    # Create client with user's API token
    client = TestIOClient(
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
        api_token=user_auth.TESTIO_CUSTOMER_API_TOKEN  # User-specific token
    )

    # Get repositories from context (shared SQLite database)
    test_repo = ctx["test_repository"]
    bug_repo = ctx["bug_repository"]

    # Service layer unchanged (repository pattern)
    service = TestService(client=client, test_repo=test_repo, bug_repo=bug_repo)
    return await service.get_test_status(test_id)
```

**Benefits:**
- ✅ **Service layer unchanged** (already receives client as dependency)
- ✅ **Clear security boundaries** (each user's token isolated)
- ✅ **Audit trail** (know which user made which request)
- ✅ **Per-user rate limiting** possible

**Changes Required:**
- Add user authentication service (JWT, session, OAuth)
- Store user → API token mappings (encrypted database, secrets manager)
- Add user context to MCP tools
- Database isolation per customer_id (multi-tenancy support in PersistentCache)

#### Approach 2: Super-User Key (Not Recommended)

**Pattern:**
```
Server → TestIO API (with super-user key that can access all customers)
```

**Security Concerns:**
- ❌ **Single point of failure** (one compromised key = all customer data)
- ❌ **No audit trail** (can't distinguish user actions)
- ❌ **Violates principle of least privilege**
- ❌ **TestIO API may not support** this pattern

### Recommended Migration Path

**Phase 1: MVP (Current)**
- Single server token
- Single tenant
- No user auth (stdio only)

**Phase 2: Multi-User (Same Tenant)**
- Add user authentication (JWT via HTTP headers)
- Multiple users share same TestIO API token
- User permissions managed application-side

**Phase 3: Multi-Tenant**
- User authentication + tenant mapping
- Store user → tenant → API token in encrypted database
- Create TestIOClient per-request with user's token
- **Service layer remains unchanged** (already accepts client as dependency)

### How Service Layer Enables Auth Migration (Updated for Repositories)

**Current (MVP):**
```python
# One client for everyone, shared repositories
client = ctx["testio_client"]  # Server-wide singleton
test_repo = ctx["test_repository"]
bug_repo = ctx["bug_repository"]
service = TestService(client=client, test_repo=test_repo, bug_repo=bug_repo)
```

**Future (Multi-Tenant):**
```python
# Client per user, tenant-isolated repositories
user_token = ctx["user_service"].get_token(user_id)
client = TestIOClient(base_url=..., api_token=user_token)  # User-specific

# Repositories filtered by customer_id (multi-tenant isolation)
test_repo = ctx["test_repository"]  # Same instance, customer_id filtering in queries
bug_repo = ctx["bug_repository"]

service = TestService(client=client, test_repo=test_repo, bug_repo=bug_repo)  # Service unchanged!
```

**Key Insight:**
- Service layer is **already designed** for dependency injection
- Services **don't care** if client is server-wide or user-specific
- PersistentCache supports multi-tenancy via `customer_id` field (already implemented)
- Migration requires changes only in **tool layer** (extract user context, create user client)
- **Zero changes** to service business logic

---

## Success Criteria Met

### ✅ ADR-006 Created
- Clear rationale, implementation guidance, code examples
- 3,500+ words of comprehensive documentation
- Links to research sources

### ✅ ARCHITECTURE.md Updated
- Service layer in component diagram
- Updated data flows
- Updated testing strategy
- Version bumped to 1.1

### ✅ ADR-001 Updated
- Service pattern in tool examples
- Testing strategy updated
- Links to ADR-006

### ✅ Stories 2-7 Updated
- Story 2 as template (complete)
- Stories 3-7 follow same pattern
- AC0 for service creation
- AC7 for service testing

### ✅ Code Examples Provided
- 5 complete examples in ADR-006
- TestService (simple)
- BugService (complex with pagination)
- Service testing
- MCP tool wrapper
- Future REST endpoint

### ✅ Testing Strategy Defined
- Service tests (primary, 80 tests)
- Integration tests (secondary, 20 tests)
- Clear separation of concerns

### ✅ No REST Implementation
- Documentation only for future
- Examples clearly marked "(NOT IN MVP)"

### ✅ Cross-References Complete
- ADRs link to each other
- Stories link to ADRs
- ARCHITECTURE.md links to ADRs

### ✅ Peer Review Ready
- Clear enough for dev team
- Complete code examples
- Testing strategy included
- Migration path documented

---

## Quality Verification

### ADR Quality ✅
- Follows existing ADR format
- Includes concrete code examples (not pseudocode)
- Explains trade-offs honestly
- Links to related decisions
- Cites research sources (9 primary sources)

### Architecture Documentation ✅
- ASCII diagrams for visual clarity
- Shows data flow with examples
- Explains component responsibilities
- Includes testing strategy for each layer

### Code Examples ✅
- Complete, copy-paste-ready
- Follows Python async/await patterns
- Includes type hints and docstrings
- Shows error handling patterns
- Includes test examples

### Research Documentation ✅
- 9 cited sources with URLs
- Explains why patterns were chosen
- Shows alternatives considered
- References industry best practices

---

## Timeline

**Total effort:** 3 hours
- Research: 1 hour
- ADR-006 writing: 1 hour
- Architecture updates: 45 minutes
- Story updates: 30 minutes
- Examples & summary: 45 minutes

**Deadline:** Before Story 1 implementation begins ✅ **COMPLETE**

---

## Next Steps for Dev Team

### 1. Create Exceptions Module (New File)

```python
# src/testio_mcp/exceptions.py

class TestIOException(Exception):
    """Base exception for TestIO errors."""

class TestNotFoundException(TestIOException):
    """Test not found (404)."""

class TestIOAPIError(TestIOException):
    """API error (4xx/5xx)."""
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
```

### 2. Create Service Directory

```bash
mkdir -p src/testio_mcp/services
touch src/testio_mcp/services/__init__.py
```

### 3. Follow Story 2 Pattern

For each story (2-7):
1. **Create service class** first (AC0)
2. **Create MCP tool** second (AC1)
3. **Write service tests** (AC7)
4. **Write integration tests** (AC8)

### 4. Review Checklist

Before implementation:
- [ ] Read ADR-006 completely
- [ ] Understand service vs tool responsibilities
- [ ] Review testing strategy
- [ ] Understand error handling pattern
- [ ] Review code examples in ADR-006

---

## Files Created/Modified

**Created:**
- ✅ `docs/architecture/adrs/ADR-006-service-layer-pattern.md` (new, 10KB)
- ✅ `docs/architecture/SERVICE_LAYER_SUMMARY.md` (this file)

**Modified:**
- ✅ `docs/architecture/ARCHITECTURE.md` (v1.0 → v1.1)
- ✅ `docs/architecture/adrs/ADR-001-api-client-dependency-injection.md`
- ✅ `docs/stories/story-002-get-test-status.md`

**Actually Created (STORY-021, STORY-023, and subsequent Epics):**
- ✅ `src/testio_mcp/exceptions.py` (Domain exceptions)
- ✅ `src/testio_mcp/services/__init__.py`
- ✅ `src/testio_mcp/utilities.py` (`get_service()` helper for DI)
- ✅ `tests/services/` (Service test directory)
- ✅ `tests/fixtures/cache_fixtures.py` (PersistentCache fixtures)

**Service Catalog (13 services as of v0.3.0):**

| Category | Service | Purpose | Lines | Epic/Story |
|----------|---------|---------|-------|------------|
| **Core** | BaseService | Minimal DI base class | ~20 | MVP |
| | TestService | Test status, queries | ~400 | MVP |
| | ProductService | Product listing | ~300 | MVP |
| | BugService | Bug listing/details | ~250 | STORY-084/085 |
| | FeatureService | Feature operations | ~200 | Epic-005 |
| | UserService | User operations | ~200 | Epic-005 |
| **Analytics** | AnalyticsService | Dynamic metrics, pivot tables | ~825 | Epic-007 |
| | QueryBuilder | Dynamic SQL construction | ~400 | Epic-007 |
| | MultiTestReportService | EBR aggregation | ~500 | Epic-003 |
| **Infrastructure** | SyncService | 3-phase sync orchestration | ~1300 | Epic-009 |
| | DiagnosticsService | Server health | ~300 | STORY-060 |
| | SearchService | FTS5 full-text search | ~200 | Epic-010 |
| | UserStoryService | User story extraction | ~150 | Epic-005 |

**Repository Layer:**
- ✅ `src/testio_mcp/repositories/test_repository.py`
- ✅ `src/testio_mcp/repositories/product_repository.py`
- ✅ `src/testio_mcp/repositories/bug_repository.py`
- ✅ `src/testio_mcp/repositories/feature_repository.py`
- ✅ `src/testio_mcp/repositories/user_repository.py`
- ✅ `src/testio_mcp/repositories/search_repository.py`

**Evolution:**
- **MVP (Nov 2024):** 3 services (Test, Product, MultiTestReport)
- **Epic-005 (Nov 2024):** +3 services (Feature, User, UserStory)
- **Epic-007 (Nov 2024):** +2 services (Analytics, QueryBuilder)
- **Epic-009 (Nov 2024):** +1 service (SyncService unified)
- **Epic-010 (Nov 2024):** +1 service (SearchService)
- **STORY-060 (Nov 2024):** +1 service (DiagnosticsService)
- **STORY-084/085 (Nov 2024):** +1 service (BugService)

---

## Conclusion

The service layer architecture refinement is **complete and fully implemented** with SQLite-first architecture. The original design (ground zero) proved successful through STORY-021, STORY-023, and subsequent epic implementations.

**Key Benefits (Validated in Production):**
1. ✅ **Future-proof architecture** - Multi-transport ready (stdio + HTTP modes implemented)
2. ✅ **Better testability** - No MCP framework overhead, repository mocking in tests
3. ✅ **Clear separation of concerns** - Transport vs business logic vs data access
4. ✅ **Authentication migration path** - User-specific clients supported via DI
5. ✅ **SQLite-first performance** - ~10ms queries, efficient background sync

**Architecture Evolution:**
- **MVP (Nov 2024):** 3 services with repository pattern
- **v0.3.0 (Dec 2024):** 13 services across Core, Analytics, and Infrastructure categories
- **Key additions:** Analytics (query_metrics), Search (FTS5), Sync (unified orchestration)

**Implementation Status:** ✅ **Complete and Production-Ready**

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-03 | 2.0.0 | Updated service catalog (3→13), added evolution timeline |
| 2025-11-18 | 1.1.0 | Post-STORY-023 refactoring, SQLite-first architecture |
| 2025-11-04 | 1.0.0 | Initial service layer design |
