# Story 008.059: MCP Prompts for Workflows

Status: drafted

## Story

As a user of the TestIO MCP server,
I want MCP prompts that act as active workflow templates,
So that I can efficiently invoke complex multi-step operations (Discover -> Summarize -> Analyze) with natural language.

## Background

MCP prompts are user-invoked templates that expand into structured instructions for AI agents. Unlike tools (which perform actions), prompts guide the agent through multi-step workflows. Users invoke prompts naturally (e.g., "analyze product quality for 18559 in Q3 2025") and the prompt expands into step-by-step instructions.

Key sources:
- [FastMCP Prompts](https://gofastmcp.com/servers/prompts)
- [MCP Prompts Spec](https://modelcontextprotocol.io/docs/concepts/prompts)

## Acceptance Criteria

1. [ ] Create MCP prompt: `analyze-product-quality`
   - **Purpose:** Guide agent through quality analysis workflow
   - **Type:** Static template (`.md` file loaded at runtime)
   - **Arguments:**
     - `product_id` (required): Product to analyze
     - `period` (optional, default "last 30 days"): Time range for analysis
     - `focus_area` (optional: "bugs", "tests", "acceptance"): Analysis focus
   - **Workflow:** sync_data → get_product_summary → get_product_quality_report → analyze results

2. [ ] Create MCP prompt: `explore-analytics`
   - **Purpose:** Provide live reference of available dimensions/metrics for custom queries
   - **Type:** Dynamic (code-generated at invocation time)
   - **Source:** Imports standalone registry builder functions from `analytics_service.py`
   - **Arguments:**
     - `topic` (optional): Focus area for suggested queries
   - **Content:** Lists all available dimensions (feature, product, tester, customer, severity, status, testing_type, month, week) and metrics (test_count, bug_count, bug_severity_score, features_tested, active_testers, bugs_per_test, tests_created, tests_submitted)
   - **Workflow:** Explains query_metrics usage with actual available options

3. [ ] Create MCP prompt: `explore-testio-data`
   - **Purpose:** Guide discovery using progressive disclosure (list → summarize → analyze)
   - **Type:** Static template (`.md` file loaded at runtime)
   - **Arguments:**
     - `entity_type` (optional: "products", "tests", "features", "users"): Entity to explore
   - **Workflow:** Funnel approach - discover IDs via list tools, drill down with summary tools

4. [ ] Prompts registered with FastMCP
   - All prompts use `@mcp.prompt` decorator
   - Prompts discoverable via MCP `prompts/list` protocol
   - Arguments properly typed and documented

5. [ ] Prompts accessible via MCP protocol
   - `prompts/get` returns correct content with argument substitution
   - Arguments validated and defaulted correctly
   - Error handling for missing required arguments

6. [ ] Documentation updated
   - `CLAUDE.md` updated with available prompts and usage examples

## Tasks / Subtasks

- [x] Task 1: Refactor AnalyticsService (AC2 prerequisite)
  - [x] Extract `_build_dimension_registry()` to module-level function
  - [x] Extract `_build_metric_registry()` to module-level function
  - [x] Ensure AnalyticsService still works (calls module functions)
  - [x] Unit test registry functions independently

- [x] Task 2: Create prompts directory structure
  - [x] Create `src/testio_mcp/prompts/` directory
  - [x] Create `__init__.py` with prompt registration

- [x] Task 3: Implement `analyze-product-quality` prompt (AC1)
  - [x] Create `analyze_product_quality.md` template
  - [x] Create `analyze_product_quality.py` loader with `@mcp.prompt` decorator
  - [x] Handle argument injection (product_id, period, focus_area)
  - [x] Unit test for rendering with various arguments

- [x] Task 4: Implement `explore-testio-data` prompt (AC3)
  - [x] Create `explore_testio_data.md` template
  - [x] Create `explore_testio_data.py` loader with `@mcp.prompt` decorator
  - [x] Handle argument injection (entity_type)
  - [x] Unit test for rendering

- [x] Task 5: Implement `explore-analytics` prompt (AC2)
  - [x] Create `explore_analytics.py` with dynamic generation
  - [x] Import registry builder functions from analytics_service
  - [x] Generate dimension/metric reference at invocation time
  - [x] Handle topic argument for focused guidance
  - [x] Unit test for dynamic rendering

- [x] Task 6: Integration & Registration (AC4, AC5)
  - [x] Import prompts module in `server.py`
  - [x] Verify `prompts/list` via MCP inspector
  - [x] Verify `prompts/get` with arguments via MCP inspector

- [x] Task 7: Documentation (AC6)
  - [x] Update `CLAUDE.md` with prompt usage section

## Dev Notes

### Architecture

```
src/testio_mcp/prompts/
├── __init__.py                    # Imports and registers all prompts
├── analyze_product_quality.py     # Loads .md, injects args, @mcp.prompt
├── analyze_product_quality.md     # Static workflow template
├── explore_testio_data.py         # Loads .md, injects args, @mcp.prompt
├── explore_testio_data.md         # Static workflow template
├── explore_analytics.py           # Dynamic generation, @mcp.prompt
```

### Template Pattern

Static prompts use `.md` files for easy editing:

```python
# analyze_product_quality.py
from pathlib import Path
from testio_mcp.server import mcp

TEMPLATE_PATH = Path(__file__).parent / "analyze_product_quality.md"

@mcp.prompt
def analyze_product_quality(
    product_id: int,
    period: str = "last 30 days",
    focus_area: str | None = None,
) -> str:
    """Analyze quality metrics for a TestIO product."""
    template = TEMPLATE_PATH.read_text()
    return template.format(
        product_id=product_id,
        period=period,
        focus_area=focus_area or "overall quality",
    )
```

### Dynamic Analytics Prompt

The `explore-analytics` prompt dynamically generates content from AnalyticsService registries:

```python
# explore_analytics.py
from testio_mcp.server import mcp
from testio_mcp.services.analytics_service import (
    build_dimension_registry,
    build_metric_registry,
)

@mcp.prompt
def explore_analytics(topic: str = "") -> str:
    """Explore available analytics dimensions and metrics."""
    dims = build_dimension_registry()
    metrics = build_metric_registry()

    # Build dynamic reference with descriptions and examples
    dim_list = "\n".join(f"- {k}: {v.description} (e.g., {v.example})" for k, v in dims.items())
    metric_list = "\n".join(f"- {k}: {v.description}" for k, v in metrics.items())

    return f"""You are an analytics assistant for TestIO data.

## Available Dimensions
{dim_list}

## Available Metrics
{metric_list}

## Query Pattern
Use query_metrics with:
- dimensions: Choose 1-2 from the list above
- metrics: Choose relevant metrics
- filters: Optional constraints (e.g., {{"severity": "critical"}})
- start_date/end_date: Date range (supports "last 30 days", ISO 8601)
- sort_by: Metric or dimension to sort by
- limit: Max rows to return

{f"Focus: {topic}" if topic else ""}
"""
```

### Testing Standards

- **Unit Tests:** Verify prompt string rendering with various argument combinations
- **Integration Tests:** Verify prompt registration and retrieval via MCP protocol
- Test file: `tests/unit/test_prompts.py`

### MCP Inspector Verification

```bash
# List prompts
npx @modelcontextprotocol/inspector --cli uv run python -m testio_mcp --method prompts/list

# Get prompt with arguments
npx @modelcontextprotocol/inspector --cli uv run python -m testio_mcp \
  --method prompts/get --prompt-name analyze-product-quality \
  --prompt-arg 'product_id="18559"' --prompt-arg 'period="Q3 2025"'
```

### References

- [Epic-008: MCP Layer Optimization](../epics/epic-008-mcp-layer-optimization.md)
- [FastMCP Prompts](https://gofastmcp.com/servers/prompts)
- [MCP Prompts Spec](https://modelcontextprotocol.io/docs/concepts/prompts)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

- `src/testio_mcp/prompts/__init__.py`
- `src/testio_mcp/prompts/analyze_product_quality.py`
- `src/testio_mcp/prompts/analyze_product_quality.md`
- `src/testio_mcp/prompts/explore_testio_data.py`
- `src/testio_mcp/prompts/explore_testio_data.md`
- `src/testio_mcp/prompts/explore_analytics.py`
- `src/testio_mcp/services/analytics_service.py` (modified - extracted registry builders)
- `src/testio_mcp/server.py` (modified - imports prompts module)
- `tests/unit/test_prompts.py`

## Senior Developer Review (AI)

### Reviewer
leoric

### Date
2025-11-28

### Outcome
**CHANGES REQUESTED** - LOW severity findings require attention before completion

### Summary

The MCP prompts implementation is **well-structured and follows FastMCP patterns correctly**. All 3 prompts are registered, accessible via MCP protocol, and have comprehensive unit tests (22 tests passing). The AnalyticsService refactoring to extract module-level registry builders was done correctly. CLAUDE.md documentation was updated (verified in staged changes).

**Minor issue:** Lint violations in prompts code need addressing.

---

### Key Findings (by Severity)

**LOW Severity:**

1. **Minor lint violations in prompts code** - 4 ruff errors:
   - Import sorting issue in `__init__.py`
   - 3 lines exceeding 100 char limit in `explore_analytics.py`

2. **Task checkboxes not marked in story** - All tasks are implemented but checkboxes remain unchecked.

---

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | Create `analyze-product-quality` prompt | ✅ IMPLEMENTED | `src/testio_mcp/prompts/analyze_product_quality.py:14-37`, `.md` template exists, arguments: product_id (required), period (default), focus_area (optional) |
| AC2 | Create `explore-analytics` prompt (dynamic) | ✅ IMPLEMENTED | `src/testio_mcp/prompts/explore_analytics.py:14-155`, imports `build_dimension_registry` and `build_metric_registry` from analytics_service, generates content at invocation time |
| AC3 | Create `explore-testio-data` prompt | ✅ IMPLEMENTED | `src/testio_mcp/prompts/explore_testio_data.py:74-115`, `.md` template with entity-specific guidance, supports 4 entity types |
| AC4 | Prompts registered with FastMCP | ✅ IMPLEMENTED | All use `@mcp.prompt(name="...")` decorator, verified via `prompts/list` inspector call |
| AC5 | Prompts accessible via MCP protocol | ✅ IMPLEMENTED | Verified 3 prompts in `prompts/list` output, arguments properly typed |
| AC6 | Documentation updated (CLAUDE.md) | ✅ IMPLEMENTED | Staged changes show "Available MCP Prompts (STORY-059)" section added at CLAUDE.md:26-29 |

**Coverage Summary:** 6 of 6 acceptance criteria fully implemented

---

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Refactor AnalyticsService | [ ] incomplete | ✅ DONE | `analytics_service.py:83-167` - `build_dimension_registry()` and `build_metric_registry()` are module-level functions, AnalyticsService uses them at line 296-297, unit tests in `test_prompts.py:234-279` |
| Task 2: Create prompts directory | [ ] incomplete | ✅ DONE | `src/testio_mcp/prompts/` exists with `__init__.py`, 3 `.py` files, 2 `.md` files |
| Task 3: Implement analyze-product-quality | [ ] incomplete | ✅ DONE | Python loader + markdown template + 5 unit tests (`test_prompts.py:20-67`) |
| Task 4: Implement explore-testio-data | [ ] incomplete | ✅ DONE | Python loader with `ENTITY_GUIDANCE` dict + markdown template + 8 unit tests (`test_prompts.py:70-127`) |
| Task 5: Implement explore-analytics | [ ] incomplete | ✅ DONE | Dynamic generation from registry, topic-based suggestions, 9 unit tests (`test_prompts.py:130-231`) |
| Task 6: Integration & Registration | [ ] incomplete | ✅ DONE | `server.py:433-437` imports prompts, verified via MCP inspector |
| Task 7: Documentation (CLAUDE.md) | [ ] incomplete | ✅ DONE | Staged changes show prompts section added at CLAUDE.md:26-29 |

**Task Summary:** 7 of 7 tasks verified complete

---

### Test Coverage and Gaps

**Unit Tests:** 22 tests in `tests/unit/test_prompts.py` - ALL PASSING

- `TestAnalyzeProductQualityPrompt`: 5 tests (argument combinations, workflow steps, key metrics)
- `TestExploreTestioDataPrompt`: 8 tests (all entity types, progressive disclosure pattern)
- `TestExploreAnalyticsPrompt`: 9 tests (dimensions, metrics, topics, dynamic registry verification)

**Coverage Assessment:** Excellent unit test coverage. No integration tests for `prompts/get` with arguments via MCP protocol, but unit tests validate rendering logic.

---

### Architectural Alignment

✅ **Follows FastMCP patterns** - Uses `@mcp.prompt` decorator correctly
✅ **Module-level registry functions** - Analytics service refactored per dev notes
✅ **Static templates for editable prompts** - `.md` files for workflow templates
✅ **Dynamic generation for analytics** - Generates from actual registry data
✅ **Auto-registration pattern** - Imports in server.py trigger registration

---

### Security Notes

No security concerns. Prompts are read-only templates with no sensitive data handling.

---

### Best-Practices and References

- [FastMCP Prompts Guide](https://gofastmcp.com/servers/prompts)
- [MCP Prompts Specification](https://modelcontextprotocol.io/docs/concepts/prompts)
- Pattern follows project's existing tool auto-discovery approach

---

### Action Items

**Code Changes Required:**

- [x] [Low] Fix ruff lint errors in prompts code
  - [x] Fix import sorting in `__init__.py` [file: src/testio_mcp/prompts/__init__.py:22-24]
  - [x] Wrap long lines in `explore_analytics.py` [file: src/testio_mcp/prompts/explore_analytics.py:54,72,81]

- [x] [Low] Mark completed task checkboxes in story file [file: docs/stories/story-059-mcp-prompts-for-workflows.md]

**Advisory Notes:**

- Note: Consider adding `prompts/get` integration test for E2E verification (not blocking)
- Note: The prompt naming uses kebab-case (`analyze-product-quality`) which aligns with MCP conventions
- Note: CLAUDE.md was already updated (verified in staged changes) - my initial grep missed staged changes

---

### Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-28 | 0.9 | Senior Developer Review notes appended - CHANGES REQUESTED |
