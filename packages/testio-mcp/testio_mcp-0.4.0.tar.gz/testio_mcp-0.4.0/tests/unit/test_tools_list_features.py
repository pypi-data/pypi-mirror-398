"""Unit tests for list_features MCP tool.

STORY-037: Data Serving Layer (MCP Tools + REST API)
STORY-040: Pagination for Data-Serving Tools
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.tools.list_features_tool import list_features as list_features_tool
from tests.unit.test_utils import mock_service_context

list_features = list_features_tool.fn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_to_service() -> None:
    """Verify tool delegates to FeatureService.list_features with default pagination."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_features.return_value = {
        "product_id": 598,
        "features": [
            {
                "id": 1,
                "title": "Login Feature",
                "description": "User authentication",
                "howtofind": "Go to login page",
                "user_story_count": 2,
                "test_count": 5,
                "bug_count": 3,
            }
        ],
        "total": 1,
        "total_count": 1,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_features_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_features(product_id=598, ctx=mock_ctx)

        # Verify service called with default pagination params (STORY-055: Added sort params)
        # STORY-058: Added has_user_stories parameter
        mock_service.list_features.assert_called_once_with(
            product_id=598,
            page=1,
            per_page=100,
            offset=0,
            sort_by=None,
            sort_order="asc",
            has_user_stories=None,
        )
        assert result["product_id"] == 598
        assert result["total"] == 1
        assert len(result["features"]) == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_returns_validated_output_with_pagination() -> None:
    """Verify tool validates output with Pydantic model including pagination."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_features.return_value = {
        "product_id": 598,
        "features": [],
        "total": 0,
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_features_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_features(product_id=598, ctx=mock_ctx)

        # Verify Pydantic validation passed
        assert "product_id" in result
        assert "features" in result
        assert "total" in result
        assert "pagination" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_exception_to_tool_error() -> None:
    """Verify generic exception → ToolError with user-friendly message."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_features.side_effect = Exception("Database error")

    with patch(
        "testio_mcp.tools.list_features_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await list_features(product_id=598, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "598" in error_msg
        assert "ℹ️" in error_msg
        assert "💡" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_empty_result() -> None:
    """Verify tool handles products with no features."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_features.return_value = {
        "product_id": 999,
        "features": [],
        "total": 0,
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_features_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_features(product_id=999, ctx=mock_ctx)

        assert result["total"] == 0
        assert result["features"] == []
        # Verify pagination for empty results
        assert result["pagination"]["end_index"] == -1


# STORY-040: Pagination Tests


@pytest.mark.unit
@pytest.mark.asyncio
async def test_pagination_parameters_passed_to_service() -> None:
    """Verify pagination parameters are passed to service (AC9)."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_features.return_value = {
        "product_id": 598,
        "features": [],
        "total": 0,
        "total_count": 0,
        "offset": 60,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_features_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await list_features(product_id=598, page=2, per_page=50, offset=10, ctx=mock_ctx)

        # STORY-055: Added sort params
        # STORY-058: Added has_user_stories parameter
        mock_service.list_features.assert_called_once_with(
            product_id=598,
            page=2,
            per_page=50,
            offset=10,
            sort_by=None,
            sort_order="asc",
            has_user_stories=None,
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_pagination_metadata_calculation() -> None:
    """Verify PaginationInfo calculation (start_index, end_index, has_more) (AC9)."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_features.return_value = {
        "product_id": 598,
        "features": [
            {
                "id": i,
                "title": f"Feature {i}",
                "user_story_count": 0,
                "test_count": 0,
                "bug_count": 0,
            }
            for i in range(50)
        ],
        "total": 50,
        "total_count": 150,
        "offset": 100,
        "has_more": True,
    }

    with patch(
        "testio_mcp.tools.list_features_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_features(product_id=598, page=3, per_page=50, ctx=mock_ctx)

        # Verify pagination metadata
        assert result["pagination"]["page"] == 3
        assert result["pagination"]["per_page"] == 50
        assert result["pagination"]["offset"] == 100
        assert result["pagination"]["start_index"] == 100
        assert result["pagination"]["end_index"] == 149
        assert result["pagination"]["total_count"] == 150
        assert result["pagination"]["has_more"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_default_per_page_uses_settings() -> None:
    """Verify default per_page=0 uses TESTIO_DEFAULT_PAGE_SIZE (AC9)."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_features.return_value = {
        "product_id": 598,
        "features": [],
        "total": 0,
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_features_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        # Call without per_page (defaults to 0, which should use settings.TESTIO_DEFAULT_PAGE_SIZE)
        result = await list_features(product_id=598, ctx=mock_ctx)

        # Verify service called with default page size (100) (STORY-055: Added sort params)
        # STORY-058: Added has_user_stories parameter
        mock_service.list_features.assert_called_once_with(
            product_id=598,
            page=1,
            per_page=100,
            offset=0,
            sort_by=None,
            sort_order="asc",
            has_user_stories=None,
        )
        # Verify response shows effective per_page
        assert result["pagination"]["per_page"] == 100
