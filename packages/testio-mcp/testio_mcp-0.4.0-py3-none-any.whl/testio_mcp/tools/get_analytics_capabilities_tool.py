"""MCP tool for discovering analytics capabilities.

This module implements the get_analytics_capabilities tool following the
service layer pattern (ADR-011). The tool is a thin wrapper that:
1. Uses async context manager for resource cleanup
2. Delegates to AnalyticsService
3. Returns dimension/metric registry information

STORY-044: Query Metrics Tool
Epic: EPIC-007 (Generic Analytics Framework)
"""

from typing import Any

from fastmcp import Context

from testio_mcp.server import mcp
from testio_mcp.services.analytics_service import AnalyticsService
from testio_mcp.utilities import get_service_context


@mcp.tool()
async def get_analytics_capabilities(ctx: Context) -> dict[str, Any]:
    """List available dimensions and metrics for query_metrics.

    Use before query_metrics to discover grouping options (dimensions)
    and measurements (metrics).

    Returns dimension/metric definitions with descriptions, examples,
    formulas, and query limits (max dimensions, rows, timeout).
    """
    async with get_service_context(ctx, AnalyticsService) as service:
        # Get registries
        dimensions = [
            {
                "key": dim.key,
                "description": dim.description,
                "example": dim.example,
            }
            for dim in service._dimensions.values()
        ]

        metrics = [
            {
                "key": metric.key,
                "description": metric.description,
                "formula": metric.formula,
            }
            for metric in service._metrics.values()
        ]

        return {
            "dimensions": dimensions,
            "metrics": metrics,
            "limits": {
                "max_dimensions": 2,  # V1 limit (V2 will extend to 3)
                "max_rows": 1000,
                "timeout_seconds": 90,  # Inherits HTTP_TIMEOUT_SECONDS
            },
        }
