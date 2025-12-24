"""Unit tests for get_problematic_tests tool.

STORY-060: Tests for get_problematic_tests (kept separate from consolidated diagnostics).
This tool provides read-only visibility for tests that failed to sync.

Reference: STORY-021 AC7 (Database Management Tools), STORY-060 (Consolidation)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from testio_mcp.tools.cache_tools import (
    get_problematic_tests as get_problematic_tests_tool,
)

# Extract actual function from FastMCP FunctionTool wrapper
get_problematic_tests = get_problematic_tests_tool.fn  # type: ignore[attr-defined]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_problematic_tests_returns_all_problematic() -> None:
    """Verify get_problematic_tests returns all problematic tests."""
    mock_cache = AsyncMock()
    mock_cache.get_problematic_tests.return_value = [
        {
            "test_id": None,
            "product_id": 123,
            "boundary_before_id": 100,
            "boundary_after_id": 102,
            "recovery_attempts": 5,
        },
        {
            "test_id": None,
            "product_id": 456,
            "boundary_before_id": 200,
            "boundary_after_id": 202,
            "recovery_attempts": 5,
        },
    ]

    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context = {"cache": mock_cache}

    result = await get_problematic_tests(ctx=mock_ctx)

    assert result["count"] == 2
    assert len(result["tests"]) == 2
    assert "500 errors" in result["message"]
    mock_cache.get_problematic_tests.assert_called_once_with(product_id=None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_problematic_tests_filters_by_product() -> None:
    """Verify get_problematic_tests filters by product_id."""
    mock_cache = AsyncMock()
    mock_cache.get_problematic_tests.return_value = [
        {
            "test_id": None,
            "product_id": 123,
            "boundary_before_id": 100,
            "boundary_after_id": 102,
            "recovery_attempts": 5,
        },
    ]

    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context = {"cache": mock_cache}

    result = await get_problematic_tests(ctx=mock_ctx, product_id=123)

    assert result["count"] == 1
    mock_cache.get_problematic_tests.assert_called_once_with(product_id=123)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_problematic_tests_handles_no_problems() -> None:
    """Verify get_problematic_tests handles zero problematic tests."""
    mock_cache = AsyncMock()
    mock_cache.get_problematic_tests.return_value = []

    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context = {"cache": mock_cache}

    result = await get_problematic_tests(ctx=mock_ctx)

    assert result["count"] == 0
    assert len(result["tests"]) == 0
