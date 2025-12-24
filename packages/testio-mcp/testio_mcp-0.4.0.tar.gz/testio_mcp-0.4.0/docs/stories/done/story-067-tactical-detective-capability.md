# Story 011.067: Tactical Detective Capability

Status: review

## Story

As a CSM using the Tactical Detective workflow,
I want the system to automatically parse bug rejection reasons and provide full test instructions,
so that I can accurately diagnose 'noisy' cycles without manually reading hundreds of comments.

## Acceptance Criteria

1. **Rejection Reason Parsing:**
   - `REJECTION_REASONS` constant is defined in `src/testio_mcp/schemas/constants.py` including `request_timeout`.
   - `Bug` ORM model includes a nullable `rejection_reason` TEXT column.
   - `transform_api_bug_to_orm` function correctly parses raw API bug data to extract rejection reasons from comments.
   - `BugRepository` uses the transformer to populate `rejection_reason` when saving bugs.
   - Existing rejected bugs are backfilled with parsed rejection reasons.

2. **Instruction Text:**
   - `get_test_summary` returns the complete, untruncated `instructions` text for a test.

## Tasks / Subtasks

- [x] **Task 1: Define Constants**
  - [x] Add `REJECTION_REASONS` list to `src/testio_mcp/schemas/constants.py`.

- [x] **Task 2: Update Data Model**
  - [x] Add `rejection_reason` column to `src/testio_mcp/models/orm/bug.py`.
  - [x] Generate Alembic migration for the new column.

- [x] **Task 3: Implement Bug Transformer**
  - [x] Create `src/testio_mcp/transformers/bug_transformers.py`.
  - [x] Implement `transform_api_bug_to_orm` to parse comments against `REJECTION_REASONS`.
  - [x] Handle `request_timeout` pattern specifically.

- [x] **Task 4: Update Repository**
  - [x] Update `BugRepository._write_bugs_to_db` in `src/testio_mcp/repositories/bug_repository.py` to use the transformer.

- [x] **Task 5: Verify Instruction Text**
  - [x] Verify `get_test_summary` in `src/testio_mcp/services/test_service.py` (or tool wrapper) does not truncate instructions.

- [x] **Task 6: Testing**
  - [x] Create `tests/unit/test_bug_transformers.py` to verify parsing logic.
  - [x] Verify backfill strategy (migration or script).

## Dev Notes

- **Architecture:**
    - **Transformer Pattern:** Use `transformers` module as an Anti-Corruption Layer (ACL) to keep Repository clean.
    - **Schema:** New column `rejection_reason` in `bugs` table.

- **Project Structure:**
    - `src/testio_mcp/transformers/bug_transformers.py` (New)
    - `src/testio_mcp/schemas/constants.py` (Modify)
    - `src/testio_mcp/models/orm/bug.py` (Modify)

### Learnings from Previous Story

**From Story story-066-knowledge-resource-playbook (Status: review)**

- **New Service Created**: `src/testio_mcp/resources/` package for MCP resources.
- **Architectural Change**: Implemented `testio://knowledge/playbook` using `@mcp.resource`.
- **Files Created**: `src/testio_mcp/resources/playbook.md`, `src/testio_mcp/resources/__init__.py`.
- **Note**: This story focuses on the *Tool* side (Tactical Detective), complementing the *Resource* side (Playbook) from Story 066.

### References

- [Tech Spec: Epic 011](docs/sprint-artifacts/tech-spec-epic-011.md)
- [Epic 011: Showcase & Polish](docs/epics/epic-011-showcase-and-polish.md)

## Dev Agent Record

### Context Reference

- [Story Context](docs/sprint-artifacts/story-067-tactical-detective-capability.context.xml)

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- Implemented `REJECTION_REASONS` constant.
- Added `rejection_reason` column to `Bug` model and generated migration.
- Created `bug_transformers.py` to parse rejection reasons from comments.
- Updated `BugRepository` to use the transformer.
- Updated `TestService` to prefer `instructions_text` for full instructions.
- Created unit tests for transformer.
- Created and executed `scripts/backfill_rejection_reasons.py` to backfill 2124 existing rejected bugs.

### File List

- src/testio_mcp/schemas/constants.py
- src/testio_mcp/models/orm/bug.py
- src/testio_mcp/transformers/bug_transformers.py
- src/testio_mcp/repositories/bug_repository.py
- src/testio_mcp/services/test_service.py
- tests/unit/test_bug_transformers.py
- scripts/backfill_rejection_reasons.py
- alembic/versions/f63655d178ae_add_rejection_reason_to_bugs.py

## Senior Developer Review (AI)

### Reviewer: leoric
### Date: 2025-11-30
### Outcome: Approve

**Summary**
The implementation successfully delivers the "Tactical Detective" capability by enabling the parsing of bug rejection reasons from comments and ensuring full instruction text is available. The solution uses a clean "Transformer Pattern" to encapsulate the parsing logic, keeping the repository and service layers focused on their primary responsibilities. The database schema changes are properly handled via Alembic, and a backfill script is provided for existing data.

**Key Findings**
- **High Quality Architecture:** The decision to use a dedicated `bug_transformers.py` module is excellent. It isolates the messy logic of parsing unstructured comments from the core data access layer.
- **Comprehensive Coverage:** The `REJECTION_REASONS` constant covers all identified patterns, including the system-generated `request_timeout`.
- **Robust Testing:** Unit tests cover various scenarios (match, no match, different reasons), and the backfill script ensures data consistency.

**Acceptance Criteria Coverage**

| AC# | Description | Status | Evidence |
| :--- | :--- | :--- | :--- |
| 1 | Rejection Reason Parsing | **IMPLEMENTED** | `src/testio_mcp/transformers/bug_transformers.py:14-38`<br>`src/testio_mcp/models/orm/bug.py:59`<br>`src/testio_mcp/repositories/bug_repository.py:759` |
| 2 | Instruction Text | **IMPLEMENTED** | `src/testio_mcp/services/test_service.py:174` |

**Summary:** 2 of 2 acceptance criteria fully implemented.

**Task Completion Validation**

| Task | Marked As | Verified As | Evidence |
| :--- | :--- | :--- | :--- |
| Task 1: Define Constants | [x] | **VERIFIED** | `src/testio_mcp/schemas/constants.py:36` |
| Task 2: Update Data Model | [x] | **VERIFIED** | `src/testio_mcp/models/orm/bug.py:59`, `alembic/versions/f63655d178ae...` |
| Task 3: Implement Bug Transformer | [x] | **VERIFIED** | `src/testio_mcp/transformers/bug_transformers.py` |
| Task 4: Update Repository | [x] | **VERIFIED** | `src/testio_mcp/repositories/bug_repository.py:759` |
| Task 5: Verify Instruction Text | [x] | **VERIFIED** | `src/testio_mcp/services/test_service.py:174` |
| Task 6: Testing | [x] | **VERIFIED** | `tests/unit/test_bug_transformers.py`, `scripts/backfill_rejection_reasons.py` |

**Summary:** 6 of 6 completed tasks verified.

**Test Coverage and Gaps**
- **Unit Tests:** `tests/unit/test_bug_transformers.py` provides good coverage for the parsing logic.
- **Integration:** The backfill script serves as a form of integration verification for the data transformation on real data.

**Architectural Alignment**
- **Transformer Pattern:** Correctly implemented as an Anti-Corruption Layer (ACL) as requested in the Tech Spec.
- **Schema:** Correctly added `rejection_reason` as a nullable TEXT column.

**Security Notes**
- No new security risks introduced. Input sanitization is handled by the transformer (stripping whitespace).

**Best-Practices and References**
- [Transformer Pattern](https://martinfowler.com/eaaCatalog/dataMapper.html) (loosely applied here for data transformation)

**Action Items**

**Advisory Notes:**
- Note: Ensure the backfill script is run in production after deployment.
- Note: Monitor logs for "unmatched" rejection reasons to potentially expand the `REJECTION_REASONS` list in the future.

## Change Log

- 2025-11-30: Senior Developer Review notes appended. Status updated to done.
