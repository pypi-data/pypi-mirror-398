"""Unit tests for search MCP tool.

STORY-065: Search MCP Tool

Tests follow the Story-016 Pattern:
- Extract actual function from FastMCP FunctionTool wrapper
- Mock context with MagicMock(), service with AsyncMock()
- Patch get_service_context at tool file level
- Test error transformations (domain exceptions → ToolError)
- Test service delegation (parameters passed correctly)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.exceptions import InvalidSearchQueryError
from testio_mcp.tools.search_tool import search as search_tool

# Extract actual function from FastMCP FunctionTool wrapper
search = search_tool.fn  # type: ignore[attr-defined]


@pytest.fixture
def mock_ctx() -> MagicMock:
    """Create mock FastMCP context."""
    return MagicMock()


@pytest.fixture
def mock_search_service() -> AsyncMock:
    """Create mock SearchService."""
    service = AsyncMock()
    service.search = AsyncMock(
        return_value={
            "query": "test",
            "total": 1,
            "results": [
                {
                    "entity_type": "feature",
                    "entity_id": 123,
                    "title": "Test Feature",
                    "score": -5.5,
                    "rank": 1,
                }
            ],
        }
    )
    return service


class TestSearchToolDelegation:
    """Test that tool correctly delegates to service."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delegates_query_to_service(
        self, mock_ctx: MagicMock, mock_search_service: AsyncMock
    ) -> None:
        """Tool should delegate query parameter to service."""
        with patch("testio_mcp.tools.search_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_search_service

            await search(ctx=mock_ctx, query="borders")

            mock_search_service.search.assert_called_once()
            call_kwargs = mock_search_service.search.call_args.kwargs
            assert call_kwargs["query"] == "borders"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delegates_all_parameters_to_service(
        self, mock_ctx: MagicMock, mock_search_service: AsyncMock
    ) -> None:
        """Tool should delegate all parameters to service."""
        with patch("testio_mcp.tools.search_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_search_service

            await search(
                ctx=mock_ctx,
                query="video mode",
                entities=["feature", "bug"],
                product_ids=[598, 601],
                start_date="2024-01-01",
                end_date="today",
                limit=50,
                match_mode="raw",
            )

            mock_search_service.search.assert_called_once()
            call_kwargs = mock_search_service.search.call_args.kwargs
            assert call_kwargs["query"] == "video mode"
            assert call_kwargs["entities"] == ["feature", "bug"]
            assert call_kwargs["product_ids"] == [598, 601]
            assert call_kwargs["start_date"] == "2024-01-01"
            assert call_kwargs["end_date"] == "today"
            assert call_kwargs["limit"] == 50
            assert call_kwargs["match_mode"] == "raw"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_formatted_output(
        self, mock_ctx: MagicMock, mock_search_service: AsyncMock
    ) -> None:
        """Tool should return properly formatted output."""
        with patch("testio_mcp.tools.search_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_search_service

            result = await search(ctx=mock_ctx, query="test")

            assert "query" in result
            assert "total" in result
            assert "results" in result
            assert result["query"] == "test"
            assert result["total"] == 1


class TestSearchToolErrorHandling:
    """Test error transformation to ToolError format."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transforms_invalid_query_to_tool_error(
        self, mock_ctx: MagicMock, mock_search_service: AsyncMock
    ) -> None:
        """InvalidSearchQueryError should transform to ToolError with ❌ℹ️💡."""
        mock_search_service.search.side_effect = InvalidSearchQueryError(
            "Search query cannot be empty."
        )

        with patch("testio_mcp.tools.search_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_search_service

            with pytest.raises(ToolError) as exc_info:
                await search(ctx=mock_ctx, query="")

            error_msg = str(exc_info.value)
            assert "❌" in error_msg
            assert "Invalid search query" in error_msg
            assert "ℹ️" in error_msg
            assert "💡" in error_msg

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transforms_invalid_entity_to_tool_error(
        self, mock_ctx: MagicMock, mock_search_service: AsyncMock
    ) -> None:
        """ValueError for invalid entity should transform to ToolError."""
        mock_search_service.search.side_effect = ValueError(
            "Invalid entity types: ['invalid']. Valid types: ['product', 'feature', 'test', 'bug']"
        )

        with patch("testio_mcp.tools.search_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_search_service

            with pytest.raises(ToolError) as exc_info:
                await search(ctx=mock_ctx, query="test", entities=["invalid"])

            error_msg = str(exc_info.value)
            assert "❌" in error_msg
            assert "Invalid entity type" in error_msg
            assert "💡" in error_msg
            assert "Valid types" in error_msg

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transforms_unexpected_error_to_tool_error(
        self, mock_ctx: MagicMock, mock_search_service: AsyncMock
    ) -> None:
        """Unexpected exceptions should transform to generic ToolError."""
        mock_search_service.search.side_effect = RuntimeError("Database connection failed")

        with patch("testio_mcp.tools.search_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_search_service

            with pytest.raises(ToolError) as exc_info:
                await search(ctx=mock_ctx, query="test")

            error_msg = str(exc_info.value)
            assert "❌" in error_msg
            assert "Search failed" in error_msg
            assert "ℹ️" in error_msg
            assert "💡" in error_msg


class TestSearchToolDefaults:
    """Test default parameter values."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_default_limit_is_20(
        self, mock_ctx: MagicMock, mock_search_service: AsyncMock
    ) -> None:
        """Default limit should be 20."""
        with patch("testio_mcp.tools.search_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_search_service

            await search(ctx=mock_ctx, query="test")

            call_kwargs = mock_search_service.search.call_args.kwargs
            assert call_kwargs["limit"] == 20

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_default_match_mode_is_simple(
        self, mock_ctx: MagicMock, mock_search_service: AsyncMock
    ) -> None:
        """Default match_mode should be 'simple'."""
        with patch("testio_mcp.tools.search_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_search_service

            await search(ctx=mock_ctx, query="test")

            call_kwargs = mock_search_service.search.call_args.kwargs
            assert call_kwargs["match_mode"] == "simple"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_none_entities_passed_as_none(
        self, mock_ctx: MagicMock, mock_search_service: AsyncMock
    ) -> None:
        """None entities should be passed as None to service."""
        with patch("testio_mcp.tools.search_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_search_service

            await search(ctx=mock_ctx, query="test", entities=None)

            call_kwargs = mock_search_service.search.call_args.kwargs
            assert call_kwargs["entities"] is None
