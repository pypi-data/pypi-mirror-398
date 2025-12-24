"""Shared pytest fixtures for unit and integration tests.

This module provides:
1. Unit test fixtures: Mock client and cache for fast, isolated service tests
2. Integration test fixtures: Real client and cache for end-to-end testing

Benefits:
- Eliminates fixture duplication across test files
- Faster test execution (connection pool reuse per test module)
- More accurate simulation of production server behavior
- Reduced load on staging API (fewer connections)
- No pytest-asyncio session-scope complexity

Note: Module scope (not session scope) avoids pytest-asyncio event loop
teardown issues while still providing substantial performance benefits.

Reference: Story-003c optimization recommendations, Story-012 AC3
"""

import gc
import os
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import text

# CRITICAL: Load repo .env BEFORE importing settings
# Tests must use repo .env, not ~/.testio-mcp.env (which takes precedence in CLI)
# This ensures consistent test environment regardless of developer's global config

repo_root = Path(__file__).parent.parent
repo_env = repo_root / ".env"
if repo_env.exists():
    load_dotenv(repo_env, override=True)

# Set environment variable BEFORE importing (Pydantic reads on import)
os.environ["TESTIO_REFRESH_INTERVAL_SECONDS"] = "0"

from testio_mcp.client import TestIOClient  # noqa: E402
from testio_mcp.config import settings  # noqa: E402
from testio_mcp.database import PersistentCache  # noqa: E402
from testio_mcp.services.base_service import BaseService  # noqa: E402

# CRITICAL: Override settings after import to ensure background refresh is disabled
# The settings object is created at import time, but we can modify it
# This prevents background tasks from running and hanging pytest
settings.TESTIO_REFRESH_INTERVAL_SECONDS = 0

# STORY-030: ORM fixtures (deferred imports to avoid circular dependencies)
# AsyncEngine and AsyncSession will be imported in fixture functions


@pytest_asyncio.fixture(scope="module")
async def shared_client() -> AsyncIterator[TestIOClient]:
    """Shared TestIOClient for integration tests (mimics server lifespan).

    This fixture creates a TestIOClient instance that is reused across
    all integration tests in the same module, mimicking the server's lifespan
    pattern where a single client is created on startup.

    Benefits:
    - Connection pool reused across all tests in the module
    - Faster test execution (no connection setup/teardown per test)
    - Matches production server behavior
    - Avoids pytest-asyncio session-scope event loop issues

    Yields:
        TestIOClient instance with connection pooling
    """
    async with TestIOClient(
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
        max_concurrent_requests=settings.MAX_CONCURRENT_API_REQUESTS,
        max_connections=settings.CONNECTION_POOL_SIZE,
        max_keepalive_connections=settings.CONNECTION_POOL_MAX_KEEPALIVE,
        timeout=settings.HTTP_TIMEOUT_SECONDS,
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="module")
async def shared_cache(
    shared_client: TestIOClient, tmp_path_factory
) -> AsyncIterator[PersistentCache]:
    """Shared PersistentCache for integration tests (STORY-021 AC5).

    This fixture creates a PersistentCache instance with a temp file database
    that is reused across all integration tests in the same module.

    NOTE: Previously used :memory: but that doesn't work with NullPool.
    Each async connection gets its own memory database, so tables created
    in one connection aren't visible in another. Using temp file instead.

    Benefits:
    - Fast execution (temp file on disk)
    - Test isolation (fresh database per module)
    - Matches production server behavior (PersistentCache API)
    - Works with NullPool (required for async SQLite)

    Yields:
        PersistentCache instance with temp file database

    """

    # Create temp database file (tmp_path_factory provides module-scoped temp dir)
    tmp_dir = tmp_path_factory.mktemp("cache")
    db_file = tmp_dir / "test_cache.db"

    # Create cache but DON'T initialize yet (we need to create tables first)
    from sqlmodel import SQLModel

    from testio_mcp.database.engine import (
        create_async_engine_for_sqlite,
        create_session_factory,
    )
    from testio_mcp.models import orm  # noqa: F401 - Import to register models with metadata

    # Manually create engine and session factory
    engine = create_async_engine_for_sqlite(db_file)
    async_session_maker = create_session_factory(engine)

    # Create all tables from ORM models
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

        # Create FTS5 table (STORY-065) - Required for search integration tests
        # Note: Triggers are omitted for simplicity as shared_cache is usually empty
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

    # Now create cache with pre-configured engine
    cache = PersistentCache(
        db_path=str(db_file),
        client=shared_client,
        customer_id=settings.TESTIO_CUSTOMER_ID,
    )

    # Manually set engine and session maker (skip cache.initialize() which expects migrations)
    cache.engine = engine
    cache.async_session_maker = async_session_maker

    # Create repository with session (like cache.initialize() does)
    # Note: Some integration tests depend on cache.repo being available
    from testio_mcp.repositories.test_repository import TestRepository

    cache._cache_session = cache.async_session_maker()
    cache.repo = TestRepository(
        session=cache._cache_session, client=shared_client, customer_id=cache.customer_id
    )

    yield cache

    # Cleanup: Ensure all aiosqlite background threads complete before event loop closes
    # This is critical for preventing "RuntimeError: Event loop is closed" warnings
    import asyncio

    # Step 1: Close cache session first (if not already closed)
    if cache._cache_session:
        await cache._cache_session.close()

    # Step 2: Force garbage collection to finalize any pending session closes
    # This triggers __del__ on any unclosed sessions from tests
    gc.collect()

    # Step 3: Give aiosqlite threads substantial time to complete their work
    # 0.5s is generous but necessary when running full test suite with many modules
    await asyncio.sleep(0.5)

    # Step 4: Dispose engine and wait for all connections to close
    await cache.close()

    # Step 5: Final gc.collect() and yield to ensure all cleanup callbacks complete
    gc.collect()
    await asyncio.sleep(0)


@pytest_asyncio.fixture(scope="function")
async def bug_repository(shared_cache: PersistentCache, shared_client: TestIOClient):
    """Create BugRepository instance for integration tests (STORY-034B).

    Provides a properly configured BugRepository with AsyncSession for tests
    that need direct repository access.

    Note: Most tests should use services instead of repositories directly.
    """
    from testio_mcp.repositories.bug_repository import BugRepository

    async with shared_cache.async_session_maker() as session:
        repo = BugRepository(
            session=session,
            client=shared_client,
            customer_id=shared_cache.customer_id,
            cache=shared_cache,  # Required for decoupled API/DB pattern (STORY-062 follow-up)
        )
        yield repo


# ==========================================
# Unit Test Fixtures (Story-012 AC3)
# ==========================================


@pytest.fixture
def mock_client() -> AsyncMock:
    """Shared mock TestIO client for all unit tests.

    Provides a pre-configured AsyncMock with TestIOClient spec for use in
    service unit tests. This fixture eliminates duplication of mock client
    setup across test files.

    Returns:
        AsyncMock instance with TestIOClient spec

    Example:
        >>> async def test_service(mock_client):
        ...     mock_client.get.return_value = {"id": 123}
        ...     service = TestService(client=mock_client, cache=mock_cache())
        ...     result = await service.get_test_status(123)
    """
    return AsyncMock(spec=TestIOClient)


@pytest.fixture
def mock_cache() -> AsyncMock:
    """Shared mock cache for all unit tests (STORY-021 AC5).

    Provides a pre-configured AsyncMock with PersistentCache spec for use in
    service unit tests. This fixture eliminates duplication of mock cache
    setup across test files.

    Returns:
        AsyncMock instance with PersistentCache spec

    Example:
        >>> async def test_service(mock_cache):
        ...     mock_cache.query_tests.return_value = []  # No tests found
        ...     service = TestService(client=mock_client(), cache=mock_cache)
        ...     result = await service.list_tests(product_id=123)
    """
    return AsyncMock(spec=PersistentCache)


@pytest.fixture
def make_service(mock_client: AsyncMock, mock_cache: AsyncMock):
    """Factory for creating service instances in tests.

    Provides a factory function that creates service instances with
    pre-configured mock dependencies. This eliminates the need for
    per-service fixtures in test files.

    Args:
        mock_client: Mock client fixture (auto-injected)
        mock_cache: Mock cache fixture (auto-injected)

    Returns:
        Factory function that creates service instances

    Example:
        >>> async def test_get_test_status(make_service, mock_client):
        ...     service = make_service(TestService)
        ...     mock_client.get.return_value = {"id": 123}
        ...     result = await service.get_test_status(123)
    """

    def _factory(service_class: type[BaseService]) -> BaseService:
        return service_class(client=mock_client, cache=mock_cache)

    return _factory


# ==========================================
# ORM Test Fixtures (STORY-030 AC5)
# ==========================================


@pytest_asyncio.fixture(scope="module")
async def async_engine():
    """Shared async engine for ORM tests.

    Creates an in-memory SQLite database with async support for testing
    SQLModel/SQLAlchemy operations.

    Yields:
        AsyncEngine instance configured for in-memory database

    Note:
        Uses module scope to share engine across tests in same module.
        In-memory database ensures test isolation.
    """
    from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
    from sqlalchemy.pool import NullPool

    engine: AsyncEngine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
        poolclass=NullPool,
        connect_args={"check_same_thread": False},
    )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Async session for ORM tests (STORY-030 AC5).

    Creates a new AsyncSession for each test. Session is automatically
    rolled back after test completion to ensure test isolation.

    Args:
        async_engine: Async engine fixture (auto-injected)

    Yields:
        AsyncSession instance

    Example:
        >>> async def test_query_product(async_session):
        ...     result = await async_session.exec(select(Product))
        ...     products = result.all()
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from sqlmodel.ext.asyncio.session import AsyncSession

    session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        await session.rollback()  # Rollback to ensure test isolation


@pytest.fixture
def mock_async_session() -> AsyncMock:
    """Mock AsyncSession for unit tests.

    Provides a pre-configured AsyncMock with AsyncSession spec for use in
    unit tests that need to mock ORM operations.

    Returns:
        AsyncMock instance with AsyncSession spec

    Example:
        >>> async def test_repository(mock_async_session):
        ...     mock_async_session.execute.return_value = AsyncMock(scalars=...)
        ...     repo = ProductRepository(session=mock_async_session)
        ...     result = await repo.get_product(123)
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    return AsyncMock(spec=AsyncSession)


# ==========================================
# Alembic Migration Test Fixtures (STORY-039, ADR-016)
# ==========================================


@pytest.fixture
def alembic_config():
    """Configure pytest-alembic for testing migrations (STORY-039).

    Returns pytest-alembic Config with default settings.
    The alembic.ini file is automatically discovered in the project root.

    Reference: https://pytest-alembic.readthedocs.io/en/latest/
    """
    from pytest_alembic.config import Config

    return Config()


@pytest.fixture
def alembic_engine(tmp_path):
    """Provide async database engine for alembic tests (STORY-039).

    Uses file-based SQLite with aiosqlite for migration tests.
    In-memory SQLite doesn't work well with pytest-alembic due to
    connection pooling - each connection gets its own :memory: database.

    Reference: https://pytest-alembic.readthedocs.io/en/latest/asyncio.html

    Args:
        tmp_path: pytest fixture providing temporary directory

    Returns:
        AsyncEngine configured for file-based SQLite database
    """
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    db_path = tmp_path / "alembic_test.db"
    return create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        echo=False,
        poolclass=NullPool,  # Required for pytest-alembic async support
    )
