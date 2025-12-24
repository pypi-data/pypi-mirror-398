"""MCP tool for on-demand data synchronization.

This module implements the sync_data tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Validates input with Pydantic
2. Parses date strings to datetime objects
3. Maps parameters to SyncService data models
4. Delegates to SyncService for sync execution
5. Converts exceptions to user-friendly error format

STORY-051: sync_data MCP Tool
Epic: EPIC-009 (Sync Consolidation)
"""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from testio_mcp.schemas.sync import SyncDataOutput
from testio_mcp.server import mcp
from testio_mcp.services.sync_service import (
    SyncLockError,
    SyncOptions,
    SyncPhase,
    SyncScope,
    SyncService,
    SyncTimeoutError,
)
from testio_mcp.utilities import get_service_context, parse_flexible_date, parse_int_list_input
from testio_mcp.utilities.progress import ProgressReporter
from testio_mcp.utilities.schema_utils import inline_schema_refs


@mcp.tool(output_schema=inline_schema_refs(SyncDataOutput.model_json_schema()))
async def sync_data(
    ctx: Context,
    product_ids: Annotated[
        list[int] | str | int | None,
        Field(
            description=(
                "Limit sync to specific products (default: all products). "
                "Accepts: list of ints [598, 599], single int 598, "
                "comma-separated string '598,599', or JSON array '[598, 599]'"
            ),
            examples=[[598], [598, 599], "598", "598,599", None],
        ),
    ] = None,
    since: Annotated[
        str | None,
        Field(
            description=(
                "Date/range filter for sync scope (ISO 8601, natural language, or 'all'). "
                "- None (default): Incremental - discover new tests only "
                "(fast, early-stop enabled). "
                "- Date string: Sync all tests after date "
                "(e.g., '7 days ago', '2025-11-01'). "
                "- 'all': Full resync - refresh all tests (slowest, most thorough)."
            ),
            examples=["7 days ago", "2025-11-01", "last week", "all"],
        ),
    ] = None,
) -> dict[str, Any]:
    """Refresh local data from TestIO API.

    Syncs products, features, and tests. Background sync runs automatically
    (configurable interval, default 15min). Use before reports for fresh data.

    Modes:
    - No params: Fast incremental (new tests only)
    - since="7 days ago": All tests after date
    - since="all": Full resync (slowest, use for recovery)

    Examples:
        sync_data()                              # Quick refresh
        sync_data(since="yesterday")             # Recent tests
        sync_data(product_ids=[598], since="all")  # Full product sync
    """
    # Normalize product_ids input (accepts string, int, list, comma-separated)
    try:
        normalized_product_ids = parse_int_list_input(product_ids)
    except ValueError as e:
        raise ToolError(
            f"❌ Invalid product_ids format\n"
            f"ℹ️ {e}\n"
            f"💡 Use: [598, 599], 598, '598,599', or '[598, 599]'"
        ) from e

    # Extract service dependency with proper session lifecycle (TD-001)
    async with get_service_context(ctx, SyncService) as service:
        try:
            # Parse 'since' parameter and determine sync mode
            # - None: Incremental mode (fast, early-stop enabled)
            # - "all": Full resync mode (force_refresh=True, no date filter)
            # - Date string: Date range mode (force_refresh=True to disable
            #   early-stop, with date filter)
            since_date = None
            force_refresh = False

            if since is None:
                # Incremental mode: discover new tests only (early-stop enabled)
                since_date = None
                force_refresh = False
            elif since.lower() == "all":
                # Full resync mode: refresh all tests (no date filter, no early-stop)
                since_date = None
                force_refresh = True
            else:
                # Date range mode: sync all tests after date (with date filter, no early-stop)
                # Auto-enable force_refresh to disable known-test early-stop
                # (age-based stop at lines 738-742 in sync_service.py handles "too old" logic)
                since_iso = parse_flexible_date(since)
                since_date = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
                force_refresh = True

            # Map parameters to SyncService data models (AC3)
            scope = SyncScope(
                product_ids=normalized_product_ids,
                since_date=since_date,
            )

            options = SyncOptions(
                force_refresh=force_refresh,
            )

            # Use all 3 phases (AC3)
            phases = [SyncPhase.PRODUCTS, SyncPhase.FEATURES, SyncPhase.NEW_TESTS]

            # Create progress reporter for MCP notifications
            # (no-op if client doesn't support progressToken)
            reporter = ProgressReporter.from_context(ctx)

            # Execute sync via SyncService (AC3)
            result = await service.execute_sync(
                phases=phases,
                scope=scope,
                options=options,
                trigger_source="mcp",
                progress=reporter,
            )

            # Update last_sync_completed timestamp (AC4)
            # This prevents immediate background sync after manual MCP sync
            await service.cache.set_metadata_value(
                key="last_sync_completed",
                value=datetime.now(UTC).isoformat(),
            )

            # Format response (AC6)
            status = "completed_with_warnings" if result.warnings else "completed"

            return SyncDataOutput(
                status=status,
                products_synced=result.products_synced,
                features_refreshed=result.features_refreshed,
                tests_discovered=result.tests_discovered,
                tests_updated=result.tests_updated,
                duration_seconds=result.duration_seconds,
                warnings=result.warnings if result.warnings else None,
            ).model_dump(exclude_none=True)

        except SyncTimeoutError as e:
            # Lock acquisition timeout (must check before SyncLockError - subclass)
            raise ToolError(
                "❌ Sync lock timeout (30s)\n"
                "ℹ️ Another process is holding the sync lock\n"
                "💡 Check for stale processes or retry after ~15min"
            ) from e

        except SyncLockError as e:
            # Lock acquisition failed - another sync in progress
            raise ToolError(
                "❌ Sync already in progress\n"
                "ℹ️ Another sync is running (CLI, background, or MCP)\n"
                "💡 Wait 30-60s or check get_server_diagnostics for sync status"
            ) from e

        except Exception as e:
            # Unexpected error
            raise ToolError(
                f"❌ Sync failed unexpectedly\n"
                f"ℹ️ Error: {e}\n"
                f"💡 Check logs for details or contact support"
            ) from e
