"""MCP tool for listing products.

This module implements the list_products tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Validates input with Pydantic
2. Extracts dependencies from server context (ADR-007)
3. Delegates to ProductService
4. Converts exceptions to user-friendly error format
"""

from typing import Annotated, Any, Literal

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, field_validator

from testio_mcp.exceptions import TestIOAPIError
from testio_mcp.server import mcp
from testio_mcp.services.product_service import ProductService
from testio_mcp.utilities import get_service_context
from testio_mcp.utilities.schema_utils import inline_schema_refs

# Type aliases for valid values (using Literal to avoid $defs in JSON schema)

ProductType = Literal["website", "mobile_app_ios", "mobile_app_android", "streaming_app"]

# Pydantic Models
# NOTE: Models use nested BaseModel classes for type safety and better FastAPI docs.
# Schemas are post-processed with inline_schema_refs() to avoid $ref resolution issues
# in some MCP clients like Gemini CLI 0.16.0.


class ProductSummary(BaseModel):
    """Product summary with computed counts and recency indicators (STORY-058, STORY-083)."""

    product_id: int = Field(description="Product ID", alias="id")
    name: str = Field(description="Product name")
    type: str = Field(description="Product type")
    description: str | None = Field(default=None, description="Product description")
    test_count: int = Field(description="Total tests for this product (all-time)", ge=0)
    feature_count: int = Field(description="Total features for this product", ge=0)
    tests_last_30_days: int = Field(
        description="Active/completed tests in last 30 days (running/locked/archived)", ge=0
    )
    tests_last_90_days: int = Field(
        description="Active/completed tests in last 90 days (running/locked/archived)", ge=0
    )
    last_test_end_at: str | None = Field(
        default=None,
        description="Most recent test end date (running/locked/archived, ISO 8601)",
    )

    @field_validator("product_id", mode="before")
    @classmethod
    def coerce_id_to_int(cls, v: Any) -> int:
        """Convert product ID to integer (accepts string or int input).

        Args:
            v: Product ID value (int or str)

        Returns:
            Product ID as integer

        Raises:
            ValueError: If value cannot be converted to integer
        """
        return int(v)


class ListProductsOutput(BaseModel):
    """List products output."""

    total_count: int = Field(description="Total products after filtering", ge=0)
    filters_applied: dict[str, str | list[str] | None] = Field(description="Applied filters")
    products: list[ProductSummary] = Field(description="Product list")
    page: int = Field(description="Page number (1-indexed)", ge=1, default=1)
    per_page: int = Field(description="Items per page", ge=1, le=100, default=50)


# MCP Tool


@mcp.tool(output_schema=inline_schema_refs(ListProductsOutput.model_json_schema()))
async def list_products(
    ctx: Context,
    search: Annotated[
        str | None, Field(description="Filter by name or description (case-insensitive)")
    ] = None,
    product_type: Annotated[
        str | list[ProductType] | None,
        Field(
            description="Filter by type. Values: website, mobile_app_ios, mobile_app_android, "
            'streaming_app. Format: "website,mobile_app_ios" or ["website"]',
            examples=["website", "mobile_app_ios,mobile_app_android", ["website"]],
        ),
    ] = None,
    sort_by: Annotated[
        Literal["title", "product_type", "last_synced"] | None,
        Field(description="Sort field. Values: title, product_type, last_synced"),
    ] = None,
    sort_order: Annotated[
        Literal["asc", "desc"], Field(description="Sort order. Values: asc, desc")
    ] = "asc",
    page: Annotated[int, Field(description="Page number (1-indexed)", ge=1)] = 1,
    per_page: Annotated[int, Field(description="Items per page", ge=1, le=100)] = 50,
    offset: Annotated[int, Field(description="0-indexed offset (alternative to page)", ge=0)] = 0,
) -> dict[str, Any]:
    """List products with search, filtering, sorting, and pagination.

    Returns enriched metadata to provide "information scent":
    - Volume: test_count, feature_count (all-time)
    - Recency: tests_last_30_days, tests_last_90_days, last_test_end_at

    Enables agents to identify active products and understand data volume
    without additional queries.

    Use to discover product IDs for other tools.

    Note: Bug counts are not included in product listings because:
    - Bug data syncs incrementally per-test (no single "product bug count" moment)
    - For bug analysis, use get_product_quality_report (with date/severity filters)
    - For aggregated bug metrics, use query_metrics (dimensions, filters)
    """
    # Create service with managed AsyncSession lifecycle (STORY-033)
    async with get_service_context(ctx, ProductService) as service:
        # Delegate to service and convert exceptions to MCP error format
        try:
            # Parse comma-separated string to list if needed (AI-friendly format)
            from typing import cast

            product_types: list[str] | None = None
            if product_type is not None:
                if isinstance(product_type, str):
                    # Parse comma-separated: "website,mobile_app_ios" → list
                    product_types = [t.strip() for t in product_type.split(",")]
                else:
                    # Already a list (cast for mypy: Literal types are strings)
                    product_types = cast(list[str], product_type)

            result = await service.list_products(
                search=search,
                product_type=product_types,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                per_page=per_page,
                offset=offset,
            )

            # Validate output with Pydantic
            # This ensures API response matches expected structure
            validated = ListProductsOutput(**result)
            return validated.model_dump(by_alias=True, exclude_none=True)

        except TestIOAPIError as e:
            # Convert API error to ToolError with user-friendly message
            raise ToolError(
                f"❌ API error: {e.message}\n"
                f"ℹ️  HTTP status code: {e.status_code}\n"
                f"💡 Check API status and authentication. If the problem persists, contact support."
            ) from e

        except Exception as e:
            # Catch-all for unexpected errors
            raise ToolError(
                f"❌ Unexpected error: {str(e)}\n"
                f"ℹ️  An unexpected error occurred while fetching products\n"
                f"💡 Please try again or contact support if the problem persists"
            ) from e
