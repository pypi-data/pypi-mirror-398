"""Unit tests for get_feature_summary MCP tool.

STORY-057: Add Summary Tools (Epic 008)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.exceptions import FeatureNotFoundException, TestIOAPIError
from testio_mcp.tools.feature_summary_tool import get_feature_summary as get_feature_summary_tool
from tests.unit.test_utils import mock_service_context

# Extract actual function from FastMCP FunctionTool wrapper
get_feature_summary = get_feature_summary_tool.fn


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_not_found_to_tool_error() -> None:
    """Verify FeatureNotFoundException → ToolError with ❌ℹ️💡 format."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_feature_summary.side_effect = FeatureNotFoundException(feature_id=123)

    with patch(
        "testio_mcp.tools.feature_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await get_feature_summary(feature_id=123, ctx=mock_ctx)

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
    mock_service.get_feature_summary.side_effect = TestIOAPIError(
        message="Timeout", status_code=504
    )

    with patch(
        "testio_mcp.tools.feature_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await get_feature_summary(feature_id=123, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "504" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_to_service_correctly() -> None:
    """Verify tool delegates to FeatureService with correct parameters."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_feature_summary.return_value = {
        "id": 123,
        "title": "User Authentication",
        "description": "Login and signup flows",
        "howtofind": "Navigate to login page",
        "user_stories": ["As a user, I want to log in", "As an admin, I want to manage users"],
        "test_count": 15,
        "bug_count": 42,
        "product": {"id": 598, "name": "Canva"},
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    with patch(
        "testio_mcp.tools.feature_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_feature_summary(feature_id=123, ctx=mock_ctx)

        mock_service.get_feature_summary.assert_called_once_with(123)
        assert result["id"] == 123
        assert result["title"] == "User Authentication"
        assert result["test_count"] == 15
        assert result["bug_count"] == 42
        assert len(result["user_stories"]) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_returns_correct_structure() -> None:
    """Verify output includes all required fields."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_feature_summary.return_value = {
        "id": 123,
        "title": "User Authentication",
        "description": "Login and signup flows",
        "howtofind": "Navigate to login page",
        "user_stories": ["As a user, I want to log in"],
        "test_count": 15,
        "bug_count": 42,
        "product": {"id": 598, "name": "Canva"},
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    with patch(
        "testio_mcp.tools.feature_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_feature_summary(feature_id=123, ctx=mock_ctx)

        # Verify all required fields present
        assert "id" in result
        assert "title" in result
        assert "user_stories" in result
        assert "test_count" in result
        assert "bug_count" in result
        assert "product" in result
        assert "data_as_of" in result

        # Verify counts are non-negative
        assert result["test_count"] >= 0
        assert result["bug_count"] >= 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_empty_user_stories() -> None:
    """Verify tool handles features with no user stories correctly."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_feature_summary.return_value = {
        "id": 100,
        "title": "New Feature",
        "description": None,
        "howtofind": None,
        "user_stories": [],
        "test_count": 0,
        "bug_count": 0,
        "product": {"id": 598, "name": "Canva"},
        "data_as_of": "2025-11-28T10:30:05Z",
    }

    with patch(
        "testio_mcp.tools.feature_summary_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await get_feature_summary(feature_id=100, ctx=mock_ctx)

        assert result["user_stories"] == []
        assert result["test_count"] == 0
        assert result["bug_count"] == 0
