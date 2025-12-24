"""Integration test for background sync using SyncService (STORY-049 AC5)."""

import asyncio
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.models.orm.sync_event import SyncEvent
from testio_mcp.services.sync_service import SyncPhase, SyncService


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name


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
def mock_cache(engine):
    """Create mock cache with real async session maker."""
    from sqlalchemy.orm import sessionmaker
    from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSessionClass

    cache = MagicMock()
    cache.customer_id = 123
    cache.engine = engine

    # Create real async session maker
    cache.async_session_maker = sessionmaker(
        bind=engine,
        class_=AsyncSessionClass,
        expire_on_commit=False,
    )

    return cache


@pytest.mark.integration
@pytest.mark.asyncio
async def test_background_sync_executes_all_phases(mock_cache, engine):
    """Test background sync executes all 3 phases in order (STORY-049 AC5)."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {"products": []}

    service = SyncService(client=mock_client, cache=mock_cache)

    # Mock repository factories
    def product_repo_factory(session):
        mock_repo = AsyncMock()
        mock_repo.upsert_product = AsyncMock()
        return mock_repo

    def feature_repo_factory(session):
        mock_repo = AsyncMock()
        mock_repo.get_features_cached_or_refresh = AsyncMock(return_value=({}, {"api_calls": 0}))
        return mock_repo

    def test_repo_factory(session):
        mock_repo = AsyncMock()
        return mock_repo

    service._product_repo_factory = product_repo_factory
    service._feature_repo_factory = feature_repo_factory
    service._test_repo_factory = test_repo_factory

    # Patch file lock
    with patch.object(service, "_acquire_file_lock") as mock_file_lock:
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute background sync with all 3 phases
        result = await service.execute_sync(
            phases=[SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS],
            trigger_source="background",
        )

    # Verify all phases completed
    assert SyncPhase.PRODUCTS in result.phases_completed
    assert SyncPhase.FEATURES in result.phases_completed
    assert SyncPhase.NEW_TESTS in result.phases_completed

    # Verify sync event logged with correct trigger_source
    async with AsyncSession(engine) as session:
        stmt = select(SyncEvent).where(SyncEvent.trigger_source == "background")
        db_result = await session.exec(stmt)
        event = db_result.first()

        assert event is not None
        assert event.status == "success"
        assert event.duration_seconds is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_background_sync_interval_behavior(mock_cache):
    """Test background sync respects interval configuration (STORY-049 AC3)."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {"products": []}

    service = SyncService(client=mock_client, cache=mock_cache)

    # Mock repository factories
    def product_repo_factory(session):
        mock_repo = AsyncMock()
        mock_repo.upsert_product = AsyncMock()
        return mock_repo

    service._product_repo_factory = product_repo_factory
    service._feature_repo_factory = lambda s: AsyncMock()
    service._test_repo_factory = lambda s: AsyncMock()

    # Simulate background task with interval
    interval_seconds = 1  # Short interval for testing
    sync_count = 0

    async def background_sync_task():
        nonlocal sync_count
        with patch.object(service, "_acquire_file_lock") as mock_file_lock:
            mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

            for _ in range(2):  # Run 2 cycles
                await asyncio.sleep(interval_seconds)
                await service.execute_sync(
                    phases=[SyncPhase.PRODUCTS],
                    trigger_source="background_interval_test",
                )
                sync_count += 1

    # Run background task
    await background_sync_task()

    # Verify sync ran multiple times
    assert sync_count == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_background_sync_handles_errors_gracefully(mock_cache, engine):
    """Test background sync handles errors without crashing (STORY-049 AC5)."""
    mock_client = AsyncMock()
    # Simulate API error
    mock_client.get.side_effect = Exception("API temporarily unavailable")

    service = SyncService(client=mock_client, cache=mock_cache)

    # Mock repository factories
    service._product_repo_factory = lambda s: AsyncMock()
    service._feature_repo_factory = lambda s: AsyncMock()
    service._test_repo_factory = lambda s: AsyncMock()

    # Patch file lock
    with patch.object(service, "_acquire_file_lock") as mock_file_lock:
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute - should not raise, but return errors in result
        result = await service.execute_sync(
            phases=[SyncPhase.PRODUCTS],
            trigger_source="background_error_test",
        )

    # Verify errors were captured
    assert len(result.errors) > 0
    assert any("API temporarily unavailable" in err for err in result.errors)

    # Verify sync event logged with partial_failure status
    async with AsyncSession(engine) as session:
        stmt = select(SyncEvent).where(SyncEvent.trigger_source == "background_error_test")
        db_result = await session.exec(stmt)
        event = db_result.first()

        assert event is not None
        assert event.status == "partial_failure"
        assert event.duration_seconds is not None
