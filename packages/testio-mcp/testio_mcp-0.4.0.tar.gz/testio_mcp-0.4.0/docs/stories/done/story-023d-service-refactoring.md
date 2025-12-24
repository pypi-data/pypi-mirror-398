---
story_id: STORY-023d
epic_id: EPIC-004
title: Service Refactoring + Delete Legacy Services
status: approved
created: 2025-01-17
estimate: 2 story points (2 days)
assignee: dev
dependencies: [STORY-023c, STORY-023b]
priority: critical
---

## Story

**As a** developer maintaining the service layer
**I want** to refactor services to use repositories and delete legacy services
**So that** we have a clean, maintainable architecture with no duplication

## Problem Solved

**Current (5 Services):**
```
TestService     - Test operations (keep)
ProductService  - Product operations (keep)
ActivityService - Date filtering, activity reports (DELETE)
ReportService   - Bug reports, aggregation (DELETE)
BugService      - Bug operations (DELETE - merged into TestService)
```

**Issues:**
- ❌ Overlapping responsibilities (test service vs bug service)
- ❌ ActivityService only used for date utilities (now extracted in STORY-023b)
- ❌ ReportService duplicates logic with TestService
- ❌ Services violate single responsibility principle

**After (3 Services):**
```
TestService     - All test + bug operations
ProductService  - Product operations
MultiTestReportService - EBR reports (STORY-023e)
```

**Benefits:**
- ✅ Clear service boundaries
- ✅ No overlapping responsibilities
- ✅ Simpler dependency graph
- ✅ -1328 lines of code (-32% reduction)

## Acceptance Criteria

### AC1: Refactor TestService

**Move list operations from ProductService:**
- [ ] Move `list_tests()` from ProductService to TestService
- [ ] Update MCP tool `list_tests_tool.py` to use TestService
- [ ] Rationale: Tests are the domain of TestService, not ProductService

**Consolidate bug operations:**
- [ ] Move bug-related methods from BugService to TestService
- [ ] Use BugRepository for data access
- [ ] Methods: `get_test_bugs()`, `get_bug_stats()`

**Updated TestService Interface:**
```python
class TestService(BaseService):
    """Service for test and bug operations."""

    def __init__(
        self,
        client: TestIOClient,
        test_repo: TestRepository,
        bug_repo: BugRepository,
    ):
        super().__init__(client)
        self.test_repo = test_repo
        self.bug_repo = bug_repo

    # Test operations
    async def list_tests(...) -> dict:
        """List tests from SQLite (no API call)."""

    async def get_test_status(test_id: int) -> dict:
        """Get test status (refresh from API, then query SQLite)."""

    # Bug operations (from BugService)
    async def get_test_bugs(test_id: int) -> dict:
        """Get bugs for test (refresh from API, then query SQLite)."""
```

### AC2: Refactor ProductService

**Simplify to product-only operations:**
- [ ] Remove `list_tests()` (moved to TestService)
- [ ] Keep `list_products()` and `get_product()`
- [ ] ProductService becomes purely product-focused

**Updated ProductService Interface:**
```python
class ProductService(BaseService):
    """Service for product operations."""

    def __init__(self, client: TestIOClient, product_repo: ProductRepository):
        super().__init__(client)
        self.product_repo = product_repo

    async def list_products() -> dict:
        """List products from SQLite (background sync)."""

    async def get_product(product_id: int) -> dict:
        """Get product details (query SQLite)."""
```

### AC3: Delete ActivityService

**Safe to delete because:**
- ✅ Date utilities extracted to `utilities/` (STORY-023b)
- ✅ Activity reports not used in current tools
- ✅ Background sync provides activity data via SQLite

**Deletion checklist:**
- [ ] Delete `src/testio_mcp/services/activity_service.py` (565 lines)
- [ ] Delete `tests/services/test_activity_service.py`
- [ ] Remove imports from `services/__init__.py`
- [ ] Verify no references in codebase: `grep -r "ActivityService" src/`

### AC4: Delete ReportService

**Safe to delete because:**
- ✅ Bug classification utilities extracted (STORY-023b)
- ✅ Report logic duplicates TestService functionality
- ✅ EBR reports will use MultiTestReportService (STORY-023e)

**Deletion checklist:**
- [ ] Delete `src/testio_mcp/services/report_service.py` (763 lines)
- [ ] Delete `tests/services/test_report_service.py`
- [ ] Remove imports from `services/__init__.py`
- [ ] Verify no references: `grep -r "ReportService" src/`

### AC5: Delete BugService

**Safe to delete because:**
- ✅ Bug operations moved to TestService
- ✅ BugRepository handles data access
- ✅ No unique business logic (all migrated)

**Deletion checklist:**
- [ ] Delete `src/testio_mcp/services/bug_service.py`
- [ ] Delete `tests/services/test_bug_service.py`
- [ ] Update tools to use TestService for bug operations
- [ ] Verify no references: `grep -r "BugService" src/`

### AC6: Update All MCP Tools

**Update tool imports and service usage:**
- [ ] `list_tests_tool.py` - Use TestService (not ProductService)
- [ ] `get_test_status_tool.py` - Use refactored TestService
- [ ] `get_test_bugs_tool.py` - Use TestService (not BugService)
- [ ] Verify all tools work via MCP Inspector

### AC7: Verify No Regressions

- [ ] Run full test suite: `uv run pytest`
- [ ] All tests pass (update service tests to match new structure)
- [ ] Run MCP Inspector: `npx @modelcontextprotocol/inspector uv run python -m testio_mcp`
- [ ] Test all tools manually (health_check, list_tests, get_test_status, etc.)
- [ ] Verify background sync still works

## Tasks

### Task 1: Refactor TestService (3 hours)

**Move list_tests from ProductService:**
- [ ] Copy `list_tests()` method to TestService
- [ ] Update to use TestRepository
- [ ] Remove from ProductService
- [ ] Update `list_tests_tool.py` to use TestService

**Consolidate bug operations:**
- [ ] Move bug methods from BugService to TestService
- [ ] Inject BugRepository into TestService
- [ ] Update `get_test_bugs()` to use BugRepository
- [ ] Update `get_test_status()` to aggregate bugs

**Test coverage:**
- [ ] Update `tests/services/test_test_service.py`
- [ ] Add tests for new list_tests method
- [ ] Add tests for bug operations

### Task 2: Simplify ProductService (1 hour)

- [ ] Remove `list_tests()` method
- [ ] Keep only `list_products()` and `get_product()`
- [ ] Update tests to reflect simpler interface
- [ ] Verify ProductService focuses only on products

### Task 3: Delete Legacy Services (2 hours)

**Delete ActivityService:**
- [ ] Verify date utilities are in `utilities/` (STORY-023b)
- [ ] Delete service file (565 lines)
- [ ] Delete test file
- [ ] Remove from `__init__.py`
- [ ] Search codebase for references, update if needed

**Delete ReportService:**
- [ ] Verify bug classifiers are in `utilities/` (STORY-023b)
- [ ] Delete service file (763 lines)
- [ ] Delete test file
- [ ] Remove from `__init__.py`
- [ ] Search codebase for references

**Delete BugService:**
- [ ] Verify bug operations moved to TestService
- [ ] Delete service file
- [ ] Delete test file
- [ ] Remove from `__init__.py`

### Task 4: Update MCP Tools (2 hours)

- [ ] Update `list_tests_tool.py` (ProductService → TestService)
- [ ] Update `get_test_bugs_tool.py` (BugService → TestService)
- [ ] Update `get_test_status_tool.py` (use refactored TestService)
- [ ] Test all tools via MCP Inspector
- [ ] Verify error handling still works

### Task 5: Testing & Validation (2 hours)

- [ ] Update service tests to match new structure
- [ ] Run full test suite: `uv run pytest`
- [ ] Fix any failing tests
- [ ] Run integration tests with real API
- [ ] Manual testing via MCP Inspector

## Testing

### Service Tests
```python
# tests/services/test_test_service.py

@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_tests_queries_repository():
    """Verify list_tests uses TestRepository (not API)."""
    mock_repo = AsyncMock()
    mock_repo.query_tests.return_value = [
        {"id": 123, "title": "Test 1"},
        {"id": 124, "title": "Test 2"},
    ]

    service = TestService(
        client=AsyncMock(),
        test_repo=mock_repo,
        bug_repo=AsyncMock(),
    )

    result = await service.list_tests(product_id=598)

    assert len(result["tests"]) == 2
    mock_repo.query_tests.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_test_bugs_uses_bug_repository():
    """Verify get_test_bugs uses BugRepository."""
    mock_bug_repo = AsyncMock()
    mock_bug_repo.refresh_bugs.return_value = 5
    mock_bug_repo.get_bugs.return_value = [{"id": 1, "status": "accepted"}]

    service = TestService(
        client=AsyncMock(),
        test_repo=AsyncMock(),
        bug_repo=mock_bug_repo,
    )

    result = await service.get_test_bugs(test_id=123)

    assert len(result["bugs"]) == 1
    mock_bug_repo.refresh_bugs.assert_called_once_with(123)
    mock_bug_repo.get_bugs.assert_called_once_with(123)
```

### Integration Tests
```python
# tests/integration/test_service_refactoring_integration.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_tests_with_real_database():
    """Verify list_tests works with real SQLite database."""
    service = TestService(...)  # Real dependencies

    result = await service.list_tests(product_id=598)

    assert "tests" in result
    assert "total_count" in result
    assert isinstance(result["tests"], list)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_test_status_refreshes_from_api():
    """Verify get_test_status fetches fresh data."""
    service = TestService(...)  # Real dependencies

    result = await service.get_test_status(test_id=109363)

    # Should have fresh data from API
    assert result["test"]["id"] == 109363
    assert "bugs" in result
```

## Implementation Notes

### Why Move list_tests to TestService?

**Domain Alignment:**
- TestService owns test operations
- ProductService owns product operations
- Listing tests is a test operation (not product operation)

**Simpler Dependencies:**
- TestService already has TestRepository
- No need to inject TestRepository into ProductService

### Why Delete ActivityService?

**Date utilities extracted (STORY-023b):**
- All date parsing logic now in `utilities/date_utils.py`
- Background sync provides activity data via SQLite
- No unique business logic remaining

### Why Delete ReportService?

**Bug classification extracted (STORY-023b):**
- Bug classifiers now in `utilities/bug_classifiers.py`
- TestService handles bug operations
- EBR reports will use MultiTestReportService (STORY-023e)

### Service Boundaries After This Story

```
TestService:
- list_tests (from ProductService)
- get_test_status (existing)
- get_test_bugs (from BugService)

ProductService:
- list_products (existing)
- get_product (existing)

MultiTestReportService (STORY-023e):
- generate_ebr_report (new)
```

### Code Deletion Summary

**Files deleted:**
- `activity_service.py` (565 lines)
- `report_service.py` (763 lines)
- `bug_service.py` (~200 lines)
- Associated test files (~600 lines)

**Total:** ~2128 lines deleted (-32% reduction)

## Success Metrics

- ✅ TestService consolidates test + bug operations
- ✅ ProductService simplified (products only)
- ✅ ActivityService deleted (565 lines)
- ✅ ReportService deleted (763 lines)
- ✅ BugService deleted (~200 lines)
- ✅ All tests pass (no regressions)
- ✅ All MCP tools work correctly
- ✅ -2128 lines total (-32% code reduction)

## References

- **EPIC-004:** Production-Ready Architecture Rewrite
- **STORY-023b:** Extract Shared Utilities (date utilities, bug classifiers)
- **STORY-023c:** SQLite-First Foundation (repository layer)
- **Architecture Docs:**
  - `docs/architecture/wip/FINAL-ARCHITECTURE-PLAN.md` - Service layer refactoring
  - `docs/architecture/wip/CLEAN-SLATE-REWRITE-PLAN.md` - Code deletion strategy

---

**Deliverable:** Clean service layer, legacy services deleted, -2128 lines, no regressions
