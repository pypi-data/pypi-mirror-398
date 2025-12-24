"""Database monitoring tool for problematic tests.

This tool provides read-only visibility for tests that failed to sync due to API 500 errors.
Useful for filing support tickets with TestIO and monitoring data quality.

STORY-060: Kept separate from consolidated diagnostics (niche use case).

Tool is auto-discovered and registered via ADR-011 pattern.
"""

from typing import Any, cast

from fastmcp import Context
from pydantic import BaseModel, Field

from testio_mcp.server import ServerContext, mcp


class ProblematicTestsOutput(BaseModel):
    """Tests that failed to sync."""

    count: int = Field(description="Number of problematic tests", ge=0)
    tests: list[dict[str, Any]] = Field(description="Tests with boundary info")
    message: str = Field(description="Guidance message")


@mcp.tool(output_schema=ProblematicTestsOutput.model_json_schema())
async def get_problematic_tests(ctx: Context, product_id: int | None = None) -> dict[str, Any]:
    """Get tests that failed to sync (API 500 errors).

    Args:
        ctx: FastMCP context
        product_id: Optional product filter

    Returns:
        Tests with boundary IDs for debugging sync failures
    """
    # Access cache from lifespan context
    assert ctx.request_context is not None
    lifespan_ctx = cast(ServerContext, ctx.request_context.lifespan_context)
    cache = lifespan_ctx["cache"]

    # Get problematic tests
    problematic = await cache.get_problematic_tests(product_id=product_id)

    # Build result
    result = ProblematicTestsOutput(
        count=len(problematic),
        tests=problematic,
        message="Tests with 500 errors during sync. Use boundary IDs for debugging.",
    )
    return result.model_dump(by_alias=True, exclude_none=True)
