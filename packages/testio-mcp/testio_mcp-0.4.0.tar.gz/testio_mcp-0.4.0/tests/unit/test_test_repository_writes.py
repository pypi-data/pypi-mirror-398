"""Unit tests for TestRepository write operations (STORY-070).

Tests insert_test and update_test methods, focusing on test_environment persistence.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.models.orm import Test
from testio_mcp.repositories.test_repository import TestRepository


@pytest.mark.unit
@pytest.mark.asyncio
class TestRepositoryWrites:
    """Test TestRepository write operations."""

    async def test_insert_test_stores_test_environment(self) -> None:
        """Should extract and store test_environment during insert."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Mock existing test check (return None -> insert new)
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        test_data = {
            "id": 100,
            "title": "Test with Env",
            "test_environment": {
                "id": 5,
                "title": "Staging",
                "type": "website",  # Extra field should be filtered
            },
        }

        # Act
        await repo.insert_test(test_data, product_id=10)

        # Assert
        mock_session.add.assert_called_once()
        new_test = mock_session.add.call_args[0][0]
        assert isinstance(new_test, Test)
        assert new_test.id == 100
        assert new_test.test_environment == {"id": 5, "title": "Staging"}

    async def test_insert_test_handles_missing_test_environment(self) -> None:
        """Should store None when test_environment is missing."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        test_data = {
            "id": 101,
            "title": "Test without Env",
            # No test_environment
        }

        # Act
        await repo.insert_test(test_data, product_id=10)

        # Assert
        new_test = mock_session.add.call_args[0][0]
        assert new_test.test_environment is None

    async def test_update_test_updates_test_environment(self) -> None:
        """Should update test_environment in existing test."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Mock existing test
        existing_test = Test(id=102, customer_id=1, product_id=10, data="{}", status="running")
        mock_result = MagicMock()
        mock_result.first.return_value = existing_test
        mock_session.exec.return_value = mock_result

        test_data = {
            "id": 102,
            "title": "Updated Test",
            "test_environment": {
                "id": 6,
                "title": "Production",
                "url": "https://prod.example.com",  # Extra field
            },
        }

        # Act
        await repo.update_test(test_data, product_id=10)

        # Assert
        assert existing_test.test_environment == {"id": 6, "title": "Production"}

    async def test_update_test_clears_test_environment(self) -> None:
        """Should clear test_environment if missing in update."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        # Existing test has environment
        existing_test = Test(
            id=103,
            customer_id=1,
            product_id=10,
            data="{}",
            status="running",
            test_environment={"id": 5, "title": "Staging"},
        )
        mock_result = MagicMock()
        mock_result.first.return_value = existing_test
        mock_session.exec.return_value = mock_result

        test_data = {
            "id": 103,
            "title": "Updated Test",
            "test_environment": None,  # Explicitly None or missing
        }

        # Act
        await repo.update_test(test_data, product_id=10)

        # Assert
        assert existing_test.test_environment is None

    async def test_insert_test_ignores_invalid_test_environment_types(self) -> None:
        """Should ignore test_environment if id or title are wrong types."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        mock_client = MagicMock(spec=TestIOClient)
        repo = TestRepository(session=mock_session, client=mock_client, customer_id=1)

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        test_data = {
            "id": 104,
            "title": "Test with Invalid Env",
            "test_environment": {
                "id": "not-an-int",  # Invalid type
                "title": "Staging",
            },
        }

        # Act
        await repo.insert_test(test_data, product_id=10)

        # Assert
        new_test = mock_session.add.call_args[0][0]
        assert new_test.test_environment is None
