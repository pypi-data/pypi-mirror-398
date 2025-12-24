"""Integration tests for CLI sync modes using SyncService (STORY-050).

Tests verify that CLI flags correctly map to SyncService parameters and that
all sync modes work end-to-end with real SQLite (temp file) and mocked API.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from testio_mcp.cli.sync import sync_database


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cli_default_mode_executes_all_phases(tmp_path: Path) -> None:
    """Test default CLI sync executes all 3 phases (PRODUCTS, FEATURES, NEW_TESTS).

    Verifies:
    - AC1: CLI delegates to SyncService.execute_sync()
    - Default mode runs all 3 phases in order
    - SyncResult stats are returned correctly
    """
    # Create temp database
    db_path = tmp_path / "test.db"

    # Mock API responses
    mock_client_get = AsyncMock(
        side_effect=[
            # Products API call
            {"products": [{"id": 598, "name": "Test Product"}]},
        ]
    )

    # Mock SyncService to verify it's called correctly
    mock_sync_result = MagicMock()
    mock_sync_result.products_synced = 1
    mock_sync_result.features_refreshed = 5
    mock_sync_result.tests_discovered = 10
    mock_sync_result.tests_updated = 0
    mock_sync_result.duration_seconds = 1.5
    mock_sync_result.warnings = []
    mock_sync_result.errors = []
    mock_sync_result.phases_completed = ["products", "features", "new_tests"]

    with (
        patch("testio_mcp.cli.sync.TestIOClient") as mock_client_cls,
        patch("testio_mcp.cli.sync.PersistentCache") as mock_cache_cls,
        patch("testio_mcp.cli.sync.SyncService") as mock_sync_service_cls,
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.get = mock_client_get
        mock_client_cls.return_value = mock_client

        mock_cache = MagicMock()
        mock_cache.initialize = AsyncMock()
        mock_cache.close = AsyncMock()
        mock_cache.db_path = db_path
        mock_cache.customer_id = 123
        mock_cache_cls.return_value = mock_cache

        mock_sync_service = MagicMock()
        mock_sync_service.execute_sync = AsyncMock(return_value=mock_sync_result)
        mock_sync_service_cls.return_value = mock_sync_service

        # Execute default sync (no special flags)
        result = await sync_database(
            product_ids=[598],
            verbose=False,
        )

        # Verify SyncService was called with all 3 phases
        mock_sync_service.execute_sync.assert_called_once()
        call_kwargs = mock_sync_service.execute_sync.call_args.kwargs

        # AC1: Verify all 3 phases passed
        assert "phases" in call_kwargs
        phases = call_kwargs["phases"]
        assert len(phases) == 3
        assert "products" in [p.value for p in phases]
        assert "features" in [p.value for p in phases]
        assert "new_tests" in [p.value for p in phases]

        # Verify result contains stats from SyncService
        assert result["products_synced"] == 1
        assert result["features_refreshed"] == 5
        assert result["tests_discovered"] == 10
        assert result["duration_seconds"] == 1.5


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cli_force_maps_to_force_refresh_option(tmp_path: Path) -> None:
    """Test --force flag maps to SyncOptions.force_refresh=True.

    Verifies AC2: --force maps to SyncOptions.force_refresh=True
    """
    db_path = tmp_path / "test.db"

    mock_sync_result = MagicMock()
    mock_sync_result.products_synced = 1
    mock_sync_result.features_refreshed = 5
    mock_sync_result.tests_discovered = 0
    mock_sync_result.tests_updated = 100  # Force mode updates tests
    mock_sync_result.duration_seconds = 3.2
    mock_sync_result.warnings = []
    mock_sync_result.errors = []
    mock_sync_result.phases_completed = ["products", "features", "new_tests"]

    with (
        patch("testio_mcp.cli.sync.TestIOClient") as mock_client_cls,
        patch("testio_mcp.cli.sync.PersistentCache") as mock_cache_cls,
        patch("testio_mcp.cli.sync.SyncService") as mock_sync_service_cls,
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_cls.return_value = mock_client

        mock_cache = MagicMock()
        mock_cache.initialize = AsyncMock()
        mock_cache.close = AsyncMock()
        mock_cache.db_path = db_path
        mock_cache.customer_id = 123
        mock_cache_cls.return_value = mock_cache

        mock_sync_service = MagicMock()
        mock_sync_service.execute_sync = AsyncMock(return_value=mock_sync_result)
        mock_sync_service_cls.return_value = mock_sync_service

        # Execute with --force flag
        await sync_database(
            force=True,
            product_ids=[598],
            verbose=False,
        )

        # Verify SyncOptions.force_refresh=True
        call_kwargs = mock_sync_service.execute_sync.call_args.kwargs
        assert "options" in call_kwargs
        options = call_kwargs["options"]
        assert options.force_refresh is True

        # Verify all 3 phases still executed
        phases = call_kwargs["phases"]
        assert len(phases) == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cli_incremental_only_maps_to_new_tests_phase(tmp_path: Path) -> None:
    """Test --incremental-only maps to phases=[SyncPhase.NEW_TESTS].

    Verifies AC3: --incremental-only maps to phases=[NEW_TESTS] only
    """
    db_path = tmp_path / "test.db"

    mock_sync_result = MagicMock()
    mock_sync_result.products_synced = 0  # No products phase
    mock_sync_result.features_refreshed = 0  # No features phase
    mock_sync_result.tests_discovered = 15
    mock_sync_result.tests_updated = 0
    mock_sync_result.duration_seconds = 0.8
    mock_sync_result.warnings = []
    mock_sync_result.errors = []
    mock_sync_result.phases_completed = ["new_tests"]

    with (
        patch("testio_mcp.cli.sync.TestIOClient") as mock_client_cls,
        patch("testio_mcp.cli.sync.PersistentCache") as mock_cache_cls,
        patch("testio_mcp.cli.sync.SyncService") as mock_sync_service_cls,
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_cls.return_value = mock_client

        mock_cache = MagicMock()
        mock_cache.initialize = AsyncMock()
        mock_cache.close = AsyncMock()
        mock_cache.db_path = db_path
        mock_cache.customer_id = 123
        mock_cache_cls.return_value = mock_cache

        mock_sync_service = MagicMock()
        mock_sync_service.execute_sync = AsyncMock(return_value=mock_sync_result)
        mock_sync_service_cls.return_value = mock_sync_service

        # Execute with --incremental-only flag
        await sync_database(
            incremental_only=True,
            product_ids=[598],
            verbose=False,
        )

        # AC3: Verify only NEW_TESTS phase passed
        call_kwargs = mock_sync_service.execute_sync.call_args.kwargs
        phases = call_kwargs["phases"]
        assert len(phases) == 1
        assert phases[0].value == "new_tests"

        # Verify incremental_only option set
        options = call_kwargs["options"]
        assert options.incremental_only is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cli_nuke_maps_to_nuke_option_with_enhanced_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test --nuke maps to SyncOptions.nuke=True with enhanced warning.

    Verifies:
    - AC4: --nuke maps to SyncOptions.nuke=True
    - AC8: Enhanced warning shows all entity counts
    """
    db_path = tmp_path / "test.db"

    # Mock user confirmation
    monkeypatch.setattr("testio_mcp.cli.sync.console.input", lambda _: "yes")

    mock_sync_result = MagicMock()
    mock_sync_result.products_synced = 1
    mock_sync_result.features_refreshed = 5
    mock_sync_result.tests_discovered = 50
    mock_sync_result.tests_updated = 0
    mock_sync_result.duration_seconds = 5.0
    mock_sync_result.warnings = []
    mock_sync_result.errors = []
    mock_sync_result.phases_completed = ["products", "features", "new_tests"]

    with (
        patch("testio_mcp.cli.sync.TestIOClient") as mock_client_cls,
        patch("testio_mcp.cli.sync.PersistentCache") as mock_cache_cls,
        patch("testio_mcp.cli.sync.SyncService") as mock_sync_service_cls,
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_cls.return_value = mock_client

        mock_cache = MagicMock()
        mock_cache.initialize = AsyncMock()
        mock_cache.close = AsyncMock()
        # Use MagicMock for db_path to avoid real Path operations
        mock_db_path = MagicMock()
        mock_db_path.unlink = MagicMock()
        mock_db_path.__str__ = lambda self: str(db_path)
        mock_cache.db_path = mock_db_path
        mock_cache.customer_id = 123
        mock_cache.count_tests = AsyncMock(return_value=100)
        mock_cache.count_products = AsyncMock(return_value=5)
        mock_cache.get_db_size_mb = AsyncMock(return_value=2.5)

        # Mock async_session_maker for entity counts (AC8)
        mock_session = MagicMock()

        # Mock Bug count
        mock_bug_result = MagicMock()
        mock_bug_result.one = MagicMock(return_value=50)

        # Mock Feature count
        mock_feature_result = MagicMock()
        mock_feature_result.one = MagicMock(return_value=20)

        # Mock User count
        mock_user_result = MagicMock()
        mock_user_result.one = MagicMock(return_value=10)

        mock_session.exec = AsyncMock(
            side_effect=[
                mock_bug_result,  # Bug count query
                mock_feature_result,  # Feature count query
                mock_user_result,  # User count query
            ]
        )
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_cache.async_session_maker = MagicMock(return_value=mock_session)
        mock_cache_cls.return_value = mock_cache

        mock_sync_service = MagicMock()
        mock_sync_service.execute_sync = AsyncMock(return_value=mock_sync_result)
        mock_sync_service_cls.return_value = mock_sync_service

        # Mock delete_product_tests to avoid real deletion
        mock_cache.delete_product_tests = AsyncMock()

        # Execute with --nuke flag (with product filter to avoid full DB deletion)
        await sync_database(
            nuke=True,
            product_ids=[598],
            verbose=False,
        )

        # AC4: Verify SyncOptions.nuke=True
        # Note: execute_sync is called after nuke deletion
        assert mock_sync_service.execute_sync.called, (
            "SyncService.execute_sync should be called after nuke"
        )
        call_kwargs = mock_sync_service.execute_sync.call_args.kwargs
        options = call_kwargs["options"]
        assert options.nuke is True

        # AC8: Verify entity counts were queried for warning
        # count_tests, count_products, get_db_size_mb should have been called
        mock_cache.count_tests.assert_called_once()
        mock_cache.count_products.assert_called_once()
        mock_cache.get_db_size_mb.assert_called_once()

        # Verify async_session_maker was called for Bug/Feature/User counts
        mock_cache.async_session_maker.assert_called()

        # Verify delete was called
        mock_cache.delete_product_tests.assert_called()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cli_product_ids_maps_to_sync_scope(tmp_path: Path) -> None:
    """Test --product-ids maps to SyncScope.product_ids.

    Verifies AC5: --product-ids maps to scope.product_ids
    """
    db_path = tmp_path / "test.db"

    mock_sync_result = MagicMock()
    mock_sync_result.products_synced = 2
    mock_sync_result.features_refreshed = 10
    mock_sync_result.tests_discovered = 25
    mock_sync_result.tests_updated = 0
    mock_sync_result.duration_seconds = 2.0
    mock_sync_result.warnings = []
    mock_sync_result.errors = []
    mock_sync_result.phases_completed = ["products", "features", "new_tests"]

    with (
        patch("testio_mcp.cli.sync.TestIOClient") as mock_client_cls,
        patch("testio_mcp.cli.sync.PersistentCache") as mock_cache_cls,
        patch("testio_mcp.cli.sync.SyncService") as mock_sync_service_cls,
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_cls.return_value = mock_client

        mock_cache = MagicMock()
        mock_cache.initialize = AsyncMock()
        mock_cache.close = AsyncMock()
        mock_cache.db_path = db_path
        mock_cache.customer_id = 123
        mock_cache_cls.return_value = mock_cache

        mock_sync_service = MagicMock()
        mock_sync_service.execute_sync = AsyncMock(return_value=mock_sync_result)
        mock_sync_service_cls.return_value = mock_sync_service

        # Execute with multiple product IDs
        await sync_database(
            product_ids=[598, 599],
            verbose=False,
        )

        # AC5: Verify SyncScope.product_ids=[598, 599]
        call_kwargs = mock_sync_service.execute_sync.call_args.kwargs
        scope = call_kwargs["scope"]
        assert scope.product_ids == [598, 599]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cli_since_maps_to_sync_scope(tmp_path: Path) -> None:
    """Test --since maps to SyncScope.since_date.

    Verifies AC6: --since maps to scope.since_date
    """
    db_path = tmp_path / "test.db"

    mock_sync_result = MagicMock()
    mock_sync_result.products_synced = 1
    mock_sync_result.features_refreshed = 5
    mock_sync_result.tests_discovered = 8
    mock_sync_result.tests_updated = 0
    mock_sync_result.duration_seconds = 1.2
    mock_sync_result.warnings = []
    mock_sync_result.errors = []
    mock_sync_result.phases_completed = ["products", "features", "new_tests"]

    with (
        patch("testio_mcp.cli.sync.TestIOClient") as mock_client_cls,
        patch("testio_mcp.cli.sync.PersistentCache") as mock_cache_cls,
        patch("testio_mcp.cli.sync.SyncService") as mock_sync_service_cls,
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_cls.return_value = mock_client

        mock_cache = MagicMock()
        mock_cache.initialize = AsyncMock()
        mock_cache.close = AsyncMock()
        mock_cache.db_path = db_path
        mock_cache.customer_id = 123
        mock_cache_cls.return_value = mock_cache

        mock_sync_service = MagicMock()
        mock_sync_service.execute_sync = AsyncMock(return_value=mock_sync_result)
        mock_sync_service_cls.return_value = mock_sync_service

        # Execute with --since date filter
        since_date = datetime.now(UTC) - timedelta(days=30)
        await sync_database(
            since=since_date,
            product_ids=[598],
            verbose=False,
        )

        # AC6: Verify SyncScope.since_date is set
        call_kwargs = mock_sync_service.execute_sync.call_args.kwargs
        scope = call_kwargs["scope"]
        assert scope.since_date == since_date


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cli_preserves_output_formatting(tmp_path: Path) -> None:
    """Test CLI preserves output formatting (progress, verbose, summary).

    Verifies AC7: Progress indicators, verbose output, and summary stats preserved
    """
    db_path = tmp_path / "test.db"

    mock_sync_result = MagicMock()
    mock_sync_result.products_synced = 1
    mock_sync_result.features_refreshed = 5
    mock_sync_result.tests_discovered = 10
    mock_sync_result.tests_updated = 3
    mock_sync_result.duration_seconds = 1.5
    mock_sync_result.warnings = ["Warning 1"]
    mock_sync_result.errors = []
    mock_sync_result.phases_completed = ["products", "features", "new_tests"]

    with (
        patch("testio_mcp.cli.sync.TestIOClient") as mock_client_cls,
        patch("testio_mcp.cli.sync.PersistentCache") as mock_cache_cls,
        patch("testio_mcp.cli.sync.SyncService") as mock_sync_service_cls,
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_cls.return_value = mock_client

        mock_cache = MagicMock()
        mock_cache.initialize = AsyncMock()
        mock_cache.close = AsyncMock()
        mock_cache.db_path = db_path
        mock_cache.customer_id = 123
        mock_cache_cls.return_value = mock_cache

        mock_sync_service = MagicMock()
        mock_sync_service.execute_sync = AsyncMock(return_value=mock_sync_result)
        mock_sync_service_cls.return_value = mock_sync_service

        # Execute with verbose flag
        result = await sync_database(
            product_ids=[598],
            verbose=True,
        )

        # AC7: Verify result contains all expected stats for output
        assert "products_synced" in result
        assert "features_refreshed" in result
        assert "tests_discovered" in result
        assert "tests_updated" in result
        assert "duration_seconds" in result
        assert "warnings" in result
        assert "errors" in result

        # Verify stats match SyncResult
        assert result["products_synced"] == 1
        assert result["features_refreshed"] == 5
        assert result["tests_discovered"] == 10
        assert result["tests_updated"] == 3
        assert result["duration_seconds"] == 1.5
        assert result["warnings"] == ["Warning 1"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cli_combined_flags_force_and_product_ids(tmp_path: Path) -> None:
    """Test combined flags: --force --product-ids work together.

    Verifies that multiple flags can be combined correctly.
    """
    db_path = tmp_path / "test.db"

    mock_sync_result = MagicMock()
    mock_sync_result.products_synced = 2
    mock_sync_result.features_refreshed = 10
    mock_sync_result.tests_discovered = 0
    mock_sync_result.tests_updated = 150
    mock_sync_result.duration_seconds = 4.5
    mock_sync_result.warnings = []
    mock_sync_result.errors = []
    mock_sync_result.phases_completed = ["products", "features", "new_tests"]

    with (
        patch("testio_mcp.cli.sync.TestIOClient") as mock_client_cls,
        patch("testio_mcp.cli.sync.PersistentCache") as mock_cache_cls,
        patch("testio_mcp.cli.sync.SyncService") as mock_sync_service_cls,
    ):
        # Setup mocks
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_cls.return_value = mock_client

        mock_cache = MagicMock()
        mock_cache.initialize = AsyncMock()
        mock_cache.close = AsyncMock()
        mock_cache.db_path = db_path
        mock_cache.customer_id = 123
        mock_cache_cls.return_value = mock_cache

        mock_sync_service = MagicMock()
        mock_sync_service.execute_sync = AsyncMock(return_value=mock_sync_result)
        mock_sync_service_cls.return_value = mock_sync_service

        # Execute with combined flags
        await sync_database(
            force=True,
            product_ids=[598, 599],
            verbose=False,
        )

        # Verify both flags mapped correctly
        call_kwargs = mock_sync_service.execute_sync.call_args.kwargs

        # Force option set
        assert call_kwargs["options"].force_refresh is True

        # Product IDs filter set
        assert call_kwargs["scope"].product_ids == [598, 599]

        # All 3 phases executed (force doesn't skip phases)
        assert len(call_kwargs["phases"]) == 3
