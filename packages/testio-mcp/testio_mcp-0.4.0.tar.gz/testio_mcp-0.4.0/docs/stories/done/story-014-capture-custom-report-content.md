---
story_id: STORY-014
epic_id: EPIC-001
title: Capture Generic Custom Report Content
status: Ready for Review
created: 2025-11-06
updated: 2025-11-06
estimate: 3-4 hours
assignee: Dev (James)
priority: high
dependencies: [STORY-005b, STORY-013]
---

# STORY-014: Capture Generic Custom Report Content

## Problem Statement

**Current Issue:**
While STORY-005b added support for classifying custom bugs (accessibility reports, purchase reports, etc.), we're only capturing ~20% of the meaningful content. The TestIO API stores rich structured data in `report.content` that contains the actual findings, but our `BugDetails` model doesn't include this field.

**Evidence from Production:**
Custom bug 3359 (accessibility report) from test 1210:

**What we currently capture:**
```json
{
  "id": "3359",
  "title": "[A][1.2.2][1.4.3][1.4.11] Feature 1: Contrast of icons...",
  "bug_type": "custom",
  "steps": [],           // Empty (null normalized by STORY-013)
  "devices": [],         // Empty (null normalized by STORY-013)
  "attachments": [...]   // Screenshots captured ✓
}
```

**What's available but NOT captured:**
```json
{
  "report": {
    "title": "[A][1.2.2][1.4.3][1.4.11] Feature 1: Contrast...",
    "content": {
      "data": [
        {
          "key": "wcag_checkpoints",
          "name": "WCAG Checkpoints",
          "type": "text",
          "value": "1.2.2, 1.4.3, 1.4.11, 1.4.6",
          "position": 1
        },
        {
          "key": "issue_type",
          "name": "Issue Type",
          "type": "text",
          "value": "Violation",
          "position": 2
        },
        {
          "key": "severity",
          "name": "Severity",
          "type": "text",
          "value": "Major",
          "position": 4
        },
        {
          "key": "steps_to_reproduce",
          "name": "Steps to Reproduce",
          "type": "text",
          "value": "1. First step\n2. Second step",
          "position": 5
        },
        {
          "key": "recommendations",
          "name": "Recommendations",
          "type": "text",
          "value": "Fix suggestions",
          "position": 10
        },
        {
          "key": "html_code_snippet",
          "name": "HTML Code",
          "type": "text",
          "value": "<div>...</div>",
          "position": 13
        }
        // ... 16 total fields for accessibility reports
      ]
    }
  }
}
```

**Impact:**
1. **Data loss** - 80% of custom report content is invisible to users
2. **Limited usefulness** - Custom bugs reduced to just title + attachments
3. **Poor UX** - Users must go to TestIO UI to see actual findings
4. **Missed use cases** - Can't query/filter by WCAG criteria, severity labels, code snippets, etc.

**Affected Use Cases:**
- ✗ Accessibility testing - WCAG checkpoints, screen readers, code snippets missing
- ✗ Purchase testing - Confirmation numbers, payment details missing
- ✗ Performance testing - Metrics, benchmarks missing
- ✗ Any future custom report type

## User Story

**As a** QA Manager using custom reports (accessibility, purchase, performance testing)
**I want** to see the full structured report content in bug responses
**So that** I can analyze findings without switching to the TestIO UI

## Current Behavior

**BugDetails Model** (src/testio_mcp/models/schemas.py):
```python
class BugDetails(BaseModel):
    id: str
    title: str
    bug_type: str  # functional|visual|content|custom
    steps: list[str]  # Empty for custom bugs (null → [])
    devices: list[BugDevice]  # Empty for custom bugs
    attachments: list[BugAttachment]  # Only field with data for custom bugs
    # ... other fields

    # NO report_content field!
```

**Result:**
- Accessibility reports: Missing WCAG criteria, recommendations, code snippets
- Purchase reports: Missing confirmation numbers, payment details
- Performance reports: Missing metrics, benchmarks
- Any custom report: Missing 80% of structured content

## Expected Behavior

**Enhanced BugDetails Model:**
```python
class BugDetails(BaseModel):
    # ... existing fields ...

    report_content: dict[str, Any] | None = Field(
        default=None,
        description="Custom report structured content (varies by report type)"
    )
```

**Example Output (get_test_bugs with accessibility report):**
```json
{
  "bugs": [
    {
      "id": "3359",
      "title": "[A][1.2.2][1.4.3][1.4.11] Feature 1: Contrast...",
      "bug_type": "custom",
      "status": "forwarded",
      "attachments": [...],
      "report_content": {
        "data": [
          {
            "key": "wcag_checkpoints",
            "name": "WCAG Checkpoints",
            "type": "text",
            "value": "1.2.2, 1.4.3, 1.4.11",
            "position": 1
          },
          {
            "key": "steps_to_reproduce",
            "name": "Steps to Reproduce",
            "type": "text",
            "value": "1. Navigate to icons\n2. Check contrast",
            "position": 5
          },
          {
            "key": "recommendations",
            "name": "Recommendations",
            "type": "text",
            "value": "Increase icon contrast to meet WCAG 1.4.3",
            "position": 10
          }
          // ... all custom fields included
        ]
      }
    }
  ]
}
```

**AI Assistant Access Pattern:**
```python
# Users can query specific fields
for field in bug["report_content"]["data"]:
    if field["key"] == "wcag_checkpoints":
        print(f"WCAG: {field['value']}")
    if field["key"] == "recommendations":
        print(f"Fix: {field['value']}")
```

## Design Decisions

### 1. Generic vs. Type-Specific Approach → **DECISION: Generic `report_content` field**

**Option A: Generic dict field (CHOSEN)**
```python
report_content: dict[str, Any] | None
```
✅ Works for any custom report type (accessibility, purchase, performance, etc.)
✅ Future-proof - new report types work automatically
✅ No assumptions about field structure
✅ Zero maintenance as custom reports evolve

**Option B: Dedicated accessibility model**
```python
class AccessibilityBugDetails(BugDetails):
    wcag_checkpoints: list[str]
    recommendations: str
    # ... hardcoded accessibility fields
```
❌ Only works for accessibility reports
❌ Requires new models for each report type
❌ High maintenance burden
❌ Doesn't scale

**Rationale:** Custom reports are designed to be heterogeneous. TestIO supports 6+ configuration types (accessibility WCAG 2.1, WCAG 2.2, purchase reports, etc.) with different field structures. A generic approach is the only sustainable solution.

### 2. Field Scope → **DECISION: Extract for all bug types if present**
- Custom bugs: Definitely have report.content
- Visual/content bugs: May have report.content (extract if present)
- Functional bugs: Unlikely but extract if present
- Implementation: Generic extraction regardless of bug_type

### 3. Backward Compatibility → **DECISION: Optional field**
```python
report_content: dict[str, Any] | None = Field(default=None)
```
- Existing responses unchanged (field omitted if None)
- No breaking changes
- Graceful degradation for bugs without report.content

## Acceptance Criteria

### AC1: Model Schema Extension
**Given** the BugDetails Pydantic model
**When** a new field is added
**Then** it should include `report_content: dict[str, Any] | None` with default=None

**Verification:**
- [x] Field added to BugDetails in `models/schemas.py`
- [x] Field has appropriate docstring
- [x] mypy --strict passes

---

### AC2: Service Layer Update
**Given** a bug response from the API with report.content
**When** `_build_bug_details()` is called
**Then** the report.content should be extracted and assigned to report_content field

**Verification:**
- [x] `BugService._build_bug_details()` updated
- [x] Logic: `report_content = bug.get("report", {}).get("content")`
- [x] Works for all bug types (not just custom)
- [x] No exceptions if report.content missing

---

### AC3: Data Structure Preservation
**Given** a custom bug with report.content.data array
**When** the bug is transformed to BugDetails
**Then** the entire data[] array structure should be preserved

**Verification:**
- [x] All elements in data[] array preserved
- [x] Each element includes: key, name, type, value, position
- [x] Field order maintained (position values)
- [x] No data truncation or transformation
- [x] Unicode characters handled correctly

---

### AC4: Unit Tests
**Given** the updated service and model
**When** unit tests are run
**Then** they should verify report_content extraction

**Test Cases:**
- [x] Bug with report.content → report_content populated
- [x] Bug without report.content → report_content = None
- [x] Bug with empty report.content.data → report_content = {"data": []}
- [x] All tests pass with mypy --strict

---

### AC5: Integration Tests
**Given** real API data from test 1210
**When** `get_test_bugs(test_id="1210", bug_type="custom")` is called
**Then** custom bugs should include populated report_content

**Verification:**
- [x] Bug 3359 includes report_content
- [x] report_content["data"] has 15 elements (verified via MCP)
- [x] Key fields present: wcag_checkpoints, steps_to_reproduce, recommendations
- [x] Test passes with real staging API token

---

### AC6: Compatibility with STORY-013
**Given** custom bugs with null steps/devices/attachments
**When** both STORY-013 validator and STORY-014 extraction run
**Then** both should work without conflicts

**Verification:**
- [x] Custom bugs still normalize null fields to []
- [x] report_content extraction happens independently
- [x] Bug 3359 has both: steps=[] AND report_content with steps_to_reproduce
- [x] No Pydantic validation errors

---

### AC7: Documentation
**Given** the new report_content field
**When** developers review the code
**Then** usage patterns should be clear

**Verification:**
- [x] BugDetails field docstring includes description and example
- [x] `_build_bug_details()` docstring mentions report extraction
- [x] Code comments explain extraction logic

---

## Tasks

### Phase 1: Model Extension
- [x] Add `report_content: dict[str, Any] | None` field to BugDetails (schemas.py:~120)
- [x] Ensure `Any` is imported from typing
- [x] Add field docstring with usage example
- [x] Run mypy: `mypy --strict src/testio_mcp/models/schemas.py`

### Phase 2: Service Layer Update
- [x] Update `_build_bug_details()` in bug_service.py (~396)
- [x] Add extraction logic before return statement:
  ```python
  # Extract custom report content if present
  report_content = None
  if bug.get("report") and bug["report"].get("content"):
      report_content = bug["report"]["content"]
  ```
- [x] Add `report_content=report_content` to BugDetails constructor
- [x] Update method docstring
- [x] Run mypy: `mypy --strict src/testio_mcp/services/bug_service.py`

### Phase 3: Unit Tests
- [x] Create `test_build_bug_details_with_report_content()` in test_bug_service.py
- [x] Create `test_build_bug_details_without_report_content()`
- [x] Create `test_build_bug_details_empty_report_content()`
- [x] Run: `pytest tests/unit/test_bug_service.py -k report_content -v`
- [x] Verify all tests pass (3 new tests, all passing)

### Phase 4: Integration Tests
- [x] Add test in test_get_test_bugs_integration.py
- [x] Test with test 1210 custom bugs
- [x] Verify report_content structure
- [x] Run: `pytest tests/integration/ -k report_content -v`

### Phase 5: Validation
- [x] Run full test suite: `pytest -v` (291 passed, 14 skipped)
- [x] Run type checker: `mypy --strict src/testio_mcp` (Success: 28 files)
- [x] Run linter: `ruff check src/ tests/` (All checks passed)
- [x] Verify backward compatibility (existing tests pass)

### Phase 6: Manual Testing
- [x] Test with MCP inspector: `get_test_bugs(test_id="1210", bug_type="custom")`
- [x] Verify response includes report_content
- [x] Check data[] array has expected fields (15 fields verified)
- [x] Verify JSON structure is valid

---

## Implementation Notes

### API Response Structure

**Raw API response for custom bug 3359:**
```json
{
  "id": 3359,
  "title": "[A][1.2.2][1.4.3][1.4.11] Feature 1: Contrast...",
  "severity": "custom",
  "steps": null,
  "devices": null,
  "report": {
    "title": "Same as bug title",
    "content": {
      "data": [
        {
          "key": "wcag_checkpoints",
          "name": "Wcag checkpoints",
          "type": "text",
          "value": "1.2.2, 1.4.3, 1.4.11",
          "position": 1
        }
        // ... 15 more fields
      ]
    }
  }
}
```

### Compatibility with STORY-013

STORY-013 added a model_validator to normalize null fields:
```python
@model_validator(mode="before")
def normalize_non_functional_bug_nulls(cls, data: dict[str, Any]) -> dict[str, Any]:
    if bug_type in ["custom", "visual", "content"]:
        for field in ["steps", "devices", "attachments"]:
            if data.get(field) is None:
                data[field] = []
    return data
```

**This story's change is independent:**
- report_content extraction happens in service layer (before model creation)
- Validator runs during Pydantic initialization
- No conflicts - both work together:
  - Service extracts report_content from API
  - Service passes data to BugDetails(**data)
  - Validator normalizes null fields
  - Model created with both report_content AND normalized fields

### Example Use Cases

**Accessibility Testing - Query WCAG Criteria:**
```python
def get_wcag_checkpoints(bug):
    if not bug.report_content:
        return None
    for field in bug.report_content["data"]:
        if field["key"] == "wcag_checkpoints":
            return field["value"].split(", ")
    return None
```

**Generic Field Access:**
```python
def get_custom_field(bug, key):
    """Get any custom field value by key."""
    if not bug.report_content or "data" not in bug.report_content:
        return None
    for field in bug.report_content.get("data", []):
        if field.get("key") == key:
            return field.get("value")
    return None

# Usage
wcag = get_custom_field(bug, "wcag_checkpoints")
recommendations = get_custom_field(bug, "recommendations")
```

---

## Out of Scope

**Not included in STORY-014:**

1. **Flattened Custom Fields** - Creating top-level convenience fields
2. **Custom Field Search/Filter** - Filtering bugs by custom field values
3. **Report Type Detection** - Auto-detecting report type from configuration
4. **Field Validation** - Validating custom field structures
5. **Visual/Content Bug Investigation** - Focused on custom bugs only

These could be future enhancements if demand arises.

---

## Performance & Security

### Performance Impact
- **Token cost:** +100-300 tokens per custom bug
- **Memory:** Minimal (JSON structure already in API response)
- **Processing:** O(1) field extraction
- **Cache:** No changes (report_content cached with bug)

### Security Considerations
- **No risks:** report_content is read-only JSON data
- **No injection:** Data not parsed or executed
- **No sensitive data:** User-generated test findings

---

## Expected Outcomes

### Data Completeness
- ✅ **100% of custom report content captured** (was 20%)
- ✅ Accessibility reports: WCAG criteria, recommendations, code snippets
- ✅ Purchase reports: Confirmation numbers, payment details
- ✅ Future custom report types: Automatically supported

### User Experience
- ✅ Users can analyze findings without switching to TestIO UI
- ✅ AI assistants can query custom fields programmatically
- ✅ Complete audit trail for compliance

### Technical Benefits
- ✅ Future-proof: New report types work automatically
- ✅ Zero maintenance: No model changes for new report types
- ✅ Backward compatible: Optional field, no breaking changes
- ✅ Generic approach: Scales to any custom report structure

---

## References

- **Investigation:** User conversation 2025-11-06 (exploration of non-functional bug data)
- **Test Case:** Test 1210 (staging) - Bug 3359 with accessibility report
- **Related Stories:**
  - STORY-005b (Custom bug classification)
  - STORY-013 (Null field normalization for non-functional bugs)
- **API Field:** `GET /exploratory_tests/{id}/bugs` returns `report.content` for custom bugs

---

## Dev Agent Record

### Agent Model Used
- Model: claude-sonnet-4-5

### Debug Log References
- None

### Completion Notes
- ✅ All 6 implementation phases completed successfully
- ✅ Added `report_content` field to BugDetails model with comprehensive docstring
- ✅ Updated `_build_bug_details()` service method to extract report.content from API
- ✅ Added 3 new unit tests covering all scenarios (with content, without content, empty content)
- ✅ Added integration test using test 1210 with real accessibility bug data
- ✅ All 291 tests pass, mypy strict passes (28 files), ruff passes
- ✅ Manual testing confirmed 15 custom fields captured for bug 3359 (accessibility report)
- ✅ Backward compatible: report_content defaults to None, existing tests unaffected
- ✅ Compatible with STORY-013: null field normalization works alongside report extraction
- 📊 **Impact:** Custom bugs now capture 100% of report content (was 20%)

**Post-Review Improvements (Codex peer review):**
- ✅ Fixed integration test brittleness: Made test resilient to staging data changes (uses pytest.skip if no data)
- ✅ Updated E2E testing documentation: Added report_content field to response examples

### File List
**Created:**
- docs/stories/story-014-capture-custom-report-content.md

**Modified:**
- src/testio_mcp/models/schemas.py (added report_content field to BugDetails)
- src/testio_mcp/services/bug_service.py (updated _build_bug_details() to extract report.content)
- tests/unit/test_bug_service.py (added 3 unit tests for report_content)
- tests/integration/test_get_test_bugs_integration.py (added integration test, made resilient to data changes)
- docs/E2E_TESTING_SCRIPT.md (updated get_test_bugs response example to include report_content)

### Change Log
| Date | Author | Change |
|------|--------|--------|
| 2025-11-06 | Dev (James) | Initial story creation |
| 2025-11-06 | Dev (James) | Implementation complete - all ACs met, all tests passing |
| 2025-11-06 | Dev (James) | Post-review improvements: Fixed test brittleness, updated E2E docs |

---

**Status:** Ready for Review
**Next Steps:** Code review, then merge to main
