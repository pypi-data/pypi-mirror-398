"""Unit tests for health_status utility functions.

Tests verify:
- Correct health status computation for all directions
- Boundary conditions (values exactly at thresholds)
- None handling (unknown status)
- Integration with PlaybookThresholds
"""

import pytest

from testio_mcp.schemas.playbook_thresholds import (
    HealthIndicators,
    MetricThreshold,
    PlaybookThresholds,
)
from testio_mcp.utilities.health_status import (
    compute_health_indicators,
    compute_health_indicators_dict,
    compute_health_status,
)


class TestComputeHealthStatus:
    """Tests for compute_health_status() function."""

    # -------------------------------------------------------------------------
    # Direction "above" tests (high values are bad)
    # -------------------------------------------------------------------------

    def test_above_direction_healthy_below_warning(self) -> None:
        """Value below warning threshold returns healthy."""
        threshold = MetricThreshold(warning=0.20, critical=0.35, direction="above")
        assert compute_health_status(0.15, threshold) == "healthy"
        assert compute_health_status(0.19, threshold) == "healthy"
        assert compute_health_status(0.0, threshold) == "healthy"

    def test_above_direction_warning_at_boundary(self) -> None:
        """Value exactly at warning threshold returns warning (inclusive)."""
        threshold = MetricThreshold(warning=0.20, critical=0.35, direction="above")
        assert compute_health_status(0.20, threshold) == "warning"

    def test_above_direction_warning_between_thresholds(self) -> None:
        """Value between warning and critical returns warning."""
        threshold = MetricThreshold(warning=0.20, critical=0.35, direction="above")
        assert compute_health_status(0.25, threshold) == "warning"
        assert compute_health_status(0.30, threshold) == "warning"
        assert compute_health_status(0.34, threshold) == "warning"

    def test_above_direction_critical_at_boundary(self) -> None:
        """Value exactly at critical threshold returns critical (inclusive)."""
        threshold = MetricThreshold(warning=0.20, critical=0.35, direction="above")
        assert compute_health_status(0.35, threshold) == "critical"

    def test_above_direction_critical_above_threshold(self) -> None:
        """Value above critical threshold returns critical."""
        threshold = MetricThreshold(warning=0.20, critical=0.35, direction="above")
        assert compute_health_status(0.40, threshold) == "critical"
        assert compute_health_status(0.50, threshold) == "critical"
        assert compute_health_status(1.0, threshold) == "critical"

    # -------------------------------------------------------------------------
    # Direction "below" tests (low values are bad)
    # -------------------------------------------------------------------------

    def test_below_direction_healthy_above_warning(self) -> None:
        """Value above warning threshold returns healthy."""
        threshold = MetricThreshold(warning=0.80, critical=0.60, direction="below")
        assert compute_health_status(0.85, threshold) == "healthy"
        assert compute_health_status(0.90, threshold) == "healthy"
        assert compute_health_status(1.0, threshold) == "healthy"

    def test_below_direction_warning_at_boundary(self) -> None:
        """Value exactly at warning threshold returns warning (inclusive)."""
        threshold = MetricThreshold(warning=0.80, critical=0.60, direction="below")
        assert compute_health_status(0.80, threshold) == "warning"

    def test_below_direction_warning_between_thresholds(self) -> None:
        """Value between warning and critical returns warning."""
        threshold = MetricThreshold(warning=0.80, critical=0.60, direction="below")
        assert compute_health_status(0.75, threshold) == "warning"
        assert compute_health_status(0.70, threshold) == "warning"
        assert compute_health_status(0.61, threshold) == "warning"

    def test_below_direction_critical_at_boundary(self) -> None:
        """Value exactly at critical threshold returns critical (inclusive)."""
        threshold = MetricThreshold(warning=0.80, critical=0.60, direction="below")
        assert compute_health_status(0.60, threshold) == "critical"

    def test_below_direction_critical_below_threshold(self) -> None:
        """Value below critical threshold returns critical."""
        threshold = MetricThreshold(warning=0.80, critical=0.60, direction="below")
        assert compute_health_status(0.55, threshold) == "critical"
        assert compute_health_status(0.30, threshold) == "critical"
        assert compute_health_status(0.0, threshold) == "critical"

    # -------------------------------------------------------------------------
    # None handling
    # -------------------------------------------------------------------------

    def test_none_value_returns_unknown(self) -> None:
        """None value returns unknown status regardless of threshold."""
        threshold_above = MetricThreshold(warning=0.20, critical=0.35, direction="above")
        threshold_below = MetricThreshold(warning=0.80, critical=0.60, direction="below")

        assert compute_health_status(None, threshold_above) == "unknown"
        assert compute_health_status(None, threshold_below) == "unknown"


class TestComputeHealthIndicators:
    """Tests for compute_health_indicators() function."""

    @pytest.fixture
    def default_thresholds(self) -> PlaybookThresholds:
        """Create default playbook thresholds matching production defaults."""
        return PlaybookThresholds(
            rejection_rate=MetricThreshold(warning=0.20, critical=0.35, direction="above"),
            auto_acceptance_rate=MetricThreshold(warning=0.20, critical=0.40, direction="above"),
            review_rate=MetricThreshold(warning=0.80, critical=0.60, direction="below"),
        )

    def test_all_healthy(self, default_thresholds: PlaybookThresholds) -> None:
        """All metrics in healthy range."""
        indicators = compute_health_indicators(
            rejection_rate=0.10,
            auto_acceptance_rate=0.15,
            review_rate=0.90,
            thresholds=default_thresholds,
        )

        assert indicators.rejection_rate == "healthy"
        assert indicators.auto_acceptance_rate == "healthy"
        assert indicators.review_rate == "healthy"

    def test_all_warning(self, default_thresholds: PlaybookThresholds) -> None:
        """All metrics in warning range."""
        indicators = compute_health_indicators(
            rejection_rate=0.25,
            auto_acceptance_rate=0.30,
            review_rate=0.70,
            thresholds=default_thresholds,
        )

        assert indicators.rejection_rate == "warning"
        assert indicators.auto_acceptance_rate == "warning"
        assert indicators.review_rate == "warning"

    def test_all_critical(self, default_thresholds: PlaybookThresholds) -> None:
        """All metrics in critical range."""
        indicators = compute_health_indicators(
            rejection_rate=0.40,
            auto_acceptance_rate=0.50,
            review_rate=0.50,
            thresholds=default_thresholds,
        )

        assert indicators.rejection_rate == "critical"
        assert indicators.auto_acceptance_rate == "critical"
        assert indicators.review_rate == "critical"

    def test_mixed_statuses(self, default_thresholds: PlaybookThresholds) -> None:
        """Different metrics can have different statuses."""
        indicators = compute_health_indicators(
            rejection_rate=0.10,  # healthy
            auto_acceptance_rate=0.25,  # warning
            review_rate=0.50,  # critical
            thresholds=default_thresholds,
        )

        assert indicators.rejection_rate == "healthy"
        assert indicators.auto_acceptance_rate == "warning"
        assert indicators.review_rate == "critical"

    def test_none_values_return_unknown(self, default_thresholds: PlaybookThresholds) -> None:
        """None values produce unknown status."""
        indicators = compute_health_indicators(
            rejection_rate=None,
            auto_acceptance_rate=None,
            review_rate=None,
            thresholds=default_thresholds,
        )

        assert indicators.rejection_rate == "unknown"
        assert indicators.auto_acceptance_rate == "unknown"
        assert indicators.review_rate == "unknown"

    def test_returns_health_indicators_model(self, default_thresholds: PlaybookThresholds) -> None:
        """Returns HealthIndicators Pydantic model."""
        indicators = compute_health_indicators(
            rejection_rate=0.10,
            auto_acceptance_rate=0.15,
            review_rate=0.90,
            thresholds=default_thresholds,
        )

        assert isinstance(indicators, HealthIndicators)


class TestComputeHealthIndicatorsDict:
    """Tests for compute_health_indicators_dict() function."""

    @pytest.fixture
    def default_thresholds(self) -> PlaybookThresholds:
        """Create default playbook thresholds."""
        return PlaybookThresholds(
            rejection_rate=MetricThreshold(warning=0.20, critical=0.35, direction="above"),
            auto_acceptance_rate=MetricThreshold(warning=0.20, critical=0.40, direction="above"),
            review_rate=MetricThreshold(warning=0.80, critical=0.60, direction="below"),
        )

    def test_returns_dict(self, default_thresholds: PlaybookThresholds) -> None:
        """Returns dict instead of Pydantic model."""
        result = compute_health_indicators_dict(
            rejection_rate=0.10,
            auto_acceptance_rate=0.15,
            review_rate=0.90,
            thresholds=default_thresholds,
        )

        assert isinstance(result, dict)
        assert result == {
            "rejection_rate": "healthy",
            "auto_acceptance_rate": "healthy",
            "review_rate": "healthy",
        }

    def test_dict_keys_match_model_fields(self, default_thresholds: PlaybookThresholds) -> None:
        """Dict keys match HealthIndicators model field names."""
        result = compute_health_indicators_dict(
            rejection_rate=0.25,
            auto_acceptance_rate=0.30,
            review_rate=0.70,
            thresholds=default_thresholds,
        )

        expected_keys = {"rejection_rate", "auto_acceptance_rate", "review_rate"}
        assert set(result.keys()) == expected_keys

    def test_serializable_for_json(self, default_thresholds: PlaybookThresholds) -> None:
        """Result is JSON-serializable (all string values)."""
        import json

        result = compute_health_indicators_dict(
            rejection_rate=0.10,
            auto_acceptance_rate=0.15,
            review_rate=0.90,
            thresholds=default_thresholds,
        )

        # Should not raise
        json_str = json.dumps(result)
        assert json_str is not None


class TestBoundaryConditionsRealWorld:
    """Real-world scenario tests for boundary conditions.

    These tests verify that the playbook table bands are correctly implemented:
    - rejection_rate: <20% healthy, 20-35% warning, >35% critical
    - auto_acceptance_rate: <20% healthy, 20-40% warning, >40% critical
    - review_rate: >80% healthy, 60-80% warning, <60% critical
    """

    @pytest.fixture
    def playbook_thresholds(self) -> PlaybookThresholds:
        """Production-like playbook thresholds."""
        return PlaybookThresholds(
            rejection_rate=MetricThreshold(warning=0.20, critical=0.35, direction="above"),
            auto_acceptance_rate=MetricThreshold(warning=0.20, critical=0.40, direction="above"),
            review_rate=MetricThreshold(warning=0.80, critical=0.60, direction="below"),
        )

    def test_rejection_rate_playbook_bands(self, playbook_thresholds: PlaybookThresholds) -> None:
        """Verify rejection_rate matches playbook: <20% healthy, 20-35% warning, >35% critical."""
        threshold = playbook_thresholds.rejection_rate

        # <20% = healthy
        assert compute_health_status(0.19, threshold) == "healthy"

        # 20% = warning (inclusive lower bound)
        assert compute_health_status(0.20, threshold) == "warning"

        # 20-35% = warning
        assert compute_health_status(0.30, threshold) == "warning"

        # 35% = critical (inclusive upper bound)
        assert compute_health_status(0.35, threshold) == "critical"

        # >35% = critical
        assert compute_health_status(0.36, threshold) == "critical"

    def test_auto_acceptance_rate_playbook_bands(
        self, playbook_thresholds: PlaybookThresholds
    ) -> None:
        """Verify auto_acceptance_rate: <20% healthy, 20-40% warning, >40% critical."""
        threshold = playbook_thresholds.auto_acceptance_rate

        # <20% = healthy
        assert compute_health_status(0.19, threshold) == "healthy"

        # 20% = warning (inclusive lower bound)
        assert compute_health_status(0.20, threshold) == "warning"

        # 20-40% = warning
        assert compute_health_status(0.35, threshold) == "warning"

        # 40% = critical (inclusive upper bound)
        assert compute_health_status(0.40, threshold) == "critical"

        # >40% = critical
        assert compute_health_status(0.41, threshold) == "critical"

    def test_review_rate_playbook_bands(self, playbook_thresholds: PlaybookThresholds) -> None:
        """Verify review_rate matches playbook: >80% healthy, 60-80% warning, <60% critical."""
        threshold = playbook_thresholds.review_rate

        # >80% = healthy
        assert compute_health_status(0.81, threshold) == "healthy"

        # 80% = warning (inclusive upper bound)
        assert compute_health_status(0.80, threshold) == "warning"

        # 60-80% = warning
        assert compute_health_status(0.70, threshold) == "warning"

        # 60% = critical (inclusive lower bound)
        assert compute_health_status(0.60, threshold) == "critical"

        # <60% = critical
        assert compute_health_status(0.59, threshold) == "critical"
