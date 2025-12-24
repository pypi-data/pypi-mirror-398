"""Unit tests for FTS5QueryBuilder.

Tests SQL generation for FTS5 queries with various filter combinations.
"""

import pytest

from testio_mcp.repositories.fts5_query_builder import FTS5QueryBuilder


@pytest.mark.unit
def test_build_search_query_basic():
    """Verify basic search query with no filters."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act
    sql, params = builder.build_search_query("test query", limit=20)

    # Assert
    assert "search_index MATCH ?" in sql
    assert "bm25(search_index, 5.0, 1.0)" in sql
    assert "ORDER BY score" in sql
    assert "LIMIT ?" in sql
    assert params == ["test query", 20]


@pytest.mark.unit
def test_build_search_query_with_entity_filter():
    """Verify query with entity type filter."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act
    sql, params = builder.build_search_query("borders", entities=["feature"], limit=10)

    # Assert
    assert "search_index MATCH ?" in sql
    assert "entity_type IN (?)" in sql
    assert params == ["borders", "feature", 10]


@pytest.mark.unit
def test_build_search_query_with_multiple_entities():
    """Verify query with multiple entity types."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act
    sql, params = builder.build_search_query("bug", entities=["test", "bug"], limit=20)

    # Assert
    assert "entity_type IN (?, ?)" in sql
    assert params == ["bug", "test", "bug", 20]


@pytest.mark.unit
def test_build_search_query_with_product_ids():
    """Verify query with product ID filter."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act
    sql, params = builder.build_search_query("search", product_ids=[598], limit=15)

    # Assert
    assert "product_id IN (?)" in sql
    assert params == ["search", 598, 15]


@pytest.mark.unit
def test_build_search_query_with_multiple_product_ids():
    """Verify query with multiple product IDs."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act
    sql, params = builder.build_search_query("test", product_ids=[598, 599, 600], limit=20)

    # Assert
    assert "product_id IN (?, ?, ?)" in sql
    assert params == ["test", 598, 599, 600, 20]


@pytest.mark.unit
def test_build_search_query_with_all_filters():
    """Verify query with entity and product filters combined."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act
    sql, params = builder.build_search_query(
        "video mode", entities=["feature", "test"], product_ids=[598, 599], limit=5
    )

    # Assert
    assert "search_index MATCH ?" in sql
    assert "entity_type IN (?, ?)" in sql
    assert "product_id IN (?, ?)" in sql
    assert params == ["video mode", "feature", "test", 598, 599, 5]


@pytest.mark.unit
def test_build_search_query_invalid_entity_type():
    """Verify ValueError raised for invalid entity type."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        builder.build_search_query("test", entities=["invalid_type"])

    assert "Invalid entity types: ['invalid_type']" in str(exc_info.value)


@pytest.mark.unit
def test_build_search_query_column_weights():
    """Verify BM25 column weights are correct (title=5.0, content=1.0)."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act
    sql, _ = builder.build_search_query("test")

    # Assert
    assert "bm25(search_index, 5.0, 1.0)" in sql


@pytest.mark.unit
def test_build_optimize_query():
    """Verify optimize query is correct."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act
    sql = builder.build_optimize_query()

    # Assert
    assert sql == "INSERT INTO search_index(search_index) VALUES('optimize')"


@pytest.mark.unit
def test_build_search_query_respects_limit():
    """Verify limit parameter is respected."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act
    sql, params = builder.build_search_query("test", limit=100)

    # Assert
    assert params[-1] == 100  # Last param should be limit


@pytest.mark.unit
def test_searchable_entities_constant_used():
    """Verify builder uses SEARCHABLE_ENTITIES constant for validation."""
    # Arrange
    builder = FTS5QueryBuilder()

    # Act & Assert - All valid entities should work
    valid_entities = ["product", "feature", "test", "bug"]
    for entity in valid_entities:
        sql, params = builder.build_search_query("test", entities=[entity])
        assert entity in params

    # Invalid entity should raise ValueError
    with pytest.raises(ValueError):
        builder.build_search_query("test", entities=["invalid"])
