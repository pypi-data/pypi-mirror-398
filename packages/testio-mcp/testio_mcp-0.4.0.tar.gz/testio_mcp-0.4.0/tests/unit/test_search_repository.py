"""Unit tests for SearchRepository.

Tests FTS5 search operations with mocked AsyncSession.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from testio_mcp.client import TestIOClient
from testio_mcp.repositories.fts5_query_builder import FTS5QueryBuilder
from testio_mcp.repositories.search_repository import SearchRepository, SearchResult


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_repository_inherits_base_repository():
    """Verify SearchRepository is subclass of BaseRepository."""
    from testio_mcp.repositories.base_repository import BaseRepository

    # Assert
    assert issubclass(SearchRepository, BaseRepository)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_returns_results():
    """Verify search() executes query and returns SearchResult objects."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    customer_id = 123

    # Mock query result rows: (entity_type, entity_id, title, score)
    mock_rows = [
        ("feature", 1, "Video Mode Feature", -2.5),
        ("test", 2, "Video Test", -1.8),
    ]

    mock_result = MagicMock()
    mock_result.fetchall.return_value = mock_rows
    mock_connection = AsyncMock()
    mock_connection.execute.return_value = mock_result
    mock_session.connection.return_value = mock_connection

    repo = SearchRepository(session=mock_session, client=mock_client, customer_id=customer_id)

    # Act
    results = await repo.search("video", entities=["feature", "test"], limit=10)

    # Assert
    assert len(results) == 2
    assert isinstance(results[0], SearchResult)
    assert results[0].entity_type == "feature"
    assert results[0].entity_id == 1
    assert results[0].title == "Video Mode Feature"
    assert results[0].score == -2.5

    # Verify execute was called
    # Verify execute was called on connection
    mock_session.connection.assert_called_once()
    mock_connection.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_uses_query_builder():
    """Verify search() delegates SQL generation to FTS5QueryBuilder."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    mock_query_builder = MagicMock(spec=FTS5QueryBuilder)

    # Mock builder to return SQL and params
    mock_query_builder.build_search_query.return_value = (
        "SELECT * FROM search_index WHERE search_index MATCH ? LIMIT ?",
        ["test", 20],
    )

    # Mock empty result
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_connection = AsyncMock()
    mock_connection.execute.return_value = mock_result
    mock_session.connection.return_value = mock_connection

    repo = SearchRepository(
        session=mock_session,
        client=mock_client,
        customer_id=123,
        query_builder=mock_query_builder,
    )

    # Act
    await repo.search("test", entities=None, product_ids=None, limit=20)

    # Assert - includes start_date and end_date (both None by default)
    mock_query_builder.build_search_query.assert_called_once_with(
        "test", None, None, None, None, 20
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_result_to_dict():
    """Verify SearchResult.to_dict() returns correct dictionary."""
    # Arrange
    result = SearchResult(entity_type="bug", entity_id=123, title="Test Bug", score=-1.5)

    # Act
    result_dict = result.to_dict()

    # Assert
    assert result_dict == {
        "entity_type": "bug",
        "entity_id": 123,
        "title": "Test Bug",
        "score": -1.5,
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_no_results():
    """Verify search() returns empty list when no results found."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)

    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_connection = AsyncMock()
    mock_connection.execute.return_value = mock_result
    mock_session.connection.return_value = mock_connection

    repo = SearchRepository(session=mock_session, client=mock_client, customer_id=123)

    # Act
    results = await repo.search("nonexistent")

    # Assert
    assert results == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_with_product_ids():
    """Verify search() passes product_ids to query builder."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    mock_query_builder = MagicMock(spec=FTS5QueryBuilder)

    mock_query_builder.build_search_query.return_value = ("SELECT ...", ["test", 598, 599, 10])
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_connection = AsyncMock()
    mock_connection.execute.return_value = mock_result
    mock_session.connection.return_value = mock_connection

    repo = SearchRepository(
        session=mock_session,
        client=mock_client,
        customer_id=123,
        query_builder=mock_query_builder,
    )

    # Act
    await repo.search("test", product_ids=[598, 599], limit=10)

    # Assert - includes start_date and end_date (both None by default)
    mock_query_builder.build_search_query.assert_called_once_with(
        "test", None, [598, 599], None, None, 10
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_optimize_index():
    """Verify optimize_index() executes optimize query and commits."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)
    mock_query_builder = MagicMock(spec=FTS5QueryBuilder)

    mock_query_builder.build_optimize_query.return_value = (
        "INSERT INTO search_index(search_index) VALUES('optimize')"
    )
    mock_connection = AsyncMock()
    mock_session.connection.return_value = mock_connection

    repo = SearchRepository(
        session=mock_session,
        client=mock_client,
        customer_id=123,
        query_builder=mock_query_builder,
    )

    # Act
    await repo.optimize_index()

    # Assert
    mock_query_builder.build_optimize_query.assert_called_once()
    mock_query_builder.build_optimize_query.assert_called_once()
    mock_session.connection.assert_called_once()
    mock_connection.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_default_query_builder():
    """Verify SearchRepository creates FTS5QueryBuilder by default."""
    # Arrange
    mock_session = AsyncMock(spec=AsyncSession)
    mock_client = AsyncMock(spec=TestIOClient)

    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_connection = AsyncMock()
    mock_connection.execute.return_value = mock_result
    mock_session.connection.return_value = mock_connection

    # Act
    repo = SearchRepository(session=mock_session, client=mock_client, customer_id=123)

    # Assert
    assert isinstance(repo.query_builder, FTS5QueryBuilder)
