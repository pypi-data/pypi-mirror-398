---
story_id: STORY-019b
epic_id: EPIC-003
title: Formatter Infrastructure & EBR Implementation
status: superseded
superseded_by: STORY-023e
superseded_date: 2025-11-18
created: 2025-01-07
estimate: 3-4 hours
assignee: dev
dependencies: [STORY-019a]
priority: high
parent_design: story-019-DESIGN.md
linear_issue: LEO-48
linear_url: https://linear.app/leoric-crown/issue/LEO-48/formatter-infrastructure-and-ebr-implementation
linear_status: Backlog
linear_branch: leonricardo314/leo-48-formatter-infrastructure-ebr-implementation
---

## Status
**SUPERSEDED** - Replaced by STORY-023e (Epic 004 - SQLite-First Architecture)

**Reason:** Formatter infrastructure is incorporated directly into MultiTestReportService in STORY-023e. The service handles both data aggregation and report formatting as a single responsibility, simplifying the architecture and avoiding the overhead of a separate formatter layer for MVP.

**See:** `docs/stories/story-023e-multitestreportservice.md` for current implementation plan.

## Story
**As a** developer
**I want** a formatter layer that renders EBR reports from aggregated data
**So that** presentation logic is separated from data fetching and can be tested independently

## Acceptance Criteria

### AC1: Create BaseReportFormatter
- [ ] File: `src/testio_mcp/formatters/base.py`
- [ ] Abstract base class with `format(data: dict, output_format: str) -> dict` method
- [ ] Docstrings explain formatter pattern:
  - Formatters receive pre-aggregated data (NO API calls)
  - Service layer handles data fetching
  - Formatters handle presentation only
- [ ] Type hints with strict mypy compliance

### AC2: Create EbrFormatter
- [ ] File: `src/testio_mcp/formatters/ebr_formatter.py`
- [ ] Inherit from `BaseReportFormatter`
- [ ] Implement `format(data: dict, output_format: str) -> dict` method
- [ ] Support `output_format`: "markdown" | "json"
- [ ] Return structure: `{"report": str, "data": dict}`

### AC3: Markdown Report Format
Generate markdown with these 6 sections:

**1. Executive Summary**
- Report period (start/end dates)
- Products covered
- Test count
- Total bugs
- Overall acceptance rate (manual + auto)
- Auto-acceptance rate
- Health indicator (✅ if auto < 20%, ⚠️ otherwise)

**2. Bug Status Breakdown**
Table format:
| Status | Count | Percentage |
|--------|-------|------------|
| Accepted (Manual) | 170 | 72.6% |
| Auto-Accepted | 15 | 6.4% |
| Rejected | 15 | 6.4% |
| Forwarded (Pending) | 34 | 14.5% |

**3. Bug Type Distribution**
Table format (iterate over all types present in data, sorted alphabetically):
| Type | Count | % of Total | Acceptance Rate | Auto Rate |
|------|-------|------------|-----------------|-----------|
| Functional | 150 | 64.1% | 88.9% | 3.7% |
| Visual | 50 | 21.4% | 85.0% | 5.0% |
| Content | 20 | 8.5% | 80.0% | 10.0% |
| Custom | 14 | 6.0% | 78.6% | 7.1% |

**4. Bug Severity Analysis** (Functional bugs only)
Table format (iterate over all severities present in data, sorted: critical, high, low):
| Severity | Count | % of Functional | Accepted | Auto-Accepted |
|----------|-------|-----------------|----------|---------------|
| Critical | 5 | 3.3% | 4 | 0 |
| High | 45 | 30.0% | 38 | 2 |
| Low | 100 | 66.7% | 78 | 3 |

**5. Test Performance**
- Test count
- Date range (earliest → latest)
- Test velocity (tests per week)

**6. Data Quality Notes** (Epic 002 integration)
- Display only if `data["data_quality"]["has_gaps"]` is True
- Format as warning callout:
  ```
  ## ⚠️ Data Quality Notes

  **Incomplete Data:** This report is based on incomplete data due to API sync errors.

  **Missing Tests:** {problematic_tests_count} test(s) could not be synced and are excluded from this report.

  **Details:**
  {for each problematic test:}
  - **Product ID:** {product_id}
  - **Position:** Test #{position_range} in chronological order
  - **Boundary (before):** Test ID {boundary_before_id}, ended {boundary_before_end_at}
  - **Boundary (after):** Test ID {boundary_after_id}, ended {boundary_after_end_at}
  - **Recovery attempts:** {recovery_attempts}
  - **Note:** The missing test has an `end_at` between the two boundary timestamps.

  **Impact:** Bug counts and acceptance rates may be understated. Use boundary information to manually investigate missing tests in TestIO UI.

  **Recovery:** Run `force_sync_product({product_id})` to retry, or contact TestIO support with boundary test IDs.
  ```
- If `has_gaps` is False, omit this section entirely (report is complete)

### AC4: JSON Format Support
- [ ] Convert aggregated data to JSON string (pretty-printed, indent=2)
- [ ] Structure: `{"report": <json_string>, "data": <original_dict>}`
- [ ] The "report" field contains the JSON-serialized data
- [ ] The "data" field contains the original dict (for compatibility)

**Clarification:** JSON format serializes the data dict into a string with formatting for readability.

### AC5: Health Indicator Display (NOT calculation)
- [ ] Read pre-calculated health from `data["bug_metrics"]["health"]`
- [ ] Display health indicator:
  - `"healthy"` → ✅ Healthy
  - `"warning"` → ⚠️ High Auto-Acceptance
  - `"unknown"` → ℹ️ Insufficient Data
  - `None` rates → Display as "N/A"
- [ ] **DO NOT recalculate health** - trust service layer value

**Rationale:** Service owns business logic (STORY-019a AC7). Formatters display pre-calculated values to prevent divergence.

### AC6: Unit Tests
- [ ] File: `tests/formatters/test_ebr_formatter.py`
- [ ] Test markdown rendering with mock data (no API)
- [ ] Verify all 6 sections present when data has gaps
- [ ] Verify only 5 sections present when data is complete (has_gaps=False)
- [ ] Test data quality section rendering with problematic tests
- [ ] Test JSON format (verify report is JSON string, includes data_quality)
- [ ] Test health indicator rendering (✅ healthy, ⚠️ warning, ℹ️ unknown)
- [ ] Test with `None` rates (display as "N/A")
- [ ] Test with dynamic types/severities (not hardcoded lists)
- [ ] Test with missing optional fields (graceful degradation)
- [ ] Coverage >80%

## Tasks / Subtasks

- [ ] Task 1: Create formatter directory structure
  - [ ] Create src/testio_mcp/formatters/__init__.py
  - [ ] Add docstring explaining formatter pattern

- [ ] Task 2: Implement BaseReportFormatter (AC1)
  - [ ] Create src/testio_mcp/formatters/base.py
  - [ ] Define abstract base class
  - [ ] Add abstract method: format(data, output_format)
  - [ ] Add comprehensive docstrings
  - [ ] Add type hints

- [ ] Task 3: Create EbrFormatter skeleton (AC2)
  - [ ] Create src/testio_mcp/formatters/ebr_formatter.py
  - [ ] Inherit from BaseReportFormatter
  - [ ] Add class docstring
  - [ ] Import dependencies

- [ ] Task 4: Implement markdown formatting (AC3)
  - [ ] Implement format() method
  - [ ] Create _format_markdown() helper
  - [ ] Section 1: Executive Summary
  - [ ] Section 2: Bug Status Breakdown (table)
  - [ ] Section 3: Bug Type Distribution (table)
  - [ ] Section 4: Severity Analysis (table, functional only)
  - [ ] Section 5: Test Performance
  - [ ] Add health indicator rendering (AC5)

- [ ] Task 5: Implement JSON formatting (AC4)
  - [ ] Create _format_json() helper
  - [ ] Return pretty-printed JSON (indent=2)
  - [ ] Preserve original data structure

- [ ] Task 6: Write unit tests (AC6)
  - [ ] Create test file
  - [ ] Create mock aggregated data fixtures
  - [ ] Test markdown format (all sections)
  - [ ] Test JSON format
  - [ ] Test health indicators
  - [ ] Test with missing fields
  - [ ] Achieve >80% coverage

## Dev Notes

### Design Pattern: Service + Formatter Separation

**Service Layer (STORY-019a):**
- Fetches data from API
- Calculates metrics
- Returns structured dict
- NO formatting logic

**Formatter Layer (This Story):**
- Receives pre-aggregated data
- Renders output (markdown/JSON)
- NO API calls
- Pure presentation logic

**Benefits:**
- Service can be reused for multiple report types
- Formatters testable with mock data (no API needed)
- Easy to add new formatters without touching service

### Input Data Contract

Formatter receives this schema from MultiTestReportService (AC5 from STORY-019a):

```python
{
    "bug_metrics": {
        "total": 234,
        "accepted": 170,
        "auto_accepted": 15,
        "overall_accepted": 185,
        "rejected": 15,
        "forwarded": 34,
        "reviewed": 200,
        "acceptance_rate": 0.85,
        "auto_acceptance_rate": 0.075,
        "overall_acceptance_rate": 0.925,
        "rejection_rate": 0.075,
        "health": "healthy",
        "by_type": { ... },
        "by_severity": { ... }
    },
    "test_metrics": {
        "test_count": 12,
        "earliest_start": "2024-10-01T00:00:00Z",
        "latest_start": "2024-12-28T14:30:00Z",
        "date_range_days": 89,
        "tests_per_week": 0.94,
        "products": ["Product A", "Product B"]
    }
}
```

### Markdown Table Formatting

Use Python string formatting for clean tables:

```python
# Example table rendering
def _format_status_table(self, bug_metrics: dict) -> str:
    """Format bug status breakdown table."""
    total = bug_metrics["total"]
    rows = [
        ("Accepted (Manual)", bug_metrics["accepted"]),
        ("Auto-Accepted", bug_metrics["auto_accepted"]),
        ("Rejected", bug_metrics["rejected"]),
        ("Forwarded", bug_metrics["forwarded"])
    ]

    table = "| Status | Count | Percentage |\n"
    table += "|--------|-------|------------|\n"

    for status, count in rows:
        pct = (count / total * 100) if total > 0 else 0
        table += f"| {status} | {count} | {pct:.1f}% |\n"

    return table
```

### Source Tree
```
src/testio_mcp/
├── formatters/                       # NEW: Create this directory
│   ├── __init__.py                  # NEW
│   ├── base.py                      # NEW: Abstract formatter
│   └── ebr_formatter.py             # NEW: EBR markdown/JSON

tests/
├── formatters/                       # NEW
│   └── test_ebr_formatter.py        # NEW
```

### Testing Strategy

**Pure Unit Tests (No API):**
- Create fixture with mock aggregated data
- Test all markdown sections render correctly
- Test JSON format preserves structure
- Test health indicator logic
- Test missing field handling

**Example Test:**
```python
@pytest.fixture
def mock_aggregated_data():
    return {
        "bug_metrics": {
            "total": 234,
            "accepted": 170,
            "auto_accepted": 15,
            "overall_accepted": 185,
            "rejected": 15,
            "forwarded": 34,
            "reviewed": 200,
            "acceptance_rate": 0.85,
            "auto_acceptance_rate": 0.075,
            "health": "healthy",
            # ... rest of data
        },
        "test_metrics": { ... }
    }

def test_markdown_format_includes_all_sections(mock_aggregated_data):
    formatter = EbrFormatter()
    result = formatter.format(mock_aggregated_data, "markdown")

    assert "Executive Summary" in result["report"]
    assert "Bug Status Breakdown" in result["report"]
    assert "Bug Type Distribution" in result["report"]
    assert "Bug Severity Analysis" in result["report"]
    assert "Test Performance" in result["report"]
```

### References
- **Design Doc:** docs/stories/story-019-DESIGN.md (lines 440-462, 852-917)
- **STORY-019a:** Data schema contract
- **ADR-006:** Service Layer Pattern (separation of concerns)

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-07 | 0.1 | Story created from story-019-DESIGN.md | Sarah (PO) |
| 2025-01-07 | 0.2 | Codex peer review fixes: Clarified JSON format behavior, health indicator display (not calculation), None rates handling, dynamic type/severity iteration | Sarah (PO) |
| 2025-01-07 | 0.3 | **Data quality section (Epic 002 integration):** (1) AC3: Added 6th section "Data Quality Notes" to markdown format (5→6 sections), displayed only when has_gaps=True, (2) Format includes warning callout with problematic test details (product_id, boundary IDs, end_at timestamps, recovery attempts), (3) AC6: Updated tests to verify conditional rendering (6 sections with gaps, 5 without), (4) Rationale: EBR reports must prominently disclose incomplete data when API sync errors occur - provides full context for manual investigation while still being faster than manual Tableau export. No estimate change (conditional rendering is simple template logic). | Winston (Architect) |

## Dev Agent Record
*This section will be populated during implementation*

## QA Results
*This section will be populated after QA review*
