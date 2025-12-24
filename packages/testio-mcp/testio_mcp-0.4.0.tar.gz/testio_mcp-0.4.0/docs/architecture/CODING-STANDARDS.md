# Coding Standards - TestIO MCP Server

## Overview

This document defines the coding standards for the TestIO MCP Server project. All code must adhere to these standards before being merged.

## Python Version

- **Minimum**: Python 3.12+
- **Rationale**: Modern type hints, better async/await support, improved error messages

## Code Quality Tools

### Ruff (Linter & Formatter)

**Required**: All code must pass `ruff format` and `ruff check` without errors.

**Configuration**: See `[tool.ruff]` in `pyproject.toml`

**Rules**:
- Line length: 100 characters max
- Use ruff format for consistent formatting (replaces black)
- Enabled lints: E, W, F, I, B, C4, UP
- Imports sorted automatically (isort replacement)

**Usage**:
```bash
# Format code
ruff format .

# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .
```

### mypy (Static Type Checker)

**Required**: All code must pass `mypy src/` with zero errors.

**Configuration**: See `[tool.mypy]` in `pyproject.toml`

**Rules**:
- **Strict mode enabled**: No implicit Any, no untyped defs
- **Type hints required** on all functions (args + return)
- **NO wildcard `ignore_missing_imports`** - use specific overrides only
- Document why overrides are needed (see AC7 policy)

**Type Hint Requirements**:
```python
# ✅ GOOD - All types specified
async def get_products(client: TestIOClient, limit: int = 10) -> dict[str, list[Product]]:
    """Fetch products from API."""
    ...

# ❌ BAD - Missing types
async def get_products(client, limit=10):
    ...
```

### Pre-commit Hooks

**Required**: All commits must pass pre-commit checks.

**Setup**:
```bash
pre-commit install
```

**Hooks**:
- ruff (format + lint)
- mypy (type check)
- forbid-files (prevent `.env` commits)
- detect-secrets (scan for tokens)

**Usage**: Hooks run automatically on `git commit`. To run manually:
```bash
pre-commit run --all-files
```

## Code Structure

### Imports

**Order** (handled automatically by ruff):
1. Standard library
2. Third-party packages
3. Local imports

**Example**:
```python
import asyncio
import logging
from typing import Any, Dict

import httpx
from pydantic import BaseModel

from testio_mcp.api.client import TestIOClient
from testio_mcp.config import settings
```

### Docstrings

**Required**: All public functions, classes, and modules must have docstrings.

**Format**: Google-style docstrings

**Example**:
```python
async def get_test_status(test_id: str) -> dict[str, Any]:
    """
    Get comprehensive status of a single exploratory test.

    Args:
        test_id: Exploratory test ID from TestIO API

    Returns:
        Dictionary with test configuration, status, and bug summary

    Raises:
        httpx.HTTPStatusError: If API returns 4xx or 5xx
        ValueError: If test_id is empty or invalid format

    Example:
        >>> status = await get_test_status("109363")
        >>> print(status["title"])
        'Evgeniya Testing'
    """
    ...
```

### Error Handling

**Required**: All errors must include helpful context.

**Example**:
```python
# ✅ GOOD - Clear, actionable error
if not test_id:
    raise ValueError(
        "test_id cannot be empty. "
        "Provide a valid exploratory test ID (e.g., '109363')"
    )

# ❌ BAD - Vague error
if not test_id:
    raise ValueError("Invalid input")
```

## Security Standards

### Token Sanitization

**Required**: API tokens must NEVER appear in logs or error messages.

**Implementation**: Use `_sanitize_token_for_logging()` helper (see AC10)

**Example**:
```python
# ✅ GOOD - Token sanitized
logger.error(f"Auth failed with token: {sanitize_token(api_token)}")
# Output: "Auth failed with token: sk_1234****"

# ❌ BAD - Token exposed
logger.error(f"Auth failed with token: {api_token}")
# Output: "Auth failed with token: sk_12345678abcdef" (SECURITY ISSUE!)
```

### Pre-commit Security Hooks

**Required**: Prevent credential leaks via automated checks.

**Hooks**:
- `forbid-files`: Blocks `.env` commits
- `detect-secrets`: Scans for API tokens, keys, secrets

**Usage**: Automatic on commit. See AC9 for setup.

## Testing Standards

### Test Organization

```
tests/
├── unit/           # Fast tests, mocked dependencies, no credentials
└── integration/    # Slow tests, real API, requires credentials
```

### Test Requirements

**Unit Tests**:
- **Required**: All code must have unit test coverage
- **Mocking**: Use `pytest-httpx` for API mocks
- **Markers**: `@pytest.mark.unit`
- **Run**: `pytest -m "not integration"`

**Integration Tests**:
- **Optional**: For critical paths only
- **Markers**: `@pytest.mark.integration` + `@pytest.mark.skipif`
- **Run**: `pytest -m integration` (requires `TESTIO_CUSTOMER_API_TOKEN`)

**Coverage Target**: ≥85% overall, ≥90% for services (see TESTING.md)

**Example**:
```python
# tests/unit/test_client.py
@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_products_success(httpx_mock):
    """Unit test with mocked API."""
    httpx_mock.add_response(json={"products": []})
    # ...

# tests/integration/test_client_integration.py
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("TESTIO_CUSTOMER_API_TOKEN"), reason="Requires API token")
@pytest.mark.asyncio
async def test_get_products_real_api():
    """Integration test with real API."""
    # ...
```

## Logging Standards

### Structured Logging

**Required**: Use structured logging (JSON format) for observability.

**Configuration**: See AC14 for JSONFormatter setup.

**Usage**:
```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD - Structured, informative
logger.info(f"API Request: GET {endpoint}")
logger.debug(f"Semaphore slots: {semaphore._value}")
logger.error(f"API Error: {status_code} for {endpoint}")

# ❌ BAD - Unstructured, vague
logger.info("Making request")
logger.error("Error occurred")
```

### Log Levels

- **DEBUG**: Detailed diagnostic info (semaphore state, request params)
- **INFO**: Key events (requests, responses, state changes)
- **WARNING**: Unexpected but handled situations
- **ERROR**: Errors that prevent operation
- **CRITICAL**: System-level failures

## Async/Await Standards

### Context Managers

**Required**: Use async context managers for resource management.

**Example**:
```python
# ✅ GOOD - Proper lifecycle management
async with TestIOClient(...) as client:
    products = await client.get("products")
# Client automatically closed

# ❌ BAD - Manual management (error-prone)
client = TestIOClient(...)
await client.__aenter__()
try:
    products = await client.get("products")
finally:
    await client.__aexit__()
```

### Concurrency Control

**Required**: Use semaphores for rate limiting (see ADR-002).

**Pattern**: Global semaphore, not per-instance (see AC11).

## Configuration Standards

### Environment Variables

**Required**: All configuration via `.env` file and `pydantic-settings`.

**Pattern**:
```python
# src/testio_mcp/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TESTIO_CUSTOMER_API_TOKEN: str  # Required
    LOG_LEVEL: str = "INFO"  # Optional with default

    class Config:
        env_file = ".env"

settings = Settings()
```

**Usage**:
```python
from testio_mcp.config import settings

client = TestIOClient(api_token=settings.TESTIO_CUSTOMER_API_TOKEN)
```

## Git Commit Standards

### Commit Messages

**Format**: `<type>: <description>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `chore`: Build/tooling

**Example**:
```
feat: add token sanitization to error messages

- Implement _sanitize_token_for_logging() helper
- Add httpx event hooks to redact Authorization header
- Add 6 security tests

Resolves: SEC-002
```

### Pre-commit Checks

**Required**: All commits must pass:
- ruff format
- ruff check
- mypy
- detect-secrets
- forbid-files

**Bypass**: Never use `--no-verify` unless explicitly approved.

## Documentation Standards

### Code Comments

**When to comment**:
- Complex algorithms
- Non-obvious business logic
- Security considerations
- Performance optimizations

**Example**:
```python
# Prevent indefinite blocking when pool is exhausted (REL-001)
# If all connections are in use, wait max 10s for one to free up
limits = httpx.Limits(max_acquire_timeout=10.0)
```

### README.md

**Required sections**:
- Installation
- Configuration
- Testing
- Development setup

## Performance Standards

### Connection Pooling

**Required**: Use persistent connection pools for HTTP clients.

**Pattern**: See AC4 for httpx.AsyncClient configuration.

### Local SQLite Datastore

**Architecture**: SQLite-first with background sync (no TTL-based caching).

**Pattern**: Use PersistentCache and repository pattern (see ARCHITECTURE.md v2.0).

**Data Flow**:
1. Query local SQLite database first (~10ms)
2. Fallback to API only if data not found (rare)
3. Background sync keeps database fresh (every hour - configurable via TESTIO_REFRESH_INTERVAL_SECONDS)

**Example**:
```python
# Service uses repository pattern (SQLite-first)
async def get_test_status(self, test_id: int) -> dict:
    # Query local database (fast)
    test = await self.test_repo.get_test_by_id(test_id)

    # Fallback to API if not in database
    if not test:
        test_data = await self.client.get(f"exploratory_tests/{test_id}")
        await self.test_repo.insert_test(test_data, product_id=test_data["product"]["id"])
        test = test_data

    return test
```

**Testing**: Use repository mocks in tests (see TESTING.md fixtures)

## Compliance Checklist

Before merging code, verify:

- [ ] `ruff format .` passes (no changes)
- [ ] `ruff check .` passes (no errors)
- [ ] `mypy src/` passes (zero errors)
- [ ] `pytest -m "not integration"` passes (unit tests)
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] No tokens in logs or error messages
- [ ] Pre-commit hooks installed and passing
- [ ] Coverage >80% (check with `pytest --cov`)

---

**Document Version**: 1.2
**Last Updated**: 2025-12-03
**Owner**: Technical Team
**Review Cycle**: Quarterly

**Changelog**:
- **v1.2 (2025-12-03):** Corrected background sync interval (1 hour - configurable via TESTIO_REFRESH_INTERVAL_SECONDS)
- **v1.1 (2025-11-18):** Updated for SQLite-first architecture
  - Coverage target: >80% → ≥85% overall, ≥90% for services
  - Caching → Local SQLite Datastore section (removed ADR-004 TTL references)
  - Added repository pattern examples
- **v1.0 (2025-11-04):** Initial version
