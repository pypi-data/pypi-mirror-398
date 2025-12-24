"""Unit tests for sync_data MCP tool.

STORY-051: sync_data MCP Tool (AC8)
- Test parameter mapping to SyncScope/SyncOptions
- Test date parsing (ISO, relative formats)
- Test error handling (domain exceptions → ToolError)
- Test delegation to SyncService

TD-001: Updated to use get_service_context (async context manager pattern)
"""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.services.sync_service import (
    SyncLockError,
    SyncOptions,
    SyncPhase,
    SyncResult,
    SyncScope,
    SyncTimeoutError,
)
from testio_mcp.tools.sync_data_tool import sync_data as sync_data_tool

# Extract actual function from FastMCP FunctionTool wrapper
sync_data = sync_data_tool.fn  # type: ignore[attr-defined]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_successful_sync_without_warnings() -> None:
    """AC8: Test successful sync returns correct stats."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()

    # Mock successful sync result
    mock_result = SyncResult(
        phases_completed=[SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS],
        products_synced=3,
        features_refreshed=42,
        tests_discovered=15,
        tests_updated=0,
        duration_seconds=30.5,
        warnings=[],
        errors=[],
    )
    mock_service.execute_sync.return_value = mock_result

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        result = await sync_data(ctx=mock_ctx)

        # Verify response structure (AC6)
        assert result["status"] == "completed"
        assert result["products_synced"] == 3
        assert result["features_refreshed"] == 42
        assert result["tests_discovered"] == 15
        assert result["tests_updated"] == 0
        assert result["duration_seconds"] == 30.5
        assert "warnings" not in result  # Excluded when None

        # Verify timestamp updated (AC4)
        mock_service.cache.set_metadata_value.assert_called_once()
        call_args = mock_service.cache.set_metadata_value.call_args
        assert call_args.kwargs["key"] == "last_sync_completed"
        # Verify timestamp is ISO 8601 UTC string
        timestamp_str = call_args.kwargs["value"]
        timestamp = datetime.fromisoformat(timestamp_str)
        assert timestamp.tzinfo is not None  # Timezone-aware


@pytest.mark.unit
@pytest.mark.asyncio
async def test_successful_sync_with_warnings() -> None:
    """AC8: Test sync with warnings returns correct status."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()

    # Mock sync result with warnings
    mock_result = SyncResult(
        phases_completed=[SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS],
        products_synced=2,
        features_refreshed=30,
        tests_discovered=10,
        tests_updated=0,
        duration_seconds=25.0,
        warnings=["Product 999 not found - skipped"],
        errors=[],
    )
    mock_service.execute_sync.return_value = mock_result

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        result = await sync_data(ctx=mock_ctx)

        # Verify status reflects warnings (AC6)
        assert result["status"] == "completed_with_warnings"
        assert result["tests_updated"] == 0
        assert result["warnings"] == ["Product 999 not found - skipped"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parameter_mapping_product_ids() -> None:
    """AC3: Test product_ids parameter maps to SyncScope.product_ids."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()
    mock_service.execute_sync.return_value = SyncResult(duration_seconds=10.0)

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        await sync_data(ctx=mock_ctx, product_ids=[598, 599])

        # Verify SyncScope mapping (AC3)
        call_args = mock_service.execute_sync.call_args
        scope: SyncScope = call_args.kwargs["scope"]
        assert scope.product_ids == [598, 599]
        assert scope.since_date is None

        # Verify all 3 phases passed (AC3)
        phases = call_args.kwargs["phases"]
        assert phases == [SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parameter_mapping_since_all() -> None:
    """Test since='all' maps to force_refresh=True with no date filter."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()
    mock_service.execute_sync.return_value = SyncResult(duration_seconds=10.0)

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        await sync_data(ctx=mock_ctx, since="all")

        # Verify mapping: since="all" → force_refresh=True, since_date=None
        call_args = mock_service.execute_sync.call_args
        scope: SyncScope = call_args.kwargs["scope"]
        options: SyncOptions = call_args.kwargs["options"]
        assert options.force_refresh is True
        assert scope.since_date is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parameter_mapping_since_iso() -> None:
    """Test since parameter (ISO 8601) maps correctly and enables force_refresh."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()
    mock_service.execute_sync.return_value = SyncResult(duration_seconds=10.0)

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        await sync_data(ctx=mock_ctx, since="2025-11-01")

        # Verify date parsed correctly
        call_args = mock_service.execute_sync.call_args
        scope: SyncScope = call_args.kwargs["scope"]
        options: SyncOptions = call_args.kwargs["options"]

        assert scope.since_date is not None
        assert scope.since_date.year == 2025
        assert scope.since_date.month == 11
        assert scope.since_date.day == 1
        assert scope.since_date.tzinfo is not None  # Timezone-aware

        # Verify force_refresh auto-enabled to disable known-test early-stop
        assert options.force_refresh is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parameter_mapping_since_relative() -> None:
    """Test since parameter (relative date) maps correctly and enables force_refresh."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()
    mock_service.execute_sync.return_value = SyncResult(duration_seconds=10.0)

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        # Test relative date parsing
        await sync_data(ctx=mock_ctx, since="30 days ago")

        # Verify date parsed (should be ~30 days before today)
        call_args = mock_service.execute_sync.call_args
        scope: SyncScope = call_args.kwargs["scope"]
        options: SyncOptions = call_args.kwargs["options"]

        assert scope.since_date is not None
        assert scope.since_date.tzinfo is not None

        # Verify it's approximately 30 days ago (within 1 day tolerance)
        now = datetime.now(UTC)
        days_diff = (now - scope.since_date).days
        assert 29 <= days_diff <= 31

        # Verify force_refresh auto-enabled to disable known-test early-stop
        assert options.force_refresh is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_sync_lock_error_to_tool_error() -> None:
    """AC8: Test SyncLockError → ToolError transformation."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()
    mock_service.execute_sync.side_effect = SyncLockError("Lock held")

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        with pytest.raises(ToolError) as exc_info:
            await sync_data(ctx=mock_ctx)

        # Verify error format (❌ℹ️💡 pattern)
        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "Sync already in progress" in error_msg
        assert "ℹ️" in error_msg
        assert "💡" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_sync_timeout_error_to_tool_error() -> None:
    """AC8: Test SyncTimeoutError → ToolError transformation."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()
    mock_service.execute_sync.side_effect = SyncTimeoutError("Timeout")

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        with pytest.raises(ToolError) as exc_info:
            await sync_data(ctx=mock_ctx)

        # Verify error format
        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "timeout" in error_msg.lower()
        assert "ℹ️" in error_msg
        assert "💡" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_unexpected_error_to_tool_error() -> None:
    """AC8: Test unexpected error → ToolError transformation."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()
    mock_service.execute_sync.side_effect = RuntimeError("Unexpected failure")

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        with pytest.raises(ToolError) as exc_info:
            await sync_data(ctx=mock_ctx)

        # Verify error format
        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "Sync failed unexpectedly" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_trigger_source() -> None:
    """AC3: Verify trigger_source='mcp' passed to execute_sync."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()
    mock_service.execute_sync.return_value = SyncResult(duration_seconds=10.0)

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        await sync_data(ctx=mock_ctx)

        # Verify trigger_source (AC3)
        call_args = mock_service.execute_sync.call_args
        assert call_args.kwargs["trigger_source"] == "mcp"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_default_parameters() -> None:
    """Test default parameter values (incremental mode)."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.cache = AsyncMock()
    mock_service.execute_sync.return_value = SyncResult(duration_seconds=10.0)

    @asynccontextmanager
    async def mock_get_service_context(*args, **kwargs):
        yield mock_service

    with patch("testio_mcp.tools.sync_data_tool.get_service_context", mock_get_service_context):
        await sync_data(ctx=mock_ctx)

        # Verify defaults: incremental mode (since=None → force_refresh=False)
        call_args = mock_service.execute_sync.call_args
        scope: SyncScope = call_args.kwargs["scope"]
        options: SyncOptions = call_args.kwargs["options"]

        assert scope.product_ids is None  # Default: all products
        assert scope.since_date is None  # Default: no date filter
        assert options.force_refresh is False  # Default: incremental (early-stop enabled)
