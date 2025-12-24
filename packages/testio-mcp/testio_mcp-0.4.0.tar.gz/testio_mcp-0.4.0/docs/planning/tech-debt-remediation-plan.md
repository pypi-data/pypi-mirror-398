# Tech Debt Remediation Plan

**Created:** 2025-12-03
**Author:** Tech Debt Audit (Claude + Gemini + Codex)
**Updated:** 2025-12-04 (TD-001 Complete)
**Status:** In Progress

---

## Executive Summary

A comprehensive tech debt audit identified **13 actionable items** across 5 categories. This document provides a prioritized remediation plan with implementation guidance, effort estimates, and dependency mapping.

### Key Findings

| Priority | Count | Categories |
|----------|-------|------------|
| Critical | 2 | Resource leaks, architectural debt |
| High | 3 | Data patterns, testing infrastructure, error handling |
| Medium | 4 | Code organization, typing, inheritance |
| Low | 4 | Configuration, edge cases |

### Recommended Timeline

- **Sprint 1:** Critical items (session leak, service factory)
- **Sprint 2:** High-priority items (Epic 013, VCRpy, exception handling)
- **Sprint 3:** Medium-priority items (god class decomposition, typing)
- **Ongoing:** Low-priority items as time permits

---

## Tech Debt Inventory

### TD-001: AsyncSession Resource Leak [CRITICAL] ✅ COMPLETE

**Status:** ✅ Completed 2025-12-04
**Commit:** `fbf974d` - "refactor: eliminate AsyncSession resource leaks (TD-001)"

**Location:** `src/testio_mcp/utilities/service_helpers.py:71-74`

**Problem:**
`get_service()` creates AsyncSession instances that are never closed, relying on garbage collection. This causes SQLAlchemy warnings and potential connection pool exhaustion under load.

```python
# Before (leaky)
session = cache.async_session_maker()  # Never closed!
```

**Root Cause:**
`get_service()` was the original pattern; `get_service_context()` was added later but not universally adopted.

**Solution Implemented:**
1. ~~Deprecate `get_service()` with warnings~~ → **Removed entirely** (no users, cleaner)
2. Migrated sync_data MCP tool to `get_service_context()` async context manager
3. Migrated 5 REST API endpoints to `get_service_context_from_server_context()`
4. Removed deprecated functions: `get_service()`, `get_service_from_server_context()`, `_build_service()`

**Acceptance Criteria:**
- [x] All MCP tools use `async with get_service_context(...)` (16/16)
- [x] All REST endpoints use `async with get_service_context_from_server_context(...)` (5/5)
- [x] No SQLAlchemy "garbage collector" warnings in logs
- [x] Integration tests verify session cleanup (5 tests passing)
- [x] Deprecated code removed (~240 lines)

**Results:**
- Zero session leaks (was: 6 across MCP + REST)
- 854 unit tests passing
- 5 integration tests passing
- Net code reduction: -137 lines
- All pre-commit hooks passing

**Effort:** Actual: 2 hours (estimated: 2.5 hours)
**Risk:** Low (changes isolated, fully tested)
**Dependencies:** None

---

### TD-002: Service Instantiation Boilerplate [CRITICAL] ✅ COMPLETE

**Status:** ✅ Completed 2025-12-04
**Commit:** `315cdcb` - "refactor: eliminate service instantiation boilerplate (TD-002)"
**Implementation Details:** See [tech-debt-critical-sprint.md](../sprint-artifacts/archive/tech-debt-critical-sprint.md)

**Location:** `src/testio_mcp/utilities/service_helpers.py:23-145, 148-360` (before refactor)

**Problem:**
8+ `if/elif` blocks check service names as strings. Every new service requires:
- Manual wiring in `_build_service()`
- Duplicate wiring in `get_service_context()`
- Duplicate wiring in `get_service_context_from_server_context()`

```python
# Current (repetitive, error-prone)
service_name = service_class.__name__
if service_name in ("TestService", "MultiTestReportService"):
    # 20 lines of setup...
elif service_name == "ProductService":
    # Different setup...
elif service_name == "BugService":
    # Yet another setup...
# ... 8 more branches
```

**Solution:**
Registry-based factory pattern:

```python
from dataclasses import dataclass
from typing import Callable

@dataclass
class ServiceBuilder:
    """Declarative service configuration."""
    needs_session: bool
    repo_factories: list[Callable[[AsyncSession, TestIOClient, int], Any]]
    extra_kwargs: dict[str, str] = field(default_factory=dict)

SERVICE_REGISTRY: dict[type[BaseService], ServiceBuilder] = {
    TestService: ServiceBuilder(
        needs_session=True,
        repo_factories=[UserRepository, TestRepository, BugRepository, ProductRepository],
    ),
    ProductService: ServiceBuilder(
        needs_session=False,
        extra_kwargs={"session_factory": "cache.async_session_maker"},
    ),
    # ... declarative config for all services
}

async def build_service[T: BaseService](
    service_class: type[T],
    server_ctx: ServerContext
) -> AsyncIterator[T]:
    """Generic service builder - one implementation for all services."""
    builder = SERVICE_REGISTRY[service_class]
    session = None
    try:
        if builder.needs_session:
            session = server_ctx["cache"].async_session_maker()
        repos = [factory(session, client, customer_id) for factory in builder.repo_factories]
        yield service_class(*repos, **resolve_kwargs(builder.extra_kwargs, server_ctx))
    finally:
        if session:
            await session.close()
```

**Acceptance Criteria:**
- [ ] Single `build_service()` function handles all service types
- [ ] Adding a new service requires only registry entry
- [ ] Session lifecycle centralized in one place
- [ ] Type-safe constructor validation (fail fast if required dep missing)

**Solution Implemented:**
Registry-based factory pattern with lazy imports to avoid circular dependencies:

```python
# src/testio_mcp/utilities/service_registry.py
SERVICE_REGISTRY = {
    TestService: ServiceConfig(
        needs_session=True,
        factory=_build_test_service,  # Explicit factory function
    ),
    DiagnosticsService: ServiceConfig(
        needs_session=False,
        factory=lambda s, c, cache, cid: DiagnosticsService(client=c, cache=cache),
    ),
    # ... 11 services total
}

# Simplified helper functions
async def get_service_context(ctx, service_class):
    client = server_ctx["testio_client"]
    cache = server_ctx["cache"]
    async with build_service(service_class, client, cache) as service:
        yield service  # Was ~160 lines, now ~15 lines
```

**Acceptance Criteria:**
- [x] Single `build_service()` function handles all service types
- [x] Adding a new service requires only registry entry
- [x] Session lifecycle centralized in one place
- [x] Type-safe constructor validation (fail fast if required dep missing)
- [x] Lazy imports to avoid circular dependencies

**Results:**
- `get_service_context()`: ~160 lines → ~15 lines (-91%)
- `get_service_context_from_server_context()`: ~130 lines → ~15 lines (-88%)
- if/elif blocks: 21 → 0
- 863 unit tests passing
- 9 new registry tests added
- Fail-fast on unregistered services (prevents silent fallback bugs)

**Effort:** Actual: 3 hours (estimated: 2-3 days)
**Risk:** Medium (touches all service instantiation)
**Dependencies:** TD-001 (combine session cleanup pattern)

---

### TD-003: Repository Read Pattern Standardization [HIGH]

**Location:** `src/testio_mcp/repositories/*.py` (9 JSON parsing locations)

**Problem:**
Repositories mix patterns for reading data:
1. Parse full JSON blob from `raw_data`/`data` column
2. Override specific fields with denormalized columns
3. Return merged dict

This causes:
- Stale data leakage (only some fields overridden)
- JSON parsing overhead on every read
- Field mapping bugs (`created_at` vs `reported_at`)

**Current Pattern (Anti-pattern):**
```python
async def get_bugs(self, test_id: int) -> list[dict]:
    bugs_orm = await self._query_bugs(test_id)
    for bug_orm in bugs_orm:
        bug_dict = json.loads(bug_orm.raw_data)  # Parse full JSON
        bug_dict["status"] = bug_orm.status       # Override some
        bug_dict["known"] = bug_orm.known         # Override some
        # Other fields NOT overridden - stale data risk!
        bugs.append(bug_dict)
    return bugs
```

**Solution:**
Column-only reads by default with opt-in detail methods:

```python
# ORM Model with deferred JSON column
class Bug(SQLModel, table=True):
    raw_data: str = Field(sa_column=deferred(Column(Text)))  # Lazy load

# Repository with column-only reads
async def get_bugs(self, test_id: int) -> list[dict]:
    """Returns bug dicts built from columns only."""
    bugs_orm = await self._query_bugs(test_id)
    return [self._bug_to_dict(bug) for bug in bugs_orm]

def _bug_to_dict(self, bug: Bug) -> dict:
    """Convert ORM to dict using columns only."""
    return {
        "id": bug.id,
        "title": bug.title,
        "severity": bug.severity,
        "status": bug.status,
        "known": bug.known,
        "reported_at": bug.reported_at,
        # All denormalized columns - single source of truth
    }

async def get_bugs_with_details(self, test_id: int) -> list[dict]:
    """Opt-in: Returns bugs with nested data (devices, reproductions)."""
    # Uses undefer(Bug.raw_data) for nested fields
```

**Acceptance Criteria:**
- [ ] `deferred()` applied to `raw_data`/`data` columns in ORM
- [ ] Default reads don't include JSON column in SQL
- [ ] All denormalized columns included in output
- [ ] `*_with_details()` methods for opt-in nested data
- [ ] Data equivalence tests verify output matches

**Effort:** Medium (5 stories in Epic 013)
**Risk:** Medium (affects all read paths)
**Dependencies:** None
**Reference:** `docs/epics/epic-013-repository-read-standardization.md`

---

### TD-004: Test Infrastructure - VCRpy Integration [HIGH]

**Location:** `tests/conftest.py`, `tests/integration/`

**Problem:**
- 18 integration tests skipped due to missing API credentials
- Tests depend on live API responses (non-deterministic)
- Hardcoded product IDs (Canva, RemoveBG, Panera)
- No HTTP response recording

**Current Pattern:**
```python
@pytest.mark.skipif(
    settings.TESTIO_CUSTOMER_API_TOKEN == "test_token_placeholder",
    reason="Requires TESTIO_CUSTOMER_API_TOKEN environment variable",
)
async def test_list_products_with_real_api():
    # Calls real API - skipped in CI
```

**Solution:**
1. **VCRpy via pytest-recording** - Record real API interactions, replay deterministically
2. **Factory-Boy** - Generate deterministic database fixtures
3. **Keep file-based SQLite** - In-memory has async connection issues

```python
# New pattern with VCRpy
@pytest.mark.vcr()  # Auto-records on first run, replays thereafter
async def test_list_products_with_recorded_api():
    # Uses recorded cassette - runs in CI without credentials
```

**Implementation Steps:**

1. Add dependencies:
   ```toml
   [project.optional-dependencies]
   dev = [
       "pytest-recording>=0.13.0",
       "vcrpy>=6.0.0",
       "factory-boy>=3.3.0",
       # ... existing deps
   ]
   ```

2. Configure VCR in `conftest.py`:
   ```python
   @pytest.fixture(scope="module")
   def vcr_config():
       return {
           "filter_headers": ["Authorization"],
           "record_mode": "once",
           "cassette_library_dir": "tests/cassettes",
       }
   ```

3. Create model factories:
   ```python
   # tests/factories.py
   from factory import Factory, Faker
   from testio_mcp.models.orm import Test, Bug, Product

   class ProductFactory(Factory):
       class Meta:
           model = Product
       id = Faker("random_int", min=1, max=100000)
       title = Faker("company")
       product_type = Faker("random_element", elements=["website", "mobile_app_ios"])
   ```

4. Convert skipped tests to VCR tests:
   ```python
   # Before
   @pytest.mark.skipif(not has_token, reason="Requires API token")
   async def test_feature_sync(): ...

   # After
   @pytest.mark.vcr()
   async def test_feature_sync(): ...
   ```

**Acceptance Criteria:**
- [ ] pytest-recording and vcrpy installed
- [ ] VCR config in conftest.py with header filtering
- [ ] Cassettes directory with recorded API responses
- [ ] Factory-Boy factories for all ORM models
- [ ] Previously-skipped tests now run in CI
- [ ] No hardcoded product IDs in tests

**Effort:** Medium-High (infrastructure change)
**Risk:** Low (additive, doesn't break existing tests)
**Dependencies:** None

---

### TD-005: Broad Exception Handling [HIGH]

**Location:** 26 instances across services

| File | Count | Example Lines |
|------|-------|---------------|
| `sync_service.py` | 12 | 287, 304, 370, 382, 456, 463, 562, 631, 636, 810, 943, 977 |
| `product_service.py` | 2 | 118, 170 |
| `test_service.py` | 2 | 132, 657 |
| `analytics_service.py` | 1 | 531 |
| `search_service.py` | 1 | 141 |

**Problem:**
`except Exception` swallows errors, masks failures, and can return stale/partial data without indication.

```python
# Current (problematic)
try:
    result = await self.repo.fetch_data()
except Exception as e:
    logger.error(f"Error: {e}")
    return cached_fallback  # Caller doesn't know this is degraded!
```

**Solution:**
Specific exception groups with domain exceptions:

```python
# Define exception hierarchy
class TestIOError(Exception): pass
class APIError(TestIOError): pass
class DatabaseError(TestIOError): pass
class ValidationError(TestIOError): pass

# Handle specifically
try:
    result = await self.repo.fetch_data()
except httpx.HTTPStatusError as e:
    raise APIError(f"API returned {e.response.status_code}") from e
except sqlalchemy.exc.SQLAlchemyError as e:
    raise DatabaseError("Database operation failed") from e
except ValidationError:
    raise  # Let validation errors propagate
except Exception as e:
    # Only catch truly unexpected errors, log with full context
    logger.exception(f"Unexpected error in {self.__class__.__name__}")
    raise TestIOError("Internal error") from e
```

**Acceptance Criteria:**
- [ ] Exception hierarchy defined in `exceptions.py`
- [ ] All 26 broad handlers reviewed and replaced
- [ ] Degraded-mode flag in responses when falling back
- [ ] Error messages include actionable context
- [ ] Tests verify specific exceptions are raised

**Effort:** Medium (2-3 days)
**Risk:** Medium (changes error behavior)
**Dependencies:** None

---

### TD-006: God Class - cache.py [MEDIUM]

**Location:** `src/testio_mcp/database/cache.py` (1,518 LOC, 47 methods)

**Problem:**
Single class mixes multiple concerns:
- Engine/connection setup
- Lock management
- Sync event logging
- Repository initialization
- Query APIs
- Stats collection

**Solution:**
Split by responsibility with facade to preserve API:

```
src/testio_mcp/database/
├── cache.py           # Facade (preserved API)
├── engine.py          # Engine setup, connection management
├── locks.py           # Per-entity refresh locks
├── sync_events.py     # Sync event logging/querying
├── session.py         # Session factory, lifecycle
└── stats.py           # Database statistics
```

**Acceptance Criteria:**
- [ ] Each module < 300 LOC
- [ ] Single responsibility per module
- [ ] `cache.py` facade preserves existing imports
- [ ] Focused tests per module
- [ ] No circular imports

**Effort:** High (1 week)
**Risk:** Medium (touches core infrastructure)
**Dependencies:** TD-001 (session management patterns)

---

### TD-007: Type Ignore Comments (117 instances) [MEDIUM]

**Distribution:**
- `analytics_service.py` - 15
- `query_builder.py` - 10
- `service_helpers.py` - 21
- Various repositories - 22
- Others - 49

**Root Causes:**
1. SQLAlchemy/SQLModel typing gaps (`.in_()`, `.case()`, `select()`)
2. `client=None` in services that don't need API client
3. Optional session attributes (`AsyncSession | None`)
4. Cast operations for type narrowing

**Solution:**
Phased approach:

**Phase 1: Add stubs/plugins**
```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
    "sqlalchemy[mypy]>=2.0.0",  # SQLAlchemy mypy plugin
]

[tool.mypy]
plugins = ["sqlalchemy.ext.mypy.plugin"]
```

**Phase 2: Split BaseRepository**
```python
# Before
class BaseRepository:
    def __init__(self, session: AsyncSession | None = None): ...

# After
class OrmRepository:
    """Repository with required session."""
    def __init__(self, session: AsyncSession): ...

class LegacyRepository:
    """Repository without session (e.g., API-only)."""
    pass
```

**Phase 3: Helper functions for type narrowing**
```python
def require_session(self) -> AsyncSession:
    """Narrow session type, fail fast if None."""
    if self.session is None:
        raise RuntimeError("Session required for this operation")
    return self.session
```

**Phase 4: Targeted stubs**
```python
# typings/sqlmodel/__init__.pyi
from typing import TypeVar, overload
from sqlalchemy.sql import Select

T = TypeVar("T")

@overload
def select(__entity: type[T]) -> Select[tuple[T]]: ...
```

**Acceptance Criteria:**
- [ ] SQLAlchemy mypy plugin enabled
- [ ] BaseRepository split into typed variants
- [ ] Helper functions eliminate union-attr ignores
- [ ] Type ignores reduced by 50%+
- [ ] `warn_unused_ignores` catches stale ignores

**Effort:** Medium (ongoing)
**Risk:** Low (gradual improvement)
**Dependencies:** None

---

### TD-008: BaseService Inheritance Mismatch [MEDIUM]

**Location:** `src/testio_mcp/services/*.py`

**Problem:**
Services that don't need API client still inherit from `BaseService`:

```python
class UserService(BaseService):
    def __init__(self, user_repo):
        super().__init__(client=None, cache=None)  # type: ignore
```

**Affected Services:**
- `UserService`
- `FeatureService`
- `SearchService`
- `UserStoryService`

**Solution:**
Create service hierarchy:

```python
class ServiceBase(ABC):
    """Base for all services - no dependencies required."""
    pass

class ApiService(ServiceBase):
    """Service that needs API client."""
    def __init__(self, client: TestIOClient, cache: PersistentCache):
        self.client = client
        self.cache = cache

class RepositoryService(ServiceBase):
    """Service that only needs repositories."""
    pass

# Usage
class UserService(RepositoryService):
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo  # No client needed!

class TestService(ApiService):
    def __init__(self, client, test_repo, bug_repo, product_repo):
        super().__init__(client, cache)
        # ...
```

**Acceptance Criteria:**
- [ ] Service hierarchy defined
- [ ] Affected services updated
- [ ] No `client=None` patterns
- [ ] Type ignores for inheritance removed

**Effort:** Low-Medium (1-2 days)
**Risk:** Low (internal refactor)
**Dependencies:** TD-002 (registry needs to handle different bases)

---

### TD-009: Large Repository Files [MEDIUM]

**Location:**
- `test_repository.py` - 1,555 LOC
- `bug_repository.py` - 1,159 LOC

**Problem:**
Files mix concerns:
- CRUD operations
- Sync logic
- Staleness checks
- Batch operations
- Metrics/aggregation

**Solution:**
Split by concern:

```
src/testio_mcp/repositories/
├── test/
│   ├── __init__.py      # Public API
│   ├── queries.py       # Read operations
│   ├── mutations.py     # Write operations
│   ├── sync.py          # Sync logic
│   └── metrics.py       # Aggregations
├── bug/
│   ├── __init__.py
│   ├── queries.py
│   ├── mutations.py
│   └── sync.py
└── ...
```

**Acceptance Criteria:**
- [ ] Each module < 400 LOC
- [ ] Clear separation of concerns
- [ ] Public API preserved via `__init__.py`
- [ ] Focused tests per module

**Effort:** Medium-High
**Risk:** Medium (touches core data access)
**Dependencies:** TD-003 (do with column-only refactor)

---

### TD-010: Hardcoded Timeouts [LOW]

**Location:**
- `config.py:HTTP_TIMEOUT_SECONDS = 90.0`
- `sync_service.py:LOCK_TIMEOUT_SECONDS = 30.0`

**Solution:**
Make configurable via environment:

```python
# config.py
HTTP_TIMEOUT_SECONDS: float = Field(default=90.0, env="TESTIO_HTTP_TIMEOUT")
LOCK_TIMEOUT_SECONDS: float = Field(default=30.0, env="TESTIO_LOCK_TIMEOUT")
```

**Effort:** Low
**Dependencies:** None

---

### TD-011: Rejection Rate Shows 0% Not N/A [LOW]

**Location:** `get_product_quality_report` tool

**Problem:**
When a test has 0 bugs, rejection rate shows `0%` instead of `N/A`, which is misleading.

**Solution:**
Return `null` or `"N/A"` when `total_bugs == 0`.

**Effort:** Low
**Dependencies:** None

---

### TD-012: datetime.now() Without UTC [LOW]

**Location:** Test fixtures

**Problem:**
Using `datetime.now()` instead of `datetime.now(UTC)` can cause timezone issues.

**Solution:**
Replace with `datetime.now(UTC)` or `datetime.utcnow()`.

**Effort:** Low
**Dependencies:** None

---

### TD-013: Missing Deprecation Warnings [LOW]

**Location:** `get_service()`, `get_service_from_server_context()`

**Problem:**
Deprecated functions don't emit warnings.

**Solution:**
Add `warnings.warn()` with `DeprecationWarning`.

**Effort:** Low
**Dependencies:** TD-001

---

## Dependency Graph

```
TD-001 (Session Leak) ─────────────────────┐
         │                                 │
         ├──────────────┐                  │
         │              │                  │
         ▼              ▼                  ▼
TD-002 (Registry)  TD-006 (Cache Split)  TD-013 (Warnings)
         │
         ▼
TD-008 (Service Hierarchy)

TD-003 (Column-Only) ──────► TD-009 (Repo Split)

TD-004 (VCRpy) ────────────► (Independent)

TD-005 (Exceptions) ───────► (Independent)

TD-007 (Type Ignores) ─────► (Independent, ongoing)
```

---

## Implementation Roadmap

### Sprint 1: Critical Foundation (Week 1-2)

| ID | Item | Owner | Est. |
|----|------|-------|------|
| TD-001 | Deprecate `get_service()`, migrate to context manager | - | 2d |
| TD-013 | Add deprecation warnings | - | 0.5d |
| TD-002 | Service registry factory | - | 3d |

**Milestone:** All MCP tools use `get_service_context()`, no session leak warnings

### Sprint 2: Data & Testing (Week 3-4)

| ID | Item | Owner | Est. |
|----|------|-------|------|
| TD-003 | Epic 013 stories (STORY-076 → STORY-080) | - | 5d |
| TD-004 | VCRpy + pytest-recording infrastructure | - | 3d |
| TD-005 | Exception handling cleanup | - | 2d |

**Milestone:** Column-only reads, VCR cassettes, specific exception handling

### Sprint 3: Code Organization (Week 5-6)

| ID | Item | Owner | Est. |
|----|------|-------|------|
| TD-006 | cache.py decomposition | - | 5d |
| TD-008 | Service hierarchy refactor | - | 2d |
| TD-009 | Repository file splitting | - | 3d |

**Milestone:** Smaller, focused modules

### Ongoing: Quality Improvements

| ID | Item | Owner | Est. |
|----|------|-------|------|
| TD-007 | Type ignore reduction | - | Ongoing |
| TD-010 | Configuration consolidation | - | 0.5d |
| TD-011 | Rejection rate fix | - | 0.5d |
| TD-012 | UTC datetime fix | - | 0.5d |

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| SQLAlchemy GC warnings | Present | Zero | Log monitoring |
| Type ignore comments | 117 | <50 | `grep -c "type: ignore"` |
| Skipped tests | 18 | 0 | `pytest --collect-only` |
| Largest file (LOC) | 1,555 | <500 | `wc -l` |
| Broad exception handlers | 26 | 0 | `grep -c "except Exception"` |
| Service wiring branches | 8 | 1 | Code review |

---

## References

- [Epic 013: Repository Read Pattern Standardization](../epics/epic-013-repository-read-standardization.md)
- [Future Enhancements](./future-enhancements.md)
- [MCP Usability Feedback](./mcp-usability-feedback.md)
- [ADR-017: Read-Through Cache Strategy](../architecture/adrs/ADR-017-read-through-cache-strategy.md)

---

## Appendix: AI Consultation Summary

### Gemini Recommendations
1. **Repository patterns:** Use `deferred()` on JSON columns, column-only reads by default
2. **Test database:** Use pytest-recording (VCRpy wrapper), keep file-based SQLite, use Factory-Boy
3. **AsyncSession:** Deprecate `get_service()`, enforce `get_service_context()`, use FastAPI Depends pattern

### Codex Recommendations
1. **Service wiring:** Registry-based factory instead of `if/elif` ladder
2. **Exception handling:** Replace broad `except Exception` with specific exception groups
3. **JSON override pattern:** Use DTOs, make columns authoritative
4. **Type ignores:** Add sqlalchemy2-stubs, split BaseRepository
5. **God classes:** Split cache.py and test_repository.py by concern

### Areas of Agreement
- `deferred()` for JSON columns is the right approach
- Column-only reads are correct for performance and consistency
- Context manager pattern for sessions is correct
- File-based SQLite is correct for tests (in-memory has async issues)
- VCRpy for API recording is recommended
- Registry-based service factory eliminates boilerplate

---

## TD-014: Redundant Referential Integrity Fills [LOW]

**Status:** Identified 2025-12-04
**Location:** `src/testio_mcp/repositories/test_repository.py:1221-1430`

**Problem:**
When syncing tests that reference missing features, the referential integrity fill pattern can trigger duplicate API calls for the same product. This happens when:
1. Multiple test_features reference the same missing feature_id
2. The double-check pattern (line 1399-1407) checks if ANY features exist, not the SPECIFIC feature_id
3. If fetched features don't include the referenced feature_id, subsequent test_features trigger additional integrity fills

**Example (Product 11149):**
- 2 new tests synced, each referencing 2 features
- Each missing feature triggered a separate integrity fill
- Result: 4 integrity fills (12 API calls) instead of 1 (3 API calls)
- All fetches return the same data (idempotent)

**Root Cause:**
Tests reference features that don't exist in the product's current feature catalog:
- Features may have been deleted after test creation
- Possible test data inconsistency in TestIO API?

**Current Behavior:**
```python
# test_repository.py:1265-1286
async def _upsert_test_feature(self, test_id, feature_data, product_id):
    feature_id = feature_data.get("feature_id")

    # AC1: Proactive check BEFORE insert
    if not await self._feature_exists(feature_id):  # Check specific feature_id
        await self._fetch_and_store_features_for_product(product_id)

    # ... upsert test_feature

# test_repository.py:1393-1407
async def _fetch_and_store_features_for_product(self, product_id):
    async with lock:
        # Double-check: ANY features exist (not specific feature_id!)
        feature_count = await session.exec(
            select(func.count()).where(Feature.product_id == product_id)
        )
        if feature_count > 0:
            return  # Already fetched

        # Fetch all features for product
        await feature_repo.sync_features(product_id)
```

**Impact:**
- **Performance:** 3-4x redundant API calls for affected products (~1 in 100)
- **Correctness:** ✅ No data corruption (idempotent operations)
- **Cost:** Minimal (adds ~2-4 seconds per affected product)
- **Logs:** Noisy (duplicate WARNING messages)

**Frequency:**
- Rare: Observed in 1 out of 100+ products during sync
- Only occurs when tests reference non-existent features

**Proposed Solutions:**

**Option 1: Track fetched products in transaction (simplest)**
```python
# Add to _upsert_test_feature or caller
_products_integrity_filled: set[int] = set()  # Per-transaction cache

async def _upsert_test_feature(self, test_id, feature_data, product_id):
    if not await self._feature_exists(feature_id):
        if product_id not in self._products_integrity_filled:
            await self._fetch_and_store_features_for_product(product_id)
            self._products_integrity_filled.add(product_id)
```

**Option 2: Check specific feature after fetch (more thorough)**
```python
async def _fetch_and_store_features_for_product(self, product_id, required_feature_id=None):
    async with lock:
        # If specific feature requested, check if it exists
        if required_feature_id:
            if await self._feature_exists(required_feature_id):
                return  # Feature now exists
        else:
            # General check: any features
            if feature_count > 0:
                return

        # Fetch all features
        await feature_repo.sync_features(product_id)

        # If specific feature still doesn't exist, log warning
        if required_feature_id and not await self._feature_exists(required_feature_id):
            logger.warning(
                f"Feature {required_feature_id} still missing after integrity fill "
                f"for product {product_id} (may be deleted feature)"
            )
```

**Option 3: Skip test_feature if feature doesn't exist after fill (defensive)**
```python
async def _upsert_test_feature(self, test_id, feature_data, product_id):
    if not await self._feature_exists(feature_id):
        if product_id not in self._products_integrity_filled:
            await self._fetch_and_store_features_for_product(product_id)
            self._products_integrity_filled.add(product_id)

        # Double-check after fill
        if not await self._feature_exists(feature_id):
            logger.warning(
                f"Skipping test_feature {test_feature_id} - feature {feature_id} "
                f"doesn't exist even after integrity fill (deleted feature?)"
            )
            return  # Skip this test_feature, don't create dangling FK
```

**Recommendation:**
Combine Option 1 + Option 3:
- Use per-transaction set to prevent duplicate fills
- Skip test_features for truly missing features
- Log warning for data quality issues

**Acceptance Criteria:**
- [ ] Product only triggers ONE integrity fill per sync transaction
- [ ] Missing features logged with actionable warning
- [ ] Test_features for missing features skipped (no FK violations)
- [ ] Logs reduced from 4x WARNING to 1x WARNING per affected product
- [ ] Integration test verifies single integrity fill per product

**Effort:** Low (1-2 hours)
**Risk:** Low (optimization, doesn't change correctness)
**Dependencies:** None
**Priority:** Low (inefficiency, not correctness issue)
