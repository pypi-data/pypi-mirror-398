# Epic Technical Specification: MCP Layer Optimization

Date: 2025-11-28
Author: leoric
Epic ID: epic-008-mcp-layer-optimization
Status: Draft

---

## Overview

The **MCP Layer Optimization** epic aims to significantly reduce token usage (target: 49% reduction) and establish a consistent "Discover → Summarize → Analyze" taxonomy across all MCP tools. It also introduces full REST API parity for all MCP tools to enable non-MCP clients. This initiative addresses the current context bloat caused by verbose tool schemas and inconsistent naming patterns, ensuring the server remains efficient and usable for AI agents as the feature set grows.

## Objectives and Scope

**Objectives:**
*   **Token Efficiency:** Reduce total tool schema token usage from ~12.8k to ~6.6k.
*   **Taxonomy Alignment:** Rename and restructure tools to follow `list_*` (Discover), `get_*_summary` (Summarize), and `query_metrics`/`get_product_quality_report` (Analyze) patterns.
*   **REST Parity:** Implement corresponding REST API endpoints for all active MCP tools.
*   **Metadata Enrichment:** Enhance list tools with computed counts (test/bug/feature counts) to provide better "information scent".

**In Scope:**
*   Renaming `get_test_status` to `get_test_summary` and `generate_ebr_report` to `get_product_quality_report`.
*   Creating new summary tools: `get_product_summary`, `get_feature_summary`, `get_user_summary`.
*   Consolidating diagnostic tools (`health_check`, `get_database_stats`, `get_sync_history`) into `get_server_diagnostics`.
*   Schema migrations: Add `product_type` to `products`, `title`/`testing_type` to `tests`, drop `tests.created_at`.
*   Adding pagination and sorting to all `list_*` tools.
*   Implementing REST endpoints for all new and renamed tools.

**Out of Scope:**
*   PostgreSQL migration (deferred).
*   GraphQL API.
*   Real-time WebSocket updates.
*   Modifying the core sync logic (handled in Epic 009).

## System Architecture Alignment

This epic aligns with the **Hybrid Server Architecture** defined in `ARCHITECTURE.md`, reinforcing the separation between the **Service Layer** (business logic) and the **Transport Layer** (MCP Tools / REST Endpoints).

*   **Service Layer:** New methods will be added to `TestService`, `ProductService`, and `UserService` to support summary retrieval and enriched listing. A new `DiagnosticsService` will centralize health and status logic.
*   **Data Access:** The **SQLite-first** strategy remains, with computed fields (counts) implemented as subqueries in repositories to ensure accuracy with the read-through cache.
*   **MCP Patterns:** The changes strictly follow the "Nested Pydantic Models" and "Schema Inlining" patterns described in `MCP.md` to ensure type safety and client compatibility.

## Detailed Design

### Services and Modules

| Module | Service | Responsibilities |
| :--- | :--- | :--- |
| `test_service.py` | `TestService` | **Modify:** Rename `get_test_status` -> `get_test_summary`. Add quality metrics (bug counts by severity). <br> **New:** Support sorting/filtering in `list_tests`. |
| `product_service.py` | `ProductService` | **New:** `get_product_summary` (metadata + counts). <br> **Modify:** Enrich `list_products` with counts. |
| `feature_service.py` | `FeatureService` | **New:** `get_feature_summary`. <br> **Modify:** Enrich `list_features` with counts and `has_user_stories` filter. |
| `user_service.py` | `UserService` | **New:** `get_user_summary`. <br> **Modify:** `list_users` with meaningful `last_activity` timestamps. |
| `diagnostics_service.py` | `DiagnosticsService` | **New:** Centralize logic for `get_server_diagnostics` (health, DB stats, sync history). |
| `product_quality_report_tool.py` | N/A (Tool) | **Rename:** From `generate_ebr_report_tool.py`. Slim down schema. |

### Data Models and Contracts

**Schema Changes (SQLite & ORM):**

*   **`products` table:**
    *   Add `product_type` (VARCHAR, nullable) - Extracted from JSON `type`.
*   **`tests` table:**
    *   Add `title` (VARCHAR, indexed) - Extracted from JSON `title`.
    *   Add `testing_type` (VARCHAR, indexed) - Extracted from JSON `testing_type`.
    *   Drop `created_at` (unused/null).

**Computed Fields (Subqueries):**
*   `Product`: `test_count`, `bug_count`, `feature_count`
*   `Feature`: `test_count`, `bug_count`
*   `User`: `last_activity` (derived from tests/bugs timestamps)

### APIs and Interfaces

**New/Renamed MCP Tools:**
*   `get_test_summary(test_id: int)`
*   `get_product_quality_report(product_id: int, ...)`
*   `get_product_summary(product_id: int)`
*   `get_feature_summary(feature_id: int)`
*   `get_user_summary(user_id: int)`
*   `get_server_diagnostics(include_sync_events: bool = False)`

**New REST Endpoints:**
*   `GET /api/tests/{id}/summary`
*   `GET /api/products/{id}/summary`
*   `GET /api/features/{id}/summary`
*   `GET /api/users/{id}/summary`
*   `GET /api/products/{id}/quality-report`
*   `GET /api/diagnostics`

### Workflows and Sequencing

**Exploration Workflow:**
1.  **Discover:** Agent calls `list_products` (sees counts/activity).
2.  **Summarize:** Agent calls `get_product_summary` for selected product.
3.  **Analyze:** Agent calls `get_product_quality_report` or `query_metrics` for deep dive.

## Non-Functional Requirements

### Performance
*   **Token Usage:** Total tool schema context must be < 7,000 tokens.
*   **Latency:** List tools with computed counts must respond in < 500ms (SQLite subqueries).
*   **Query Optimization:** Ensure new indices on `product_type`, `title`, and `testing_type` are used.

### Security
*   **Authentication:** All new REST endpoints must require `Authorization: Token <token>`.
*   **Input Validation:** Strict Pydantic validation for all new parameters (pagination, sorting).

### Reliability/Availability
*   **Backward Compatibility:** Breaking changes allowed for MCP tools (clean break strategy). REST API is new, so no breaking changes there.
*   **Diagnostics:** Consolidated diagnostics tool must provide accurate system health status.

### Observability
*   **Logging:** Log deprecation warnings for old diagnostic tools if called.
*   **Metrics:** Track usage of new summary tools.

## Dependencies and Integrations

*   **Internal:** Depends on **Epic 007** (Analytics Framework) for repository patterns.
*   **External:** None.

## Acceptance Criteria (Authoritative)

1.  **Renaming & Taxonomy:**
    *   `get_test_status` renamed to `get_test_summary`.
    *   `generate_ebr_report` renamed to `get_product_quality_report`.
    *   `list_user_stories` removed.
    *   `get_analytics_capabilities` disabled by default.
2.  **Schema Migration:**
    *   `products.product_type` column added and backfilled.
    *   `tests.title` and `tests.testing_type` columns added and backfilled.
    *   `tests.created_at` column dropped.
3.  **Standardization:**
    *   All `list_*` tools support `page`, `per_page`, `offset`.
    *   All `list_*` tools support `sort_by`, `sort_order`.
4.  **Token Optimization:**
    *   Total schema token usage < 6,600.
    *   `get_product_quality_report` schema < 1,000 tokens.
5.  **New Tools:**
    *   `get_product_summary`, `get_feature_summary`, `get_user_summary` implemented.
    *   `get_server_diagnostics` implemented (consolidating 3 tools).
6.  **REST Parity:**
    *   REST endpoints exist for all active MCP tools.
    *   OpenAPI documentation generated and valid.

## Traceability Mapping

| Acceptance Criteria | Component | API / Tool | Test Idea |
| :--- | :--- | :--- | :--- |
| Rename `get_test_status` | `test_summary_tool.py` | `get_test_summary` | Verify tool name and output structure |
| Rename `generate_ebr_report` | `product_quality_report_tool.py` | `get_product_quality_report` | Verify tool name and schema size |
| Schema Migration | `alembic/versions` | N/A | Verify DB schema after migration |
| Pagination/Sorting | `repositories/*.py` | `list_*` | Test sorting by various fields |
| Summary Tools | `*_service.py` | `get_*_summary` | Verify summary content and counts |
| Diagnostics Consolidation | `diagnostics_service.py` | `get_server_diagnostics` | Verify all stats included |
| REST Parity | `api.py` | `/api/*` | Verify HTTP 200 and JSON response |

## Risks, Assumptions, Open Questions

*   **Risk:** Computed subqueries for counts might be slow on very large datasets.
    *   *Mitigation:* Monitor performance; indices added. SQLite is generally fast enough for current scale.
*   **Assumption:** Breaking changes to tool names are acceptable for the user base (internal/beta).
*   **Question:** Should we alias old tool names for a transition period?
    *   *Decision:* No, clean break to minimize context bloat (as per Epic 008).

## Test Strategy Summary

*   **Unit Tests:**
    *   Test new Service methods (`get_*_summary`).
    *   Test Repository subqueries and sorting logic.
    *   Test Pydantic models for schema correctness.
*   **Integration Tests:**
    *   Verify MCP tool execution flow.
    *   Verify REST API endpoints return correct data and status codes.
    *   Verify database migrations (up/down).
*   **Token Measurement:**
    *   Run `scripts/measure_tool_tokens.py` to validate reduction targets.
