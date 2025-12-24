# Testing - TestIO MCP Server

**Purpose:** Comprehensive testing guide covering philosophy, organization, design principles, and practical workflows.

**Audience:** All developers writing tests for testio-mcp

---

## Overview & Philosophy

### Goals

1. **Fast feedback**: Unit tests complete in seconds (~2s for 388 unit tests)
2. **High confidence**: Critical paths covered by integration and E2E tests
3. **CI/CD friendly**: Tests run without external dependencies
4. **Security-first**: Security tests are mandatory, not optional
5. **Behavior over implementation**: Tests survive refactoring

### Test Philosophy

**Tests should validate WHAT the system does (behavior), not HOW it does it (implementation).**

- ✅ Assert on **observable outcomes** (return values, state changes, side effects)
- ✅ Allow **implementation flexibility** (algorithms can be optimized without breaking tests)
- ✅ Use **realistic test data** (not minimal mocks)
- ❌ Don't test **internal method calls** or **private functions**
- ❌ Don't hardcode **magic numbers** derived from implementation details

---

## Test Levels & Organization

### Test Pyramid Distribution

```
E2E Tests (15%)           - Full system journeys, MCP protocol validation
Integration Tests (35%)   - Component interactions, service layer contracts
Unit Tests (50%)          - Pure logic, business rules, isolated components
```

### Directory Structure

```
tests/
├── conftest.py                     # Shared fixtures
├── fixtures/                       # Mock data (JSON files)
├── unit/                           # Unit tests (fast, mocked, no credentials)
│   ├── test_client.py              # HTTP client behavior
│   ├── test_client_security.py     # Token sanitization (mandatory)
│   ├── test_persistent_cache.py    # SQLite cache operations
│   └── test_*_tool.py              # MCP tool wrappers
├── services/                       # Service layer tests
│   ├── test_test_service.py        # TestService business logic
│   └── test_product_service.py     # ProductService business logic
├── integration/                    # Integration tests (slow, real API)
│   └── test_*_integration.py       # Real API workflows
└── e2e/                            # End-to-end tests (MCP protocol)
    └── test_mcp_protocol.py        # Full MCP client → server flow
```

---

## Test Levels: When to Use Each

### Unit Tests (50% of test suite)

**Purpose:** Test pure logic and business rules in isolation

**Use for:** Input validation, business logic, algorithms, error handling, data transformations

**Characteristics:**
- No external dependencies (DB, API, file system)
- Fast (<1ms per test, ~0.5s for full suite)
- Easy to debug
- High coverage target (≥85%)

**Running:**
```bash
# Fast feedback loop (recommended during development)
uv run pytest -m unit              # ~0.5s

# With coverage
uv run pytest -m unit --cov=src --cov-report=html
```

### Integration Tests (35% of test suite)

**Purpose:** Test component interactions with real API

**Use for:** Service layer contracts, API integration, real data workflows

**Characteristics:**
- Real TestIO API calls (requires credentials)
- Slower (~30s for full suite)
- Validates external contracts
- Skips positive tests without `TESTIO_TEST_ID` (prevents brittle tests)

**Running:**
```bash
# All integration tests
uv run pytest -m integration

# With valid test ID for positive tests
export TESTIO_TEST_ID=109363
uv run pytest -m integration
```

### E2E Tests (15% of test suite)

**Purpose:** Validate full system journeys and MCP protocol compliance

**Use for:** MCP client → server flows, protocol validation, user journeys

**Characteristics:**
- Full stack (MCP protocol + services + API)
- Slowest (~1-2 minutes)
- Highest confidence
- Fewer tests, critical paths only

---

## Coverage & Security Targets

### Coverage Requirements

**Minimum Coverage (enforced in CI):**
- **Overall:** 85%+ (enforced via `pyproject.toml`)
- **Services:** 90%+ (business logic)
- **Tools:** 85%+ (MCP interface)
- **Cache/Client:** 85%+ (infrastructure)

**Running Coverage:**
```bash
# Unit test coverage only (fast)
uv run pytest -m unit --cov=src --cov-report=html

# Full coverage (unit + integration)
uv run pytest --cov=src --cov-report=html

# Enforce 85% threshold (fails if below)
uv run pytest -m unit --cov=src --cov-fail-under=85
```

### Security Testing (Mandatory)

**Token Sanitization Tests:**
- `test_client_security.py` - Validates tokens never appear in logs
- **Status:** Mandatory (SEC-002 compliance)
- **Coverage:** 100% required

**Example:**
```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_not_in_logs(caplog):
    """Verify API token never appears in logs."""
    client = TestIOClient(base_url="https://api.test.io", api_token="secret-token")

    # Trigger logging
    await client.get("products")

    # Verify token sanitization
    assert "secret-token" not in caplog.text
    assert "Authorization" not in caplog.text
```

---

## Core Design Principles

### 1. Test Behavior, Not Implementation

**❌ BAD - Tests implementation details:**
```python
def test_cache_uses_correct_key():
    service.get_test(123)
    # BAD: Tests internal cache key format
    cache.get.assert_called_with("test:123:status")
```

**✅ GOOD - Tests observable behavior:**
```python
async def test_get_test_returns_correct_data():
    result = await service.get_test(123)
    # GOOD: Tests what user sees
    assert result["id"] == 123
    assert result["title"] == "Expected Title"
```

### 2. Avoid Hardcoded Magic Numbers

**❌ BAD - Magic number from implementation:**
```python
def test_pagination():
    result = service.list_tests(page=1, per_page=25)
    assert len(result["tests"]) == 17  # BAD: Why 17?
```

**✅ GOOD - Assert on behavior:**
```python
def test_pagination():
    result = service.list_tests(page=1, per_page=25)
    assert len(result["tests"]) <= 25  # GOOD: Respects page size
    assert all(t["id"] for t in result["tests"])  # GOOD: Valid structure
```

### 3. Use Set Membership, Not Equality

**❌ BAD - Brittle list equality:**
```python
assert result["statuses"] == ["running", "locked", "archived"]  # BAD: Order matters
```

**✅ GOOD - Set membership:**
```python
assert set(result["statuses"]) == {"running", "locked", "archived"}  # GOOD: Order-independent
assert "running" in result["statuses"]  # GOOD: Specific assertion
```

### 4. Test Schemas, Not Data

**✅ GOOD - Schema validation:**
```python
def test_get_test_response_schema():
    result = await service.get_test(123)

    # Assert on structure (schema)
    assert "id" in result
    assert "title" in result
    assert "status" in result
    assert isinstance(result["bugs"], list)

    # Don't assert on specific data values (unless critical business rule)
```

### 5. Make Tests Self-Documenting

**✅ GOOD - Clear test names and assertions:**
```python
async def test_list_tests_filters_by_status_running():
    """Verify list_tests returns only tests with status='running'."""
    result = await service.list_tests(product_id=123, statuses=["running"])

    # Self-documenting assertion
    assert all(test["status"] == "running" for test in result["tests"]), \
        "All returned tests should have status='running'"
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **Testing Framework Behavior** | Tests pytest itself, not your code | Remove tests that validate framework features |
| **Over-Mocking** | Mocks everything, tests nothing real | Only mock external dependencies (API, DB) |
| **Testing Private Methods** | Couples tests to implementation | Test public interface only |
| **Snapshot Testing Everything** | Hides breaking changes | Use snapshots sparingly, prefer explicit assertions |
| **Hardcoded Magic Numbers** | Tests implementation, not behavior | Use set membership, schema validation |
| **Testing Internal Calls** | Brittle, breaks on refactoring | Test observable outcomes only |
| **Minimal Mock Data** | Doesn't catch edge cases | Use realistic test data |

**For detailed examples, see:** [pytest documentation](https://docs.pytest.org/en/stable/explanation/goodpractices.html)

---

## Fixtures & Test Data

### Common Fixtures

**Defined in `conftest.py`:**
```python
@pytest.fixture
def mock_testio_client():
    """Mock TestIO API client for unit tests."""
    client = AsyncMock(spec=TestIOClient)
    client.get = AsyncMock()
    client.post = AsyncMock()
    return client

@pytest.fixture
def mock_persistent_cache():
    """Mock PersistentCache for unit tests."""
    cache = AsyncMock(spec=PersistentCache)
    cache.get_connection = AsyncMock()
    return cache

@pytest.fixture
def sample_test_data():
    """Realistic test data for unit tests."""
    return {
        "id": 123,
        "title": "Sample Test",
        "status": "running",
        "bugs": [{"id": 1, "severity": "critical"}]
    }
```

### Test Data Management

**JSON Fixtures:**
- Store in `tests/fixtures/` directory
- Use realistic data from actual API responses
- Keep fixtures small (< 100 lines)

**Example:**
```python
import json
from pathlib import Path

@pytest.fixture
def load_fixture():
    def _load(filename):
        path = Path(__file__).parent / "fixtures" / filename
        return json.loads(path.read_text())
    return _load

def test_with_fixture(load_fixture):
    data = load_fixture("sample_test.json")
    result = service.process(data)
    assert result["status"] == "success"
```

---

## ORM & Repository Testing Patterns

### SQLModel Session Fixtures

**In-memory SQLite for unit tests:**
```python
@pytest_asyncio.fixture
async def async_engine():
    """In-memory SQLite engine with WAL mode."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def async_session(async_engine):
    """Async session for ORM tests (auto-rollback)."""
    async_session_maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session
        await session.rollback()  # Ensure isolation
```

### Repository Mocking Patterns

**Use `spec=AsyncSession` for isinstance checks:**
```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_repository_with_mock_session():
    # CRITICAL: Use spec=AsyncSession for isinstance to work
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)

    repo = TestRepository(
        session=mock_session,
        client=mock_client,
        customer_id=123
    )

    # Mock the exec() chain for SQLModel queries
    mock_result = AsyncMock()
    mock_result.first.return_value = Test(id=1, title="Test")
    mock_session.exec.return_value = mock_result

    result = await repo.get_by_id(1)
    assert result.id == 1
```

**Factory pattern for service tests:**
```python
@pytest.fixture
def make_service(mock_client, mock_cache):
    """Factory for creating services with mocks."""
    def _make(service_class, **overrides):
        return service_class(
            client=overrides.get("client", mock_client),
            cache=overrides.get("cache", mock_cache),
        )
    return _make

# Usage
async def test_service(make_service):
    service = make_service(TestService)
    result = await service.get_test(123)
```

### Alembic Migration Testing

**Built-in pytest-alembic tests** (see `tests/integration/test_alembic_migrations.py`):

```python
from pytest_alembic.tests import (
    test_model_definitions_match_ddl,  # ORM matches migrations
    test_single_head_revision,         # No diverging branches
    test_up_down_consistency,          # Downgrades work
    test_upgrade,                      # Upgrade path works
)

pytestmark = pytest.mark.integration
```

**Running migration tests:**
```bash
uv run pytest tests/integration/test_alembic_migrations.py -v
```

**Key rules (ADR-016):**
- ORM changes MUST have corresponding migration
- Never edit baseline migration (frozen at 2025-11-24)
- Run `test_model_definitions_match_ddl` before committing

### FTS5 Search Index Testing

**Test search index with real SQLite:**
```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_fts5_search(async_session):
    # Insert data (triggers auto-populate via SQLite triggers)
    product = Product(id=1, title="Mobile App", customer_id=123)
    async_session.add(product)
    await async_session.commit()

    # Query FTS5 index
    result = await async_session.exec(
        text("SELECT * FROM search_index WHERE search_index MATCH 'mobile'")
    )
    matches = result.all()
    assert len(matches) == 1
    assert matches[0].entity_type == "product"
```

**BM25 ranking tests:**
```python
async def test_search_ranking(search_repo):
    # Insert test data with varying relevance
    await search_repo.index_product({"id": 1, "title": "Mobile App Testing"})
    await search_repo.index_product({"id": 2, "title": "Web Testing"})

    # Search and verify ranking
    results = await search_repo.search("mobile testing")
    assert results[0]["entity_id"] == 1  # More relevant match first
```

### Common ORM Testing Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| **Missing `spec=AsyncSession`** | `isinstance()` check fails | Always use `spec=AsyncSession` |
| **Raw SQL in tests** | Creates incomplete schema | Use ORM models, not `INSERT` statements |
| **Shared session across tasks** | Concurrency errors | Create new session per concurrent task |
| **Forgetting `.first()/.all()`** | Returns `Result` not model | Always extract with `.first()`, `.one()`, `.all()` |
| **Not mocking exec chain** | `AttributeError` on mock | Mock `session.exec().first()` etc. |

---

## CI/Local Workflows

### Local Development (Fast Feedback)

```bash
# 1. TDD Loop (unit tests only)
uv run pytest -m unit --lf  # Run last failed tests
uv run pytest -m unit -k test_my_feature  # Run specific test

# 2. Pre-commit check (full suite)
uv run pytest  # All tests (~31s)

# 3. Code quality
uv run ruff check --fix
uv run ruff format
uv run mypy src/testio_mcp
```

### Performance Metrics

| Test Type | Count | Duration | Speed |
|-----------|-------|----------|-------|
| Unit tests | 138 | ~0.5s | ⚡ Lightning fast |
| Integration tests | 20 | ~30s | 🐢 Slow (API calls) |
| E2E tests | 5 | ~60s | 🐢 Slowest |
| **Total** | **163** | **~31s** | **Acceptable** |

### CI/CD Integration

**GitHub Actions:**
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv pip install -e ".[dev]"
      - name: Run unit tests
        run: uv run pytest -m unit --cov=src --cov-fail-under=85
      - name: Run integration tests
        if: github.event_name == 'push'
        env:
          TESTIO_CUSTOMER_API_TOKEN: ${{ secrets.TESTIO_API_TOKEN }}
        run: uv run pytest -m integration
```

---

## Debugging & Performance

### Pytest Debugging Options

```bash
# Show print statements
uv run pytest -s

# Stop on first failure
uv run pytest -x

# Show local variables on failure
uv run pytest -l

# Run specific test with verbose output
uv run pytest tests/unit/test_cache.py::test_get_cached_value -vv

# Debug with pdb
uv run pytest --pdb
```

### Logging in Tests

```python
def test_with_logging(caplog):
    """Capture and assert on log messages."""
    caplog.set_level(logging.INFO)

    service.do_something()

    assert "Expected log message" in caplog.text
    assert any(record.levelname == "ERROR" for record in caplog.records)
```

### Performance Targets

- **Unit test:** < 1ms per test
- **Integration test:** < 5s per test
- **E2E test:** < 30s per test
- **Full suite:** < 60s

---

## Best Practices

### Naming Conventions

```python
# Test files
test_<module>.py                    # Unit tests
test_<module>_integration.py        # Integration tests

# Test functions
test_<function>_<scenario>()        # Clear, descriptive names
test_get_test_returns_correct_data()
test_list_tests_filters_by_status()
test_create_bug_raises_validation_error()
```

### Arrange-Act-Assert Pattern

```python
async def test_get_test_status():
    # Arrange - Set up test data
    mock_client.get.return_value = {"id": 123, "status": "running"}
    service = TestService(client=mock_client, test_repo=mock_repo)

    # Act - Execute the behavior
    result = await service.get_test_status(123)

    # Assert - Verify the outcome
    assert result["id"] == 123
    assert result["status"] == "running"
```

### Test Independence

- Each test should run independently (no shared state)
- Use fixtures for setup/teardown
- Don't rely on test execution order
- Clean up resources in teardown

---

## Review Checklist

Before submitting tests:

- [ ] All tests pass (`uv run pytest`)
- [ ] Coverage ≥85% (`uv run pytest --cov=src --cov-fail-under=85`)
- [ ] Security tests included (if touching auth/tokens)
- [ ] Tests are behavioral (not implementation-focused)
- [ ] No hardcoded magic numbers
- [ ] Clear test names and docstrings
- [ ] Fixtures used for common setup
- [ ] Integration tests skip positive cases without `TESTIO_TEST_ID`
- [ ] No snapshot testing for critical schemas

---

## Migration Guide: Fixing Brittle Tests

### Step 1: Identify Brittleness

**Signs of brittle tests:**
- Breaks on refactoring (even when behavior unchanged)
- Tests internal method calls
- Hardcoded magic numbers from implementation
- Tests framework behavior

### Step 2: Understand Intent

Ask: "What behavior is this test validating?"

### Step 3: Refactor to Behavioral

Replace implementation assertions with behavioral assertions:

**Before:**
```python
def test_cache_key_format():
    service.get_test(123)
    cache.get.assert_called_with("test:123:status")  # BAD: Implementation
```

**After:**
```python
async def test_get_test_uses_cache():
    result = await service.get_test(123)
    assert result["id"] == 123  # GOOD: Behavior
    assert cache.get.call_count == 1  # GOOD: Caching happened
```

### Step 4: Validate Resilience

- Refactor implementation (change algorithm, rename methods)
- Tests should still pass if behavior unchanged

---

## Examples from Our Codebase

### Good Example: test_persistent_cache.py

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_tests_filters_by_status():
    """Verify query_tests returns only tests matching status filter."""
    # Arrange
    cache = PersistentCache(db_path=":memory:", customer_id=1)
    await cache.initialize()
    await cache.upsert_test({"id": 1, "status": "running"})
    await cache.upsert_test({"id": 2, "status": "locked"})

    # Act
    result = await cache.query_tests(statuses=["running"])

    # Assert - Behavioral validation
    assert len(result["tests"]) == 1
    assert result["tests"][0]["status"] == "running"
```

**Why it's good:**
- ✅ Tests observable behavior (filtering works)
- ✅ Uses realistic test data
- ✅ Clear arrange-act-assert structure
- ✅ Self-documenting assertions

---

## Continuous Improvement

### Test Metrics to Monitor

- **Coverage:** Track per-module coverage trends
- **Duration:** Alert if test suite exceeds 60s
- **Flakiness:** Track intermittent failures
- **Maintenance:** Track test changes per feature change

---

## Resources

**External Documentation:**
- [pytest documentation](https://docs.pytest.org/en/stable/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

**Internal Documentation:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CODING-STANDARDS.md](CODING-STANDARDS.md) - Code style guide
- [SECURITY.md](SECURITY.md) - Security testing requirements

---

**Document Version:** 2.1
**Last Updated:** 2025-12-03
**Changes:** Added ORM & Repository Testing Patterns section (SQLModel fixtures, Alembic, FTS5)
