# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TestIO MCP Server is a Model Context Protocol (MCP) server that provides AI-first access to TestIO's Customer API. It enables non-developer stakeholders (CSMs, PMs, QA leads) to query test status, bug information, and activity metrics through AI tools like Claude and Cursor.

**Key Characteristics:**
- Read-only MVP (no write operations)
- Service layer architecture (business logic separated from transport)
- Async Python with strict typing
- Comprehensive security (token sanitization, input validation)

**Available MCP Tools:**
- `list_products` - List all products with optional filtering
- `list_tests` - List tests for a product with status filtering
- `get_test_summary` - Get comprehensive status of a single test
- `list_features` - List features for a product (Epic 005)
- `list_users` - List testers and customers with type filter (Epic 005)
- `generate_quality_report` - Generate Product Quality Report (multi-product support)
- `query_metrics` - Custom analytics with pivot tables (Epic 007)
- `get_analytics_capabilities` - Discover available dimensions/metrics for query_metrics (Epic 007)
- `search` - Full-text search across entities with BM25 ranking (Epic 010)
- `sync_data` - Explicit data refresh control (Epic 009)
- `get_server_diagnostics` - Consolidated server health (API, database, sync status) (STORY-060)
- `get_problematic_tests` - Tests that failed to sync (debugging tool)
- `list_bugs` - List bugs for specific tests with filters (STORY-084)
- `get_bug_summary` - Get comprehensive bug details (STORY-085)
- `get_product_summary` - Get product metadata with counts (STORY-057)
- `get_feature_summary` - Get feature metadata with user stories (STORY-057)
- `get_user_summary` - Get user metadata with activity counts (STORY-057)

**Available MCP Prompts:**
- `analyze-product-quality` - Interactive 5-phase quality analysis workflow with portfolio mode (STORY-087)
- `prep-meeting` - Narrative-first meeting preparation workflow (STORY-099)

**Available MCP Resources:**
- `testio://knowledge/playbook` - Expert heuristics and templates for CSMs (STORY-066)
- `testio://knowledge/programmatic-access` - REST API discovery guide (STORY-099)

**Breaking Changes (v0.3.0+):**
- `health_check` → replaced by `get_server_diagnostics`
- `get_database_stats` → replaced by `get_server_diagnostics`
- `list_user_stories` → **REMOVED** (use `list_features` + `get_feature_summary`)
- `query_metrics` default now excludes initialized/cancelled tests

## Quick Start

```bash
# Setup environment
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
uv run pre-commit install

# Fast feedback loop (use this during development)
uv run pytest -m unit              # ~0.5s, no API needed
uv run pytest -m unit --cov=src    # With coverage
```

## Development Commands

### Testing

**Fast Feedback Loop (Primary):**
```bash
# Unit tests only - Lightning fast!
uv run pytest -m unit
uv run pytest -m unit --cov=src --cov-report=html

# Full verification (pre-commit)
uv run pytest                      # ~31s (all tests, requires API token)

# Specific test types
uv run pytest tests/unit/test_cache.py           # Single file
uv run pytest -m integration                     # Integration only (~30s), ask user for env vars if needed
```

**See [docs/architecture/TESTING.md](docs/architecture/TESTING.md) for comprehensive testing guide.**

### Code Quality

```bash
uv run ruff format                 # Format code
uv run ruff check --fix            # Lint with auto-fix
uv run mypy src                    # Type check (strict mode)
uv run pre-commit run --all-files         # Run all hooks
```

### Running the Server

```bash
# Development (from repository)
uv run python -m testio_mcp                      # stdio mode (default)
uv run python -m testio_mcp serve --transport http --port 8080  # HTTP mode (recommended)

# Production (via uvx from PyPI)
uvx testio-mcp                                   # stdio mode
uvx testio-mcp serve --transport http           # HTTP mode (multi-client)
```

**See [MCP_SETUP.md](MCP_SETUP.md) for client configuration (Claude Code, Cursor, Inspector).**

### CLI Sync Command

```bash
# Basic usage
uvx testio-mcp sync --status       # Check sync status
uvx testio-mcp sync --verbose      # Manual sync with progress
uvx testio-mcp sync --since yesterday --product-ids 598

# Sync modes
uvx testio-mcp sync                           # Hybrid (default): discover + update mutable
uvx testio-mcp sync --incremental-only        # Fast: discover new only
uvx testio-mcp sync --force --product-ids 598 # Non-destructive: update all
uvx testio-mcp sync --nuke --yes              # Destructive: delete + resync

# Manage failed syncs
uvx testio-mcp problematic list
uvx testio-mcp problematic retry 598
```

**See [README.md](README.md) for advanced sync patterns and troubleshooting.**

### MCP Inspector

```bash
# List available tools
npx @modelcontextprotocol/inspector --cli uv run python -m testio_mcp --method tools/list

# Test a tool (note: string params must be quoted)
npx @modelcontextprotocol/inspector --cli uv run python -m testio_mcp \
  --method tools/call --tool-name get_test_summary --tool-arg 'test_id="109363"'

# Interactive mode for Human Users (web UI)
npx @modelcontextprotocol/inspector uv run python -m testio_mcp
```

## Architecture

### Service Layer Pattern

This codebase follows a **service layer architecture** that separates business logic from transport:

```
MCP Tools (thin wrappers)
    ↓ extract dependencies, delegate
Service Layer (business logic)
    ↓ make API calls, cache, aggregate
Infrastructure (TestIOClient, PersistentCache)
    ↓ HTTP requests, SQLite queries
TestIO Customer API
```

**Key Components:**

1. **MCP Tools** (`src/testio_mcp/tools/`) - Thin wrappers that:
   - Extract dependencies from server context
   - Create service instances
   - Delegate to service layer
   - Convert domain exceptions to MCP error format (❌ℹ️💡)

2. **Service Layer** (`src/testio_mcp/services/`) - Business logic that:
   - Handles domain operations (queries, filtering, aggregation)
   - Makes caching decisions
   - Orchestrates multiple API calls
   - Raises domain exceptions (TestNotFoundException, etc.)
   - Framework-agnostic (can be reused in REST API, CLI, webhooks)

3. **Infrastructure** - HTTP client and persistent cache:
   - `TestIOClient`: Async HTTP wrapper with connection pooling, concurrency control
   - `PersistentCache`: SQLite-based local data store with incremental sync

**Example Pattern:**
```python
# Tool (thin wrapper)
@mcp.tool()
async def get_test_summary(test_id: int, ctx: Context) -> dict:
    service = get_service(ctx, TestService)
    try:
        return await service.get_test_summary(test_id)
    except TestNotFoundException:
        raise ToolError(f"❌ Test ID '{test_id}' not found") from None

# Service (business logic)
class TestService(BaseService):
    async def get_test_summary(self, test_id: int) -> dict:
        # Delegates to repository, raises domain exceptions
        ...
```

**See [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) for complete architecture details.**

## Adding New Tools

**Pattern simplified with BaseService + get_service() helper:**

1. **Create service class** (`src/testio_mcp/services/my_service.py`):
   ```python
   from testio_mcp.services.base_service import BaseService
   from testio_mcp.exceptions import ResourceNotFoundException

   class MyService(BaseService):
       """Service for my resource operations.

       Inherits from BaseService for:
       - Standard constructor (client, cache injection)
       - Cache key formatting (_make_cache_key)
       - Cache-or-fetch pattern (_get_cached_or_fetch)
       - TTL constants (CACHE_TTL_PRODUCTS, CACHE_TTL_TESTS, CACHE_TTL_BUGS)
       """

       async def get_resource(self, resource_id: int) -> dict:
           """Fetch resource with caching."""
           return await self._get_cached_or_fetch(
               cache_key=self._make_cache_key("resource", resource_id),
               fetch_fn=lambda: self.client.get(f"resources/{resource_id}"),
               ttl_seconds=self.CACHE_TTL_TESTS,
               transform_404=ResourceNotFoundException(resource_id)
           )
   ```

2. **Create MCP tool** (`src/testio_mcp/tools/my_tool.py`):
   ```python
   from fastmcp import Context
   from fastmcp.exceptions import ToolError

   from testio_mcp.server import mcp
   from testio_mcp.services.my_service import MyService
   from testio_mcp.utilities import get_service
   from testio_mcp.exceptions import ResourceNotFoundException

   @mcp.tool()
   async def get_resource(resource_id: int, ctx: Context) -> dict:
       """Get resource by ID.

       Args:
           resource_id: Resource identifier
           ctx: FastMCP context (injected automatically by framework)

       Returns:
           Resource data dictionary
       """
       service = get_service(ctx, MyService)

       try:
           return await service.get_resource(resource_id)
       except ResourceNotFoundException:
           raise ToolError(
               f"❌ Resource '{resource_id}' not found\n"
               f"ℹ️ The resource may have been deleted\n"
               f"💡 Verify the resource ID is correct"
           ) from None
   ```

3. **Write service tests** (`tests/services/test_my_service.py`):
   - Mock client and cache
   - Test business logic directly
   - No FastMCP mocking needed

4. **Write integration test** (`tests/integration/test_my_tool_integration.py`):
   - Use real API (staging environment)
   - Test full flow: tool → service → API

**Tool auto-registration:** Tools are automatically discovered and registered at server startup. Just create `*_tool.py` file in `src/testio_mcp/tools/` with `@mcp.tool()` decorator - no manual imports needed!

**Key patterns:**
- **BaseService:** Inherit for standard caching infrastructure (ADR-011)
- **get_service():** 1-line dependency injection with full type safety (ADR-011)
- **ToolError:** FastMCP exception pattern for consistent error handling (ADR-011)
- **Auto-discovery:** Tools register automatically via pkgutil (ADR-011)
- **AsyncSession Lifecycle:** Always use `async with get_service_context()` for resource cleanup

---

## SQLModel Query Patterns (Epic 006)

**Added:** 2025-11-23 (Epic 006 Retrospective)
**Lesson Learned:** Mixing SQLAlchemy and SQLModel query patterns caused production bugs (STORY-034B)

This codebase uses **SQLModel** (SQLAlchemy 2.0 + Pydantic) for ORM queries. Understanding the difference between `session.execute()` and `session.exec()` is critical.

### Quick Reference

| Need | Use | Returns | Example |
|------|-----|---------|---------|
| **ORM Model** | `session.exec(select(...)).first()` | `Test \| None` | Attribute access (`test.data`) |
| **Scalar Value** | `session.exec(select(func.count(...))).one()` | `int` | Direct value |
| **Multiple Models** | `session.exec(select(...)).all()` | `list[Test]` | List of ORM models |
| **Raw SQL (avoid)** | `session.exec(text("...")` | Depends | Use only when ORM can't express query |

### Pattern 1: Get Single ORM Model (Most Common)

**✅ CORRECT - Use `session.exec().first()`:**
```python
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from testio_mcp.models.orm import Test

async def get_test(session: AsyncSession, test_id: int) -> Test | None:
    """Get test by ID - returns ORM model."""
    result = await session.exec(select(Test).where(Test.id == test_id))
    test = result.first()  # Returns Test ORM model or None

    if test:
        # ✅ Attribute access works
        print(test.data)  # Works!
        print(test.status)  # Works!

    return test
```

**❌ WRONG - Using `session.execute().one_or_none()`:**
```python
# This returns Row, not ORM model!
result = await session.execute(select(Test).where(Test.id == test_id))
test = result.one_or_none()  # Returns Row (dict-like)

# ❌ AttributeError: 'Row' object has no attribute 'data'
print(test.data)  # CRASHES!

# Must use dict-like access for Row
print(test._mapping['data'])  # Works but shouldn't use Row pattern
```

**Why this matters:** SQLAlchemy's `execute()` returns `Result[Row]`, SQLModel's `exec()` returns `Result[Model]`. Always use `exec()` for ORM queries.

---

### Pattern 2: Get Multiple ORM Models

**✅ CORRECT - Use `session.exec().all()`:**
```python
async def get_tests_for_product(session: AsyncSession, product_id: int) -> list[Test]:
    """Get all tests for product - returns list of ORM models."""
    result = await session.exec(
        select(Test).where(Test.product_id == product_id)
    )
    tests = result.all()  # Returns list[Test]

    # ✅ Attribute access works on each model
    for test in tests:
        print(test.id, test.status)  # Works!

    return tests
```

---

### Pattern 3: Get Scalar Values (Count, Sum, etc.)

**✅ CORRECT - Use `session.exec().one()` for aggregates:**
```python
from sqlmodel import func

async def count_tests(session: AsyncSession, product_id: int) -> int:
    """Count tests for product - returns scalar int."""
    result = await session.exec(
        select(func.count(Test.id)).where(Test.product_id == product_id)
    )
    count = result.one()  # Returns int directly
    return count
```

**Note:** Use `.one()` when you expect exactly one result, `.one_or_none()` when result might be NULL.

---

### Pattern 4: Checking Existence

**✅ CORRECT - Use `session.exec().first()` with bool check:**
```python
async def test_exists(session: AsyncSession, test_id: int) -> bool:
    """Check if test exists."""
    result = await session.exec(select(Test).where(Test.id == test_id))
    test = result.first()
    return test is not None
```

**Alternative (more efficient) - Use count:**
```python
async def test_exists_fast(session: AsyncSession, test_id: int) -> bool:
    """Check if test exists (efficient - doesn't load full model)."""
    result = await session.exec(
        select(func.count(Test.id)).where(Test.id == test_id)
    )
    count = result.one()
    return count > 0
```

---

### Pattern 5: Update ORM Models

**✅ CORRECT - Modify attributes, commit:**
```python
async def update_test_status(session: AsyncSession, test_id: int, new_status: str) -> None:
    """Update test status."""
    result = await session.exec(select(Test).where(Test.id == test_id))
    test = result.first()

    if test:
        # ✅ Modify attributes directly
        test.status = new_status
        test.synced_at = datetime.utcnow()

        # Commit (caller decides when to commit)
        await session.commit()
```

**Note:** Follow repository pattern - let caller control transaction boundaries.

---

### Pattern 6: Insert New Models

**✅ CORRECT - Use `session.add()`:**
```python
async def create_test(session: AsyncSession, test_data: dict) -> Test:
    """Create new test."""
    test = Test(
        id=test_data["id"],
        customer_id=test_data["customer_id"],
        product_id=test_data["product_id"],
        data=test_data,
        status=test_data.get("status", "initialized"),
    )

    session.add(test)
    await session.commit()
    await session.refresh(test)  # Load DB-generated fields

    return test
```

---

### Pattern 7: Bulk Operations

**✅ CORRECT - Use bulk insert/update:**
```python
async def bulk_insert_tests(session: AsyncSession, tests_data: list[dict]) -> None:
    """Bulk insert tests."""
    tests = [Test(**data) for data in tests_data]

    session.add_all(tests)
    await session.commit()
```

---

### Common Pitfalls

**❌ PITFALL #1: Using `execute()` instead of `exec()`**
```python
# WRONG - Returns Row objects
result = await session.execute(select(Test))
tests = result.all()  # list[Row] - no attribute access!

# CORRECT - Returns ORM models
result = await session.exec(select(Test))
tests = result.all()  # list[Test] - attribute access works!
```

**❌ PITFALL #2: Forgetting `.first()`, `.one()`, or `.all()`**
```python
# WRONG - Returns Result object, not model
result = await session.exec(select(Test).where(Test.id == test_id))
print(result.data)  # AttributeError!

# CORRECT - Extract model from Result
result = await session.exec(select(Test).where(Test.id == test_id))
test = result.first()  # Now test is Test | None
if test:
    print(test.data)  # Works!
```

**❌ PITFALL #3: Using raw SQL INSERT in tests**
```python
# WRONG - Creates incomplete schema, ORM queries fail
await session.execute(text("INSERT INTO tests (id, customer_id) VALUES (1, 123)"))

# CORRECT - Use ORM models in tests
session.add(Test(id=1, customer_id=123, product_id=456, data={}, status="initialized"))
await session.commit()
```

---

### Type Annotations (SQLModel-specific)

**SQLModel uses SQLAlchemy column methods that mypy doesn't recognize:**
```python
from sqlmodel import col  # Import for .in_() operations

# Type ignore needed for SQLAlchemy-specific methods
test_ids = [1, 2, 3]
result = await session.exec(
    select(Test).where(col(Test.id).in_(test_ids))  # type: ignore[arg-type]
)
```

**Common type ignores:**
- `col(Model.field).in_(...)` - SQLAlchemy column method
- `func.count(Model.field)` - SQLAlchemy function
- `select(Model).order_by(desc(...))` - SQLAlchemy ordering

---

### Resource Lifecycle (Critical)

**✅ ALWAYS use async context managers:**
```python
# CORRECT - Session automatically closed
async with cache.async_session_maker() as session:
    result = await session.exec(select(Test))
    test = result.first()
    # Session closed when exiting block
```

**❌ NEVER create sessions without cleanup:**
```python
# WRONG - Resource leak!
session = cache.async_session_maker()  # Never closed!
result = await session.exec(select(Test))
```

**✅ For tools, use `get_service_context()`:**
```python
@mcp.tool()
async def my_tool(ctx: Context) -> dict:
    """MCP tool with proper resource cleanup."""
    async with get_service_context(ctx, MyService) as service:
        return await service.do_something()
    # Session automatically closed
```

---

### Async Session Management (STORY-062)

**Added:** 2025-11-27 (STORY-062 - Async Session Management Refactor)
**Root Cause:** `AsyncSession` is NOT concurrency-safe. Sharing one session across `asyncio.gather()` tasks causes:
- `sqlite3.ProgrammingError: Cannot operate on a closed database`
- `SAWarning: Attribute history events accumulated on previously clean instances`

#### The Golden Rule

**NEVER share an AsyncSession across concurrent `asyncio.gather()` tasks that write to the database.**

Each concurrent task MUST get its own session via `cache.async_session_maker()`.

#### Per-Operation Session Pattern for Batch Operations

When you need concurrent database operations (e.g., refreshing data for multiple products), create isolated sessions for each concurrent task:

**✅ CORRECT - Each concurrent operation gets its own session:**
```python
async def get_features_cached_or_refresh(self, product_ids: list[int]):
    async def refresh_product(product_id: int):
        # Each task creates its own session - SAFE
        async with self.cache.async_session_maker() as session:
            repo = FeatureRepository(session, self.client, self.customer_id)
            await repo.sync_features(product_id)  # commits internally, isolated

    # Concurrent tasks are now isolated
    results = await asyncio.gather(*[
        refresh_product(pid) for pid in products_to_refresh
    ])
```

**❌ WRONG - Shared session across asyncio.gather():**
```python
async def get_features_cached_or_refresh(self, product_ids: list[int]):
    # self.session is shared across all tasks - DANGEROUS
    results = await asyncio.gather(*[
        self.sync_features(pid) for pid in products_to_refresh
    ])
    await self.session.commit()  # Conflicts with commits inside sync_features()!
```

#### Session Lifecycle Rules

| Scenario | Pattern | Who Commits |
|----------|---------|-------------|
| **Simple operations** | Repository receives session, uses it | Repository commits |
| **Batch operations** | Repository creates new sessions per-item from `async_session_maker` | Each isolated session commits |
| **Sequential phases** | Single session passed between phases | Last operation or explicit commit |

#### SQLite Write Serialization

**Important:** SQLite serializes all write transactions, even with WAL mode enabled.

| Aspect | Behavior |
|--------|----------|
| **WAL Mode** | Allows concurrent reads during writes, but writes are still serialized |
| **`asyncio.gather()` benefit** | Overlaps API I/O (network calls), NOT parallel DB writes |
| **HTTP semaphore** | `TestIOClient` limits to ~10 concurrent API calls, naturally throttling DB commits |
| **30-second timeout** | Configured in `engine.py`; sufficient headroom for serialized commits |

**Why no DB write semaphore?** The HTTP client semaphore already throttles API calls, which means commits are naturally staggered. The 30-second timeout is sufficient as a safety net.

#### Tradeoff: Atomicity vs Availability

The per-operation session pattern sacrifices atomicity across batch operations:
- One product failing doesn't rollback others
- Partial success is better than total failure
- Sync operations are idempotent (can retry failed items)
- Each product's data is independent

This is **acceptable** for sync operations but may not be for other use cases.

#### Pattern Rejected: `async_scoped_session`

SQLAlchemy provides `async_scoped_session(session_factory, scopefunc=asyncio.current_task)` which automatically maintains one session per asyncio task. This was evaluated but **rejected** for STORY-062.

**Why it was rejected:**
- Blast radius: 6-10 files would need changes vs 2-3 methods
- Risk: Memory leaks if `.remove()` missed at any entry point
- DI changes: Would require changing all repository constructors

**Verdict:** The explicit per-task session pattern is a surgical fix. Consider `async_scoped_session` for future architectural initiatives, not bug fixes.

#### Files Using This Pattern

- `src/testio_mcp/repositories/feature_repository.py` - `get_features_cached_or_refresh()`
- `src/testio_mcp/repositories/bug_repository.py` - `get_bugs_cached_or_refresh()`

---

### References

- **SQLModel Docs:** https://sqlmodel.tiangolo.com/
- **SQLAlchemy 2.0 Async:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Lesson Learned:** Epic 006 Retrospective (STORY-034B) - Row vs ORM model confusion
- **Lesson Learned:** STORY-062 - AsyncSession concurrency issues with `asyncio.gather()`

---

## Database Migrations (ADR-016)

**Strategy:** Single-path with frozen baseline DDL and pytest-alembic CI protection.

### Adding Schema Changes

```bash
# 1. Update ORM model (e.g., add new column)
# Edit: src/testio_mcp/models/orm/product.py

# 2. Generate migration
uv run alembic revision --autogenerate -m "Add field X"

# 3. Review migration (ensure it only adds new changes, no baseline duplication)
# Edit: alembic/versions/xxxx_add_field_x.py

# 4. Run tests (catches ORM/migration drift)
uv run pytest tests/integration/test_alembic_migrations.py -v

# 5. Apply migration
uv run alembic upgrade head
```

### Key Rules

1. **NEVER edit the baseline migration** - it's frozen at a point in time (2025-11-24)
2. **ALWAYS run pytest-alembic tests** before committing migrations
3. **Use `alembic upgrade head`** for both fresh and existing databases
4. **Import new ORM models in `alembic/env.py`** for autogenerate detection

### Troubleshooting

**"duplicate column name" error:**
- If baseline were still using `metadata.create_all()` - but now it's frozen DDL
- For fresh DB, just run `alembic upgrade head`

**`test_model_definitions_match_ddl` fails:**
- ORM changed without migration
- Run `uv run alembic revision --autogenerate -m "Description"` to generate migration

**Migration chain broken:**
- Never edit or delete existing migrations
- If stuck, check `alembic history` and `alembic current`

### Fresh Database Setup

```bash
rm ~/.testio-mcp/cache.db
uv run alembic upgrade head
uv run python -m testio_mcp  # Server auto-syncs data
```

### References

- **ADR-016:** Alembic Migration Strategy (decision rationale)
- **STORY-039:** Frozen baseline implementation
- **pytest-alembic:** https://pytest-alembic.readthedocs.io/

## Testing Strategy

### Test Pyramid

```
E2E Tests (5)           - Full MCP protocol flow
Integration Tests (20)  - Tool → Service → Real API
Tool Tests (50+)        - Error handling, validation, delegation
Service Tests (80)      - Business logic with mocked client/cache
Unit Tests (30+)        - Pure functions (helpers, filters)
```

### Writing Tests

**Tool Tests (Story-016 Pattern):**
```python
# tests/unit/test_tools_get_test_bugs.py
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.tools.get_test_bugs_tool import get_test_bugs as get_test_bugs_tool

# Extract actual function from FastMCP FunctionTool wrapper
get_test_bugs = get_test_bugs_tool.fn  # type: ignore[attr-defined]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_not_found_to_tool_error() -> None:
    """Verify TestNotFoundException → ToolError with ❌ℹ️💡 format."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_test_bugs.side_effect = TestNotFoundException(test_id=123)

    with patch("testio_mcp.tools.get_test_bugs_tool.get_service", return_value=mock_service):
        with pytest.raises(ToolError) as exc_info:
            await get_test_bugs(test_id=123, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg  # Error indicator
        assert "not found" in error_msg.lower()
        assert "ℹ️" in error_msg  # Context
        assert "💡" in error_msg  # Solution
```

**Key Tool Testing Patterns:**
1. Extract function from FastMCP wrapper: `tool_fn = tool_wrapper.fn`
2. Mock context with `MagicMock()`, service with `AsyncMock()`
3. Patch `get_service()` at tool file level
4. Test error transformations (domain exceptions → ToolError)
5. Test service delegation (parameters passed correctly)

**Service Tests:**
```python
# tests/services/test_test_service.py
async def test_get_test_summary_returns_data(service, mock_test_repo):
    mock_test_repo.get_test_with_bugs.return_value = {"test": {...}}
    result = await service.get_test_summary(123)
    assert result["test"]["id"] == 123
```

**See [docs/architecture/TESTING.md](docs/architecture/TESTING.md) for comprehensive testing guide (behavioral principles, coverage targets, anti-patterns).**

## File Structure

```
src/testio_mcp/
├── __init__.py
├── __main__.py              # Entry point
├── server.py                # FastMCP server, lifespan handler
├── client.py                # TestIOClient (HTTP wrapper)
├── persistent_cache.py      # PersistentCache (SQLite)
├── config.py                # Pydantic settings
├── exceptions.py            # Domain exceptions
├── services/                # Business logic layer
│   ├── base_service.py      # BaseService (shared infrastructure)
│   ├── test_service.py      # Test operations
│   ├── product_service.py   # Product operations
│   └── report_service.py    # Report generation
├── tools/                   # MCP tool wrappers
│   ├── test_summary_tool.py
│   ├── list_tests_tool.py
│   └── product_quality_report_tool.py
└── repositories/            # SQLite data access
    ├── test_repository.py
    └── bug_repository.py

tests/
├── unit/                    # Pure function tests
├── services/                # Service layer tests (primary)
├── integration/             # Tool + service + real API
└── e2e/                     # Full MCP protocol
```

## Configuration

All configuration via environment variables. See [.env.example](.env.example) for complete reference.

**Key settings:**
- `TESTIO_CUSTOMER_API_TOKEN` - API authentication
- `TESTIO_DB_PATH` - SQLite database location (default: `~/.testio-mcp/cache.db`)
- `TESTIO_REFRESH_INTERVAL_SECONDS` - Background sync interval (default: 3600s/1 hour)
- `TESTIO_FORCE_INITIAL_SYNC` - Force initial sync on startup (default: false, use `--force-sync` flag)
- `TESTIO_PRODUCT_IDS` - Optional product filtering (comma-separated)
- `CACHE_TTL_SECONDS` - Unified staleness threshold for bugs, features, and test metadata (default: 3600s/1hour)
- `LOG_LEVEL` - Logging verbosity (INFO, DEBUG, WARNING)

**Initial Sync Flow (3 Phases - STORY-046):**
```
Phase 1: Upsert product metadata
  → Products API → Database (product names, metadata)

Phase 2: Refresh features (product catalog metadata)
  → Products → Features (always refresh on initial sync)

Phase 3: Discover new tests (incremental sync)
  → Products → Tests (new only, respects TESTIO_SYNC_SINCE)

Note: Bugs/test metadata refresh on-demand via read-through caching (ADR-017)
```

**Background Refresh Flow (3 Phases - STORY-046):**
```
Phase 1: Refresh product metadata
  → Products API → Database (products can be renamed/archived)

Phase 2: Refresh features (staleness check)
  → Products → Features (if stale > CACHE_TTL_SECONDS)

Phase 3: Discover new tests (incremental sync)
  → Products → Tests (new only)

Note: Bugs/test metadata refresh on-demand via read-through caching (ADR-017)
```

**Read-Through Caching (On-Demand):**
- `BugRepository.get_bugs_cached_or_refresh()` - Refreshes stale bugs when queried
- `TestRepository.get_tests_cached_or_refresh()` - Refreshes stale test metadata
- `FeatureRepository.get_features_cached_or_refresh()` - Refreshes stale features
- Per-entity locks prevent duplicate API calls for concurrent requests

**Setup:** Run `uvx testio-mcp setup` for interactive configuration wizard.

## Data Refresh Patterns

### MCP Tool: sync_data for Explicit Refresh Control

Use `sync_data` for explicit data refresh before reports. Background sync runs every hour.

```python
# Single product - fresh data: sync first
sync_data(product_ids=[598])
generate_quality_report(product_ids=598)

# Multi-product portfolio: sync once, report all
sync_data(product_ids=[598, 599, 600])
generate_quality_report(product_ids=[598, 599, 600])

# Specific tests only (must belong to product_ids)
generate_quality_report(product_ids=598, test_ids=[141290, 141285])

# Historical: cache is sufficient
generate_quality_report(product_ids=598, start_date="2024-01-01", end_date="2024-12-31")
```

### Performance Implications

- **With cache** (default): ~10-30s for 100+ tests
- **After sync_data**: First report uses fresh cache (~10-30s), subsequent reports instant
- **Background sync**: Runs every hour, keeps cache reasonably fresh

## Read-Through Cache & Test Mutability (ADR-017)

Understanding the caching strategy is essential for working with this codebase. The system uses a **Pull Model** (read-through caching) for efficiency.

### Test Mutability Concept

Tests have two categories based on whether their data can still change:

| Category | Statuses | Behavior |
|----------|----------|----------|
| **Mutable** | `customer_finalized`, `waiting`, `running`, `locked`, `initialized` | Data can change; cache checked for staleness |
| **Immutable** | `archived`, `cancelled` | Final states; always served from cache |

**Key Insight:** `locked` is **MUTABLE**, not immutable! Tests are auto-locked 4-6 weeks after `end_at`, but bug statuses can still change during the review period. Only when tests reach `archived` or `cancelled` do they become truly immutable.

**Source:** `src/testio_mcp/config.py` (MUTABLE_TEST_STATUSES, IMMUTABLE_TEST_STATUSES)

### Read-Through Cache Pattern (Pull Model)

```
Background Sync (every hour):                On-Demand (when queried):
┌────────────────────────────────────┐      ┌──────────────────────────────────┐
│ Phase 1: Refresh product metadata  │      │ BugRepository                    │
│ Phase 2: Refresh features (TTL)    │      │   .get_bugs_cached_or_refresh()  │
│ Phase 3: Discover new tests        │      │                                  │
│ Phase 4: REMOVED (ADR-017)         │      │ TestRepository                   │
└────────────────────────────────────┘      │   .get_tests_cached_or_refresh() │
                                            └──────────────────────────────────┘
```

- **Background sync** handles "catalog data" (products, features, new test discovery)
- **On-demand refresh** handles "query data" (bugs, test metadata) via read-through caching

### Cache Decision Logic

When a tool queries data, the repository follows this priority order:

1. **Check `force_refresh` parameter** → refresh from API
2. **Check `synced_at IS NULL`** → refresh (never synced)
3. **Check test status is immutable** (`archived`/`cancelled`) → **always use cache**
4. **Check test status is mutable** + staleness:
   - If `synced_at` > `CACHE_TTL_SECONDS` (1 hour) → **stale, refresh from API**
   - If `synced_at` < `CACHE_TTL_SECONDS` → **fresh, use cache**

**Staleness Formula:**
```
seconds_since_sync = now - synced_at
if seconds_since_sync > CACHE_TTL_SECONDS:  # default: 3600 (1 hour)
    refresh_from_api()
else:
    use_cached_data()
```

### Per-Entity Locks (Duplicate Prevention)

To prevent duplicate API calls when concurrent requests target the same entity:

```python
# In PersistentCache (src/testio_mcp/database/cache.py)
_refresh_locks: dict[tuple[int, str, int], asyncio.Lock] = {}

# Key: (customer_id, entity_type, entity_id)
lock = cache.get_refresh_lock("bug", test_id=123)
async with lock:
    await refresh_bugs_for_test(123)  # Only one request refreshes at a time
```

**How it works:**
1. Request A queries test 123's bugs → acquires lock → starts API fetch
2. Request B queries test 123's bugs → tries to acquire same lock → **WAITS**
3. Request A completes → updates cache → releases lock
4. Request B acquires lock → sees fresh cache → **skips API call**

### Performance Impact

| Metric | Before (Push Model) | After (Pull Model) |
|--------|---------------------|-------------------|
| API calls/cycle | ~1000 | ~50 |
| Sync duration | 15+ minutes | 2-5 minutes |
| Cache hit rate | N/A | ~80% typical |
| Immutable tests | Always refreshed | Always 100% cache hit |

**Reference:** See [ADR-017](docs/architecture/adrs/ADR-017-background-sync-optimization-pull-model.md) for full design rationale.

## Common Pitfalls

1. **Don't put business logic in tools** - Tools are thin wrappers; logic goes in services
2. **Don't mock FastMCP in service tests** - Test services directly with mocked client/cache
3. **Don't skip type hints** - Strict mypy is enforced (`mypy --strict`)
4. **Don't commit secrets** - Use `.env` file (gitignored), detect-secrets hook will catch violations
5. **Always use uv** - Don't use `python` or `python3` directly, use `uv run python`
6. **Don't test implementation details** - Test behavior and outcomes, not internal algorithm details

## Tool Testing Workflow

When implementing new tools, test via MCP inspector in this order:

1. **List tools** - Verify tool appears in registry
2. **Call with valid input** - Test happy path
3. **Call with invalid input** - Test error handling
4. **Call with edge cases** - Test boundary conditions

Example workflow:
```bash
# 1. List tools
npx @modelcontextprotocol/inspector --cli uv run python -m testio_mcp --method tools/list

# 2. Test valid input
npx @modelcontextprotocol/inspector --cli uv run python -m testio_mcp \
  --method tools/call --tool-name my_tool --tool-arg 'param="value"'

# 3. Test invalid input (expect error)
npx @modelcontextprotocol/inspector --cli uv run python -m testio_mcp \
  --method tools/call --tool-name my_tool --tool-arg 'param="invalid"'
```

## Documentation Reference

- **[README.md](README.md)** - User guide, features, installation, CLI reference
- **[MCP_SETUP.md](MCP_SETUP.md)** - Client configuration (Claude Code, Cursor, Inspector)
- **[docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)** - System design, data flow, component architecture
- **[docs/architecture/TESTING.md](docs/architecture/TESTING.md)** - Comprehensive testing guide (philosophy, patterns, coverage)
- **[docs/architecture/SERVICE_LAYER_SUMMARY.md](docs/architecture/SERVICE_LAYER_SUMMARY.md)** - Service pattern details
- **[docs/architecture/adrs/](docs/architecture/adrs/)** - Architecture Decision Records (ADR-001 through ADR-011)
- **[docs/stories/](docs/stories/)** - User story specifications with acceptance criteria
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and migration guides

## Pre-commit Hooks

Hooks run automatically on `git commit`:
- detect-secrets (SEC-002)
- ruff (linting + formatting)
- mypy (type checking)
- JSON/YAML/TOML validation
- trailing whitespace removal

If hooks fail, fix issues and commit again.
