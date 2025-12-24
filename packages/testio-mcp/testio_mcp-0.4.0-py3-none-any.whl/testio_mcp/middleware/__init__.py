"""Custom middleware for TestIO MCP server."""

from testio_mcp.middleware.error_handler import PromptErrorMiddleware

__all__ = ["PromptErrorMiddleware"]
