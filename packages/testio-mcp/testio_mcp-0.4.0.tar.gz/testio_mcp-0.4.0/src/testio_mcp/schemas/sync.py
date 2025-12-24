"""Output schemas for sync-related MCP tools.

This module defines Pydantic models for sync operations following the
schema optimization principles from STORY-051 AC7:
- Structured models for schema richness (Union types, nested models)
- Concise Field descriptions (1 sentence, no filler words)
- Input examples in Field definitions (teaches Claude parameter conventions)
- Usage examples in docstring (not json_schema_extra)

Target: ~550-600 tokens per tool schema (NOT the aggressive 500 from initial spec).
"""

from pydantic import BaseModel, Field


class SyncDataOutput(BaseModel):
    """Response from sync_data tool with stats and diagnostics.

    Examples:
        Incremental sync (since=None, default):
        {
            "status": "completed",
            "products_synced": 1,
            "features_refreshed": 10,
            "tests_discovered": 5,
            "tests_updated": 0,
            "duration_seconds": 2.3
        }

        Date range sync (since="7 days ago"):
        {
            "status": "completed",
            "products_synced": 1,
            "features_refreshed": 10,
            "tests_discovered": 3,
            "tests_updated": 12,
            "duration_seconds": 8.5
        }

        Full resync (since="all"):
        {
            "status": "completed_with_warnings",
            "products_synced": 3,
            "features_refreshed": 42,
            "tests_discovered": 0,
            "tests_updated": 127,
            "duration_seconds": 45.2,
            "warnings": ["Product 999 not found - skipped"]
        }
    """

    status: str = Field(
        description='Sync completion status: "completed" or "completed_with_warnings"'
    )
    products_synced: int = Field(description="Number of products synchronized")
    features_refreshed: int = Field(description="Number of features refreshed")
    tests_discovered: int = Field(description="Number of new tests discovered")
    tests_updated: int = Field(description="Number of existing tests updated")
    duration_seconds: float = Field(description="Total sync duration in seconds (always populated)")
    warnings: list[str] | None = Field(
        default=None, description="Non-fatal issues encountered (if any)"
    )
