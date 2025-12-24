---
story_id: STORY-019a
epic_id: EPIC-003
title: Core EBR Service Infrastructure
status: superseded
superseded_by: STORY-023e
superseded_date: 2025-11-18
created: 2025-01-07
estimate: 3-4 hours
assignee: dev
dependencies: [STORY-001, STORY-003c, STORY-004, STORY-005, STORY-006, STORY-021, STORY-020]
priority: high
parent_design: story-019-DESIGN.md
estimate_note: Increased from 2-3h to 3-4h to include AC3 shared bug classification helper extraction (~30-45min additional work)
linear_issue: LEO-47
linear_url: https://linear.app/leoric-crown/issue/LEO-47/core-ebr-service-infrastructure
linear_status: Backlog
linear_branch: leonricardo314/leo-47-core-ebr-service-infrastructure
---

## Status
**SUPERSEDED** - Replaced by STORY-023e (Epic 004 - SQLite-First Architecture)

**Reason:** Epic 004 refactoring (STORY-023 series) extracted shared utilities (STORY-023b) and created clean SQLite-first architecture (STORY-023c/d). STORY-023e implements the same EBR functionality on the modern codebase without the InMemoryCache migration complexity.

**What was preserved:**
- ✅ Shared utilities extracted in STORY-023b (bug_classifiers.py, date_utils.py)
- ✅ Repository pattern created in STORY-023c
- ✅ Linear issue LEO-47 tracks this work (implement via STORY-023e)

**See:** `docs/stories/story-023e-multitestreportservice.md` for current implementation plan.

## Story
**As a** CSM
**I want** a service that discovers tests and aggregates bug metrics across multiple tests
**So that** I can generate EBR reports without manually exporting from Tableau

## Acceptance Criteria

### AC1: Create Shared Date Utilities (Filtering + Parsing)
- [ ] Create `src/testio_mcp/utilities/date_filters.py`
- [ ] Extract `filter_tests_by_timeframe()` from ActivityService
- [ ] Extract `is_test_in_timeframe()` from ActivityService
- [ ] Extract `date_in_range()` from ActivityService
- [ ] **Extract `parse_date_input()` from ActivityService** (make public)
- [ ] Refactor ActivityService to use shared utilities
- [ ] Verify all existing ActivityService tests still pass

**Rationale:**
- Avoid code duplication between ActivityService and MultiTestReportService
- **Make `parse_date_input()` public API:** STORY-019c tool layer needs to parse user-provided date strings (e.g., "last 30 days", "Q4 2024") without reaching into service protected methods. Public utility enables clean tool implementation.

### AC2: Create MultiTestReportService
- [ ] File: `src/testio_mcp/services/multi_test_report_service.py`
- [ ] Inherit from `BaseService` (dependency injection, caching)
- [ ] Inject `PersistentCache` (from STORY-021) via constructor
- [ ] Implement `discover_and_fetch_tests()` method:
  - Accept parameters: `product_ids: list[int]`, `start_date: datetime`, `end_date: datetime`, `date_field: str`
  - **Simplified with STORY-021 local store:**
    - Ensure each product is synced: `await cache.sync_product_tests(pid)` (1-2s if new data)
    - Query tests from local store with date filtering: SQL BETWEEN query (~10ms)
    - Process products concurrently using `asyncio.gather` (semaphore-limited)
  - **Return list of test dictionaries with this minimal schema:**
    ```python
    {
        "id": int,
        "title": str,
        "product_id": int,
        "start_at": str | None,  # ISO 8601
        "end_at": str | None,
        "created_at": str | None,
        # ... (full API payload preserved, but above fields guaranteed)
    }
    ```
  - **Raise `NoTestsFoundException` if filters yield zero tests** (see AC8)
  - **Performance:** ~2-5s for fresh sync, ~10-50ms for warm cache
  - **Dependency:** STORY-021 (local store), STORY-020 (simplified pagination service)
- [ ] Implement `aggregate_report_data()` method:
  - Method signature: `async def aggregate_report_data(self, tests: list[dict], product_ids: list[int]) -> dict[str, Any]`
  - Accept parameters: `tests: list[dict]` (test payloads from discover_and_fetch_tests), `product_ids: list[int]` (for querying problematic tests)
  - Fetch all bugs for tests concurrently via client
  - Aggregate bugs across all tests into single list
  - Calculate bug metrics (status buckets, acceptance rates, type/severity distribution)
  - Calculate test metrics (count, date range, velocity)
  - Fetch product names from cache for display
  - **Query problematic tests (Epic 002 integration):**
    - For each product_id, call `cache.get_problematic_tests(product_id)`
    - Aggregate problematic tests across all products
    - Include in `data_quality` section of return dict (see AC5 schema)
  - Return structured dict (NO formatting - data only, see AC5 for schema)

### AC3: Shared Bug Classification Helper (Extract from test_service.py)
- [ ] Create `src/testio_mcp/utilities/bug_classifiers.py`
- [ ] Extract bug classification logic from `test_service.py:201-279` into shared helper:
  ```python
  def classify_bugs(bugs: list[dict]) -> dict[str, int]:
      """Classify bugs into status buckets (mutually exclusive).

      Returns:
          Dictionary with keys: accepted, auto_accepted, rejected, forwarded,
          overall_accepted, reviewed (all int counts)
      """
      # Implementation from test_service.py:201-216
  ```
- [ ] Extract acceptance rate calculations into shared helper:
  ```python
  def calculate_acceptance_rates(
      accepted: int,
      auto_accepted: int,
      rejected: int
  ) -> dict[str, float | None]:
      """Calculate acceptance rates using reviewed bugs as denominator.

      Returns:
          Dictionary with keys: acceptance_rate, auto_acceptance_rate,
          overall_acceptance_rate, rejection_rate (all float | None)
      """
      # Implementation from test_service.py:246-279
  ```
- [ ] Refactor `test_service.py` to use shared helpers (prevents duplication)
- [ ] Use shared helpers in `MultiTestReportService.aggregate_report_data()`
- [ ] Add unit tests for `bug_classifiers.py` (test edge cases: zero bugs, all auto, missing fields)

**Rationale:** Shared utilities ensure consistent bug metrics between `test_service` and `MultiTestReportService`. Prevents metric drift when business logic changes.

### AC3.5: Bug Classification Usage (Reference)
Use shared helpers from AC3. **Original logic** from test_service.py:201-279 (for reference only):

```python
# Status buckets (MUTUALLY EXCLUSIVE)
accepted = 0       # Manual acceptance (status="accepted", auto_accepted!=True)
auto_accepted = 0  # Auto acceptance (status="accepted", auto_accepted=True)
rejected = 0       # status="rejected"
forwarded = 0      # status="forwarded" (pending/open)

# Classify each bug
for bug in bugs:
    if bug["status"] == "accepted":
        if bug.get("auto_accepted") is True:
            auto_accepted += 1  # BAD signal (auto after 10 days)
        else:
            accepted += 1  # GOOD signal (manual or staging)
    elif bug["status"] == "rejected":
        rejected += 1
    elif bug["status"] == "forwarded":
        forwarded += 1

# Derived metrics
overall_accepted = accepted + auto_accepted
reviewed_count = accepted + auto_accepted + rejected  # Excludes forwarded
```

### AC4: Acceptance Rate Calculations (CRITICAL)
Use **reviewed bugs as denominator** (NOT total) - matches test_service.py:246-279:

```python
reviewed_count = accepted + auto_accepted + rejected  # Has been reviewed

if reviewed_count > 0:
    acceptance_rate = accepted / reviewed_count  # Manual only
    auto_acceptance_rate = auto_accepted / reviewed_count  # Auto only
    overall_acceptance_rate = (accepted + auto_accepted) / reviewed_count
    rejection_rate = rejected / reviewed_count
else:
    # No reviewed bugs - return None (avoid division by zero)
    acceptance_rate = None
```

### AC5: Output Schema
Return structured dict matching this schema:

```python
{
    "bug_metrics": {
        # Counts
        "total": 234,
        "accepted": 170,              # Manual only
        "auto_accepted": 15,
        "overall_accepted": 185,      # accepted + auto_accepted
        "rejected": 15,
        "forwarded": 34,
        "reviewed": 200,               # accepted + auto + rejected

        # Rates (denominator = reviewed)
        "acceptance_rate": 0.85,
        "auto_acceptance_rate": 0.075,
        "overall_acceptance_rate": 0.925,
        "rejection_rate": 0.075,

        # Health indicator
        "health": "healthy",          # "healthy" if auto < 0.20 else "warning"

        # Type distribution
        "by_type": {
            "functional": {
                "count": 150,
                "accepted": 120,
                "auto_accepted": 5,
                "overall_accepted": 125,
                "rejected": 10,
                "reviewed": 135,
                "percentage": 0.641,
                "acceptance_rate": 0.889,
                "auto_acceptance_rate": 0.037
            },
            # ... visual, content, custom
        },

        # Severity (functional bugs only)
        "by_severity": {
            "critical": {
                "count": 5,
                "accepted": 4,
                "auto_accepted": 0,
                "percentage": 0.033  # % of functional bugs
            },
            # ... high, low
        }
    },
    "test_metrics": {
        "test_count": 12,
        "earliest_start": "2024-10-01T00:00:00Z",
        "latest_start": "2024-12-28T14:30:00Z",
        "date_range_days": 89,
        "tests_per_week": 0.94,
        "products": ["Product A", "Product B"]
    },
    "data_quality": {
        "has_gaps": true,                # True if any problematic tests exist
        "problematic_tests_count": 2,    # Number of tests that failed to sync
        "problematic_tests": [
            {
                "test_id": null,         # Unknown (couldn't fetch)
                "product_id": 18559,
                "boundary_before_id": 144523,
                "boundary_before_end_at": "2025-10-27T02:00:00+01:00",
                "boundary_after_id": 144472,
                "boundary_after_end_at": "2025-10-24T04:00:00+02:00",
                "position_range": [49, 49],
                "timestamp": "2025-01-07T19:22:19Z",
                "recovery_attempts": 5   # Tried page_size: 25, 10, 5, 2, 1
            }
            # ... additional problematic tests
        ],
        "estimated_missing_bugs": null   # Estimate if possible, else null
    }
}
```

### AC6: Edge Case Handling
- [ ] Zero bugs: Return rates as `None` (avoid division by zero)
- [ ] Missing `auto_accepted` field (staging): Default to manual acceptance
- [ ] Invalid flag combos: Honor `status` field, log warning, ignore flag
- [ ] No functional bugs: Return empty severity dict
- [ ] No reviewed bugs: Return rates as `None`, health as `"unknown"`

### AC7: Health Indicator Calculation (Use Existing Config)
- [ ] Read threshold from `settings.AUTO_ACCEPTANCE_ALERT_THRESHOLD` (default 0.20)
- [ ] Calculate health from `auto_acceptance_rate`:
  - `"healthy"` if `auto_acceptance_rate < AUTO_ACCEPTANCE_ALERT_THRESHOLD`
  - `"warning"` if `auto_acceptance_rate >= AUTO_ACCEPTANCE_ALERT_THRESHOLD`
  - `"unknown"` if `auto_acceptance_rate is None` (no reviewed bugs)
- [ ] Store in `bug_metrics["health"]` field (formatters should not recalculate)
- [ ] Inject settings via constructor: `MultiTestReportService(client, cache, settings)`

**Rationale:** Reuse existing `AUTO_ACCEPTANCE_ALERT_THRESHOLD` from config.py (STORY-005c) instead of introducing duplicate setting. Service owns business logic; formatters should display the pre-calculated health indicator, not recompute it (prevents divergence).

### AC8: Exception Definitions
- [ ] Define `NoTestsFoundException` in `src/testio_mcp/exceptions.py`:
  ```python
  class NoTestsFoundException(Exception):
      """Raised when test discovery yields zero tests after filtering."""
      def __init__(self, product_ids: list[int], start_date: str, end_date: str, date_field: str):
          self.product_ids = product_ids
          self.start_date = start_date
          self.end_date = end_date
          self.date_field = date_field
          super().__init__(f"No tests found for products {product_ids} in date range")
  ```
- [ ] Define `DateParseException` in `src/testio_mcp/exceptions.py`:
  ```python
  class DateParseException(Exception):
      """Raised when date string cannot be parsed."""
      def __init__(self, date_str: str, expected_formats: list[str] | None = None):
          self.date_str = date_str
          self.expected_formats = expected_formats or [
              "ISO 8601 (2024-10-01)",
              "Relative (last 30 days)",
              "Business terms (Q4 2024)"
          ]
          super().__init__(f"Cannot parse date: '{date_str}'")
  ```
- [ ] Raise `NoTestsFoundException` from `discover_and_fetch_tests()` when filtered list is empty
- [ ] Raise `DateParseException` from `parse_date_input()` when date string is invalid

**Rationale:** Provides exception contracts for STORY-019c error handling.

### AC9: Unit Tests
- [ ] File: `tests/services/test_multi_test_report_service.py`
- [ ] Test `discover_and_fetch_tests()` date filtering
- [ ] Test `discover_and_fetch_tests()` raises `NoTestsFoundException` when no tests match
- [ ] Test `aggregate_report_data()` metric calculations
- [ ] Test edge cases (zero bugs, all auto-accepted, missing fields)
- [ ] Test health indicator calculation (healthy/warning/unknown)
- [ ] Test error handling (404, invalid inputs)
- [ ] Test property invariants:
  - All rates in [0,1] or None
  - `overall_accepted = accepted + auto_accepted`
  - `total >= accepted + auto_accepted + rejected`
- [ ] Coverage >80%

## Tasks / Subtasks

- [ ] Task 1: Extract shared date utilities (AC1)
  - [ ] Create src/testio_mcp/utilities/__init__.py
  - [ ] Create src/testio_mcp/utilities/date_filters.py
  - [ ] Copy filter_tests_by_timeframe from ActivityService
  - [ ] Copy is_test_in_timeframe from ActivityService
  - [ ] Copy date_in_range from ActivityService
  - [ ] **Copy parse_date_input from ActivityService (make public API)**
  - [ ] Add type hints and docstrings
  - [ ] Refactor ActivityService to import utilities
  - [ ] Run existing ActivityService tests (verify no breakage)

- [ ] Task 1.5: Extract shared bug classification helpers (AC3 - NEW)
  - [ ] Create src/testio_mcp/utilities/bug_classifiers.py
  - [ ] Extract classify_bugs() from test_service.py:201-216
  - [ ] Extract calculate_acceptance_rates() from test_service.py:246-279
  - [ ] Add type hints and comprehensive docstrings
  - [ ] Create tests/unit/test_bug_classifiers.py
  - [ ] Test edge cases (zero bugs, all auto, missing auto_accepted field)
  - [ ] Refactor test_service.py to use shared helpers
  - [ ] Verify test_service tests still pass

- [ ] Task 2: Create MultiTestReportService skeleton (AC2)
  - [ ] Create src/testio_mcp/services/multi_test_report_service.py
  - [ ] Inherit from BaseService
  - [ ] Add docstring explaining service purpose
  - [ ] Import dependencies (BaseService, date utilities, exceptions)
  - [ ] Add type hints

- [ ] Task 3: Implement discover_and_fetch_tests (AC2)
  - [ ] Add method signature with type hints
  - [ ] Fetch tests for each product concurrently (asyncio.gather)
  - [ ] Filter tests using shared date utilities
  - [ ] Return full test payloads (not IDs)
  - [ ] Add error handling (ProductNotFoundException)

- [ ] Task 4: Implement aggregate_report_data (AC2, AC3, AC4)
  - [ ] Add method signature with type hints
  - [ ] Fetch bugs for all tests concurrently
  - [ ] **Use shared bug helpers** from bug_classifiers.py (AC3):
    - Call `classify_bugs(all_bugs)` for status counts
    - Call `calculate_acceptance_rates(...)` for rate metrics
  - [ ] Calculate type distribution with per-type rates (use shared helpers per type)
  - [ ] Calculate severity analysis (functional bugs only)
  - [ ] Calculate test metrics
  - [ ] Return structured dict (AC5 schema)

- [ ] Task 5: Add edge case handling (AC6)
  - [ ] Zero division guards
  - [ ] Missing auto_accepted field handling
  - [ ] Invalid flag combination logging
  - [ ] Empty functional bugs handling

- [ ] Task 6: Write unit tests (AC9)
  - [ ] Create test file
  - [ ] Mock TestIOClient and PersistentCache (NOT InMemoryCache - removed in STORY-021)
  - [ ] Mock PersistentCache with customer_id filtering behavior
  - [ ] Test discover_and_fetch_tests with date filtering
  - [ ] Test aggregate_report_data with known data
  - [ ] Test edge cases
  - [ ] Test property invariants
  - [ ] **CRITICAL:** Verify that mocked cache queries filter by customer_id
  - [ ] Achieve >80% coverage

## Dev Notes

### Test Discovery: Simplified with STORY-021 Local Store

**SIMPLIFIED APPROACH (STORY-021 First):**

With STORY-021's local SQLite store, test discovery becomes trivial - no complex pagination or parallel-fetch logic needed:

```python
async def discover_and_fetch_tests(
    self,
    product_ids: list[int],
    start_date: datetime,
    end_date: datetime,
    date_field: str
) -> list[dict]:
    """Discover and fetch tests for products in date range.

    Simplified with STORY-021 local store:
    1. Ensure products are synced (1-2s if new data)
    2. Query from SQLite with date filter (~10ms)

    MVP: cache.customer_id is set at init from TESTIO_CUSTOMER_ID env var
    Future (STORY-010): Will accept customer_id parameter per-request
    """
    all_tests = []

    # Ensure each product is synced
    # MVP: cache.sync_product_tests() uses self.customer_id internally
    sync_tasks = [self.cache.sync_product_tests(pid) for pid in product_ids]
    await asyncio.gather(*sync_tasks)

    # Query tests from local store with date filtering
    # MVP: cache.query_tests() filters by self.customer_id automatically
    for product_id in product_ids:
        tests = await self.cache.query_tests(
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            date_field=date_field
        )
        all_tests.extend(tests)

    # Raise exception if no tests found (AC8 contract for STORY-019c)
    if not all_tests:
        raise NoTestsFoundException(product_ids, start_date, end_date, date_field)

    return all_tests
```

**Performance Characteristics:**
- **Cold start (first sync):** 2-5s per product (one-time cost)
- **Warm cache (incremental sync):** 1-2s per product (only fetches new tests)
- **Query from SQLite:** 10-50ms (regardless of dataset size)
- **vs STORY-020 approach:** 1000x faster for queries, no complex pagination logic

**Dependency on STORY-021:**
- `PersistentCache.sync_product_tests(product_id)` - Incremental sync using chronological ordering
- `PersistentCache.query_tests(...)` - SQL query with date filtering (BETWEEN clause)
- See STORY-021 design for cache implementation details

**Why STORY-021 First Makes This Trivial:**
1. ✅ No "parallel-fetch, sequential-filter" complexity
2. ✅ No pagination loops
3. ✅ No cache management (SQLite handles it)
4. ✅ Instant queries after warm-up
5. ✅ ~50% reduction in implementation complexity

### Critical Implementation Patterns

**1. API Data Structure (story-019-DESIGN.md:143-156):**
```python
# API returns TWO fields for accepted bugs:
{
    "status": "accepted" | "rejected" | "forwarded",
    "auto_accepted": true | false | None  # Boolean flag
}

# Classification logic (matches test_service.py:201-216):
if bug["status"] == "accepted":
    if bug.get("auto_accepted") is True:
        auto_accepted += 1  # BAD signal
    else:
        accepted += 1  # GOOD signal
```

**2. Acceptance Rate Denominators (story-019-DESIGN.md:159-163):**
```python
# Use TRIAGED bugs as denominator (matches test_service.py:246-279)
reviewed_count = accepted + auto_accepted + rejected  # Excludes forwarded/open
acceptance_rate = accepted / reviewed_count  # NOT total!
```

**3. Reuse Existing Patterns:**
- Inherit from `BaseService` for caching/DI (ADR-006, ADR-011)
- Follow `test_service.py` bug classification exactly (lines 201-279)
- Extract date utilities from `ActivityService` (avoid duplication)

**4. Concurrency & Caching:**
- Use `asyncio.gather()` for concurrent API calls
- Semaphore limits to 10 concurrent (in BaseService client)
- Cache TTLs: products (1h), tests (5min), bugs (1min)
- Stampede protection via `BaseService._inflight_fetches`

### Source Tree
```
src/testio_mcp/
├── services/
│   ├── base_service.py              # INHERIT: BaseService
│   ├── activity_service.py          # SOURCE: Date filtering logic
│   ├── test_service.py              # REFERENCE: Bug classification (201-279)
│   └── multi_test_report_service.py # NEW
├── utilities/                        # NEW: Create this directory
│   ├── __init__.py                  # NEW
│   └── date_filters.py              # NEW: Shared date utilities

tests/
├── services/
│   └── test_multi_test_report_service.py  # NEW
```

### References
- **Design Doc:** `docs/stories/story-019-DESIGN.md` (lines 284-593)
- **Bug Classification:** test_service.py:201-279
- **Date Filtering:** ActivityService methods
- **ADR-006:** Service Layer Pattern
- **ADR-011:** Extensibility Infrastructure

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-07 | 0.1 | Story created from story-019-DESIGN.md | Sarah (PO) |
| 2025-01-07 | 0.2 | Codex peer review fixes: Added test payload schema, NoTestsFoundException, health indicator calculation, public parse_date_input | Sarah (PO) |
| 2025-01-07 | 0.3 | Integrated STORY-020 pagination pattern: Added parallel-fetch/sequential-filter with early termination, dependency on STORY-020, comprehensive implementation example in Dev Notes | Sarah (PO) |
| 2025-01-07 | 0.4 | Sequencing update: Added STORY-021 dependency (local store first), simplified AC2 and Dev Notes to use SQLite queries instead of complex pagination, reduced estimate from 4-5h to 2-3h | Claude (Dev) |
| 2025-01-07 | 0.5 | Story checklist validation fixes: (1) Enhanced AC1 rationale to explain why parse_date_input must be public API, (2) Added return type hint to aggregate_report_data signature in AC2, (3) Added DateParseException definition to AC8 for STORY-019c error handling contract, (4) Added exception raise example to Dev Notes discover_and_fetch_tests code | Bob (SM) |
| 2025-01-07 | 0.6 | **Codex technical review fixes:** (1) AC3: Replaced duplicated bug classification logic with shared helper extraction (new AC) - creates `bug_classifiers.py` utility to prevent metric drift between test_service and MultiTestReportService, (2) Added Task 1.5 for helper extraction with test coverage, (3) Updated Task 4 to use shared helpers, (4) Increased estimate from 2-3h to 3-4h (+30-45min for extraction work). Prevents maintenance burden of duplicated business logic. | Bob (SM) + Codex |
| 2025-01-07 | 0.7 | **Data quality integration (Epic 002 sync errors):** (1) AC2: Updated aggregate_report_data to query problematic tests from Epic 002 local store and include in data_quality section of output schema, (2) AC5: Added data_quality schema with problematic_tests array including boundary information (test IDs + end_at timestamps) for manual investigation/recovery, (3) Rationale: EBR reports must disclose data gaps prominently when API 500 errors prevent test sync - enables users to manually fix reports with full boundary context, still saves time vs manual Tableau export. No estimate change (queries existing cache.get_problematic_tests interface from STORY-021). | Winston (Architect) |

## Dev Agent Record
*This section will be populated during implementation*

## QA Results
*This section will be populated after QA review*
