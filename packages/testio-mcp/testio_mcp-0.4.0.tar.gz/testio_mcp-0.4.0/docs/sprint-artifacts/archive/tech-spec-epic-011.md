# Epic Technical Specification: Showcase & Polish

Date: 2025-11-29
Author: Ricardo_Leon1
Epic ID: 011
Status: Draft

---

## Overview

Epic 011: Showcase & Polish marks a strategic shift from feature development to demonstrating the "Context-Aware" capabilities of the TestIO MCP Server. The primary goal is to enable two high-value scenarios for Customer Success Managers (CSMs): the "Tactical Detective" (operational root cause analysis) and the "Strategic Analyst" (EBR/QBR trend analysis). This involves creating a new "Knowledge Resource" (the Playbook) and polishing existing tools to ensure they support these workflows robustly.

## Objectives and Scope

**In-Scope:**
*   **Knowledge Resource:** Create and expose `testio://knowledge/playbook` as an MCP resource containing expert heuristics.
*   **Tool Polish:**
    *   **STORY-067 (Tactical Detective):**
        *   **Rejection Reason Parsing (Clean Architecture):**
            *   **Context:** Rejection reasons are embedded in bug comments, not structured fields.
            *   **Strategy:** Use the **Transformer Pattern** to parse comments during data ingestion and denormalize the result into a new `rejection_reason` column in the `bugs` table.
            *   **Verified Patterns:** Analysis of 2,124 rejected bugs confirmed 100% coverage using the standard API list plus one discovered system pattern:
                *   `request_timeout`: "Your bug was rejected automatically, because you didn't respond to the request within 24 hours"
            *   **Components:**
                1.  **Schema Constant:** Add `REJECTION_REASONS` to `src/testio_mcp/schemas/constants.py` (including `request_timeout`).
                2.  **ORM Model:** Add `rejection_reason` (TEXT, nullable) to `src/testio_mcp/models/orm/bug.py`.
                3.  **Transformer:** Create `src/testio_mcp/transformers/bug_transformers.py` with `transform_api_bug_to_orm` function. This function will:
                    *   Accept raw API bug dictionary.
                    *   Parse `comments` against `REJECTION_REASONS`.
                    *   Return a dictionary suitable for `Bug` model instantiation.
                4.  **Repository:** Update `BugRepository._write_bugs_to_db` to use the transformer instead of inline logic.
            *   **Benefit:** Keeps the Repository clean (data access only) and the Service clean (business logic only). Parsing logic is encapsulated in the Transformer (Anti-Corruption Layer).
        *   **Instruction Text:** Verify `get_test_summary` returns the full, untruncated `instructions` text. (no truncation).
    *   **STORY-068 (Strategic Analyst):**
        *   Enhance `query_metrics` to support a "quarter" dimension for long-term trend analysis.
        *   Enhance `query_metrics` to support a "rejection_reason" dimension (leveraging data from STORY-067).
*   **Scenario Validation:**
    *   Validate the "Tactical Detective" workflow: Correlating "vague instructions" with "rejection patterns" using the Playbook.
    *   Validate the "Strategic Analyst" workflow: Generating quarterly quality trend reports using the Playbook templates.

**Out-of-Scope:**
*   New major features or architectural overhauls.
*   Modifications to the core sync engine or database schema.
*   Customer-facing "Context Integration" scenario (deferred to a later epic).

## System Architecture Alignment

*   **MCP Resources:** This epic introduces the first use of MCP Resources (`@mcp.resource`) in the system, expanding the server's capabilities beyond Tools and Prompts. This aligns with the "Context-Aware" vision.
*   **Service Layer:** Updates to `AnalyticsService` will follow the existing "Metric Cube" pattern, adding a new dimension without altering the core logic.
*   **Tool Layer:** Enhancements to `query_metrics` and verification of `get_test_summary` respect the existing tool contracts and thin-wrapper design.

## Detailed Design

### Services and Modules

| Module | Responsibility | Changes |
| :--- | :--- | :--- |
| `src/testio_mcp/resources.py` | Handle MCP resource registration and serving. | **New Module**: Implement `register_resources()` and resource handlers. |
| `src/testio_mcp/services/analytics_service.py` | Dynamic query construction. | Update `build_dimension_registry` to include "quarter" dimension using SQLite date functions. |
| `src/testio_mcp/server.py` | Server initialization. | Import and register resources module. |

### Data Models and Contracts

**Playbook Structure (Markdown):**
```markdown
# TestIO CSM Playbook

## Tactical Patterns (Operational)
### Pattern: The "Noisy" Cycle
- **Signals:** High rejection rate (>30%), "Out of Scope" rejections, Short instructions (<20 words).
- **Diagnosis:** Vague instructions led to tester confusion.
- **Action:** Coach customer on "Scope Definition".

## Strategic Templates (EBR/QBR)
### Template: Quarterly Quality Review
- **Metrics:** Bug Count, Acceptance Rate, Severity Breakdown.
- **Grouping:** Quarterly.
- **Narrative:** Focus on trends (improving vs declining).
```

### APIs and Interfaces

**MCP Resource:**
*   **URI:** `testio://knowledge/playbook`
*   **MIME Type:** `text/markdown`
*   **Description:** "Expert heuristics for analyzing TestIO data (patterns, templates)."

**Analytics Dimension:**
*   **Key:** `quarter`
*   **Description:** "Group by Quarter (test end date)"
*   **SQL:** `strftime('%Y-Q', end_at) || ((strftime('%m', end_at) + 2) / 3)` (SQLite approximation)

*   **Key:** `rejection_reason`
*   **Description:** "Group by Rejection Reason"
*   **SQL:** `Bug.rejection_reason` (New column)

### Workflows and Sequencing

**Scenario A: Tactical Detective**
1.  **User:** "Why was cycle 123 so noisy?"
2.  **AI:** Reads `testio://knowledge/playbook` -> Finds "Noisy Cycle" pattern.
3.  **AI:** Calls `get_test_summary(123)` -> Gets instructions and bug counts.
4.  **AI:** Calls `get_test_bugs(123)` -> Checks rejection reasons.
5.  **AI:** Matches data to pattern -> "Instructions were 15 words. 40% rejections. Matches 'Noisy Cycle' pattern."

**Scenario B: Strategic Analyst**
1.  **User:** "Prepare Q3 EBR for Product X."
2.  **AI:** Reads `testio://knowledge/playbook` -> Finds "Quarterly Quality Review" template.
3.  **AI:** Calls `query_metrics(dimensions=['quarter'], ...)` -> Gets aggregated data.
4.  **AI:** Synthesizes narrative -> "Quality improved in Q3..."

## Non-Functional Requirements

### Performance
*   **Resource Access:** Reading the Playbook resource should be near-instantaneous (<50ms).
*   **Analytics:** Quarterly aggregation queries should complete within standard timeouts (<5s).

### Security
*   **Access Control:** Resource access is subject to the same authentication as tools.
*   **Content Safety:** Playbook content is static and trusted.

### Reliability/Availability
*   **Availability:** The Playbook resource must be available whenever the server is running.

### Observability
*   **Logging:** Resource access should be logged (debug level).

## Dependencies and Integrations

*   **FastMCP:** Requires FastMCP support for `@mcp.resource` (already available).
*   **SQLite:** Requires SQLite date functions for quarter calculation.

### Migration Strategy (STORY-067)
*   **Schema Change:** Add `rejection_reason` column (TEXT, NULLABLE) to `bugs` table via Alembic migration.
*   **Backfill Strategy:**
    1.  Migration script adds the column.
    2.  Post-migration step (or separate script) iterates through *all* existing bugs in the DB.
    3.  Applies the `transform_api_bug_to_orm` logic to parse `raw_data` comments.
    4.  Updates the `rejection_reason` column.
    5.  **Performance:** Batch updates to avoid locking the DB for too long.

### Playbook Content Specification (Initial Version)
*   **Tactical Pattern: "The Noisy Cycle"**
    *   **Signals:**
        *   Rejection Rate > 30% (calculated as `rejected_bugs / total_bugs`).
        *   Rejection Reason = `ignored_instructions` OR `intended_behavior`.
        *   Instruction Length < 50 words.
    *   **Diagnosis:** "Vague instructions led to tester confusion."
    *   **Action:** "Coach customer on Scope Definition."
*   **Strategic Template: "Quarterly Quality Review"**
    *   **Metrics:** `bug_count`, `acceptance_rate`, `severity_breakdown`.
    *   **Grouping:** `quarter`.
    *   **Narrative:** "Focus on trends (improving vs declining) over the last 4 quarters."

### Unmatched Handling
*   If the parser cannot match a comment to a known `REJECTION_REASON`, the `rejection_reason` column remains `NULL`.
*   **Logging:** Log a warning (DEBUG level) with the bug ID and comment body for future analysis (potential new pattern discovery).

## Acceptance Criteria (Authoritative)

1.  **Playbook Resource:**
    *   `testio://knowledge/playbook` is discoverable via `list_resources`.
    *   Reading the resource returns the full markdown content matching the "Content Specification".
2.  **Instruction Text:**
    *   `get_test_summary` returns the complete `instructions` text for a test, even if long (>500 words).
3.  **Quarterly Analytics:**
    *   `query_metrics` accepts `dimensions=['quarter']`.
    *   Results are correctly grouped by year and quarter (e.g., "2024-Q3").
    *   **Performance:** Query completes in < 2 seconds for < 10k rows.
4.  **Rejection Reason Analytics:**
    *   `query_metrics` accepts `dimensions=['rejection_reason']`.
    *   Results include the parsed reasons (e.g., `ignored_instructions`).
    *   **Backfill:** Existing rejected bugs (verified 2,124) are correctly backfilled.
5.  **Tactical Detective Validation:**
    *   AI can successfully identify a "bad test cycle" by correlating tool data with Playbook patterns.
6.  **Strategic Analyst Validation:**
    *   AI can successfully generate a quarterly trend report using `query_metrics` and Playbook templates.

## Traceability Mapping

| Acceptance Criteria | Spec Section | Component/API | Test Idea |
| :--- | :--- | :--- | :--- |
| AC1: Playbook Resource | APIs and Interfaces | `resources.py` | Integration test: `read_resource("testio://knowledge/playbook")` |
| AC2: Instruction Text | Detailed Design | `test_summary_tool.py` | Unit test: Mock test with long instructions, verify output |
| AC3: Quarterly Analytics | Detailed Design | `AnalyticsService` | Unit test: Query with `quarter` dimension, verify SQL and results |
| AC4: Rejection Analytics | Detailed Design | `AnalyticsService` | Unit test: Query with `rejection_reason`, verify grouping |
| AC5: Detective Validation | Workflows | End-to-End | Manual scenario walk-through |
| AC6: Analyst Validation | Workflows | End-to-End | Manual scenario walk-through |

## Risks, Assumptions, Open Questions

*   **Risk:** AI might hallucinate connections if Playbook patterns are too generic.
    *   *Mitigation:* Enforce specific thresholds (e.g., >30%) in Playbook content.
*   **Assumption:** SQLite `strftime` is sufficient for quarter calculation.
*   **Question:** Should we expose other resources (e.g., "Bug Types Definition")?
    *   *Decision:* Start with Playbook only for this epic.
*   **Risk:** Backfill might take time on large databases.
    *   *Mitigation:* Use batched updates.

## Test Strategy Summary

*   **Unit Tests:**
    *   Verify `AnalyticsService` generates correct SQL for "quarter" dimension.
    *   Verify `get_test_summary` handles large text fields correctly.
    *   **Transformer Tests:** Verify `transform_api_bug_to_orm` correctly parses all known rejection patterns (including `request_timeout`) and handles unmatched cases (returns NULL).
*   **Integration Tests:**
    *   Verify `testio://knowledge/playbook` is registered and readable.
    *   **Migration Test:** Verify schema upgrade and backfill logic works on a sample database.
*   **Manual Validation:**
    *   Execute the "Tactical Detective" and "Strategic Analyst" demo scripts to ensure the AI "gets it".
