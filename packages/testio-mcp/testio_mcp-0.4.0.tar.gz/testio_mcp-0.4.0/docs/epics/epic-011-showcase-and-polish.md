# Epic 011: Showcase & Polish

**Status:** Planned
**Epic Lead:** Ricardo_Leon1
**Start Date:** 2025-11-29

---

## Executive Summary

**Goal:** Shift from feature building to "Context-Aware" demonstration. We will implement and polish the system to support two specific, high-value scenarios that showcase the AI's ability to synthesize TestIO data with expert domain knowledge.

**Core Value Proposition:**
The TestIO MCP Server isn't just a database reader; it is an **intelligent partner** that applies "Expert Knowledge" (CSM Playbook) to raw data to solve complex business problems.

---

## Scope

### 1. The "Expert Knowledge" Resource
We will expose a new MCP resource: `testio://knowledge/playbook`.
*   **Content:** A structured markdown file containing "Expert Heuristics" for CSMs.
*   **Tactical Section:** Signals of "bad test setup" (e.g., short instructions, high rejection rates, low participation).
*   **Strategic Section:** Templates for Executive Business Reviews (EBRs), defining which metrics matter for ROI (e.g., acceptance rate trends, severity breakdown).

### 2. Scenario A: The "Tactical Detective" (Operational)
**User:** CSM (Reactive)
**Trigger:** A customer complains about a "noisy" or "low value" test cycle.
**Workflow:**
1.  User provides the complaint: "Cycle 123 was noisy."
2.  AI consults the **Playbook** to know what "noisy" implies (e.g., vague instructions).
3.  AI retrieves **Test Details** (specifically instructions) and **Bug Rejection Reasons**.
4.  AI correlates the data: "The instructions were only 10 words long, and 40% of bugs were rejected as 'Out of Scope'. This matches the 'Vague Instructions' pattern in the Playbook."
5.  **Outcome:** Evidence-based coaching for the customer.

### 3. Scenario B: The "Strategic Analyst" (EBR/QBR)
**User:** CSM (Proactive)
**Trigger:** Preparing for a Quarterly Business Review (QBR/EBR).
**Workflow:**
1.  User asks: "Prepare an EBR summary for Product X for Q3."
2.  AI consults the **Playbook** to know the "EBR Template" (Trend Analysis, Severity Breakdown, ROI).
3.  AI uses `query_metrics` to aggregate data over the quarter (group by month/week).
4.  AI synthesizes the trends: "Quality has improved; Critical bugs dropped by 20% since Q2, while test coverage increased."
5.  **Outcome:** Strategic, executive-ready narrative.

---

## Implementation Plan (Stories)

### STORY-066: Knowledge Resource (The Playbook)
*   **Goal:** Create and expose the `testio://knowledge/playbook` resource.
*   **Tasks:**
    *   Draft `docs/resources/playbook.md` with Tactical and Strategic sections.
    *   Implement `resources.py` to serve this file via MCP.
    *   Ensure prompt context encourages the AI to "consult the playbook".

### STORY-067: Tactical Detective Capability
*   **Goal:** Polish tools to support the "Detective" workflow.
*   **Tasks:**
    *   **Tool Verification:** Verify `get_test_summary` returns *full* instruction text without truncation.
    *   **Tool Polish (Rejection Reasons):**
        *   **Problem:** The API does not provide a structured `rejection_reason` field. It is only found in the comments.
        *   **Solution:** Implement a "Rejection Reason Parser" in `TestService` using the **Transformer Pattern**.
        *   **Mechanism:**
            *   Define a constant `REJECTION_REASONS` containing the known static strings from the API.
            *   **Verified Patterns:** We have verified 100% coverage against the local database (2,124 rejected bugs) using the following keys:
                *   `device_not_relevant`
                *   `ignored_instructions`
                *   `intended_behavior`
                *   `irrelevant`
                *   `known_bug`
                *   `not_reproducible`
                *   `request_timeout` (Matches: "Your bug was rejected automatically, because you didn't respond to the request within 24 hours")
            *   **Implementation:** The Transformer will parse comments during ingestion and denormalize the key into a new `rejection_reason` column in the `bugs` table.
    *   **Validation:** Verify the AI can connect "Vague Instructions" (from tool) to "Playbook Pattern" (from resource).

### STORY-068: Strategic Analyst Capability
*   **Goal:** Polish tools to support the "Analyst" workflow.
*   **Tasks:**
    *   **Analytics Polish:**
        *   Add `quarter` dimension to `query_metrics` (e.g., "2024-Q3").
        *   Add `rejection_reason` dimension to `query_metrics` (enabled by STORY-067 data).
    *   **Validation:** Verify the AI can generate a "Quarterly Quality Review" using the Playbook template and the new dimensions.
    *   **Tool Polish:** Verify `query_metrics` handles long-range trend analysis (e.g., last 4 quarters) efficiently.
    *   **Validation:** Verify the AI can generate a coherent narrative from the aggregated metrics.

---

## Success Criteria
1.  **Playbook Accessible:** The AI can read and quote from `testio://knowledge/playbook`.
2.  **Detective Solved:** The AI successfully diagnoses a "bad test cycle" using the Playbook's heuristics.
3.  **EBR Generated:** The AI generates a data-backed QBR summary that focuses on trends and ROI, not just raw counts.
