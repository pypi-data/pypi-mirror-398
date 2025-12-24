"""Unit tests for query_metrics MCP tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.tools.query_metrics_tool import QueryMetricsInput
from testio_mcp.tools.query_metrics_tool import query_metrics as query_metrics_tool
from tests.unit.test_utils import mock_service_context

query_metrics = query_metrics_tool.fn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rejects_invalid_status_values() -> None:
    """Verify invalid status values are rejected with clear error."""
    mock_ctx = MagicMock()

    with pytest.raises(ToolError) as exc_info:
        await query_metrics(
            metrics=["bug_count"],
            dimensions=["feature"],
            filters={"status": ["invalid_status", "another_bad_one"]},
            ctx=mock_ctx,
        )

    error_msg = str(exc_info.value)
    assert "❌ Invalid input" in error_msg
    assert "Invalid status values" in error_msg
    assert "invalid_status" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accepts_valid_status_values() -> None:
    """Verify valid status values pass validation."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.query_metrics.return_value = MagicMock(
        model_dump=MagicMock(return_value={"data": [], "metadata": {}, "query_explanation": ""})
    )

    with patch(
        "testio_mcp.tools.query_metrics_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await query_metrics(
            metrics=["bug_count"],
            dimensions=["feature"],
            filters={"status": ["running", "locked"]},
            ctx=mock_ctx,
        )

    # Should not raise, and service should be called
    assert mock_service.query_metrics.called


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accepts_single_status_string() -> None:
    """Verify single status string is accepted."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.query_metrics.return_value = MagicMock(
        model_dump=MagicMock(return_value={"data": [], "metadata": {}, "query_explanation": ""})
    )

    with patch(
        "testio_mcp.tools.query_metrics_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await query_metrics(
            metrics=["bug_count"],
            dimensions=["feature"],
            filters={"status": "running"},
            ctx=mock_ctx,
        )

    assert mock_service.query_metrics.called


@pytest.mark.unit
def test_pydantic_model_rejects_invalid_status() -> None:
    """Test QueryMetricsInput model validation directly."""
    with pytest.raises(ValueError) as exc_info:
        QueryMetricsInput(
            metrics=["bug_count"],
            dimensions=["feature"],
            filters={"status": ["invalid_status"]},
        )

    assert "Invalid status values" in str(exc_info.value)
    assert "invalid_status" in str(exc_info.value)


@pytest.mark.unit
def test_pydantic_model_accepts_valid_statuses() -> None:
    """Test QueryMetricsInput model accepts all valid statuses."""
    valid_statuses = [
        "running",
        "locked",
        "archived",
        "cancelled",
        "customer_finalized",
        "initialized",
    ]

    model = QueryMetricsInput(
        metrics=["bug_count"],
        dimensions=["feature"],
        filters={"status": valid_statuses},
    )

    assert model.filters == {"status": valid_statuses}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_without_status_filter() -> None:
    """Verify tool delegates correctly when no status filter provided."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.query_metrics.return_value = MagicMock(
        model_dump=MagicMock(return_value={"data": [], "metadata": {}, "query_explanation": ""})
    )

    with patch(
        "testio_mcp.tools.query_metrics_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await query_metrics(
            metrics=["bug_count"],
            dimensions=["feature"],
            ctx=mock_ctx,
        )

    call_args = mock_service.query_metrics.call_args
    assert call_args.kwargs["metrics"] == ["bug_count"]
    assert call_args.kwargs["dimensions"] == ["feature"]
    # Default: filters should be empty dict (service applies default status filter)
    assert call_args.kwargs["filters"] == {}
