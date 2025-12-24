# Epic 003: Automated Executive Testing Reports - Brownfield Enhancement

## Epic Goal

Enable CSMs to generate executive bug reports on-demand via natural language, eliminating manual Tableau exports and enabling data-driven customer conversations through instant multi-test analytics with consistent formatting.

## Epic Description

### Existing System Context

**Current functionality:**
- Individual test queries via `get_test_status(test_id)` - single test at a time
- Bug metrics calculated per test (acceptance rates, type/severity distribution)
- Manual Tableau exports required for multi-test EBR (Executive Bug Report) aggregation
- No natural language interface for report generation
- No file output capability for reports

**Technology stack:**
- Python async with service layer pattern (ADR-006)
- BaseService for dependency injection and caching patterns
- TestIO Customer API for bug/test data
- FastMCP for tool registration and auto-discovery
- Existing date parsing utilities (`date_utils.py`)

**Integration points:**
- Extends `TestService` bug classification logic (lines 201-279: reviewed denominator, auto-acceptance rates)
- Reuses `BaseService` patterns (`get_service()` helper, `ToolError` exceptions)
- Integrates with local data store from Epic 002 (PersistentCache for instant queries)
- Leverages existing concurrency controls (semaphore-limited API calls)

### Enhancement Details

**What's being added/changed:**

This epic adds a complete EBR report generation system:

1. **Multi-test aggregation service** (`MultiTestReportService`):
   - Discovers tests across multiple products by date range
   - Aggregates bug metrics from all tests into single report
   - Calculates acceptance rates, type/severity distributions, health indicators
   - Uses local store for instant test discovery (~10ms vs 10s API queries)

2. **Report formatting layer** (`formatters/`):
   - Separates presentation from business logic
   - Supports markdown and JSON output formats
   - 5-section EBR format: Executive Summary, Status Breakdown, Type Distribution, Severity Analysis, Test Performance

3. **MCP tool with file output** (`generate_multi_test_report`):
   - Natural language interface (e.g., "Generate Q4 2024 EBR for Customer A")
   - Orchestrates service → formatter → file write workflow
   - Writes reports to disk with security (workspace anchoring)
   - Returns metadata (not content) - reports meant to be saved/shared

4. **Shared utilities** (`utilities/date_filters.py`):
   - Extracts date filtering logic from `ActivityService` (avoid duplication)
   - Makes `parse_date_input()` public API for downstream tools
   - Reuses existing `date_utils.py` for flexible date parsing

**How it integrates:**

1. **Service layer** - `MultiTestReportService` inherits from `BaseService`, follows existing patterns
2. **Data discovery** - Uses `PersistentCache.query_tests()` from Epic 002 for instant multi-test queries
3. **Bug classification** - Replicates exact logic from `test_service.py:201-279` (reviewed denominator, auto-acceptance)
4. **Formatter pattern** - New layer enables multiple report formats without touching service logic
5. **Tool integration** - Follows ADR-011 patterns (`get_service()`, `ToolError`, auto-discovery)

**Success criteria:**

- **User experience:** Generate EBR report via natural language in <5 seconds (after warm cache)
- **Data accuracy:** Report metrics match Tableau dashboard data (with Customer API data limitations documented)
- **Technical quality:** Query performance <50ms from SQLite, code coverage >85%
- **CSM validation:** Manual comparison against Tableau confirms calculation correctness

**Critical data validation note:** Customer API does not include tester device data that appears in full Tableau dashboards. Acceptance criteria focuses on validating metrics that ARE available in Customer API (bug counts, status, type, severity, acceptance rates).

## Stories

### 1. STORY-019a: Core EBR Service Infrastructure (2-3 hours)
**Description:** Create `MultiTestReportService` that discovers tests across products and aggregates bug metrics. Extract shared date utilities from `ActivityService` to avoid duplication.

**Key deliverables:**
- `utilities/date_filters.py` - Shared date filtering logic (extracted from ActivityService)
- `MultiTestReportService.discover_and_fetch_tests()` - Uses PersistentCache for instant queries
- `MultiTestReportService.aggregate_report_data()` - Bug metric calculations (reviewed rates, health indicator)
- `NoTestsFoundException` - Raised when filters yield zero tests
- Unit tests with mocked cache (>80% coverage)

**Critical business logic (CSM-validated):**
- **Reviewed bugs** = active_accepted + rejected (human-reviewed only, excludes auto_accepted)
  - Note: API returns ALL bugs as "forwarded to customer" since this is the Customer API
- **Acceptance rate** = accepted / reviewed (NOT total)
- **Auto-acceptance** <20% = healthy, ≥20% = warning (threshold configurable via env var)
- **Severity analysis** = functional bugs only (not visual/content/custom)

**Dependencies:** Epic 002 (STORY-021 PersistentCache, STORY-020 pagination pattern)

### 2. STORY-019b: Formatter Infrastructure & EBR Implementation (3-4 hours)
**Description:** Create formatter layer that renders EBR reports from aggregated data. Separate presentation logic from business logic for testability and extensibility.

**Key deliverables:**
- `formatters/base.py` - Abstract `BaseReportFormatter` class
- `formatters/ebr_formatter.py` - EBR markdown/JSON renderer
- 5-section markdown format: Executive Summary, Status Breakdown, Type Distribution, Severity Analysis, Test Performance
- Health indicator display (✅ healthy, ⚠️ warning, ℹ️ unknown)
- Unit tests with mock data (>80% coverage)

**Design pattern:**
- Service layer = data fetching + calculations (NO formatting)
- Formatter layer = presentation only (NO API calls)
- Benefits: Service reusable, formatters testable with mock data, easy to add new formats

**Dependencies:** STORY-019a (depends on service data schema)

### 3. STORY-019c: MCP Tool Integration & File Output (2-3 hours)
**Description:** Create `generate_multi_test_report` MCP tool that orchestrates report generation and writes files to disk with security controls.

**Key deliverables:**
- `tools/generate_multi_test_report_tool.py` - MCP tool with natural language interface
- Orchestration: parse dates → discover tests → aggregate data → format → write file
- File I/O security: Workspace anchoring with `Path.relative_to()` (prevents path traversal)
- Error handling: Domain exceptions → ToolError with ❌ℹ️💡 format
- Tool unit tests (>85% coverage)

**Tool signature:**
```python
async def generate_multi_test_report(
    product_ids: list[int],
    start_date: str,  # Flexible: ISO 8601, "last 30 days", "Q4 2024"
    end_date: str,
    output_path: str,
    date_field: Literal["created_at", "start_at", "end_at", "any"] = "start_at",
    format: Literal["markdown", "json"] = "markdown"
) -> dict  # Returns metadata (file_path, size, test_count, bug_count), not content
```

**Dependencies:** STORY-019a (service), STORY-019b (formatter)

### 4. STORY-019d: EBR Integration Testing & Documentation (2-3 hours)
**Description:** End-to-end integration tests with real API, comprehensive documentation for CSM users, manual validation against Tableau baseline.

**Key deliverables:**
- `tests/integration/test_generate_multi_test_report.py` - E2E tests with real API
- User guide documentation (README.md, formatters/README.md)
- Manual test artifact: `docs/qa/manual-tests/story-019-ebr-manual-tests.md`
- Tableau validation results (with Customer API data limitations documented)
- Test coverage >85% across all EBR components

**Testing strategy:**
- Integration tests: Markdown format, JSON format, different date fields, parameterized
- Manual tests: MCP Inspector CLI, Claude UI natural language, date format variations
- Accuracy validation: Compare against Tableau dashboard (noting tester device data unavailable in Customer API)

**Documentation deliverables:**
- README.md: Tool listing, brief description, link to usage guide
- formatters/README.md: Formatter pattern guide, how to add new formatters
- Manual test results: Pass/fail table, screenshots, Tableau comparison notes

**Dependencies:** STORY-019a, STORY-019b, STORY-019c (full stack integration)

## Compatibility Requirements

### Backward Compatibility

- ✅ Existing tools/services remain unchanged (additive feature, no breaking changes)
- ✅ Existing APIs unchanged (new tool, new services, new formatters)
- ✅ Database schema compatible (relies on Epic 002 foundation)
- ✅ Service patterns followed (BaseService, get_service(), ToolError)

### Tool Patterns

- ✅ Auto-discovery via `@mcp.tool()` decorator (ADR-011)
- ✅ `get_service()` helper for dependency injection
- ✅ `ToolError` exceptions with ❌ℹ️💡 format
- ✅ Pydantic validation for tool inputs
- ✅ Tool testing pattern from STORY-016 (extract fn from wrapper, mock service)

### Cache Integration

- ✅ Uses `PersistentCache` from Epic 002 (no cache management needed in service)
- ✅ SQLite queries handle all filtering (status, date range, pagination)
- ✅ Customer isolation via `customer_id` in queries (multi-tenant safe)
- ✅ No explicit cache key generation (SQL queries are the cache interface)

### API Contract Stability

- ✅ Relies on TestIO Customer API bug classification fields (`status`, `auto_accepted`)
- ✅ Assumes chronological test ordering (inherited from Epic 002 sync)
- ✅ Assumes stable pagination (100 tests per page)
- ⚠️ Customer API limitation: No tester device data (present in full Tableau dashboards)

### Configuration

**No new environment variables needed** - reuses existing settings:
- `AUTO_ACCEPTANCE_ALERT_THRESHOLD` - Health indicator threshold (default: 0.20 = 20%, from config.py STORY-005c)
- `TESTIO_CUSTOMER_ID` - For customer data isolation (Epic 002)
- `TESTIO_DB_PATH` - SQLite database location (Epic 002)

## Risk Mitigation

### Primary Risk: Report Accuracy vs Tableau Baseline

**Risk:** Bug classification logic or aggregation calculations differ from existing Tableau/ebr_tools reports, causing CSM confusion or incorrect reporting.

**Mitigation:**
- Replicate exact logic from `test_service.py:201-279` (reviewed denominator, auto-acceptance)
- CSM-validated business rules (reviewed bugs, 20% threshold, severity functional-only)
- Manual testing: Generate reports and compare against Tableau dashboard
- Document Customer API data limitations (no tester device data)
- QA artifact required: `docs/qa/manual-tests/story-019-ebr-manual-tests.md` with comparison results

**Validation criteria:**
- Acceptance rates match Tableau (within Customer API data constraints)
- Bug counts match Tableau (total, accepted, rejected, forwarded)
- Type/severity distributions match Tableau (functional bugs only for severity)

### Secondary Risk: File I/O Security

**Risk:** Path traversal vulnerabilities in `output_path` parameter allow writing files outside workspace.

**Mitigation:**
- Workspace anchoring: Use `Path.relative_to()` to validate output is within workspace
- Never use `str.startswith()` for path checks (vulnerable to `/workspace_backup/` bypasses)
- `expanduser()` and `resolve()` handle symlinks and `~` paths correctly
- Tool unit tests cover path traversal attempts

### Tertiary Risk: Date Parsing Edge Cases

**Risk:** Flexible date parsing ("last 30 days", "Q4 2024") fails for edge cases or ambiguous inputs.

**Mitigation:**
- Reuse existing `date_utils.py` (already handles ISO 8601, business terms, relative dates)
- Comprehensive error messages with ❌ℹ️💡 format guide users to correct inputs
- Tool unit tests cover all supported date formats
- Integration tests validate date range filtering with real API

## Definition of Done

- [x] All 4 stories completed with acceptance criteria met
  - [x] STORY-019a: Service infrastructure with date utilities
  - [x] STORY-019b: Formatter layer with markdown/JSON support
  - [x] STORY-019c: MCP tool with file output security
  - [x] STORY-019d: Integration tests and documentation

- [x] CSM validation completed
  - [x] Manual report generation via MCP Inspector
  - [x] Manual report generation via Claude natural language
  - [x] Tableau comparison documented (with Customer API limitations noted)
  - [x] QA artifact created: `docs/qa/manual-tests/story-019-ebr-manual-tests.md`

- [x] Bug classification logic validated
  - [x] Reviewed denominator confirmed (excludes forwarded/pending)
  - [x] Auto-acceptance threshold uses existing config (AUTO_ACCEPTANCE_ALERT_THRESHOLD)
  - [x] Health indicator calculation correct
  - [x] Severity analysis functional bugs only

- [x] Existing functionality verified through testing
  - [x] No regression in existing tools/services
  - [x] Service unit tests pass (>85% coverage)
  - [x] Integration tests pass with real API

- [x] Integration points working correctly
  - [x] Service integrates with PersistentCache from Epic 002
  - [x] Formatter receives correct data schema from service
  - [x] Tool orchestrates service → formatter → file write workflow
  - [x] Natural language date parsing works (ISO, relative, business terms)

- [x] Documentation updated appropriately
  - [x] README.md tool listing updated
  - [x] formatters/README.md created (pattern guide)
  - [x] Manual test results documented with Tableau comparison

- [x] Performance targets met
  - [x] Report generation <5 seconds after warm cache
  - [x] Test discovery <50ms (SQLite queries from Epic 002)
  - [x] Natural language interface responsive (<1s orchestration overhead)

- [x] Security validated
  - [x] Path traversal prevention tested (workspace anchoring)
  - [x] No arbitrary file writes outside workspace
  - [x] Tool unit tests cover security edge cases

---

**Epic Status:** ✅ COMPLETED - 2025-01-20
**Release Version:** 0.2.0
**Stories Completed:** 4/4 (100%)

## CSM Use Case Examples

**Example 1: Quarterly EBR for Customer**
```
CSM: "Generate Q4 2024 EBR for Customer A products and save to reports folder"

Claude:
✅ EBR report generated!
📄 File: /Users/Ricardo/reports/customer_a_q4_2024.md
📊 Size: 15.2 KB
🧪 Tests analyzed: 12
🐛 Bugs found: 187

The report covers 2 products across Q4 2024 with 85% overall acceptance rate.
```

**Example 2: Monthly Status Check**
```
CSM: "Show me bug trends for HALO product for last 30 days"

Claude:
[Calls generate_multi_test_report with relative date parsing]

✅ Report generated!
📄 File: reports/halo_last_30_days.md
🧪 Tests: 3
🐛 Bugs: 45
⚠️ Warning: Auto-acceptance rate 22% (above 20% healthy threshold)
```

**Example 3: Custom Date Range**
```
CSM: "Generate EBR for Customer A from October 1 to December 31"

Claude:
[Calls with ISO 8601 dates, discovers tests, aggregates metrics, formats report]

✅ Report ready!
📄 File: reports/customer_a_oct_dec.md
🧪 Tests: 8
🐛 Bugs: 134
✅ Healthy: Auto-acceptance 12%
```

## Validation Notes

**Tableau Comparison (Critical Success Criteria):**

CSM will manually validate report accuracy against Tableau dashboard:
- **Metrics to validate:** Bug counts (total, accepted, rejected), acceptance rates, type distribution, severity (functional only)
- **Known limitation:** Customer API does not include tester device data visible in full Tableau dashboards
- **Validation approach:** Compare Customer API-derived metrics with corresponding Tableau sections
- **Documentation:** Results recorded in `docs/qa/manual-tests/story-019-ebr-manual-tests.md`

**No Production Users:**

Project has no users yet, so risk is minimal. This epic:
- Enables powerful CSM self-service capability (eliminates manual Tableau exports)
- Demonstrates natural language query potential for future features
- Sets foundation for advanced multi-test analytics (trends, comparisons, forecasting)

---

**Epic Created:** 2025-01-07
**Author:** Sarah (Product Owner)
**Parent Design:** docs/stories/story-019-DESIGN.md
**Dependencies:** Epic 002 (Local Data Store Foundation) - MUST complete first
**Execution Order:** STORY-021 → STORY-020 → STORY-019a → STORY-019b → STORY-019c → STORY-019d
