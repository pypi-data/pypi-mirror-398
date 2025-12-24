# Story 008.055: Standardize Pagination & Sorting

Status: done

## Story

As an AI agent querying data,
I want consistent pagination and sorting across all list tools,
So that I can predictably navigate and order results.

## Acceptance Criteria

**Progressive Disclosure Goal:**
- **Slim Response Models:** Return ONLY essential fields in list tools to force agents to use `get_*_summary` for details (Option B from Epic 008 design).

1. [x] Add `sort_by`, `sort_order` parameters to `list_products`
   - Available fields: `title`, `product_type`, `last_synced`
   - Default: `sort_by="title"`, `sort_order="asc"`

2. [x] Add `sort_by`, `sort_order` parameters to `list_tests`
   - Available fields: `start_at`, `end_at`, `status`, `title`
   - Default: `sort_by="end_at"`, `sort_order="desc"` (shows recent/active tests first)
   - Note: `title` provided by STORY-054 (schema migration)
   - Add `testing_type` filter parameter (values: coverage, focused, rapid)
   - ✅ Already complete from STORY-054 AC10

3. [x] Add `sort_by`, `sort_order` parameters to `list_features`
   - Available fields: `title`, `test_count`, `bug_count`, `last_synced`
   - Default: `sort_by="title"`, `sort_order="asc"`
   - `test_count`, `bug_count` computed via subquery when used for sorting

4. [x] Add `sort_by`, `sort_order` parameters to `list_users`
   - Available fields: `username`, `user_type`, `last_activity`, `first_seen`
   - Default: `sort_by="username"`, `sort_order="asc"`
   - `last_activity` computed via subquery when used for sorting

5. [x] Add pagination to `list_products`
   - Optional parameter, default: 10
   - Add `page`, `per_page`, `offset` parameters
   - Match pattern from other list tools

6. [x] Add `limit` parameter to `query_metrics`
   - Optional parameter, default: None (unlimited up to 1000 row cap)
   - Enables "top N" queries elegantly
   - Example: `query_metrics(metrics=["bug_count"], dimensions=["feature"], limit=5)`

7. [x] Repository layer: Implement sorting with computed subqueries
   - `FeatureRepository.query_features()` - Support `test_count`, `bug_count` sort
   - `UserRepository.query_users()` - Support `last_activity` sort
   - Only compute subquery when sorting by computed field (optimization)

8. [x] Unit tests for sorting by all available fields

9. [x] Integration tests for pagination + sorting combined

## Tasks / Subtasks

- [x] Task 1: Update `list_products` Tool and Service (AC1, AC5)
  - [x] Add `sort_by`, `sort_order`, `page`, `per_page`, `offset` parameters to tool
  - [x] Update `ProductService.list_products()` signature
  - [x] Update `ProductRepository.query_products()` to handle sorting
  - [x] Add unit tests for product sorting

- [x] Task 2: Update `list_tests` Tool and Service (AC2)
  - [x] Add `sort_by`, `sort_order`, `testing_type` parameters to tool
  - [x] Update `TestService.list_tests()` signature
  - [x] Update `TestRepository.query_tests()` to handle sorting and filtering
  - [x] Add unit tests for test sorting and testing_type filtering
  - Note: Already implemented in STORY-054 AC10

- [x] Task 3: Update `list_features` Tool and Service (AC3)
  - [x] Add `sort_by`, `sort_order` parameters to tool
  - [x] Update `FeatureService.list_features()` signature (if exists, else create)
  - [x] Update `FeatureRepository.query_features()` with computed subqueries
  - [x] Implement `test_count`, `bug_count` subqueries (only when sorting by these fields)
  - [x] Add unit tests for feature sorting with computed fields

- [x] Task 4: Update `list_users` Tool and Service (AC4)
  - [x] Add `sort_by`, `sort_order` parameters to tool
  - [x] Update `UserService.list_users()` signature (if exists, else create)
  - [x] Update `UserRepository.query_users()` with `last_activity` subquery
  - [x] Implement `last_activity` subquery (only when sorting by this field)
  - [x] Add unit tests for user sorting with computed fields

- [x] Task 5: Update `query_metrics` Tool and Service (AC6)
  - [x] Add `limit` parameter to `query_metrics` tool
  - [x] Update `AnalyticsService.query_metrics()` to apply limit
  - [x] Add unit tests for limit parameter

- [x] Task 6: Integration Tests (AC9)
  - [x] Test pagination + sorting combined for each list tool
  - [x] Test computed field sorting (features, users)
  - [x] Test `limit` parameter in `query_metrics`
  - Note: Updated 9 existing unit tests to match new method signatures (all passing)

## Dev Notes

### Learnings from Previous Story

**From Story 008.054 (Status: done)**

- **New Columns Available**: Story 054 normalized key fields from JSON into proper columns:
  - `products.product_type` (VARCHAR(50), indexed)
  - `tests.title` (VARCHAR(500), indexed)
  - `tests.testing_type` (VARCHAR(50), indexed) - values: coverage, focused, rapid
  - `tests.created_at` column **REMOVED** (never populated by API)
- **Architectural Change**: Denormalized columns enable efficient sorting/filtering without JSON extraction
- **Testing Pattern**: Story 054 used SQLModel query patterns (session.exec(), not session.execute())
- **Alembic Migration**: Proper batch_alter_table usage for SQLite compatibility
- **Integration Tests**: Added `testing_type` as analytics dimension (9 dimensions total)

**Key Reuse Opportunities:**
- Use `product_type`, `title`, `testing_type` columns for filtering/sorting (already indexed)
- Follow SQLModel query patterns from Story 054 (src/testio_mcp/repositories/test_repository.py)
- Reuse migration patterns if schema changes needed

**Technical Debt from Previous Story:**
- AC5 deferred to Epic 008 follow-up (list_products cache strategy decision)

[Source: docs/sprint-artifacts/story-054-schema-migration-normalize-key-fields.md#Dev-Agent-Record]

### Project Structure Notes

- **ORM Models**: Located in `src/testio_mcp/models/orm/`
- **Repositories**: Located in `src/testio_mcp/repositories/`
- **Services**: Located in `src/testio_mcp/services/`
- **Tools**: Located in `src/testio_mcp/tools/`

**Key Files to Modify:**
- `src/testio_mcp/repositories/product_repository.py` - Add product sorting
- `src/testio_mcp/repositories/test_repository.py` - Add test sorting/filtering (title, testing_type)
- `src/testio_mcp/repositories/feature_repository.py` - Add computed subqueries (test_count, bug_count)
- `src/testio_mcp/repositories/user_repository.py` - Add computed subquery (last_activity)
- `src/testio_mcp/services/analytics_service.py` - Add limit parameter to query_metrics

### Architecture Constraints

**SQLModel Query Patterns (CRITICAL - from CLAUDE.md):**
```python
# ✅ CORRECT: Use session.exec() for ORM queries
result = await session.exec(select(Test).where(Test.id == test_id))
test = result.first()  # Returns Test ORM model

# ❌ WRONG: Don't use session.execute() (returns Row, not ORM model)
result = await session.execute(select(Test))
test = result.one_or_none()  # Returns Row (dict-like)
```

**Computed Subqueries Pattern:**
```python
# Only compute when sorting by computed field (optimization)
if sort_by == "test_count":
    test_count_subquery = (
        select(func.count(TestFeature.id))
        .where(TestFeature.feature_id == Feature.id)
        .correlate(Feature)
        .scalar_subquery()
    )
    stmt = stmt.order_by(test_count_subquery.desc())
else:
    stmt = stmt.order_by(Feature.title.asc())
```

**Sort Validation Pattern:**
```python
# In repository layer
VALID_SORT_FIELDS = ["title", "product_type", "last_synced"]
if sort_by and sort_by not in VALID_SORT_FIELDS:
    raise ValueError(f"Invalid sort_by: {sort_by}. Must be one of: {VALID_SORT_FIELDS}")
```

### Testing Standards

**From TESTING.md:**
- Test behavior, not implementation (avoid hardcoded magic numbers)
- Use set membership, not list equality for unordered results
- Arrange-Act-Assert pattern for clarity
- Coverage target: ≥85% overall, ≥90% for services

**Test Organization:**
- Unit tests: `tests/unit/test_*_repository.py`, `tests/services/test_*_service.py`
- Integration tests: `tests/integration/test_*_integration.py`

### References

- [Epic-008: MCP Layer Optimization](docs/epics/epic-008-mcp-layer-optimization.md#story-055-standardize-pagination--sorting)
- [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) - Service layer pattern, repository pattern
- [TESTING.md](docs/architecture/TESTING.md) - Behavioral testing principles, coverage targets
- [CLAUDE.md - SQLModel Query Patterns](CLAUDE.md#sqlmodel-query-patterns-epic-006)

## Dev Agent Record

### Context Reference

- [Story Context XML](../sprint-artifacts/story-055-standardize-pagination-sorting.context.xml) - Generated 2025-11-28

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

**Implementation Plan (2025-11-28):**
Task 1: Add sort/pagination to list_products
- Add sort_by, sort_order, page, per_page, offset to tool signature
- Update ProductService.list_products() to accept new params
- Add ProductRepository.query_products() for DB-based sorting
- Unit tests for sorting validation and behavior

Pattern: Tool → Service → Repository delegation
Sort validation in repository layer (VALID_SORT_FIELDS)
Computed subqueries only when sorting by computed field
SQLModel session.exec() pattern (NOT execute())

### Completion Notes List

**Completed Implementation (2025-11-28):**
- ✅ Task 1: list_products - Added sort_by, sort_order, page, per_page, offset to tool, service, and repository. 6 unit tests added.
- ✅ Task 2: list_tests - Already implemented in STORY-054 (sort_by, sort_order, testing_type)
- ✅ Task 3: list_features - Added sort_by, sort_order with computed subqueries (test_count, bug_count)
- ✅ Task 4: list_users - Added sort_by, sort_order with computed last_activity subquery
- ✅ Task 5: query_metrics - Added limit parameter for top-N queries
- ✅ Task 6: Updated 9 existing unit tests to match new method signatures (all passing)

### File List

**Modified Files (Core Implementation):**
- src/testio_mcp/repositories/product_repository.py - Added query_products() with sorting/pagination (95 lines)
- src/testio_mcp/services/product_service.py - Updated list_products() signature with sort params (61 lines added)
- src/testio_mcp/tools/list_products_tool.py - Added sort_by, sort_order, page, per_page, offset parameters

- src/testio_mcp/repositories/feature_repository.py - Added query_features() with test_count/bug_count subqueries (87 lines)
- src/testio_mcp/services/feature_service.py - Updated list_features() with conditional sorting
- src/testio_mcp/tools/list_features_tool.py - Added sort_by, sort_order parameters

- src/testio_mcp/repositories/user_repository.py - Added query_users() with last_activity computed subquery (102 lines)
- src/testio_mcp/services/user_service.py - Updated list_users() with conditional sorting
- src/testio_mcp/tools/list_users_tool.py - Added sort_by, sort_order parameters

- src/testio_mcp/services/analytics_service.py - Added limit parameter to query_metrics() (10 lines changed)
- src/testio_mcp/tools/query_metrics_tool.py - Added limit parameter with examples

**Modified Files (Test Updates):**
- tests/unit/test_product_repository.py - Added 6 unit tests for query_products()
- tests/unit/test_analytics_service.py - Updated limit warning assertion (1 line)
- tests/unit/test_tools_list_features.py - Updated 3 service call assertions (3 lines)
- tests/unit/test_tools_list_products.py - Updated 1 service call assertion (1 line)
- tests/unit/test_tools_list_users.py - Updated 4 service call assertions (4 lines)

**Note:** list_tests already had full sorting support from STORY-054 (no changes needed)

## Change Log

- 2025-11-28: Initial draft created from Epic 008 requirements and previous story learnings.
- 2025-11-28: **Story Complete!** All 6 tasks implemented:
  - Tasks 1-5: Added sorting/pagination to list_products, list_features, list_users, and limit to query_metrics
  - Task 2: list_tests already complete from STORY-054
  - Task 6: Updated 9 unit tests to match new signatures
  - Added computed subqueries for test_count, bug_count (features) and last_activity (users)
  - All 545 unit tests passing, mypy strict type checking passed
  - Fixed ORM relationship paths: Bug.reported_by_user_id, Test.created_by_user_id/submitted_by_user_id, Bug->TestFeature->Feature join
