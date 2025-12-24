---
story_id: STORY-028
epic_id: NONE
title: Database and Utilities Code Reorganization
status: Ready for Review
created: 2025-11-20
updated: 2025-11-20
estimate: 0.5 days
assignee: dev (James)
dependencies: [STORY-026]
priority: low
implementation_difficulty: 2/10 (low)
---

# STORY-028: Database and Utilities Code Reorganization

## User Story
**As a** developer
**I want** to have database code in a dedicated `database/` directory and all utility functions consolidated in `utilities/`
**So that** the codebase follows consistent organizational patterns and is easier to navigate

## Context
Following the CLI reorganization in STORY-026, we have identified additional opportunities to improve code organization:

1. **Database files in root:** `cache.py` (100KB!) and `schema.py` are in the root of `src/testio_mcp/`, but they're tightly related and should be grouped together.
2. **Scattered utilities:** `timezone_utils.py` and `schema_utils.py` are in the root, but `utilities/` directory already exists with other utility modules.

This story follows the same pattern as STORY-026 to improve discoverability and maintainability.

## Goals
1. Group related database code together in a dedicated directory.
2. Consolidate all utility functions in the `utilities/` directory.
3. Maintain consistent organizational patterns across the codebase.
4. Reduce root directory clutter.

## Acceptance Criteria

### Phase 1: Database Directory
- [ ] Create `src/testio_mcp/database/` directory.
- [ ] Move `src/testio_mcp/cache.py` to `src/testio_mcp/database/cache.py`.
- [ ] Move `src/testio_mcp/schema.py` to `src/testio_mcp/database/schema.py`.
- [ ] Create `src/testio_mcp/database/__init__.py` exposing `PersistentCache` and schema functions.
- [ ] Update all imports referencing `testio_mcp.cache` and `testio_mcp.schema` (~11 files).

### Phase 2: Utilities Consolidation
- [ ] Move `src/testio_mcp/timezone_utils.py` to `src/testio_mcp/utilities/timezone_utils.py`.
- [ ] Move `src/testio_mcp/schema_utils.py` to `src/testio_mcp/utilities/schema_utils.py`.
- [ ] Update `src/testio_mcp/utilities/__init__.py` to expose commonly used functions.
- [ ] Update all imports referencing these utilities.

### Quality Verification
- [ ] All tests pass after reorganization.
- [ ] No import errors when running `uvx testio-mcp` commands.
- [ ] Mypy type checking passes.
- [ ] Pre-commit hooks pass.

## Technical Design

### Directory Structure (After)
```
src/testio_mcp/
├── database/
│   ├── __init__.py      # Exposes PersistentCache, schema functions
│   ├── cache.py         # Moved from parent (PersistentCache class)
│   └── schema.py        # Moved from parent (DDL operations)
├── utilities/
│   ├── __init__.py      # Exposes commonly used utilities
│   ├── bug_classifiers.py    # Already here
│   ├── date_utils.py         # Already here
│   ├── file_export.py        # Already here
│   ├── parsing.py            # Already here
│   ├── service_helpers.py    # Already here
│   ├── timezone_utils.py     # MOVED from parent
│   └── schema_utils.py       # MOVED from parent
```

### Import Mappings

**Database imports:**
```python
# Before
from testio_mcp.cache import PersistentCache
from testio_mcp.schema import initialize_database, CURRENT_SCHEMA_VERSION

# After
from testio_mcp.database import PersistentCache
from testio_mcp.database import initialize_database, CURRENT_SCHEMA_VERSION
```

**Utilities imports:**
```python
# Before
from testio_mcp.timezone_utils import normalize_to_utc
from testio_mcp.schema_utils import format_test_dates

# After
from testio_mcp.utilities import normalize_to_utc, format_test_dates
# Or explicit:
from testio_mcp.utilities.timezone_utils import normalize_to_utc
from testio_mcp.utilities.schema_utils import format_test_dates
```

### Files Requiring Import Updates

**Phase 1 (database):** ~11 files
- `src/testio_mcp/server.py`
- `src/testio_mcp/tools/cache_tools.py`
- `src/testio_mcp/cli/sync.py`
- `src/testio_mcp/cli/problematic.py`
- `src/testio_mcp/repositories/test_repository.py`
- Test files in `tests/`

**Phase 2 (utilities):**
- `src/testio_mcp/cache.py` (becomes `database/cache.py`)
- `src/testio_mcp/repositories/test_repository.py`
- `src/testio_mcp/tools/` (multiple tool files)
- `src/testio_mcp/cli/problematic.py`
- Test files: `tests/unit/test_date_utils.py`, `tests/unit/test_schema_utils.py`

### `database/__init__.py` Exports
```python
"""Database layer for TestIO MCP server.

This module provides persistent storage using SQLite with:
- PersistentCache: Main cache interface
- Schema operations: DDL and migrations
"""

from testio_mcp.database.cache import PersistentCache
from testio_mcp.database.schema import (
    CURRENT_SCHEMA_VERSION,
    check_schema_version,
    initialize_database,
)

__all__ = [
    "PersistentCache",
    "CURRENT_SCHEMA_VERSION",
    "check_schema_version",
    "initialize_database",
]
```

### `utilities/__init__.py` Exports
```python
"""Utility functions for TestIO MCP server.

Commonly used utilities exposed at package level for convenience.
"""

# Date/time utilities (most commonly used)
from testio_mcp.utilities.date_utils import (
    format_date,
    parse_flexible_date,
)
from testio_mcp.utilities.timezone_utils import normalize_to_utc

# Schema/formatting utilities
from testio_mcp.utilities.schema_utils import format_test_dates

# Service helpers
from testio_mcp.utilities.service_helpers import get_service

__all__ = [
    # Date/time
    "format_date",
    "normalize_to_utc",
    "parse_flexible_date",
    # Schema
    "format_test_dates",
    # Services
    "get_service",
]
```

## Implementation Steps

### Phase 1: Database Directory
1. Create `src/testio_mcp/database/` directory
2. Use `git mv` to preserve history:
   ```bash
   git mv src/testio_mcp/cache.py src/testio_mcp/database/cache.py
   git mv src/testio_mcp/schema.py src/testio_mcp/database/schema.py
   ```
3. Create `database/__init__.py` with exports
4. Update imports in all affected files
5. Run tests to verify

### Phase 2: Utilities Consolidation
1. Use `git mv` to preserve history:
   ```bash
   git mv src/testio_mcp/timezone_utils.py src/testio_mcp/utilities/timezone_utils.py
   git mv src/testio_mcp/schema_utils.py src/testio_mcp/utilities/schema_utils.py
   ```
2. Update `utilities/__init__.py` with new exports
3. Update imports in all affected files
4. Run tests to verify

### Phase 3: Quality Verification
```bash
# Run all quality checks in one command
uv run ruff check --fix && uv run ruff format && uv run mypy src && uv run pre-commit run --all-files && time TESTIO_PRODUCT_ID=25043 TESTIO_PRODUCT_IDS=25043 TESTIO_TEST_ID=141290 uv run pytest -q --cov=src
```

## Benefits
1. **Improved discoverability:** Database code grouped together, utilities consolidated
2. **Consistent patterns:** Follows CLI reorganization pattern from STORY-026
3. **Reduced root clutter:** Root directory only contains top-level modules
4. **Better separation of concerns:** Clear boundaries between database, utilities, services, tools, etc.
5. **Easier onboarding:** New developers can quickly understand code organization

## Risks and Mitigation
- **Import breakage:** Use comprehensive grep to find all imports before changing
- **Test failures:** Run full test suite after each phase
- **Git history:** Use `git mv` to preserve file history for future blame/log operations

## Definition of Done
- [x] All files moved to new locations using `git mv`.
- [x] All imports updated and verified.
- [x] Application runs without import errors (`uvx testio-mcp serve`).
- [x] CLI commands work (`uvx testio-mcp sync --status`, `uvx testio-mcp problematic list`).
- [x] Quality verification passes: `uv run ruff check --fix && uv run ruff format && uv run mypy src && uv run pre-commit run --all-files && time TESTIO_PRODUCT_ID=25043 TESTIO_PRODUCT_IDS=25043 TESTIO_TEST_ID=141290 uv run pytest -q --cov=src`
- [x] Documentation updated (if CLAUDE.md references these files).
- [x] No degradation in test coverage.

---

## Dev Agent Record

### Tasks Completed
- [x] Phase 1: Created database/ directory and moved cache.py, schema.py with git mv
- [x] Phase 1: Created database/__init__.py with proper exports
- [x] Phase 1: Updated all imports in source files (~11 files)
- [x] Phase 2: Moved timezone_utils.py and schema_utils.py to utilities/
- [x] Phase 2: Updated utilities/__init__.py with new exports
- [x] Phase 2: Updated all imports for utilities files
- [x] Phase 3: Ran full quality verification (all passed)

### Debug Log
No blockers or errors encountered during implementation.

### Completion Notes
- Successfully reorganized database code into `database/` directory
- Successfully consolidated utilities in `utilities/` directory
- All tests pass: 373 passed, 18 skipped in 33.02s
- All quality checks pass: ruff (17 fixes), mypy (no issues), unit tests (251 passed)
- Git history preserved with `git mv` for all moved files

### File List
**Created:**
- `src/testio_mcp/database/__init__.py` - Database layer exports

**Moved:**
- `src/testio_mcp/cache.py` → `src/testio_mcp/database/cache.py`
- `src/testio_mcp/schema.py` → `src/testio_mcp/database/schema.py`
- `src/testio_mcp/timezone_utils.py` → `src/testio_mcp/utilities/timezone_utils.py`
- `src/testio_mcp/schema_utils.py` → `src/testio_mcp/utilities/schema_utils.py`

**Modified (imports updated):**
- `src/testio_mcp/server.py`
- `src/testio_mcp/cli/sync.py`
- `src/testio_mcp/cli/problematic.py`
- `src/testio_mcp/services/product_service.py`
- `src/testio_mcp/repositories/test_repository.py`
- `src/testio_mcp/tools/cache_tools.py`
- `src/testio_mcp/tools/generate_ebr_report_tool.py`
- `src/testio_mcp/tools/list_products_tool.py`
- `src/testio_mcp/tools/list_tests_tool.py`
- `src/testio_mcp/tools/test_status_tool.py`
- `src/testio_mcp/utilities/__init__.py`
- `tests/conftest.py`
- `tests/unit/test_persistent_cache.py`
- `tests/unit/test_date_utils.py`
- `tests/unit/test_schema_utils.py`
- `tests/integration/test_sync_integration.py`
- `tests/integration/test_get_test_status_integration.py`
- `tests/integration/test_generate_ebr_report_file_export_integration.py`
- `tests/integration/test_generate_ebr_report_integration.py`
- `tests/integration/test_list_products_integration.py`
- `tests/integration/test_list_tests_integration.py`

### Change Log
- 2025-11-20: Implemented database/ and utilities/ reorganization (STORY-028)
  - Created database/ directory with cache.py, schema.py, __init__.py
  - Moved timezone_utils.py and schema_utils.py to utilities/
  - Updated 25+ import statements across source and test files
  - All tests pass, no regressions
