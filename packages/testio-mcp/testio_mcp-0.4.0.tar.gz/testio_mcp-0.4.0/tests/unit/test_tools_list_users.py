"""Unit tests for list_users MCP tool.

STORY-037: Data Serving Layer (MCP Tools + REST API)
STORY-040: Pagination for Data-Serving Tools
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.tools.list_users_tool import list_users as list_users_tool
from tests.unit.test_utils import mock_service_context

list_users = list_users_tool.fn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_to_service_without_filters() -> None:
    """Verify tool delegates to UserService.list_users with defaults."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    # STORY-058: Changed last_seen → last_activity
    mock_service.list_users.return_value = {
        "users": [
            {
                "id": 1,
                "username": "john_tester",
                "user_type": "tester",
                "first_seen": "2024-01-01T00:00:00+00:00",
                "last_activity": "2024-06-15T00:00:00+00:00",
            }
        ],
        "total": 1,
        "total_count": 1,
        "offset": 0,
        "has_more": False,
        "filter": {"user_type": None, "days": 365},
    }

    with patch(
        "testio_mcp.tools.list_users_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_users(ctx=mock_ctx)

        # STORY-055: Added sort params
        mock_service.list_users.assert_called_once_with(
            user_type=None, days=365, page=1, per_page=100, offset=0, sort_by=None, sort_order="asc"
        )
        assert result["total"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_user_type_filter() -> None:
    """Verify tool passes user_type filter to service."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_users.return_value = {
        "users": [],
        "total": 0,
        "total_count": 0,
        "offset": 0,
        "has_more": False,
        "filter": {"user_type": "tester", "days": 365},
    }

    with patch(
        "testio_mcp.tools.list_users_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_users(user_type="tester", ctx=mock_ctx)

        # STORY-055: Added sort params
        mock_service.list_users.assert_called_once_with(
            user_type="tester",
            days=365,
            page=1,
            per_page=100,
            offset=0,
            sort_by=None,
            sort_order="asc",
        )
        assert result["filter"]["user_type"] == "tester"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_days_filter() -> None:
    """Verify tool passes days filter to service."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_users.return_value = {
        "users": [],
        "total": 0,
        "total_count": 0,
        "offset": 0,
        "has_more": False,
        "filter": {"user_type": None, "days": 30},
    }

    with patch(
        "testio_mcp.tools.list_users_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_users(days=30, ctx=mock_ctx)

        # STORY-055: Added sort params
        mock_service.list_users.assert_called_once_with(
            user_type=None, days=30, page=1, per_page=100, offset=0, sort_by=None, sort_order="asc"
        )
        assert result["filter"]["days"] == 30


@pytest.mark.unit
@pytest.mark.asyncio
async def test_returns_validated_output_with_pagination() -> None:
    """Verify tool validates output with Pydantic model including pagination."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_users.return_value = {
        "users": [],
        "total": 0,
        "total_count": 0,
        "offset": 0,
        "has_more": False,
        "filter": {"user_type": None, "days": 365},
    }

    with patch(
        "testio_mcp.tools.list_users_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_users(ctx=mock_ctx)

        # Verify Pydantic validation passed
        assert "users" in result
        assert "total" in result
        assert "filter" in result
        assert "pagination" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_exception_to_tool_error() -> None:
    """Verify generic exception → ToolError with user-friendly message."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_users.side_effect = Exception("Database error")

    with patch(
        "testio_mcp.tools.list_users_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await list_users(ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "ℹ️" in error_msg
        assert "💡" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_empty_result() -> None:
    """Verify tool handles no users."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_users.return_value = {
        "users": [],
        "total": 0,
        "total_count": 0,
        "offset": 0,
        "has_more": False,
        "filter": {"user_type": None, "days": 365},
    }

    with patch(
        "testio_mcp.tools.list_users_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_users(ctx=mock_ctx)

        assert result["total"] == 0
        assert result["users"] == []
        # Verify pagination for empty results
        assert result["pagination"]["end_index"] == -1


# STORY-040: Pagination Tests


@pytest.mark.unit
@pytest.mark.asyncio
async def test_pagination_parameters_passed_to_service() -> None:
    """Verify pagination parameters are passed to service."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.list_users.return_value = {
        "users": [],
        "total": 0,
        "total_count": 0,
        "offset": 60,
        "has_more": False,
        "filter": {"user_type": "tester", "days": 365},
    }

    with patch(
        "testio_mcp.tools.list_users_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await list_users(user_type="tester", page=2, per_page=50, offset=10, ctx=mock_ctx)

        # STORY-055: Added sort params
        mock_service.list_users.assert_called_once_with(
            user_type="tester",
            days=365,
            page=2,
            per_page=50,
            offset=10,
            sort_by=None,
            sort_order="asc",
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_pagination_metadata_calculation() -> None:
    """Verify PaginationInfo calculation (start_index, end_index, has_more)."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    # STORY-058: Changed last_seen → last_activity
    mock_service.list_users.return_value = {
        "users": [
            {
                "id": i,
                "username": f"user{i}",
                "user_type": "tester",
                "first_seen": "2024-01-01T00:00:00+00:00",
                "last_activity": "2024-06-15T00:00:00+00:00",
            }
            for i in range(20)
        ],
        "total": 20,
        "total_count": 78,
        "offset": 40,
        "has_more": True,
        "filter": {"user_type": "tester", "days": 365},
    }

    with patch(
        "testio_mcp.tools.list_users_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await list_users(user_type="tester", page=3, per_page=20, ctx=mock_ctx)

        # Verify pagination metadata
        assert result["pagination"]["page"] == 3
        assert result["pagination"]["per_page"] == 20
        assert result["pagination"]["offset"] == 40
        assert result["pagination"]["start_index"] == 40
        assert result["pagination"]["end_index"] == 59
        assert result["pagination"]["total_count"] == 78
        assert result["pagination"]["has_more"] is True
