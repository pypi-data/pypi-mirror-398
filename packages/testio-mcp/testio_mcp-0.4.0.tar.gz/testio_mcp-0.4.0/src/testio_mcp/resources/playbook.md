# TestIO CSM Playbook

---

## 1. Customer Lifecycle Context (Ground Truth)

Understanding the TestIO lifecycle is critical for accurate diagnosis.

1.  **Features (The Map):** High-level product areas.
    *   *If vague:* Testers get lost -> "Intended Behavior" bugs.
2.  **Test Cycles (The Mission):** Instructions + Features + Devices.
    *   *If instructions contradict features:* "Intended Behavior" bugs.
    *   *If devices/environment wrong:* "Not Reproducible" bugs.
3.  **Bugs (The Findings):** Output of the test.
4.  **Review (The Feedback Loop):** After test is completed, customer accepts/rejects bugs.
    *   *Note:* "Known" is a status tag, not a third review outcome.
    *   *Low engagement:* High Auto-Acceptance.
5.  **Verify (Optional):** After Test is completed, during bug review, request Bug Fix Confirmation.
    *   *Missing step:* Bugs fixed but never verified.

---

## 2. Bug Review Decision Logic

Use this logic to recommend the *correct* remediation for rejected bugs.

**Q1: Is this actionable (will the customer fix it)?**
*   **YES** -> **Accept** (AND **Mark as Known** if deferred/wont-fix).
*   **NO** -> Go to Q2.

**Q2: Is it Intended Behavior?**
*   **Unlikely to recur?** -> **Reject as "Intended Behavior"**.
*   **Likely to recur?**
    *   **Global** (Always true) -> **Update Feature Description**.
    *   **Specific** (Test/Env specific) -> **Update Test Instructions**.

**Q3: Is it Not Reproducible?**
*   **Active Cycle** -> **Request Information** immediately (ask for video/steps).
*   **Retrospective** -> **Reject**, but suggest monitoring environment stability.

**Q4: Is it a Duplicate?**
*   **YES** -> **Reject as Duplicate**.

**Q5: Is it a Known Bug?**
*   **Already in Known List** -> **Reject as "Known Bug"**.
*   **New but won't fix** -> **Mark as Known** (Add to list to prevent future reports).

---

## 3. Tactical Patterns (Escalation Investigation)

### Pattern: Noisy Cycle
**Signals:** Rejection Rate > 30%, high "Intended Behavior" or "Ignored Instructions".
**Hypothesis:** The "Map" (Features) or "Mission" (Instructions) is unclear.
**Action:**
*   **Global Issue:** Update Feature Descriptions.
*   **Test-Specific:** Update Test Instructions (e.g., "Ignore login button on Staging").
*   **Tester Issue:** If instructions were clear but ignored, **Inform CSM** to coach tester.

### Pattern: "Not Reproducible" Spike
**Signals:** High "Not Reproducible" rejection rate.
**Hypothesis:** Environment mismatch, flaky test, or poor reporting.
**Action:**
*   **Immediate:** Use **Request Information** to get video/logs before rejecting.
*   **Strategic:** Suggest customer **audit and review** test environments (acknowledged external dependency).

### Pattern: Volume & Bandwidth Management
**Signals:** Auto-Acceptance > {auto_acceptance_critical_pct}% or Review Rate < {review_critical_pct}%.
**Hypothesis:** Bug volume exceeds team's triage bandwidth (10-day window).
**Action:**
*   **Restrict Scope:** Switch to **Rapid Tests** (Critical only) or **Focused Tests** (limit features).
*   **Custom Config:** CSM can enable **Fully Custom Tests** (mix & match features/severities/durations) on backend.
*   **Reduce Cadence:** Space out test cycles to allow triage time.

### Pattern: Known Bug Management
**Signals:** High "Known Bug" rejections or recurring "Wont Fix" issues.
**Hypothesis:** Testers are finding valid bugs that you don't intend to fix.
**Action:**
*   **Valid but Wont Fix:** **Mark as Known**. (Tell testers: "We know, stop reporting.")
*   **Intended/Irrelevant:** Do **NOT** use Known Bug List. **Update Feature and/or Test Cycle instructions** instead.

---

## 4. Strategic Templates (EBR/QBR)

### Template: Quarterly Quality Review
**Purpose:** Executive summary of quality trends.
**Queries:**
1.  **Volume:** `query_metrics(dimensions=["quarter"], metrics=["test_count", "bug_count"], start_date="1 year ago")`
2.  **Quality:** `query_metrics(dimensions=["quarter"], metrics=["rejection_rate", "review_rate"], start_date="1 year ago")`
3.  **Rejection:** `query_metrics(dimensions=["quarter", "rejection_reason"], metrics=["bug_count"], start_date="1 year ago")`
4.  **Severity:** `query_metrics(dimensions=["quarter", "severity"], metrics=["bug_count"], start_date="1 year ago")`

### Template: Feature Coverage Analysis
**Purpose:** Identify untested or fragile areas.
**Query:**
`query_metrics(dimensions=["feature"], metrics=["test_count", "bugs_per_test"], start_date="90 days ago", limit=10)`
**Narrative:** "Feature X has high bug density but low test count - opportunity for regression testing."

---

## 5. Quick Reference: Key Thresholds

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| auto_acceptance_rate | <{auto_acceptance_warning_pct}% | {auto_acceptance_warning_pct}-{auto_acceptance_critical_pct}% | >{auto_acceptance_critical_pct}% |
| rejection_rate | <{rejection_warning_pct}% | {rejection_warning_pct}-{rejection_critical_pct}% | >{rejection_critical_pct}% |
| review_rate | >{review_warning_pct}% | {review_critical_pct}-{review_warning_pct}% | <{review_critical_pct}% |

**Note on Auto-Acceptance:** High rates (>{auto_acceptance_critical_pct}%) signal disengagement. Action: Investigate bandwidth (see Volume Management pattern) and any team friction or usability issues.
