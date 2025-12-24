"""MCP tool for getting test summary.

This module implements the get_test_summary tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Validates input with Pydantic
2. Extracts dependencies from server context (ADR-007)
3. Delegates to TestService
4. Converts exceptions to user-friendly error format
"""

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, field_validator

from testio_mcp.exceptions import TestIOAPIError, TestNotFoundException
from testio_mcp.schemas.api import TestStatusOutput
from testio_mcp.server import mcp
from testio_mcp.services.test_service import TestService
from testio_mcp.utilities import get_service_context
from testio_mcp.utilities.schema_utils import inline_schema_refs
from testio_mcp.validators import coerce_to_int

# Pydantic Models (AC2-5)
# NOTE: Schemas imported from testio_mcp.schemas.api for DRY principle.
# Schemas are post-processed with inline_schema_refs() to avoid $ref resolution issues
# in some MCP clients like Gemini CLI 0.16.0.


class GetTestStatusInput(BaseModel):
    """Input validation for get_test_summary tool.

    Accepts test_id as int or string, coerces to int for validation.
    """

    test_id: int = Field(
        gt=0,
        description="Test ID from TestIO (e.g., 109363). Use list_tests to find IDs.",
    )

    @field_validator("test_id", mode="before")
    @classmethod
    def coerce_test_id(cls, v: Any) -> int:
        """Coerce test_id from string to int if needed."""
        return coerce_to_int(v)


# MCP Tool (AC1)


@mcp.tool(output_schema=inline_schema_refs(TestStatusOutput.model_json_schema()))
async def get_test_summary(
    test_id: Annotated[
        int,
        Field(
            gt=0,
            description="Test ID from TestIO (e.g., 109363). Use list_tests to find IDs.",
        ),
    ],
    ctx: Context,
) -> dict[str, Any]:
    """Get a summary of a test including status, configuration, and bug statistics.

    Returns detailed test configuration, bug severity/platform breakdown, and recent bugs.
    Use for drilling into specific tests. For quality trends across multiple tests,
    use get_product_quality_report.
    """
    # Validate and coerce input (accepts string or int)
    try:
        validated_input = GetTestStatusInput(test_id=test_id)
        test_id = validated_input.test_id
    except ValueError as e:
        raise ToolError(
            f"❌ Invalid test_id: {e}\n"
            f"ℹ️  test_id must be a positive integer\n"
            f"💡 Use an integer like 1216, not a string like '1216.5'"
        ) from e

    # Create service with managed AsyncSession lifecycle (STORY-033)
    async with get_service_context(ctx, TestService) as service:
        # Delegate to service and convert exceptions to MCP error format
        try:
            result = await service.get_test_summary(test_id)

            # Validate output with Pydantic (optional but recommended)
            # This ensures API response matches expected structure
            validated = TestStatusOutput(**result)
            # Note: Do NOT use exclude_none=True here because acceptance_rates
            # has semantically meaningful None values (STORY-081: None means "no bugs",
            # which is different from "field not present"). exclude_none=True would
            # strip out the rate fields, leaving only {open_count, has_alert}.
            return validated.model_dump(by_alias=True)

        except TestNotFoundException:
            # Convert domain exception to ToolError with user-friendly message
            raise ToolError(
                f"❌ Test ID '{test_id}' not found\n"
                f"ℹ️  The test may have been deleted, archived, or you may not have access to it\n"
                f"💡 Verify the test ID is correct and the test still exists"
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
                f"ℹ️  An unexpected error occurred while fetching test status\n"
                f"💡 Please try again or contact support if the problem persists"
            ) from e
