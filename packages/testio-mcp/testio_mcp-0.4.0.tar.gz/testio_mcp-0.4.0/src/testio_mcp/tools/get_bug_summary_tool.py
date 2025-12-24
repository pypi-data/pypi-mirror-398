"""MCP tool for getting bug summary.

This module implements the get_bug_summary tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Validates input with Pydantic
2. Extracts dependencies from server context (ADR-007)
3. Delegates to BugService
4. Converts exceptions to user-friendly error format

STORY-085: Add get_bug_summary Tool (Epic 014)
"""

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, field_validator

from testio_mcp.exceptions import BugNotFoundException, TestIOAPIError
from testio_mcp.server import mcp
from testio_mcp.services.bug_service import BugService
from testio_mcp.utilities import get_service_context
from testio_mcp.utilities.schema_utils import inline_schema_refs
from testio_mcp.validators import coerce_to_int


class GetBugSummaryInput(BaseModel):
    """Input validation for get_bug_summary tool.

    Accepts bug_id as int or string, coerces to int for validation.
    """

    bug_id: int = Field(
        gt=0,
        description="Bug ID from TestIO (e.g., 12345). Use list_bugs to find IDs.",
    )

    @field_validator("bug_id", mode="before")
    @classmethod
    def coerce_bug_id(cls, v: Any) -> int:
        """Coerce bug_id from string to int if needed."""
        return coerce_to_int(v)


# Nested models for related entities (AC2)
class UserInfo(BaseModel):
    """Nested model for user information."""

    id: int = Field(description="User ID", examples=[123])
    username: str = Field(description="Username", examples=["john_doe"])


class TestInfo(BaseModel):
    """Nested model for test information."""

    id: int = Field(description="Test ID", examples=[109363])
    title: str = Field(description="Test title", examples=["Homepage Navigation Test"])


class FeatureInfo(BaseModel):
    """Nested model for feature information."""

    id: int = Field(description="Feature ID", examples=[456])
    title: str = Field(description="Feature title", examples=["User Login"])


class BugSummaryOutput(BaseModel):
    """Bug summary with full details, related entities, and metadata.

    This is the output model for the get_bug_summary tool.
    Returns comprehensive bug information per AC1-3.
    """

    # Core fields (AC1)
    id: int = Field(description="Bug ID", examples=[12345])
    title: str = Field(description="Bug title/summary", examples=["Login button not clickable"])
    severity: str | None = Field(
        default=None,
        description="Bug severity level (critical, high, medium, low)",
        examples=["critical"],
    )
    status: str | None = Field(
        default=None,
        description="Bug status (rejected, accepted, forwarded, auto_accepted)",
        examples=["rejected"],
    )
    known: bool = Field(
        default=False,
        description="Whether this is a known issue",
        examples=[False],
    )

    # Detail fields (AC1)
    actual_result: str | None = Field(
        default=None,
        description="Actual result observed",
        examples=["Button does not respond to clicks"],
    )
    expected_result: str | None = Field(
        default=None,
        description="Expected result",
        examples=["Button should navigate to dashboard"],
    )
    steps: str | None = Field(
        default=None,
        description="Reproduction steps",
        examples=["1. Navigate to login page\n2. Click login button"],
    )

    # Rejection field (AC1)
    rejection_reason: str | None = Field(
        default=None,
        description="Reason for rejection (if status is rejected)",
        examples=["test_is_invalid"],
    )

    # Related entities (AC2)
    reported_by_user: UserInfo | None = Field(
        default=None,
        description="Tester who reported this bug",
    )
    test: TestInfo = Field(
        description="Parent test containing this bug",
    )
    feature: FeatureInfo | None = Field(
        default=None,
        description="Feature being tested (if linked)",
    )

    # Metadata (AC3)
    reported_at: str | None = Field(
        default=None,
        description="When bug was reported (ISO 8601)",
        examples=["2025-11-28T10:30:00Z"],
    )
    data_as_of: str = Field(
        description="Timestamp when this summary was generated (ISO 8601)",
        examples=["2025-11-28T10:30:05Z"],
    )


@mcp.tool(output_schema=inline_schema_refs(BugSummaryOutput.model_json_schema()))
async def get_bug_summary(
    bug_id: Annotated[
        int,
        Field(
            gt=0,
            description="Bug ID from TestIO (e.g., 12345). Use list_bugs to find IDs.",
        ),
    ],
    ctx: Context,
) -> dict[str, Any]:
    """Get a summary of a bug including full details, related entities, and metadata.

    Returns comprehensive bug information with core fields (id, title, severity, status, known),
    detail fields (actual_result, expected_result, steps), rejection field (rejection_reason
    if rejected), attribution (reported_by_user, test, feature), and metadata (reported_at,
    data_as_of).

    Use for drilling into specific bugs to understand rejection reasons, reporter details,
    and complete reproduction steps.
    """
    # Validate and coerce input (accepts string or int)
    try:
        validated_input = GetBugSummaryInput(bug_id=bug_id)
        bug_id = validated_input.bug_id
    except ValueError as e:
        raise ToolError(
            f"❌ Invalid bug_id: {e}\n"
            f"ℹ️  bug_id must be a positive integer\n"
            f"💡 Use an integer like 12345, not a string like '12345.5'"
        ) from e

    # Create service with managed AsyncSession lifecycle (STORY-033)
    async with get_service_context(ctx, BugService) as service:
        # Delegate to service and convert exceptions to MCP error format
        try:
            result = await service.get_bug_summary(bug_id)

            # Validate output with Pydantic
            validated = BugSummaryOutput(**result)
            return validated.model_dump(by_alias=True, exclude_none=True)

        except BugNotFoundException:
            # Convert domain exception to ToolError with user-friendly message (AC4)
            raise ToolError(
                f"❌ Bug ID '{bug_id}' not found\n"
                f"ℹ️  The bug may have been deleted or not yet synced\n"
                f"💡 Use list_bugs to find available bugs"
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
                f"ℹ️  An unexpected error occurred while fetching bug summary\n"
                f"💡 Please try again or contact support if the problem persists"
            ) from e
