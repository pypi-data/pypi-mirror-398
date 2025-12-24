"""MCP Prompts for TestIO workflows.

This package provides user-invoked workflow templates that expand into
structured instructions for AI agents. Prompts follow verb+noun naming
and guide agents through multi-step operations.

Available prompts:
- analyze-product-quality: Quality analysis workflow for a product
- prep-meeting: Transform analysis artifacts into meeting-ready materials

Usage:
    Prompts are auto-registered with the MCP server via import.
    Import this module in server.py to register all prompts.

Example:
    # In server.py
    from testio_mcp import prompts  # noqa: F401 - registers prompts
"""

# Import all prompt modules to register them with @mcp.prompt decorator
from testio_mcp.prompts import (
    analyze_product_quality,  # noqa: F401
    prep_meeting,  # noqa: F401
)

__all__ = [
    "analyze_product_quality",
    "prep_meeting",
]
