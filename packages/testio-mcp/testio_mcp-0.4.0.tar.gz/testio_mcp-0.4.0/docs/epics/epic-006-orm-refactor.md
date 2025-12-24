# Epic-006: ORM Refactor (SQLModel + Alembic)

## 1. Overview
**Goal:** Transition the `testio-mcp` server's data access layer from raw SQL (using `aiosqlite`) to a modern ORM stack using **SQLModel** (SQLAlchemy + Pydantic) and **Alembic** for schema migrations.

**Motivation:**
*   **Complexity Management:** As we add new entities (Features, User Stories) and relationships, raw SQL becomes unmaintainable and error-prone.
*   **Type Safety:** SQLModel provides end-to-end type safety from database models to API responses.
*   **Schema Management:** Alembic allows for versioned, auto-generated schema migrations, replacing manual `CREATE TABLE` scripts.
*   **Maintainability:** A proper Repository pattern with an ORM reduces boilerplate and separates business logic from SQL syntax.

## 2. Scope
Refactor all existing database interactions to use SQLModel.
*   **Entities:** `Product`, `Test`, `Bug`, `SyncEvent`, `SyncMetadata`.
*   **Components:** `PersistentCache` (to be refactored), `ProductService`, `TestService`, repositories.
*   **Infrastructure:** Add `sqlmodel`, `alembic`, `greenlet` (for async SQLAlchemy).

**Stories:** 7 total
- STORY-030: ORM Infrastructure Setup
- STORY-031: Entity Modeling
- STORY-032A: Refactor BaseRepository + ProductRepository
- STORY-032B: Refactor TestRepository
- STORY-032C: Refactor BugRepository
- STORY-033: Service Integration
- STORY-034A: Baseline Migration & Startup
- STORY-034B: Cleanup & Performance Validation

## 3. Pre-Flight Checklist (3 hours)

**MUST COMPLETE BEFORE STARTING:**

### 3.1. Verify Greenlet Compatibility (1 hour)
```bash
uv pip install greenlet
uv run python -c "import greenlet; print(f'Greenlet {greenlet.version_info} works!')"
```
**Expected:** Greenlet installs and imports successfully on Python 3.12+

### 3.2. Establish Performance Baseline (2 hours)
```bash
# Benchmark list_tests 100 times
uv run python scripts/benchmark_list_tests.py
# Document p50/p95/p99 in docs/architecture/PERFORMANCE.md
```
**Regression threshold:** p95 must stay < 20ms after ORM refactor

**Status:** [x] Greenlet verified | [x] Baseline documented

## 4. Strategy
We will follow a "Replace and Verify" strategy:
1.  **Infrastructure:** Set up the ORM engine and migration framework.
2.  **Modeling:** Define SQLModel classes that mirror the *existing* database schema exactly to avoid immediate data migration issues.
3.  **Refactor:** Systematically replace raw SQL queries in the application logic with ORM operations.
4.  **Cleanup:** Remove the old `aiosqlite` direct dependencies.

## 5. Stories

### STORY-030: ORM Infrastructure Setup

**User Story:**
As a developer working on the MCP server,
I want async SQLAlchemy engine and Alembic migration infrastructure configured,
So that I can use SQLModel for type-safe database operations and versioned schema management.

**Acceptance Criteria:**
1. [ ] Dependencies added to `pyproject.toml`: `sqlmodel`, `alembic`, `greenlet`
2. [ ] `src/testio_mcp/database/engine.py` created with `create_async_engine()` and `async_session_maker`
3. [ ] `PersistentCache.initialize()` creates AsyncEngine alongside existing connection
4. [ ] Alembic initialized: `alembic init alembic` executed, `env.py` configured for async
5. [ ] Test fixtures in `tests/conftest.py` provide AsyncSession mocks
6. [ ] All repository tests updated to use AsyncSession (not aiosqlite.Connection)
7. [ ] `alembic upgrade head` runs without errors on clean database
8. [ ] Type checking passes: `mypy src/testio_mcp/database/engine.py --strict`
9. [ ] **Performance baseline documented in `docs/architecture/PERFORMANCE.md`**
10. [ ] **Baseline includes p50/p95/p99 for `list_tests` and `list_products` (cold + warm cache)**
11. [ ] **Pre-flight checklist status fields (section 3) marked complete in this epic file**

**Tasks:**
*   Add dependencies to `pyproject.toml`
*   Create `src/testio_mcp/database/engine.py` with async engine factory
*   Update `PersistentCache.initialize()` for dual-mode operation
*   Initialize Alembic and configure for async SQLite
*   Create test fixtures and update repository test setup

**Estimated Effort:** 2-3 hours

### STORY-031: Entity Modeling

**User Story:**
As a developer using SQLModel,
I want ORM models for all existing database tables,
So that I can query and manipulate data with type safety and IDE autocomplete.

**Acceptance Criteria:**
1. [ ] `src/testio_mcp/models/orm/` package created with proper `__init__.py`
2. [ ] SQLModel classes defined: `Product`, `Test`, `Bug`, `SyncEvent`, `SyncMetadata`
3. [ ] All field types match current SQLite schema (verified by comparing `schema.py`)
4. [ ] All constraints match current schema (primary keys, foreign keys, indexes)
5. [ ] Models include proper relationships (e.g., `Test.bugs` relationship)
6. [ ] Type checking passes: `mypy src/testio_mcp/models/orm/ --strict`
7. [ ] Models importable: `from testio_mcp.models.orm import Product, Test, Bug`

**Tasks:**
*   Create `src/testio_mcp/models/orm/` package structure
*   Define SQLModel classes matching current schema exactly
*   Add relationships between models where applicable
*   Validate field types and constraints against `database/schema.py`

**Estimated Effort:** 2-3 hours

### STORY-032A: Refactor BaseRepository + ProductRepository

**User Story:**
As a developer querying product data,
I want ProductRepository to use SQLModel with AsyncSession and shared base patterns,
So that I get type-safe product queries with consistent error handling across all repositories.

**Acceptance Criteria:**
1. [ ] `BaseRepository` refactored in `src/testio_mcp/repositories/base.py`
2. [ ] BaseRepository constructor updated: `__init__(self, session: AsyncSession, client: TestIOClient, customer_id: int)`
3. [ ] Shared session management patterns implemented (commit, rollback, close)
4. [ ] Common query helpers updated for SQLModel (e.g., `_execute_query()`)
5. [ ] `ProductRepository` created in `src/testio_mcp/repositories/product_repository.py`
6. [ ] ProductRepository inherits from refactored BaseRepository
7. [ ] Methods extracted from TestRepository: `get_product_info()`, `update_product_last_synced()`, `get_synced_products_info()`, `count_products()`, `delete_all_products()`
8. [ ] All queries use SQLModel syntax: `select(ProductModel).where(...)`
9. [ ] All product unit tests pass (100% success rate)
10. [ ] ProductService integration tests pass
11. [ ] Performance: `list_products()` p95 < 15ms (baseline comparison)
12. [ ] Code quality: `grep "aiosqlite.Connection" product_repository.py` returns empty
13. [ ] Code quality: `grep "aiosqlite.Connection" base.py` returns empty
14. [ ] Type checking passes: `mypy src/testio_mcp/repositories/product_repository.py --strict`
15. [ ] Type checking passes: `mypy src/testio_mcp/repositories/base.py --strict`
16. [ ] Existing repository tests updated to use AsyncSession mocks

**Tasks:**
*   Refactor `BaseRepository` constructor and shared patterns for AsyncSession
*   Create `ProductRepository` class inheriting from refactored `BaseRepository`
*   Extract product methods from `TestRepository`
*   Implement using `AsyncSession` and `select(ProductModel)` queries
*   Update unit tests to use AsyncSession mocks
*   Update `ProductService` to use new repository
*   Validate performance against baseline

**Estimated Effort:** 4-5 hours

**Note:** This story combines BaseRepository refactor with ProductRepository to deliver a demonstrable outcome (products queryable via ORM with shared base patterns).

---

### STORY-032B: Refactor TestRepository

**User Story:**
As a developer querying test data,
I want TestRepository to use SQLModel with AsyncSession,
So that I can query tests with type safety and without raw SQL strings.

**Acceptance Criteria:**
1. [ ] `TestRepository` constructor updated: `__init__(self, session: AsyncSession, ...)`
2. [ ] TestRepository inherits from refactored BaseRepository (from 032A)
3. [ ] All product-related methods removed (moved to ProductRepository in 032A)
4. [ ] All queries updated to SQLModel syntax: `select(TestModel).where(...)`
5. [ ] Insert/update methods use ORM patterns: `session.add()`, `session.commit()`
6. [ ] All test unit tests pass (100% success rate)
7. [ ] TestService integration tests pass
8. [ ] MCP tool `list_tests` works correctly
9. [ ] Performance: `list_tests()` p95 < 20ms (baseline comparison)
10. [ ] Code quality: `grep "aiosqlite.Connection" test_repository.py` returns empty
11. [ ] Type checking passes: `mypy src/testio_mcp/repositories/test_repository.py --strict`

**Tasks:**
*   Remove product methods from TestRepository
*   Update constructor to take AsyncSession and inherit from BaseRepository
*   Refactor all queries to use `select(TestModel).where(...)` syntax
*   Update insert/update to use session.add() and commit()
*   Update unit tests to use AsyncSession mocks
*   Update TestService to inject AsyncSession
*   Validate performance and MCP tools

**Estimated Effort:** 3-4 hours

**Prerequisites:** STORY-032A must be complete (provides refactored BaseRepository)

---

### STORY-032C: Refactor BugRepository

**User Story:**
As a developer querying bug data,
I want BugRepository to use SQLModel with AsyncSession,
So that bug queries are type-safe and consistent with other repositories.

**Acceptance Criteria:**
1. [ ] `BugRepository` constructor updated: `__init__(self, session: AsyncSession, ...)`
2. [ ] BugRepository inherits from refactored BaseRepository (from 032A)
3. [ ] All queries updated to SQLModel syntax: `select(BugModel).where(...)`
4. [ ] Insert/update methods use ORM patterns: `session.add()`, `session.commit()`
5. [ ] Relationship queries work: `test.bugs` loads associated bugs
6. [ ] All bug unit tests pass (100% success rate)
7. [ ] Integration test: `get_test_status()` includes bug data via ORM
8. [ ] MCP tool `generate_ebr_report` works correctly with ORM bugs
9. [ ] Performance: Bug queries maintain baseline performance
10. [ ] Code quality: `grep "aiosqlite.Connection" bug_repository.py` returns empty
11. [ ] Type checking passes: `mypy src/testio_mcp/repositories/bug_repository.py --strict`

**Tasks:**
*   Update BugRepository constructor to take AsyncSession and inherit from BaseRepository
*   Refactor all queries to use `select(BugModel).where(...)` syntax
*   Update insert/update to use session.add() and commit()
*   Test relationship loading (test.bugs)
*   Update unit tests to use AsyncSession mocks
*   Validate MCP tools that use bug data
*   Validate performance

**Estimated Effort:** 2-3 hours

**Prerequisites:** STORY-032A must be complete (provides refactored BaseRepository)

### STORY-033: Service Integration

**User Story:**
As a service layer consuming repositories,
I want ProductService and TestService to use ORM-based repositories,
So that business logic gets type-safe data access with consistent patterns.

**Acceptance Criteria:**
1. [ ] `ProductService` updated to inject and use `ProductRepository`
2. [ ] `ProductService` methods updated to work with ORM models (not raw dicts)
3. [ ] `TestService` updated to inject and use `TestRepository` and `BugRepository`
4. [ ] `TestService` methods updated to work with ORM models
5. [ ] Service layer creates AsyncSession using `get_async_session()` context manager
6. [ ] All service unit tests pass (100% success rate)
7. [ ] All MCP tools work correctly: `health_check`, `list_tests`, `get_test_status`, `generate_ebr_report`
8. [ ] Integration tests pass: full MCP request → service → repository → database flow
9. [ ] Type checking passes: `mypy src/testio_mcp/services/ --strict`

**Tasks:**
*   Update `ProductService` to inject `ProductRepository` via AsyncSession
*   Update `ProductService` methods to handle ORM Product models
*   Update `TestService` to inject `TestRepository` and `BugRepository`
*   Update `TestService` methods to handle ORM Test/Bug models
*   Update service instantiation in `server.py` to provide AsyncSession
*   Update all service unit tests
*   Validate all MCP tools end-to-end

**Estimated Effort:** 3-4 hours

### STORY-034A: Baseline Migration & Startup

**User Story:**
As a developer deploying the ORM-refactored MCP server,
I want Alembic migrations to run automatically on startup,
So that the database schema stays in sync and deployments are safe.

**Acceptance Criteria:**
1. [ ] Baseline migration generated: `alembic revision --autogenerate -m "Baseline: existing schema"`
2. [ ] Baseline migration includes all tables: `products`, `tests`, `bugs`, `sync_events`, `sync_metadata`
3. [ ] Baseline migration includes all indexes and constraints
4. [ ] Baseline migration tested: `alembic upgrade head` works on clean database
5. [ ] Baseline revision ID documented in this epic file for Epic 005 reference
6. [ ] Server lifespan handler runs migrations on startup with fail-fast behavior
7. [ ] `TESTIO_SKIP_MIGRATIONS` env flag implemented with warning log
8. [ ] SQLite JSON1 extension verified available during migration pre-check
9. [ ] Single migration head verified: `alembic heads` returns exactly one revision
10. [ ] Migration rollback tested: `alembic downgrade -1` works
11. [ ] Server starts successfully with migrations applied
12. [ ] Type checking passes: `mypy src/testio_mcp/server.py --strict` (lifespan handler)

**Tasks:**

**A. Generate Baseline Migration:****
*   Run `alembic revision --autogenerate -m "Baseline: existing schema"`.
*   Capture current state: `products`, `tests`, `bugs`, `sync_events`, `sync_metadata` tables.
*   Verify migration includes all indexes and constraints.
*   Test migration on clean database: `alembic upgrade head`.
*   **Document the baseline revision ID** in this epic file (e.g., `a1b2c3d4e5f6`).
    - Epic 005 migrations will reference this as their parent revision.
    - Enables clear migration chain tracking.

**B. Migration Chain Management:**

**Baseline Migration (Epic 006):**
- **Revision ID: `0965ad59eafa`** (STORY-034A)
- Creates the **migration head** for Epic 005
- All future Epic 005 migrations must chain from this baseline
- Migration file: `alembic/versions/0965ad59eafa_baseline_existing_schema.py`

**Epic 005 Prerequisites (enforced before any Story-035+ work):**
1. Epic 006 fully merged to main
2. Alembic head verified: `alembic current` shows baseline revision
3. Single migration head enforced: `alembic heads` returns exactly one revision
4. All repositories using AsyncSession (grep for `aiosqlite.Connection` returns empty)
5. Performance baseline met (see section 6 Success Criteria)

**Migration Conflict Prevention:**
- Epic 005 work MUST NOT start until Epic 006 baseline is merged
- If Epic 006 needs post-merge fixes, create new forward migration (don't edit baseline)
- Epic 005 authors must rebase on new head if Epic 006 adds migrations post-merge
- Before generating any Epic 005 migration:
  - Run `alembic heads` → must return single head
  - Run `alembic current` → must be at head
  - If not, rebase branch and resolve conflicts

**Rollback Order:**
```bash
# Snapshot database before downgrades
cp ~/.testio-mcp/cache.db ~/.testio-mcp/cache.db.backup
sqlite3 ~/.testio-mcp/cache.db "SELECT * FROM alembic_version;"

# Rollback Epic 005 completely (if needed)
alembic downgrade <epic-006-baseline-revision-id>

# Rollback Epic 006 (if needed)
alembic downgrade base  # Back to pre-ORM state
```

**C. Safe Startup with Migrations:**

Update `server.py` lifespan handler:

```python
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run migrations before accepting requests."""

    # Check if migrations should be skipped (dev/CI only)
    skip_migrations = os.getenv("TESTIO_SKIP_MIGRATIONS", "0") == "1"

    if skip_migrations:
        logger.warning(
            "⚠️  TESTIO_SKIP_MIGRATIONS=1: Skipping database migrations. "
            "Database schema may be out of sync!"
        )
    else:
        logger.info("Running Alembic migrations...")

        try:
            from alembic import command
            from alembic.config import Config

            alembic_cfg = Config("alembic.ini")

            # Log current state
            logger.info("Checking current migration state...")
            command.current(alembic_cfg)

            # Run migrations
            command.upgrade(alembic_cfg, "head")

            # Log final state
            logger.info("✅ Migrations complete")
            command.current(alembic_cfg)

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise RuntimeError(
                "Database migration failed - server cannot start. "
                "Check logs for details."
            ) from e

    # Initialize cache/client only after migrations succeed
    await cache.initialize()
    yield
    await cache.close()
```

**Benefits:**
- Fail-fast: Server won't start with migration errors
- Clear logging: Startup shows current → head migration path
- No mixed state: Migrations complete before any requests
- Dev escape hatch: `TESTIO_SKIP_MIGRATIONS=1` for local dev (with warning)

**Risks:**
- Startup time increases (typically <1s for SQLite)
- Failed migration blocks server (intentional - better than corrupt state)

**D. Verify JSON1 Extension:**

Add SQLite JSON1 extension check:
```python
# In cache.initialize() or migration pre-check
async with engine.begin() as conn:
    result = await conn.execute(text("SELECT json_valid('{}')"))
    if not result.scalar():
        raise RuntimeError("SQLite JSON1 extension not available")
```

**E. Remove Legacy Schema Management:**
*   Remove `src/testio_mcp/database/schema.py`:
    - Manual schema management now handled by Alembic migrations.
    - Keep schema version constant for reference in comments.

**F. Refactor PersistentCache:**
*   Refactor `PersistentCache` (src/testio_mcp/database/cache.py):
    - Update `initialize()` to use AsyncEngine and session factory.
    - Replace `self.repo` instantiation to use AsyncSession.
    - Keep PersistentCache as orchestration layer (do NOT delete).
    - Update all methods to work with ORM-backed repositories.

**Estimated Effort:** 3-4 hours

---

### STORY-034B: Cleanup & Performance Validation

**User Story:**
As a developer completing the ORM refactor,
I want legacy code removed and performance validated,
So that the codebase is clean and Epic 005 can begin with confidence.

**Acceptance Criteria:**
1. [ ] `src/testio_mcp/database/schema.py` removed (replaced by Alembic)
2. [ ] `PersistentCache` refactored to use AsyncEngine and session factory
3. [ ] All Epic 006 stories (030, 031, 032A/B/C, 033, 034A) complete and passing tests
4. [ ] Performance validation against baseline (from STORY-030):
   - `list_tests()` p95 < 20ms (20% regression tolerance)
   - `list_products()` p95 < 15ms
   - `list_tests --with-bugs` shows no N+1 query issues
5. [ ] Performance results documented in `docs/architecture/PERFORMANCE.md`
6. [ ] Code quality: `grep -r "aiosqlite.Connection" src/` returns empty
7. [ ] All migration `downgrade()` functions tested
8. [ ] Epic 006 Success Criteria (section 6) all met
9. [ ] Epic 005 Prerequisites (Epic 005 lines 47-77) verified and documented
10. [ ] Type checking passes: `mypy src/ --strict`

**Tasks:**
*   Remove `src/testio_mcp/database/schema.py`
*   Refactor `PersistentCache` to use AsyncEngine
*   Run performance benchmarks (cold + warm cache)
*   Compare results to baseline from STORY-030
*   Document performance analysis in `docs/architecture/PERFORMANCE.md`
*   Verify all Epic 006 success criteria met
*   Test all migration downgrade functions
*   Verify Epic 005 prerequisites (Alembic head, no aiosqlite, performance)
*   Final code quality sweep (mypy, grep checks)

**Estimated Effort:** 2-3 hours

**Prerequisites:** STORY-034A must be complete (provides baseline migration and startup runner)

**Note:** This story serves as the Epic 006 completion gate. Epic 005 cannot begin until all acceptance criteria pass.

---

## 6. Success Criteria (ALL must pass before Epic 005 begins)

**Code Quality:**
*   All existing tests pass (after rewriting for ORM)
*   Test coverage maintained at >90%
*   No raw SQL strings remain in repositories (except documented optimizations)
*   All repositories use `AsyncSession` and SQLModel queries
*   Services work unchanged with refactored repositories (interface compatibility maintained)
*   `grep -r "aiosqlite.Connection" src/` returns empty

**Migration Management:**
*   Database schema is managed via Alembic migrations
*   Application startup runs Alembic migrations automatically with fail-fast behavior
*   `alembic heads` returns exactly one migration head
*   Baseline revision ID documented in this epic file
*   All migration `downgrade()` functions tested

**Performance:**
*   Performance baseline documented in `docs/architecture/PERFORMANCE.md`
*   Post-ORM measurements meet targets:
    - `list_tests` p95 < 20ms (20% regression tolerance from baseline)
    - `list_tests` p99 < 30ms
    - `list_tests --with-bugs` shows no N+1 query issues (relationship test)
*   Cold start and warm cache runs both measured and documented

**Infrastructure:**
*   SQLite JSON1 extension verified available
*   Greenlet compatibility verified on target Python version
*   `TESTIO_SKIP_MIGRATIONS` env flag implemented with warning

**Documentation:**
*   `docs/architecture/PERFORMANCE.md` created with:
    - Pre-ORM baseline measurements (p50/p95/p99)
    - Post-ORM measurements
    - Regression analysis
    - Benchmark methodology
*   Migration chain strategy documented in this epic
*   Rollback procedures tested and documented

## 7. Rollback Strategy

**Simplified:** Database resyncs in ~5 minutes, no users yet.

**Per-Story Rollback:**
```bash
git revert <commit-hash>
rm ~/.testio-mcp/cache.db
uv run python -m testio_mcp sync --verbose
```

## 8. Notes from Validation

**Migration:** 5-minute resync acceptable (no complex migration needed)
**Regression Testing:** Not needed (simple schema, quick resync validates)
**Performance:** Must measure baseline before starting (see section 3.2)

**Code Rollback:**
*   Git revert to pre-ORM commit if critical bugs discovered post-merge.
*   Feature flag option: Keep raw SQL queries as comments during transition for emergency fallback.

**Schema Rollback:**
*   All Alembic migrations include `downgrade()` functions.
*   Test downgrade path before merging: `alembic downgrade -1`.
*   Backup database before running migrations in production.

**Performance Monitoring:**
*   Compare query performance before/after ORM adoption:
    - Use SQLite `EXPLAIN QUERY PLAN` to verify index usage.
    - Monitor slow query logs (queries > 100ms).
    - Regression test: `list_tests` tool should remain ~10ms.
*   If performance degrades >50%, investigate query optimization (eager loading, select_related).

**Fallback Trigger:**
*   If critical bugs or >2x performance regression, revert Epic-006 changes.
*   Document issues and re-plan ORM adoption approach.

---

## Post-Review Follow-ups (STORY-034A)

**Review Date:** 2025-11-23
**Story Status:** ✅ APPROVED (ready for DONE)

### Recommendations for STORY-034B

**Priority: Low (Enhancement Opportunities)**

1. **Migration Timeout** - Consider adding timeout to `asyncio.to_thread()` migration call
   - Rationale: Large migrations could block startup indefinitely
   - Impact: Low (baseline migration is fast, ~1-2s)
   - Suggested: Add `MIGRATION_TIMEOUT_SECONDS` config setting

2. **Cursor Cleanup Pattern** - Use async context managers in `database/utils.py`
   - Rationale: More Pythonic, ensures cleanup on exception
   - Impact: Very Low (current implementation is correct)
   - Files: `src/testio_mcp/database/utils.py`

3. **Integration Test Coverage** - Add migration failure scenario test
   - Rationale: Verify fail-fast behavior with actual error condition
   - Impact: Low (fail-fast already verified via code inspection)
   - Test: Corrupt `alembic.ini` and verify server refuses to start

4. **Index Verification** - Add index checks to integration tests
   - Rationale: Comprehensive schema verification
   - Impact: Low (indexes verified via manual testing)
   - Files: `tests/integration/test_startup_migrations.py`

### Recommendations for Epic 005

**Priority: Medium (Future Migration Quality)**

1. **Migration Testing Template** - Establish pattern for Epic 005 migrations
   - Include upgrade/downgrade tests for each migration
   - Verify data integrity across migrations
   - Test migration rollback scenarios

2. **Migration Documentation** - Add Epic 005 migration guide
   - Document baseline revision (`0965ad59eafa`) as parent
   - Explain migration chain management
   - Provide examples of common migration patterns

**Note:** All recommendations are non-blocking. Story 034A meets all acceptance criteria and is approved for DONE status.

---

**Epic Status:** ✅ COMPLETED
**Stories:** 034A, 034B, 037, 038, 039, 040 all complete
**Completed:** 2025-11-23
