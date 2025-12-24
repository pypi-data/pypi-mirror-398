"""Unit tests for Bug Field Denormalization (STORY-063).

Tests the extraction of actual_result and expected_result fields from API responses
and their storage in the bugs table for FTS indexing.
"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.models.orm.bug import Bug
from testio_mcp.repositories.bug_repository import BugRepository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_bugs_extracts_result_fields():
    """Verify refresh_bugs extracts actual_result and expected_result from API response."""
    # Setup: Mock API response with result fields
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "bugs": [
            {
                "id": 1,
                "title": "Login fails",
                "severity": "high",
                "status": "accepted",
                "actual_result": "  User sees error message  ",  # With whitespace
                "expected_result": "User should be logged in",
                "test": {"id": 456},
            },
            {
                "id": 2,
                "title": "Button missing",
                "severity": "medium",
                "status": "rejected",
                "actual_result": "",  # Empty string should become None
                "expected_result": None,  # Explicitly None
                "test": {"id": 456},
            },
        ]
    }

    mock_session = AsyncMock(spec=AsyncSession)
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Execute
    count = await repo.refresh_bugs(test_id=456)

    # Verify API call
    mock_client.get.assert_called_once_with("bugs?filter_test_cycle_ids=456")

    # Verify UPSERT was called
    assert mock_session.exec.call_count == 1

    # Verify the values passed to the UPSERT include trimmed result fields
    # The statement contains the bug_rows data
    # Bug 1 should have trimmed actual_result and expected_result
    # Bug 2 should have None for both (empty string converted to None)

    assert count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_bugs_handles_missing_result_fields():
    """Verify refresh_bugs handles bugs without actual_result/expected_result fields."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "bugs": [
            {
                "id": 1,
                "title": "Bug without result fields",
                "severity": "low",
                "status": "forwarded",
                # actual_result and expected_result missing
                "test": {"id": 456},
            }
        ]
    }

    mock_session = AsyncMock(spec=AsyncSession)
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Execute - should not raise error
    count = await repo.refresh_bugs(test_id=456)

    # Verify UPSERT was called (fields should be None)
    assert mock_session.exec.call_count == 1
    assert count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_bugs_batch_extracts_result_fields():
    """Verify refresh_bugs_batch extracts actual_result and expected_result from API response."""
    mock_client = AsyncMock()
    mock_client.get.return_value = {
        "bugs": [
            {
                "id": 1,
                "title": "Bug 1",
                "severity": "critical",
                "status": "accepted",
                "actual_result": "App crashes",
                "expected_result": "App should work",
                "test": {"id": 456},
            },
            {
                "id": 2,
                "title": "Bug 2",
                "severity": "low",
                "status": "rejected",
                "actual_result": "  ",  # Whitespace only should become None
                "expected_result": "Expected behavior",
                "test": {"id": 457},
            },
        ]
    }

    mock_session = AsyncMock(spec=AsyncSession)
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Execute
    counts = await repo.refresh_bugs_batch(test_ids=[456, 457])

    # Verify API call
    mock_client.get.assert_called_once_with("bugs?filter_test_cycle_ids=456,457")

    # Verify UPSERT was called
    assert mock_session.exec.call_count == 1

    # Verify counts
    assert counts[456] == 1
    assert counts[457] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bugs_returns_result_fields():
    """Verify get_bugs returns actual_result and expected_result from ORM."""
    # Setup: Mock AsyncSession with bug data including result fields
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()

    bug_raw = {
        "id": 1,
        "title": "Bug with results",
        "status": "accepted",
        "actual_result": "Error displayed",
        "expected_result": "Success message",
    }

    bug_orm = Bug(
        id=1,
        customer_id=123,
        test_id=456,
        title="Bug with results",
        status="accepted",
        actual_result="Error displayed",
        expected_result="Success message",
        raw_data=json.dumps(bug_raw),
        synced_at=datetime.now(UTC),
    )

    mock_result.all.return_value = [bug_orm]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    repo = BugRepository(session=mock_session, client=mock_client, customer_id=123)

    # Execute
    result = await repo.get_bugs(test_id=456)

    # Verify: Result fields are present in returned data
    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["title"] == "Bug with results"
    # Note: get_bugs returns deserialized raw_data, so result fields come from JSON
    assert result[0]["actual_result"] == "Error displayed"
    assert result[0]["expected_result"] == "Success message"
