# Meeting Preparation Workflow

**Analysis directory**: `{analysis_dir}`

**User-provided context**: {context}

---

## Phase 0: Load Knowledge Base

**REQUIRED FIRST STEP**: Load the playbook resource to understand available metrics and patterns.

```
Resource: testio://knowledge/playbook
```

This defines the data schema boundaries:
- Available dimensions (feature, platform, severity, tester, month, etc.)
- Available metrics (bug_count, test_count, acceptance rates, rejection_rate, etc.)
- Known patterns (Noisy Cycle, Silent Period, Platform Bias, etc.)

**Stay within this schema** - do not invent metrics that don't exist in the playbook.

---

## Phase 0.5: Verify Analysis Exists

Check that `{analysis_dir}` contains analysis artifacts:
- If empty or missing: Suggest running `/analyze-product-quality` first
- If exists: Proceed to Phase 1

> "I see analysis artifacts in `{analysis_dir}`. Let me understand the narrative you want to build."

---

## Phase 1: Understand the Narrative

**STOP** and ask the user rich context questions to understand the business situation:

### Meeting Logistics
1. **What type of meeting is this?**
   - EBR (Executive Business Review)?
   - QBR (Quarterly Business Review)?
   - Renewal discussion?
   - Escalation response?
   - Routine sync?
   - Other?

2. **How long is the meeting?**
   - Duration in minutes (e.g., 30, 45, 60)

### Meeting Context

3. **What's driving this meeting?**
   - Renewal coming up?
   - Recent escalation or concern?
   - New stakeholder introduction?
   - Routine check-in?
   - Customer requested it?

   {context_hint}

4. **Who's in the room?**
   - New stakeholder who needs onboarding?
   - Existing operational partners who know TestIO well?
   - Executive level (VP/Director) or practitioner level (QA lead)?
   - Decision makers or influencers?

5. **What does success look like?**
   - What outcome would make this meeting successful for you?
   - What decision or action do you hope comes from this?

6. **What concerns or opportunities are on the table?**
   - Any friction points to address?
   - Scope expansion opportunities?
   - Process improvements to suggest?
   - Topics to avoid?

### Propose Narrative Hypothesis

Based on the user's answers, **propose a narrative hypothesis**:

> "Based on what you've told me, it sounds like this is a **[narrative type]** meeting.
>
> Possible narratives:
> - **Value proof before renewal** - Show impact, justify continued investment
> - **Escalation response** - Address concerns, show corrective action
> - **Scope expansion** - Identify coverage gaps, propose new testing areas
> - **Executive introduction** - High-level value story, strategic positioning
> - **Routine check-in** - Health metrics, collaborative roadmap planning
>
> Which narrative resonates with you? Or would you describe it differently?"

**Wait for user confirmation or refinement** before proceeding.

---

## Phase 2: Identify Supporting Evidence

Now that we have the narrative, determine what evidence would support it.

### Ask the user:

1. **What story are we trying to tell?**
   - Example: "We're finding critical bugs that matter"
   - Example: "Quality has improved over time"
   - Example: "We're underutilizing certain features"

2. **Which metrics would make that case?**
   - Refer to playbook for available metrics
   - Example: "To show value, we'd want bug_count, severity breakdown, active_acceptance_rate"
   - Example: "To show improvement, we'd want rejection_rate trend over time"

3. **What questions will metrics help us explore WITH the customer?**
   - Metrics should elicit conversation, not just inform us
   - Example: "Does the platform breakdown align with your release schedule?"
   - Example: "What's your sense of why rejection rate spiked in March?"

### Output: Evidence Requirements List

Create a checklist of metrics needed:
- [ ] Metric 1 (dimension: X, reason: supports narrative point Y)
- [ ] Metric 2 (dimension: Z, reason: explores question Q)
- [ ] Metric 3 (comparison: time period A vs B, reason: shows trend)

---

## Phase 3: Gather Evidence from Analysis

Read the analysis artifacts in `{analysis_dir}` with your evidence requirements in mind:

1. **Explore the analysis directory**:
   - List all files in `{analysis_dir}`
   - Read markdown files to understand what analysis was performed
   - Note any data files (JSON, CSV) available for the fetch script

2. **Extract what's relevant to your narrative**:
   - Product ID(s) and product name(s)
   - Date range analyzed
   - Metrics that match your evidence requirements
   - Findings that support or contradict your narrative
   - Gaps: what's missing that you'd need?

3. **Adapt to what exists**:
   - Single product analysis → standard meeting prep
   - Portfolio analysis → executive portfolio review prep
   - Custom artifacts → incorporate into conversation guide

4. **Map evidence to narrative**:
   ```
   Narrative point: "We find critical bugs"
   Supporting evidence: 23 critical bugs found, 87% accepted
   Gap: No trend data - is this improving?
   ```

If analysis artifacts don't exist or are incomplete, note the gaps.

---

## Phase 3.5: HITL Validation & Investigation

**STOP** and show the user your evidence mapping:

### Present Findings

> "Here's what I found to support the **[narrative]**:
>
> **Supporting Evidence**:
> - [Metric/finding 1] → supports [narrative point]
> - [Metric/finding 2] → explores [question]
>
> **Gaps Identified**:
> - Missing: [metric] - would help show [point]
> - Unclear: [finding] - contradicts narrative, need to investigate
>
> **Proposed Investigation**:
> I can fetch additional metrics using MCP tools:
> - query_metrics with [dimensions] to see [breakdown]
> - get_product_quality_report with [date range] for comparison
> - search for [feature/bug pattern] mentioned in narrative
>
> Should I investigate these gaps, or is the current evidence sufficient?"

### Investigation Loop

If user approves investigation:
1. Use MCP tools to fetch additional metrics (stay within playbook schema)
2. Present refined evidence set
3. Ask: "Does this tell the story you want?"

**User can**:
- ✅ Approve and proceed to Phase 4
- 🔄 Request different metrics (loop back to Phase 2)
- ✏️ Refine narrative (loop back to Phase 1)
- 🔍 Request more investigation (stay in Phase 3.5)

**Do not proceed to Phase 4 until user explicitly approves the evidence set.**

---

## Phase 4: Generate Artifacts

Write the following files to `{analysis_dir}/`:

### 4.1 fetch_metrics.py

**Before writing this script, load resource: `testio://knowledge/programmatic-access`**

Write a Python script that:
1. Uses REST API (HTTP mode) to fetch the APPROVED metrics from Phase 3.5
2. Only includes metrics that support the validated narrative
3. Fetches:
   - Product quality report for date range
   - Custom analytics queries (query_metrics) for validated dimensions
4. Saves to `data/` subdirectory (relative to script location using `Path(__file__).parent`):
   - JSON format (raw data)
   - CSV format (for spreadsheet import)
5. Prints markdown tables for copy/paste

**Important**:
- Use `http://localhost:8080/openapi.json` to discover exact endpoint schemas
- Only fetch metrics user validated in Phase 3.5
- Include comments explaining what each metric supports in the narrative

**After writing the script, run it to verify it works:**

```bash
uv run python {analysis_dir}/fetch_metrics.py
```

If the script fails, debug and fix before proceeding. Common issues:
- Analytics queries require at least 1 dimension (use quality-report for totals)
- Field names in response may differ from assumptions (always inspect schema first)

### 4.2 slide-data.md

Create a markdown file with tables/charts optimized for the narrative:

```markdown
# [Product Name] — [Meeting Type] Data
**Period**: [date range from analysis]
**Generated**: [today's date]
**Narrative**: [one-sentence narrative from Phase 1]

## Key Metrics (Narrative-Driven)

[Only include metrics that support the narrative]

### [Narrative Point 1]

| Metric | Value | Interpretation |
|--------|-------|----------------|
| ...    | ...   | Why this matters for our story |

### [Narrative Point 2]

[Visualization suggestion]:
- Chart type: [bar/line/combo based on narrative]
- X-axis: [dimension]
- Y-axis: [metric]
- Why: [how this visual supports narrative]

## Back-Pocket Details

[Additional context from analysis - only if customer drills down]
```

### 4.3 conversation-guide.md

Create a facilitator script structured around the narrative:

```markdown
# [Product Name] — [Meeting Type] Conversation Guide
**Duration**: [meeting duration] minutes
**Date**: [meeting date]
**Narrative**: [validated narrative from Phase 1]

## Meeting Context
[User's answers from Phase 1]

---

## Opening (2-3 min)

**For new stakeholders**:
- Brief intro: "Exploratory testing complements your test-case work by finding edge cases and real-world issues"
- Set context based on relationship history (if known)

**For existing partners**:
- Acknowledge relationship history
- Quick recap if needed: "We've been working together on [product] testing"

**Value hook** (from validated evidence):
- "[Key metric] in [period]"
- "[Insight that sets up narrative]"

---

## Value Overview (5 min)

Show 1-2 slides with narrative-supporting metrics. **Pause for reaction**.

Talking points (use conversationally, don't read):
- [Metric 1 from validated evidence] → [what this means]
- [Metric 2 from validated evidence] → [why this matters]
- [Narrative point from Phase 1]

**Ask**: "[Question from Phase 2 evidence requirements]"

Example: "Does this breakdown align with what your team has been seeing?"

---

## Discussion ([meeting duration] - 10 min)

### Understanding Their Context
- "What's on your roadmap for [next period]?"
- "Any upcoming releases we should be aware of?"
- "How has the bug feedback been useful to your team?"

### Exploring with Metrics (from Phase 2)
[Questions designed in Phase 2 that metrics help explore]

Example:
- [If platform breakdown relevant]: "We noticed [pattern] - does that match your release schedule?"
- [If rejection rate part of narrative]: "What's your sense of what's driving [observation]?"

### Seeds to Plant
[Based on user's Phase 1 context - introduce naturally]

Example opportunities:
- Expand testing to undertested features
- Improve process (share Known Bug List, tighter SLAs)
- Platform coverage expansion

---

## Wrap-up (2 min)

- "Based on what we discussed, what would be most valuable to focus on in [next period]?"
- "Any questions about the data or our process?"

---

## Back-Pocket (Only if Asked)

[Detailed findings from analysis - use only if customer drills down]

**Prepared for**:
- [Topic 1]: [Brief answer with supporting data]
- [Topic 2]: [Brief answer with supporting data]
```

---

## Design Principles

Remember throughout all phases:

1. **Narrative first, metrics second** - Story drives evidence, not vice versa
2. **Customer talks > We talk** - Questions elicit conversation, metrics support it
3. **Schema-grounded** - Stay within playbook boundaries, no invented metrics
4. **HITL validation** - User must approve evidence before generating artifacts
5. **Reproducible** - Scripts can be re-run for fresh data before meeting

---

## Troubleshooting

**If analysis directory is empty**:
- Ask user to run `/analyze-product-quality` first
- Or offer to help gather initial data using MCP tools

**If narrative unclear**:
- Revisit Phase 1 questions
- Ask user to describe the meeting outcome they want in one sentence

**If evidence doesn't support narrative**:
- Be honest: "The data doesn't strongly support [narrative]. Should we refine the story or investigate further?"
- Don't force a narrative that metrics contradict
