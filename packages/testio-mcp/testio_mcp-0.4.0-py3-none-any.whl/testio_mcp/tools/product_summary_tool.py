"""MCP tool for getting product summary.

This module implements the get_product_summary tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Validates input with Pydantic
2. Extracts dependencies from server context (ADR-007)
3. Delegates to ProductService
4. Converts exceptions to user-friendly error format

STORY-057: Add Summary Tools (Epic 008)
"""

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, field_validator

from testio_mcp.exceptions import ProductNotFoundException, TestIOAPIError
from testio_mcp.server import mcp
from testio_mcp.services.product_service import ProductService
from testio_mcp.utilities import get_service_context
from testio_mcp.utilities.schema_utils import inline_schema_refs
from testio_mcp.validators import coerce_to_int


class GetProductSummaryInput(BaseModel):
    """Input validation for get_product_summary tool.

    Accepts product_id as int or string, coerces to int for validation.
    """

    product_id: int = Field(
        gt=0,
        description="Product ID from TestIO (e.g., 598). Use list_products to find IDs.",
    )

    @field_validator("product_id", mode="before")
    @classmethod
    def coerce_product_id(cls, v: Any) -> int:
        """Coerce product_id from string to int if needed."""
        return coerce_to_int(v)


class ProductSummaryOutput(BaseModel):
    """Product summary with metadata and computed counts.

    This is the output model for the get_product_summary tool,
    providing product metadata and aggregated statistics.

    STORY-083: Removed bug_count (use get_product_quality_report instead).
    """

    id: int = Field(description="Product ID (integer from API)", examples=[598])
    title: str = Field(description="Product title/name", examples=["Canva"])
    type: str = Field(
        description="Product type (website, mobile_app_ios, etc.)",
        examples=["website"],
    )
    description: str | None = Field(
        default=None,
        description="Product description",
    )
    test_count: int = Field(
        description="Total number of tests for this product",
        ge=0,
        examples=[216],
    )
    feature_count: int = Field(
        description="Total number of features for this product",
        ge=0,
        examples=[45],
    )
    last_synced: str | None = Field(
        default=None,
        description="Timestamp when product data was last synced",
        examples=["2025-11-28T10:30:00Z"],
    )
    data_as_of: str = Field(
        description="Timestamp when this summary was generated",
        examples=["2025-11-28T10:30:05Z"],
    )


@mcp.tool(output_schema=inline_schema_refs(ProductSummaryOutput.model_json_schema()))
async def get_product_summary(
    product_id: Annotated[
        int,
        Field(
            gt=0,
            description="Product ID from TestIO (e.g., 598). Use list_products to find IDs.",
        ),
    ],
    ctx: Context,
) -> dict[str, Any]:
    """Get a summary of a product including metadata and computed counts.

    Returns product metadata (id, title, type, description) along with computed counts:
    - test_count: Total tests for this product
    - feature_count: Total features

    Uses SQLite cache (no API calls). Excludes recent activity to prevent context bloat.

    Note: Bug counts not included. For bug analysis, use:
    - get_product_quality_report (with date/severity filters)
    - query_metrics (for aggregated bug metrics with dimensions)
    """
    # Validate and coerce input (accepts string or int)
    try:
        validated_input = GetProductSummaryInput(product_id=product_id)
        product_id = validated_input.product_id
    except ValueError as e:
        raise ToolError(
            f"❌ Invalid product_id: {e}\n"
            f"ℹ️  product_id must be a positive integer\n"
            f"💡 Use an integer like 598, not a string like '598.5'"
        ) from e

    # Create service with managed AsyncSession lifecycle
    async with get_service_context(ctx, ProductService) as service:
        # Delegate to service and convert exceptions to MCP error format
        try:
            result = await service.get_product_summary(product_id)

            # Validate output with Pydantic
            validated = ProductSummaryOutput(**result)
            return validated.model_dump(by_alias=True, exclude_none=True)

        except ProductNotFoundException:
            # Convert domain exception to ToolError with user-friendly message
            raise ToolError(
                f"❌ Product ID '{product_id}' not found\n"
                f"ℹ️  The product may not exist or you may not have access to it\n"
                f"💡 Use list_products to see available products"
            ) from None

        except TestIOAPIError as e:
            # Convert API error to ToolError with user-friendly message
            raise ToolError(
                f"❌ API error: {e.message}\n"
                f"ℹ️  HTTP status code: {e.status_code}\n"
                f"💡 Check API status and try again. If the problem persists, contact support."
            ) from e

        except Exception as e:
            # Catch-all for unexpected errors
            raise ToolError(
                f"❌ Unexpected error: {str(e)}\n"
                f"ℹ️  An unexpected error occurred while fetching product summary\n"
                f"💡 Please try again or contact support if the problem persists"
            ) from e
