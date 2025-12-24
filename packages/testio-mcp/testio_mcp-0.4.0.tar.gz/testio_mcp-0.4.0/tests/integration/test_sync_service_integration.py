"""Integration tests for SyncService (STORY-048, AC3, AC7).

Tests with real SQLite (temp file) to verify:
- Phases execute in order
- Sync events logged correctly to database
- Duration always populated
"""

import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.models.orm.sync_event import SyncEvent
from testio_mcp.services.sync_service import (
    SyncPhase,
    SyncResult,
    SyncScope,
    SyncService,
)


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
    """Create mock cache with real async session maker."""
    from sqlmodel.ext.asyncio.session import AsyncSession as AsyncSessionClass

    cache = MagicMock()
    cache.customer_id = 123
    cache.engine = engine

    # Create real async session maker
    from sqlalchemy.orm import sessionmaker

    cache.async_session_maker = sessionmaker(
        bind=engine,
        class_=AsyncSessionClass,
        expire_on_commit=False,
    )

    return cache


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_sync_logs_sync_events(mock_cache, engine):
    """Verify execute_sync logs sync events to database."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {"products": []}

    service = SyncService(client=mock_client, cache=mock_cache)

    # Use factory functions that return AsyncMock repos
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

    # Patch file lock to avoid actual file operations
    with patch.object(service, "_acquire_file_lock") as mock_file_lock:
        # Make file lock work as context manager
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act
        await service.execute_sync(
            phases=[SyncPhase.PRODUCTS],
            trigger_source="integration_test",
        )

    # Assert - Check sync event was logged
    async with AsyncSession(engine) as session:
        stmt = select(SyncEvent).order_by(SyncEvent.id.desc())
        db_result = await session.exec(stmt)
        event = db_result.first()

        assert event is not None
        assert event.event_type == "sync"
        assert event.status == "success"
        assert event.trigger_source == "integration_test"
        assert event.duration_seconds is not None
        assert event.duration_seconds >= 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_sync_phases_in_order(mock_cache):
    """Verify phases execute in PRODUCTS -> FEATURES -> NEW_TESTS order."""
    mock_client = AsyncMock()

    execution_order: list[SyncPhase] = []

    service = SyncService(client=mock_client, cache=mock_cache)

    async def track_phase(phase, scope, options, session, progress):
        execution_order.append(phase)
        return SyncResult()

    with (
        patch.object(service, "_acquire_file_lock") as mock_file_lock,
        patch.object(service, "_execute_single_phase", side_effect=track_phase),
        patch.object(service, "_log_sync_start", return_value=1),
        patch.object(service, "_log_sync_completion"),
    ):
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act - pass phases in reverse order
        await service.execute_sync(
            phases=[SyncPhase.NEW_TESTS, SyncPhase.PRODUCTS, SyncPhase.FEATURES]
        )

    # Assert - phases executed in correct order
    assert execution_order == [
        SyncPhase.PRODUCTS,
        SyncPhase.FEATURES,
        SyncPhase.NEW_TESTS,
    ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_sync_duration_always_populated(mock_cache):
    """Verify SyncResult.duration_seconds is always populated."""
    mock_client = AsyncMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    # Mock to complete quickly
    async def fast_phase(phase, scope, options, session, progress):
        return SyncResult()

    with (
        patch.object(service, "_acquire_file_lock") as mock_file_lock,
        patch.object(service, "_execute_single_phase", side_effect=fast_phase),
        patch.object(service, "_log_sync_start", return_value=1),
        patch.object(service, "_log_sync_completion"),
    ):
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await service.execute_sync(phases=[SyncPhase.PRODUCTS])

    # Assert - duration is > 0
    assert result.duration_seconds >= 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_execute_sync_full_flow_with_mocked_api(mock_cache, engine):
    """Integration test: Full sync flow with mocked API but real database."""
    mock_client = AsyncMock()

    # Mock API responses
    mock_client.get.side_effect = lambda endpoint: {
        "products": {"products": [{"id": 598, "name": "Test Product"}]},
        "products/598/features": {"features": []},
        "products/598/exploratory_tests": {"exploratory_tests": []},
    }.get(endpoint, {})

    service = SyncService(client=mock_client, cache=mock_cache)

    # Create repository factories that work with real session
    def product_repo_factory(session):
        mock_repo = AsyncMock()
        mock_repo.upsert_product = AsyncMock()
        mock_repo.commit = AsyncMock()
        return mock_repo

    def feature_repo_factory(session):
        mock_repo = AsyncMock()
        mock_repo.get_features_cached_or_refresh = AsyncMock(
            return_value=({598: []}, {"api_calls": 1})
        )
        return mock_repo

    def test_repo_factory(session):
        mock_repo = AsyncMock()
        mock_repo.test_exists = AsyncMock(return_value=False)
        mock_repo.insert_test = AsyncMock()
        return mock_repo

    service._product_repo_factory = product_repo_factory
    service._feature_repo_factory = feature_repo_factory
    service._test_repo_factory = test_repo_factory

    with patch.object(service, "_acquire_file_lock") as mock_file_lock:
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act
        result = await service.execute_sync(
            phases=[SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS],
            scope=SyncScope(product_ids=[598]),
            trigger_source="integration_full_flow",
        )

    # Assert - all phases completed
    assert SyncPhase.PRODUCTS in result.phases_completed
    assert SyncPhase.FEATURES in result.phases_completed
    assert SyncPhase.NEW_TESTS in result.phases_completed

    # Assert - sync event logged
    async with AsyncSession(engine) as session:
        stmt = select(SyncEvent).where(SyncEvent.trigger_source == "integration_full_flow")
        db_result = await session.exec(stmt)
        events = db_result.all()

        assert len(events) >= 1
        # Find the completion event
        completion_event = next(
            (e for e in events if e.status in ("success", "partial_failure")), None
        )
        assert completion_event is not None
        assert completion_event.duration_seconds is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_event_records_stats(mock_cache, engine):
    """Verify sync event records stats like products_synced, features_refreshed."""
    mock_client = AsyncMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    # Mock repositories to return specific counts
    def product_repo_factory(session):
        mock_repo = AsyncMock()
        mock_repo.upsert_product = AsyncMock()
        mock_repo.get_all_products = AsyncMock(return_value=[{"id": 1}, {"id": 2}])
        return mock_repo

    def feature_repo_factory(session):
        mock_repo = AsyncMock()
        # Mock returns features dict with one feature per product
        mock_repo.get_features_cached_or_refresh = AsyncMock(
            return_value=(
                {1: [{"id": 1, "title": "Feature 1"}], 2: [{"id": 2, "title": "Feature 2"}]},
                {"api_calls": 2},
            )
        )
        return mock_repo

    service._product_repo_factory = product_repo_factory
    service._feature_repo_factory = feature_repo_factory

    # Mock client for products phase
    mock_client.get.return_value = {
        "products": [
            {"id": 1, "name": "Product 1"},
            {"id": 2, "name": "Product 2"},
            {"id": 3, "name": "Product 3"},
        ]
    }

    with patch.object(service, "_acquire_file_lock") as mock_file_lock:
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await service.execute_sync(
            phases=[SyncPhase.PRODUCTS, SyncPhase.FEATURES],
            trigger_source="stats_test",
        )

    # Assert - stats recorded
    assert result.products_synced == 3
    assert result.features_refreshed == 2

    # Assert - sync event has stats
    async with AsyncSession(engine) as session:
        stmt = select(SyncEvent).where(SyncEvent.trigger_source == "stats_test")
        db_result = await session.exec(stmt)
        event = db_result.first()

        assert event is not None
        assert event.products_synced == 3
        assert event.features_refreshed == 2
