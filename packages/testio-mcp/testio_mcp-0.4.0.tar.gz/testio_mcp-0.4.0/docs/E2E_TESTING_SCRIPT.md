# TestIO MCP Server - E2E Testing Script

**Version:** 3.0
**Generated:** 2025-12-03 (Updated with 17 active tools, STORY-084/085 bug tools, STORY-057 summaries)
**Purpose:** Regression test suite for implementation validation with expected outputs

---

## 📖 Document Purpose

**This is a REGRESSION TEST SUITE, not a usability test.**

- **Audience:** QA engineers (human or AI) executing manual tests
- **Purpose:** Verify tools work as documented, catch breaking changes
- **Format:** Step-by-step instructions with expected outputs for validation
- **Scope:** Implementation correctness, data structure integrity, performance benchmarks

**This document provides the "answer key"** - it shows exactly what outputs to expect. This is intentional for regression testing.

**For usability testing** (tool discoverability, parameter clarity, error quality), see:
- `AGENT_USABILITY_TASKS.md` - Task prompts (give to agent)
- `AGENT_USABILITY_EVALUATION.md` - Success criteria & scoring (evaluator only)

---

## 🤖 Execution Guidance for Agents

**All test cases are MANDATORY.** Execute every test in this document.

### Execution Rules

1. **Use MCP tools directly** - Do not use bash commands or file reads. Call the testio-mcp tools via MCP protocol.

2. **Execute ALL tests** - Every test case in every persona section must be run. No sampling or representative subsets.

3. **Continue on failure** - If a test fails, document the failure and continue to the next test. Do not stop at first failure.

4. **Test error cases explicitly** - Tests marked with "Expected Error" MUST be executed to validate error handling. Intentionally trigger errors using invalid IDs as documented.

5. **Document results** - For each test, record:
   - Tool called with parameters
   - Actual response (summary, not full payload)
   - Pass/Fail status with reason if failed
   - Response time (approximate)

### Error Testing Requirements

Error handling tests (e.g., Test 5.1, 5.2) are **mandatory**. You must:
- Call tools with intentionally invalid IDs (e.g., `test_id=999999`)
- Verify error follows 3-part format (❌ ℹ️ 💡)
- Confirm no stack traces are exposed
- Document the actual error message received

### Performance Measurement

- Measure response time for each tool call
- No need to run multiple iterations - single execution is sufficient
- "Cold" vs "warm" cache distinction is noted in test descriptions where relevant
- Target times are guidelines; <5s is acceptable, <2s is target

### Test Completion Criteria

The suite is complete when:
- ✅ All 25 test cases executed (Tests 1.1-1.5, 2.1-2.3, 3.1-3.3, 4.1-4.2, 5.1-5.2, 6.1-6.3, 7.1-7.5)
- ✅ All error handling tests triggered and validated
- ✅ Results documented with pass/fail status
- ✅ Summary report generated with overall pass rate

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Test Suite Overview](#test-suite-overview)
3. [Persona-Based Test Scenarios](#persona-based-test-scenarios)
4. [Validation Criteria](#validation-criteria)
5. [Troubleshooting Guide](#troubleshooting-guide)

---

## Prerequisites

### Environment Setup

1. **MCP Connection:**
   - Ensure testio-mcp server is running and connected
   - Verify connection: Run `/mcp` command and confirm "Connected to testio-mcp"

2. **API Access:**
   - Valid TestIO API token configured in `.env`
   - Access to staging or production environment
   - Network connectivity to TestIO API

3. **Local Database Setup (STORY-021):**
   - SQLite database initialized at `~/.testio-mcp/cache.db` (or custom path from `TESTIO_DB_PATH`)
   - Database synced with at least 1 product (run `uv run python -m testio_mcp sync` if needed)
   - Customer ID configured in `.env` (`TESTIO_CUSTOMER_ID`)

4. **Expected Test Data:**
   - At least 1 product with ID.
   - At least 1 test with bugs. **Note:** Test IDs can differ between staging and production environments. Use `list_tests` to find a valid `test_id` for your environment.
   - Tests with various statuses (initialized, locked, archived, etc.)

### Success Criteria Summary

- ✅ All MCP tools callable without errors
- ✅ Error messages follow 3-part format (❌ ℹ️  💡)
- ✅ Response times <5 seconds for API calls (target: <2s)
- ✅ Local database queries <100ms (imperceptible to users)
- ✅ Data structure integrity (no missing required fields)
- ✅ Pagination working with continuation tokens
- ✅ Database operations functional (sync, query, stats)

---

## Test Suite Overview

### Test Coverage (20 Test Cases)

| Persona | Test Cases | Focus Area |
|---------|-----------|------------|
| **Customer Success Manager** | 5 | Product overview, test status queries |
| **QA Team Leader** | 3 | Database monitoring, EBR reports, file export |
| **Executive/Stakeholder** | 3 | Test listing, pagination, status filtering |
| **Data Analyst** | 2 | Analytics capabilities, dynamic metrics queries (Epic 007) |
| **Support Engineer** | 2 | Error handling, input validation |
| **Integration Tests** | 3 | End-to-end workflows, data persistence |
| **New Tests** | 2 | Advanced pagination scenarios, EBR edge cases |

### Estimated Execution Time: 10-15 minutes

### ⚠️ Tools Removed in Recent Refactoring

The following tools were removed during architecture refactoring (STORY-023d):
- **`get_test_bugs`** - Bug filtering and pagination (replaced by direct API access)
- **`generate_status_report`** - Multi-format report generation (report_service deleted)
- **`get_test_activity_by_timeframe`** - Activity analysis (activity_service deleted)

**Rationale:** Simplified architecture focusing on core product/test query operations. Bug details available via `get_test_summary` tool.

---

## Persona-Based Test Scenarios

## 🎭 Persona 1: Customer Success Manager (Sarah)

**Scenario:** Weekly customer check-in preparation

### Test 1.1: Verify API Connection and Server Health

**Tool:** `get_server_diagnostics`

**Note:** This tool provides consolidated health check including API connectivity, database status, sync history, and storage range. Replaces the deprecated `health_check` and `get_database_stats` tools.

```python
# Execute
mcp__testio-mcp__get_server_diagnostics()

# Expected Result
{
    "api": {
        "connected": true,
        "latency_ms": <float>,
        "product_count": <int>,
        "message": "API connected successfully"
    },
    "database": {
        "size_mb": <float>,
        "path": "<path to .testio-mcp/cache.db>",
        "test_count": <int>,
        "product_count": <int>,
        "bug_count": <int>,
        "feature_count": <int>
    },
    "sync": {
        "last_sync": "<ISO 8601 timestamp>",
        "success_rate_24h": <float>,
        "circuit_breaker_active": <bool>,
        "products_synced": <int>
    },
    "storage": {
        "oldest_test_date": "<ISO 8601 timestamp | null>",
        "newest_test_date": "<ISO 8601 timestamp | null>"
    }
}

# Validation
✅ api.connected = true
✅ api.product_count > 0
✅ database.size_mb > 0
✅ database.test_count > 0
✅ sync.last_sync is valid ISO 8601 timestamp
✅ storage.newest_test_date is populated
✅ response time <2 seconds
```

**Optional: Include sync event history for debugging:**
```python
# Execute with sync events
mcp__testio-mcp__get_server_diagnostics(
    include_sync_events=True,
    sync_event_limit=5
)

# Additional field in response
{
    ...
    "events": [
        {
            "event_id": "<uuid>",
            "event_type": "<string>",
            "timestamp": "<ISO 8601>",
            "status": "<string>",
            "details": {...}
        },
        ...
    ]
}
```

**Pass Criteria:** All validations ✅

---

### Test 1.2: List All Products

**Tool:** `list_products`

```python
# Execute
mcp__testio-mcp__list_products()

# Expected Result
{
    "total_count": <number>,
    "filters_applied": {"search": null, "product_type": null},
    "products": [
        {
            "id": <integer>,
            "name": "<string>",
            "type": "<website|mobile_app_ios|mobile_app_android|streaming_app>",
            "description": "<string|null>",
            "default_section_id": "<integer|null>",
            "sections": "<array>",
            "sections_with_default": "<array>",
            "connection": "<object|null>",
            "remote_device_testing": "<boolean>"
        },
        ...
    ]
}

# Validation
✅ total_count matches products array length
✅ all products have id, name, type fields
✅ filters_applied shows null (no filters)
✅ response time <2 seconds
```

**Pass Criteria:** All validations ✅

---

### Test 1.3: Filter Products by Type

**Tool:** `list_products` with type filter

```python
# Execute - Filter by product type
mcp__testio-mcp__list_products(product_type="mobile_app_ios")

# Expected Result
{
    "total_count": <number (< total products)>,
    "filters_applied": {"search": null, "product_type": "mobile_app_ios"},
    "products": [...]
}

# Validation
✅ total_count <= original total
✅ all products have type = "mobile_app_ios"
✅ filters_applied shows correct filter
```

**Valid Product Types:**
- `website` - Web applications
- `mobile_app_ios` - iOS mobile apps
- `mobile_app_android` - Android mobile apps
- `streaming_app` - Streaming applications (Roku, Apple TV, etc.)

**Note:** Product type parameter uses enum validation. Invalid types are rejected before API call.

**Pass Criteria:** All validations ✅

---

### Test 1.4: Search Products by Keyword

**Tool:** `list_products` with search

```python
# Execute
mcp__testio-mcp__list_products(search="Campaign")

# Expected Result
{
    "total_count": <number>,
    "filters_applied": {"search": "Campaign", "product_type": null},
    "products": [<filtered list>]
}

# Validation
✅ all product names or descriptions contain "Campaign" (case-insensitive)
✅ total_count <= original total
✅ search is case-insensitive
```

**Pass Criteria:** All validations ✅

---

### Test 1.5: Get Test Status with Bug Summary

**Tool:** `get_test_summary`

**Prerequisites:** Know a valid `test_id`. You can find one by using the `list_tests` tool.

```python
# Execute
mcp__testio-mcp__get_test_summary(test_id=<your_test_id>)

# Expected Result
{
    "test": {
        "id": <your_test_id>,
        "title": "<string>",
        "goal": "<string>",
        "testing_type": "<coverage|rapid|focused|usability>",
        "status": "<initialized|running|locked|archived|cancelled|customer_finalized>",
        "review_status": "<string>",
        "requirements": [<array>],
        "product": {"id": <int>, "name": "<string>"}
    },
    "bugs": {
        "total_count": <int>,
        "by_severity": {
            "critical": <int>,
            "high": <int>,
            "low": <int>,
            "visual": <int>,
            "content": <int>,
            "custom": <int>
        },
        "by_status": {
            "active_accepted": <int>,
            "auto_accepted": <int>,
            "total_accepted": <int>,
            "rejected": <int>,
            "open": <int>
        },
        "recent_bugs": [<array of top 3 bugs>]
    }
}

# Validation
✅ test object has all required fields
✅ bug summary has correct structure
✅ total_count matches sum of severity counts (for functional bugs)
✅ recent_bugs array has ≤3 items
```

**Pass Criteria:** All validations ✅

---

## 🔬 Persona 2: QA Team Leader (Marcus)

**Scenario:** Database monitoring and sync status verification

### Test 2.1: Monitor Database Statistics (STORY-060)

**Tool:** `get_server_diagnostics`

**Note:** Database monitoring is now consolidated into `get_server_diagnostics`. The database section provides all storage health metrics. This replaces the deprecated `get_database_stats` tool.

```python
# Execute (after initial sync)
mcp__testio-mcp__get_server_diagnostics()

# Expected Result - Focus on database section
{
    "api": {...},
    "database": {
        "size_mb": <float>,
        "path": "<path to .testio-mcp/cache.db>",
        "test_count": <int>,
        "product_count": <int>,
        "bug_count": <int>,
        "feature_count": <int>
    },
    "sync": {
        "last_sync": "<ISO 8601 timestamp>",
        "success_rate_24h": <float>,
        "circuit_breaker_active": <bool>,
        "products_synced": <int>
    },
    "storage": {
        "oldest_test_date": "<ISO 8601 timestamp | null>",
        "newest_test_date": "<ISO 8601 timestamp | null>"
    }
}

# Validation
✅ database.size_mb > 0
✅ database.product_count > 0
✅ database.test_count > 0
✅ database.bug_count >= 0
✅ database.feature_count >= 0
✅ sync.last_sync is valid ISO 8601 timestamp
✅ sync.products_synced > 0
✅ response time <0.5 seconds (local database query + API ping)
```

**Pass Criteria:** All validations ✅

---

### Test 2.2: Generate Evidence-Based Review (EBR) Report

**Tool:** `get_product_quality_report`

**Prerequisites:** A product with completed tests (use product ID 18559 - Canva Monoproduct with historical test data)

**Purpose:** Validate EBR report generation for quality metrics analysis and quarterly reviews

```python
# Execute - Generate EBR report for Q4 2025 (July-December)
mcp__testio-mcp__get_product_quality_report(
    product_id=18559,
    start_date="2025-07-01",
    end_date="2025-12-31"
)

# Expected Result Structure
{
    "summary": {
        "total_tests": <int>,
        "tests_by_status": {
            "locked": <int>,
            "archived": <int>,
            "customer_finalized": <int>
        },
        "statuses_applied": ["running", "locked", "archived", "customer_finalized"],  # Excludes initialized, cancelled
        "total_bugs": <int>,
        "bugs_by_status": {
            "active_accepted": <int>,
            "auto_accepted": <int>,
            "rejected": <int>,
            "open": <int>
        },
        "total_accepted": <int>,
        "reviewed": <int>,
        "active_acceptance_rate": <float>,      # active_accepted / reviewed
        "auto_acceptance_rate": <float>,        # auto_accepted / total_accepted
        "overall_acceptance_rate": <float>,     # total_accepted / total_bugs
        "rejection_rate": <float>,              # rejected / total_bugs
        "review_rate": <float>,                 # reviewed / total_bugs
        "period": "2025-07-01 to 2025-12-31"
    },
    "by_test": [
        {
            "test_id": <int>,
            "title": "<string>",
            "status": "<locked|archived|customer_finalized>",
            "start_at": "<ISO 8601 timestamp>",
            "end_at": "<ISO 8601 timestamp>",
            "bugs_count": <int>,
            "bugs": {
                "active_accepted": <int>,
                "auto_accepted": <int>,
                "rejected": <int>,
                "open": <int>,
                "total_accepted": <int>,
                "reviewed": <int>
            },
            "active_acceptance_rate": <float|null>,  # null if no reviewed bugs
            "auto_acceptance_rate": <float|null>,    # null if no accepted bugs
            "overall_acceptance_rate": <float|null>, # null if no bugs
            "rejection_rate": <float|null>,
            "review_rate": <float|null>
        },
        ...
    ]
}

# Validation (Summary Level)
✅ total_tests > 0 (tests found in date range)
✅ tests_by_status contains counts for executed tests only
✅ statuses_applied = ["running", "locked", "archived", "customer_finalized"]
✅ total_bugs = sum of all bug statuses
✅ total_accepted = active_accepted + auto_accepted
✅ reviewed = total_bugs - open
✅ active_acceptance_rate between 0.0 and 1.0 (or null)
✅ auto_acceptance_rate between 0.0 and 1.0 (or null)
✅ overall_acceptance_rate between 0.0 and 1.0
✅ rejection_rate + overall_acceptance_rate ≤ 1.0 (may not sum to 1.0 due to open bugs)
✅ review_rate between 0.0 and 1.0
✅ period matches input date range

# Validation (Per-Test Level)
✅ by_test array contains test summaries
✅ each test has test_id, title, status, timestamps
✅ each test has bugs breakdown with acceptance rates
✅ acceptance rates are null for tests with no bugs
✅ auto_acceptance_rate is null if no accepted bugs

# Edge Cases to Test
# ---------------------

# Test 1: No status filter (default excludes initialized/cancelled)
result = mcp__testio-mcp__get_product_quality_report(
    product_id=18559,
    start_date="2025-11-01",
    end_date="2025-11-30"
)
✅ statuses_applied = ["running", "locked", "archived", "customer_finalized"]
✅ No initialized or cancelled tests in results

# Test 2: Explicit status filter (overrides default)
result = mcp__testio-mcp__get_product_quality_report(
    product_id=18559,
    start_date="2025-11-01",
    end_date="2025-11-30",
    statuses=["archived"]
)
✅ Only archived tests returned
✅ statuses_applied = ["archived"]

# Test 3: Date range with no tests
result = mcp__testio-mcp__get_product_quality_report(
    product_id=18559,
    start_date="2020-01-01",
    end_date="2020-01-31"
)
✅ total_tests = 0
✅ total_bugs = 0
✅ by_test array is empty []

# Test 4: Tests with no bugs
✅ Tests with bugs_count = 0 have null acceptance rates
✅ Review_rate is null for tests with zero bugs
```

**Acceptance Rate Formulas (for validation):**
```
active_acceptance_rate = active_accepted / reviewed
auto_acceptance_rate = auto_accepted / total_accepted  # null if no accepted
overall_acceptance_rate = total_accepted / total_bugs
rejection_rate = rejected / total_bugs
review_rate = reviewed / total_bugs  # reviewed = total_bugs - open
```

**Default Status Filtering:**
- **Default behavior:** Excludes `initialized` (not executed) and `cancelled` (aborted) tests
- **Rationale:** Only include tests that were actually executed and reviewed
- **Override:** Pass explicit `statuses` parameter to include/exclude specific statuses

**Performance Characteristics:**
- **Cold start (261 tests, 0% cache hit):** ~60-70s (fetches bugs for all tests from API)
- **Warm cache (100% hit):** ~1-2s (all bugs retrieved from SQLite)
- **Partial cache (50% hit):** ~30-35s (half from cache, half from API)
- **Real example (from logs):**
  - Product 18559, 261 tests, 2541 bugs
  - 0% cache hit (all from API): 64 seconds
  - API calls: 18 batch requests (15 test IDs per batch)
- **Caching strategy:**
  - Immutable tests (archived/cancelled): Cached in SQLite indefinitely
  - Mutable tests (running/locked): Refreshed if >1 hour old
  - Use `force_refresh_bugs=true` for guaranteed fresh data (bypasses cache completely)

**Pass Criteria:** All validations ✅, acceptance rate calculations correct

---

### Test 2.3: Generate EBR Report with File Export (STORY-025)

**Tool:** `get_product_quality_report` with `output_file` parameter

**Prerequisites:** A product with many tests (use product ID 18559 - Canva Monoproduct with 260+ tests)

**Purpose:** Validate file export functionality for large reports that exceed MCP token limits

```python
# Execute - Export EBR report to file
mcp__testio-mcp__get_product_quality_report(
    product_id=18559,
    start_date="2025-07-01",
    end_date="2025-10-15",
    output_file="canva-ebr-q3-2025.json"
)

# Expected Result (File Metadata Response)
{
    "summary": {
        "total_tests": <int>,
        "tests_by_status": {
            "locked": <int>,
            "archived": <int>
        },
        "statuses_applied": ["running", "locked", "archived", "customer_finalized"],
        "total_bugs": <int>,
        "bugs_by_status": {
            "active_accepted": <int>,
            "auto_accepted": <int>,
            "rejected": <int>,
            "open": <int>
        },
        "total_accepted": <int>,
        "reviewed": <int>,
        "active_acceptance_rate": <float>,
        "auto_acceptance_rate": <float>,
        "overall_acceptance_rate": <float>,
        "rejection_rate": <float>,
        "review_rate": <float>,
        "period": "2025-07-01 to 2025-10-15"
    },
    "file_path": "/Users/username/.testio-mcp/reports/canva-ebr-q3-2025.json",
    "record_count": <int>,  # Number of tests in file
    "file_size_bytes": <int>,  # File size
    "format": "json"
}

# Validation (Response Structure)
✅ Response contains file_path (absolute path)
✅ Response contains summary (aggregate metrics only)
✅ Response contains record_count (matches total_tests)
✅ Response contains file_size_bytes (> 0)
✅ Response contains format = "json"
✅ Response does NOT contain by_test array (omitted for file export)
✅ Response does NOT contain cache_stats (omitted for file export)

# Validation (File Contents)
# Open the file at file_path and verify:
✅ File exists at specified path
✅ File is valid JSON (can be parsed)
✅ File contains "summary" key
✅ File contains "by_test" array (full test details)
✅ File contains "cache_stats" object
✅ by_test array length matches record_count
✅ File is formatted with indentation (readable)
✅ File size matches file_size_bytes in response

# Validation (Summary Consistency)
✅ summary.total_tests in response matches file summary
✅ summary.total_bugs in response matches file summary
✅ summary.overall_acceptance_rate matches file summary

# Path Resolution Tests
# ---------------------

# Test 1: Relative path (default location)
result = mcp__testio-mcp__get_product_quality_report(
    product_id=18559,
    output_file="test-report.json"
)
✅ file_path = "/Users/username/.testio-mcp/reports/test-report.json"
✅ File created in default reports directory

# Test 2: Subdirectory (auto-created)
result = mcp__testio-mcp__get_product_quality_report(
    product_id=18559,
    output_file="q3-2025/canva.json"
)
✅ file_path = "/Users/username/.testio-mcp/reports/q3-2025/canva.json"
✅ Parent directory q3-2025 created automatically

# Test 3: Absolute path
result = mcp__testio-mcp__get_product_quality_report(
    product_id=18559,
    output_file="/tmp/reports/test.json"
)
✅ file_path = "/tmp/reports/test.json"
✅ Absolute path used as-is

# Security Tests
# --------------

# Test 4: Path traversal attempt (should fail)
try:
    result = mcp__testio-mcp__get_product_quality_report(
        product_id=18559,
        output_file="../../../etc/passwd"
    )
    ❌ FAIL - Should have raised error
except ToolError as e:
    ✅ Error message contains "Invalid output file path"
    ✅ Error explains path traversal not allowed
    ✅ Error suggests using .json extension

# Test 5: Invalid extension (should fail)
try:
    result = mcp__testio-mcp__get_product_quality_report(
        product_id=18559,
        output_file="report.csv"
    )
    ❌ FAIL - Should have raised error
except ToolError as e:
    ✅ Error message contains "Unsupported file extension"
    ✅ Error lists supported extensions (.json)

# Performance Characteristics
# ---------------------------
✅ File write time <1 second for 200+ tests
✅ File export doesn't slow down report generation
✅ Response time similar to non-export mode
✅ File overwrite succeeds (existing file replaced)

# Use Cases
# ---------

# Use Case 1: Large product (>100 tests) - avoid token limits
# Canva Monoproduct: 260 tests, 2541 bugs
# JSON response would be ~150KB (exceeds 25K token limit)
# File export: Returns metadata only (~1KB response)

# Use Case 2: Stakeholder sharing
# Export to file, email to stakeholders for Excel/Sheets import
# File is formatted JSON (indent=2) for readability

# Use Case 3: Historical archiving
# Export quarterly reports to timestamped files
# Example: "canva-ebr-2025-q3.json", "canva-ebr-2025-q4.json"
```

**Benefits of File Export:**
- ✅ No token limits (files can be any size)
- ✅ Complete data in single file (no pagination)
- ✅ Easy import to Excel/Google Sheets
- ✅ Shareable with stakeholders (email file)
- ✅ Historical archiving (timestamped files)
- ✅ Backward compatible (output_file is optional)

**Default Reports Directory:**
- Relative paths: `~/.testio-mcp/reports/`
- Absolute paths: Used as-is
- Parent directories: Created automatically

**Pass Criteria:** All validations ✅, file export working correctly, security checks pass

---

## 💼 Persona 3: Executive/Stakeholder (Jennifer)

**Scenario:** Product portfolio management and test status overview



### Test 3.1: Filter Tests by Status with Pagination (STORY-020)

**Tool:** `list_tests` with status filter and pagination

**Prerequisites:** A valid Product ID.

```python
# Execute - Pass status values as JSON array with pagination
mcp__testio-mcp__list_tests(
    product_id=<your_product_id>,
    statuses=["locked", "archived"],  # JSON array format required
    page=1,                            # Default: 1
    per_page=50,                       # Default: 100 (from TESTIO_DEFAULT_PAGE_SIZE)
    offset=0                           # Default: 0 (optional flexible pagination)
)

# Expected Result (STORY-020 Structure)
{
    "product": {
        "id": <int>,
        "name": "<string>",
        "type": "<string>"
    },
    "statuses_filter": ["locked", "archived"],
    "pagination": {
        "page": 1,
        "per_page": 50,
        "offset": 0,
        "start_index": 0,              # First item index (zero-based)
        "end_index": 49,               # Last item index (or -1 if no results)
        "total_count": <int>,          # Total matching tests (all pages)
        "has_more": <bool>             # True if results == per_page (heuristic)
    },
    "total_tests": <int>,              # Count in current page (≤ per_page)
    "tests": [...]
}

# Validation
✅ all tests have status in ["locked", "archived"]
✅ statuses_filter shows correct filters
✅ pagination.total_count shows total matching tests (all pages)
✅ pagination.start_index = 0 (first page with offset=0)
✅ pagination.end_index = total_tests - 1 (or -1 if empty)
✅ pagination.has_more = true if total_tests == per_page
✅ total_tests ≤ per_page (items in current page)
✅ response time <100ms (local database query)
```

**Pagination Use Cases (STORY-020):**

1. **Basic Pagination:**
   ```python
   # Page 1
   list_tests(product_id=123, page=1, per_page=100)
   # Page 2
   list_tests(product_id=123, page=2, per_page=100)
   ```

2. **Flexible Pagination with Offset (Optimization Pattern):**
   ```python
   # Step 1: Get small sample to check total_count
   result = list_tests(product_id=123, page=1, per_page=10)
   # Shows: "Showing items 0-9 of 247 total"

   # Step 2: If many results, fetch larger page with offset
   result = list_tests(product_id=123, page=1, per_page=100, offset=10)
   # Shows: "Showing items 10-109 of 247 total"
   # (Skips first 10 already seen, gets next 100)
   ```

3. **Status Filtering:**
   ```python
   # Active tests only
   list_tests(product_id=123, statuses=["running"], page=1, per_page=50)

   # Completed tests
   list_tests(product_id=123, statuses=["archived", "locked"], page=1, per_page=100)
   ```

**Common Status Patterns:**
- Active tests: `statuses=["running"]`
- Completed tests: `statuses=["archived", "locked", "customer_finalized"]`
- Active + pending: `statuses=["running", "initialized"]`
- Customer-approved only: `statuses=["customer_finalized"]`

**Pagination Math (Repository Owns This):**
- Formula: `actual_offset = offset + (page - 1) * per_page`
- Example: `page=2, per_page=50, offset=10` → `actual_offset = 10 + (2-1)*50 = 60`
- Display: `start_index = actual_offset`, `end_index = actual_offset + count - 1`

**Performance Characteristics:**
- Cold start: 2-5s (initial product sync if not cached)
- Warm cache: 10-50ms (SQL query with LIMIT/OFFSET)
- Count query: +5ms overhead (one-time per request, same WHERE clause)

**Note:** Parameter requires JSON array format. Valid status values: `running`, `locked`, `archived`, `cancelled`, `customer_finalized`, `initialized`.

**Pass Criteria:** All validations ✅

---

### Test 3.2: Advanced Pagination - Offset Combinations (STORY-020)

**Tool:** `list_tests` with offset and page combinations

**Prerequisites:** A product with at least 20 tests (use product ID 18559 - Canva Monoproduct with 659 tests)

**Purpose:** Verify pagination math, offset handling, and index calculation

```python
# Scenario 1: Basic multi-page navigation
# ========================================

# Step 1: Page 1 (items 0-9)
result1 = mcp__testio-mcp__list_tests(
    product_id=18559,
    page=1,
    per_page=10
)

# Validation
✅ pagination.start_index = 0
✅ pagination.end_index = 9 (or total_tests - 1 if fewer than 10)
✅ pagination.page = 1
✅ pagination.per_page = 10
✅ pagination.offset = 0
✅ total_tests ≤ 10

# Step 2: Page 2 (items 10-19)
result2 = mcp__testio-mcp__list_tests(
    product_id=18559,
    page=2,
    per_page=10
)

# Validation
✅ pagination.start_index = 10
✅ pagination.end_index = 19 (or total_tests - 1 if fewer)
✅ pagination.page = 2
✅ no overlap with Page 1 results (verify test_ids differ)

# Scenario 2: Offset + Page combination (Optimization pattern)
# =============================================================

# Step 1: Small sample (items 0-4)
sample = mcp__testio-mcp__list_tests(
    product_id=18559,
    page=1,
    per_page=5
)

# Step 2: Skip sample, fetch larger page (items 5-54)
batch = mcp__testio-mcp__list_tests(
    product_id=18559,
    page=1,
    per_page=50,
    offset=5
)

# Validation
✅ batch.pagination.start_index = 5  # Starts after sample
✅ batch.pagination.end_index = 54 (or fewer if not enough tests)
✅ batch.pagination.offset = 5
✅ first test in batch != any test in sample (no overlap)
✅ actual_offset calculation: 5 + (1-1)*50 = 5 ✅

# Scenario 3: Complex offset + multi-page
# ========================================

# Fetch items 20-29 using offset + page 2
result = mcp__testio-mcp__list_tests(
    product_id=18559,
    page=2,
    per_page=5,
    offset=10
)

# Validation
✅ pagination.start_index = 15  # offset(10) + (page-1)*per_page = 10 + 5 = 15
✅ pagination.end_index = 19 (or fewer)
✅ actual_offset = 10 + (2-1)*5 = 15 ✅

# Scenario 4: Edge cases
# ======================

# Test with offset beyond results (expect empty or partial)
edge = mcp__testio-mcp__list_tests(
    product_id=18559,
    page=1,
    per_page=10,
    offset=9999
)

# Validation
✅ total_tests = 0 (offset beyond available data)
✅ pagination.start_index = 9999
✅ pagination.end_index = -1 (no results)
✅ tests array is empty []
```

**Pagination Math Reference:**
```
actual_offset = offset + (page - 1) * per_page
start_index = actual_offset
end_index = actual_offset + total_tests - 1 (or -1 if no results)
```

**Pass Criteria:** All validations ✅, no duplicate results across pages

---

### Test 3.3: Pagination with Status Filtering (Combined)

**Tool:** `list_tests` with status filter + pagination

**Prerequisites:** Product with tests in multiple statuses

```python
# Get all archived tests with pagination
page1 = mcp__testio-mcp__list_tests(
    product_id=18559,
    statuses=["archived"],
    page=1,
    per_page=20
)

# Validation
✅ all tests have status = "archived"
✅ pagination.total_count = total archived tests (all pages)
✅ pagination.has_more indicates if more pages exist
✅ statuses_filter = ["archived"]

# If has_more = true, fetch page 2
if page1["pagination"]["has_more"]:
    page2 = mcp__testio-mcp__list_tests(
        product_id=18559,
        statuses=["archived"],
        page=2,
        per_page=20
    )

    # Validation
    ✅ pagination.start_index = 20
    ✅ no overlap with page1 (verify test_ids)
    ✅ all tests still have status = "archived"
```

**Pass Criteria:** All validations ✅, status filter applied correctly across pages

---

## 📊 Persona 4: Data Analyst (Rachel)

**Scenario:** Testing quality metrics analysis and trend identification

### Test 4.1: Discover Analytics Capabilities

**Tool:** `get_analytics_capabilities`

**Purpose:** Verify dimension and metric discovery for dynamic analytics queries

```python
# Execute
mcp__testio-mcp__get_analytics_capabilities()

# Expected Result
{
    "dimensions": [
        {
            "key": "feature",
            "description": "Group by Feature Title",
            "example": "Login, Signup, Dashboard"
        },
        {
            "key": "tester",
            "description": "Group by Tester Username",
            "example": "alice, bob, charlie"
        },
        {
            "key": "month",
            "description": "Group by Month (YYYY-MM)",
            "example": "2025-01, 2025-02"
        },
        {
            "key": "week",
            "description": "Group by ISO Week (YYYY-WW)",
            "example": "2025-W01, 2025-W02"
        },
        {
            "key": "product",
            "description": "Group by Product Name",
            "example": "My App, Test Product"
        },
        {
            "key": "customer",
            "description": "Group by Customer Name",
            "example": "Acme Corp, Test Co"
        },
        {
            "key": "severity",
            "description": "Group by Bug Severity",
            "example": "critical, high, low"
        },
        {
            "key": "status",
            "description": "Group by Test Status",
            "example": "running, locked, archived"
        }
    ],
    "metrics": [
        {
            "key": "bug_count",
            "description": "Total number of bugs found",
            "formula": "COUNT(DISTINCT bug_id)"
        },
        {
            "key": "test_count",
            "description": "Total number of tests executed",
            "formula": "COUNT(DISTINCT test_id)"
        },
        {
            "key": "bugs_per_test",
            "description": "Ratio of bugs to tests (fragility metric)",
            "formula": "bug_count / NULLIF(test_count, 0)"
        },
        {
            "key": "bug_severity_score",
            "description": "Weighted bug severity score",
            "formula": "SUM(CASE severity WHEN 'critical' THEN 10 WHEN 'high' THEN 5 ELSE 1 END)"
        },
        {
            "key": "features_tested",
            "description": "Count of unique features tested",
            "formula": "COUNT(DISTINCT feature_id)"
        },
        {
            "key": "active_testers",
            "description": "Count of unique testers who found bugs",
            "formula": "COUNT(DISTINCT tester_username)"
        }
    ],
    "limits": {
        "max_dimensions": 2,
        "max_rows": 1000,
        "timeout_seconds": 90
    }
}

# Validation
✅ dimensions array has 8 entries
✅ each dimension has key, description, example
✅ dimension keys include: feature, tester, month, week, product, customer, severity, status
✅ metrics array has 6 entries
✅ each metric has key, description, formula
✅ metric keys include: bug_count, test_count, bugs_per_test, bug_severity_score, features_tested, active_testers
✅ limits show max_dimensions=2, max_rows=1000, timeout_seconds=90
```

**Pass Criteria:** All validations ✅, all dimensions and metrics documented

---

### Test 4.2: Query Metrics - Feature Fragility Analysis

**Tool:** `query_metrics`

**Purpose:** Verify dynamic analytics queries with dimensions, metrics, filters, and sorting

**⚠️ BREAKING CHANGE (v0.3.0):** `query_metrics` now excludes initialized and cancelled tests by default. This matches `get_product_quality_report` behavior for consistency.

To include ALL tests (override default filter):
```python
mcp__testio-mcp__query_metrics(
    metrics=["bug_count"],
    dimensions=["feature"],
    filters={"status": ["initialized", "cancelled", "running", "locked", "archived", "customer_finalized"]}
)
```

```python
# Execute - Find most fragile features (highest bugs per test ratio)
mcp__testio-mcp__query_metrics(
    metrics=["bugs_per_test", "bug_count", "test_count"],
    dimensions=["feature"],
    sort_by="bugs_per_test",
    sort_order="desc"
)

# Expected Result Structure
{
    "data": [
        {
            "feature_id": <int>,
            "feature": "<string>",
            "bugs_per_test": <float>,
            "bug_count": <int>,
            "test_count": <int>
        },
        ...
    ],
    "metadata": {
        "query_time_ms": <int>,
        "total_rows": <int>,
        "dimensions_used": ["feature"],
        "metrics_used": ["bugs_per_test", "bug_count", "test_count"]
    },
    "query_explanation": "<string>",
    "warnings": [<optional list of strings>]
}

# Validation (Response Structure)
✅ data array contains feature metrics
✅ each row has feature_id, feature (both ID and display name)
✅ each row has all 3 requested metrics
✅ data is sorted by bugs_per_test descending (highest first)
✅ metadata.total_rows matches data array length
✅ metadata.dimensions_used = ["feature"]
✅ metadata.metrics_used = ["bugs_per_test", "bug_count", "test_count"]
✅ metadata.query_time_ms >= 0
✅ query_explanation contains human-readable summary
✅ query_explanation mentions "bugs_per_test" and "feature"

# Validation (Data Quality)
✅ bugs_per_test values are floats (ratio metric)
✅ bug_count values are integers (count metric)
✅ test_count values are integers (count metric)
✅ bugs_per_test = bug_count / test_count (formula validation)
✅ no null values in required fields
✅ feature names are descriptive strings

# Advanced Queries to Test
# ---------------------------

# Query 1: Tester leaderboard for critical bugs
result = mcp__testio-mcp__query_metrics(
    metrics=["bug_count"],
    dimensions=["tester"],
    filters={"severity": "critical"},
    sort_by="bug_count",
    sort_order="desc"
)
✅ Only critical severity bugs counted
✅ Sorted by bug_count descending
✅ query_explanation mentions "severity=critical"

# Query 2: Monthly testing volume trend
result = mcp__testio-mcp__query_metrics(
    metrics=["test_count", "bug_count"],
    dimensions=["month"],
    start_date="2025-07-01",
    end_date="2025-10-31",
    sort_by="month",
    sort_order="asc"
)
✅ Only tests in date range (Jul-Oct 2025)
✅ Sorted by month ascending (chronological)
✅ query_explanation mentions date range

# Query 3: Multi-dimensional (feature + month)
result = mcp__testio-mcp__query_metrics(
    metrics=["bug_count"],
    dimensions=["feature", "month"]
)
✅ Rows grouped by both feature and month
✅ Each row has feature_id, feature, month, bug_count

# Query 4: Validation error (too many dimensions)
try:
    result = mcp__testio-mcp__query_metrics(
        metrics=["bug_count"],
        dimensions=["feature", "month", "severity"]  # 3 dimensions (max is 2)
    )
    ❌ FAIL - Should have raised error
except ToolError as e:
    ✅ Error message contains "Too many dimensions"
    ✅ Error explains max is 2
    ✅ Error suggests using get_analytics_capabilities()

# Query 5: Invalid dimension key
try:
    result = mcp__testio-mcp__query_metrics(
        metrics=["bug_count"],
        dimensions=["invalid_dimension"]
    )
    ❌ FAIL - Should have raised error
except ToolError as e:
    ✅ Error message contains "Invalid dimensions"
    ✅ Error lists invalid key
    ✅ Error suggests using get_analytics_capabilities()
```

**Performance Characteristics:**
- Typical query time: <2 seconds
- Complex queries (multi-dimension, large date range): <5 seconds
- Query timeout: 90 seconds (inherits HTTP_TIMEOUT_SECONDS)
- Result limit: 1000 rows (hard limit)

**Pass Criteria:** All validations ✅, queries return correct data, error handling works

---

## 🔧 Persona 5: Support Engineer (David)

**Scenario:** System resilience and error handling verification

### Test 5.1: Invalid Test ID Error Handling

**Tool:** `get_test_summary` with invalid ID

```python
# Execute
mcp__testio-mcp__get_test_summary(test_id=999999)

# Expected Error (ToolError exception)
❌ Test ID '999999' not found
ℹ️  The test may have been deleted, archived, or you may not have access to it
💡 Verify the test ID is correct and the test still exists

# Validation
✅ Error message follows 3-part format (❌ ℹ️  💡)
✅ "What went wrong" is clear
✅ "Why it happened" provides context
✅ "How to fix" gives actionable guidance
✅ No stack traces exposed to user
```

**Pass Criteria:** All validations ✅

---

### Test 5.2: Invalid Product ID Error

**Tool:** `list_tests` with invalid product

```python
# Execute
mcp__testio-mcp__list_tests(product_id=999999)

# Expected Error
❌ Product ID '999999' not found
ℹ️  The product may have been deleted or you may not have access to it
💡 Verify the product ID is correct and the product still exists

# Validation
✅ 3-part error format
✅ Clear error message
✅ Actionable guidance
```

**Pass Criteria:** All validations ✅

---

## 🔗 Integration Tests

### Test 6.1: Database Persistence After Sync

**Workflow:** Verify local database persists data across queries (no unnecessary API calls)

```python
# Step 1: Get initial database stats
stats1 = mcp__testio-mcp__get_database_stats()

# Capture initial values
initial_tests = stats1["total_tests"]
initial_size_mb = stats1["database_size_mb"]

# Step 2: Query product tests (should hit local DB, not API)
tests = mcp__testio-mcp__list_tests(product_id=<your_product_id>)

# Step 3: Get stats again (should be unchanged - no new API sync)
stats2 = mcp__testio-mcp__get_database_stats()

# Validation (database persistence)
✅ stats1["total_tests"] == stats2["total_tests"]  # No new tests synced
✅ stats1["database_size_mb"] == stats2["database_size_mb"]  # Size unchanged
✅ list_tests query time <100ms  # Local database query (fast)
✅ No API calls made during list_tests (verify via server logs)
```

**Pass Criteria:** All validations ✅

---

### Test 6.2: Product Search and Test Retrieval

**Workflow:** End-to-end discovery workflow

```python
# Step 1: Search for products
products = mcp__testio-mcp__list_products(search="Ana")

# Step 2: Get first product's tests
product_id = products["products"][0]["id"]
tests = mcp__testio-mcp__list_tests(product_id=product_id)

# Step 3: Get test details
test_id = tests["tests"][0]["test_id"]
test_status = mcp__testio-mcp__get_test_summary(test_id=test_id)

# Validation
✅ Product search returns relevant products
✅ Product ID from search works in list_tests
✅ Test ID from list works in get_test_summary
✅ All data consistent across calls
```

**Pass Criteria:** All validations ✅

---

### Test 6.3: Get Problematic Tests that Failed to Sync (STORY-021e)

**Workflow:** View tests that failed to sync with 500 errors

**Prerequisites:** None (test passes even with empty results)

```python
# Execute
mcp__testio-mcp__get_problematic_tests()

# Expected Result
{
    "count": <int>,
    "tests": [
        {
            "product_id": <int>,
            "page": <int>,
            "position_range": "<string>",
            "recovery_attempts": <int>,
            "reason": "<string>",
            "boundary_before_id": <int>,
            "boundary_before_end_at": "<ISO 8601>",
            "sync_mode": "<string>",
            "command_run_at": "<ISO 8601>",
            "boundary_after_id": <int>,
            "boundary_after_end_at": "<ISO 8601>",
            "event_id": "<uuid>"
        },
        ...
    ],
    "message": "<string>"
}

# Validation
✅ count >= 0
✅ tests array structure correct
✅ each test has product_id, page, position_range
✅ No error raised even if no problematic tests exist
```

**Pass Criteria:** All validations ✅

---

## 🔍 New Test Cases (v3.0)

### Test 7.1: Full-Text Search Discovery (Epic 010)

**Tool:** `search`

**Prerequisites:** None (searches across all entities in local database)

**Purpose:** Verify full-text search with BM25 ranking across products, features, tests, and bugs

```python
# Execute - Search for keyword across all entities
mcp__testio-mcp__search(
    query="login",
    entities=["product", "feature", "test", "bug"],
    limit=20
)

# Expected Result
{
    "query": "login",
    "total": <int>,
    "results": [
        {
            "entity_type": "feature",
            "entity_id": <int>,
            "title": "<string containing 'login'>",
            "score": <float>,  # BM25 relevance score
            "rank": <int>      # 1 = best match
        },
        ...
    ]
}

# Validation
✅ Results contain entities matching "login"
✅ Results ranked by BM25 score (descending)
✅ Each result has entity_type, entity_id, title, score, rank
✅ Total count matches or exceeds results length
✅ Response time <2 seconds

# Advanced Search Tests
# --------------------

# Test 1: Filter by entity type
result = mcp__testio-mcp__search(
    query="authentication",
    entities=["feature", "bug"],
    limit=10
)
✅ Only feature and bug entities returned
✅ No product or test results

# Test 2: Date filtering (tests and bugs only)
result = mcp__testio-mcp__search(
    query="error",
    start_date="2025-01-01",
    end_date="2025-12-31",
    limit=50
)
✅ Only tests and bugs returned (products/features don't have timestamps)
✅ Results within date range

# Test 3: Product scoping
result = mcp__testio-mcp__search(
    query="crash",
    product_ids=[598, 18559],
    limit=25
)
✅ Results scoped to specified products
```

**Pass Criteria:** All validations ✅

---

### Test 7.2: List Bugs with Filters (STORY-084)

**Tool:** `list_bugs`

**Prerequisites:** Valid test IDs (use `list_tests` to find)

**⚠️ CRITICAL:** `list_bugs` requires `test_ids` parameter (no global bug listing). Must be preceded by `list_tests` or `search` to get test IDs.

```python
# Step 1: Get test IDs first
tests = mcp__testio-mcp__list_tests(product_id=<your_product_id>, per_page=5)
test_ids = [t["test_id"] for t in tests["tests"]]

# Step 2: List bugs for those tests with filters
mcp__testio-mcp__list_bugs(
    test_ids=test_ids,
    status=["rejected"],
    severity=["critical", "high"],
    page=1,
    per_page=50,
    sort_by="severity",
    sort_order="desc"
)

# Expected Result
{
    "bugs": [
        {
            "id": <int>,
            "title": "<string>",
            "severity": "critical" | "high",  # Filtered
            "status": "rejected",             # Filtered
            "test_id": <int>,
            "reported_at": "<ISO 8601>"
        },
        ...
    ],
    "pagination": {
        "page": 1,
        "per_page": 50,
        "total_count": <int>,
        "has_more": <bool>
    },
    "filters_applied": {
        "test_ids": [<int>, ...],
        "status": ["rejected"],
        "severity": ["critical", "high"]
    },
    "warnings": <list[str] | null>
}

# Validation
✅ All bugs have status="rejected"
✅ All bugs have severity in ["critical", "high"]
✅ All bugs belong to provided test_ids
✅ pagination.total_count shows total matching bugs
✅ filters_applied shows correct filters
✅ Warnings present if tests not found or data stale

# Edge Cases
# ----------

# Test 1: No filters (all bugs for tests)
result = mcp__testio-mcp__list_bugs(test_ids=test_ids)
✅ All bugs returned regardless of status/severity

# Test 2: Pagination
page2 = mcp__testio-mcp__list_bugs(
    test_ids=test_ids,
    page=2,
    per_page=10
)
✅ pagination.page = 2
✅ No overlap with page 1 bugs

# Test 3: Invalid test_ids (warning path)
result = mcp__testio-mcp__list_bugs(test_ids=[999999])
✅ warnings contains "Test ID 999999 not found"
✅ bugs array is empty []
```

**Pass Criteria:** All validations ✅

---

### Test 7.3: Get Bug Details (STORY-085)

**Tool:** `get_bug_summary`

**Prerequisites:** Valid bug ID (use `list_bugs` to find)

```python
# Execute
mcp__testio-mcp__get_bug_summary(bug_id=<your_bug_id>)

# Expected Result
{
    "id": <int>,
    "title": "<string>",
    "severity": "<string>",
    "status": "<string>",
    "known": <bool>,
    "actual_result": "<string | null>",
    "expected_result": "<string | null>",
    "steps": "<string | null>",
    "rejection_reason": "<string | null>",
    "reported_by_user": {
        "id": <int>,
        "username": "<string>"
    } | null,
    "test": {
        "id": <int>,
        "title": "<string>"
    },
    "feature": {
        "id": <int>,
        "title": "<string>"
    } | null,
    "reported_at": "<ISO 8601>",
    "data_as_of": "<ISO 8601>"
}

# Validation
✅ Core fields present (id, title, severity, status, known)
✅ Detail fields present (actual_result, expected_result, steps)
✅ test always populated (required relation)
✅ feature populated if bug is linked to feature
✅ reported_by_user populated if tester info available
✅ rejection_reason present if status="rejected"
✅ Timestamps in ISO 8601 format
✅ data_as_of shows cache freshness

# Edge Cases
# ----------

# Test 1: Bug with rejection reason
result = mcp__testio-mcp__get_bug_summary(bug_id=<rejected_bug_id>)
✅ status = "rejected"
✅ rejection_reason is not null

# Test 2: Invalid bug ID
try:
    result = mcp__testio-mcp__get_bug_summary(bug_id=999999)
    ❌ FAIL - Should have raised error
except ToolError as e:
    ✅ Error message contains "not found"
    ✅ Error follows ❌ℹ️💡 format
```

**Pass Criteria:** All validations ✅

---

### Test 7.4: Quick Entity Summaries (STORY-057)

**Tools:** `get_product_summary`, `get_feature_summary`, `get_user_summary`

**Purpose:** Verify lightweight cache-only summary tools for quick lookups

```python
# Product Summary (cache-only, no API calls)
product = mcp__testio-mcp__get_product_summary(product_id=<id>)

# Expected Result
{
    "id": <int>,
    "title": "<string>",
    "type": "<string>",
    "description": "<string | null>",
    "test_count": <int>,
    "feature_count": <int>,
    "last_synced": "<ISO 8601>",
    "data_as_of": "<ISO 8601>"
}

# Validation
✅ Returns: id, title, type, description, test_count, feature_count
✅ Response time <100ms (SQLite query, no API)
✅ No bug_count field (deliberately excluded - use get_product_quality_report for bugs)
✅ data_as_of shows cache timestamp
```

```python
# Feature Summary (includes embedded user_stories)
feature = mcp__testio-mcp__get_feature_summary(feature_id=<id>)

# Expected Result
{
    "id": <int>,
    "title": "<string>",
    "description": "<string | null>",
    "howtofind": "<string | null>",
    "user_stories": ["<story title 1>", "<story title 2>", ...],
    "test_count": <int>,
    "bug_count": <int>,
    "product": {
        "id": <int>,
        "name": "<string>"
    },
    "data_as_of": "<ISO 8601>"
}

# Validation
✅ user_stories is list of title strings (not counts!)
✅ product includes id and name
✅ test_count and bug_count are integers
✅ data_as_of shows cache timestamp
```

```python
# User Summary (activity counts by type)
user = mcp__testio-mcp__get_user_summary(user_id=<id>)

# Expected Result (varies by user_type)
{
    "id": <int>,
    "username": "<string>",
    "user_type": "tester" | "customer",
    "last_activity": "<ISO 8601>",
    "first_seen": "<ISO 8601>",
    "data_as_of": "<ISO 8601>",
    # For customers:
    "tests_created_count": <int>,
    "tests_submitted_count": <int>,
    # For testers:
    "bugs_reported_count": <int>
}

# Validation
✅ Customer users have tests_created_count, tests_submitted_count
✅ Tester users have bugs_reported_count
✅ last_activity is valid timestamp
✅ data_as_of shows cache timestamp
```

**Pass Criteria:** All validations ✅, response times <100ms

---

### Test 7.5: Manual Data Refresh (Epic 009)

**Tool:** `sync_data`

**Purpose:** Verify explicit data refresh control for freshness before reports

```python
# Incremental sync (discover new tests only - fast)
result = mcp__testio-mcp__sync_data()

# Expected Result
{
    "status": "completed" | "completed_with_warnings",
    "products_synced": <int>,
    "features_refreshed": <int>,
    "tests_discovered": <int>,
    "tests_updated": <int>,
    "duration_seconds": <float>,
    "warnings": [<string>, ...] | null
}

# Validation
✅ status is "completed" or "completed_with_warnings"
✅ products_synced >= 0
✅ features_refreshed >= 0
✅ tests_discovered >= 0
✅ tests_updated >= 0
✅ duration_seconds > 0
✅ warnings is list[str] or null
```

```python
# Date range sync (all tests after date)
result = mcp__testio-mcp__sync_data(since="7 days ago")

# Validation
✅ Same structure as above
✅ tests_discovered + tests_updated likely higher than incremental

# Product-scoped sync
result = mcp__testio-mcp__sync_data(product_ids=[598])

# Validation
✅ Only syncs specified product
✅ products_synced = 1

# Full resync (slowest, most thorough)
result = mcp__testio-mcp__sync_data(since="all")

# Validation
✅ Duration significantly longer
✅ All tests refreshed
```

**Sync Best Practices:**
- Call `sync_data()` before generating fresh reports
- Use `sync_data(since="7 days ago")` for moderate freshness
- Use `sync_data(since="all")` only for recovery/debugging

**Pass Criteria:** All validations ✅

---

## Validation Criteria

### Overall Test Suite Success Criteria

**Required for PASS:**
- ✅ All 12 test cases pass
- ✅ Zero errors during execution (excluding intentional error tests)
- ✅ All response times <5 seconds (target: <2s)
- ✅ Error messages follow 3-part format
- ✅ Data structure integrity maintained
- ✅ Database operations functional

### Quality Metrics

| Metric | Target | Acceptable | Fail |
|--------|--------|------------|------|
| Test Pass Rate | 100% | ≥95% | <95% |
| API Response Time (p50) | <2s | <5s | ≥5s |
| API Response Time (p99) | <5s | <10s | ≥10s |
| **Database Query Time** | <100ms | <500ms | ≥500ms |
| Error Rate | 0% | <1% | ≥1% |
| Cache Hit Rate (warm, TTL) | >70% | >50% | <50% |
| **Database Size (1000 tests)** | ~25MB | <50MB | ≥50MB |
| Data Completeness | 100% | 100% | <100% |

### Data Integrity Checks

For every response, verify:
- ✅ No missing required fields
- ✅ No null values in required fields
- ✅ Integer IDs preserved (not converted to strings)
- ✅ Timestamps in ISO 8601 format
- ✅ Enum values match documented options

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Tool Not Found Error

**Symptom:**
```
Error: No such tool available: mcp__testio-mcp__health_check
```

**Cause:** MCP server not connected or incorrectly named

**Solution:**
1. Run `/mcp` command to reconnect
2. Verify server name is exactly "testio-mcp"
3. Check Claude Code settings for MCP server configuration

---

#### Issue 2: Authentication Failed

**Symptom:**
```
❌ Authentication failed
ℹ️  API token is invalid or expired
💡 Check TESTIO_CUSTOMER_API_TOKEN in .env file
```

**Cause:** Invalid or missing API token

**Solution:**
1. Check `.env` file exists in project root
2. Verify `TESTIO_CUSTOMER_API_TOKEN` is set
3. Ensure token is valid (test with curl)
4. Restart MCP server after updating `.env`

---

#### Issue 3: Test ID Not Found

**Symptom:**
```
❌ Test ID 'XXXXX' not found
```

**Cause:** Test ID doesn't exist in current environment

**Solution:**
1. Run `list_products()` to get valid product IDs
2. Run `list_tests(product_id=<id>)` to get valid test IDs
3. Use test IDs from the list in subsequent calls
4. Note: Staging vs Production have different test IDs

---

#### Issue 4: Slow Response Times

**Symptom:** Response times >5 seconds consistently

**Cause:** API rate limiting, network issues, or large datasets

**Solution:**
1. Check database stats with `get_database_stats()`
2. Verify network connectivity to TestIO API
3. Check if database sync is up to date
4. Run manual sync if needed: `uv run python -m testio_mcp sync`

---

#### Issue 5: Database Not Synced (STORY-021)

**Symptom:**
```
❌ Product ID 'XXXXX' not found
ℹ️  This product may not exist or you don't have access to it
```

**Cause:** Local database not synced with API (product exists in API but not in local DB)

**Solution:**
1. Run `uv run python -m testio_mcp sync --status` to check sync status
2. Run `uv run python -m testio_mcp sync` to sync all products
3. Or sync specific product: `uv run python -m testio_mcp sync --product-ids XXXXX`
4. Verify with `get_database_stats` tool (check `total_products` > 0)

---

#### Issue 6: Database Corruption (STORY-021)

**Symptom:** SQLite errors, inconsistent data, or missing product names

**Cause:** Database corruption, schema mismatch, or incomplete sync

**Solution:**
1. Check database stats: `get_database_stats()`
2. Clear and resync: `uv run python -m testio_mcp sync --nuke --yes`
3. Verify schema version matches expected (v1 for MVP)
4. If persistent, delete database file and resync:
   ```bash
   rm ~/.testio-mcp/cache.db
   uv run python -m testio_mcp sync
   ```

---

### Performance Optimization Tips

1. **Local Database Queries (STORY-021):**
   - `list_tests` queries local database (fast, <100ms)
   - Use date filters and status filters to reduce result size
   - Database queries imperceptible to users (<10ms at our scale)
   - No API calls for `list_tests` queries

2. **Use Caching Effectively:**
   - TTL-based in-memory cache for API responses (products, test status)
   - Products cache for 1 hour (stable data)
   - Test status cache for 5 minutes (moderate changes)

3. **Database Sync Strategy:**
   - Incremental sync by default (only new tests)
   - Use `--force` for full refresh (non-destructive upsert)
   - Use `--refresh` for hybrid (new tests + mutable test updates)
   - Background sync on server startup (non-blocking)
   - Manual sync via CLI: `uv run python -m testio_mcp sync`

4. **Filter Early:**
   - Apply status filters in `list_tests` (not client-side)
   - Reduces data transfer and processing time
   - Filters applied at database query level (fast)

5. **Parallel Queries:**
   - Use `asyncio.gather()` for independent queries
   - Don't parallelize dependent queries
   - Respect API rate limits (max 10 concurrent)

---

## Summary

This E2E testing script provides comprehensive coverage of the testio-mcp server functionality through persona-based scenarios. Execute all test cases to verify:

- ✅ API connectivity and authentication
- ✅ **Local database operations (STORY-021)** - sync, query, stats
- ✅ **EBR report generation** - quality metrics, acceptance rates
- ✅ **Analytics queries (Epic 007)** - dynamic metrics, dimensions, filtering
- ✅ Product discovery and filtering
- ✅ Test status retrieval and bug summary
- ✅ **Advanced pagination** - offset combinations, status filtering
- ✅ Error handling and edge cases
- ✅ Data integrity and performance
- ✅ Database persistence and caching

**Expected Execution Time:** 8-12 minutes
**Pass Rate Target:** 100% (all 20 tests)
**Quality Bar:** Production-ready if all tests pass

### Available MCP Tools (17 Active)

The following tools are currently available for testing:

**Core Query Tools:**
1. **`list_products`** - Product discovery with search and filtering
2. **`list_tests`** - Test listing with status filtering and bug counts
3. **`get_test_summary`** - Comprehensive test status with bug summary
4. **`list_features`** - List features for a product with pagination (Epic 005)
5. **`list_users`** - List users (testers/customers) with type filter and pagination (Epic 005)
6. **`list_bugs`** - List bugs for specific tests with filters (STORY-084) ⚠️ Requires test_ids

**Summary Tools (Cache-Only):**
7. **`get_product_summary`** - Product metadata with counts (STORY-057)
8. **`get_feature_summary`** - Feature metadata with embedded user stories (STORY-057)
9. **`get_user_summary`** - User metadata with activity counts (STORY-057)
10. **`get_bug_summary`** - Comprehensive bug details with relations (STORY-085)

**Analytics Tools:**
11. **`query_metrics`** - Dynamic analytics queries with dimensions/metrics (Epic 007)
12. **`get_analytics_capabilities`** - Discover available dimensions and metrics (Epic 007)

**Report Tools:**
13. **`get_product_quality_report`** - Generate Evidence-Based Review reports with quality metrics

**Infrastructure Tools:**
14. **`get_server_diagnostics`** - Consolidated server health (API, database, sync status) (STORY-060)
15. **`get_problematic_tests`** - View tests that failed to sync (debugging tool)
16. **`sync_data`** - Explicit data refresh control (Epic 009)
17. **`search`** - Full-text search across entities with BM25 ranking (Epic 010)

### Removed/Deprecated Tools

The following tools were **removed** or **replaced**:
- ❌ `health_check` → Replaced by `get_server_diagnostics`
- ❌ `get_database_stats` → Replaced by `get_server_diagnostics`
- ❌ `list_user_stories` → **REMOVED** (use `list_features` + `get_feature_summary` workflow)
- ❌ `get_test_bugs` → **REMOVED** (use `list_bugs` with test_ids)
- ❌ `generate_status_report` → **REMOVED** (use `get_product_quality_report`)
- ❌ `get_test_activity_by_timeframe` → **REMOVED**

**Breaking Change (v0.3.0+):** `query_metrics` default now excludes initialized/cancelled tests.

---

**Document Version:** 3.0
**Last Updated:** 2025-12-03 (Added 17 active tools, STORY-084/085 bug tools, STORY-057 summaries)
**Maintainer:** TestIO MCP Development Team
**Complementary Tests:**
- `AGENT_USABILITY_TASKS.md` (task prompts for agents)
- `AGENT_USABILITY_EVALUATION.md` (evaluator scoring guide)
**Feedback:** Report issues at https://github.com/testio/testio-mcp/issues
