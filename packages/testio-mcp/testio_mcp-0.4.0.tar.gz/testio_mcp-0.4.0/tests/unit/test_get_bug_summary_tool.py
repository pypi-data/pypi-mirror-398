"""Unit tests for get_bug_summary MCP tool.

Tests the tool wrapper layer: input validation, service delegation,
exception conversion to ToolError format.

STORY-085: Add get_bug_summary Tool (Epic 014)
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.exceptions import BugNotFoundException, TestIOAPIError
from testio_mcp.tools.get_bug_summary_tool import get_bug_summary as get_bug_summary_tool

# Extract actual function from FastMCP FunctionTool wrapper
get_bug_summary = get_bug_summary_tool.fn  # type: ignore[attr-defined]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_success() -> None:
    """Verify tool delegates to service and returns validated output."""
    # Arrange
    mock_ctx = MagicMock()
    mock_service = AsyncMock()

    bug_data = {
        "id": 12345,
        "title": "Login button not clickable",
        "severity": "critical",
        "status": "rejected",
        "known": False,
        "actual_result": "Button does not respond to clicks",
        "expected_result": "Button should navigate to dashboard",
        "steps": "1. Navigate to login page\n2. Click login button",
        "rejection_reason": "test_is_invalid",
        "reported_by_user": {"id": 123, "username": "john_doe"},
        "test": {"id": 109363, "title": "Homepage Navigation Test"},
        "feature": {"id": 456, "title": "User Login"},
        "reported_at": "2025-11-28T10:30:00+00:00",
        "data_as_of": datetime.now(UTC).isoformat(),
    }

    mock_service.get_bug_summary.return_value = bug_data

    # Act
    with patch("testio_mcp.tools.get_bug_summary_tool.get_service_context") as mock_get_service:
        mock_get_service.return_value.__aenter__.return_value = mock_service

        result = await get_bug_summary(bug_id=12345, ctx=mock_ctx)

    # Assert
    mock_service.get_bug_summary.assert_called_once_with(12345)
    assert result["id"] == 12345
    assert result["title"] == "Login button not clickable"
    assert result["severity"] == "critical"
    assert result["status"] == "rejected"
    assert result["known"] is False
    assert result["rejection_reason"] == "test_is_invalid"
    assert result["reported_by_user"] == {"id": 123, "username": "john_doe"}
    assert result["test"] == {"id": 109363, "title": "Homepage Navigation Test"}
    assert result["feature"] == {"id": 456, "title": "User Login"}
    assert "data_as_of" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_not_found() -> None:
    """Verify BugNotFoundException is converted to ToolError with helpful message (AC4)."""
    # Arrange
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_bug_summary.side_effect = BugNotFoundException(bug_id=99999)

    # Act & Assert
    with patch("testio_mcp.tools.get_bug_summary_tool.get_service_context") as mock_get_service:
        mock_get_service.return_value.__aenter__.return_value = mock_service

        with pytest.raises(ToolError) as exc_info:
            await get_bug_summary(bug_id=99999, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg  # Error indicator
        assert "99999" in error_msg  # Bug ID mentioned
        assert "not found" in error_msg.lower()
        assert "ℹ️" in error_msg  # Context
        assert "💡" in error_msg  # Solution
        assert "list_bugs" in error_msg.lower()  # Helpful suggestion


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_invalid_bug_id_string() -> None:
    """Verify invalid bug_id (string) raises ToolError with validation message."""
    # Arrange
    mock_ctx = MagicMock()

    # Act & Assert
    with pytest.raises(ToolError) as exc_info:
        await get_bug_summary(bug_id="invalid", ctx=mock_ctx)  # type: ignore[arg-type]

    error_msg = str(exc_info.value)
    assert "❌" in error_msg
    assert "Invalid bug_id" in error_msg
    assert "positive integer" in error_msg.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_invalid_bug_id_zero() -> None:
    """Verify bug_id=0 raises ToolError."""
    # Arrange
    mock_ctx = MagicMock()

    # Act & Assert
    with pytest.raises(ToolError) as exc_info:
        await get_bug_summary(bug_id=0, ctx=mock_ctx)

    error_msg = str(exc_info.value)
    assert "❌" in error_msg
    assert "Invalid bug_id" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_invalid_bug_id_negative() -> None:
    """Verify negative bug_id raises ToolError."""
    # Arrange
    mock_ctx = MagicMock()

    # Act & Assert
    with pytest.raises(ToolError) as exc_info:
        await get_bug_summary(bug_id=-123, ctx=mock_ctx)

    error_msg = str(exc_info.value)
    assert "❌" in error_msg
    assert "Invalid bug_id" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_api_error() -> None:
    """Verify TestIOAPIError is converted to ToolError with helpful message."""
    # Arrange
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_bug_summary.side_effect = TestIOAPIError(
        message="Internal Server Error", status_code=500
    )

    # Act & Assert
    with patch("testio_mcp.tools.get_bug_summary_tool.get_service_context") as mock_get_service:
        mock_get_service.return_value.__aenter__.return_value = mock_service

        with pytest.raises(ToolError) as exc_info:
            await get_bug_summary(bug_id=12345, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "API error" in error_msg
        assert "500" in error_msg
        assert "ℹ️" in error_msg
        assert "💡" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_unexpected_error() -> None:
    """Verify unexpected exceptions are converted to ToolError."""
    # Arrange
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_bug_summary.side_effect = RuntimeError("Unexpected database error")

    # Act & Assert
    with patch("testio_mcp.tools.get_bug_summary_tool.get_service_context") as mock_get_service:
        mock_get_service.return_value.__aenter__.return_value = mock_service

        with pytest.raises(ToolError) as exc_info:
            await get_bug_summary(bug_id=12345, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "Unexpected error" in error_msg
        assert "ℹ️" in error_msg
        assert "💡" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_with_nullable_fields() -> None:
    """Verify tool handles bugs with NULL detail fields gracefully."""
    # Arrange
    mock_ctx = MagicMock()
    mock_service = AsyncMock()

    bug_data = {
        "id": 12345,
        "title": "Login button not clickable",
        "severity": None,  # NULL severity
        "status": None,  # NULL status
        "known": False,
        "actual_result": None,  # NULL actual_result
        "expected_result": None,  # NULL expected_result
        "steps": None,  # NULL steps
        "rejection_reason": None,  # No rejection
        "reported_by_user": None,  # No user (anonymous?)
        "test": {"id": 109363, "title": "Homepage Test"},
        "feature": None,  # No feature
        "reported_at": None,  # NULL reported_at
        "data_as_of": datetime.now(UTC).isoformat(),
    }

    mock_service.get_bug_summary.return_value = bug_data

    # Act
    with patch("testio_mcp.tools.get_bug_summary_tool.get_service_context") as mock_get_service:
        mock_get_service.return_value.__aenter__.return_value = mock_service

        result = await get_bug_summary(bug_id=12345, ctx=mock_ctx)

    # Assert - NULL fields should be excluded from output
    assert result["id"] == 12345
    assert "severity" not in result  # Excluded by exclude_none=True
    assert "actual_result" not in result
    assert "reported_by_user" not in result
    assert "feature" not in result
    assert result["test"] == {"id": 109363, "title": "Homepage Test"}


# Note: String coercion test removed - MCP handles type coercion at protocol level.
# Validator raises ValueError for strings, which is correct per coerce_to_int.
