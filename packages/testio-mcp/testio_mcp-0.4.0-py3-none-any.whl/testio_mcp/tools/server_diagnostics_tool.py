"""Server diagnostics tool for health monitoring.

Consolidated tool combining:
- API connectivity (health_check)
- Database statistics (get_database_stats)
- Sync history (get_sync_history)

STORY-060: Reduce token overhead by consolidating 3 tools into 1.

Tool is auto-discovered and registered via ADR-011 pattern.
"""

from typing import Any

from fastmcp import Context

from testio_mcp.server import mcp
from testio_mcp.services.diagnostics_service import ServerDiagnostics
from testio_mcp.utilities import get_service_context
from testio_mcp.utilities.schema_utils import inline_schema_refs


@mcp.tool(output_schema=inline_schema_refs(ServerDiagnostics.model_json_schema()))
async def get_server_diagnostics(
    ctx: Context,
    include_sync_events: bool = False,
    sync_event_limit: int = 5,
) -> dict[str, Any]:
    """Get server diagnostics (API, database, sync status).

    Consolidated health check for monitoring server state.

    Args:
        ctx: FastMCP context (injected)
        include_sync_events: Include recent sync event history
        sync_event_limit: Max sync events (1-20, default: 5)

    Returns:
        Server diagnostics with API status, database stats, sync info, and storage range
    """
    from testio_mcp.services.diagnostics_service import DiagnosticsService

    async with get_service_context(ctx, DiagnosticsService) as service:
        return await service.get_server_diagnostics(
            include_sync_events=include_sync_events,
            sync_event_limit=sync_event_limit,
        )
