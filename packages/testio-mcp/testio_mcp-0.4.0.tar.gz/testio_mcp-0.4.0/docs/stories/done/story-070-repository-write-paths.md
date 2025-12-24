Status: review

## Story

As a **developer**,
I want **the repository layer to extract and store test_environment and known on writes**,
so that **new synced data populates the new columns correctly**.

## Acceptance Criteria

1. **Test Repository Write Path:**
   - When `TestRepository.insert_test()` or `update_test()` is called with a test API response containing `test_environment`.
   - The `test.test_environment` column stores `{id, title}` (extracting only these fields for security).

2. **Bug Repository Write Path:**
   - When `BugRepository._write_bugs_to_db()` or `refresh_bugs()` is called with a bug API response containing `known`.
   - The `bug.known` column is set to the boolean value from the API.

3. **Bug Known Default Value:**
   - If the bug API response is missing the `known` field.
   - The `bug.known` column defaults to `False`.

## Tasks / Subtasks

- [x] **Task 1: Update Bug Transformers and Types** (AC: 2, 3)
  - [x] Update `BugOrmData` TypedDict in `src/testio_mcp/transformers/bug_transformers.py` to include `known: bool`.
  - [x] Update transformer logic to extract `known` field from API response, defaulting to `False`.

- [x] **Task 2: Update Test Repository Writes** (AC: 1)
  - [x] Update `insert_test` in `src/testio_mcp/repositories/test_repository.py` to extract and store `test_environment`.
  - [x] Update `update_test` in `src/testio_mcp/repositories/test_repository.py` to update `test_environment`.
  - [x] Implement security filtering to only store `id` and `title` from `test_environment`.
  - [x] Add unit tests for `insert_test` and `update_test` verifying `test_environment` persistence.

- [x] **Task 3: Update Bug Repository Writes** (AC: 2, 3)
  - [x] Update `_write_bugs_to_db` in `src/testio_mcp/repositories/bug_repository.py` to include `known` in the UPSERT `set_` clause.
  - [x] Verify `known` is correctly passed from transformer to ORM model.
  - [x] Add unit tests for `_write_bugs_to_db` verifying `known` persistence and default value.

## Dev Notes

- **Architecture Patterns:**
  - **Security:** Explicitly filter `test_environment` fields. Do not store the raw dictionary blindly.
  - **ORM:** SQLAlchemy handles JSON serialization for `test_environment`.
  - **UPSERT:** Ensure `known` is included in the `on_conflict_do_update` set clause for bugs.

- **Source Tree Components:**
  - `src/testio_mcp/repositories/test_repository.py`
  - `src/testio_mcp/repositories/bug_repository.py`
  - `src/testio_mcp/transformers/bug_transformers.py`

- **Testing Standards:**
  - Unit tests should use `mock_persistent_cache` and verify DB state.
  - Test cases should cover:
    - `test_environment` present/missing/malformed.
    - `known` true/false/missing.

### Project Structure Notes

- Aligns with unified project structure.
- Modifies existing repositories and transformers.

### Learnings from Previous Story

**From Story story-069-database-columns (Status: done)**

- **New Columns Created**: `test_environment` (JSON) in `tests` table, `known` (BOOLEAN) in `bugs` table.
- **Migration Complete**: Schema is ready, backfill applied to existing data.
- **Critical Dependency**: This story (070) is required to populate these columns for *new* data. Without it, new syncs will leave these columns NULL/False.
- **Files Modified**: `src/testio_mcp/models/orm/test.py`, `src/testio_mcp/models/orm/bug.py`.

[Source: stories/story-069-database-columns.md#Dev-Agent-Record]

### References

- [Epic 012: Test Environments and Known Bugs](docs/epics/epic-012-polish.md#story-070-update-repository-write-paths-for-new-columns)
- [Architecture: Local Data Store](docs/architecture/ARCHITECTURE.md#local-data-store-strategy)
- [Coding Standards](docs/architecture/CODING-STANDARDS.md)

## Dev Agent Record

### Context Reference

- [Story Context](docs/sprint-artifacts/story-070-repository-write-paths.context.xml)

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- Implemented `test_environment` extraction and storage in `TestRepository`.
- Implemented `known` field extraction and storage in `BugRepository`.
- Updated `BugOrmData` and transformer logic.
- Added comprehensive unit tests for both repositories.
- Verified all changes with unit tests.

### File List

- `src/testio_mcp/transformers/bug_transformers.py`
- `src/testio_mcp/repositories/test_repository.py`
- `src/testio_mcp/repositories/bug_repository.py`
- `tests/unit/test_test_repository_writes.py`
- `tests/unit/test_bug_repository_writes.py`

## Change Log

- 2025-11-30: Story drafted
- 2025-12-01: Implemented repository write paths for `test_environment` and `known` fields. Added unit tests.
- 2025-11-30: Senior Developer Review notes appended.

## Senior Developer Review (AI)

### Reviewer
leoric

### Date
2025-11-30

### Outcome
**Approve**

The implementation correctly updates the repository write paths to handle the new `test_environment` and `known` fields. Security filtering is implemented as required, and comprehensive unit tests are provided.

### Key Findings

- **[Low]** Implementation follows existing patterns and is clean.
- **[Low]** Security filtering for `test_environment` is correctly implemented in `TestRepository`.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| 1 | Test Repository Write Path | **IMPLEMENTED** | `src/testio_mcp/repositories/test_repository.py`:181, 310; `tests/unit/test_test_repository_writes.py` |
| 2 | Bug Repository Write Path | **IMPLEMENTED** | `src/testio_mcp/repositories/bug_repository.py`:816; `tests/unit/test_bug_repository_writes.py` |
| 3 | Bug Known Default Value | **IMPLEMENTED** | `src/testio_mcp/transformers/bug_transformers.py`:129; `tests/unit/test_bug_repository_writes.py` |

**Summary:** 3 of 3 acceptance criteria fully implemented.

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Task 1: Update Bug Transformers and Types | [x] | **VERIFIED COMPLETE** | `src/testio_mcp/transformers/bug_transformers.py` |
| Task 2: Update Test Repository Writes | [x] | **VERIFIED COMPLETE** | `src/testio_mcp/repositories/test_repository.py`, `tests/unit/test_test_repository_writes.py` |
| Task 3: Update Bug Repository Writes | [x] | **VERIFIED COMPLETE** | `src/testio_mcp/repositories/bug_repository.py`, `tests/unit/test_bug_repository_writes.py` |

**Summary:** 3 of 3 completed tasks verified.

### Test Coverage and Gaps
- **Coverage:** Comprehensive unit tests added for both `TestRepository` (insert/update) and `BugRepository` (write/refresh).
- **Gaps:** None identified.

### Architectural Alignment
- **Tech Spec:** Aligns with Epic 012 requirements.
- **Patterns:** Follows Repository pattern and SQLModel usage.
- **Security:** `test_environment` filtering implemented as requested.

### Action Items

**Code Changes Required:**
*(None)*

**Advisory Notes:**
*(None)*

## Extra Validation Review (Codex)

### Reviewer
codex

### Date
2025-11-30

### Findings Addressed
- **Known Field Validation:** Enforced boolean type for `known` field in `BugOrmData` transformer.
- **Reported At Consistency:** Updated transformer to use `reported_at` from API, and refactored `refresh_bugs` and `refresh_bugs_batch` to use `_write_bugs_to_db` for consistency.
- **Test Environment Security:** Added type validation for `id` (int) and `title` (str) in `TestRepository` to prevent PII/nested object storage.
- **Test Coverage:** Added unit test for invalid `test_environment` types. Verified all tests pass.

### Outcome
**Validated & Fixed**
