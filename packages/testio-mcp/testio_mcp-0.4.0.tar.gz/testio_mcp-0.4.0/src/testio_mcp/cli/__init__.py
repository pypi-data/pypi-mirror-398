"""CLI module for TestIO MCP Server.

Provides command-line interface with subcommands:
- serve: Start MCP server (default)
- sync: Manual database synchronization
- problematic: Manage tests that failed to sync
"""

from testio_mcp.cli.main import main

__all__ = ["main"]
