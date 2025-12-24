"""Unit tests for BugService.

Tests verify that:
1. get_bug_summary returns correctly formatted bug summary with metadata
2. get_bug_summary raises BugNotFoundException when bug not found

STORY-085: Add get_bug_summary Tool (Epic 014)
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from testio_mcp.exceptions import BugNotFoundException
from testio_mcp.services.bug_service import BugService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_returns_data() -> None:
    """Verify get_bug_summary returns bug data with data_as_of timestamp."""
    # Arrange
    mock_bug_repo = AsyncMock()
    mock_test_repo = AsyncMock()

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
    }

    mock_bug_repo.get_bug_by_id.return_value = bug_data

    # Act
    service = BugService(client=None, bug_repo=mock_bug_repo, test_repo=mock_test_repo)  # type: ignore[arg-type]
    result = await service.get_bug_summary(12345)

    # Assert
    mock_bug_repo.get_bug_by_id.assert_called_once_with(12345)
    assert result["id"] == 12345
    assert result["title"] == "Login button not clickable"
    assert result["severity"] == "critical"
    assert result["status"] == "rejected"
    assert result["known"] is False
    assert result["actual_result"] == "Button does not respond to clicks"
    assert result["expected_result"] == "Button should navigate to dashboard"
    assert result["steps"] == "1. Navigate to login page\n2. Click login button"
    assert result["rejection_reason"] == "test_is_invalid"
    assert result["reported_by_user"] == {"id": 123, "username": "john_doe"}
    assert result["test"] == {"id": 109363, "title": "Homepage Navigation Test"}
    assert result["feature"] == {"id": 456, "title": "User Login"}
    assert result["reported_at"] == "2025-11-28T10:30:00+00:00"

    # Verify data_as_of timestamp added (AC3)
    assert "data_as_of" in result
    data_as_of = datetime.fromisoformat(result["data_as_of"])
    now = datetime.now(UTC)
    # Timestamp should be within 1 second of now
    assert abs((now - data_as_of).total_seconds()) < 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_raises_not_found() -> None:
    """Verify get_bug_summary raises BugNotFoundException when bug not found."""
    # Arrange
    mock_bug_repo = AsyncMock()
    mock_test_repo = AsyncMock()
    mock_bug_repo.get_bug_by_id.return_value = None  # Bug not found

    # Act & Assert
    service = BugService(client=None, bug_repo=mock_bug_repo, test_repo=mock_test_repo)  # type: ignore[arg-type]

    with pytest.raises(BugNotFoundException) as exc_info:
        await service.get_bug_summary(99999)

    assert exc_info.value.bug_id == 99999
    assert "99999" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bug_summary_with_null_fields() -> None:
    """Verify get_bug_summary handles NULL detail fields gracefully."""
    # Arrange
    mock_bug_repo = AsyncMock()
    mock_test_repo = AsyncMock()

    bug_data = {
        "id": 12345,
        "title": "Login button not clickable",
        "severity": None,  # NULL severity
        "status": None,  # NULL status
        "known": False,
        "actual_result": None,  # NULL
        "expected_result": None,  # NULL
        "steps": None,  # NULL
        "rejection_reason": None,  # No rejection
        "reported_by_user": None,  # No user
        "test": {"id": 109363, "title": "Homepage Test"},
        "feature": None,  # No feature
        "reported_at": None,  # NULL
    }

    mock_bug_repo.get_bug_by_id.return_value = bug_data

    # Act
    service = BugService(client=None, bug_repo=mock_bug_repo, test_repo=mock_test_repo)  # type: ignore[arg-type]
    result = await service.get_bug_summary(12345)

    # Assert - NULL fields should pass through (tool layer handles exclude_none)
    assert result["id"] == 12345
    assert result["severity"] is None
    assert result["actual_result"] is None
    assert result["reported_by_user"] is None
    assert result["feature"] is None
    assert result["test"] == {"id": 109363, "title": "Homepage Test"}
    assert "data_as_of" in result
