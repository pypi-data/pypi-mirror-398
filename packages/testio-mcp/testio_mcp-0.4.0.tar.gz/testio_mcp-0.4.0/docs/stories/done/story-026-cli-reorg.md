---
story_id: STORY-026
epic_id: NONE
title: CLI Code Reorganization
status: todo
created: 2025-11-20
updated: 2025-11-20
estimate: 0.5 days
assignee: unassigned
dependencies: []
priority: low
implementation_difficulty: 2/10 (low)
---

# STORY-026: CLI Code Reorganization

## User Story
**As a** developer
**I want** to have all CLI commands organized in a dedicated `src/testio_mcp/cli/` directory
**So that** the codebase is easier to navigate and maintain

## Context
Currently, CLI commands are scattered or located in places that might not be intuitive (e.g., `src/testio_mcp/sync.py`, `src/testio_mcp/problematic.py`). We want to improve code organization by grouping all CLI-related code into a dedicated `src/testio_mcp/cli` folder.

## Goals
1. Improve codebase organization.
2. Make CLI commands easier to find.
3. Prepare for adding more CLI commands (like the setup command in STORY-027).

## Acceptance Criteria
- [ ] Create `src/testio_mcp/cli/` directory.
- [ ] Move `src/testio_mcp/cli.py` to `src/testio_mcp/cli/main.py`.
- [ ] Move `src/testio_mcp/sync.py` to `src/testio_mcp/cli/sync.py`.
- [ ] Move `src/testio_mcp/problematic.py` to `src/testio_mcp/cli/problematic.py`.
- [ ] Create `src/testio_mcp/cli/__init__.py` exposing `main`.
- [ ] Update `src/testio_mcp/__main__.py` to import from `testio_mcp.cli.main`.
- [ ] Update imports in `sync.py` and `problematic.py` to fix relative/absolute imports.
- [ ] Update `load_env_file()` to support precedence order: 1) `--env-file` (if provided), 2) `~/.testio-mcp.env` (if exists), 3) `.env` in current directory.
- [ ] Verify `uvx testio-mcp` still works for all subcommands.

## Technical Design
- **Directory Structure:**
  ```
  src/testio_mcp/
  ├── cli/
  │   ├── __init__.py      # Exposes main
  │   ├── main.py          # Formerly cli.py (argparse setup)
  │   ├── sync.py          # Moved from parent
  │   └── problematic.py   # Moved from parent
  ├── __main__.py          # Imports from testio_mcp.cli.main
  ```
- **Imports:**
  - `testio_mcp.cli.main` will import `sync_command_main` from `.sync` and `problematic_command_main` from `.problematic`.
  - Ensure `testio_mcp` package imports (like `testio_mcp.config`) still work correctly.
- **Environment File Loading (Precedence Order):**
  - Update `load_env_file()` function in `main.py`:
    ```python
    def load_env_file(env_file: Path | None) -> None:
        """Load environment variables with precedence order.

        Precedence:
        1. --env-file PATH (if provided) - explicit user override
        2. ~/.testio-mcp.env (if exists) - setup command default
        3. .env in current directory (if exists) - local development
        """
        if env_file:
            # Explicit --env-file takes highest precedence
            if not env_file.exists():
                print(f"Error: --env-file '{env_file}' not found", file=sys.stderr)
                sys.exit(1)
            load_dotenv(env_file, override=True)
        else:
            # Check ~/.testio-mcp.env first (setup command default)
            global_env = Path.home() / ".testio-mcp.env"
            if global_env.exists():
                load_dotenv(global_env, override=True)
            else:
                # Fall back to .env in current directory (local dev)
                load_dotenv(override=False)
    ```

## Definition of Done
- [ ] Code moved to `src/testio_mcp/cli/`.
- [ ] Application runs without import errors.
- [ ] Environment file precedence order implemented and tested (--env-file > ~/.testio-mcp.env > .env).
- [ ] Quality verification passes: `uv run ruff check --fix && uv run ruff format && uv run mypy src && uv run pre-commit run --all-files && time TESTIO_PRODUCT_ID=25043 TESTIO_PRODUCT_IDS=25043 TESTIO_TEST_ID=141290 uv run pytest -q --cov=src`
