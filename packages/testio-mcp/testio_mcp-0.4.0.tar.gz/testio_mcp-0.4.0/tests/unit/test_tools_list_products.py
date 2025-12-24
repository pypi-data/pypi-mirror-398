"""Unit tests for list_products MCP tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.exceptions import TestIOAPIError
from testio_mcp.tools.list_products_tool import list_products as list_products_tool
from tests.unit.test_utils import mock_service_context

list_products = list_products_tool.fn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_api_error_to_tool_error() -> None:
    """Verify TestIOAPIError → ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_products.side_effect = TestIOAPIError(message="Error", status_code=500)

    with patch(
        "testio_mcp.tools.list_products_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await list_products(ctx=mock_ctx)

        assert "❌" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_without_filters() -> None:
    """Verify tool delegates with no filters."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    # STORY-058: Added test_count, bug_count, feature_count to response
    mock_service.list_products.return_value = {
        "total_count": 1,
        "filters_applied": {},
        "products": [
            {
                "id": 1,
                "name": "Test Product",
                "type": "web",
                "test_count": 5,
                "bug_count": 3,
                "feature_count": 2,
                "tests_last_30_days": 1,
                "tests_last_90_days": 3,
                "last_test_end_at": "2025-11-28T00:00:00+00:00",
            }
        ],
    }

    with patch(
        "testio_mcp.tools.list_products_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_products(ctx=mock_ctx)

        # STORY-055: Added sort and pagination params
        mock_service.list_products.assert_called_once_with(
            search=None,
            product_type=None,
            sort_by=None,
            sort_order="asc",
            page=1,
            per_page=50,
            offset=0,
        )
        assert "products" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_search_filter() -> None:
    """Verify tool passes search parameter."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_products.return_value = {
        "total_count": 0,
        "filters_applied": {"search": "test"},
        "products": [],
    }

    with patch(
        "testio_mcp.tools.list_products_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await list_products(search="test", ctx=mock_ctx)

        call_args = mock_service.list_products.call_args
        assert call_args.kwargs["search"] == "test"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_product_type_filter() -> None:
    """Verify tool parses product_type string to list."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_products.return_value = {
        "total_count": 0,
        "filters_applied": {"product_type": ["website"]},
        "products": [],
    }

    with patch(
        "testio_mcp.tools.list_products_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await list_products(product_type="website", ctx=mock_ctx)

        call_args = mock_service.list_products.call_args
        # Verify product_type parsed to list
        assert call_args.kwargs["product_type"] == ["website"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validates_literal_product_types() -> None:
    """Verify Pydantic validates product_type against Literal type."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_products.return_value = {
        "total_count": 0,
        "filters_applied": {"product_type": ["mobile_app_ios"]},
        "products": [],
    }

    with patch(
        "testio_mcp.tools.list_products_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        # Valid Literal value passes through (parsed to list)
        await list_products(product_type="mobile_app_ios", ctx=mock_ctx)

        call_args = mock_service.list_products.call_args
        assert call_args.kwargs["product_type"] == ["mobile_app_ios"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parses_comma_separated_product_types() -> None:
    """Verify tool parses comma-separated string to list (AI-friendly format)."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_products.return_value = {
        "total_count": 0,
        "filters_applied": {"product_type": ["mobile_app_ios", "mobile_app_android"]},
        "products": [],
    }

    with patch(
        "testio_mcp.tools.list_products_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        # Pass comma-separated string
        await list_products(product_type="mobile_app_ios,mobile_app_android", ctx=mock_ctx)

        call_args = mock_service.list_products.call_args
        # Verify parsed to list
        assert call_args.kwargs["product_type"] == ["mobile_app_ios", "mobile_app_android"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_product_type_array() -> None:
    """Verify tool handles product_type as array."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_products.return_value = {
        "total_count": 0,
        "filters_applied": {"product_type": ["website", "mobile_app_ios"]},
        "products": [],
    }

    with patch(
        "testio_mcp.tools.list_products_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        # Pass array directly
        await list_products(product_type=["website", "mobile_app_ios"], ctx=mock_ctx)

        call_args = mock_service.list_products.call_args
        # Verify passed through as list
        assert call_args.kwargs["product_type"] == ["website", "mobile_app_ios"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_whitespace_in_comma_separated_types() -> None:
    """Verify tool strips whitespace from comma-separated values."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_products.return_value = {
        "total_count": 0,
        "filters_applied": {"product_type": ["website", "mobile_app_ios"]},
        "products": [],
    }

    with patch(
        "testio_mcp.tools.list_products_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        # Pass with extra whitespace
        await list_products(product_type="website, mobile_app_ios", ctx=mock_ctx)

        call_args = mock_service.list_products.call_args
        # Verify whitespace stripped
        assert call_args.kwargs["product_type"] == ["website", "mobile_app_ios"]
