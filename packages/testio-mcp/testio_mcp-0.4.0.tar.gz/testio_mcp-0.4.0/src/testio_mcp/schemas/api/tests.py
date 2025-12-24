"""Test-related API response schemas.

Contains schemas for test information used in API responses.
These use semantic field names (test_id, product_id) for external APIs.
Models are shared between MCP tools and REST endpoints to ensure consistency.
"""

from typing import Any

from pydantic import BaseModel, Field

from testio_mcp.schemas.api.bugs import BugSummary
from testio_mcp.schemas.api.features import FeatureInfo
from testio_mcp.schemas.api.products import ProductInfo, ProductInfoSummary
from testio_mcp.schemas.api.shared import PaginationInfo, PlatformRequirement


class TestSummary(BaseModel):
    """Summary information for a single test.

    Attributes:
        test_id: Unique test identifier (integer from API)
        title: Test title/name
        goal: Test goal/objective (optional)
        status: Current test status
        review_status: Review status (optional)
        testing_type: Type of testing (rapid, focused, coverage, usability)
        duration: Test duration in minutes (optional)
        starts_at: Test start timestamp (optional)
        ends_at: Test end timestamp (optional)
        test_environment: Test environment configuration (optional, STORY-072)
    """

    __test__ = False

    test_id: int = Field(description="Test ID (integer from API)")
    title: str = Field(description="Test title")
    goal: str | None = Field(default=None, description="Test goal/objective")
    status: str = Field(description="Test status (running, locked, archived, etc.)")
    review_status: str | None = Field(default=None, description="Review status (if applicable)")
    testing_type: str = Field(description="Testing type: rapid, focused, coverage, or usability")
    duration: int | None = Field(default=None, description="Test duration in minutes")
    starts_at: str | None = Field(default=None, description="Test start timestamp")
    ends_at: str | None = Field(default=None, description="Test end timestamp")
    test_environment: dict[str, Any] | None = Field(
        default=None, description="Test environment configuration (STORY-072)"
    )


class ListTestsOutput(BaseModel):
    """Complete output for list_tests tool.

    This is the primary output model combining product info with
    filtered test summaries and pagination metadata.
    """

    product: ProductInfoSummary = Field(description="Product information for context")
    statuses_filter: list[str] = Field(description="Statuses that were used to filter tests")
    pagination: PaginationInfo = Field(description="Pagination metadata")
    total_tests: int = Field(description="Total number of tests returned in current page", ge=0)
    tests: list[TestSummary] = Field(description="List of test summaries")


class TestDetails(BaseModel):
    """Detailed information about an exploratory test."""

    __test__ = False

    id: int = Field(description="Test ID (integer from API)")
    title: str = Field(description="Test title")
    goal: str | None = Field(default=None, description="Test goal/objective")
    instructions: str | None = Field(default=None, description="Test instructions (STORY-057)")
    out_of_scope: str | None = Field(default=None, description="Out of scope details (STORY-057)")
    testing_type: str = Field(
        description="Testing type: rapid, focused, coverage, usability, or custom",
    )
    duration: int | None = Field(default=None, description="Test duration in minutes")
    status: str = Field(
        description="Test status: locked, archived, running, review, etc.",
    )
    review_status: str | None = Field(
        default=None,
        description="Review status: review_successful, review_failed, etc.",
    )
    requirements_summary: list[PlatformRequirement] | None = Field(
        default=None,
        description="Summarized requirements with platform-browser relationships",
    )
    enable_low: bool = Field(default=False, description="Enable low severity bugs (STORY-057)")
    enable_high: bool = Field(default=False, description="Enable high severity bugs (STORY-057)")
    enable_critical: bool = Field(
        default=False, description="Enable critical severity bugs (STORY-057)"
    )
    starts_at: str | None = Field(default=None, description="Start timestamp")
    ends_at: str | None = Field(default=None, description="End timestamp")
    test_environment: dict[str, Any] | None = Field(
        default=None, description="Test environment configuration (STORY-072)"
    )
    product: ProductInfo = Field(description="Associated product information")
    feature: FeatureInfo | None = Field(
        default=None,
        description="Associated feature information (if applicable)",
    )


class TestStatusOutput(BaseModel):
    """Complete test status with configuration and bug summary.

    This is the primary output model for the get_test_summary tool,
    combining test configuration details with aggregated bug statistics.
    """

    test: TestDetails = Field(description="Detailed test configuration and status")
    bugs: BugSummary = Field(description="Aggregated bug summary statistics")
