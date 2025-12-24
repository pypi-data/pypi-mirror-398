# TestIO MCP - Epic 013: Repository Read Pattern Standardization

**Author:** leoric
**Date:** 2025-12-01
**Project Level:** Brownfield Refactor
**Target Scale:** Production MCP Server

---

## Overview

This epic eliminates technical debt in the repository layer by standardizing read patterns to use denormalized columns instead of parsing JSON blobs. This reduces maintenance risk, prevents stale data leakage, and improves query performance.

**Epic Count:** 1 (focused refactoring effort)
**Story Count:** 5 stories (STORY-076 through STORY-080)

**Origin:** Tech debt identified during Epic 012 implementation (see `docs/planning/repository-read-pattern-standardization.md`)

---

## Problem Statement

Repository read methods have inconsistent patterns for returning data:

1. **JSON Blob Parsing Overhead**: Every read parses the full `raw_data`/`data` JSON blob, even when only denormalized columns are needed
2. **Override Pattern Debt**: Manual field overrides (`status`, `known`, `test_environment`) scattered across methods
3. **Stale Data Leakage**: Only some denormalized fields are overridden; others may return stale JSON values
4. **Field Mapping Bugs**: `created_at` vs `reported_at` - service code expects `created_at` but API returns `reported_at`
5. **Inconsistent Return Types**: Some methods return ORM models, some return dicts, some return partial dicts

---

## Functional Requirements Inventory

| FR | Description | Source |
|----|-------------|--------|
| FR1 | Add missing `review_status` column to Test ORM with backfill | Consumer Audit |
| FR2 | BugRepository reads from columns only (no JSON parsing for standard reads) | Architecture Decision |
| FR3 | TestRepository reads from columns only (no JSON parsing for standard reads) | Architecture Decision |
| FR4 | ProductRepository and FeatureRepository follow same column-only pattern | Architecture Decision |
| FR5 | Fix `reported_at` field mapping (Bug timestamp consistency) | Field Mapping Audit |
| FR6 | Opt-in `*_with_details()` methods for nested data access | Consumer Audit |

---

## FR Coverage Map

| Epic | FRs Covered |
|------|-------------|
| Epic 013 | FR1, FR2, FR3, FR4, FR5, FR6 |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Breaking existing consumers** | Medium | High | Comprehensive consumer audit completed; update all callers |
| **Missing fields in column-only reads** | Medium | Medium | Data equivalence tests compare old vs new output |
| **Performance regression** | Low | Medium | Capture baseline timing; verify improvement with thresholds |
| **NULL handling in `*_with_details()`** | Medium | Low | Defensive checks for NULL `raw_data` |
| **Implicit blocking I/O in async context** | Medium | High | Use `deferred` column + test assertions to detect accidental access; avoid lazy loads in async paths |
| **Migration backfill on large datasets** | Low | Medium | Use batched backfill if >10k rows; test on realistic dataset |

### Rollback Strategy

Each story is independently reversible:

1. **Database changes (STORY-076)**: Migration has `downgrade()` function
2. **Repository changes (STORY-077-079)**: Revert to previous implementation; no schema changes
3. **Schema changes (STORY-080)**: Revert schema files; API contract preserved

**Full rollback**: Revert commits in reverse story order. No data migration needed (columns are additive).

---

## Dependency Graph

```
STORY-076 (review_status column)
    │
    ├── STORY-077 (BugRepository) ──┐
    │                               │
    ├── STORY-078 (TestRepository) ─┼── STORY-080 (reported_at fix)
    │       depends on 076          │        depends on 077-079
    │                               │
    └── STORY-079 (Product/Feature)─┘
```

**Critical Path:** 076 → [077 ∥ 078 ∥ 079] → 080

**Note:** Stories 077, 078, 079 can run in parallel after 076 completes. Story 080 requires all three repository refactors complete.

---

## Architecture Decision

### Before (Current Pattern)

```python
async def get_bugs(self, test_id: int) -> list[dict[str, Any]]:
    bugs_orm = await self._query_bugs(test_id)
    bugs = []
    for bug_orm in bugs_orm:
        bug_dict = json.loads(bug_orm.raw_data)  # Parse full JSON
        bug_dict["status"] = bug_orm.status       # Override some fields
        bug_dict["known"] = bug_orm.known
        # Other denormalized fields NOT overridden (stale data risk)
        bugs.append(bug_dict)
    return bugs
```

### After (Target Pattern)

```python
async def get_bugs(self, test_id: int) -> list[dict[str, Any]]:
    """Returns bug dicts built from columns only."""
    bugs_orm = await self._query_bugs(test_id)
    return [self._bug_to_dict(bug) for bug in bugs_orm]

def _bug_to_dict(self, bug: Bug) -> dict[str, Any]:
    """Convert ORM model to dict using columns only."""
    return {
        "id": bug.id,
        "title": bug.title,
        "severity": bug.severity,
        "status": bug.status,
        "known": bug.known,
        "reported_at": bug.reported_at,
        # ... all denormalized columns
    }

async def get_bugs_with_details(self, test_id: int) -> list[dict[str, Any]]:
    """Returns bug dicts with nested data (devices, reproductions).

    Use sparingly - requires JSON parsing. Single query with undefer.
    """
    # Explicit opt-in for nested data
    ...
```

### Key Changes

1. **Default read path**: Column-only, no JSON parsing
2. **Opt-in detail methods**: `*_with_details()` for nested data (single query with `undefer`)
3. **`deferred()` on JSON columns**: Prevent accidental loading
4. **Helper methods**: `_bug_to_dict()` / `_test_to_dict()` for reuse

---

## Epic 013: Repository Read Pattern Standardization

**Goal:** Eliminate JSON parsing from default repository reads, using denormalized columns as the single source of truth.

**User Value:** Developers get:
- Predictable, consistent data from all repository methods
- No more "did I remember to override this field?" bugs
- Faster queries for common operations
- Clear separation between basic reads and detail-heavy reads

---

### STORY-076: Add `review_status` Column + Backfill

As a **developer**,
I want **the Test ORM to include a `review_status` column populated from API data**,
So that **this field is available for column-only reads without JSON parsing**.

**Acceptance Criteria:**

**Given** the existing Test ORM
**When** the migration runs
**Then** the `tests` table has a new `review_status` column (VARCHAR, nullable)

**Given** existing test records with `review_status` in their `data` JSON blob
**When** the migration backfill runs
**Then** the `review_status` column is populated with the value from `data`

**Given** a new test sync from the API
**When** `TestRepository.insert_test()` is called
**Then** the `review_status` column is populated from the API response

**Given** the TestRepository
**When** `query_tests()` returns test data
**Then** the response includes `review_status` from the column

**Prerequisites:** None (first story)

**Technical Notes:**
- ORM change in `src/testio_mcp/models/orm/test.py`
- Transformer update to extract `review_status` on sync
- Backfill SQL uses `json_extract(data, '$.review_status')`
- Follow STORY-069 pattern for migration structure

**Files to Modify:**
- `src/testio_mcp/models/orm/test.py`
- `src/testio_mcp/repositories/test_repository.py` (write path)
- `src/testio_mcp/transformers/test_transformers.py`
- `alembic/versions/xxxx_add_review_status_column.py` (new)

---

### STORY-077: BugRepository Column-Only Reads

As a **developer**,
I want **BugRepository to return data built from columns only by default**,
So that **there is no stale data leakage and no JSON parsing overhead**.

**Acceptance Criteria:**

**Given** the Bug ORM definition
**When** reviewing `Bug.raw_data`
**Then** it has `deferred(True)` applied (lazy loading by default)

**Given** a call to `BugRepository.get_bugs()`
**When** executing the query
**Then** the generated SQL does NOT include the `raw_data` column

**Given** a call to `BugRepository.get_bugs()`
**When** results are returned
**Then** each bug dict contains ALL denormalized columns: `id`, `title`, `severity`, `status`, `known`, `reported_at`, `actual_result`, `expected_result`, `rejection_reason`, `steps`, `reported_by_user_id`, `test_feature_id`

**Given** consumers that need nested data (`devices`, `reproductions`, `category`)
**When** calling `BugRepository.get_bugs_with_details()`
**Then** nested fields are included via single query with `undefer(Bug.raw_data)`

**Given** a bug where `raw_data` is NULL (edge case)
**When** calling `get_bugs_with_details()`
**Then** the method handles gracefully (empty nested fields, no crash)

**Given** a sample dataset
**When** comparing old `get_bugs()` output to new `get_bugs()` output
**Then** all non-nested fields match exactly (data equivalence test)

**Given** 100 bugs in the database
**When** measuring `get_bugs()` performance
**Then** column-only read is faster than JSON-parsing read (baseline captured)

**Prerequisites:** None (parallel with STORY-076)

**Technical Notes:**
- **SQLModel `deferred` syntax** (important!):
  ```python
  from sqlalchemy.orm import deferred
  from sqlalchemy import Column, Text
  # Correct pattern for SQLModel:
  raw_data: str = Field(sa_column=deferred(Column(Text)))
  ```
- Create `_bug_to_dict()` helper method
- Use `undefer(Bug.raw_data)` in `get_bugs_with_details()`
- Update `test_service._build_bug_summary()` to use `get_bugs_with_details()`
- Remove dead code: `test_service._aggregate_bug_counts()` if confirmed unused
- **Async I/O safety:** Add test assertion to detect accidental `raw_data` access (see test template)
- **Story splitting:** If implementation exceeds single session, split at natural boundaries (ORM → repo → consumers)

**Files to Modify:**
- `src/testio_mcp/models/orm/bug.py`
- `src/testio_mcp/repositories/bug_repository.py`
- `src/testio_mcp/services/test_service.py` (consumer update)

**Test Template:**
```python
def test_column_only_read_excludes_raw_data(session, repository):
    """Verify default read doesn't load raw_data column."""
    # Capture SQL query via echo=True or event listener
    bugs = await repository.get_bugs(test_id=123)
    assert "raw_data" not in captured_sql

def test_all_denormalized_columns_included(session, repository):
    """Verify all column fields present in output."""
    bugs = await repository.get_bugs(test_id=123)
    required_fields = {"id", "title", "severity", "status", "known", "reported_at",
                       "actual_result", "expected_result", "rejection_reason",
                       "steps", "reported_by_user_id", "test_feature_id"}
    assert required_fields.issubset(bugs[0].keys())

def test_nested_data_only_in_details_method(session, repository):
    """Verify nested fields require opt-in."""
    basic = (await repository.get_bugs(test_id=123))[0]
    assert "devices" not in basic

    detailed = (await repository.get_bugs_with_details(test_id=123))[0]
    assert "devices" in detailed

def test_no_accidental_raw_data_access(session, repository):
    """Detect accidental deferred column access (async I/O safety)."""
    from unittest.mock import PropertyMock, patch
    with patch.object(Bug, 'raw_data', new_callable=PropertyMock) as mock_raw:
        mock_raw.side_effect = AssertionError("raw_data accessed unexpectedly!")
        bugs = await repository.get_bugs(test_id=123)
        # If we reach here without error, raw_data wasn't touched

def test_performance_improvement(session, repository):
    """Verify column-only read meets performance threshold."""
    # Given: 100 bugs in database (setup in fixture)
    # When: get_bugs() called 10 times
    import time
    start = time.perf_counter()
    for _ in range(10):
        await repository.get_bugs(test_id=123)
    elapsed_ms = (time.perf_counter() - start) * 1000
    # Then: Average < 50ms per call (500ms total for 10 calls)
    assert elapsed_ms < 500, f"Performance threshold exceeded: {elapsed_ms}ms"
```

---

### STORY-078: TestRepository Column-Only Reads

As a **developer**,
I want **TestRepository to return data built from columns only by default**,
So that **test data reads are consistent with the BugRepository pattern**.

**Acceptance Criteria:**

**Given** the Test ORM definition
**When** reviewing `Test.data`
**Then** it has `deferred(True)` applied

**Given** a call to `TestRepository.query_tests()`
**When** executing the query
**Then** the generated SQL does NOT include the `data` column

**Given** a call to `TestRepository.query_tests()`
**When** results are returned
**Then** each test dict contains ALL denormalized columns including `review_status` (from STORY-076)

**Given** consumers that need nested data (`requirements` array)
**When** calling `TestRepository.get_tests_with_requirements()`
**Then** requirements are included via single query with `undefer(Test.data)`

**Given** a test where `data` is NULL (edge case)
**When** calling `get_tests_with_requirements()`
**Then** the method handles gracefully (empty requirements, no crash)

**Given** the existing `test_environment` handling
**When** reviewing the column-only read
**Then** `test_environment` is included correctly (it's already a JSON column, not in blob)

**Given** pagination parameters
**When** calling `query_tests()` with limit/offset
**Then** pagination still works correctly with column-only reads

**Prerequisites:** STORY-076 (`review_status` column exists)

**Technical Notes:**
- **SQLModel `deferred` syntax** (same as STORY-077):
  ```python
  from sqlalchemy.orm import deferred
  from sqlalchemy import Column, Text
  data: str = Field(sa_column=deferred(Column(Text)))
  ```
- Create `_test_to_dict()` helper method
- `test_environment` is a separate JSON column, NOT part of `data` blob - handle correctly
- Update `_summarize_requirements()` consumers to use `get_tests_with_requirements()`
- **Story splitting:** If implementation exceeds single session, split at natural boundaries (ORM → repo → consumers)

**Files to Modify:**
- `src/testio_mcp/models/orm/test.py`
- `src/testio_mcp/repositories/test_repository.py`
- `src/testio_mcp/services/test_service.py` (consumer update)
- `src/testio_mcp/services/multi_test_report_service.py` (if uses requirements)

---

### STORY-079: ProductRepository & FeatureRepository Alignment

As a **developer**,
I want **ProductRepository and FeatureRepository to follow the same column-only pattern**,
So that **all repositories have consistent read behavior**.

**Acceptance Criteria:**

**Given** the Product ORM definition
**When** reviewing `Product.data`
**Then** it has `deferred(True)` applied

**Given** the Feature ORM definition
**When** reviewing `Feature.raw_data`
**Then** it has `deferred(True)` applied

**Given** a call to `ProductRepository.get_products()`
**When** results are returned
**Then** each product dict is built from columns only

**Given** a call to `FeatureRepository.get_features()`
**When** results are returned
**Then** each feature dict is built from columns only

**Given** Product and Feature entities
**When** reviewing available columns
**Then** no nested data is needed (simpler than Bug/Test - no `*_with_details` needed)

**Prerequisites:** STORY-077 (pattern established)

**Technical Notes:**
- Product has: `id`, `customer_id`, `title`, `product_type` columns
- Feature has: `id`, `customer_id`, `product_id`, `title`, `description`, `howtofind` columns
- Neither entity needs nested data access for current consumers
- Simpler implementation than Bug/Test

**Files to Modify:**
- `src/testio_mcp/models/orm/product.py`
- `src/testio_mcp/models/orm/feature.py`
- `src/testio_mcp/repositories/product_repository.py`
- `src/testio_mcp/repositories/feature_repository.py`

---

### STORY-080: Fix `reported_at` Field Mapping

As a **developer**,
I want **the bug timestamp field to use `reported_at` consistently**,
So that **there is no confusion between `created_at` and `reported_at`**.

**Acceptance Criteria:**

**Given** the `RecentBug` schema
**When** reviewing field definitions
**Then** `created_at` is renamed to `reported_at`

**Given** `test_service.py` building recent bugs
**When** sorting bugs by timestamp
**Then** it uses `reported_at` (not `created_at`)

**Given** a grep search for `created_at` in bug-related code
**When** reviewing results
**Then** no references remain (grep clean)

**Given** existing tests using `created_at` for bugs
**When** running the test suite
**Then** tests are updated and pass

**Given** API response data
**When** the bug is processed
**Then** `reported_at` timestamp matches the API's `reported_at` field

**Prerequisites:** STORY-077, STORY-078, STORY-079 (repos are column-only, no JSON conflicts)

**Technical Notes:**
- API provides `reported_at`, not `created_at`
- Bug ORM column is already named `reported_at`
- Only schema and service code need updates
- Safe to do after repos are column-only (no JSON field name conflicts)

**Files to Modify:**
- `src/testio_mcp/schemas/api/bugs.py` (`RecentBug` schema)
- `src/testio_mcp/services/test_service.py` (sorting/building)
- `tests/` (any tests referencing `created_at` for bugs)

---

## FR Coverage Matrix

| FR | Stories | Verification |
|----|---------|--------------|
| FR1 | STORY-076 | `review_status` column exists and populated |
| FR2 | STORY-077 | BugRepository default reads are column-only |
| FR3 | STORY-078 | TestRepository default reads are column-only |
| FR4 | STORY-079 | Product/Feature repos are column-only |
| FR5 | STORY-080 | `reported_at` used consistently |
| FR6 | STORY-077, STORY-078 | `*_with_details()` methods exist for nested data |

---

## Acceptance Criteria Template (All Stories)

Per Clink review feedback, each repository story should include:

### SQL Verification
> "The generated SQL SELECT statement must NOT include the `data` or `raw_data` column for default reads."

### Data Equivalence
> "The data returned by the new column-only method must match the expected fields for a sample set of records."

### Performance (Measurable Thresholds)
> **Given:** 100 records in database
> **When:** Default read method called 10 times
> **Then:** Total elapsed time < 500ms (avg 50ms/call)
>
> Baseline JSON parsing typically ~80-100ms/call; column-only should be <50ms.

### Safety
> "The `raw_data`/`data` field should NOT be present in default read output. Detail methods explicitly include nested fields."

### Async I/O Safety
> "Accidental access to deferred column in default read path must be detected by test assertion (no silent lazy loads)."

---

## Summary

**Epic 013** eliminates JSON parsing from repository read paths:

| Layer | Changes |
|-------|---------|
| **ORM** | `deferred()` on JSON columns via `sa_column` |
| **Repository** | Column-only `_to_dict()` helpers, `*_with_details()` for opt-in |
| **Schema** | Field mapping fixes (`reported_at`) |
| **Tests** | SQL verification, data equivalence, performance thresholds, async I/O safety |

**Story Sequence:**
1. STORY-076: Add `review_status` column (foundation)
2. STORY-077: BugRepository column-only (establish pattern) - *can run parallel with 078, 079*
3. STORY-078: TestRepository column-only (apply pattern) - *depends on 076*
4. STORY-079: Product/Feature alignment (complete pattern) - *can run parallel with 077, 078*
5. STORY-080: Fix `reported_at` mapping (cleanup) - *depends on 077, 078, 079*

**Estimated Risk:** Medium (affects all read paths, mitigated by comprehensive tests and test assertions for async I/O safety)

---

## Follow-up Items (Out of Scope)

1. **ADR for this pattern** - Create `ADR-XXX: Repository Read Pattern - Column-Only Defaults`
2. **Performance monitoring** - Add timing logs to refactored methods
3. **Documentation updates** - After stories complete:
   - `CLAUDE.md` - Update SQLModel query patterns section
   - `docs/architecture/ARCHITECTURE.md` - Update repository layer description
4. **`duration` field removal** - Deferred. Field is always NULL but harmless; removal would be breaking API change for zero value. Consumers can use `start_at`/`end_at` if duration calculation needed.

---

## References

- [Planning Document](../planning/repository-read-pattern-standardization.md) - Full analysis and Clink review
- [Epic 012 Tech Debt Section](./epic-012-polish.md#tech-debt-repository-read-pattern-standardization) - Origin of this work
- [ADR-017: Read-Through Caching](../architecture/adrs/ADR-017-read-through-cache-strategy.md) - Related caching decisions
- [Existing DTOs](../../src/testio_mcp/schemas/dtos.py) - Current schema definitions

---

_For implementation: Use the `dev-story` workflow to implement each story sequentially._
