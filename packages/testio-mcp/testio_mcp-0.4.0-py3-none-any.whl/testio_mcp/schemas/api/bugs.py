"""Bug-related API response schemas.

Contains schemas for bug summary statistics used in API responses.
These use semantic field names for external APIs.
"""

from pydantic import BaseModel, Field

from testio_mcp.schemas.api.shared import PaginationInfo


class RecentBug(BaseModel):
    """Recent bug preview with essential fields.

    Used in BugSummary.recent_bugs to show the 3 most recent bugs
    with minimal context for quick reference.
    """

    id: str = Field(description="Bug ID (string for display)")
    title: str = Field(description="Bug title")
    severity: str = Field(description="Bug severity: critical, high, low, visual, content, custom")
    status: str = Field(description="Bug status: active_accepted, auto_accepted, rejected, open")
    created_at: str | None = Field(default=None, description="Bug creation timestamp (ISO 8601)")
    known: bool = Field(
        default=False, description="Whether bug is marked as known issue (STORY-072)"
    )


class AcceptanceRates(BaseModel):
    """Bug acceptance rate metrics.

    Quality metrics calculated from bug status distribution.
    Rates are floats between 0.0 and 1.0, or None when no bugs exist.
    """

    active_acceptance_rate: float | None = Field(
        description=(
            "Rate of actively accepted bugs (customer approved) / total bugs. "
            "None if no bugs exist."
        ),
    )
    auto_acceptance_rate: float | None = Field(
        default=None,
        description=("Rate of auto-accepted bugs / total accepted bugs. None if no accepted bugs."),
    )
    overall_acceptance_rate: float | None = Field(
        description=(
            "Rate of all accepted bugs (active + auto) / total bugs. None if no bugs exist."
        ),
    )
    rejection_rate: float | None = Field(
        description=("Rate of rejected bugs / total bugs. None if no bugs exist."),
    )
    review_rate: float | None = Field(
        description=(
            "Rate of human-reviewed bugs (active_accepted + rejected) / total bugs. "
            "None if no bugs exist."
        ),
    )
    open_count: int = Field(
        description="Count of open bugs awaiting review",
        ge=0,
    )
    has_alert: bool = Field(
        description="Whether auto-acceptance rate exceeds alert threshold (>30%)",
    )


class BugSummary(BaseModel):
    """Bug summary statistics for a test.

    Attributes:
        total_count: Total number of bugs found in test
        known_bugs_count: Count of bugs marked as known issues (STORY-072)
        by_severity: Bug count grouped by severity level
        by_status: Bug count grouped by bug status
        by_platform: Bug distribution across platforms (OS, browser, device type)
        acceptance_rates: Quality metrics (acceptance rates, alerts) or None if no bugs
        recent_bugs: List of 3 most recent bugs with basic info
    """

    total_count: int = Field(
        description="Total number of bugs found in test",
        ge=0,
        examples=[42],
    )
    known_bugs_count: int = Field(
        default=0,
        description="Count of bugs marked as known issues (STORY-072)",
        ge=0,
    )
    by_severity: dict[str, int] = Field(
        description="Bug count grouped by severity (critical, high, low, visual, content)",
        examples=[{"critical": 5, "high": 12, "low": 18, "visual": 4, "content": 3}],
    )
    by_status: dict[str, int] = Field(
        description=(
            "Bug count grouped by status: active_accepted (customer approved), "
            "auto_accepted (auto-approved after 10 days), total_accepted (active + auto), "
            "rejected, open (forwarded/awaiting review)"
        ),
        examples=[
            {
                "active_accepted": 28,
                "auto_accepted": 5,
                "total_accepted": 33,
                "rejected": 7,
                "open": 2,
            }
        ],
    )
    by_platform: dict[str, dict[str, int]] = Field(
        description="Platform breakdown: operating_systems, browsers, device_categories",
        examples=[
            {
                "operating_systems": {"Windows": 15, "macOS": 12, "iOS": 10, "Android": 5},
                "browsers": {"Chrome": 20, "Safari": 15, "Firefox": 7},
                "device_categories": {"Desktop": 27, "Mobile": 15},
            }
        ],
    )
    acceptance_rates: AcceptanceRates = Field(
        description=(
            "Quality metrics: active/auto/overall acceptance rates, rejection rate, alerts. "
            "Always present (STORY-081), but individual rate fields may be None when no bugs exist."
        ),
    )
    recent_bugs: list[RecentBug] = Field(
        default_factory=list,
        description="3 most recent bugs with id, title, severity, status",
        max_length=3,
    )


class BugListItem(BaseModel):
    """Minimal bug representation for list_bugs tool output.

    Contains only essential fields for quick scanning and filtering.
    Used in ListBugsOutput.bugs list.
    """

    id: str = Field(description="Bug ID")
    title: str = Field(description="Bug title/summary")
    severity: str | None = Field(default=None, description="Bug severity level")
    status: str | None = Field(
        default=None, description="Bug status (accepted, rejected, forwarded, etc.)"
    )
    test_id: int = Field(description="Test ID this bug belongs to")
    reported_at: str | None = Field(
        default=None, description="Timestamp when bug was reported (ISO 8601)"
    )


class ListBugsOutput(BaseModel):
    """Output schema for list_bugs tool.

    Returns a list of bugs for specified tests with pagination and filter transparency.
    """

    bugs: list[BugListItem] = Field(description="List of bugs matching the query")
    pagination: PaginationInfo = Field(
        description="Pagination metadata (page, per_page, offset, total_count, has_more)"
    )
    filters_applied: dict[str, object] = Field(description="Filters that were applied to the query")
    warnings: list[str] | None = Field(
        default=None,
        description="Warning messages (e.g., tests not found, stale data refreshed, no bugs found)",
    )
