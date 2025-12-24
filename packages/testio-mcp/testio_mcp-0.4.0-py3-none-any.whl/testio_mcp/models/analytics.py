"""Pydantic models for analytics responses.

These models provide type-safe data structures for analytics query results.

STORY-043: Analytics Service (The Engine)
Epic: EPIC-007 (Generic Analytics Framework)
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Chart types supported by the visualization hint system
ChartType = Literal[
    "line",  # Single-series time trend
    "multi_line",  # Multiple series (time + breakdown by category/entity)
    "pie",  # Distribution (≤7 categories, single metric)
    "horizontal_bar",  # Ranked comparison
    "stacked_bar",  # Entity/category + categorical breakdown
    "grouped_bar",  # Side-by-side comparison
    "table",  # Fallback for complex/large data
]

# Confidence levels for visualization recommendations
ConfidenceLevel = Literal["high", "medium", "low"]


class VisualizationHint(BaseModel):
    """Hint for frontend chart rendering.

    Provides intelligent chart type recommendations based on:
    - Dimension types (time, categorical, entity)
    - Row/series count (too many → table fallback)
    - Metric compatibility (mixed types → dual axis or table)

    Attributes:
        chart_type: Recommended chart type for rendering
        x_axis: Primary dimension for x-axis (None for pie charts)
        y_axis: Primary metrics (counts) for y-axis
        y_axis_secondary: Rate metrics for secondary y-axis (dual-axis scenarios)
        series_by: Secondary dimension for color/stacking
        included_series: Which series are shown (for top-N scenarios)
        dropped_series_count: How many series were dropped
        rationale: Human-readable explanation of the recommendation
        confidence: Confidence level in the recommendation
        alternatives: Alternative chart types that could work
        metric_types: Map of metric names to their types (count/rate)
    """

    chart_type: ChartType = Field(..., description="Recommended chart type")

    # Axis mapping
    x_axis: str | None = Field(default=None, description="Primary dimension for x-axis")
    y_axis: list[str] = Field(default_factory=list, description="Primary metrics (counts)")
    y_axis_secondary: list[str] = Field(
        default_factory=list, description="Rate metrics for secondary y-axis"
    )
    series_by: str | None = Field(
        default=None, description="Secondary dimension for color/stacking"
    )

    # For top-N scenarios
    included_series: list[str] | None = Field(
        default=None, description="Series included in chart (for top-N)"
    )
    dropped_series_count: int = Field(
        default=0, ge=0, description="Number of series dropped from chart"
    )

    # Decision transparency
    rationale: str = Field(..., description="Explanation of the recommendation")
    confidence: ConfidenceLevel = Field(
        default="high", description="Confidence in the recommendation"
    )
    alternatives: list[str] = Field(default_factory=list, description="Alternative chart types")

    # Metric type info for dual-axis rendering
    metric_types: dict[str, str] = Field(
        default_factory=dict,
        description="Map of metric names to types (count/rate)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chart_type": "line",
                "x_axis": "month",
                "y_axis": ["bug_count", "test_count"],
                "y_axis_secondary": [],
                "series_by": None,
                "rationale": "Time dimension detected; line chart shows trend over time",
                "confidence": "high",
                "alternatives": ["table"],
                "metric_types": {"bug_count": "count", "test_count": "count"},
            }
        }
    )


class QueryMetadata(BaseModel):
    """Metadata about an analytics query execution.

    Attributes:
        total_rows: Number of rows returned in the result set
        dimensions_used: List of dimension keys used for grouping
        metrics_used: List of metric keys measured
        query_time_ms: Query execution time in milliseconds
    """

    total_rows: int = Field(..., ge=0, description="Number of rows in result set")
    dimensions_used: list[str] = Field(..., description="Dimension keys used for grouping")
    metrics_used: list[str] = Field(..., description="Metric keys measured")
    query_time_ms: int = Field(..., ge=0, description="Query execution time in milliseconds")


class QueryResponse(BaseModel):
    """Response structure for analytics queries.

    Contains query results with rich metadata and human-readable explanation.

    Attributes:
        data: Query result rows (structure varies by dimensions/metrics)
        metadata: Query execution metadata
        query_explanation: Human-readable description of what was queried
        warnings: List of warnings or caveats about the results
        visualization_hint: Recommended chart type and configuration for rendering
    """

    data: list[dict[str, Any]] = Field(..., description="Query result rows with dynamic schema")
    metadata: QueryMetadata = Field(..., description="Query execution metadata")
    query_explanation: str = Field(..., description="Human-readable query description")
    warnings: list[str] = Field(default_factory=list, description="Result caveats")
    visualization_hint: VisualizationHint | None = Field(
        default=None,
        description="Recommended chart type and axis configuration for rendering",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [
                    {"feature_id": 1, "feature": "Login", "bug_count": 10},
                    {"feature_id": 2, "feature": "Dashboard", "bug_count": 5},
                ],
                "metadata": {
                    "total_rows": 2,
                    "dimensions_used": ["feature"],
                    "metrics_used": ["bug_count"],
                    "query_time_ms": 45,
                },
                "query_explanation": (
                    "Showing Total number of bugs found grouped by "
                    "Group by Feature Title, sorted by bug_count descending"
                ),
                "warnings": [],
                "visualization_hint": {
                    "chart_type": "horizontal_bar",
                    "x_axis": "feature",
                    "y_axis": ["bug_count"],
                    "rationale": "Entity dimension with ≤15 rows; horizontal bar",
                    "confidence": "high",
                    "metric_types": {"bug_count": "count"},
                },
            }
        }
    )
