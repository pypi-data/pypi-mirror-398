"""Unit tests for TestRepository read operations (STORY-071).

Tests get_test_with_bugs and query_tests methods, focusing on test_environment column override.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.repositories.test_repository import TestRepository


@pytest.mark.unit
@pytest.mark.asyncio
class TestRepositoryReads:
    """Test TestRepository read operations with test_environment column override."""

    async def test_get_test_with_bugs_returns_test_environment_from_column(self) -> None:
        """Should return test_environment from column, not JSON (AC1)."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Test data with different test_environment in JSON vs column
        test_data_json = json.dumps(
            {
                "id": 100,
                "title": "Test",
                "test_environment": {"id": 1, "title": "Old Environment"},  # JSON value
            }
        )
        # Column value (authoritative)
        test_environment_column = {"id": 2, "title": "New Environment"}

        # Mock test query result
        mock_test_result = MagicMock()
        mock_test_result.first.return_value = (test_data_json, test_environment_column)

        # Mock bug query result (empty)
        mock_bug_result = MagicMock()
        mock_bug_result.all.return_value = []

        # Configure exec to return different results for different queries
        mock_session.exec.side_effect = [mock_test_result, mock_bug_result]

        # Act
        result = await repo.get_test_with_bugs(test_id=100)

        # Assert
        assert result is not None
        assert result["test"]["test_environment"] == {"id": 2, "title": "New Environment"}
        # Verify column value overrode JSON value

    async def test_get_test_with_bugs_handles_null_test_environment(self) -> None:
        """Should handle NULL test_environment column gracefully (AC1)."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        test_data_json = json.dumps(
            {
                "id": 101,
                "title": "Test without Env",
                "test_environment": {"id": 1, "title": "JSON Env"},  # JSON has value
            }
        )
        test_environment_column = None  # Column is NULL

        mock_test_result = MagicMock()
        mock_test_result.first.return_value = (test_data_json, test_environment_column)

        mock_bug_result = MagicMock()
        mock_bug_result.all.return_value = []

        mock_session.exec.side_effect = [mock_test_result, mock_bug_result]

        # Act
        result = await repo.get_test_with_bugs(test_id=101)

        # Assert
        assert result is not None
        # When column is NULL, JSON value should remain
        assert result["test"]["test_environment"] == {"id": 1, "title": "JSON Env"}

    async def test_get_test_with_bugs_returns_none_when_test_not_found(self) -> None:
        """Should return None when test doesn't exist."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        # Act
        result = await repo.get_test_with_bugs(test_id=999)

        # Assert
        assert result is None

    async def test_query_tests_returns_test_environment_from_column(self) -> None:
        """Should return test_environment from column for all tests (AC2)."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Multiple tests with different environments
        test1_json = json.dumps(
            {
                "id": 100,
                "title": "Test 1",
                "test_environment": {"id": 1, "title": "Old Env 1"},
            }
        )
        test1_env_column = {"id": 10, "title": "New Env 1"}

        test2_json = json.dumps(
            {
                "id": 101,
                "title": "Test 2",
                "test_environment": {"id": 2, "title": "Old Env 2"},
            }
        )
        test2_env_column = {"id": 20, "title": "New Env 2"}

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (test1_json, test1_env_column),
            (test2_json, test2_env_column),
        ]
        mock_session.exec.return_value = mock_result

        # Act
        result = await repo.query_tests(product_id=10)

        # Assert
        assert len(result) == 2
        assert result[0]["test_environment"] == {"id": 10, "title": "New Env 1"}
        assert result[1]["test_environment"] == {"id": 20, "title": "New Env 2"}

    async def test_query_tests_handles_null_test_environment(self) -> None:
        """Should handle NULL test_environment columns in query results (AC2)."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        test1_json = json.dumps(
            {
                "id": 100,
                "title": "Test with Env",
                "test_environment": {"id": 1, "title": "JSON Env"},
            }
        )
        test1_env_column = {"id": 10, "title": "Column Env"}

        test2_json = json.dumps(
            {
                "id": 101,
                "title": "Test without Env",
                "test_environment": {"id": 2, "title": "JSON Env 2"},
            }
        )
        test2_env_column = None  # NULL column

        mock_result = MagicMock()
        mock_result.all.return_value = [
            (test1_json, test1_env_column),
            (test2_json, test2_env_column),
        ]
        mock_session.exec.return_value = mock_result

        # Act
        result = await repo.query_tests(product_id=10)

        # Assert
        assert len(result) == 2
        assert result[0]["test_environment"] == {"id": 10, "title": "Column Env"}
        # NULL column should preserve JSON value
        assert result[1]["test_environment"] == {"id": 2, "title": "JSON Env 2"}

    async def test_query_tests_with_filters_includes_test_environment(self) -> None:
        """Should include test_environment override with status/date filters (AC2)."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        test_json = json.dumps(
            {
                "id": 100,
                "title": "Filtered Test",
                "test_environment": {"id": 1, "title": "JSON Env"},
            }
        )
        test_env_column = {"id": 10, "title": "Column Env"}

        mock_result = MagicMock()
        mock_result.all.return_value = [(test_json, test_env_column)]
        mock_session.exec.return_value = mock_result

        # Act
        result = await repo.query_tests(
            product_id=10,
            statuses=["running", "locked"],
            testing_type="coverage",
        )

        # Assert
        assert len(result) == 1
        assert result[0]["test_environment"] == {"id": 10, "title": "Column Env"}
