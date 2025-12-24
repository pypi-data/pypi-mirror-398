"""Unit tests for get_user_summary MCP tool.

STORY-057: Add Summary Tools (Epic 008)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.exceptions import TestIOAPIError, UserNotFoundException
from testio_mcp.tools.user_summary_tool import get_user_summary as get_user_summary_tool
from tests.unit.test_utils import mock_service_context

# Extract actual function from FastMCP FunctionTool wrapper
get_user_summary = get_user_summary_tool.fn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_not_found_to_tool_error() -> None:
    """Verify UserNotFoundException → ToolError with ❌ℹ️💡 format."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_user_summary.side_effect = UserNotFoundException(user_id=123)

    with patch(
        "testio_mcp.tools.user_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await get_user_summary(user_id=123, ctx=mock_ctx)

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
    mock_service.get_user_summary.side_effect = TestIOAPIError(message="Timeout", status_code=504)

    with patch(
        "testio_mcp.tools.user_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await get_user_summary(user_id=123, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "504" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_to_service_correctly_customer() -> None:
    """Verify tool delegates to UserService for customer user."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_user_summary.return_value = {
        "id": 123,
        "username": "john_doe",
        "user_type": "customer",
        "tests_created_count": 15,
        "tests_submitted_count": 12,
        "last_activity": "2025-11-28T10:30:00Z",
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    with patch(
        "testio_mcp.tools.user_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_user_summary(user_id=123, ctx=mock_ctx)

        mock_service.get_user_summary.assert_called_once_with(123)
        assert result["id"] == 123
        assert result["username"] == "john_doe"
        assert result["user_type"] == "customer"
        assert result["tests_created_count"] == 15
        assert result["tests_submitted_count"] == 12


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_to_service_correctly_tester() -> None:
    """Verify tool delegates to UserService for tester user."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_user_summary.return_value = {
        "id": 456,
        "username": "jane_tester",
        "user_type": "tester",
        "bugs_reported_count": 42,
        "last_activity": "2025-11-28T10:30:00Z",
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    with patch(
        "testio_mcp.tools.user_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_user_summary(user_id=456, ctx=mock_ctx)

        mock_service.get_user_summary.assert_called_once_with(456)
        assert result["id"] == 456
        assert result["username"] == "jane_tester"
        assert result["user_type"] == "tester"
        assert result["bugs_reported_count"] == 42


@pytest.mark.unit
@pytest.mark.asyncio
async def test_returns_correct_structure() -> None:
    """Verify output includes all required fields."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_user_summary.return_value = {
        "id": 123,
        "username": "john_doe",
        "user_type": "customer",
        "tests_created_count": 15,
        "tests_submitted_count": 12,
        "last_activity": "2025-11-28T10:30:00Z",
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    with patch(
        "testio_mcp.tools.user_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_user_summary(user_id=123, ctx=mock_ctx)

        # Verify all required fields present
        assert "id" in result
        assert "username" in result
        assert "user_type" in result
        assert "data_as_of" in result

        # Verify counts are non-negative
        if "tests_created_count" in result:
            assert result["tests_created_count"] >= 0
        if "tests_submitted_count" in result:
            assert result["tests_submitted_count"] >= 0
        if "bugs_reported_count" in result:
            assert result["bugs_reported_count"] >= 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_zero_activity() -> None:
    """Verify tool handles users with no activity correctly."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_user_summary.return_value = {
        "id": 100,
        "username": "new_customer",
        "user_type": "customer",
        "tests_created_count": 0,
        "tests_submitted_count": 0,
        "last_activity": None,
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    with patch(
        "testio_mcp.tools.user_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_user_summary(user_id=100, ctx=mock_ctx)

        assert result["tests_created_count"] == 0
        assert result["tests_submitted_count"] == 0
