"""Unit tests for visualization hint logic.

Tests the _determine_visualization_hint method in AnalyticsService
to verify correct chart type recommendations based on the decision matrix.
"""

from testio_mcp.schemas.visualization_constants import (
    BAR_MAX_ROWS,
    MULTI_LINE_MAX_SERIES,
    PIE_MAX_CATEGORIES,
)
from testio_mcp.services.analytics_service import AnalyticsService


class TestVisualizationHintHelpers:
    """Test helper methods for visualization hints."""

    def test_classify_dimension_time(self) -> None:
        """Time dimensions are correctly classified."""
        # Create minimal service (no DB needed for classification)
        service = AnalyticsService.__new__(AnalyticsService)

        assert service._classify_dimension("month") == "time"
        assert service._classify_dimension("week") == "time"
        assert service._classify_dimension("quarter") == "time"
        assert service._classify_dimension("day") == "time"
        assert service._classify_dimension("date") == "time"
        assert service._classify_dimension("year") == "time"

    def test_classify_dimension_categorical(self) -> None:
        """Categorical dimensions are correctly classified."""
        service = AnalyticsService.__new__(AnalyticsService)

        assert service._classify_dimension("severity") == "categorical"
        assert service._classify_dimension("status") == "categorical"
        assert service._classify_dimension("testing_type") == "categorical"
        assert service._classify_dimension("rejection_reason") == "categorical"
        assert service._classify_dimension("known_bug") == "categorical"

    def test_classify_dimension_entity(self) -> None:
        """Entity dimensions are correctly classified."""
        service = AnalyticsService.__new__(AnalyticsService)

        assert service._classify_dimension("feature") == "entity"
        assert service._classify_dimension("tester") == "entity"
        assert service._classify_dimension("customer") == "entity"
        assert service._classify_dimension("product") == "entity"
        assert service._classify_dimension("platform") == "entity"
        assert service._classify_dimension("test_environment") == "entity"

    def test_classify_dimension_unknown_defaults_to_entity(self) -> None:
        """Unknown dimensions default to entity for safety."""
        service = AnalyticsService.__new__(AnalyticsService)

        assert service._classify_dimension("unknown_dim") == "entity"

    def test_classify_metrics_count(self) -> None:
        """Count metrics are correctly classified."""
        service = AnalyticsService.__new__(AnalyticsService)

        result = service._classify_metrics(["bug_count", "test_count", "features_tested"])
        assert result["bug_count"] == "count"
        assert result["test_count"] == "count"
        assert result["features_tested"] == "count"

    def test_classify_metrics_rate(self) -> None:
        """Rate metrics are correctly classified."""
        service = AnalyticsService.__new__(AnalyticsService)

        result = service._classify_metrics(
            ["rejection_rate", "overall_acceptance_rate", "bugs_per_test"]
        )
        assert result["rejection_rate"] == "rate"
        assert result["overall_acceptance_rate"] == "rate"
        assert result["bugs_per_test"] == "rate"

    def test_classify_metrics_mixed(self) -> None:
        """Mixed metrics are correctly classified."""
        service = AnalyticsService.__new__(AnalyticsService)

        result = service._classify_metrics(["bug_count", "rejection_rate"])
        assert result["bug_count"] == "count"
        assert result["rejection_rate"] == "rate"

    def test_classify_metrics_unknown_defaults_to_count(self) -> None:
        """Unknown metrics default to count for safety."""
        service = AnalyticsService.__new__(AnalyticsService)

        result = service._classify_metrics(["unknown_metric"])
        assert result["unknown_metric"] == "count"


class TestVisualizationHintEmptyData:
    """Test visualization hints for empty result sets."""

    def test_empty_data_returns_table_with_low_confidence(self) -> None:
        """Empty results return table with low confidence."""
        service = AnalyticsService.__new__(AnalyticsService)

        hint = service._determine_visualization_hint(
            data=[],
            dimensions=["month"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "table"
        assert hint.confidence == "low"
        assert "No data" in hint.rationale


class TestVisualizationHintSingleDimension:
    """Test visualization hints for single dimension queries."""

    def test_time_dimension_returns_line(self) -> None:
        """Time dimension with any row count returns line chart."""
        service = AnalyticsService.__new__(AnalyticsService)

        data = [{"month": "2024-01", "bug_count": 10} for _ in range(12)]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["month"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "line"
        assert hint.x_axis == "month"
        assert hint.y_axis == ["bug_count"]
        assert hint.confidence == "high"

    def test_time_dimension_with_mixed_metrics_uses_dual_axis(self) -> None:
        """Time dimension with mixed metrics splits into primary/secondary axes."""
        service = AnalyticsService.__new__(AnalyticsService)

        data = [{"month": "2024-01", "bug_count": 10, "rejection_rate": 0.15} for _ in range(6)]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["month"],
            metrics=["bug_count", "rejection_rate"],
        )

        assert hint.chart_type == "line"
        assert hint.y_axis == ["bug_count"]
        assert hint.y_axis_secondary == ["rejection_rate"]
        assert hint.metric_types["bug_count"] == "count"
        assert hint.metric_types["rejection_rate"] == "rate"

    def test_categorical_dimension_small_single_metric_returns_pie(self) -> None:
        """Categorical dimension with ≤7 categories and 1 metric returns pie."""
        service = AnalyticsService.__new__(AnalyticsService)

        data = [
            {"severity": "critical", "bug_count": 5},
            {"severity": "high", "bug_count": 10},
            {"severity": "low", "bug_count": 20},
        ]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["severity"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "pie"
        assert hint.x_axis == "severity"
        assert len(hint.y_axis) == 1
        assert "pie" in hint.rationale.lower() or "distribution" in hint.rationale.lower()

    def test_categorical_dimension_multiple_metrics_returns_bar(self) -> None:
        """Categorical dimension with multiple metrics returns horizontal bar."""
        service = AnalyticsService.__new__(AnalyticsService)

        data = [
            {"severity": "critical", "bug_count": 5, "test_count": 2},
            {"severity": "high", "bug_count": 10, "test_count": 5},
        ]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["severity"],
            metrics=["bug_count", "test_count"],
        )

        assert hint.chart_type == "horizontal_bar"
        assert hint.x_axis == "severity"

    def test_categorical_dimension_many_categories_returns_bar(self) -> None:
        """Categorical dimension with >7 categories returns horizontal bar."""
        service = AnalyticsService.__new__(AnalyticsService)

        # Create more than PIE_MAX_CATEGORIES rows
        data = [{"status": f"status_{i}", "bug_count": i} for i in range(10)]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["status"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "horizontal_bar"

    def test_entity_dimension_small_returns_bar(self) -> None:
        """Entity dimension with ≤15 rows returns horizontal bar."""
        service = AnalyticsService.__new__(AnalyticsService)

        data = [{"feature": f"Feature {i}", "bug_count": i} for i in range(10)]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["feature"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "horizontal_bar"
        assert hint.x_axis == "feature"
        assert hint.confidence == "high"

    def test_entity_dimension_large_returns_table(self) -> None:
        """Entity dimension with >15 rows returns table."""
        service = AnalyticsService.__new__(AnalyticsService)

        # Create more than BAR_MAX_ROWS
        data = [{"feature": f"Feature {i}", "bug_count": i} for i in range(20)]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["feature"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "table"
        assert "horizontal_bar" in hint.alternatives


class TestVisualizationHintTwoDimensions:
    """Test visualization hints for two dimension queries."""

    def test_time_plus_categorical_small_returns_multi_line(self) -> None:
        """Time + categorical with ≤8 series returns multi_line."""
        service = AnalyticsService.__new__(AnalyticsService)

        data = [
            {"month": "2024-01", "severity": "critical", "bug_count": 5},
            {"month": "2024-01", "severity": "high", "bug_count": 10},
            {"month": "2024-02", "severity": "critical", "bug_count": 3},
            {"month": "2024-02", "severity": "high", "bug_count": 8},
        ]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["month", "severity"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "multi_line"
        assert hint.x_axis == "month"
        assert hint.series_by == "severity"
        assert hint.included_series is not None
        assert set(hint.included_series) == {"critical", "high"}

    def test_time_plus_categorical_large_returns_table(self) -> None:
        """Time + categorical with >8 series returns table."""
        service = AnalyticsService.__new__(AnalyticsService)

        # Create more than MULTI_LINE_MAX_SERIES unique series
        data = []
        for month in ["2024-01", "2024-02"]:
            for i in range(10):  # 10 unique statuses
                data.append({"month": month, "status": f"status_{i}", "bug_count": i})

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["month", "status"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "table"
        assert hint.dropped_series_count > 0
        assert "multi_line" in hint.alternatives

    def test_categorical_plus_categorical_returns_stacked_bar(self) -> None:
        """Two categorical dimensions with small row count returns stacked bar."""
        service = AnalyticsService.__new__(AnalyticsService)

        data = [
            {"severity": "critical", "status": "open", "bug_count": 5},
            {"severity": "critical", "status": "closed", "bug_count": 3},
            {"severity": "high", "status": "open", "bug_count": 10},
            {"severity": "high", "status": "closed", "bug_count": 8},
        ]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["severity", "status"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "stacked_bar"
        assert hint.x_axis == "severity"
        assert hint.series_by == "status"

    def test_entity_plus_categorical_small_returns_stacked_bar(self) -> None:
        """Entity + categorical with small row count returns stacked bar."""
        service = AnalyticsService.__new__(AnalyticsService)

        data = [
            {"feature": "Login", "severity": "critical", "bug_count": 5},
            {"feature": "Login", "severity": "high", "bug_count": 3},
            {"feature": "Signup", "severity": "critical", "bug_count": 2},
            {"feature": "Signup", "severity": "high", "bug_count": 4},
        ]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["feature", "severity"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "stacked_bar"
        assert hint.x_axis == "feature"
        assert hint.series_by == "severity"

    def test_entity_plus_entity_always_returns_table(self) -> None:
        """Two entity dimensions always returns table."""
        service = AnalyticsService.__new__(AnalyticsService)

        data = [
            {"feature": "Login", "tester": "Alice", "bug_count": 5},
            {"feature": "Login", "tester": "Bob", "bug_count": 3},
        ]

        hint = service._determine_visualization_hint(
            data=data,
            dimensions=["feature", "tester"],
            metrics=["bug_count"],
        )

        assert hint.chart_type == "table"
        assert hint.confidence == "high"
        assert len(hint.alternatives) == 0  # No good alternatives


class TestVisualizationHintMetricTypes:
    """Test metric type handling in visualization hints."""

    def test_metric_types_always_populated(self) -> None:
        """Metric types are always included in the hint."""
        service = AnalyticsService.__new__(AnalyticsService)

        hint = service._determine_visualization_hint(
            data=[{"month": "2024-01", "bug_count": 10}],
            dimensions=["month"],
            metrics=["bug_count"],
        )

        assert "bug_count" in hint.metric_types
        assert hint.metric_types["bug_count"] == "count"

    def test_mixed_metrics_correctly_split(self) -> None:
        """Mixed metrics are correctly split between axes."""
        service = AnalyticsService.__new__(AnalyticsService)

        hint = service._determine_visualization_hint(
            data=[
                {
                    "month": "2024-01",
                    "bug_count": 10,
                    "test_count": 5,
                    "rejection_rate": 0.2,
                }
            ],
            dimensions=["month"],
            metrics=["bug_count", "test_count", "rejection_rate"],
        )

        assert "bug_count" in hint.y_axis
        assert "test_count" in hint.y_axis
        assert "rejection_rate" in hint.y_axis_secondary


class TestVisualizationHintThresholds:
    """Test that thresholds are correctly applied."""

    def test_pie_threshold_boundary(self) -> None:
        """Pie chart threshold is correctly applied at boundary."""
        service = AnalyticsService.__new__(AnalyticsService)

        # Exactly at threshold
        data_at_threshold = [
            {"severity": f"sev_{i}", "bug_count": i} for i in range(PIE_MAX_CATEGORIES)
        ]
        hint = service._determine_visualization_hint(
            data=data_at_threshold,
            dimensions=["severity"],
            metrics=["bug_count"],
        )
        assert hint.chart_type == "pie"

        # One over threshold
        data_over_threshold = [
            {"severity": f"sev_{i}", "bug_count": i} for i in range(PIE_MAX_CATEGORIES + 1)
        ]
        hint = service._determine_visualization_hint(
            data=data_over_threshold,
            dimensions=["severity"],
            metrics=["bug_count"],
        )
        assert hint.chart_type == "horizontal_bar"

    def test_bar_threshold_boundary(self) -> None:
        """Bar chart threshold is correctly applied at boundary."""
        service = AnalyticsService.__new__(AnalyticsService)

        # Exactly at threshold
        data_at_threshold = [{"feature": f"feat_{i}", "bug_count": i} for i in range(BAR_MAX_ROWS)]
        hint = service._determine_visualization_hint(
            data=data_at_threshold,
            dimensions=["feature"],
            metrics=["bug_count"],
        )
        assert hint.chart_type == "horizontal_bar"

        # One over threshold
        data_over_threshold = [
            {"feature": f"feat_{i}", "bug_count": i} for i in range(BAR_MAX_ROWS + 1)
        ]
        hint = service._determine_visualization_hint(
            data=data_over_threshold,
            dimensions=["feature"],
            metrics=["bug_count"],
        )
        assert hint.chart_type == "table"

    def test_multi_line_threshold_boundary(self) -> None:
        """Multi-line chart threshold is correctly applied at boundary."""
        service = AnalyticsService.__new__(AnalyticsService)

        # Exactly at threshold (MULTI_LINE_MAX_SERIES unique series)
        data_at_threshold = []
        for month in ["2024-01", "2024-02"]:
            for i in range(MULTI_LINE_MAX_SERIES):
                data_at_threshold.append({"month": month, "severity": f"sev_{i}", "bug_count": i})

        hint = service._determine_visualization_hint(
            data=data_at_threshold,
            dimensions=["month", "severity"],
            metrics=["bug_count"],
        )
        assert hint.chart_type == "multi_line"

        # One over threshold
        data_over_threshold = []
        for month in ["2024-01", "2024-02"]:
            for i in range(MULTI_LINE_MAX_SERIES + 1):
                data_over_threshold.append({"month": month, "severity": f"sev_{i}", "bug_count": i})

        hint = service._determine_visualization_hint(
            data=data_over_threshold,
            dimensions=["month", "severity"],
            metrics=["bug_count"],
        )
        assert hint.chart_type == "table"
