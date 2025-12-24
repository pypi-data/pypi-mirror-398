# Critical Tech Debt Implementation Plan

**Created:** 2025-12-03
**Updated:** 2025-12-04 (TD-001 & TD-002 Complete)
**Status:** ✅ Complete - Archived
**Parent:** [Tech Debt Remediation Plan](../../planning/tech-debt-remediation-plan.md)

---

## Verified Findings

### TD-001: AsyncSession Resource Leak ✅ COMPLETE

**Severity:** Critical
**Status:** ✅ Completed 2025-12-04
**Commit:** `fbf974d`

#### Implementation Summary

**What was fixed:**
- Migrated 1 MCP tool (`sync_data_tool.py`) to `get_service_context()`
- Migrated 5 REST endpoints to `get_service_context_from_server_context()`
- Removed 3 deprecated functions (~240 lines of dead code)
- Updated 16 test files (11 unit + 5 integration)

**Results:**
- Zero session leaks (was: 6)
- Net code reduction: -137 lines
- All 854 unit tests passing
- All 5 integration tests passing

#### Original State (Reference)

| Pattern | Usage Count | Files |
|---------|-------------|-------|
| `get_service(ctx, ...)` (deprecated) | 1 | `sync_data_tool.py:77` ✅ FIXED |
| `get_service_context(ctx, ...)` (safe) | 15 → 16 | Various tools ✅ |
| `get_service_from_server_context(...)` (leaky) | 5 | `api.py:380,412,504,562,663` ✅ FIXED |
| `get_service_context_from_server_context(...)` (safe) | 11 → 16 | Various API endpoints ✅ |

#### Correction from Gemini Review

> **SyncService is NOT leaking.** It falls through to the default case in `_build_service()`
> (returning only `client, cache`) and manages its own sessions internally via
> `async with self.cache.async_session_maker()`. The fix for `sync_data_tool.py` is for
> **consistency only**, not to fix a leak.

#### Leaky Call Sites

**MCP Tool (consistency fix, not a leak):**
```
sync_data_tool.py:77  →  service = get_service(ctx, SyncService)
                         SyncService manages own sessions - no leak here
```

**REST API Endpoints (actual leaks):**
```
api.py:380  →  /api/tests/{test_id}/summary      →  TestService (CORRECTED PATH)
api.py:412  →  /api/tests                        →  TestService
api.py:504  →  /api/products                     →  ProductService
api.py:562  →  /api/products/{id}/tests          →  TestService
api.py:663  →  /api/products/{id}/quality-report →  MultiTestReportService
```

---

### TD-002: Service Instantiation Boilerplate

**Severity:** Critical
**Scope:** 21 if/elif blocks across 3 functions

#### Current State (Verified)

| Function | Location | Service Branches |
|----------|----------|------------------|
| `_build_service()` | Lines 55-145 | 4 (TestService, ProductService, BugService, default) |
| `get_service_context()` | Lines 192-354 | 9 (Test, Product, Feature, UserStory, User, Analytics, Search, Bug, default) |
| `get_service_context_from_server_context()` | Lines 472-595 | 8 (Test, Product, Feature, UserStory, User, Analytics, Search, default) |

**Total:** 21 if/elif blocks with significant code duplication

#### Service Dependency Patterns (11 services)

| Service | Needs Session | Dependencies | Notes |
|---------|--------------|--------------|-------|
| TestService | Yes | UserRepo, TestRepo, BugRepo, ProductRepo | Complex |
| MultiTestReportService | Yes | Same as TestService | Shares pattern |
| BugService | Yes | UserRepo, BugRepo, TestRepo | Complex |
| ProductService | No | session_factory, customer_id | Uses factory pattern |
| FeatureService | Yes | FeatureRepo | Simple |
| UserStoryService | Yes | FeatureRepo | Simple |
| UserService | Yes | UserRepo | Simple |
| AnalyticsService | Yes | Direct session + customer_id + client + cache | Unique |
| SearchService | Yes | SearchRepo | Simple |
| DiagnosticsService | No | client, cache | Default pattern |
| SyncService | No | client, cache, optional repo factories | Default pattern |

---

## Implementation Plan

### Phase 1: TD-001 Fix (1-2 hours)

**Goal:** Eliminate all AsyncSession leaks

#### Step 1.1: Add Deprecation Warnings

```python
# In service_helpers.py

import warnings

def get_service(...):
    """... existing docstring ..."""
    warnings.warn(
        "get_service() is deprecated due to AsyncSession leak. "
        "Use 'async with get_service_context(...)' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    # ... existing implementation

def get_service_from_server_context(...):
    """... existing docstring ..."""
    warnings.warn(
        "get_service_from_server_context() is deprecated due to AsyncSession leak. "
        "Use 'async with get_service_context_from_server_context(...)' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    # ... existing implementation
```

#### Step 1.2: Fix sync_data_tool.py

**Before:**
```python
# Line 77
service = get_service(ctx, SyncService)

try:
    # ... use service
```

**After:**
```python
async with get_service_context(ctx, SyncService) as service:
    try:
        # ... use service
```

**Note:** SyncService is not currently handled by `get_service_context()`. Need to add it:

```python
# In get_service_context(), add new branch:
elif service_name == "SyncService":
    # SyncService uses client + cache (no session needed)
    from testio_mcp.services.sync_service import SyncService as SyncSvc
    service = service_class(client=client, cache=cache)  # type: ignore[call-arg]
    yield service
```

#### Step 1.3: Fix api.py Endpoints (5 locations)

**Pattern to apply at each location:**

**Before:**
```python
server_ctx = get_server_context_from_request(request)
service = get_service_from_server_context(server_ctx, TestService)
result = await service.method()
return Output(**result)
```

**After:**
```python
server_ctx = get_server_context_from_request(request)
async with get_service_context_from_server_context(server_ctx, TestService) as service:
    result = await service.method()
    return Output(**result)
```

**Specific Fixes:**

| Line | Endpoint | Service | Fix |
|------|----------|---------|-----|
| 380 | `/api/tests/{test_id}` | TestService | Wrap in context manager |
| 412 | `/api/tests` | TestService | Wrap in context manager |
| 504 | `/api/products` | ProductService | Wrap in context manager |
| 562 | `/api/products/{id}/tests` | TestService | Wrap in context manager |
| 663 | `/api/products/{id}/quality-report` | MultiTestReportService | Wrap in context manager |

#### Step 1.4: Update Tests

- Verify no SQLAlchemy GC warnings in test output
- Add test that deprecated functions emit warnings

---

### Phase 2: TD-002 Refactor (1-2 days)

**Goal:** Replace 21 if/elif blocks with factory-based registry

#### Review Feedback (Gemini + Codex)

> **REJECTED: List-based repo configuration**
>
> The original plan used `repos: list[tuple[type, str]]` which is **too naive** to handle
> inter-repository dependencies. `TestRepository` requires `user_repo` to be passed in
> `__init__` for user extraction during sync (STORY-036). A generic loop can't inject
> the created `UserRepository` instance into `TestRepository`.
>
> **APPROVED: Factory-based registry** using explicit factory functions (lambdas) that
> handle complex wiring while maintaining type safety.

#### Step 2.1: Define Factory-Based Service Config

```python
# src/testio_mcp/utilities/service_registry.py

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.database.cache import PersistentCache
from testio_mcp.services.base_service import BaseService


# Type alias for service factory functions
ServiceFactory = Callable[
    [AsyncSession | None, TestIOClient, PersistentCache, int],  # session, client, cache, customer_id
    BaseService
]


@dataclass
class ServiceConfig:
    """Factory-based service configuration.

    Attributes:
        needs_session: Whether to create an AsyncSession before calling factory
        factory: Callable that creates the fully-configured service instance
    """
    needs_session: bool
    factory: ServiceFactory
```

#### Step 2.2: Build Service Registry with Explicit Factories

```python
# Continuation of service_registry.py

from testio_mcp.repositories.bug_repository import BugRepository
from testio_mcp.repositories.feature_repository import FeatureRepository
from testio_mcp.repositories.product_repository import ProductRepository
from testio_mcp.repositories.search_repository import SearchRepository
from testio_mcp.repositories.test_repository import TestRepository
from testio_mcp.repositories.user_repository import UserRepository

from testio_mcp.services.analytics_service import AnalyticsService
from testio_mcp.services.bug_service import BugService
from testio_mcp.services.diagnostics_service import DiagnosticsService
from testio_mcp.services.feature_service import FeatureService
from testio_mcp.services.multi_test_report_service import MultiTestReportService
from testio_mcp.services.product_service import ProductService
from testio_mcp.services.search_service import SearchService
from testio_mcp.services.sync_service import SyncService
from testio_mcp.services.test_service import TestService
from testio_mcp.services.user_service import UserService
from testio_mcp.services.user_story_service import UserStoryService


def _build_test_service(
    session: AsyncSession | None,
    client: TestIOClient,
    cache: PersistentCache,
    customer_id: int,
) -> TestService:
    """Factory for TestService with proper repo wiring.

    CRITICAL: UserRepository must be created first and passed to
    TestRepository/BugRepository for user extraction (STORY-036).
    """
    assert session is not None
    user_repo = UserRepository(session=session, client=client, customer_id=customer_id)
    test_repo = TestRepository(
        session=session,
        client=client,
        customer_id=customer_id,
        user_repo=user_repo,
        cache=cache,
    )
    bug_repo = BugRepository(
        session=session,
        client=client,
        customer_id=customer_id,
        user_repo=user_repo,
        cache=cache,
    )
    product_repo = ProductRepository(
        session=session, client=client, customer_id=customer_id
    )
    return TestService(
        client=client,
        test_repo=test_repo,
        bug_repo=bug_repo,
        product_repo=product_repo,
    )


def _build_bug_service(
    session: AsyncSession | None,
    client: TestIOClient,
    cache: PersistentCache,
    customer_id: int,
) -> BugService:
    """Factory for BugService with proper repo wiring."""
    assert session is not None
    user_repo = UserRepository(session=session, client=client, customer_id=customer_id)
    bug_repo = BugRepository(
        session=session,
        client=client,
        customer_id=customer_id,
        user_repo=user_repo,
        cache=cache,
    )
    test_repo = TestRepository(
        session=session,
        client=client,
        customer_id=customer_id,
        user_repo=user_repo,
        cache=cache,
    )
    return BugService(client=client, bug_repo=bug_repo, test_repo=test_repo)


SERVICE_REGISTRY: dict[type[BaseService], ServiceConfig] = {
    # Complex services with inter-repo dependencies
    TestService: ServiceConfig(
        needs_session=True,
        factory=_build_test_service,
    ),
    MultiTestReportService: ServiceConfig(
        needs_session=True,
        factory=lambda s, c, cache, cid: MultiTestReportService(
            client=c,
            test_repo=TestRepository(s, c, cid, UserRepository(s, c, cid), cache),
            bug_repo=BugRepository(s, c, cid, UserRepository(s, c, cid), cache),
            product_repo=ProductRepository(s, c, cid),
        ),
    ),
    BugService: ServiceConfig(
        needs_session=True,
        factory=_build_bug_service,
    ),

    # Simple services with single repo (no inter-dependencies)
    FeatureService: ServiceConfig(
        needs_session=True,
        factory=lambda s, c, cache, cid: FeatureService(
            feature_repo=FeatureRepository(s, c, cid)
        ),
    ),
    UserStoryService: ServiceConfig(
        needs_session=True,
        factory=lambda s, c, cache, cid: UserStoryService(
            feature_repo=FeatureRepository(s, c, cid)
        ),
    ),
    UserService: ServiceConfig(
        needs_session=True,
        factory=lambda s, c, cache, cid: UserService(
            user_repo=UserRepository(s, c, cid)
        ),
    ),
    SearchService: ServiceConfig(
        needs_session=True,
        factory=lambda s, c, cache, cid: SearchService(
            search_repo=SearchRepository(s, c, cid)
        ),
    ),

    # AnalyticsService: needs session + cache (Codex fix: was missing cache)
    AnalyticsService: ServiceConfig(
        needs_session=True,
        factory=lambda s, c, cache, cid: AnalyticsService(
            session=s, customer_id=cid, client=c, cache=cache
        ),
    ),

    # ProductService: uses session factory pattern (no session needed)
    ProductService: ServiceConfig(
        needs_session=False,
        factory=lambda s, c, cache, cid: ProductService(
            client=c,
            cache=cache,
            session_factory=cache.async_session_maker,
            customer_id=cid,
        ),
    ),

    # Default client+cache services (manage own sessions internally)
    DiagnosticsService: ServiceConfig(
        needs_session=False,
        factory=lambda s, c, cache, cid: DiagnosticsService(client=c, cache=cache),
    ),
    SyncService: ServiceConfig(
        needs_session=False,
        factory=lambda s, c, cache, cid: SyncService(client=c, cache=cache),
    ),
}
```

#### Step 2.3: Generic Build Function (Fail-Fast)

```python
# Continuation of service_registry.py


@asynccontextmanager
async def build_service[T: BaseService](
    service_class: type[T],
    client: TestIOClient,
    cache: PersistentCache,
) -> AsyncIterator[T]:
    """Generic service builder using registry configuration.

    Args:
        service_class: Service class to instantiate
        client: TestIO API client
        cache: Persistent cache with session maker

    Yields:
        Configured service instance

    Raises:
        KeyError: If service not in registry (fail-fast, no silent fallback)
    """
    # FAIL-FAST: Require explicit registration (Codex recommendation)
    if service_class not in SERVICE_REGISTRY:
        raise KeyError(
            f"Service {service_class.__name__} not in SERVICE_REGISTRY. "
            "Add an explicit ServiceConfig entry to register this service."
        )

    config = SERVICE_REGISTRY[service_class]
    session: AsyncSession | None = None
    customer_id = cache.customer_id

    try:
        # Create session if needed
        if config.needs_session:
            assert cache.async_session_maker is not None
            session = cache.async_session_maker()

        # Call factory with all dependencies
        service = config.factory(session, client, cache, customer_id)
        yield service  # type: ignore[misc]

    finally:
        # CRITICAL: Always close session to prevent resource leak
        if session is not None:
            await session.close()
```

#### Step 2.4: Simplify service_helpers.py

```python
# Updated service_helpers.py

from testio_mcp.utilities.service_registry import build_service


@asynccontextmanager
async def get_service_context[ServiceT: BaseService](
    ctx: Context, service_class: type[ServiceT]
) -> AsyncIterator[ServiceT]:
    """Create service with proper AsyncSession lifecycle.

    Uses factory-based registry for consistent, maintainable service creation.
    """
    assert ctx.request_context is not None
    server_ctx = cast("ServerContext", ctx.request_context.lifespan_context)

    client = server_ctx["testio_client"]
    cache = server_ctx["cache"]

    async with build_service(service_class, client, cache) as service:
        yield service


@asynccontextmanager
async def get_service_context_from_server_context[ServiceT: BaseService](
    server_ctx: "ServerContext", service_class: type[ServiceT]
) -> AsyncGenerator[ServiceT, None]:
    """Create service from ServerContext with proper session cleanup.

    Uses factory-based registry for consistent, maintainable service creation.
    """
    client = server_ctx["testio_client"]
    cache = server_ctx["cache"]

    async with build_service(service_class, client, cache) as service:
        yield service
```

**Result:**
- `_build_service()` eliminated entirely
- `get_service_context()` reduced from ~160 lines to ~15 lines
- `get_service_context_from_server_context()` reduced from ~130 lines to ~15 lines
- Adding new service = 1 factory function + 1 registry entry
- **Fail-fast** on unregistered services (no silent fallback)
- **Type-safe** wiring with explicit factories

---

## Testing Strategy

### TD-001 Tests

```python
# tests/unit/test_service_helpers_deprecation.py

import warnings
import pytest
from testio_mcp.utilities import get_service, get_service_from_server_context

@pytest.mark.unit
def test_get_service_emits_deprecation_warning(mock_ctx):
    """Verify deprecated function warns users."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        get_service(mock_ctx, TestService)

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "get_service_context" in str(w[0].message)
```

### TD-002 Tests

```python
# tests/unit/test_service_registry.py

import pytest
from testio_mcp.utilities.service_registry import SERVICE_REGISTRY, build_service

@pytest.mark.unit
def test_all_services_registered():
    """Verify all service classes have registry entries."""
    from testio_mcp.services import (
        TestService, ProductService, BugService, FeatureService,
        UserService, UserStoryService, AnalyticsService, SearchService,
        DiagnosticsService, SyncService, MultiTestReportService,
    )

    expected = {
        TestService, ProductService, BugService, FeatureService,
        UserService, UserStoryService, AnalyticsService, SearchService,
        DiagnosticsService, SyncService, MultiTestReportService,
    }

    assert set(SERVICE_REGISTRY.keys()) == expected


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_creates_valid_instance(mock_client, mock_cache):
    """Verify registry builds working service instances."""
    async with build_service(FeatureService, mock_client, mock_cache) as service:
        assert isinstance(service, FeatureService)
        assert service.feature_repo is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_closes_session(mock_client, mock_cache):
    """Verify session is closed after context manager exits.

    FIXED (Codex review): Previous test created a different session instance
    than build_service() would use. Now we configure the mock to return a
    single session instance that we can verify.
    """
    # Create a single mock session that will be returned by session_maker
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()

    # Configure session_maker to return the SAME session instance
    mock_cache.async_session_maker.return_value = mock_session

    async with build_service(FeatureService, mock_client, mock_cache):
        # Session should not be closed yet
        mock_session.close.assert_not_awaited()

    # After exiting context, session.close() should have been awaited
    mock_session.close.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_service_fails_fast_for_unregistered():
    """Verify unregistered services raise KeyError (no silent fallback)."""
    class UnregisteredService(BaseService):
        pass

    with pytest.raises(KeyError, match="not in SERVICE_REGISTRY"):
        async with build_service(UnregisteredService, mock_client, mock_cache):
            pass
```

---

## Rollback Plan

### TD-001 Rollback
- Revert deprecation warnings (no functional change)
- Revert context manager conversions (return to direct service calls)
- Risk: Low (changes are isolated to call sites)

### TD-002 Rollback
- Keep `service_registry.py` but don't use it
- Revert `service_helpers.py` to if/elif pattern
- Risk: Medium (touches core infrastructure)

---

## Success Criteria

| Metric | Before | After (TD-001) | After (TD-002) | Status |
|--------|--------|----------------|----------------|--------|
| Leaky call sites | 6 | 0 ✅ | 0 ✅ | Complete |
| SQLAlchemy GC warnings | Present | None ✅ | None ✅ | Complete |
| Deprecated functions | 3 | 0 ✅ | 0 ✅ | Complete |
| if/elif blocks in service_helpers.py | 21 | 21 | 0 ✅ | Complete |
| Lines in get_service_context() | ~160 | ~160 | ~15 ✅ | Complete |
| Lines in get_service_context_from_server_context() | ~130 | ~130 | ~15 ✅ | Complete |
| New service addition effort | 3 functions | 3 functions | 1 registry entry ✅ | Complete |
| Unit tests passing | 854 | 854 ✅ | 863 ✅ | Complete |
| Registry tests added | 0 | 0 | 9 ✅ | Complete |
| Code reduction | 0 | -137 lines ✅ | -412 lines ✅ | Complete |

---

## Implementation Checklist

### TD-001 ✅ COMPLETE (2025-12-04)
- [x] ~~Add deprecation warning~~ → Removed functions entirely (cleaner)
- [x] SyncService already handled by default case in `get_service_context()`
- [x] Fix `sync_data_tool.py:77` → Migrated to `get_service_context()`
- [x] Fix `api.py:380` (get_test_summary_rest) → Migrated to context manager
- [x] Fix `api.py:412` (list_tests_rest) → Migrated to context manager
- [x] Fix `api.py:504` (list_products_rest) → Migrated to context manager
- [x] Fix `api.py:562` (list_product_tests_rest) → Migrated to context manager
- [x] Fix `api.py:663` (get_product_quality_report_rest) → Migrated to context manager
- [x] Updated tests (11 unit + 5 integration) → All passing
- [x] Verify no GC warnings → None detected
- [x] Remove deprecated functions → `get_service()`, `get_service_from_server_context()`, `_build_service()` removed
- [x] All pre-commit hooks passing → ruff, mypy, detect-secrets, etc.

### TD-002 ✅ COMPLETE (2025-12-04)
- [x] Create `src/testio_mcp/utilities/service_registry.py`
- [x] Define `ServiceConfig` dataclass
- [x] Build `SERVICE_REGISTRY` with all 11 services
- [x] Implement `build_service()` generic function
- [x] Refactor `get_service_context()` to use registry (~160 lines → ~15 lines)
- [x] Refactor `get_service_context_from_server_context()` to use registry (~130 lines → ~15 lines)
- [x] Lazy imports to avoid circular dependencies
- [x] Add 9 registry tests (all passing)
- [x] Verify all 863 unit tests pass
- [x] Update documentation

---

## Estimated Timeline

| Phase | Task | Estimate |
|-------|------|----------|
| TD-001.1 | Deprecation warnings | 30 min |
| TD-001.2 | Add SyncService to context manager | 30 min |
| TD-001.3 | Fix 6 call sites | 1 hour |
| TD-001.4 | Tests & verification | 30 min |
| **TD-001 Total** | | **2.5 hours** |
| TD-002.1 | Create service_registry.py | 2 hours |
| TD-002.2 | Implement build_service() | 2 hours |
| TD-002.3 | Refactor service_helpers.py | 1 hour |
| TD-002.4 | Tests & verification | 2 hours |
| **TD-002 Total** | | **7 hours** |
| **Combined Total** | | **~1.5 days** |

---

## Appendix: AI Review Feedback

### Gemini Review (2025-12-03)

**TD-001 Verdict:** Valid / Critical

**Key Correction:** SyncService is NOT leaking - it's a false positive.
- `SyncService.__init__` does not accept a session
- It manages its own sessions internally via `async with self.cache.async_session_maker()`
- `get_service(ctx, SyncService)` falls through to default case, creating no session
- **Recommendation:** Migrate for consistency, but ensure `get_service_context` handles SyncService by NOT injecting a session

**TD-002 Verdict:** Valid Problem / **Flawed Solution** (original plan)

**Registry Pattern Flaw (original):**
- Proposed `repos: list[tuple[type, str]]` was too naive for inter-repo dependencies
- `TestRepository` requires `user_repo` passed in `__init__` for STORY-036
- Generic loop couldn't inject the created `UserRepository` instance

**Recommended Fix:** Use explicit factory functions (lambdas) in registry - **APPLIED**

---

### Codex Review (2025-12-03)

**Key Findings:**

1. **High Risk:** Registry plan omitted `cache` when building `AnalyticsService`
   - **Fix Applied:** Added `cache=cache` to AnalyticsService factory

2. **High Risk:** `build_service()` fallback silently instantiated unregistered services
   - **Fix Applied:** Now raises `KeyError` for missing registry entries (fail-fast)

3. **Medium:** Session-close test was ineffective (patched different instance)
   - **Fix Applied:** Test now configures mock to return single session instance

4. **Medium:** TD-001 table had wrong endpoint path (`/api/tests/{test_id}` vs `/api/tests/{test_id}/summary`)
   - **Fix Applied:** Corrected path in documentation

5. **Low:** Registry still special-cases repos needing `user_repo`/`cache`
   - **Accepted:** Explicit factory functions handle this cleanly

---

### Summary of Changes from Reviews

| Issue | Source | Resolution |
|-------|--------|------------|
| SyncService false positive | Gemini | Documented as consistency fix, not leak |
| Wrong endpoint path | Codex | Corrected to `/api/tests/{test_id}/summary` |
| List-based repos can't handle dependencies | Both | Replaced with factory-based registry |
| Silent fallback for unregistered services | Codex | Added fail-fast KeyError |
| Missing cache for AnalyticsService | Codex | Added cache to factory |
| Session-close test ineffective | Codex | Fixed mock configuration |
| String-based extra_deps fragile | Gemini | Replaced with explicit factory calls |
