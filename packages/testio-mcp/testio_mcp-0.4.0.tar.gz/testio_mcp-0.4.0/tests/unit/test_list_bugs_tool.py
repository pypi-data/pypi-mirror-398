"""Unit tests for list_bugs MCP tool.

STORY-084: list_bugs Tool

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

from testio_mcp.exceptions import TestIOAPIError
from testio_mcp.tools.list_bugs_tool import list_bugs as list_bugs_tool

# Extract actual function from FastMCP FunctionTool wrapper
list_bugs = list_bugs_tool.fn  # type: ignore[attr-defined]


@pytest.fixture
def mock_ctx() -> MagicMock:
    """Create mock FastMCP context."""
    return MagicMock()


@pytest.fixture
def mock_bug_service() -> AsyncMock:
    """Create mock BugService."""
    service = AsyncMock()
    service.list_bugs = AsyncMock(
        return_value={
            "bugs": [
                {
                    "id": "123",
                    "title": "Test bug",
                    "severity": "critical",
                    "status": "rejected",
                    "test_id": 456,
                    "reported_at": "2024-01-01T12:00:00",
                }
            ],
            "pagination": {
                "page": 1,
                "per_page": 100,
                "offset": 0,
                "start_index": 0,
                "end_index": 0,
                "total_count": 1,
                "has_more": False,
            },
            "filters_applied": {"test_ids": [456]},
        }
    )
    return service


class TestListBugsToolDelegation:
    """Test that tool correctly delegates to service."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delegates_test_ids_to_service(
        self, mock_ctx: MagicMock, mock_bug_service: AsyncMock
    ) -> None:
        """Tool should delegate test_ids parameter to service."""
        with patch("testio_mcp.tools.list_bugs_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_bug_service

            await list_bugs(ctx=mock_ctx, test_ids=[123, 456])

            mock_bug_service.list_bugs.assert_called_once()
            call_kwargs = mock_bug_service.list_bugs.call_args.kwargs
            assert call_kwargs["test_ids"] == [123, 456]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delegates_filters_to_service(
        self, mock_ctx: MagicMock, mock_bug_service: AsyncMock
    ) -> None:
        """Tool should delegate filter parameters to service."""
        with patch("testio_mcp.tools.list_bugs_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_bug_service

            await list_bugs(
                ctx=mock_ctx,
                test_ids=[123],
                status="rejected",
                severity=["critical", "high"],
                rejection_reason="test_is_invalid",
                reported_by_user_id=789,
            )

            mock_bug_service.list_bugs.assert_called_once()
            call_kwargs = mock_bug_service.list_bugs.call_args.kwargs
            assert call_kwargs["status"] == "rejected"
            assert call_kwargs["severity"] == ["critical", "high"]
            assert call_kwargs["rejection_reason"] == "test_is_invalid"
            assert call_kwargs["reported_by_user_id"] == 789

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delegates_pagination_to_service(
        self, mock_ctx: MagicMock, mock_bug_service: AsyncMock
    ) -> None:
        """Tool should delegate pagination parameters to service."""
        with patch("testio_mcp.tools.list_bugs_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_bug_service

            await list_bugs(
                ctx=mock_ctx,
                test_ids=[123],
                page=2,
                per_page=50,
                offset=5,
            )

            mock_bug_service.list_bugs.assert_called_once()
            call_kwargs = mock_bug_service.list_bugs.call_args.kwargs
            assert call_kwargs["page"] == 2
            assert call_kwargs["per_page"] == 50
            assert call_kwargs["offset"] == 5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delegates_sorting_to_service(
        self, mock_ctx: MagicMock, mock_bug_service: AsyncMock
    ) -> None:
        """Tool should delegate sorting parameters to service."""
        with patch("testio_mcp.tools.list_bugs_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_bug_service

            await list_bugs(
                ctx=mock_ctx,
                test_ids=[123],
                sort_by="severity",
                sort_order="asc",
            )

            mock_bug_service.list_bugs.assert_called_once()
            call_kwargs = mock_bug_service.list_bugs.call_args.kwargs
            assert call_kwargs["sort_by"] == "severity"
            assert call_kwargs["sort_order"] == "asc"


class TestListBugsToolErrorHandling:
    """Test error transformation to ToolError."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transforms_api_error_to_tool_error(
        self, mock_ctx: MagicMock, mock_bug_service: AsyncMock
    ) -> None:
        """Tool should convert TestIOAPIError to ToolError with user-friendly message."""
        mock_bug_service.list_bugs.side_effect = TestIOAPIError(
            status_code=500, message="Internal server error"
        )

        with patch("testio_mcp.tools.list_bugs_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_bug_service

            with pytest.raises(ToolError) as exc_info:
                await list_bugs(ctx=mock_ctx, test_ids=[123])

            error_msg = str(exc_info.value)
            assert "❌" in error_msg  # Error indicator
            assert "API error" in error_msg
            assert "500" in error_msg
            assert "ℹ️" in error_msg  # Context
            assert "💡" in error_msg  # Solution

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_transforms_generic_error_to_tool_error(
        self, mock_ctx: MagicMock, mock_bug_service: AsyncMock
    ) -> None:
        """Tool should convert unexpected errors to ToolError."""
        mock_bug_service.list_bugs.side_effect = RuntimeError("Something went wrong")

        with patch("testio_mcp.tools.list_bugs_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_bug_service

            with pytest.raises(ToolError) as exc_info:
                await list_bugs(ctx=mock_ctx, test_ids=[123])

            error_msg = str(exc_info.value)
            assert "❌" in error_msg
            assert "Unexpected error" in error_msg
            assert "ℹ️" in error_msg
            assert "💡" in error_msg


class TestListBugsToolOutput:
    """Test output schema validation."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_valid_output_schema(
        self, mock_ctx: MagicMock, mock_bug_service: AsyncMock
    ) -> None:
        """Tool should return valid ListBugsOutput schema."""
        with patch("testio_mcp.tools.list_bugs_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_bug_service

            result = await list_bugs(ctx=mock_ctx, test_ids=[456])

            # Verify output structure
            assert "bugs" in result
            assert "pagination" in result
            assert "filters_applied" in result

            # Verify bugs list
            assert isinstance(result["bugs"], list)
            if result["bugs"]:
                bug = result["bugs"][0]
                assert "id" in bug
                assert "title" in bug
                assert "severity" in bug
                assert "status" in bug
                assert "test_id" in bug
                assert "reported_at" in bug

            # Verify pagination
            pagination = result["pagination"]
            assert "page" in pagination
            assert "per_page" in pagination
            assert "offset" in pagination
            assert "start_index" in pagination
            assert "end_index" in pagination
            assert "total_count" in pagination
            assert "has_more" in pagination

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handles_empty_results(
        self, mock_ctx: MagicMock, mock_bug_service: AsyncMock
    ) -> None:
        """Tool should handle empty bug list correctly."""
        mock_bug_service.list_bugs.return_value = {
            "bugs": [],
            "pagination": {
                "page": 1,
                "per_page": 100,
                "offset": 0,
                "start_index": 0,
                "end_index": -1,
                "total_count": 0,
                "has_more": False,
            },
            "filters_applied": {"test_ids": [123]},
        }

        with patch("testio_mcp.tools.list_bugs_tool.get_service_context") as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_bug_service

            result = await list_bugs(ctx=mock_ctx, test_ids=[123])

            assert result["bugs"] == []
            assert result["pagination"]["total_count"] == 0
            assert result["pagination"]["has_more"] is False
