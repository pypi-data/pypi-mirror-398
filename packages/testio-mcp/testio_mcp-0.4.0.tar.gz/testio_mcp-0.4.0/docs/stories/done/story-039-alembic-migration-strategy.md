---
story_id: STORY-039
epic_id: null
title: Alembic Migration Strategy Implementation
status: done
created: 2025-11-24
dependencies: []
priority: medium
parent_epic: null (Standalone Infrastructure Story)
trigger: Recurring migration conflicts discovered during STORY-038
---

## Status
🟢 **DONE** - Approved by Senior Developer Review (2025-11-24)

## Dev Agent Record

### Context Reference
- ADR: `docs/architecture/adrs/ADR-016-alembic-migration-strategy.md`
- Context File: `docs/sprint-artifacts/story-039-alembic-migration-strategy.context.xml`
- Trigger: STORY-038 migration conflict (features_synced_at duplicate column)
- Research: Codex peer review + pytest-alembic documentation + Alembic cookbook

### Debug Log
**2025-11-24 Implementation:**
1. Added pytest-alembic>=0.11.0 to dev dependencies
2. Updated env.py to support async pytest-alembic (detects AsyncEngine)
3. Added alembic_config() and alembic_engine() fixtures to conftest.py
4. Created tests/integration/test_alembic_migrations.py with 4 pytest-alembic tests
5. Converted baseline to explicit DDL (frozen at 2025-11-24)
6. All 4 pytest-alembic tests pass:
   - test_single_head_revision ✓
   - test_upgrade ✓
   - test_model_definitions_match_ddl ✓
   - test_up_down_consistency ✓
7. Updated CLAUDE.md Database Migrations section with ADR-016 reference
8. AC9 (CI) skipped - no general test workflow exists

### Completion Notes
Successfully implemented sustainable migration strategy with pytest-alembic CI protection.
Key implementation choices:
- Used file-based SQLite for alembic_engine fixture (in-memory doesn't work with NullPool)
- env.py detects AsyncEngine via isinstance() and branches appropriately
- Baseline frozen with explicit DDL matching ORM state at 2025-11-24

## Story

**As a** developer making schema changes,
**I want** a sustainable migration strategy with CI protection,
**So that** I can add new migrations without "duplicate column" conflicts and catch schema drift automatically.

## Background

**Recurring Problem:**
Our baseline migration uses `SQLModel.metadata.create_all(checkfirst=True)` which dynamically reads current ORM models. When we add new migrations for schema changes, they fail with "duplicate column name" errors because the baseline already created the columns.

**Current Workaround:**
We've been manually "flattening" migrations (deleting intermediate ones, keeping only baseline). This is not sustainable and has occurred multiple times:
- Epic-006: ORM refactor required baseline flattening
- STORY-038: `features_synced_at` column conflict required flattening

**Root Cause:**
The baseline's `metadata.create_all()` creates tables reflecting **current** ORM state, not the schema at baseline creation time.

**Solution (ADR-016):**
1. Convert baseline to explicit frozen DDL
2. Add pytest-alembic for CI schema drift detection
3. Use single `alembic upgrade head` path for all scenarios

## Problem Solved

**Before (Current State):**
```bash
# Add new column to ORM
class Product(SQLModel, table=True):
    features_synced_at: datetime | None = None  # NEW

# Generate migration
alembic revision --autogenerate -m "Add features_synced_at"
# Creates: op.add_column('products', sa.Column('features_synced_at', ...))

# Run migration on fresh DB
alembic upgrade head
# ERROR: duplicate column name: features_synced_at
# (baseline's create_all already created it from current ORM)

# Manual fix required
rm alembic/versions/xxx_add_features_synced_at.py
# Repeat for every schema change...
```

**After (STORY-039):**
```bash
# Add new column to ORM
class Product(SQLModel, table=True):
    features_synced_at: datetime | None = None  # NEW

# Generate migration
alembic revision --autogenerate -m "Add features_synced_at"
# Creates: op.add_column('products', sa.Column('features_synced_at', ...))

# Run migration on fresh DB
alembic upgrade head
# SUCCESS: baseline creates frozen schema, migration adds new column

# CI catches forgotten migrations
pytest --test-alembic
# test_model_definitions_match_ddl PASSED (ORM matches migrations)
```

## Acceptance Criteria

### AC1: Add pytest-alembic Dependency

**File:** `pyproject.toml`

**Implementation:**
```toml
[project.optional-dependencies]
dev = [
    # ... existing deps
    "pytest-alembic>=0.11.0",
]
```

**Verification:**
```bash
uv pip install -e ".[dev]"
python -c "import pytest_alembic; print(pytest_alembic.__version__)"
```

---

### AC2: Modify env.py for pytest-alembic Compatibility

**File:** `alembic/env.py`

**Why:** pytest-alembic needs to inject its own connection for testing. Without this modification, the built-in tests cannot run.

**Implementation:**
```python
def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Allow pytest-alembic to inject connection
    connectable = context.config.attributes.get("connection", None)

    if connectable is None:
        # Normal path - create engine from config
        connectable = engine_from_config(
            context.config.get_section(context.config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    # ... rest of function unchanged
```

**Verification:**
```bash
pytest --test-alembic --collect-only
# Should show 4 built-in tests without errors
```

---

### AC3: Create Alembic Test Fixtures

**File:** `tests/conftest.py` (additions)

**Implementation:**
```python
import pytest
from pytest_alembic.config import Config

@pytest.fixture
def alembic_config():
    """Configure pytest-alembic for testing migrations."""
    return Config()

@pytest.fixture
def alembic_engine():
    """Provide database engine for alembic tests.

    Uses in-memory SQLite for simplicity. For production databases,
    consider pytest-mock-resources for Docker-based testing.
    """
    from sqlalchemy import create_engine
    return create_engine("sqlite:///")
```

**Verification:**
```bash
pytest --test-alembic -v
# All 4 tests should run (may fail until baseline is frozen)
```

---

### AC4: Create Integration Test File for Alembic

**File:** `tests/integration/test_alembic_migrations.py`

**Implementation:**
```python
"""
Alembic migration consistency tests (STORY-039).

Uses pytest-alembic built-in tests to verify:
1. Single head revision (no diverging branches)
2. Upgrade path works (base to head)
3. ORM matches migrations (no forgotten migrations)
4. Downgrade consistency (all downgrades succeed)
"""

import pytest

# Import built-in tests for explicit collection
# (alternative to --test-alembic flag)
from pytest_alembic.tests import (
    test_model_definitions_match_ddl,
    test_single_head_revision,
    test_up_down_consistency,
    test_upgrade,
)

# Mark all tests as integration (require database)
pytestmark = pytest.mark.integration


# Tests are imported and run automatically by pytest
# No additional code needed - the imports above make them available
```

**Verification:**
```bash
pytest tests/integration/test_alembic_migrations.py -v
# Should show 4 tests (imported from pytest_alembic)
```

---

### AC5: Convert Baseline to Explicit DDL

**File:** `alembic/versions/0965ad59eafa_baseline_existing_schema.py`

**Why:** This is the core fix. The baseline must use explicit DDL that captures the schema at a specific point in time, not dynamic `metadata.create_all()` that reads current ORM.

**Implementation:**
Replace dynamic `metadata.create_all()` with explicit table creation:

```python
"""Baseline existing schema.

Revision ID: 0965ad59eafa
Revises:
Create Date: 2025-11-23

FROZEN DDL - Do not modify after creation.
New schema changes should be added as new migrations.
"""

from alembic import op
import sqlalchemy as sa


revision = "0965ad59eafa"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create baseline schema with explicit DDL."""
    # Products table
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("last_synced", sa.DateTime(), nullable=True),
        sa.Column("features_synced_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_customer_id", "products", ["customer_id"])

    # Tests table
    op.create_table(
        "tests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.Column("bugs_synced_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )
    op.create_index("ix_tests_customer_id", "tests", ["customer_id"])
    op.create_index("ix_tests_product_id", "tests", ["product_id"])
    op.create_index("ix_tests_status", "tests", ["status"])

    # Bugs table
    op.create_table(
        "bugs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"]),
    )
    op.create_index("ix_bugs_customer_id", "bugs", ["customer_id"])
    op.create_index("ix_bugs_test_id", "bugs", ["test_id"])

    # Features table
    op.create_table(
        "features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("section_ids", sa.Text(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )
    op.create_index("ix_features_customer_id", "features", ["customer_id"])
    op.create_index("ix_features_product_id", "features", ["product_id"])

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_customer_id", "users", ["customer_id"])

    # Sync events table
    op.create_table(
        "sync_events",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("products_synced", sa.Integer(), nullable=True),
        sa.Column("tests_synced", sa.Integer(), nullable=True),
        sa.Column("tests_refreshed", sa.Integer(), nullable=True),
        sa.Column("bugs_synced", sa.Integer(), nullable=True),
        sa.Column("features_synced", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_events_customer_id", "sync_events", ["customer_id"])
    op.create_index("ix_sync_events_event_type", "sync_events", ["event_type"])
    op.create_index("ix_sync_events_status", "sync_events", ["status"])


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_table("sync_events")
    op.drop_table("users")
    op.drop_table("features")
    op.drop_table("bugs")
    op.drop_table("tests")
    op.drop_table("products")
```

**Note:** The exact columns should match the current ORM state at time of implementation. Use `alembic revision --autogenerate` output as reference.

**Verification:**
```bash
# Delete existing database
rm ~/.testio-mcp/cache.db

# Run migrations on fresh DB
alembic upgrade head
# Should succeed without errors

# Verify schema
sqlite3 ~/.testio-mcp/cache.db ".schema"
# Should show all tables with correct columns
```

---

### AC6: Freeze Baseline Downgrade

**File:** `alembic/versions/0965ad59eafa_baseline_existing_schema.py` (downgrade function)

**Why:** Downgrade must also be explicit to match upgrade. Dynamic `metadata.drop_all()` may miss tables if ORM changes.

**Implementation:** See AC5 - downgrade function included above.

**Verification:**
```bash
alembic downgrade base
# Should drop all tables without errors

alembic upgrade head
# Should recreate all tables
```

---

### AC7: Update CLAUDE.md Migration Documentation

**File:** `CLAUDE.md`

**Implementation:** Update the "Database Migrations" section:

```markdown
## Database Migrations (ADR-016)

**Strategy:** Single-path with frozen baseline and pytest-alembic CI protection.

### Adding Schema Changes

1. **Update ORM model** (e.g., add new column)
2. **Generate migration:** `alembic revision --autogenerate -m "Add field X"`
3. **Review migration:** Ensure it only adds new changes (no baseline duplication)
4. **Run tests:** `pytest --test-alembic` (catches ORM/migration drift)
5. **Apply:** `alembic upgrade head`

### Key Rules

1. **NEVER edit the baseline migration** - it's frozen at a point in time
2. **ALWAYS run `pytest --test-alembic`** before committing migrations
3. **Use `alembic upgrade head`** for both fresh and existing databases
4. **Import new ORM models in `alembic/env.py`** for autogenerate detection

### Troubleshooting

**"duplicate column name" error:**
- Baseline is not frozen (still using `metadata.create_all()`)
- Run STORY-039 to convert baseline to explicit DDL

**`test_model_definitions_match_ddl` fails:**
- ORM changed without migration
- Run `alembic revision --autogenerate -m "Description"` to generate migration

### Reference
- ADR-016: Alembic Migration Strategy
- pytest-alembic: https://pytest-alembic.readthedocs.io/
```

**Verification:**
- CLAUDE.md updated with new migration workflow
- Section references ADR-016

---

### AC8: Verify pytest-alembic Tests Pass

**Verification:**
```bash
# Run all 4 built-in tests
pytest --test-alembic -v

# Expected output:
# test_single_head_revision PASSED
# test_upgrade PASSED
# test_model_definitions_match_ddl PASSED
# test_up_down_consistency PASSED
```

**All 4 tests must pass before story is complete.**

---

### AC9: Add pytest-alembic to CI (Optional - If CI Exists)

**File:** `.github/workflows/test.yml` or equivalent

**Implementation:**
```yaml
- name: Run tests with Alembic checks
  run: pytest --test-alembic
```

**Verification:**
- CI pipeline includes `--test-alembic` flag
- PR fails if ORM doesn't match migrations

---

## Technical Notes

### pytest-alembic Built-in Tests

| Test | Purpose | Catches |
|------|---------|---------|
| `test_single_head_revision` | No diverging branches | Merge conflicts that create multiple heads |
| `test_upgrade` | Migration chain works | Broken migrations, syntax errors |
| `test_model_definitions_match_ddl` | ORM matches migrations | **Forgotten migrations** (our problem) |
| `test_up_down_consistency` | Downgrades work | Broken downgrade scripts |

### Why Single Path?

Codex peer review identified that two-path approaches (`create_all + stamp` vs `upgrade head`) create:
- Untested code paths
- Risk of bypassing data migrations
- Schema drift if ORM changes after stamp

Single path (`alembic upgrade head` always) is simpler and safer.

### Migration Performance

For <100 migrations, the overhead of running migration chain vs `create_all()` is negligible (~100ms). If migration count grows significantly (1000+), revisit with proper safeguards.

## Out of Scope

- Data migrations (no existing production data)
- Multi-tenant schema separation
- Migration squashing (not needed for <100 migrations)
- PostgreSQL-specific features (SQLite only for MVP)

## Definition of Done

- [ ] pytest-alembic added to dev dependencies
- [ ] env.py modified for pytest-alembic compatibility
- [ ] Alembic fixtures added to conftest.py
- [ ] Integration test file created
- [ ] Baseline converted to explicit DDL
- [ ] All 4 pytest-alembic tests pass
- [ ] CLAUDE.md updated with new migration workflow
- [ ] Fresh database creation works (`alembic upgrade head`)
- [ ] Existing database upgrade works (`alembic upgrade head`)

## File List

### Modified Files
| File | Change Type | Description |
|------|-------------|-------------|
| `pyproject.toml` | Modified | Added pytest-alembic>=0.11.0 to dev dependencies |
| `alembic/env.py` | Modified | Added AsyncEngine detection for pytest-alembic support |
| `alembic/versions/0965ad59eafa_baseline_existing_schema.py` | Rewritten | Converted from dynamic metadata.create_all() to frozen explicit DDL |
| `tests/conftest.py` | Modified | Added alembic_config() and alembic_engine() fixtures |
| `CLAUDE.md` | Modified | Updated Database Migrations section with ADR-016 reference |

### New Files
| File | Description |
|------|-------------|
| `tests/integration/test_alembic_migrations.py` | pytest-alembic built-in test imports |
| `docs/architecture/adrs/ADR-016-alembic-migration-strategy.md` | ADR documenting migration strategy decision |
| `docs/sprint-artifacts/story-039-alembic-migration-strategy.context.xml` | Story context file |

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-24 | Story created (triggered by STORY-038 migration conflict) | Claude |
| 2025-11-24 | AC1: Added pytest-alembic dependency | Claude |
| 2025-11-24 | AC2: Modified env.py for async pytest-alembic support | Claude |
| 2025-11-24 | AC3: Added alembic fixtures to conftest.py | Claude |
| 2025-11-24 | AC4: Created integration test file | Claude |
| 2025-11-24 | AC5-AC6: Converted baseline to frozen DDL | Claude |
| 2025-11-24 | AC7: Updated CLAUDE.md documentation | Claude |
| 2025-11-24 | AC8: Verified all 4 pytest-alembic tests pass | Claude |
| 2025-11-24 | Story marked review (AC9 skipped - no CI workflow) | Claude |
| 2025-11-24 | Senior Developer Review: APPROVED - all ACs verified | leoric (AI)

## References

- **ADR-016:** Alembic Migration Strategy (decision rationale)
- **STORY-038:** Feature Sync Integration (trigger)
- **pytest-alembic docs:** https://pytest-alembic.readthedocs.io/
- **Alembic cookbook:** https://alembic.sqlalchemy.org/en/latest/cookbook.html

---

## Senior Developer Review (AI)

### Review Metadata
- **Reviewer:** leoric (AI-assisted)
- **Date:** 2025-11-24
- **Outcome:** ✅ **APPROVE**

### Summary

STORY-039 delivers a comprehensive, well-implemented solution to the recurring Alembic migration conflict problem. The implementation follows ADR-016 exactly as specified, with explicit frozen DDL in the baseline migration, pytest-alembic CI protection, and thorough documentation. All acceptance criteria are fully satisfied with evidence-backed verification.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | Add pytest-alembic Dependency | ✅ IMPLEMENTED | `pyproject.toml:62` |
| AC2 | Modify env.py for pytest-alembic | ✅ IMPLEMENTED | `alembic/env.py:102-136` |
| AC3 | Create Alembic Test Fixtures | ✅ IMPLEMENTED | `tests/conftest.py:338-376` |
| AC4 | Create Integration Test File | ✅ IMPLEMENTED | `tests/integration/test_alembic_migrations.py:1-38` |
| AC5 | Convert Baseline to Explicit DDL | ✅ IMPLEMENTED | `alembic/versions/0965ad59eafa...py:37-169` |
| AC6 | Freeze Baseline Downgrade | ✅ IMPLEMENTED | `alembic/versions/0965ad59eafa...py:171-184` |
| AC7 | Update CLAUDE.md Documentation | ✅ IMPLEMENTED | `CLAUDE.md:531-587` |
| AC8 | All 4 pytest-alembic Tests Pass | ✅ VERIFIED | Live execution: 4 passed in 0.16s |
| AC9 | Add to CI (Optional) | ⏭️ SKIPPED | Correctly skipped - no CI workflow exists |

**Summary: 8 of 8 mandatory acceptance criteria fully implemented**

### Task Completion Validation

| Task | Verified | Evidence |
|------|----------|----------|
| pytest-alembic added to dev dependencies | ✅ | `pyproject.toml:62` |
| env.py modified for pytest-alembic | ✅ | AsyncEngine detection at line 130 |
| Alembic fixtures added to conftest.py | ✅ | `alembic_config()` + `alembic_engine()` |
| Integration test file created | ✅ | File exists with 4 test imports |
| Baseline converted to explicit DDL | ✅ | 7 tables with explicit `op.create_table()` |
| All 4 pytest-alembic tests pass | ✅ | Live verified: 4 passed |
| CLAUDE.md updated | ✅ | Full "Database Migrations (ADR-016)" section |
| Fresh database creation works | ✅ | Live: `alembic upgrade head` succeeds |
| Existing database upgrade works | ✅ | Live: downgrade + re-upgrade works |

**Summary: 9 of 9 completed tasks verified, 0 questionable, 0 falsely marked complete**

### Test Coverage and Gaps

- **Migration Tests:** 4 pytest-alembic built-in tests cover critical migration scenarios
  - `test_single_head_revision` - No diverging branches
  - `test_upgrade` - Migration chain works
  - `test_model_definitions_match_ddl` - ORM matches migrations (key drift detector)
  - `test_up_down_consistency` - Downgrades work
- **No gaps identified:** The 4 built-in tests provide comprehensive CI protection

### Architectural Alignment

- ✅ Follows ADR-016 single-path strategy exactly
- ✅ Frozen baseline DDL prevents future "duplicate column" conflicts
- ✅ AsyncEngine detection in env.py handles both CLI and programmatic modes
- ✅ File-based SQLite for alembic_engine fixture (NullPool requires file-based)

### Security Notes

- No security concerns identified
- No secrets exposed in migration files
- Database operations properly isolated

### Best-Practices and References

- **pytest-alembic async pattern:** https://pytest-alembic.readthedocs.io/en/latest/asyncio.html
- **Alembic frozen baseline:** Standard pattern per Alembic cookbook
- **env.py connection injection:** Recommended pytest-alembic integration pattern

### Code Quality Notes

- ✅ All files pass `ruff check` (linting)
- ✅ All files pass `mypy` (type checking)
- ✅ Well-documented with story references (STORY-039, ADR-016)
- ✅ Follows existing conftest.py patterns for fixture organization

### Action Items

**Advisory Notes (no action required):**
- Note: Pre-existing warnings in `test_hybrid_api_integration.py` about connection cleanup are unrelated to this story
- Note: Pre-existing `session.execute()` deprecation warnings in `test_engine.py` are documented in CLAUDE.md

**No code changes required - implementation is complete and correct**

### Recommendation

**✅ APPROVE** - This story is ready to be marked done. The implementation is thorough, well-tested, and properly documented. The frozen baseline approach will prevent the recurring migration conflicts that triggered this story.
