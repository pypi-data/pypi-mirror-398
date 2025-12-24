---
story_id: STORY-019d
epic_id: EPIC-003
title: EBR Integration Testing & Documentation
status: superseded
superseded_by: STORY-023e
superseded_date: 2025-11-18
created: 2025-01-07
estimate: 2-3 hours
assignee: dev
dependencies: [STORY-019a, STORY-019b, STORY-019c]
priority: high
parent_design: story-019-DESIGN.md
linear_issue: LEO-50
linear_url: https://linear.app/leoric-crown/issue/LEO-50/ebr-integration-testing-documentation
linear_status: Backlog
linear_branch: leonricardo314/leo-50-ebr-integration-testing-documentation
---

## Status
**SUPERSEDED** - Replaced by STORY-023e (Epic 004 - SQLite-First Architecture)

**Reason:** Testing and documentation requirements are included in STORY-023e acceptance criteria (AC4, AC5). The testing approach follows modern patterns with repository mocking and SQLite fixtures already established in the codebase.

**See:** `docs/stories/story-023e-multitestreportservice.md` for current implementation plan.

## Story
**As a** developer
**I want** integration tests and comprehensive documentation for the EBR feature
**So that** users understand how to use the tool and the system is validated end-to-end

## Acceptance Criteria

### AC1: Integration Test with CI Guidance
- [ ] File: `tests/integration/test_generate_multi_test_report.py`
- [ ] Mark with `@pytest.mark.integration`
- [ ] Use real TestIO API (requires `TESTIO_CUSTOMER_API_TOKEN`)
- [ ] Skip if credentials missing: `pytest.skip(reason="No API credentials")`
- [ ] Test end-to-end workflow:
  - Call generate_multi_test_report tool
  - Verify file written to disk
  - Verify file content contains expected sections
  - Verify metadata returned correctly
- [ ] Use `tmp_path` fixture for file operations
- [ ] Document test product IDs in docstring (use 25073: Customer A - test IO - HALO)
- [ ] **CI/CD Guidance:**
  - Integration tests run only when `TESTIO_CUSTOMER_API_TOKEN` is set
  - Local dev: Set in `.env` file (gitignored)
  - CI: Set as GitHub secret `TESTIO_CUSTOMER_API_TOKEN`
  - Tests skip gracefully if env var missing (won't block PR merge)

**Rationale:** Provides clear path for running tests locally and in CI without blocking development when credentials unavailable.

### AC2: Update CLAUDE.md
Add these sections:

**File-Output Tool Pattern:**
```markdown
### File Output Tools

Some tools write files to disk instead of returning content inline:

**Why write to file?**
- Reports can be large (100+ lines)
- Meant to be saved, shared, presented
- Consistent with document generation tools

**Pattern:**
1. Tool writes to `output_path`
2. Creates parent directories automatically
3. Returns metadata (not content)

**Example: generate_multi_test_report**
```python
# Returns metadata
{
    "success": True,
    "file_path": "/absolute/path/to/report.md",
    "file_size_bytes": 15240,
    "test_count": 12,
    "bug_count": 234,
    "summary": "Generated EBR for 2 products, 12 tests, 234 bugs"
}
```

**Usage Examples:**

**Via Natural Language (Claude):**
```
User: "Generate a Q4 2024 EBR for Customer A products and save to reports folder"

Claude calls:
generate_multi_test_report(
    product_ids=[25073],
    start_date="2024-10-01",
    end_date="2024-12-31",
    output_path="reports/customer_a_q4_2024.md"
)

✅ EBR report generated!
📄 File: /Users/Ricardo/reports/customer_a_q4_2024.md
📊 Size: 15.2 KB
🧪 Tests: 12
🐛 Bugs: 187
```

**Via MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector uv run python -m testio_mcp \
  --method tools/call \
  --tool-name generate_multi_test_report \
  --tool-arg 'product_ids=[25073]' \
  --tool-arg 'start_date="2024-10-01"' \
  --tool-arg 'end_date="2024-12-31"' \
  --tool-arg 'output_path="reports/ebr.md"'
```
```

### AC3: Create Formatter README
- [ ] File: `src/testio_mcp/formatters/README.md`
- [ ] Content:
  - Explain formatter pattern (service vs formatter separation)
  - Document data schema contract from service
  - Show how to add new formatters (step-by-step)
  - Include example: extending BaseReportFormatter

### AC4: Update Main README.md
- [ ] Add `generate_multi_test_report` to tools list
- [ ] Brief description: "Generate EBR reports for multiple tests"
- [ ] Link to CLAUDE.md for detailed usage

### AC5: Integration Test Coverage (Parameterized)
Create parameterized tests for these scenarios:
- [ ] `test_generate_markdown_single_product` - One product, markdown format
- [ ] `test_generate_markdown_multiple_products` - Multiple products, markdown format
- [ ] `test_generate_json_format` - JSON format output
- [ ] `test_different_date_fields` - Parameterized: start_at, created_at, end_at
- [ ] Verify file written with correct permissions
- [ ] Verify all 5 markdown sections present (in markdown tests)
- [ ] Verify metadata structure matches AC4 from STORY-019c

**Implementation:** Use `@pytest.mark.parametrize` for date_field tests to reduce duplication.

### AC6: Manual Testing Checklist with Artifact Requirement
Document these manual test scenarios **and record results in `docs/qa/manual-tests/story-019-ebr-manual-tests.md`**:

- [ ] Test via MCP Inspector (command-line) → Record command + output
- [ ] Test via Claude conversational interface → Record screenshot/transcript
- [ ] Compare output to ebr_tools reports for accuracy → Record diff/notes
- [ ] Test natural language date parsing → Record each format result:
  - "last 30 days"
  - "Q4 2024"
  - "this quarter"
  - ISO dates: "2024-10-01"
- [ ] Test error handling → Record error messages:
  - Invalid product ID
  - Invalid date format
  - No tests in date range
  - File permission errors

**Artifact:** Create `docs/qa/manual-tests/story-019-ebr-manual-tests.md` with test results table (pass/fail, notes, screenshots).

## Tasks / Subtasks

- [ ] Task 1: Write integration test (AC1)
  - [ ] Create test file
  - [ ] Add pytest integration marker
  - [ ] Import dependencies (tmp_path, real credentials)
  - [ ] Test markdown report generation
  - [ ] Test JSON report generation
  - [ ] Test file I/O
  - [ ] Test metadata response
  - [ ] Document test product IDs

- [ ] Task 2: Update CLAUDE.md (AC2)
  - [ ] Add "File Output Tools" section
  - [ ] Document pattern and rationale
  - [ ] Add generate_multi_test_report examples
  - [ ] Add MCP Inspector examples
  - [ ] Add natural language examples

- [ ] Task 3: Create formatter README (AC3)
  - [ ] Create src/testio_mcp/formatters/README.md
  - [ ] Document formatter pattern
  - [ ] Document service → formatter data contract
  - [ ] Show how to add new formatters
  - [ ] Include BaseReportFormatter example

- [ ] Task 4: Update main README (AC4)
  - [ ] Add generate_multi_test_report to tools list
  - [ ] Add brief description
  - [ ] Link to CLAUDE.md for details

- [ ] Task 5: Manual testing with artifact creation (AC6)
  - [ ] Create docs/qa/manual-tests/ directory
  - [ ] Create story-019-ebr-manual-tests.md file
  - [ ] Test via MCP Inspector → Record in artifact
  - [ ] Test via Claude UI → Record in artifact
  - [ ] Compare to ebr_tools output → Record in artifact
  - [ ] Test all date formats → Record in artifact
  - [ ] Test error scenarios → Record in artifact
  - [ ] Add pass/fail summary table to artifact

## Dev Notes

### Integration Test Pattern

**File Location:** `tests/integration/test_generate_multi_test_report.py`

**Key Patterns:**
```python
import pytest
from pathlib import Path

@pytest.mark.integration
async def test_generate_markdown_report(tmp_path):
    """Test end-to-end EBR report generation with real API.

    Uses product ID 25073 (Customer A - test IO - HALO) for testing.
    Requires TESTIO_CUSTOMER_API_TOKEN environment variable.
    """
    output_path = tmp_path / "ebr_report.md"

    # Call tool
    result = await generate_multi_test_report(
        product_ids=[25073],
        start_date="2024-10-01",
        end_date="2024-12-31",
        output_path=str(output_path)
    )

    # Verify metadata
    assert result["success"] is True
    assert result["test_count"] > 0
    assert result["bug_count"] >= 0
    assert "file_path" in result

    # Verify file written
    assert output_path.exists()

    # Verify content
    content = output_path.read_text()
    assert "Executive Summary" in content
    assert "Bug Status Breakdown" in content
    assert "Bug Type Distribution" in content
    assert "Bug Severity Analysis" in content
    assert "Test Performance" in content
```

### Formatter README Structure

**File:** `src/testio_mcp/formatters/README.md`

**Sections:**
1. **Overview** - Service + Formatter separation pattern
2. **Data Contract** - Schema from MultiTestReportService
3. **Adding New Formatters** - Step-by-step guide
4. **Example** - Custom formatter implementation

**Example Content:**
```markdown
# Report Formatters

## Pattern: Service + Formatter Separation

**Service Layer:** Fetches data, calculates metrics (NO formatting)
**Formatter Layer:** Renders output (NO API calls)

Benefits:
- Service reusable for multiple report types
- Formatters testable with mock data
- Easy to add formatters without touching service

## Data Contract

Formatters receive this schema from MultiTestReportService:

```python
{
    "bug_metrics": {
        "total": 234,
        "accepted": 170,
        # ... (full schema from AC5 in STORY-019a)
    },
    "test_metrics": {
        "test_count": 12,
        # ...
    }
}
```

## Adding a New Formatter

1. Create file: `src/testio_mcp/formatters/my_formatter.py`
2. Inherit from `BaseReportFormatter`
3. Implement `format(data, output_format)` method
4. Import in tool
5. Write unit tests with mock data

Example:
```python
from testio_mcp.formatters.base import BaseReportFormatter

class MyCustomFormatter(BaseReportFormatter):
    def format(self, data: dict, output_format: str) -> dict:
        # Render output
        return {"report": content, "data": data}
```
```

### Manual Testing Workflow

**1. MCP Inspector Test:**
```bash
npx @modelcontextprotocol/inspector uv run python -m testio_mcp \
  --method tools/call \
  --tool-name generate_multi_test_report \
  --tool-arg 'product_ids=[25073]' \
  --tool-arg 'start_date="last 30 days"' \
  --tool-arg 'end_date="today"' \
  --tool-arg 'output_path="test_report.md"'
```

**2. Claude Conversational Test:**
```
User: "Generate an EBR for Customer A covering October 2024"

Expected: Claude calls tool with correct date parsing
```

**3. Accuracy Validation:**
- Generate report via testio-mcp
- Generate equivalent report via ebr_tools
- Compare metrics (acceptance rates, counts, distributions)
- Document any discrepancies

### Documentation Cross-References

Update these files:
- **CLAUDE.md:** File output pattern, usage examples
- **README.md:** Tool list entry
- **formatters/README.md:** Formatter pattern guide
- **story-019-DESIGN.md:** Keep as technical reference

### Testing Standards

**Integration Test Requirements:**
- Mark with `@pytest.mark.integration`
- Skip if `TESTIO_CUSTOMER_API_TOKEN` missing
- Use `tmp_path` for file operations
- Document test product IDs
- Clean up files after test
- Test both markdown and JSON formats

**Manual Test Requirements:**
- Test via MCP Inspector (CLI)
- Test via Claude UI (conversational)
- Validate against ebr_tools output
- Test all date format variations
- Test error scenarios

### References
- **Design Doc:** docs/stories/story-019-DESIGN.md (lines 597-791, 920-956)
- **STORY-019a:** Service implementation
- **STORY-019b:** Formatter implementation
- **STORY-019c:** Tool implementation
- **STORY-016:** Tool testing patterns
- **ebr_tools:** `/Users/Ricardo_Leon1/TestIO/ebr_tools/` (accuracy baseline)

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-07 | 0.1 | Story created from story-019-DESIGN.md | Sarah (PO) |
| 2025-01-07 | 0.2 | Codex peer review fixes: Added CI/CD guidance for integration tests, parameterized test coverage, manual test artifact requirement (docs/qa/manual-tests/) | Sarah (PO) |

## Dev Agent Record
*This section will be populated during implementation*

## QA Results
*This section will be populated after QA review*
