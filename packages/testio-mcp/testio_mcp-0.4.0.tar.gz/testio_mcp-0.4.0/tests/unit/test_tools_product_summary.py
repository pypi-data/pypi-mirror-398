"""Unit tests for get_product_summary MCP tool.

STORY-057: Add Summary Tools (Epic 008)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.exceptions import ProductNotFoundException, TestIOAPIError
from testio_mcp.tools.product_summary_tool import get_product_summary as get_product_summary_tool
from tests.unit.test_utils import mock_service_context

# Extract actual function from FastMCP FunctionTool wrapper
get_product_summary = get_product_summary_tool.fn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_not_found_to_tool_error() -> None:
    """Verify ProductNotFoundException → ToolError with ❌ℹ️💡 format."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_summary.side_effect = ProductNotFoundException(product_id=598)

    with patch(
        "testio_mcp.tools.product_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await get_product_summary(product_id=598, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "not found" in error_msg.lower()
        assert "ℹ️" in error_msg
        assert "💡" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_api_error_to_tool_error() -> None:
    """Verify TestIOAPIError → ToolError with status code."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_summary.side_effect = TestIOAPIError(
        message="Timeout", status_code=504
    )

    with patch(
        "testio_mcp.tools.product_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await get_product_summary(product_id=598, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "504" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_to_service_correctly() -> None:
    """Verify tool delegates to ProductService with correct parameters."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_summary.return_value = {
        "id": 598,
        "title": "Canva",
        "type": "website",
        "description": "Design platform",
        "test_count": 216,
        "feature_count": 45,
        "last_synced": "2025-11-28T10:30:00Z",
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    with patch(
        "testio_mcp.tools.product_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_product_summary(product_id=598, ctx=mock_ctx)

        mock_service.get_product_summary.assert_called_once_with(598)
        assert result["id"] == 598
        assert result["title"] == "Canva"
        assert result["test_count"] == 216
        # STORY-083: bug_count removed
        assert result["feature_count"] == 45


@pytest.mark.unit
@pytest.mark.asyncio
async def test_returns_correct_structure() -> None:
    """Verify output includes all required fields."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_summary.return_value = {
        "id": 598,
        "title": "Canva",
        "type": "website",
        "description": "Design platform",
        "test_count": 216,
        "feature_count": 45,
        "last_synced": "2025-11-28T10:30:00Z",
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    with patch(
        "testio_mcp.tools.product_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_product_summary(product_id=598, ctx=mock_ctx)

        # Verify all required fields present
        assert "id" in result
        assert "title" in result
        assert "type" in result
        assert "test_count" in result
        # STORY-083: bug_count removed
        assert "feature_count" in result
        assert "data_as_of" in result

        # Verify counts are non-negative
        assert result["test_count"] >= 0
        assert result["feature_count"] >= 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_invalid_product_id() -> None:
    """Verify input validation rejects invalid product_id."""
    mock_ctx = MagicMock()

    with patch(
        "testio_mcp.tools.product_summary_tool.get_service_context",
        return_value=mock_service_context(AsyncMock()),
    ):
        # Test with negative ID
        with pytest.raises(ToolError) as exc_info:
            await get_product_summary(product_id=-1, ctx=mock_ctx)

        assert "❌" in str(exc_info.value)
        assert "Invalid" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_zero_counts() -> None:
    """Verify tool handles products with zero counts correctly."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_summary.return_value = {
        "id": 100,
        "title": "New Product",
        "type": "website",
        "description": None,
        "test_count": 0,
        "feature_count": 0,
        "last_synced": None,
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    with patch(
        "testio_mcp.tools.product_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_product_summary(product_id=100, ctx=mock_ctx)

        assert result["test_count"] == 0
        # STORY-083: bug_count removed
        assert result["feature_count"] == 0
