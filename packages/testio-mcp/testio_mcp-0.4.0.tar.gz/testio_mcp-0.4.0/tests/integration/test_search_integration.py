"""Integration tests for Search functionality (STORY-065).

Tests validate:
- SearchService with real FTS5 database
- SearchRepository with real FTS5 queries
- REST endpoint /api/search

Prerequisites:
- FTS5 search_index must be populated (via sync or migration)
- Test data should exist in database

Note: These tests require a database with FTS5 search_index populated.
Run `uv run alembic upgrade head` and sync data before running.
"""

import pytest

from testio_mcp.exceptions import InvalidSearchQueryError
from testio_mcp.repositories.search_repository import SearchRepository
from testio_mcp.services.search_service import SearchService

# ==========================================
# SearchRepository Integration Tests
# ==========================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_repository_basic_search(shared_cache, shared_client) -> None:
    """Integration test: SearchRepository.search with real FTS5 data."""
    async with shared_cache.async_session_maker() as session:
        repo = SearchRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )

        # Search for a common term - should return results
        results = await repo.search(query="test", limit=10)

        # Verify we get results (assuming there's test data)
        # Results may be empty if no data matches, but shouldn't error
        assert isinstance(results, list)

        if results:
            # Verify result structure
            result = results[0]
            assert hasattr(result, "entity_type")
            assert hasattr(result, "entity_id")
            assert hasattr(result, "title")
            assert hasattr(result, "score")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_repository_entity_filter(shared_cache, shared_client) -> None:
    """Integration test: SearchRepository.search with entity type filter."""
    async with shared_cache.async_session_maker() as session:
        repo = SearchRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )

        # Search only features
        results = await repo.search(query="video", entities=["feature"], limit=20)

        # All results should be features
        for result in results:
            assert result.entity_type == "feature"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_repository_product_filter(
    shared_cache, shared_client, test_product_id: int
) -> None:
    """Integration test: SearchRepository.search with product_id filter."""
    async with shared_cache.async_session_maker() as session:
        repo = SearchRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )

        # Search within specific product
        results = await repo.search(query="test", product_ids=[test_product_id], limit=20)

        # Results should be from the specified product (can't verify directly,
        # but query should succeed)
        assert isinstance(results, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_repository_optimize_index(shared_cache, shared_client) -> None:
    """Integration test: SearchRepository.optimize_index runs without error."""
    async with shared_cache.async_session_maker() as session:
        repo = SearchRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )

        # Should not raise
        await repo.optimize_index()


# ==========================================
# SearchService Integration Tests
# ==========================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_service_basic_search(shared_cache, shared_client) -> None:
    """Integration test: SearchService.search with real data."""
    async with shared_cache.async_session_maker() as session:
        repo = SearchRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        service = SearchService(search_repo=repo)

        # Basic search
        result = await service.search(query="test", limit=10)

        # Verify response structure
        assert "query" in result
        assert "total" in result
        assert "results" in result
        assert result["query"] == "test"
        assert isinstance(result["results"], list)

        if result["results"]:
            # Verify result item structure
            item = result["results"][0]
            assert "entity_type" in item
            assert "entity_id" in item
            assert "title" in item
            assert "score" in item
            assert "rank" in item


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_service_empty_query_raises_error(shared_cache, shared_client) -> None:
    """Integration test: SearchService raises error for empty query."""
    async with shared_cache.async_session_maker() as session:
        repo = SearchRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        service = SearchService(search_repo=repo)

        with pytest.raises(InvalidSearchQueryError) as exc_info:
            await service.search(query="")

        assert "cannot be empty" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_service_with_date_filter(shared_cache, shared_client) -> None:
    """Integration test: SearchService.search with date filter."""
    async with shared_cache.async_session_maker() as session:
        repo = SearchRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        service = SearchService(search_repo=repo)

        # Search with date filter (last year)
        result = await service.search(
            query="test",
            start_date="2024-01-01",
            end_date="today",
            limit=10,
        )

        # Should succeed - verify structure
        assert "query" in result
        assert "total" in result
        assert "results" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_service_with_all_filters(
    shared_cache, shared_client, test_product_id: int
) -> None:
    """Integration test: SearchService.search with all filters combined."""
    async with shared_cache.async_session_maker() as session:
        repo = SearchRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        service = SearchService(search_repo=repo)

        # Search with all filters
        result = await service.search(
            query="test",
            entities=["feature", "bug"],
            product_ids=[test_product_id],
            start_date="2024-01-01",
            end_date="today",
            limit=50,
            match_mode="simple",
        )

        # Should succeed - verify structure
        assert "query" in result
        assert "total" in result
        assert isinstance(result["results"], list)

        # If results, entity types should be filtered
        for item in result["results"]:
            assert item["entity_type"] in ["feature", "bug"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_service_raw_match_mode(shared_cache, shared_client) -> None:
    """Integration test: SearchService.search with raw FTS5 syntax."""
    async with shared_cache.async_session_maker() as session:
        repo = SearchRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        service = SearchService(search_repo=repo)

        # Search with raw FTS5 syntax
        result = await service.search(
            query="test*",  # Prefix search
            match_mode="raw",
            limit=10,
        )

        # Should succeed
        assert "query" in result
        assert result["query"] == "test*"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_service_optimize_index(shared_cache, shared_client) -> None:
    """Integration test: SearchService.optimize_index runs without error."""
    async with shared_cache.async_session_maker() as session:
        repo = SearchRepository(
            session=session, client=shared_client, customer_id=shared_cache.customer_id
        )
        service = SearchService(search_repo=repo)

        # Should not raise
        await service.optimize_index()


# ==========================================
# REST API Integration Tests
# ==========================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_search_endpoint(test_client) -> None:
    """Integration test: GET /api/search REST endpoint."""
    response = await test_client.get("/api/search", params={"query": "test"})

    # Should return 200 or 400 (if no data/invalid query)
    assert response.status_code in [200, 400]

    if response.status_code == 200:
        data = response.json()
        assert "query" in data
        assert "total" in data
        assert "results" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_search_with_filters(test_client) -> None:
    """Integration test: GET /api/search with query parameters."""
    response = await test_client.get(
        "/api/search",
        params={
            "query": "video",
            "entities": "feature,bug",
            "limit": 10,
        },
    )

    # Should return 200 or 400
    assert response.status_code in [200, 400]

    if response.status_code == 200:
        data = response.json()
        assert "query" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_search_empty_query_returns_400(test_client) -> None:
    """Integration test: Empty query should return 400."""
    response = await test_client.get("/api/search", params={"query": ""})

    # Empty query should be rejected
    assert response.status_code == 400


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rest_search_invalid_entity_returns_400(test_client) -> None:
    """Integration test: Invalid entity type should return 400."""
    response = await test_client.get(
        "/api/search",
        params={
            "query": "test",
            "entities": "invalid_type",
        },
    )

    # Invalid entity should be rejected
    assert response.status_code == 400
