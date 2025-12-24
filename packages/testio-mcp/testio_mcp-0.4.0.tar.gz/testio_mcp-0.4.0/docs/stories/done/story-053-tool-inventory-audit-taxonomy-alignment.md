# Story 008.053: Tool Inventory Audit & Taxonomy Alignment

status: done

## Story

As a developer maintaining the MCP server,
I want tools to follow a consistent naming taxonomy,
So that users can predict tool names and understand their purpose.

## Acceptance Criteria

1. [ ] Rename `get_test_status` -> `get_test_summary`
   - Update tool file name: `test_status_tool.py` -> `test_summary_tool.py`
   - Update function name and decorator
   - Update all imports and references
   - **Constraint:** Do NOT maintain backward compatibility (clean break)

2. [ ] Rename `generate_ebr_report` -> `get_product_quality_report`
   - Update tool file name: `generate_ebr_report_tool.py` -> `product_quality_report_tool.py`
   - Update function name and decorator
   - Update tool description (remove "EBR" jargon)
   - Update all imports and references
   - **Constraint:** Do NOT maintain backward compatibility

3. [ ] Remove `list_user_stories` tool (redundant)
   - Delete `src/testio_mcp/tools/list_user_stories_tool.py`
   - Remove any imports/references to `list_user_stories`
   - Update CLAUDE.md: remove from tool list, note user stories via `list_features`
   - Verify `list_features` returns embedded user stories (no functionality loss)

4. [ ] Move `get_analytics_capabilities` to disabled-by-default
   - Add to `TESTIO_DISABLED_TOOLS` default list in config
   - Document how to enable if needed
   - Create MCP prompt as alternative (STORY-059)

5. [ ] Update all tool descriptions for consistency
   - Follow pattern: "Verb + object + purpose"
   - Remove redundant examples from descriptions (move to prompts)

6. [ ] Update REST API routes to match new tool names
   - `/api/test/{id}/status` -> `/api/test/{id}/summary`
   - `/api/products/{id}/ebr` -> `/api/products/{id}/quality-report`

7. [ ] Update CLAUDE.md with new tool names

8. [ ] All tests pass after renaming

## Tasks / Subtasks

- [ ] Task 1: Rename `get_test_status` (AC1)
  - [ ] Rename file `src/testio_mcp/tools/test_status_tool.py` to `test_summary_tool.py`
  - [ ] Update function name to `get_test_summary`
  - [ ] Update imports in `server.py` and `api.py`
  - [ ] Update tests in `tests/unit/test_tools_test_status.py` (rename file too)

- [ ] Task 2: Rename `generate_ebr_report` (AC2)
  - [ ] Rename file `src/testio_mcp/tools/generate_ebr_report_tool.py` to `product_quality_report_tool.py`
  - [ ] Update function name to `get_product_quality_report`
  - [ ] Update imports in `server.py` and `api.py`
  - [ ] Update tests in `tests/unit/test_tools_generate_ebr_report_file_export.py` (rename file too)

- [ ] Task 3: Remove `list_user_stories` (AC3)
  - [ ] Delete `src/testio_mcp/tools/list_user_stories_tool.py`
  - [ ] Remove from `server.py`
  - [ ] Update `CLAUDE.md`

- [ ] Task 4: Disable `get_analytics_capabilities` (AC4)
  - [ ] Update `config.py` to include it in `TESTIO_DISABLED_TOOLS` by default

- [ ] Task 5: Update Tool Descriptions (AC5)
  - [ ] Audit and update all tool docstrings/descriptions
  - [ ] Remove verbose examples

- [ ] Task 6: Update REST API (AC6)
  - [ ] Update routes in `src/testio_mcp/api.py`

- [ ] Task 7: Update Documentation (AC7)
  - [ ] Update `CLAUDE.md` tool list

- [ ] Task 8: Verification (AC8)
  - [ ] Run full test suite
  - [ ] Verify MCP tool list via inspector (optional)

## Dev Notes

### Learnings from Previous Story

**From Story 9.4 - Remove force_refresh_bugs (Status: done)**

- **New Services/Patterns**:
    - `sync_data` MCP tool for explicit data refresh
    - `SyncDataOutput` schema
    - Timestamp persistence pattern (`cache.get/set_metadata_value`)
- **Architectural Decisions**:
    - Service Layer Pattern (ADR-006): Tools are thin wrappers
    - Schema Token Optimization: Target ~550-600 tokens
- **Warnings/Recommendations**:
    - ⚠️ **Schema token count**: Measure carefully. Target 10-15% reduction.
    - ✅ **Migration guidance**: Document clear before/after examples in CLAUDE.md.

[Source: docs/stories/story-052-remove-force-refresh-bugs.md#Dev-Agent-Record]

### Project Structure Notes

- Alignment with unified project structure:
    - Tools in `src/testio_mcp/tools/`
    - Services in `src/testio_mcp/services/`
    - Tests in `tests/unit/` and `tests/integration/`

### References

- [Epic-008: MCP Layer Optimization](docs/epics/epic-008-mcp-layer-optimization.md)
- [Story-052: Remove force_refresh_bugs](docs/stories/story-052-remove-force-refresh-bugs.md)

## Dev Agent Record

### Context Reference

- [story-053-tool-inventory-audit-taxonomy-alignment.context.xml](docs/sprint-artifacts/story-053-tool-inventory-audit-taxonomy-alignment.context.xml)

### Agent Model Used

Gemini 2.0 Flash

### Debug Log References

### Completion Notes List

### File List

## Code Review - 2025-11-28

**Reviewer:** Senior Developer Agent
**Status:** ❌ Changes Requested

### Summary
The implementation largely meets the requirements for tool renaming and taxonomy alignment. However, a significant inconsistency was found in the service layer for AC1, where the underlying service method was not renamed to match the new taxonomy, unlike AC2 where it was correctly updated.

### Validation Findings

| AC | Description | Status | Evidence/Notes |
|----|-------------|--------|----------------|
| 1 | Rename `get_test_status` -> `get_test_summary` | ⚠️ Partial | Tool and API renamed, but `TestService.get_test_status` (src/testio_mcp/services/test_service.py:102) was NOT renamed. |
| 2 | Rename `generate_ebr_report` -> `get_product_quality_report` | ✅ Implemented | Renamed in Tool, API, and Service (`MultiTestReportService.get_product_quality_report`). |
| 3 | Remove `list_user_stories` tool | ✅ Implemented | Tool file removed. `UserStoryService` and API endpoint remain (acceptable). |
| 4 | Move `get_analytics_capabilities` to disabled-by-default | ✅ Implemented | Added to `DISABLED_TOOLS` in `config.py`. |
| 5 | Update all tool descriptions | ✅ Implemented | Verified descriptions follow "Verb + object + purpose". |
| 6 | Update REST API routes | ✅ Implemented | `/api/tests/{id}/summary` and `/api/products/{id}/quality-report` updated. |
| 7 | Update `CLAUDE.md` | ✅ Implemented | Tool names updated. |
| 8 | All tests pass | ✅ Implemented | 755 passed, 12 skipped. |

### Code Quality & Risk
*   **Consistency:** The mismatch between `TestService.get_test_status` and `MultiTestReportService.get_product_quality_report` (renamed) creates architectural inconsistency.
*   **Testing:** Unit tests (`tests/unit/test_test_service.py`) still reference the old method name `get_test_status`.
*   **Risk:** Low functional risk (tests pass), but high maintainability risk due to confusing naming.

### Action Items
1.  **[High]** Rename `TestService.get_test_status` to `TestService.get_test_summary` to match AC1 and the new taxonomy. (✅ Done)
2.  **[High]** Update `tests/unit/test_test_service.py` to use `get_test_summary`. (✅ Done)
3.  **[High]** Update `src/testio_mcp/tools/test_summary_tool.py` and `src/testio_mcp/api.py` to call the renamed service method. (✅ Done)

## Code Review - 2025-11-28 (Final)

**Reviewer:** Senior Developer Agent
**Status:** ✅ Approved

### Summary
All feedback from the previous review has been addressed. `TestService.get_test_status` has been correctly renamed to `get_test_summary`, and all dependent code (tests, API, tools) has been updated. The full test suite passes.

### Final Verification
- **AC1:** `TestService.get_test_summary` is now consistent with the tool name.
- **Tests:** All tests passed.

### Outcome
Story is approved and ready for merge.

## Senior Developer Review (AI) - 2025-11-28

**Reviewer:** leoric
**Date:** 2025-11-28
**Outcome:** ⚠️ Changes Requested (Documentation Gap)

### Summary
Re-review of this completed story reveals that the core implementation is correct, but CLAUDE.md contains stale references to old method/tool names in the example code sections. This is a LOW severity documentation issue that should be addressed for consistency, but does not block functionality.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| 1 | Rename `get_test_status` -> `get_test_summary` | ✅ Implemented | Tool: `src/testio_mcp/tools/test_summary_tool.py` (file exists). Service: `TestService.get_test_summary` at `src/testio_mcp/services/test_service.py:102`. |
| 2 | Rename `generate_ebr_report` -> `get_product_quality_report` | ✅ Implemented | Tool: `src/testio_mcp/tools/product_quality_report_tool.py` (file exists). Service: `MultiTestReportService.get_product_quality_report` at `src/testio_mcp/services/multi_test_report_service.py:91`. |
| 3 | Remove `list_user_stories` tool | ✅ Implemented | Tool file `src/testio_mcp/tools/list_user_stories_tool.py` does NOT exist. |
| 4 | Move `get_analytics_capabilities` to disabled-by-default | ✅ Implemented | `config.py:339` sets default `DISABLED_TOOLS = ["get_analytics_capabilities"]`. |
| 5 | Update all tool descriptions | ✅ Implemented | Tool docstrings follow "Verb + object + purpose" pattern. |
| 6 | Update REST API routes | ✅ Implemented | `api.py:200`: `GET /api/tests/{test_id}/summary`. `api.py:428`: `GET /api/products/{product_id}/quality-report`. |
| 7 | Update CLAUDE.md with new tool names | ⚠️ Partial | Tool list at lines 18-21 updated. **But example code at lines 165, 177, 750-757, 849-922 still references old names** (`get_test_status`, `generate_ebr_report`). |
| 8 | All tests pass | ✅ Verified | Test run: 755 passed, 12 skipped. |

**Summary:** 7 of 8 ACs fully implemented. AC7 partial (tool list updated, but example code sections not updated).

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Rename `get_test_status` | [ ] (unchecked) | ✅ DONE | Tool renamed, service renamed, tests updated. |
| Task 2: Rename `generate_ebr_report` | [ ] (unchecked) | ✅ DONE | Tool renamed, service renamed, tests updated. |
| Task 3: Remove `list_user_stories` | [ ] (unchecked) | ✅ DONE | File deleted, no references. |
| Task 4: Disable `get_analytics_capabilities` | [ ] (unchecked) | ✅ DONE | Added to default disabled list. |
| Task 5: Update Tool Descriptions | [ ] (unchecked) | ✅ DONE | Descriptions follow pattern. |
| Task 6: Update REST API | [ ] (unchecked) | ✅ DONE | Routes updated. |
| Task 7: Update Documentation | [ ] (unchecked) | ⚠️ PARTIAL | Tool list updated, example code not updated. |
| Task 8: Verification | [ ] (unchecked) | ✅ DONE | Tests pass. |

**Summary:** 7 of 8 tasks fully verified. Task 7 partial (checkboxes not marked in story file, but tasks are completed except documentation examples).

### Code Quality & Risk

- **Implementation:** Clean and consistent. Tool files, service methods, API routes, and tests all use new naming conventions.
- **Documentation Gap:** CLAUDE.md example code sections still reference:
  - `service.get_test_status` (should be `get_test_summary`) at lines 165, 177
  - `generate_ebr_report(...)` examples at lines 849-922
- **Risk:** LOW - This is documentation-only; functional code is correct.

### Test Coverage and Gaps

- **Unit tests:** `tests/unit/test_test_service.py` correctly uses `get_test_summary`.
- **Tool tests:** `tests/unit/test_tools_test_summary.py`, `tests/unit/test_tools_product_quality_report.py` exist and pass.
- **Integration tests:** 12 skipped (require API credentials), but pattern is correct.

### Architectural Alignment

- ✅ Service layer pattern (ADR-006) followed correctly.
- ✅ Tool -> Service naming consistency achieved (both use `get_test_summary`).
- ✅ Taxonomy alignment: discover (`list_*`) + summarize (`get_*_summary`) + analyze pattern.

### Security Notes

No security concerns identified.

### Best-Practices and References

- [FastMCP Documentation](https://gofastmcp.com) - Tool registration patterns
- [ADR-006](docs/architecture/adrs/ADR-006-service-layer.md) - Service layer pattern

### Action Items

**Code Changes Required:**
- [x] [Low] Update CLAUDE.md example pattern: change `service.get_test_status` to `service.get_test_summary` ✅ Done
- [x] [Low] Update CLAUDE.md service test example: change `get_test_status` to `get_test_summary` ✅ Done
- [x] [Low] Update CLAUDE.md migration examples: change `generate_ebr_report` to `get_product_quality_report` ✅ Done

**Advisory Notes:**
- Note: All CLAUDE.md examples now use correct tool/method names.
- Note: Examples also shortened for brevity.
