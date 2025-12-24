# ADR-016: Alembic Migration Strategy

**Date:** 2025-11-24
**Status:** Accepted
**Affects:** All database schema changes going forward
**Context:** Recurring migration conflicts from baseline using `metadata.create_all()`

## Context

During STORY-038 implementation, we encountered a recurring migration conflict pattern:

1. Our baseline migration (`0965ad59eafa`) uses `SQLModel.metadata.create_all(checkfirst=True)`
2. This creates tables reflecting the **current** ORM models, not the schema at baseline creation time
3. When we add new migrations (e.g., `add_features_synced_at`), they fail with "duplicate column name" errors
4. We've been "flattening" migrations (deleting intermediate ones) as a workaround

**Root Cause:** The baseline's `metadata.create_all()` dynamically reads current ORM state, causing schema drift.

**Problem Statement:** We need a sustainable long-term migration strategy that:
- Prevents baseline/migration conflicts
- Catches schema drift in CI before it reaches main
- Works for both fresh databases and existing database upgrades

## Decision

**Adopt a single-path migration strategy with frozen baseline DDL and pytest-alembic CI protection.**

### Core Principles

1. **Single Code Path:** Always use `alembic upgrade head` for both fresh and existing databases
2. **Frozen Baseline:** Convert baseline to explicit DDL that never changes
3. **CI Protection:** Use pytest-alembic to catch ORM/migration drift automatically
4. **No `stamp head`:** Avoid `create_all() + stamp` pattern to prevent divergent code paths

### Implementation

#### 1. Freeze Baseline Migration (Next Schema Change)

Convert from dynamic `metadata.create_all()` to explicit DDL:

```python
# BEFORE (problematic - reads current ORM state)
def upgrade():
    bind = op.get_bind()
    SQLModel.metadata.create_all(bind=bind, checkfirst=True)

# AFTER (frozen - exact DDL at baseline time)
def upgrade():
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.Text(), nullable=False),
        sa.Column('last_synced', sa.DateTime(), nullable=True),
        sa.Column('features_synced_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    # ... other tables with exact DDL
```

#### 2. Add pytest-alembic to CI

Install and configure pytest-alembic for automatic schema drift detection:

```python
# tests/conftest.py (additions)
import pytest
from pytest_alembic.config import Config

@pytest.fixture
def alembic_config():
    """Configure pytest-alembic."""
    return Config()

@pytest.fixture
def alembic_engine(test_engine):
    """Use test engine for alembic tests."""
    return test_engine
```

```python
# tests/integration/test_alembic_migrations.py
import pytest
from pytest_alembic.tests import (
    test_model_definitions_match_ddl,
    test_single_head_revision,
    test_up_down_consistency,
    test_upgrade,
)

# Tests run automatically with --test-alembic flag
# Or import explicitly for pytest collection
```

#### 3. Modify env.py for pytest-alembic Compatibility

```python
# alembic/env.py (modify run_migrations_online)
def run_migrations_online():
    # Allow pytest-alembic to inject connection
    connectable = context.config.attributes.get("connection", None)

    if connectable is None:
        connectable = engine_from_config(
            context.config.get_section(context.config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    # ... rest unchanged
```

### Built-in Tests Provided by pytest-alembic

| Test | Purpose |
|------|---------|
| `test_single_head_revision` | Ensures no diverging migration branches |
| `test_upgrade` | Validates migration chain runs from base to head |
| `test_model_definitions_match_ddl` | **Key test:** Catches forgotten migrations (ORM changed, no migration) |
| `test_up_down_consistency` | Validates all downgrades succeed |

The `test_model_definitions_match_ddl` test is critical - it verifies that running `alembic revision --autogenerate` would generate an empty migration, meaning ORM and migrations are in sync.

## Rationale

### Why Single Path (Not Two-Path)?

Initial proposal suggested two paths:
- **Path A (Fresh DB):** `create_all() + alembic stamp head`
- **Path B (Existing DB):** `alembic upgrade head`

**Rejected based on Codex peer review:**
- Divergent code paths create untested scenarios
- `stamp head` bypasses data migrations, triggers, and `ALTER TABLE` logic
- If ORM changes after stamp, database misses incremental changes
- Creates maintenance burden (two paths to test and maintain)

### Why Frozen Baseline?

The dynamic `metadata.create_all()` approach:
- Reads **current** ORM models, not historical schema
- Causes "duplicate column" errors when new migrations add columns already in current ORM
- Requires manual flattening on every schema change

Frozen explicit DDL:
- Captures schema state at a specific point in time
- New migrations work correctly (they add columns not in frozen baseline)
- Standard Alembic pattern used by most production systems

### Why pytest-alembic?

**Official pytest plugin with 4 built-in tests:**
1. Catches forgotten migrations before merge
2. Catches schema drift (ORM vs migrations)
3. Validates migration chain integrity
4. Tests downgrade consistency

**Integration with CI:**
- Runs automatically with `pytest --test-alembic`
- Fails PR if migrations don't match ORM
- Prevents our exact problem from recurring

## Consequences

### Positive

- **No more flattening:** New migrations work correctly after frozen baseline
- **CI protection:** Schema drift caught automatically before merge
- **Single code path:** Same `alembic upgrade head` for all scenarios
- **Standard pattern:** Follows Alembic best practices and community patterns
- **Maintainable:** pytest-alembic is actively maintained and well-documented

### Negative

- **Migration overhead:** Fresh DBs run migration chain vs single `create_all()`
  - **Mitigation:** Negligible for <100 migrations (~100ms difference)
  - **Mitigation:** Can revisit two-path with safeguards if migration count grows significantly

- **Initial setup work:** Need to convert baseline and add pytest-alembic
  - **Mitigation:** One-time effort, documented in STORY-039

- **env.py modification:** Requires change to allow pytest-alembic connection injection
  - **Mitigation:** Standard pattern documented in pytest-alembic docs

## Alternatives Considered

### Alternative 1: Continue Flattening

Keep current baseline with `metadata.create_all()` and flatten migrations when conflicts occur.

**Rejected because:**
- Not sustainable - conflicts recur on every schema change
- Manual intervention required each time
- Risk of losing migration history
- Can't test incremental migrations properly

### Alternative 2: Two-Path with Validation

Use `create_all() + stamp head` for fresh DBs, but add schema validation before stamping.

**Rejected because:**
- Additional complexity (schema comparison code)
- Still creates divergent code paths
- Bypasses data migrations (if we add them later)
- Codex review explicitly recommended against this pattern

### Alternative 3: Schema Snapshots

Periodically generate SQL snapshots of current schema, use for fresh DBs.

**Rejected because:**
- Requires manual snapshot management
- Snapshots can drift from actual migrations
- More complex than single-path approach
- Not standard Alembic pattern

## Research Sources

| Source | Key Finding |
|--------|-------------|
| **Alembic Cookbook** | `create_all() + stamp head` valid only for brand new DBs matching ORM exactly |
| **pytest-alembic docs** | `model_definitions_match_ddl` catches ORM/migration drift |
| **Codex Peer Review** | "Collapse to single bootstrap path: `alembic upgrade head` for both fresh and existing DBs" |
| **Google Groups** | Edge case: ORM changes after stamp cause missed incremental changes |
| **Stack Overflow** | `stamp` should only be used with validated schema equality |

## Implementation Timeline

| Phase | Action | Effort |
|-------|--------|--------|
| **STORY-039** | Add pytest-alembic to dev dependencies | 5 min |
| **STORY-039** | Modify env.py for pytest-alembic compatibility | 10 min |
| **STORY-039** | Create `test_alembic_migrations.py` | 30 min |
| **STORY-039** | Convert baseline to explicit DDL | 2-4 hours |
| **STORY-039** | Add `--test-alembic` to CI pytest command | 5 min |
| **STORY-039** | Update CLAUDE.md with new migration workflow | 30 min |

## Success Metrics

**Functional:**
- [ ] `pytest --test-alembic` passes (4 built-in tests)
- [ ] New migrations can be added without "duplicate column" errors
- [ ] `alembic upgrade head` works on fresh database
- [ ] `alembic upgrade head` works on existing database

**Operational:**
- [ ] CI fails if ORM changes without migration
- [ ] No manual flattening required for schema changes
- [ ] Migration workflow documented in CLAUDE.md

## References

- **STORY-038:** Feature Sync Integration (trigger for this ADR)
- **STORY-039:** Migration Strategy Implementation (implementation story)
- **pytest-alembic:** https://pytest-alembic.readthedocs.io/
- **Alembic Cookbook:** https://alembic.sqlalchemy.org/en/latest/cookbook.html
- **Codex Peer Review:** 2025-11-24 (via clink tool)

## Decision Log

- **2025-11-24:** Migration conflict recurred during STORY-038 (features_synced_at)
- **2025-11-24:** User requested long-term solution ("can't sustain just flattening")
- **2025-11-24:** Initial two-path proposal created
- **2025-11-24:** Codex peer review identified flaws in two-path approach
- **2025-11-24:** Research validated single-path + pytest-alembic as best practice
- **2025-11-24:** **ACCEPTED** - Single-path with frozen baseline and CI protection
