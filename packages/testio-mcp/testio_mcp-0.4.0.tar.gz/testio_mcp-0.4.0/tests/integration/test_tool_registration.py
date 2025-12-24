"""Integration tests for tool registration (STORY-015).

Tests the default tool registration using in-process FastMCP client.
Tool filtering tests (ENABLED_TOOLS/DISABLED_TOOLS) should be unit tests
since they require reimporting modules with different environment variables.
"""

import pytest
from fastmcp import Client


async def list_tools_in_process() -> list[dict[str, any]]:
    """List tools using in-process FastMCP client.

    Returns:
        List of tool definitions
    """
    from testio_mcp.server import mcp

    # Use in-process client (no subprocess needed)
    async with Client(mcp) as client:
        tools = await client.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in tools
        ]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_default_all_tools_registered() -> None:
    """Test that all tools are registered by default with valid schema (behavioral).

    Tests behavior (schema compliance, minimum count) instead of exact tool names.
    This makes tests resilient to tool additions/renames.

    Note: Tool filtering tests (ENABLED_TOOLS/DISABLED_TOOLS) are better suited
    for unit tests since they require module reloading with different env vars.
    """
    tools = await list_tools_in_process()

    # Test behavior: minimum tool count (not exact count - tolerates additions)
    assert len(tools) >= 6, f"Expected minimum 6 tools, got {len(tools)}"

    # Test behavior: all tools have required MCP schema fields
    for tool in tools:
        assert "name" in tool, f"Tool missing 'name' field: {tool}"
        assert "description" in tool, f"Tool '{tool.get('name')}' missing 'description'"
        assert "inputSchema" in tool, f"Tool '{tool['name']}' missing 'inputSchema'"
        assert tool["description"], f"Tool '{tool['name']}' has empty description"

    # Test behavior: core tools always available (minimum required set)
    tool_names = {tool["name"] for tool in tools}
    # Updated for STORY-060: health_check consolidated into get_server_diagnostics
    required_tools = {"get_server_diagnostics", "list_products", "get_test_summary"}
    assert required_tools.issubset(tool_names), (
        f"Missing required tools: {required_tools - tool_names}"
    )
