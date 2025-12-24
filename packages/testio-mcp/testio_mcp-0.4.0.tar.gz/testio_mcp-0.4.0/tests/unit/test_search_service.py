"""Unit tests for SearchService.

STORY-065: Search MCP Tool
"""

from unittest.mock import AsyncMock

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.exceptions import InvalidSearchQueryError
from testio_mcp.repositories.search_repository import SearchResult
from testio_mcp.services.search_service import SearchService


@pytest.fixture
def mock_search_repo() -> AsyncMock:
    """Create mock SearchRepository."""
    repo = AsyncMock()
    repo.search = AsyncMock(return_value=[])
    repo.optimize_index = AsyncMock()
    return repo


@pytest.fixture
def search_service(mock_search_repo: AsyncMock) -> SearchService:
    """Create SearchService with mock repository."""
    return SearchService(search_repo=mock_search_repo)


class TestSearchValidation:
    """Test query validation."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_empty_query_raises_error(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Empty query should raise InvalidSearchQueryError."""
        with pytest.raises(InvalidSearchQueryError) as exc_info:
            await search_service.search(query="")

        assert "cannot be empty" in str(exc_info.value)
        mock_search_repo.search.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_whitespace_only_query_raises_error(self, search_service: SearchService) -> None:
        """Whitespace-only query should raise InvalidSearchQueryError."""
        with pytest.raises(InvalidSearchQueryError) as exc_info:
            await search_service.search(query="   ")

        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_too_short_query_raises_error(self, search_service: SearchService) -> None:
        """Query under 2 chars should raise InvalidSearchQueryError."""
        with pytest.raises(InvalidSearchQueryError) as exc_info:
            await search_service.search(query="a")

        assert "at least 2 characters" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_short_prefix_query_allowed(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Short query with prefix wildcard should be allowed."""
        mock_search_repo.search.return_value = []

        result = await search_service.search(query="a*")

        assert result["total"] == 0
        mock_search_repo.search.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_entity_type_raises_error(self, search_service: SearchService) -> None:
        """Invalid entity type should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await search_service.search(query="test", entities=["invalid"])

        assert "Invalid entity types" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_valid_entity_types_accepted(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Valid entity types should be accepted."""
        mock_search_repo.search.return_value = []

        result = await search_service.search(
            query="test", entities=["product", "feature", "test", "bug"]
        )

        assert result["total"] == 0
        mock_search_repo.search.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_match_mode_raises_error(self, search_service: SearchService) -> None:
        """Invalid match_mode should raise InvalidSearchQueryError."""
        with pytest.raises(InvalidSearchQueryError) as exc_info:
            await search_service.search(query="test", match_mode="invalid")

        assert "Invalid match_mode" in str(exc_info.value)


class TestSearchExecution:
    """Test search execution and formatting."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_returns_formatted_results(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Search should return formatted results with ranks."""
        mock_search_repo.search.return_value = [
            SearchResult(entity_type="feature", entity_id=123, title="Test Feature", score=-5.5),
            SearchResult(entity_type="bug", entity_id=456, title="Test Bug", score=-3.2),
        ]

        result = await search_service.search(query="test")

        assert result["query"] == "test"
        assert result["total"] == 2
        assert len(result["results"]) == 2

        # Check first result
        assert result["results"][0]["entity_type"] == "feature"
        assert result["results"][0]["entity_id"] == 123
        assert result["results"][0]["title"] == "Test Feature"
        assert result["results"][0]["rank"] == 1

        # Check second result
        assert result["results"][1]["entity_type"] == "bug"
        assert result["results"][1]["rank"] == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_search_passes_filters_to_repository(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Search should pass filters to repository."""
        mock_search_repo.search.return_value = []

        await search_service.search(
            query="borders",
            entities=["feature", "bug"],
            product_ids=[598, 601],
            limit=50,
        )

        mock_search_repo.search.assert_called_once()
        call_kwargs = mock_search_repo.search.call_args.kwargs
        assert call_kwargs["entities"] == ["feature", "bug"]
        assert call_kwargs["product_ids"] == [598, 601]
        assert call_kwargs["limit"] == 50

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_limit_clamped_to_max(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Limit should be clamped to max 100."""
        mock_search_repo.search.return_value = []

        await search_service.search(query="test", limit=200)

        mock_search_repo.search.assert_called_once()
        call_kwargs = mock_search_repo.search.call_args.kwargs
        assert call_kwargs["limit"] == 100

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_limit_clamped_to_min(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Limit should be clamped to min 1."""
        mock_search_repo.search.return_value = []

        await search_service.search(query="test", limit=0)

        mock_search_repo.search.assert_called_once()
        call_kwargs = mock_search_repo.search.call_args.kwargs
        assert call_kwargs["limit"] == 1


class TestQuerySanitization:
    """Test query sanitization in simple mode."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_simple_mode_sanitizes_quotes(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Simple mode should remove quotes."""
        mock_search_repo.search.return_value = []

        await search_service.search(query='"video mode"', match_mode="simple")

        call_args = mock_search_repo.search.call_args.kwargs
        assert '"' not in call_args["query"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_simple_mode_removes_boolean_operators(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Simple mode should remove AND/OR/NOT operators."""
        mock_search_repo.search.return_value = []

        await search_service.search(query="video AND mode OR test", match_mode="simple")

        call_args = mock_search_repo.search.call_args.kwargs
        assert "AND" not in call_args["query"]
        assert "OR" not in call_args["query"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raw_mode_preserves_query(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Raw mode should preserve query as-is."""
        mock_search_repo.search.return_value = []

        await search_service.search(query='"video mode" AND test', match_mode="raw")

        call_args = mock_search_repo.search.call_args.kwargs
        assert call_args["query"] == '"video mode" AND test'


class TestDateFiltering:
    """Test date range filtering."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_iso_dates_parsed_correctly(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """ISO date strings should be parsed and formatted."""
        mock_search_repo.search.return_value = []

        await search_service.search(query="test", start_date="2024-01-01", end_date="2024-12-31")

        call_args = mock_search_repo.search.call_args.kwargs
        # Start date should be start of day
        assert call_args["start_date"] == "2024-01-01T00:00:00Z"
        # End date should be end of day
        assert call_args["end_date"] == "2024-12-31T23:59:59Z"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_natural_language_dates_parsed(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """Natural language dates should be parsed."""
        mock_search_repo.search.return_value = []

        # "today" should parse without error
        await search_service.search(query="test", end_date="today")

        call_args = mock_search_repo.search.call_args.kwargs
        assert call_args["end_date"] is not None
        assert "T" in call_args["end_date"]  # ISO format

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_date_raises_error(self, search_service: SearchService) -> None:
        """Invalid date should raise ToolError."""
        with pytest.raises(ToolError):
            await search_service.search(query="test", start_date="not-a-date")


class TestOptimizeIndex:
    """Test index optimization."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_optimize_index_calls_repository(
        self, search_service: SearchService, mock_search_repo: AsyncMock
    ) -> None:
        """optimize_index should call repository method."""
        await search_service.optimize_index()

        mock_search_repo.optimize_index.assert_called_once()
