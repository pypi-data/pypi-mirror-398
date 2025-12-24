"""Unit tests for BaseRepository.

Tests the shared session management patterns for all repositories.
"""

from unittest.mock import AsyncMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.repositories.base_repository import BaseRepository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_repository_init_with_async_session():
    """Verify BaseRepository initializes with AsyncSession correctly."""
    # Arrange
    # Must use spec=AsyncSession for isinstance check to work
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    # Act
    repo = BaseRepository(session_or_db=mock_session, client=mock_client, customer_id=customer_id)

    # Assert
    assert repo.session == mock_session
    assert repo.db is None
    assert repo.client == mock_client


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_repository_init_with_legacy_db():
    """Verify BaseRepository initializes with legacy DB connection correctly."""
    # Arrange
    # Raw AsyncMock is not an instance of AsyncSession, so it falls back to db
    mock_db = AsyncMock()
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    # Act
    repo = BaseRepository(session_or_db=mock_db, client=mock_client, customer_id=customer_id)

    # Assert
    assert repo.session is None
    assert repo.db == mock_db
    assert repo.client == mock_client


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_repository_commit_delegates_correctly():
    """Verify commit() delegates to the active session or db."""
    # Case 1: Session
    mock_session = AsyncMock(spec=AsyncSession)
    repo1 = BaseRepository(mock_session, AsyncMock(), 123)
    await repo1.commit()
    mock_session.commit.assert_called_once()

    # Case 2: Legacy DB
    mock_db = AsyncMock()
    repo2 = BaseRepository(mock_db, AsyncMock(), 123)
    await repo2.commit()
    mock_db.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_repository_rollback_delegates_correctly():
    """Verify rollback() delegates to the active session or db."""
    # Case 1: Session
    mock_session = AsyncMock(spec=AsyncSession)
    repo1 = BaseRepository(mock_session, AsyncMock(), 123)
    await repo1.rollback()
    mock_session.rollback.assert_called_once()

    # Case 2: Legacy DB
    mock_db = AsyncMock()
    repo2 = BaseRepository(mock_db, AsyncMock(), 123)
    await repo2.rollback()
    mock_db.rollback.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_base_repository_close_delegates_correctly():
    """Verify close() delegates to the active session or db."""
    # Case 1: Session
    mock_session = AsyncMock(spec=AsyncSession)
    repo1 = BaseRepository(mock_session, AsyncMock(), 123)
    await repo1.close()
    mock_session.close.assert_called_once()

    # Case 2: Legacy DB
    mock_db = AsyncMock()
    repo2 = BaseRepository(mock_db, AsyncMock(), 123)
    await repo2.close()
    mock_db.close.assert_called_once()
