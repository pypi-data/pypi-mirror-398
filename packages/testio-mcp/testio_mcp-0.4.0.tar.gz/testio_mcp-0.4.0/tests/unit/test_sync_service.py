"""Unit tests for SyncService (STORY-048).

Tests cover:
- AC1: SyncService class exists and inherits from BaseService
- AC2: Data model serialization (SyncPhase, SyncScope, SyncOptions, SyncResult)
- AC3: execute_sync() phase orchestration
- AC4: File lock acquisition and timeout
- AC5: Stale lock recovery
- AC6: Asyncio lock for in-process serialization
- AC7: Sync event logging
- AC8: Mock repository delegation

Coverage target: >= 90% for sync_service.py
"""

import asyncio
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from testio_mcp.services.sync_service import (
    SyncLockError,
    SyncOptions,
    SyncPhase,
    SyncResult,
    SyncScope,
    SyncService,
    SyncTimeoutError,
)
from testio_mcp.utilities.progress import ProgressReporter

# =============================================================================
# AC1: SyncService class exists and inherits from BaseService
# =============================================================================


@pytest.mark.unit
def test_sync_service_exists():
    """Verify SyncService class can be imported from services module."""
    from testio_mcp.services import SyncService

    assert SyncService is not None


@pytest.mark.unit
def test_sync_service_inherits_from_base_service():
    """Verify SyncService inherits from BaseService."""
    from testio_mcp.services.base_service import BaseService

    assert issubclass(SyncService, BaseService)


# =============================================================================
# AC2: Data model serialization
# =============================================================================


@pytest.mark.unit
def test_sync_phase_enum_values():
    """Verify SyncPhase enum has correct values."""
    assert SyncPhase.PRODUCTS.value == "products"
    assert SyncPhase.FEATURES.value == "features"
    assert SyncPhase.NEW_TESTS.value == "new_tests"


@pytest.mark.unit
def test_sync_phase_is_string_enum():
    """Verify SyncPhase is a string enum for JSON serialization."""
    # String enum allows direct JSON serialization
    assert isinstance(SyncPhase.PRODUCTS.value, str)
    assert str(SyncPhase.PRODUCTS) == "SyncPhase.PRODUCTS"


@pytest.mark.unit
def test_sync_scope_defaults():
    """Verify SyncScope has correct default values."""
    scope = SyncScope()

    assert scope.product_ids is None
    assert scope.since_date is None
    assert scope.entity_types is None


@pytest.mark.unit
def test_sync_scope_with_values():
    """Verify SyncScope accepts values correctly."""
    since = datetime(2025, 1, 1, tzinfo=UTC)
    scope = SyncScope(
        product_ids=[598, 1024],
        since_date=since,
        entity_types=["tests"],
    )

    assert scope.product_ids == [598, 1024]
    assert scope.since_date == since
    assert scope.entity_types == ["tests"]


@pytest.mark.unit
def test_sync_options_defaults():
    """Verify SyncOptions has correct default values."""
    options = SyncOptions()

    assert options.force_refresh is False
    assert options.incremental_only is False
    assert options.nuke is False


@pytest.mark.unit
def test_sync_options_with_values():
    """Verify SyncOptions accepts values correctly."""
    options = SyncOptions(
        force_refresh=True,
        incremental_only=True,
        nuke=True,
    )

    assert options.force_refresh is True
    assert options.incremental_only is True
    assert options.nuke is True


@pytest.mark.unit
def test_sync_result_defaults():
    """Verify SyncResult has correct default values."""
    result = SyncResult()

    assert result.phases_completed == []
    assert result.products_synced == 0
    assert result.features_refreshed == 0
    assert result.tests_discovered == 0
    assert result.tests_updated == 0
    assert result.duration_seconds == 0.0
    assert result.warnings == []
    assert result.errors == []


@pytest.mark.unit
def test_sync_result_with_values():
    """Verify SyncResult accepts values correctly."""
    result = SyncResult(
        phases_completed=[SyncPhase.PRODUCTS, SyncPhase.FEATURES],
        products_synced=5,
        features_refreshed=10,
        tests_discovered=20,
        tests_updated=3,
        duration_seconds=45.2,
        warnings=["Warning 1"],
        errors=["Error 1"],
    )

    assert len(result.phases_completed) == 2
    assert result.products_synced == 5
    assert result.features_refreshed == 10
    assert result.tests_discovered == 20
    assert result.tests_updated == 3
    assert result.duration_seconds == 45.2
    assert result.warnings == ["Warning 1"]
    assert result.errors == ["Error 1"]


@pytest.mark.unit
def test_sync_result_duration_always_populated():
    """Verify SyncResult.duration_seconds is always populated (AC2 requirement)."""
    result = SyncResult()
    # duration_seconds has a default of 0.0, ensuring it's always populated
    assert result.duration_seconds is not None
    assert isinstance(result.duration_seconds, float)


# =============================================================================
# AC3: execute_sync() phase orchestration
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_sync_phase_ordering():
    """Verify phases execute in order: PRODUCTS -> FEATURES -> NEW_TESTS."""
    # Arrange
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    # Track phase execution order
    execution_order: list[SyncPhase] = []

    async def mock_execute_phase(phase, scope, options, session, progress):
        execution_order.append(phase)
        return SyncResult()

    # Create mock session context manager
    mock_session = AsyncMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    # Patch file lock and execute_single_phase
    with (
        patch.object(service, "_acquire_file_lock") as mock_file_lock,
        patch.object(service, "_execute_single_phase", side_effect=mock_execute_phase),
        patch.object(service, "_log_sync_start", return_value=1),
        patch.object(service, "_log_sync_completion"),
        patch.object(service, "_update_products_last_synced"),  # Fix: prevent AsyncMock warning
        patch.object(service, "_update_products_last_synced"),  # Fix: prevent AsyncMock warning
    ):
        # Make file lock context manager work
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act - pass phases out of order
        result = await service.execute_sync(
            phases=[SyncPhase.NEW_TESTS, SyncPhase.PRODUCTS, SyncPhase.FEATURES]
        )

        # Assert - phases executed in correct order regardless of input order
        assert execution_order == [
            SyncPhase.PRODUCTS,
            SyncPhase.FEATURES,
            SyncPhase.NEW_TESTS,
        ]
        assert result.phases_completed == [
            SyncPhase.PRODUCTS,
            SyncPhase.FEATURES,
            SyncPhase.NEW_TESTS,
        ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_sync_subset_of_phases():
    """Verify execute_sync can run subset of phases."""
    # Arrange
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    execution_order: list[SyncPhase] = []

    async def mock_execute_phase(phase, scope, options, session, progress):
        execution_order.append(phase)
        return SyncResult()

    mock_session = AsyncMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    with (
        patch.object(service, "_acquire_file_lock") as mock_file_lock,
        patch.object(service, "_execute_single_phase", side_effect=mock_execute_phase),
        patch.object(service, "_log_sync_start", return_value=1),
        patch.object(service, "_log_sync_completion"),
        patch.object(service, "_update_products_last_synced"),  # Fix: prevent AsyncMock warning
        patch.object(service, "_update_products_last_synced"),  # Fix: prevent AsyncMock warning
    ):
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act - only run PRODUCTS and NEW_TESTS
        result = await service.execute_sync(phases=[SyncPhase.PRODUCTS, SyncPhase.NEW_TESTS])

        # Assert - FEATURES was skipped
        assert execution_order == [SyncPhase.PRODUCTS, SyncPhase.NEW_TESTS]
        assert SyncPhase.FEATURES not in result.phases_completed


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_sync_default_phases():
    """Verify execute_sync runs all phases by default."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    execution_order: list[SyncPhase] = []

    async def mock_execute_phase(phase, scope, options, session, progress):
        execution_order.append(phase)
        return SyncResult()

    mock_session = AsyncMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    with (
        patch.object(service, "_acquire_file_lock") as mock_file_lock,
        patch.object(service, "_execute_single_phase", side_effect=mock_execute_phase),
        patch.object(service, "_log_sync_start", return_value=1),
        patch.object(service, "_log_sync_completion"),
        patch.object(service, "_update_products_last_synced"),  # Fix: prevent AsyncMock warning
    ):
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act - no phases specified
        await service.execute_sync()

        # Assert - all 3 phases executed
        assert len(execution_order) == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_sync_partial_failure_continues():
    """Verify execute_sync continues after phase failure (partial failure handling)."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    execution_order: list[SyncPhase] = []

    async def mock_execute_phase(phase, scope, options, session, progress):
        execution_order.append(phase)
        if phase == SyncPhase.FEATURES:
            raise Exception("Features API error")
        return SyncResult()

    mock_session = AsyncMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    with (
        patch.object(service, "_acquire_file_lock") as mock_file_lock,
        patch.object(service, "_execute_single_phase", side_effect=mock_execute_phase),
        patch.object(service, "_log_sync_start", return_value=1),
        patch.object(service, "_log_sync_completion"),
        patch.object(service, "_update_products_last_synced"),  # Fix: prevent AsyncMock warning
    ):
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act
        result = await service.execute_sync()

        # Assert - all phases attempted despite failure
        assert execution_order == [
            SyncPhase.PRODUCTS,
            SyncPhase.FEATURES,
            SyncPhase.NEW_TESTS,
        ]
        # Only successful phases in completed list
        assert SyncPhase.PRODUCTS in result.phases_completed
        assert SyncPhase.FEATURES not in result.phases_completed
        assert SyncPhase.NEW_TESTS in result.phases_completed
        # Warning recorded for failed phase
        assert any("FEATURES" in w.upper() for w in result.warnings)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_sync_scope_filtering():
    """Verify scope.product_ids is passed to phase execution."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    captured_scope: SyncScope | None = None

    async def mock_execute_phase(phase, scope, options, session, progress):
        nonlocal captured_scope
        captured_scope = scope
        return SyncResult()

    mock_session = AsyncMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    with (
        patch.object(service, "_acquire_file_lock") as mock_file_lock,
        patch.object(service, "_execute_single_phase", side_effect=mock_execute_phase),
        patch.object(service, "_log_sync_start", return_value=1),
        patch.object(service, "_log_sync_completion"),
        patch.object(service, "_update_products_last_synced"),  # Fix: prevent AsyncMock warning
    ):
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act
        await service.execute_sync(
            phases=[SyncPhase.PRODUCTS],
            scope=SyncScope(product_ids=[598]),
        )

        # Assert
        assert captured_scope is not None
        assert captured_scope.product_ids == [598]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_sync_duration_always_populated():
    """Verify SyncResult.duration_seconds is always populated (AC2 requirement)."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    async def mock_execute_phase(phase, scope, options, session, progress):
        await asyncio.sleep(0.01)  # Small delay for measurable duration
        return SyncResult()

    mock_session = AsyncMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    with (
        patch.object(service, "_acquire_file_lock") as mock_file_lock,
        patch.object(service, "_execute_single_phase", side_effect=mock_execute_phase),
        patch.object(service, "_log_sync_start", return_value=1),
        patch.object(service, "_log_sync_completion"),
        patch.object(service, "_update_products_last_synced"),  # Fix: prevent AsyncMock warning
    ):
        mock_file_lock.return_value.__aenter__ = AsyncMock(return_value=None)
        mock_file_lock.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await service.execute_sync(phases=[SyncPhase.PRODUCTS])

        # Assert - duration is > 0
        assert result.duration_seconds > 0


# =============================================================================
# AC4: File lock acquisition and timeout
# =============================================================================


@pytest.mark.unit
def test_lock_file_path():
    """Verify lock file path is ~/.testio-mcp/sync.lock."""
    expected_path = Path.home() / ".testio-mcp" / "sync.lock"
    assert SyncService.LOCK_FILE == expected_path


@pytest.mark.unit
def test_lock_timeout_is_30_seconds():
    """Verify lock timeout is 30 seconds (AC4)."""
    assert SyncService.LOCK_TIMEOUT_SECONDS == 30.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_lock_timeout_raises_sync_timeout_error():
    """Verify lock timeout raises SyncTimeoutError with clear message."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    service = SyncService(client=mock_client, cache=mock_cache)

    # Patch FileLock to raise Timeout
    from filelock import Timeout

    with patch("testio_mcp.services.sync_service.FileLock") as MockFileLock:
        mock_lock = MagicMock()
        mock_lock.acquire.side_effect = Timeout(service.LOCK_FILE)
        MockFileLock.return_value = mock_lock

        # Act & Assert
        ctx = service._acquire_file_lock()
        with pytest.raises(SyncTimeoutError) as exc_info:
            await ctx.__aenter__()

        assert "30" in str(exc_info.value)  # Mentions timeout duration
        assert "sync.lock" in str(exc_info.value)  # Mentions lock file


# =============================================================================
# AC5: Stale lock recovery
# =============================================================================


@pytest.mark.unit
def test_stale_lock_threshold_is_1_hour():
    """Verify stale lock threshold is 1 hour (3600 seconds)."""
    assert SyncService.STALE_LOCK_THRESHOLD_SECONDS == 3600


@pytest.mark.unit
def test_is_lock_stale_returns_false_if_file_missing():
    """Verify _is_lock_stale returns False if lock file doesn't exist."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    with patch.object(Path, "exists", return_value=False):
        result = service._is_lock_stale(Path("/nonexistent/sync.lock"))

    assert result is False


@pytest.mark.unit
def test_is_lock_stale_returns_true_if_pid_dead():
    """Verify _is_lock_stale returns True if PID is not running."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    lock_content = "PID: 99999\nSTARTED: 2025-01-01T00:00:00Z\n"

    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "read_text", return_value=lock_content),
        patch("testio_mcp.services.sync_service.psutil.pid_exists", return_value=False),
    ):
        result = service._is_lock_stale(service.LOCK_FILE)

    assert result is True


@pytest.mark.unit
def test_is_lock_stale_returns_true_if_mtime_old():
    """Verify _is_lock_stale returns True if mtime > 1 hour."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    lock_content = f"PID: {os.getpid()}\nSTARTED: 2025-01-01T00:00:00Z\n"
    # mtime 2 hours ago
    old_mtime = time.time() - 7200

    mock_stat = MagicMock()
    mock_stat.st_mtime = old_mtime

    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "read_text", return_value=lock_content),
        patch("testio_mcp.services.sync_service.psutil.pid_exists", return_value=True),
        patch.object(Path, "stat", return_value=mock_stat),
    ):
        result = service._is_lock_stale(service.LOCK_FILE)

    assert result is True


@pytest.mark.unit
def test_is_lock_stale_returns_false_if_fresh():
    """Verify _is_lock_stale returns False if lock is fresh and PID alive."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    lock_content = f"PID: {os.getpid()}\nSTARTED: 2025-01-01T00:00:00Z\n"
    # mtime just now
    recent_mtime = time.time()

    mock_stat = MagicMock()
    mock_stat.st_mtime = recent_mtime

    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "read_text", return_value=lock_content),
        patch("testio_mcp.services.sync_service.psutil.pid_exists", return_value=True),
        patch.object(Path, "stat", return_value=mock_stat),
    ):
        result = service._is_lock_stale(service.LOCK_FILE)

    assert result is False


# =============================================================================
# AC6: Asyncio lock for in-process serialization
# =============================================================================


@pytest.mark.unit
def test_get_sync_lock_returns_asyncio_lock():
    """Verify _get_sync_lock returns an asyncio.Lock."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    service = SyncService(client=mock_client, cache=mock_cache)

    lock = service._get_sync_lock()

    assert isinstance(lock, asyncio.Lock)


@pytest.mark.unit
def test_get_sync_lock_reuses_same_lock():
    """Verify _get_sync_lock returns same lock for same customer."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    service = SyncService(client=mock_client, cache=mock_cache)

    lock1 = service._get_sync_lock()
    lock2 = service._get_sync_lock()

    assert lock1 is lock2


@pytest.mark.unit
def test_get_sync_lock_different_for_different_customer():
    """Verify _get_sync_lock returns different lock for different customer."""
    mock_client = AsyncMock()

    mock_cache1 = MagicMock()
    mock_cache1.customer_id = 123
    service1 = SyncService(client=mock_client, cache=mock_cache1)

    mock_cache2 = MagicMock()
    mock_cache2.customer_id = 456
    service2 = SyncService(client=mock_client, cache=mock_cache2)

    lock1 = service1._get_sync_lock()
    lock2 = service2._get_sync_lock()

    # Different customers have different locks
    assert lock1 is not lock2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_asyncio_lock_prevents_concurrent_execution():
    """Verify asyncio lock prevents thundering herd within same process."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    service = SyncService(client=mock_client, cache=mock_cache)

    execution_count = 0
    max_concurrent = 0

    async def simulate_work():
        nonlocal execution_count, max_concurrent
        lock = service._get_sync_lock()
        async with lock:
            execution_count += 1
            if execution_count > max_concurrent:
                max_concurrent = execution_count
            await asyncio.sleep(0.01)
            execution_count -= 1

    # Run multiple concurrent tasks
    await asyncio.gather(*[simulate_work() for _ in range(5)])

    # Only 1 should have been executing at a time
    assert max_concurrent == 1


# =============================================================================
# AC7: Sync event logging
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_sync_start_creates_event():
    """Verify _log_sync_start creates sync event in database."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    # Mock session and event
    mock_session = AsyncMock()
    # Fix: session.add() is synchronous, not async
    mock_session.add = MagicMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    # Mock the event with an ID
    mock_event = MagicMock()
    mock_event.id = 42

    async def mock_refresh(event):
        event.id = 42

    mock_session.refresh = mock_refresh

    # Act
    event_id = await service._log_sync_start(
        phases=[SyncPhase.PRODUCTS],
        scope=SyncScope(),
        trigger_source="test",
    )

    # Assert
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    assert event_id == 42


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_sync_completion_updates_event():
    """Verify _log_sync_completion updates sync event with stats."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    # Fix: session.add() is synchronous, not async
    mock_session.add = MagicMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    # Mock finding the event
    mock_event = MagicMock()
    mock_result = MagicMock()
    mock_result.first.return_value = mock_event
    mock_session.exec.return_value = mock_result

    result = SyncResult(
        phases_completed=[SyncPhase.PRODUCTS],
        products_synced=5,
        features_refreshed=10,
        tests_discovered=20,
        duration_seconds=45.2,
    )

    # Act
    await service._log_sync_completion(event_id=42, result=result)

    # Assert
    assert mock_event.status == "success"
    assert mock_event.products_synced == 5
    assert mock_event.features_refreshed == 10
    assert mock_event.tests_discovered == 20
    assert mock_event.duration_seconds == 45.2
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_sync_completion_partial_failure_status():
    """Verify _log_sync_completion sets partial_failure status if errors exist."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    # Fix: session.add() is synchronous, not async
    mock_session.add = MagicMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    mock_event = MagicMock()
    mock_result = MagicMock()
    mock_result.first.return_value = mock_event
    mock_session.exec.return_value = mock_result

    result = SyncResult(
        errors=["Phase 2 failed"],
        duration_seconds=30.0,
    )

    # Act
    await service._log_sync_completion(event_id=42, result=result)

    # Assert
    assert mock_event.status == "partial_failure"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_log_sync_error_updates_event():
    """Verify _log_sync_error updates sync event with error."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    # Fix: session.add() is synchronous, not async
    mock_session.add = MagicMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    mock_event = MagicMock()
    mock_result = MagicMock()
    mock_result.first.return_value = mock_event
    mock_session.exec.return_value = mock_result

    start_time = time.time() - 5.0  # Started 5 seconds ago

    # Act
    await service._log_sync_error(
        event_id=42,
        error_message="Lock timeout",
        start_time=start_time,
    )

    # Assert
    assert mock_event.status == "failure"
    assert mock_event.error_message == "Lock timeout"
    assert mock_event.duration_seconds is not None
    assert mock_event.duration_seconds >= 5.0  # At least 5 seconds
    mock_session.commit.assert_called_once()


# =============================================================================
# AC8: Repository factory methods
# =============================================================================


@pytest.mark.unit
def test_get_product_repo_uses_factory():
    """Verify _get_product_repo uses factory if provided."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_repo = MagicMock()
    mock_factory = MagicMock(return_value=mock_repo)
    mock_session = AsyncMock()

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        product_repo_factory=mock_factory,
    )

    # Act
    repo = service._get_product_repo(mock_session)

    # Assert
    mock_factory.assert_called_once_with(mock_session)
    assert repo is mock_repo


@pytest.mark.unit
def test_get_feature_repo_uses_factory():
    """Verify _get_feature_repo uses factory if provided."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_repo = MagicMock()
    mock_factory = MagicMock(return_value=mock_repo)
    mock_session = AsyncMock()

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        feature_repo_factory=mock_factory,
    )

    # Act
    repo = service._get_feature_repo(mock_session)

    # Assert
    mock_factory.assert_called_once_with(mock_session)
    assert repo is mock_repo


@pytest.mark.unit
def test_get_test_repo_uses_factory():
    """Verify _get_test_repo uses factory if provided."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_repo = MagicMock()
    mock_factory = MagicMock(return_value=mock_repo)
    mock_session = AsyncMock()

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        test_repo_factory=mock_factory,
    )

    # Act
    repo = service._get_test_repo(mock_session)

    # Assert
    mock_factory.assert_called_once_with(mock_session)
    assert repo is mock_repo


# =============================================================================
# Exception classes
# =============================================================================


@pytest.mark.unit
def test_sync_lock_error_is_exception():
    """Verify SyncLockError is an Exception."""
    assert issubclass(SyncLockError, Exception)


@pytest.mark.unit
def test_sync_timeout_error_is_sync_lock_error():
    """Verify SyncTimeoutError inherits from SyncLockError."""
    assert issubclass(SyncTimeoutError, SyncLockError)


# =============================================================================
# Products phase execution
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_products_phase_fetches_and_upserts():
    """Verify products phase fetches from API and upserts to database."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "products": [
            {"id": 598, "name": "Product 1"},
            {"id": 1024, "name": "Product 2"},
        ]
    }

    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_product_repo = AsyncMock()

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        product_repo_factory=lambda s: mock_product_repo,
    )

    # Act
    result = await service._execute_products_phase(
        scope=SyncScope(),
        options=SyncOptions(),
        session=mock_session,
    )

    # Assert
    mock_client.get.assert_called_once_with("products")
    assert mock_product_repo.upsert_product.call_count == 2
    assert result.products_synced == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_products_phase_filters_by_scope():
    """Verify products phase filters by scope.product_ids."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "products": [
            {"id": 598, "name": "Product 1"},
            {"id": 1024, "name": "Product 2"},
        ]
    }

    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_product_repo = AsyncMock()

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        product_repo_factory=lambda s: mock_product_repo,
    )

    # Act - only sync product 598
    result = await service._execute_products_phase(
        scope=SyncScope(product_ids=[598]),
        options=SyncOptions(),
        session=mock_session,
    )

    # Assert - only 1 product upserted
    assert mock_product_repo.upsert_product.call_count == 1
    assert result.products_synced == 1


# =============================================================================
# Features phase execution
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_features_phase_with_scope():
    """Verify features phase uses scope.product_ids."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_feature_repo = AsyncMock()
    # Mock returns features dict with one feature
    mock_feature_repo.get_features_cached_or_refresh.return_value = (
        {598: [{"id": 1, "title": "Feature 1"}]},
        {"api_calls": 1, "cache_hits": 0},
    )

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        feature_repo_factory=lambda s: mock_feature_repo,
    )

    # Act
    result = await service._execute_features_phase(
        scope=SyncScope(product_ids=[598]),
        options=SyncOptions(),
        session=mock_session,
    )

    # Assert
    # Features always force_refresh=True during sync (Bug #2 fix)
    mock_feature_repo.get_features_cached_or_refresh.assert_called_once_with(
        product_ids=[598],
        force_refresh=True,
    )
    assert result.features_refreshed == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_features_phase_without_scope():
    """Verify features phase gets all products when no scope."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_feature_repo = AsyncMock()
    # Mock returns features dict with one feature per product
    mock_feature_repo.get_features_cached_or_refresh.return_value = (
        {598: [{"id": 1, "title": "Feature 1"}], 1024: [{"id": 2, "title": "Feature 2"}]},
        {"api_calls": 2, "cache_hits": 0},
    )

    mock_product_repo = AsyncMock()
    mock_product_repo.get_all_products.return_value = [
        {"id": 598, "name": "Product 1"},
        {"id": 1024, "name": "Product 2"},
    ]

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        feature_repo_factory=lambda s: mock_feature_repo,
        product_repo_factory=lambda s: mock_product_repo,
    )

    # Act - no product_ids in scope
    result = await service._execute_features_phase(
        scope=SyncScope(),
        options=SyncOptions(),
        session=mock_session,
    )

    # Assert
    mock_product_repo.get_all_products.assert_called_once()
    assert result.features_refreshed == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_features_phase_with_force_refresh():
    """Verify features phase passes force_refresh option."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_feature_repo = AsyncMock()
    mock_feature_repo.get_features_cached_or_refresh.return_value = (
        {},
        {"api_calls": 0, "cache_hits": 0},
    )

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        feature_repo_factory=lambda s: mock_feature_repo,
    )

    # Act
    await service._execute_features_phase(
        scope=SyncScope(product_ids=[598]),
        options=SyncOptions(force_refresh=True),
        session=mock_session,
    )

    # Assert
    mock_feature_repo.get_features_cached_or_refresh.assert_called_once_with(
        product_ids=[598],
        force_refresh=True,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_features_phase_no_products():
    """Verify features phase returns early when no products found."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_product_repo = AsyncMock()
    mock_product_repo.get_all_products.return_value = []

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        product_repo_factory=lambda s: mock_product_repo,
    )

    # Act - no scope, no products in DB
    result = await service._execute_features_phase(
        scope=SyncScope(),
        options=SyncOptions(),
        session=mock_session,
    )

    # Assert
    assert result.features_refreshed == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_features_phase_handles_error():
    """Verify features phase handles errors gracefully."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_feature_repo = AsyncMock()
    mock_feature_repo.get_features_cached_or_refresh.side_effect = Exception("API error")

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        feature_repo_factory=lambda s: mock_feature_repo,
    )

    # Act
    result = await service._execute_features_phase(
        scope=SyncScope(product_ids=[598]),
        options=SyncOptions(),
        session=mock_session,
    )

    # Assert
    assert len(result.errors) > 0
    assert "Features phase failed" in result.errors[0]


# =============================================================================
# New tests phase execution
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_new_tests_phase_basic():
    """Verify new tests phase fetches and inserts tests with pagination."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "exploratory_tests": [
            {"id": 1001, "end_at": "2025-01-01T00:00:00Z"},
            {"id": 1002, "end_at": "2025-01-02T00:00:00Z"},
        ]
    }

    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_test_repo = AsyncMock()
    mock_test_repo.test_exists.return_value = False

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        test_repo_factory=lambda s: mock_test_repo,
    )

    # Act
    result = await service._execute_new_tests_phase(
        scope=SyncScope(product_ids=[598]),
        options=SyncOptions(),
        session=mock_session,
        progress=ProgressReporter.noop(),
    )

    # Assert - API called with pagination params
    mock_client.get.assert_called_with(
        "products/598/exploratory_tests",
        params={"page": 1, "per_page": 25},
    )
    assert mock_test_repo.insert_test.call_count == 2
    assert result.tests_discovered == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_new_tests_phase_upserts_all_tests():
    """Verify new tests phase upserts ALL tests (both new and existing).

    The paginated sync algorithm always upserts tests to keep data fresh.
    Known test detection only controls when to stop pagination.
    """
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "exploratory_tests": [
            {"id": 1001, "end_at": "2025-01-01T00:00:00Z"},
            {"id": 1002, "end_at": "2025-01-02T00:00:00Z"},
        ]
    }

    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_test_repo = AsyncMock()
    # First test exists, second doesn't
    mock_test_repo.test_exists.side_effect = [True, False]

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        test_repo_factory=lambda s: mock_test_repo,
    )

    # Act - incremental mode (default)
    result = await service._execute_new_tests_phase(
        scope=SyncScope(product_ids=[598]),
        options=SyncOptions(),
        session=mock_session,
        progress=ProgressReporter.noop(),
    )

    # Assert - BOTH tests upserted (keeps data fresh)
    # Existing test counted as updated, new test as discovered
    assert mock_test_repo.insert_test.call_count == 2
    assert result.tests_discovered == 1  # New test
    assert result.tests_updated == 1  # Existing test


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_new_tests_phase_force_refresh_includes_existing():
    """Verify new tests phase includes existing tests when force_refresh=True.

    Note: Both incremental and force_refresh modes upsert all tests.
    The difference is force_refresh bypasses date filtering.
    """
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "exploratory_tests": [
            {"id": 1001, "end_at": "2025-01-01T00:00:00Z"},
        ]
    }

    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_test_repo = AsyncMock()
    mock_test_repo.test_exists.return_value = True  # Test exists

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        test_repo_factory=lambda s: mock_test_repo,
    )

    # Act - force refresh mode
    result = await service._execute_new_tests_phase(
        scope=SyncScope(product_ids=[598]),
        options=SyncOptions(force_refresh=True),
        session=mock_session,
        progress=ProgressReporter.noop(),
    )

    # Assert - test upserted, counted as updated (exists)
    assert mock_test_repo.insert_test.call_count == 1
    assert result.tests_updated == 1  # Existing test updated


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_new_tests_phase_filters_by_since_date():
    """Verify new tests phase filters by since_date using end_at field."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "exploratory_tests": [
            {"id": 1001, "end_at": "2024-01-01T00:00:00Z"},  # Old (filtered out)
            {"id": 1002, "end_at": "2025-06-15T00:00:00Z"},  # New (included)
        ]
    }

    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_test_repo = AsyncMock()
    mock_test_repo.test_exists.return_value = False

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        test_repo_factory=lambda s: mock_test_repo,
    )

    # Act - only tests since 2025-01-01 (filters by end_at)
    result = await service._execute_new_tests_phase(
        scope=SyncScope(
            product_ids=[598],
            since_date=datetime(2025, 1, 1, tzinfo=UTC),
        ),
        options=SyncOptions(),
        session=mock_session,
        progress=ProgressReporter.noop(),
    )

    # Assert - only 1 test (the new one) inserted
    assert mock_test_repo.insert_test.call_count == 1
    assert result.tests_discovered == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_new_tests_phase_no_products():
    """Verify new tests phase returns early when no products."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_product_repo = AsyncMock()
    mock_product_repo.get_all_products.return_value = []

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        product_repo_factory=lambda s: mock_product_repo,
    )

    # Act
    result = await service._execute_new_tests_phase(
        scope=SyncScope(),
        options=SyncOptions(),
        session=mock_session,
        progress=ProgressReporter.noop(),
    )

    # Assert
    assert result.tests_discovered == 0
    mock_client.get.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_new_tests_phase_handles_product_error():
    """Verify new tests phase continues after single product failure."""
    mock_client = AsyncMock()

    # First product succeeds, second fails
    async def mock_get(endpoint: str, params: dict | None = None):
        if "598" in endpoint:
            return {"exploratory_tests": [{"id": 1001, "end_at": "2025-01-01T00:00:00Z"}]}
        raise Exception("API error for product 1024")

    mock_client.get.side_effect = mock_get

    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_test_repo = AsyncMock()
    mock_test_repo.test_exists.return_value = False

    service = SyncService(
        client=mock_client,
        cache=mock_cache,
        test_repo_factory=lambda s: mock_test_repo,
    )

    # Act
    result = await service._execute_new_tests_phase(
        scope=SyncScope(product_ids=[598, 1024]),
        options=SyncOptions(),
        session=mock_session,
        progress=ProgressReporter.noop(),
    )

    # Assert - first product's test was synced, second failed with warning
    assert result.tests_discovered == 1
    assert len(result.warnings) > 0
    assert "1024" in result.warnings[0]


# =============================================================================
# Filter tests by date
# =============================================================================


# STORY-054: Removed dead code tests for _filter_tests_by_date
# The method was never called and has been removed from SyncService


# test_filter_tests_by_date_handles_invalid_date also removed (dead code)


# test_filter_tests_by_date_handles_naive_datetime also removed (dead code)


# =============================================================================
# Write lock PID
# =============================================================================


@pytest.mark.unit
def test_write_lock_pid_writes_content():
    """Verify _write_lock_pid writes PID and timestamp to lock file."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    written_content = None

    def mock_write_text(self, content: str):
        nonlocal written_content
        written_content = content

    with patch.object(Path, "write_text", mock_write_text):
        service._write_lock_pid()

    assert written_content is not None
    assert f"PID: {os.getpid()}" in written_content
    assert "STARTED:" in written_content


@pytest.mark.unit
def test_write_lock_pid_handles_error():
    """Verify _write_lock_pid handles write errors gracefully."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    with patch.object(Path, "write_text", side_effect=OSError("Permission denied")):
        # Should not raise
        service._write_lock_pid()


# =============================================================================
# Default repository creation
# =============================================================================


@pytest.mark.unit
def test_get_product_repo_creates_default():
    """Verify _get_product_repo creates ProductRepository when no factory."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    with patch("testio_mcp.repositories.product_repository.ProductRepository") as MockProductRepo:
        mock_repo = MagicMock()
        MockProductRepo.return_value = mock_repo

        result = service._get_product_repo(mock_session)

        MockProductRepo.assert_called_once_with(mock_session, mock_client, 123)
        assert result is mock_repo


@pytest.mark.unit
def test_get_feature_repo_creates_default():
    """Verify _get_feature_repo creates FeatureRepository when no factory."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    with patch("testio_mcp.repositories.feature_repository.FeatureRepository") as MockFeatureRepo:
        mock_repo = MagicMock()
        MockFeatureRepo.return_value = mock_repo

        result = service._get_feature_repo(mock_session)

        MockFeatureRepo.assert_called_once_with(mock_session, mock_client, 123, mock_cache)
        assert result is mock_repo


@pytest.mark.unit
def test_get_test_repo_creates_default():
    """Verify _get_test_repo creates TestRepository when no factory."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    with patch("testio_mcp.repositories.test_repository.TestRepository") as MockTestRepo:
        mock_repo = MagicMock()
        MockTestRepo.return_value = mock_repo

        result = service._get_test_repo(mock_session)

        MockTestRepo.assert_called_once_with(mock_session, mock_client, 123, cache=mock_cache)
        assert result is mock_repo


# =============================================================================
# File lock context manager
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_lock_context_reclaims_stale_lock():
    """Verify file lock context reclaims stale lock."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    service = SyncService(client=mock_client, cache=mock_cache)

    with (
        patch.object(service, "_is_lock_stale", return_value=True),
        patch.object(Path, "mkdir"),
        patch.object(Path, "unlink") as mock_unlink,
        patch("testio_mcp.services.sync_service.FileLock") as MockFileLock,
        patch.object(service, "_write_lock_pid"),
    ):
        mock_lock = MagicMock()
        MockFileLock.return_value = mock_lock

        ctx = service._acquire_file_lock()
        await ctx.__aenter__()

        # Stale lock was removed
        mock_unlink.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_lock_context_releases_on_exit():
    """Verify file lock context releases lock on exit."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    service = SyncService(client=mock_client, cache=mock_cache)

    with (
        patch.object(service, "_is_lock_stale", return_value=False),
        patch.object(Path, "mkdir"),
        patch("testio_mcp.services.sync_service.FileLock") as MockFileLock,
        patch.object(service, "_write_lock_pid"),
    ):
        mock_lock = MagicMock()
        mock_lock.is_locked = True
        MockFileLock.return_value = mock_lock

        ctx = service._acquire_file_lock()
        await ctx.__aenter__()
        await ctx.__aexit__(None, None, None)

        mock_lock.release.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_sync_raises_on_lock_timeout():
    """Verify execute_sync raises SyncTimeoutError on lock timeout."""
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()
    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_cache.async_session_maker = mock_session_maker

    service = SyncService(client=mock_client, cache=mock_cache)

    # Patch _log_sync_start and _log_sync_error
    with (
        patch.object(service, "_log_sync_start", return_value=1),
        patch.object(service, "_log_sync_error"),
    ):
        # Make file lock raise timeout
        async def mock_file_lock_enter(self):
            raise SyncTimeoutError("Lock timeout")

        with patch.object(service, "_acquire_file_lock") as mock_file_lock:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = mock_file_lock_enter
            mock_file_lock.return_value = mock_ctx

            with pytest.raises(SyncTimeoutError):
                await service.execute_sync()


# =============================================================================
# Per-Page Progress Reporting Tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_product_tests_paginated_reports_per_page_progress():
    """Verify _sync_product_tests_paginated reports progress for each page fetched.

    Tests that per-page progress is reported with:
    - total=None (indeterminate mode - unknown total pages)
    - force=False (throttled to prevent spam)
    - message includes product ID and page number
    """
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()

    # Mock test repository with test_exists returning False (all new tests)
    mock_test_repo = AsyncMock()
    mock_test_repo.test_exists.return_value = False
    mock_test_repo.insert_test = AsyncMock()

    # Mock progress reporter to capture calls
    mock_progress = AsyncMock(spec=ProgressReporter)
    mock_progress.report = AsyncMock()

    service = SyncService(client=mock_client, cache=mock_cache)

    # Mock API response with 2 pages of tests
    page1_response = {
        "exploratory_tests": [
            {"id": 1001, "end_at": "2025-01-01T00:00:00Z"},
            {"id": 1002, "end_at": "2025-01-02T00:00:00Z"},
        ]
    }
    page2_response = {
        "exploratory_tests": []  # Empty page signals end
    }
    mock_client.get.side_effect = [page1_response, page2_response]

    # Call the paginated sync method
    await service._sync_product_tests_paginated(
        product_id=598,
        test_repo=mock_test_repo,
        session=mock_session,
        scope=SyncScope(),
        options=SyncOptions(),
        progress=mock_progress,
    )

    # Verify progress was reported for each page
    assert mock_progress.report.call_count >= 1

    # Check first progress call (page 1)
    first_call = mock_progress.report.call_args_list[0]
    # Updated expectations for Phase 3 global progress reporting
    assert first_call.kwargs["progress"] == 0.0  # Defaults to 0.0 if not passed
    assert first_call.kwargs["total"] == 3.0  # Uses Phase 3 scale (3.0 max)
    assert "Discovering tests" in first_call.kwargs["message"]
    assert "page 1" in first_call.kwargs["message"]
    assert first_call.kwargs["force"] is False  # Throttled


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_product_tests_paginated_progress_uses_noop_safely():
    """Verify _sync_product_tests_paginated works with ProgressReporter.noop().

    Ensures the no-op reporter doesn't cause errors when progress is reported.
    """
    mock_client = AsyncMock()
    mock_cache = MagicMock()
    mock_cache.customer_id = 123

    mock_session = AsyncMock()

    mock_test_repo = AsyncMock()
    mock_test_repo.test_exists.return_value = False
    mock_test_repo.insert_test = AsyncMock()

    # Use actual noop reporter
    noop_progress = ProgressReporter.noop()

    service = SyncService(client=mock_client, cache=mock_cache)

    # Mock single empty page (quick exit)
    mock_client.get.return_value = {"exploratory_tests": []}

    # Should complete without error
    result = await service._sync_product_tests_paginated(
        product_id=598,
        test_repo=mock_test_repo,
        session=mock_session,
        scope=SyncScope(),
        options=SyncOptions(),
        progress=noop_progress,
    )

    assert result["new_tests_count"] == 0
    assert result["tests_updated"] == 0
