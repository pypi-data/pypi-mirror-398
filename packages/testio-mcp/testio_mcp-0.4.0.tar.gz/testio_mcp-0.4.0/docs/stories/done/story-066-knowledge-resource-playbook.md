# Story 011.066: Knowledge Resource (The Playbook)

Status: review

## Story

As a CSM or AI Agent,
I want to access a structured "Playbook" of expert knowledge via a standard URI (`testio://knowledge/playbook`),
so that I can apply proven heuristics to diagnose issues and generate strategic reports without hallucinating domain rules.

## Acceptance Criteria

1. `testio://knowledge/playbook` is discoverable via `list_resources`.
2. Reading the resource returns the full markdown content matching the "Content Specification" in the Tech Spec.
3. The resource content includes both "Tactical Patterns" (e.g., Noisy Cycle) and "Strategic Templates" (e.g., Quarterly Quality Review).
4. Accessing the resource is logged at debug level.
5. The resource is available via FastMCP's `@mcp.resource` decorator.

## Tasks / Subtasks

- [x] **Task 1: Create Playbook Content**
  - [x] Create `src/testio_mcp/resources/playbook.md` with the content defined in the Tech Spec.
- [x] **Task 2: Implement Resources Module**
  - [x] Create `src/testio_mcp/resources/` directory (python package).
  - [x] Create `src/testio_mcp/resources/__init__.py` to implement the module logic.
  - [x] Implement `register_resources(mcp: FastMCP)` function in `__init__.py`.
  - [x] Use `@mcp.resource("testio://knowledge/playbook")` to serve the file content.
  - [x] Read `playbook.md` relative to the module location (`Path(__file__).parent / "playbook.md"`).
  - [x] Ensure `playbook.md` is included in package data.
- [x] **Task 3: Register Resources in Server**
  - [x] Update `src/testio_mcp/server.py` to import `register_resources` from `testio_mcp.resources`.
- [x] **Task 4: Update Documentation**
  - [x] Update `CLAUDE.md` to list the new resource.
  - [x] Update `README.md` to mention the Playbook resource.
- [x] **Task 5: Testing**
  - [x] Create `tests/unit/test_resources.py` to verify resource registration and content retrieval.
  - [x] Verify `list_resources` includes the playbook.
  - [x] Verify `read_resource` returns correct content.

## Dev Notes

- **Architecture:** We are using a self-contained `resources` package.
- **Project Structure:**
    - `src/testio_mcp/resources/` (New Package)
    - `src/testio_mcp/resources/__init__.py` (Module logic)
    - `src/testio_mcp/resources/playbook.md` (Data file)
- **Source Tree Components:**
    - `src/testio_mcp/server.py`
    - `src/testio_mcp/resources/` (New)

### Project Structure Notes

- Alignment with unified project structure: `src/testio_mcp/resources.py` fits well alongside `tools/` and `services/`.
- No conflicts detected.

### References

- [Tech Spec: Epic 011](docs/sprint-artifacts/tech-spec-epic-011.md)
- [Epic 011: Showcase & Polish](docs/epics/epic-011-showcase-and-polish.md)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- Implemented `testio://knowledge/playbook` resource using FastMCP's `@mcp.resource` decorator.
- Created `src/testio_mcp/resources/` package to house resource logic and data.
- Added `playbook.md` with "Tactical Patterns" and "Strategic Templates" as defined in Tech Spec.
- Registered resources in `src/testio_mcp/server.py`.
- Updated `CLAUDE.md` and `README.md` to document the new capability.
- Added unit tests in `tests/unit/test_resources.py` to verify registration and content serving.

### File List

- src/testio_mcp/resources/playbook.md
- src/testio_mcp/resources/__init__.py
- src/testio_mcp/server.py
- CLAUDE.md
- README.md
- tests/unit/test_resources.py
