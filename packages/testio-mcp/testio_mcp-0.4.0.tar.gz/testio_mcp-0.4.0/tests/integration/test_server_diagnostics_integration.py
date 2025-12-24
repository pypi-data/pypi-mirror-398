"""Integration tests for get_server_diagnostics tool.

STORY-060: Test consolidated diagnostic tool with real database.

Integration tests use real PersistentCache and verify tool registration.
Marked with @pytest.mark.integration to separate from unit tests.
"""

import pytest

from testio_mcp.database.cache import PersistentCache
from testio_mcp.tools.server_diagnostics_tool import (
    get_server_diagnostics as get_server_diagnostics_tool,
)

# Extract actual function from FastMCP FunctionTool wrapper
get_server_diagnostics = get_server_diagnostics_tool.fn  # type: ignore[attr-defined]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tool_registration_and_discovery():
    """Verify get_server_diagnostics is registered via auto-discovery."""
    # Import server to trigger tool registration
    from testio_mcp import server

    # Verify tool is registered
    tools = list(server.mcp._tool_manager._tools.keys())
    assert "get_server_diagnostics" in tools


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_server_diagnostics_with_real_database(shared_cache: PersistentCache):
    """Verify tool returns valid ServerDiagnostics structure with real data."""
    # Create mock context
    from unittest.mock import MagicMock

    from testio_mcp.client import TestIOClient
    from testio_mcp.config import Settings

    settings = Settings()
    client = TestIOClient(
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
    )

    # Create mock MCP context
    ctx = MagicMock()
    ctx.request_context = MagicMock()
    ctx.request_context.lifespan_context = {
        "testio_client": client,
        "cache": shared_cache,
    }

    # Act
    result = await get_server_diagnostics(ctx=ctx, include_sync_events=False)

    # Assert - verify structure
    assert "api" in result
    assert "database" in result
    assert "sync" in result
    assert "storage" in result

    # Assert - API status (may fail if no token, but structure should be valid)
    assert "connected" in result["api"]
    assert "product_count" in result["api"]
    assert "message" in result["api"]

    # Assert - Database status
    assert isinstance(result["database"]["size_mb"], float)
    assert result["database"]["size_mb"] >= 0
    assert isinstance(result["database"]["test_count"], int)
    assert result["database"]["test_count"] >= 0
    assert isinstance(result["database"]["product_count"], int)
    assert result["database"]["feature_count"] >= 0
    assert result["database"]["bug_count"] >= 0

    # Assert - Sync status
    # success_rate_24h can be None if no syncs in last 24h (more honest than defaulting to 100%)
    if result["sync"]["success_rate_24h"] is not None:
        assert isinstance(result["sync"]["success_rate_24h"], float)
        assert 0 <= result["sync"]["success_rate_24h"] <= 100
    assert isinstance(result["sync"]["circuit_breaker_active"], bool)

    # Assert - Storage range (may be empty if no tests in database)
    assert "storage" in result
    # If there are tests, dates should be present
    if result["database"]["test_count"] > 0:
        # Dates may be excluded if None (exclude_none=True)
        # This is valid - an empty storage dict means no test data available
        assert isinstance(result["storage"], dict)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_server_diagnostics_with_sync_events(shared_cache: PersistentCache):
    """Verify tool includes sync events when requested."""
    # Create mock context
    from unittest.mock import MagicMock

    from testio_mcp.client import TestIOClient
    from testio_mcp.config import Settings

    settings = Settings()
    client = TestIOClient(
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
    )

    # Create mock MCP context
    ctx = MagicMock()
    ctx.request_context = MagicMock()
    ctx.request_context.lifespan_context = {
        "testio_client": client,
        "cache": shared_cache,
    }

    # Act
    result = await get_server_diagnostics(ctx=ctx, include_sync_events=True, sync_event_limit=5)

    # Assert - events field exists
    assert "events" in result

    # If events exist, verify structure
    if result["events"] is not None and len(result["events"]) > 0:
        event = result["events"][0]
        assert "started_at" in event
        assert "status" in event
        assert event["status"] in ["running", "completed", "failed"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_stats_reflect_real_data(shared_cache: PersistentCache):
    """Verify database stats reflect actual entity counts."""
    # Create mock context
    from unittest.mock import MagicMock

    from testio_mcp.client import TestIOClient
    from testio_mcp.config import Settings

    settings = Settings()
    client = TestIOClient(
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
    )

    # Create mock MCP context
    ctx = MagicMock()
    ctx.request_context = MagicMock()
    ctx.request_context.lifespan_context = {
        "testio_client": client,
        "cache": shared_cache,
    }

    # Get actual counts from cache
    actual_test_count = await shared_cache.count_tests()
    actual_product_count = await shared_cache.count_products()

    # Act
    result = await get_server_diagnostics(ctx=ctx)

    # Assert - counts match
    assert result["database"]["test_count"] == actual_test_count
    assert result["database"]["product_count"] == actual_product_count
