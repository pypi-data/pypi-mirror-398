"""Unit tests for DiagnosticsService.

STORY-060: Test consolidated diagnostic service orchestration.

Tests use behavioral approach: assert on outputs and state, not internal calls.
All dependencies (client, cache) are mocked.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from testio_mcp.services.diagnostics_service import DiagnosticsService


@pytest.fixture
def mock_client():
    """Mock TestIOClient."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_cache():
    """Mock PersistentCache with all diagnostic methods."""
    cache = AsyncMock()

    # Database stats defaults
    cache.get_db_size_mb.return_value = 12.5
    cache.db_path = "/path/to/cache.db"
    cache.count_tests.return_value = 100
    cache.count_products.return_value = 5
    cache.count_features.return_value = 20
    cache.count_bugs.return_value = 50

    # Storage range defaults
    cache.get_oldest_test_date.return_value = "2025-01-01"
    cache.get_newest_test_date.return_value = "2025-11-28"

    # Sync events defaults
    now = datetime.now(UTC)
    cache.get_sync_events.return_value = [
        {
            "started_at": (now - timedelta(hours=1)).isoformat(),
            "completed_at": (now - timedelta(hours=1) + timedelta(minutes=5)).isoformat(),
            "status": "completed",
            "duration_seconds": 300.0,
            "tests_synced": 50,
            "error": None,
        },
        {
            "started_at": (now - timedelta(hours=2)).isoformat(),
            "completed_at": (now - timedelta(hours=2) + timedelta(minutes=3)).isoformat(),
            "status": "completed",
            "duration_seconds": 180.0,
            "tests_synced": 30,
            "error": None,
        },
    ]

    cache.count_sync_failures_since.return_value = 0

    # Session factory for ProductService
    cache.async_session_maker = MagicMock()
    cache.customer_id = 123

    return cache


@pytest.fixture
def service(mock_client, mock_cache):
    """Create DiagnosticsService with mocked dependencies."""
    return DiagnosticsService(client=mock_client, cache=mock_cache)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_server_diagnostics_returns_complete_data(service, mock_cache, monkeypatch):
    """Verify get_server_diagnostics returns all expected fields."""
    # Mock ProductService.list_products
    from testio_mcp.services.product_service import ProductService

    mock_list_products = AsyncMock(return_value={"total_count": 5, "items": []})
    monkeypatch.setattr(ProductService, "list_products", mock_list_products)

    # Act
    result = await service.get_server_diagnostics(include_sync_events=False, sync_event_limit=5)

    # Assert - verify structure
    assert "api" in result
    assert "database" in result
    assert "sync" in result
    assert "storage" in result
    assert "events" not in result or result["events"] is None

    # Assert - API status
    assert result["api"]["connected"] is True
    assert result["api"]["product_count"] == 5
    assert "latency_ms" in result["api"]

    # Assert - Database status
    assert result["database"]["size_mb"] == 12.5
    assert result["database"]["test_count"] == 100
    assert result["database"]["product_count"] == 5
    assert result["database"]["feature_count"] == 20
    assert result["database"]["bug_count"] == 50

    # Assert - Sync status
    assert "last_sync" in result["sync"]
    assert "success_rate_24h" in result["sync"]
    assert "circuit_breaker_active" in result["sync"]

    # Assert - Storage range
    assert result["storage"]["oldest_test_date"] == "2025-01-01"
    assert result["storage"]["newest_test_date"] == "2025-11-28"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_include_sync_events_false_omits_events(service, mock_cache, monkeypatch):
    """Verify include_sync_events=False omits events field."""
    # Mock ProductService
    from testio_mcp.services.product_service import ProductService

    mock_list_products = AsyncMock(return_value={"total_count": 5, "items": []})
    monkeypatch.setattr(ProductService, "list_products", mock_list_products)

    # Act
    result = await service.get_server_diagnostics(include_sync_events=False, sync_event_limit=5)

    # Assert
    assert "events" not in result or result["events"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_include_sync_events_true_includes_events(service, mock_cache, monkeypatch):
    """Verify include_sync_events=True includes sync events list."""
    # Mock ProductService
    from testio_mcp.services.product_service import ProductService

    mock_list_products = AsyncMock(return_value={"total_count": 5, "items": []})
    monkeypatch.setattr(ProductService, "list_products", mock_list_products)

    # Act
    result = await service.get_server_diagnostics(include_sync_events=True, sync_event_limit=5)

    # Assert
    assert "events" in result
    assert result["events"] is not None
    assert isinstance(result["events"], list)
    assert len(result["events"]) == 2  # Mock returns 2 events

    # Verify event structure
    event = result["events"][0]
    assert "started_at" in event
    assert "status" in event
    assert "duration_seconds" in event


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_event_limit_respects_bounds(service, mock_cache, monkeypatch):
    """Verify sync_event_limit is clamped to 1-20."""
    # Mock ProductService
    from testio_mcp.services.product_service import ProductService

    mock_list_products = AsyncMock(return_value={"total_count": 5, "items": []})
    monkeypatch.setattr(ProductService, "list_products", mock_list_products)

    # Test upper bound (30 -> 20)
    await service.get_server_diagnostics(include_sync_events=True, sync_event_limit=30)
    mock_cache.get_sync_events.assert_called_with(limit=20)

    # Test lower bound (0 -> 1)
    await service.get_server_diagnostics(include_sync_events=True, sync_event_limit=0)
    mock_cache.get_sync_events.assert_called_with(limit=1)

    # Test valid value (10 -> 10)
    await service.get_server_diagnostics(include_sync_events=True, sync_event_limit=10)
    mock_cache.get_sync_events.assert_called_with(limit=10)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_active_when_3_failures(service, mock_cache, monkeypatch):
    """Verify circuit breaker active when 3+ failures in 5 minutes."""
    # Mock ProductService
    from testio_mcp.services.product_service import ProductService

    mock_list_products = AsyncMock(return_value={"total_count": 5, "items": []})
    monkeypatch.setattr(ProductService, "list_products", mock_list_products)

    # Simulate 3 failures in last 5 minutes
    mock_cache.count_sync_failures_since.return_value = 3

    # Act
    result = await service.get_server_diagnostics()

    # Assert
    assert result["sync"]["circuit_breaker_active"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_circuit_breaker_inactive_when_less_than_3_failures(service, mock_cache, monkeypatch):
    """Verify circuit breaker inactive when <3 failures."""
    # Mock ProductService
    from testio_mcp.services.product_service import ProductService

    mock_list_products = AsyncMock(return_value={"total_count": 5, "items": []})
    monkeypatch.setattr(ProductService, "list_products", mock_list_products)

    # Simulate only 2 failures
    mock_cache.count_sync_failures_since.return_value = 2

    # Act
    result = await service.get_server_diagnostics()

    # Assert
    assert result["sync"]["circuit_breaker_active"] is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_api_health_check_failure_handling(service, mock_cache, monkeypatch):
    """Verify API health check gracefully handles failures."""
    # Mock ProductService to raise exception
    from testio_mcp.services.product_service import ProductService

    async def failing_list_products(*args, **kwargs):
        raise Exception("API connection failed")

    monkeypatch.setattr(ProductService, "list_products", failing_list_products)

    # Act
    result = await service.get_server_diagnostics()

    # Assert - API status should show failure
    assert result["api"]["connected"] is False
    assert result["api"]["product_count"] == 0
    # latency_ms is None on failure (kept with exclude_unset=True)
    assert result["api"]["latency_ms"] is None
    assert "failed" in result["api"]["message"].lower()

    # Assert - Other sections should still work
    assert "database" in result
    assert "sync" in result
    assert "storage" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sync_status_calculates_24h_statistics(service, mock_cache, monkeypatch):
    """Verify sync status correctly calculates 24h success rate."""
    # Mock ProductService
    from testio_mcp.services.product_service import ProductService

    mock_list_products = AsyncMock(return_value={"total_count": 5, "items": []})
    monkeypatch.setattr(ProductService, "list_products", mock_list_products)

    # Setup sync events: 3 completed, 1 failed in last 24h
    now = datetime.now(UTC)
    mock_cache.get_sync_events.return_value = [
        {
            "started_at": (now - timedelta(hours=1)).isoformat(),
            "completed_at": (now - timedelta(hours=1) + timedelta(minutes=5)).isoformat(),
            "status": "completed",
            "duration_seconds": 300.0,
            "tests_synced": 50,
            "error": None,
        },
        {
            "started_at": (now - timedelta(hours=5)).isoformat(),
            "completed_at": None,
            "status": "failed",
            "duration_seconds": None,
            "tests_synced": None,
            "error": "Timeout",
        },
        {
            "started_at": (now - timedelta(hours=10)).isoformat(),
            "completed_at": (now - timedelta(hours=10) + timedelta(minutes=3)).isoformat(),
            "status": "completed",
            "duration_seconds": 180.0,
            "tests_synced": 30,
            "error": None,
        },
        {
            "started_at": (now - timedelta(hours=20)).isoformat(),
            "completed_at": (now - timedelta(hours=20) + timedelta(minutes=4)).isoformat(),
            "status": "completed",
            "duration_seconds": 240.0,
            "tests_synced": 40,
            "error": None,
        },
    ]

    # Act
    result = await service.get_server_diagnostics()

    # Assert - 3 completed, 1 failed = 75% success rate
    assert result["sync"]["syncs_completed_24h"] == 3
    assert result["sync"]["syncs_failed_24h"] == 1
    assert result["sync"]["success_rate_24h"] == 75.0
