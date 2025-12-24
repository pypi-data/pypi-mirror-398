"""Unit tests for BugRepository write operations (STORY-070).

Tests _write_bugs_to_db and refresh_bugs methods, focusing on known field persistence.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.repositories.bug_repository import BugRepository


@pytest.mark.unit
@pytest.mark.asyncio
class TestBugRepositoryWrites:
    """Test BugRepository write operations."""

    async def test_write_bugs_to_db_stores_known_true(self) -> None:
        """Should store known=True when present in API data."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = BugRepository(session=mock_session, client=mock_client, customer_id=1)

        bugs_data = [
            {
                "id": 1,
                "title": "Known Bug",
                "known": True,
                "test": {"id": 100},
            }
        ]

        # Patch sqlite_insert to capture values
        with patch("testio_mcp.repositories.bug_repository.sqlite_insert") as mock_insert:
            mock_stmt = MagicMock()
            mock_insert.return_value = mock_stmt
            mock_stmt.values.return_value = mock_stmt
            mock_stmt.on_conflict_do_update.return_value = mock_stmt

            # Act
            await repo._write_bugs_to_db(bugs_data, test_ids=[100])

            # Assert
            mock_insert.assert_called_once()
            # Check values passed to values()
            call_args = mock_stmt.values.call_args
            assert call_args is not None
            bug_rows = call_args[0][0]
            assert len(bug_rows) == 1
            assert bug_rows[0]["known"] is True

    async def test_write_bugs_to_db_stores_known_false(self) -> None:
        """Should store known=False when present in API data."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = BugRepository(session=mock_session, client=mock_client, customer_id=1)

        bugs_data = [
            {
                "id": 2,
                "title": "Unknown Bug",
                "known": False,
                "test": {"id": 100},
            }
        ]

        with patch("testio_mcp.repositories.bug_repository.sqlite_insert") as mock_insert:
            mock_stmt = MagicMock()
            mock_insert.return_value = mock_stmt
            mock_stmt.values.return_value = mock_stmt
            mock_stmt.on_conflict_do_update.return_value = mock_stmt

            # Act
            await repo._write_bugs_to_db(bugs_data, test_ids=[100])

            # Assert
            bug_rows = mock_stmt.values.call_args[0][0]
            assert bug_rows[0]["known"] is False

    async def test_write_bugs_to_db_defaults_known_false(self) -> None:
        """Should default known to False when missing in API data."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = BugRepository(session=mock_session, client=mock_client, customer_id=1)

        bugs_data = [
            {
                "id": 3,
                "title": "Legacy Bug",
                # known field missing
                "test": {"id": 100},
            }
        ]

        with patch("testio_mcp.repositories.bug_repository.sqlite_insert") as mock_insert:
            mock_stmt = MagicMock()
            mock_insert.return_value = mock_stmt
            mock_stmt.values.return_value = mock_stmt
            mock_stmt.on_conflict_do_update.return_value = mock_stmt

            # Act
            await repo._write_bugs_to_db(bugs_data, test_ids=[100])

            # Assert
            bug_rows = mock_stmt.values.call_args[0][0]
            assert bug_rows[0]["known"] is False

    async def test_refresh_bugs_stores_known(self) -> None:
        """Should store known field in refresh_bugs."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = AsyncMock(spec=TestIOClient)
        repo = BugRepository(session=mock_session, client=mock_client, customer_id=1)

        mock_client.get.return_value = {
            "bugs": [
                {
                    "id": 4,
                    "title": "Refreshed Bug",
                    "known": True,
                    "test": {"id": 100},
                }
            ]
        }

        with patch("testio_mcp.repositories.bug_repository.sqlite_insert") as mock_insert:
            mock_stmt = MagicMock()
            mock_insert.return_value = mock_stmt
            mock_stmt.values.return_value = mock_stmt
            mock_stmt.on_conflict_do_update.return_value = mock_stmt

            # Act
            await repo.refresh_bugs(test_id=100)

            # Assert
            bug_rows = mock_stmt.values.call_args[0][0]
            assert bug_rows[0]["known"] is True
