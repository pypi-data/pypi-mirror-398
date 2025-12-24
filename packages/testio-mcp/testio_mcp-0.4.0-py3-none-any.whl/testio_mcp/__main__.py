"""Entry point for running TestIO MCP server as a module.

This allows running the server with: python -m testio_mcp
Or via CLI entry point: testio-mcp (after pip install)
"""

from testio_mcp.cli.main import main

if __name__ == "__main__":
    main()
