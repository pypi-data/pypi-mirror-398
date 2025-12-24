"""Shared schemas used across multiple API endpoints.

Contains common utility schemas like pagination metadata and platform requirements
that are reused by multiple domain entities (tests, features, users, etc.).
"""

from pydantic import BaseModel, Field


class PaginationInfo(BaseModel):
    """Pagination metadata for paginated responses."""

    page: int = Field(description="Current page number (1-indexed)", ge=1)
    per_page: int = Field(description="Number of items per page", ge=1)
    offset: int = Field(description="Starting offset for results (0-indexed)", ge=0)
    start_index: int = Field(
        description="Index of first item in current page (0-indexed, equals offset)", ge=0
    )
    end_index: int = Field(
        description="Index of last item in current page (0-indexed, equals offset+count-1)",
        ge=-1,  # -1 when no results
    )
    total_count: int = Field(
        description="Total number of results matching the query (across all pages)", ge=0
    )
    has_more: bool = Field(description="Whether more results may be available (heuristic)")


class PlatformRequirement(BaseModel):
    """Platform requirement with OS version and allowed browsers."""

    platform: str = Field(
        description=(
            "OS platform with version and device type "
            "(e.g., 'Windows 11 (Computers)', 'iOS 17.0+ (Smartphones)')"
        )
    )
    browsers: list[str] = Field(
        description=("Allowed browsers for this platform (e.g., ['Chrome', 'Firefox', 'Safari'])")
    )
