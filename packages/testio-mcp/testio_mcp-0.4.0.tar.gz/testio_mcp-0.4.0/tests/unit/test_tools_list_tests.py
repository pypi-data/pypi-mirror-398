"""Unit tests for list_tests MCP tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.exceptions import ProductNotFoundException, TestIOAPIError
from testio_mcp.tools.list_tests_tool import list_tests as list_tests_tool
from tests.unit.test_utils import mock_service_context

list_tests = list_tests_tool.fn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_product_not_found_to_tool_error() -> None:
    """Verify ProductNotFoundException → ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.side_effect = ProductNotFoundException(product_id=999)

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await list_tests(product_id=999, ctx=mock_ctx)

        assert "❌" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_api_error_to_tool_error() -> None:
    """Verify TestIOAPIError → ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.side_effect = TestIOAPIError(message="Error", status_code=503)

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await list_tests(product_id=123, ctx=mock_ctx)

        assert "❌" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_without_filters() -> None:
    """Verify tool delegates with minimal parameters."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test Product", "type": "web"},
        "statuses_filter": [],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await list_tests(product_id=123, ctx=mock_ctx)

        call_args = mock_service.list_tests.call_args
        assert call_args.kwargs["product_id"] == 123
        assert call_args.kwargs["statuses"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_status_filter() -> None:
    """Verify tool passes status filter (Literal types are strings)."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": ["running"],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await list_tests(product_id=123, statuses=["running"], ctx=mock_ctx)

        call_args = mock_service.list_tests.call_args
        # Verify statuses passed through as strings (Literal types)
        assert call_args.kwargs["statuses"] == ["running"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_multiple_status_filters() -> None:
    """Verify tool handles multiple status values (Literal types)."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": ["running", "locked"],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await list_tests(
            product_id=123,
            statuses=["running", "locked"],
            ctx=mock_ctx,
        )

        call_args = mock_service.list_tests.call_args
        # Verify statuses passed through as strings (Literal types)
        assert call_args.kwargs["statuses"] == ["running", "locked"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validates_literal_status_values() -> None:
    """Verify Pydantic validates status values against Literal type."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": ["running", "archived"],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        # Valid Literal values pass through
        await list_tests(
            product_id=123,
            statuses=["running", "archived"],
            ctx=mock_ctx,
        )

        call_args = mock_service.list_tests.call_args
        assert call_args.kwargs["statuses"] == ["running", "archived"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parses_comma_separated_string() -> None:
    """Verify tool parses comma-separated string to list (AI-friendly format)."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": ["running", "locked"],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        # Pass comma-separated string
        await list_tests(product_id=123, statuses="running,locked", ctx=mock_ctx)

        call_args = mock_service.list_tests.call_args
        # Verify parsed to list
        assert call_args.kwargs["statuses"] == ["running", "locked"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parses_single_status_string() -> None:
    """Verify tool handles single status as string."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": ["running"],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        # Pass single status as string (no comma)
        await list_tests(product_id=123, statuses="running", ctx=mock_ctx)

        call_args = mock_service.list_tests.call_args
        # Verify parsed to list with single element
        assert call_args.kwargs["statuses"] == ["running"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_whitespace_in_comma_separated() -> None:
    """Verify tool strips whitespace from comma-separated values."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": ["running", "locked"],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        # Pass with extra whitespace
        await list_tests(product_id=123, statuses="running, locked", ctx=mock_ctx)

        call_args = mock_service.list_tests.call_args
        # Verify whitespace stripped
        assert call_args.kwargs["statuses"] == ["running", "locked"]


# STORY-020: Pagination tests


@pytest.mark.unit
@pytest.mark.asyncio
async def test_defaults_to_page_1() -> None:
    """Verify tool defaults to page 1 when not specified."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": [],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await list_tests(product_id=123, ctx=mock_ctx)

        call_args = mock_service.list_tests.call_args
        assert call_args.kwargs["page"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_uses_default_page_size_from_settings() -> None:
    """Verify tool uses TESTIO_DEFAULT_PAGE_SIZE when per_page not specified."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": [],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        # Patch settings at the config module level (where it's imported from)
        with patch("testio_mcp.config.settings") as mock_settings:
            mock_settings.TESTIO_DEFAULT_PAGE_SIZE = 100

            await list_tests(product_id=123, ctx=mock_ctx)

            call_args = mock_service.list_tests.call_args
            assert call_args.kwargs["per_page"] == 100


@pytest.mark.unit
@pytest.mark.asyncio
async def test_passes_explicit_page_and_per_page() -> None:
    """Verify tool passes explicit pagination parameters."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": [],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await list_tests(product_id=123, page=2, per_page=50, ctx=mock_ctx)

        call_args = mock_service.list_tests.call_args
        assert call_args.kwargs["page"] == 2
        assert call_args.kwargs["per_page"] == 50


@pytest.mark.unit
@pytest.mark.asyncio
async def test_includes_pagination_in_output() -> None:
    """Verify tool output includes pagination metadata."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": [],
        "tests": [],
        "total_count": 100,
        "offset": 100,  # Offset for page 2
        "has_more": True,  # More results available
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_tests(product_id=123, page=2, per_page=50, ctx=mock_ctx)

        # Verify pagination metadata in output
        assert "pagination" in result
        assert result["pagination"]["page"] == 2
        assert result["pagination"]["per_page"] == 50
        assert result["pagination"]["offset"] == 100
        assert result["pagination"]["start_index"] == 100
        assert result["pagination"]["end_index"] == -1  # Empty results
        assert result["pagination"]["total_count"] == 100
        assert result["pagination"]["has_more"] is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_has_more_false_when_no_more_results() -> None:
    """Verify has_more is False when service indicates no more results."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_tests.return_value = {
        "product": {"id": 123, "name": "Test", "type": "web"},
        "statuses_filter": [],
        "tests": [],
        "total_count": 0,
        "offset": 0,
        "has_more": False,  # No more results
    }

    with patch(
        "testio_mcp.tools.list_tests_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_tests(product_id=123, page=1, per_page=100, ctx=mock_ctx)

        # Verify has_more is False
        assert result["pagination"]["has_more"] is False
