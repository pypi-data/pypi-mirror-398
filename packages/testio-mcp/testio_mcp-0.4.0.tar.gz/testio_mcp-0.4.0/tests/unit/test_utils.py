"""Test utilities for mocking async context managers in MCP tool tests.

This module provides helper functions to simplify mocking of get_service_context()
in unit tests after the STORY-033 refactoring.
"""

from unittest.mock import AsyncMock


def mock_service_context(mock_service):
    """Create a mock async context manager that yields the given service.

    This helper simplifies mocking get_service_context() in tool tests.

    Args:
        mock_service: The mocked service instance to yield from the context manager

    Returns:
        AsyncMock configured as an async context manager

    Example:
        >>> mock_service = AsyncMock()
        >>> mock_service.get_test_status.return_value = {...}
        >>> mock_ctx = mock_service_context(mock_service)
        >>> with patch(
                "testio_mcp.tools.test_status_tool.get_service_context",
                return_value=mock_ctx,
            ):
            ...     result = await get_test_status(test_id=123, ctx=ctx)
    """
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_service
    mock_context.__aexit__.return_value = None
    return mock_context
