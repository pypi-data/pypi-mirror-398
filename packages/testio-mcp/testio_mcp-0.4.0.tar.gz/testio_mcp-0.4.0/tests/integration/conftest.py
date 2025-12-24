"""Shared fixtures for integration tests.

This module provides common test fixtures used across integration tests.

**Test Isolation Strategy:**

Integration tests use the `shared_cache` fixture from tests/conftest.py which:
- Creates temporary databases with tables from SQLModel.metadata.create_all()
- Uses module scope for efficiency (one database per test module)
- Avoids Alembic migrations to prevent schema drift issues
- Tests never touch user's database (~/.testio-mcp/cache.db)
- CI/CD compatible (no dependency on user environment)

**Benefits:**
- Consistent schema across all integration tests (always uses current ORM models)
- Fast (tables created from metadata once per module)
- Safe (cannot corrupt user data)
- Reproducible (same schema every run, no migration conflicts)
- No schema drift (ORM models are source of truth)

**Migration Note:**
We deliberately avoid running Alembic migrations in test fixtures because:
1. Old migrations may not match current ORM models (schema drift)
2. SQLModel.metadata.create_all() is faster and always current
3. Integration tests focus on business logic, not migration testing
4. Migration testing should be done in dedicated migration tests

**Special Cases:**
- E2E workflow tests (test_e2e_workflows.py): Module-scoped mcp_client fixture
  explicitly depends on shared_cache to ensure isolated database
- REST API tests: Use test_client fixture with function-scoped temp databases
  for isolated endpoint testing

Reference: STORY-036 (Integration Test Infrastructure Fix), Epic 006 Retrospective
"""

import gc
import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from testio_mcp.config import settings

# All integration test fixtures are now imported from tests/conftest.py:
# - shared_client: Module-scoped TestIOClient with connection pooling
# - shared_cache: Module-scoped PersistentCache with temp database
# - bug_repository: Function-scoped BugRepository instance
# - test_repository: Function-scoped TestRepository instance
# - user_repository: Function-scoped UserRepository instance


@pytest.fixture(scope="session")
def test_product_id() -> int:
    """Get test product ID from environment.

    Returns the first product ID from TESTIO_PRODUCT_ID or TESTIO_PRODUCT_IDS.
    Tests requiring a product ID should use this fixture instead of hardcoding.

    Usage:
        async def test_my_feature(test_product_id):
            result = await service.get_product(test_product_id)
    """
    # Try TESTIO_PRODUCT_ID first (single product)
    product_id = os.getenv("TESTIO_PRODUCT_ID")
    if product_id:
        return int(product_id)

    # Try TESTIO_PRODUCT_IDS (comma-separated list)
    product_ids = os.getenv("TESTIO_PRODUCT_IDS")
    if product_ids:
        first_id = product_ids.split(",")[0].strip()
        return int(first_id)

    # Fallback to settings
    if settings.TESTIO_PRODUCT_IDS:
        return settings.TESTIO_PRODUCT_IDS[0]

    pytest.skip("No test product ID available (set TESTIO_PRODUCT_ID or TESTIO_PRODUCT_IDS)")


@pytest.fixture(scope="session")
def test_product_ids() -> list[int]:
    """Get all test product IDs from environment.

    Returns all product IDs from TESTIO_PRODUCT_ID or TESTIO_PRODUCT_IDS.
    Tests requiring multiple products should use this fixture.

    Usage:
        async def test_multi_product(test_product_ids):
            for pid in test_product_ids:
                result = await service.get_product(pid)
    """
    product_ids = []

    # Try TESTIO_PRODUCT_ID first (single product)
    product_id = os.getenv("TESTIO_PRODUCT_ID")
    if product_id:
        product_ids.append(int(product_id))

    # Try TESTIO_PRODUCT_IDS (comma-separated list)
    product_ids_str = os.getenv("TESTIO_PRODUCT_IDS")
    if product_ids_str:
        product_ids.extend([int(pid.strip()) for pid in product_ids_str.split(",")])

    # Fallback to settings
    if not product_ids and settings.TESTIO_PRODUCT_IDS:
        product_ids = settings.TESTIO_PRODUCT_IDS.copy()

    if not product_ids:
        pytest.skip("No test product IDs available (set TESTIO_PRODUCT_ID or TESTIO_PRODUCT_IDS)")

    return product_ids


@pytest_asyncio.fixture(scope="function")
async def test_client(tmp_path) -> AsyncIterator[AsyncClient]:
    """Create test client with properly initialized lifespan context.

    Function-scoped fixture ensures each test gets a fresh FastAPI app instance
    with isolated resources (temp file database). This prevents test interference
    and database lock conflicts when running the full test suite.

    STORY-034B: Changed from :memory: to temp file because NullPool gives each
    connection its own separate memory database, causing "no such table" errors.

    Note: We only initialize the MCP server lifespan (resources), not the
    MCP app lifespan (session manager) since we're only testing REST endpoints.

    Usage:
        @pytest.mark.asyncio
        async def test_my_endpoint(test_client):
            response = await test_client.get("/api/products")
            assert response.status_code == 200
    """
    from sqlmodel import SQLModel

    from testio_mcp.api import api
    from testio_mcp.client import TestIOClient
    from testio_mcp.database import PersistentCache

    # Create isolated resources for this test (temp file database)
    db_file = tmp_path / "test_cache.db"

    client = TestIOClient(
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
        max_concurrent_requests=settings.MAX_CONCURRENT_API_REQUESTS,
        max_connections=settings.CONNECTION_POOL_SIZE,
        max_keepalive_connections=settings.CONNECTION_POOL_MAX_KEEPALIVE,
        timeout=settings.HTTP_TIMEOUT_SECONDS,
    )
    await client.__aenter__()

    cache = PersistentCache(
        db_path=str(db_file),  # Use temp file (not :memory:)
        client=client,
        customer_id=settings.TESTIO_CUSTOMER_ID,
    )
    await cache.initialize()

    # Create ORM tables (STORY-034B: required after ORM refactor)
    # STORY-034B-FIX: Properly dispose connection after table creation
    async with cache.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

        # Create FTS5 table (STORY-065) - Required for search integration tests
        # Note: Triggers are omitted for simplicity as test_client DB is usually empty
        await conn.execute(
            text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
                entity_type UNINDEXED,
                entity_id UNINDEXED,
                product_id UNINDEXED,
                timestamp UNINDEXED,
                title,
                content,
                tokenize='porter unicode61 remove_diacritics 2',
                prefix='2 3'
            )
        """)
        )
    # Connection automatically closed by context manager

    # Create server context manually (mimics lifespan behavior)
    # ServerContext is a TypedDict, so it must be a dict (subscriptable)
    server_ctx = {
        "testio_client": client,
        "cache": cache,
    }

    # Set app state (normally done by hybrid_lifespan)
    api.state.server_context = server_ctx
    api.state.start_time = 0.0

    async with AsyncClient(
        transport=ASGITransport(app=api, raise_app_exceptions=True), base_url="http://test"
    ) as http_client:
        yield http_client

    # Cleanup: Ensure all connections are returned to pool before disposing engine
    # SAWarning fix: Force garbage collection of any orphaned sessions before engine disposal
    gc.collect()

    await cache.close()
    await client.__aexit__(None, None, None)
