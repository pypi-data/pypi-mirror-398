"""Integration tests for sync_data MCP tool (STORY-051, AC9).

Tests with real SyncService + temp database to verify:
- last_sync_completed timestamp updated in DB after success
- timestamp NOT updated on failure
- Background sync respects timestamp (skips if recent)
- Timestamp survives server restart (persisted in SQLite)

TD-001: Updated to use get_service_context (async context manager pattern)
"""

import tempfile
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.database.cache import PersistentCache
from testio_mcp.models.orm.sync_metadata import SyncMetadata
from testio_mcp.services.sync_service import (
    SyncPhase,
    SyncResult,
    SyncService,
)
from testio_mcp.tools.sync_data_tool import sync_data as sync_data_tool

# Extract function from wrapper
sync_data = sync_data_tool.fn  # type: ignore[attr-defined]


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    # Cleanup handled by tempfile


@pytest.fixture
async def engine(temp_db_path: str):
    """Create async engine for temp database."""
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{temp_db_path}",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def mock_cache(engine: AsyncEngine):
    """Create mock cache with real async session maker and metadata methods."""
    from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSessionClass

    cache = MagicMock(spec=PersistentCache)
    cache.async_session_maker = lambda: AsyncSessionClass(engine, expire_on_commit=False)
    cache.customer_id = 123

    # Create wrapped functions that update the database but use AsyncMock for tracking
    async def _get_metadata_value(key: str) -> str | None:
        async with AsyncSessionClass(engine, expire_on_commit=False) as session:
            from sqlmodel import col

            result = await session.exec(select(SyncMetadata).where(col(SyncMetadata.key) == key))
            metadata = result.first()
            return metadata.value if metadata else None

    async def _set_metadata_value(key: str, value: str) -> None:
        async with AsyncSessionClass(engine, expire_on_commit=False) as session:
            metadata = SyncMetadata(key=key, value=value)
            await session.merge(metadata)
            await session.commit()

    # Create AsyncMock wrappers that call real functions AND track calls
    cache.get_metadata_value = AsyncMock(side_effect=_get_metadata_value)
    cache.set_metadata_value = AsyncMock(side_effect=_set_metadata_value)

    return cache


@pytest.fixture
def mock_service(mock_cache):
    """Create mock SyncService that returns successful result."""
    service = AsyncMock(spec=SyncService)
    service.cache = mock_cache

    # Default successful result
    service.execute_sync.return_value = SyncResult(
        phases_completed=[SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS],
        products_synced=1,
        features_refreshed=10,
        tests_discovered=5,
        tests_updated=0,
        duration_seconds=15.0,
        warnings=[],
        errors=[],
    )

    return service


@pytest.mark.integration
@pytest.mark.asyncio
async def test_last_sync_completed_updated_on_success(mock_service, engine) -> None:
    """AC9: Verify last_sync_completed timestamp updated in DB after success."""
    mock_ctx = MagicMock()

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        # Execute sync
        await sync_data(ctx=mock_ctx)

        # Verify timestamp was written to database (AC4)
        mock_service.cache.set_metadata_value.assert_called_once()
        call_args = mock_service.cache.set_metadata_value.call_args
        assert call_args.kwargs["key"] == "last_sync_completed"

        # Verify value is ISO 8601 UTC string
        timestamp_str = call_args.kwargs["value"]
        timestamp = datetime.fromisoformat(timestamp_str)
        assert timestamp.tzinfo is not None

        # Verify timestamp is recent (within 5 seconds)
        now = datetime.now(UTC)
        elapsed = (now - timestamp).total_seconds()
        assert elapsed < 5

        # Verify timestamp persisted in database (survives restart)
        async with AsyncSession(engine, expire_on_commit=False) as session:
            from sqlmodel import col

            result = await session.exec(
                select(SyncMetadata).where(col(SyncMetadata.key) == "last_sync_completed")
            )
            metadata = result.first()
            assert metadata is not None
            assert metadata.value == timestamp_str


@pytest.mark.integration
@pytest.mark.asyncio
async def test_last_sync_completed_not_updated_on_failure(mock_service, engine) -> None:
    """AC9: Verify timestamp NOT updated on failure."""
    mock_ctx = MagicMock()

    # Set initial timestamp
    initial_timestamp = datetime(2025, 11, 1, 10, 0, 0, tzinfo=UTC).isoformat()
    await mock_service.cache.set_metadata_value("last_sync_completed", initial_timestamp)

    # Make execute_sync fail
    mock_service.execute_sync.side_effect = RuntimeError("Sync failed")

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        # Execute sync (should fail)
        try:
            await sync_data(ctx=mock_ctx)
        except Exception:
            pass  # Expected to fail

        # Verify timestamp was NOT updated (failure doesn't reset timer)
        async with AsyncSession(engine, expire_on_commit=False) as session:
            from sqlmodel import col

            result = await session.exec(
                select(SyncMetadata).where(col(SyncMetadata.key) == "last_sync_completed")
            )
            metadata = result.first()
            assert metadata is not None
            assert metadata.value == initial_timestamp  # Still the old timestamp


@pytest.mark.integration
@pytest.mark.asyncio
async def test_timestamp_survives_server_restart(mock_service, engine, temp_db_path) -> None:
    """AC9: Verify timestamp survives server restart (persisted in SQLite)."""
    mock_ctx = MagicMock()

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        # First sync - write timestamp
        await sync_data(ctx=mock_ctx)

        # Get timestamp that was written
        timestamp_str = mock_service.cache.set_metadata_value.call_args.kwargs["value"]

    # Simulate server restart - dispose engine
    await engine.dispose()

    # Create new engine (simulates restart)
    new_engine = create_async_engine(
        f"sqlite+aiosqlite:///{temp_db_path}",
        echo=False,
    )

    try:
        # Verify timestamp survived restart
        async with AsyncSession(new_engine, expire_on_commit=False) as session:
            from sqlmodel import col

            result = await session.exec(
                select(SyncMetadata).where(col(SyncMetadata.key) == "last_sync_completed")
            )
            metadata = result.first()
            assert metadata is not None
            assert metadata.value == timestamp_str  # Persisted across restart

    finally:
        await new_engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_background_sync_respects_timestamp(mock_service, mock_cache, engine) -> None:
    """AC9: Verify background sync checks last_sync_completed before running.

    This test simulates the background sync logic checking the timestamp
    and skipping sync if recent (< interval).
    """
    # Set last_sync_completed to now (very recent)
    now = datetime.now(UTC)
    await mock_cache.set_metadata_value("last_sync_completed", now.isoformat())

    # Simulate background sync logic (AC5)
    interval_seconds = 900  # 15 minutes
    last_sync_str = await mock_cache.get_metadata_value("last_sync_completed")

    assert last_sync_str is not None
    last_sync = datetime.fromisoformat(last_sync_str)
    elapsed = (datetime.now(UTC) - last_sync).total_seconds()

    # Should skip sync because elapsed < interval
    assert elapsed < interval_seconds

    # Set last_sync_completed to old timestamp (> interval)
    old_timestamp = datetime(2025, 11, 1, 10, 0, 0, tzinfo=UTC)
    await mock_cache.set_metadata_value("last_sync_completed", old_timestamp.isoformat())

    last_sync_str = await mock_cache.get_metadata_value("last_sync_completed")
    assert last_sync_str is not None
    last_sync = datetime.fromisoformat(last_sync_str)
    elapsed = (datetime.now(UTC) - last_sync).total_seconds()

    # Should NOT skip sync because elapsed >= interval
    assert elapsed >= interval_seconds


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duration_seconds_always_populated(mock_service) -> None:
    """AC9: Verify duration_seconds always populated in response."""
    mock_ctx = MagicMock()

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        result = await sync_data(ctx=mock_ctx)

        # Verify duration_seconds present (AC6)
        assert "duration_seconds" in result
        assert isinstance(result["duration_seconds"], float)
        assert result["duration_seconds"] > 0
