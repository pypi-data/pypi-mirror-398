---
story_id: STORY-019c
epic_id: EPIC-003
title: MCP Tool Integration & File Output
status: superseded
superseded_by: STORY-023e
superseded_date: 2025-11-18
created: 2025-01-07
estimate: 2-3 hours
assignee: dev
dependencies: [STORY-019a, STORY-019b]
priority: high
parent_design: story-019-DESIGN.md
linear_issue: LEO-49
linear_url: https://linear.app/leoric-crown/issue/LEO-49/mcp-tool-integration-and-file-output
linear_status: Backlog
linear_branch: leonricardo314/leo-49-mcp-tool-integration-file-output
---

## Status
**SUPERSEDED** - Replaced by STORY-023e (Epic 004 - SQLite-First Architecture)

**Reason:** MCP tool integration is included in STORY-023e acceptance criteria (AC3). The tool implementation follows the simplified architecture with repository pattern and shared utilities already in place.

**See:** `docs/stories/story-023e-multitestreportservice.md` for current implementation plan.

## Story
**As a** CSM
**I want** an MCP tool that orchestrates report generation and writes files to disk
**So that** I can request EBR reports via natural language and receive a saved file

## Acceptance Criteria

### AC1: Create generate_multi_test_report Tool
- [ ] File: `src/testio_mcp/tools/generate_multi_test_report_tool.py`
- [ ] Tool signature:
  ```python
  async def generate_multi_test_report(
      product_ids: list[int],
      start_date: str,
      end_date: str,
      output_path: str,
      date_field: Literal["created_at", "start_at", "end_at"] = "start_at",
      report_type: Literal["ebr"] = "ebr",
      format: Literal["markdown", "json"] = "markdown",
      ctx: Context = None
  ) -> dict
  ```
- [ ] Use `@mcp.tool()` decorator
- [ ] Tool auto-registers via server.py pkgutil discovery
- [ ] **Add to tool docstring:** Recommend using `output_path='reports/filename.md'` or `output_path='output/filename.md'` to avoid accidentally overwriting code files. Path validation allows any workspace location but following this convention improves safety.

### AC2: Orchestration Workflow
Tool orchestrates this flow:
1. Parse date strings using `parse_date_input()` from `testio_mcp.utilities.date_filters`
2. Create MultiTestReportService via `get_service()` helper
3. Call `service.discover_and_fetch_tests()` to get test data
4. Call `service.aggregate_report_data()` to get metrics
5. Create EbrFormatter instance
6. Call `formatter.format()` to generate report
7. Write report to file (create parent dirs if needed)
8. Return metadata dict

**Date Parsing:** Use public `parse_date_input()` from utilities (created in STORY-019a AC1), not private ActivityService method.

### AC3: File I/O Implementation with Security
- [ ] Use `pathlib.Path` for path operations
- [ ] Define allowed output root (workspace directory): `Path.cwd()`
- [ ] **CRITICAL - Security validation (filesystem-safe check):**
  ```python
  output_path = Path(output_path).expanduser().resolve()
  allowed_root = Path.cwd().resolve()

  # Verify output path is within workspace using filesystem-safe check
  try:
      output_path.relative_to(allowed_root)
  except ValueError:
      raise ToolError(
          "❌ Invalid path: Output must be within workspace directory\n"
          f"ℹ️ Workspace: {allowed_root}\n"
          f"💡 Use relative paths or paths under {allowed_root}"
      )
  ```
- [ ] Create parent directories: `.parent.mkdir(parents=True, exist_ok=True)`
- [ ] Write file: `.write_text(report_content)`
- [ ] Handle existing files: Overwrite without warning (MVP behavior)

**Security Rationale:**
- **DO NOT use `str.startswith()`** - vulnerable to path traversal (e.g., `/workspace_backup/` bypasses `/workspace/` check)
- **USE `Path.relative_to()`** - filesystem-safe check that raises `ValueError` if path is outside allowed root
- **ALSO handle symlinks:** `resolve()` follows symlinks, preventing symlink-based escapes
- **expanduser()** handles `~` paths correctly before resolving

### AC4: Return Metadata (Not Content)
Return this structure:
```python
{
    "success": True,
    "file_path": "/absolute/path/to/report.md",  # Absolute resolved path
    "file_size_bytes": 15240,
    "test_count": 12,
    "bug_count": 234,
    "products": ["Product A", "Product B"],
    "date_range": "2024-10-01 to 2024-12-31",
    "summary": "Generated EBR for 2 products, 12 tests, 234 bugs"
}
```

**Rationale:** Reports are meant to be saved/shared (not displayed inline), consistent with document generation tools.

### AC5: Error Handling
Transform domain exceptions to ToolError with ❌ℹ️💡 format:

- [ ] `ProductNotFoundException` → "❌ Product ID not found\nℹ️ Product may be deleted\n💡 Verify product ID with list_products"
- [ ] `DateParseException` → "❌ Invalid date format\nℹ️ Expected ISO 8601 or relative dates\n💡 Examples: '2024-10-01', 'last 30 days', 'Q4 2024'"
- [ ] `NoTestsFoundException` (from STORY-019a AC8) → "❌ No tests in date range\nℹ️ Filters may be too restrictive\n💡 Try wider date range or different date_field"
- [ ] File write error (OSError, PermissionError) → "❌ Cannot write file\nℹ️ Permission denied or invalid path\n💡 Check directory permissions"
- [ ] Empty product_ids → "❌ No products specified\nℹ️ At least one product ID required\n💡 Use list_products to find IDs"

### AC6: Tool Unit Tests
- [ ] File: `tests/unit/test_tools_generate_multi_test_report.py`
- [ ] Mock context, service, formatter
- [ ] Test error transformations (domain exceptions → ToolError)
- [ ] Test service delegation (parameters passed correctly)
- [ ] Test input validation (Pydantic edge cases)
- [ ] Coverage >85%

## Tasks / Subtasks

- [ ] Task 1: Create MCP tool file (AC1)
  - [ ] Create src/testio_mcp/tools/generate_multi_test_report_tool.py
  - [ ] Import dependencies (Context, ToolError, get_service, etc.)
  - [ ] Add @mcp.tool() decorator
  - [ ] Define tool signature with type hints
  - [ ] Add comprehensive docstring (visible in Claude UI)

- [ ] Task 2: Implement orchestration workflow (AC2)
  - [ ] Import parse_date_input from testio_mcp.utilities.date_filters
  - [ ] Parse start_date and end_date strings
  - [ ] Create MultiTestReportService via get_service()
  - [ ] Call discover_and_fetch_tests()
  - [ ] Call aggregate_report_data()
  - [ ] Create EbrFormatter
  - [ ] Call formatter.format()

- [ ] Task 3: Implement file I/O with security (AC3)
  - [ ] Define allowed_root (Path.cwd())
  - [ ] Expand user paths (~) and resolve output_path to absolute
  - [ ] **CRITICAL:** Validate path is within workspace using `Path.relative_to()` (NOT `str.startswith()`)
  - [ ] Catch ValueError from relative_to() to detect path traversal attempts
  - [ ] Create parent directories
  - [ ] Write file
  - [ ] Calculate file size

- [ ] Task 4: Build metadata response (AC4)
  - [ ] Extract metrics from aggregated data
  - [ ] Format date range string
  - [ ] Build summary message
  - [ ] Return structured dict

- [ ] Task 5: Add error handling (AC5)
  - [ ] Wrap service calls in try/except
  - [ ] Transform ProductNotFoundException
  - [ ] Transform DateParseException
  - [ ] Transform NoTestsFoundException (from STORY-019a)
  - [ ] Transform file write errors (OSError, PermissionError)
  - [ ] Transform validation errors (empty product_ids)

- [ ] Task 6: Write unit tests (AC6)
  - [ ] Create test file
  - [ ] Mock Context, MultiTestReportService, EbrFormatter
  - [ ] Patch get_service()
  - [ ] Test error transformations
  - [ ] Test service delegation
  - [ ] Test input validation
  - [ ] Achieve >85% coverage

## Dev Notes

### Tool Testing Pattern (Story-016)

Extract function from FastMCP wrapper and test directly:

```python
# tests/unit/test_tools_generate_multi_test_report.py
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.tools.generate_multi_test_report_tool import (
    generate_multi_test_report as generate_multi_test_report_tool
)

# Extract actual function from FastMCP FunctionTool wrapper
generate_multi_test_report = generate_multi_test_report_tool.fn  # type: ignore

@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_not_found_to_tool_error():
    """Verify ProductNotFoundException → ToolError with ❌ℹ️💡."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.discover_and_fetch_tests.side_effect = ProductNotFoundException(123)

    with patch("testio_mcp.tools.generate_multi_test_report_tool.get_service",
               return_value=mock_service):
        with pytest.raises(ToolError) as exc_info:
            await generate_multi_test_report(
                product_ids=[123],
                start_date="2024-10-01",
                end_date="2024-12-31",
                output_path="report.md",
                ctx=mock_ctx
            )

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "not found" in error_msg.lower()
        assert "ℹ️" in error_msg
        assert "💡" in error_msg
```

### File Output Security

**Path Traversal Prevention (matches AC3):**

Use `Path.relative_to()` for filesystem-safe validation as specified in AC3. The acceptance criteria provide the correct, secure implementation that prevents path traversal attacks.

### Natural Language Example Usage

**Via Claude Conversational Interface:**
```
User: "Generate a Q4 2024 EBR for Saatva products and save to reports folder"

Claude:
[Calls generate_multi_test_report(
    product_ids=[25073, 25074],
    start_date="2024-10-01",
    end_date="2024-12-31",
    output_path="reports/saatva_q4_2024.md"
)]

✅ EBR report generated!

📄 File: /Users/Ricardo/testio-mcp/reports/saatva_q4_2024.md
📊 Size: 15.2 KB
🧪 Tests analyzed: 12
🐛 Bugs found: 187

The report covers 2 products across Q4 2024.
```

### Date Parsing (Use Public Utility)

Support these formats:
- **ISO 8601:** `"2024-10-01"`, `"2024-Q4"`
- **Relative:** `"last 30 days"`, `"this quarter"`
- **Business:** `"Q4 2024"`, `"October 2024"`

**Implementation (CORRECTED):**
```python
from testio_mcp.utilities.date_filters import parse_date_input

# In tool implementation:
parsed_start = parse_date_input(start_date, is_end_date=False)
parsed_end = parse_date_input(end_date, is_end_date=True)
```

**Why:** STORY-019a AC1 extracts `parse_date_input()` into public utilities module. Do NOT use private `ActivityService._parse_date_input()` method.

### Source Tree
```
src/testio_mcp/
├── tools/
│   └── generate_multi_test_report_tool.py  # NEW: MCP tool

tests/
├── unit/
│   └── test_tools_generate_multi_test_report.py  # NEW
```

### Tool Registration (Automatic)

Tool auto-registers via server.py pkgutil discovery (ADR-011):
- No manual imports needed
- Just create `*_tool.py` file with `@mcp.tool()` decorator
- Server discovers and registers at startup

### References
- **Design Doc:** docs/stories/story-019-DESIGN.md (lines 465-490, 815-840, 920-956)
- **STORY-019a:** MultiTestReportService API
- **STORY-019b:** EbrFormatter API
- **STORY-016:** Tool testing patterns
- **ADR-007:** FastMCP Context Injection
- **ADR-011:** get_service() helper, ToolError pattern

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-07 | 0.1 | Story created from story-019-DESIGN.md | Sarah (PO) |
| 2025-01-07 | 0.2 | Codex peer review fixes: Corrected path traversal security (workspace anchoring), aligned date parser to public utility, clarified NoTestsFoundException handling | Sarah (PO) |
| 2025-01-07 | 0.3 | **Codex technical review fix:** AC1: Added tool docstring recommendation to use `output_path='reports/*.md'` or `output_path='output/*.md'` to avoid accidentally overwriting code files. Keeps flexible Path.cwd() validation but documents safety best practice. No estimate change (documentation only). | Bob (SM) + Codex |

## Dev Agent Record
*This section will be populated during implementation*

## QA Results
*This section will be populated after QA review*
