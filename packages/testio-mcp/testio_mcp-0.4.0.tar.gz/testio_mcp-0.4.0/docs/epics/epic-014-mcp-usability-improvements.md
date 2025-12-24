# Epic 014: MCP Usability Improvements

**Source:** `docs/planning/mcp-usability-feedback.md` (Customer EBR analysis)
**Date:** 2025-12-01

---

## Overview

**Goal:** Improve data clarity, add bug drill-down tools, and enhance prompts for quality analysis workflows.

**Value:** CSMs can trust report data, investigate rejection patterns efficiently, and get actionable guidance for EBR preparation.

---

## Functional Requirements Summary

| FR | Description | Source Issue |
|----|-------------|--------------|
| FR1 | Null handling for rate metrics when `total_bugs=0` | Issue #1 |
| FR2 | Rate metrics in `query_metrics` (acceptance_rate, rejection_rate, review_rate) | Issue #5 |
| FR3 | Null vs zero for uncached bug counts in `list_products` | Issue #4 |
| FR4 | Enhanced `analyze-product-quality` prompt with rejection analysis | Prompt Enhancement #1 |
| FR5 | Bug drill-down tools (`list_bugs`, `get_bug_summary`) + prompt update | Issue #7, Friction #2 |

---

## Stories

### STORY-081: Null Handling for Rate Metrics (FR1)

**As a** CSM reviewing quality reports,
**I want** rate metrics to show `null`/`N/A` when no bugs exist,
**So that** I don't misinterpret "0%" as "perfect quality" vs "no data."

**Acceptance Criteria:**
- **Given** a test with 0 bugs reported
- **When** `get_product_quality_report` calculates rejection_rate
- **Then** rejection_rate is `null`, not `0.0`

- **Given** `query_metrics` aggregates by month with 0 bugs for a month
- **When** rate metrics are calculated
- **Then** rates are `null` for that month

**Technical Notes:**
- Modify `src/testio_mcp/utilities/bug_classifiers.py` `calculate_acceptance_rates()`
- Return `None` instead of `0.0` when `total_bugs == 0`
- Update Pydantic models to allow `float | None` for rate fields

**Prerequisites:** None

---

### STORY-082: Rate Metrics in query_metrics (FR2)

**As a** CSM analyzing quality trends,
**I want** to query acceptance_rate, rejection_rate, review_rate as metrics,
**So that** I can create trend reports without manual calculation.

**Acceptance Criteria:**
- **Given** `get_analytics_capabilities()` is called
- **When** I inspect available metrics
- **Then** I see: `overall_acceptance_rate`, `rejection_rate`, `review_rate`, `active_acceptance_rate`, `auto_acceptance_rate`

- **Given** `query_metrics(dimensions=["month"], metrics=["rejection_rate"], filters={"product_id": X})`
- **When** executed
- **Then** returns rejection_rate per month (using formulas from `bug_classifiers.py`)

- **Given** a month with 0 bugs
- **When** rate metrics are queried
- **Then** rate values are `null` (per STORY-081)

**Technical Notes:**
- Add rate metrics to `src/testio_mcp/services/analytics_service.py` metrics registry
- Formulas already exist in `bug_classifiers.py:110-198`
- Ensure null handling per STORY-081

**Prerequisites:** STORY-081

---

### STORY-083: Null vs Zero for Uncached Bug Counts (FR3)

**As a** CSM listing products,
**I want** `bug_count` to distinguish "not synced" from "zero bugs",
**So that** I know when to call `sync_data` vs trust the count.

**Acceptance Criteria:**
- **Given** a fresh server with no bug sync
- **When** `list_products` is called
- **Then** `bug_count` is `null` (not `0`)

- **Given** `sync_data` has run and product has 0 bugs
- **When** `list_products` is called
- **Then** `bug_count` is `0` (confirmed zero)

**Technical Notes:**
- Modify `src/testio_mcp/services/product_service.py` `list_products()`
- Track `bugs_synced_at` per product (new column or check cache metadata)
- Return `None` if never synced, `0` if synced and confirmed zero

**Prerequisites:** None

---

### STORY-084: list_bugs Tool (FR5a)

**As a** CSM investigating high rejection tests,
**I want** to list bugs for specific tests with filters,
**So that** I can see rejection patterns without loading all product bugs.

**Acceptance Criteria:**
- **Given** `list_bugs(test_ids=[123, 456])`
- **When** executed
- **Then** returns bugs only for those tests, with pagination

- **Given** `list_bugs(test_ids=[123], status="rejected", severity=["critical", "high"])`
- **When** executed
- **Then** returns only rejected critical/high bugs (AND logic)

- **Given** `list_bugs(test_ids=[123], rejection_reason="not_reproducible")`
- **When** executed
- **Then** returns bugs rejected for that reason

**Parameters:**
```python
test_ids: list[int]  # REQUIRED - scopes query
severity: str | list[str] | None  # critical, high, medium, low
status: str | list[str] | None  # accepted, rejected, auto_accepted, forwarded, pending
rejection_reason: str | list[str] | None  # not_reproducible, intended_behavior, etc.
reported_by_user_id: int | None  # tester filter
# Standard pagination: page, per_page, offset
# Standard sorting: sort_by (title, severity, status, reported_at), sort_order
```

**Return Format (minimal):**
```python
{
    "bugs": [
        {"id": int, "title": str, "severity": str, "status": str, "test_id": int, "reported_at": str}
    ],
    "pagination": {...},
    "filters_applied": {...}
}
```

**Technical Notes:**
- New file: `src/testio_mcp/tools/list_bugs_tool.py`
- New service method: `BugService.list_bugs()`
- Query via BugRepository with filters
- Follow `list_tests` pattern for structure

**Prerequisites:** None

---

### STORY-085: get_bug_summary Tool (FR5b)

**As a** CSM drilling into a specific bug,
**I want** full bug details including rejection reason and reporter,
**So that** I can understand why a bug was rejected.

**Acceptance Criteria:**
- **Given** `get_bug_summary(bug_id=12345)`
- **When** executed
- **Then** returns full bug details including:
  - Core: id, title, severity, status, known
  - Details: actual_result, expected_result, steps
  - Rejection: rejection_reason (if rejected)
  - Attribution: reported_by_user (username, id), test (id, title), feature (if linked)
  - Metadata: reported_at, data_as_of

- **Given** invalid bug_id
- **When** `get_bug_summary` called
- **Then** raises ToolError with helpful message

**Technical Notes:**
- New file: `src/testio_mcp/tools/get_bug_summary_tool.py`
- New service method: `BugService.get_bug_summary()`
- Follow `get_test_summary` pattern
- Include related entities (user, test, feature)

**Prerequisites:** None (can parallel with STORY-084)

---

### STORY-086: Update explore-testio-data Prompt (FR5c)

**As a** user exploring TestIO data,
**I want** the prompt to guide me through bug analysis,
**So that** I know how to drill into rejection patterns.

**Acceptance Criteria:**
- **Given** `explore-testio-data` prompt is invoked
- **When** user asks about bugs
- **Then** prompt guides to:
  1. Discovery: `list_bugs(test_ids=[X], status="rejected")`
  2. Summary: `get_bug_summary(bug_id=Y)`
  3. Analysis: `query_metrics(dimensions=["rejection_reason"], ...)`

**Technical Notes:**
- Modify `src/testio_mcp/prompts/explore_testio_data.py`
- Add "bugs" entity to ENTITY_GUIDANCE dict

**Prerequisites:** STORY-084, STORY-085

---

### STORY-087: Enhanced analyze-product-quality Prompt (FR4)

**As a** CSM analyzing product quality,
**I want** the prompt to guide me through rejection analysis,
**So that** I can diagnose "noisy cycle" patterns.

**Acceptance Criteria:**
- **Given** `analyze-product-quality` prompt
- **When** a test has rejection_rate > 30%
- **Then** prompt suggests:
  1. Query rejection reasons: `query_metrics(dimensions=["rejection_reason"], ...)`
  2. Match to CSM Playbook patterns
  3. Compare test instructions

- **Given** prompt output
- **When** rejection_reason breakdown shown
- **Then** includes interpretation guide (ignored_instructions → noisy cycle, etc.)

**Technical Notes:**
- Modify `src/testio_mcp/prompts/analyze_product_quality.py`
- Add "Diagnosing High Rejection Tests" section
- Reference CSM Playbook patterns

**Prerequisites:** STORY-082 (rate metrics available)

---

## FR Coverage Matrix

| FR | Stories |
|----|---------|
| FR1 | STORY-081 |
| FR2 | STORY-082 |
| FR3 | STORY-083 |
| FR4 | STORY-087 |
| FR5 | STORY-084, STORY-085, STORY-086 |

---

## Critical Files

- `src/testio_mcp/utilities/bug_classifiers.py` - rate calculations (STORY-081, STORY-082)
- `src/testio_mcp/services/analytics_service.py` - metrics registry (STORY-082)
- `src/testio_mcp/services/product_service.py` - list_products (STORY-083)
- `src/testio_mcp/tools/list_bugs_tool.py` (NEW - STORY-084)
- `src/testio_mcp/tools/get_bug_summary_tool.py` (NEW - STORY-085)
- `src/testio_mcp/services/bug_service.py` - new methods (STORY-084, STORY-085)
- `src/testio_mcp/repositories/bug_repository.py` - queries (STORY-084, STORY-085)
- `src/testio_mcp/prompts/explore_testio_data.py` - prompt update (STORY-086)
- `src/testio_mcp/prompts/analyze_product_quality.py` - prompt enhancement (STORY-087)

---

## Suggested Implementation Order

1. **STORY-081** (FR1) - Foundation for all rate handling
2. **STORY-084** (list_bugs) - Can start in parallel
3. **STORY-085** (get_bug_summary) - Can start in parallel
4. **STORY-082** (FR2) - Depends on STORY-081
5. **STORY-083** (FR3) - Independent
6. **STORY-086** (prompt) - After STORY-084, STORY-085
7. **STORY-087** (FR4) - After STORY-082
