"""Unit tests for playbook_thresholds schema models.

Tests verify:
- MetricThreshold validation (threshold ordering)
- PlaybookThresholds factory method (from_settings)
- PlaybookThresholds.with_overrides() method
- HealthIndicators model structure
"""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from testio_mcp.schemas.playbook_thresholds import (
    HealthIndicators,
    MetricThreshold,
    PlaybookThresholds,
)


class TestMetricThreshold:
    """Tests for MetricThreshold model."""

    # -------------------------------------------------------------------------
    # Valid construction tests
    # -------------------------------------------------------------------------

    def test_valid_above_direction(self) -> None:
        """Valid threshold with direction='above' (warning < critical)."""
        threshold = MetricThreshold(warning=0.20, critical=0.35, direction="above")

        assert threshold.warning == 0.20
        assert threshold.critical == 0.35
        assert threshold.direction == "above"

    def test_valid_below_direction(self) -> None:
        """Valid threshold with direction='below' (warning > critical)."""
        threshold = MetricThreshold(warning=0.80, critical=0.60, direction="below")

        assert threshold.warning == 0.80
        assert threshold.critical == 0.60
        assert threshold.direction == "below"

    def test_boundary_values(self) -> None:
        """Threshold values at boundaries (0.0 and 1.0)."""
        threshold = MetricThreshold(warning=0.0, critical=0.5, direction="above")
        assert threshold.warning == 0.0

        threshold = MetricThreshold(warning=1.0, critical=0.5, direction="below")
        assert threshold.warning == 1.0

    # -------------------------------------------------------------------------
    # Threshold ordering validation tests
    # -------------------------------------------------------------------------

    def test_above_direction_rejects_warning_greater_than_critical(self) -> None:
        """Direction='above' rejects warning >= critical."""
        with pytest.raises(ValidationError) as exc_info:
            MetricThreshold(warning=0.40, critical=0.30, direction="above")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "warning" in errors[0]["msg"].lower()
        assert "critical" in errors[0]["msg"].lower()

    def test_above_direction_rejects_warning_equal_to_critical(self) -> None:
        """Direction='above' rejects warning == critical."""
        with pytest.raises(ValidationError) as exc_info:
            MetricThreshold(warning=0.30, critical=0.30, direction="above")

        errors = exc_info.value.errors()
        assert len(errors) == 1

    def test_below_direction_rejects_warning_less_than_critical(self) -> None:
        """Direction='below' rejects warning <= critical."""
        with pytest.raises(ValidationError) as exc_info:
            MetricThreshold(warning=0.50, critical=0.70, direction="below")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "warning" in errors[0]["msg"].lower()
        assert "critical" in errors[0]["msg"].lower()

    def test_below_direction_rejects_warning_equal_to_critical(self) -> None:
        """Direction='below' rejects warning == critical."""
        with pytest.raises(ValidationError) as exc_info:
            MetricThreshold(warning=0.60, critical=0.60, direction="below")

        errors = exc_info.value.errors()
        assert len(errors) == 1

    # -------------------------------------------------------------------------
    # Field validation tests
    # -------------------------------------------------------------------------

    def test_rejects_negative_values(self) -> None:
        """Threshold values must be >= 0.0."""
        with pytest.raises(ValidationError):
            MetricThreshold(warning=-0.1, critical=0.35, direction="above")

    def test_rejects_values_above_one(self) -> None:
        """Threshold values must be <= 1.0."""
        with pytest.raises(ValidationError):
            MetricThreshold(warning=0.20, critical=1.5, direction="above")

    def test_rejects_invalid_direction(self) -> None:
        """Direction must be 'above' or 'below'."""
        with pytest.raises(ValidationError):
            MetricThreshold(warning=0.20, critical=0.35, direction="invalid")  # type: ignore[arg-type]


class TestPlaybookThresholds:
    """Tests for PlaybookThresholds model."""

    # -------------------------------------------------------------------------
    # Construction tests
    # -------------------------------------------------------------------------

    def test_valid_construction(self) -> None:
        """Valid PlaybookThresholds with all metrics."""
        thresholds = PlaybookThresholds(
            rejection_rate=MetricThreshold(warning=0.20, critical=0.35, direction="above"),
            auto_acceptance_rate=MetricThreshold(warning=0.20, critical=0.40, direction="above"),
            review_rate=MetricThreshold(warning=0.80, critical=0.60, direction="below"),
        )

        assert thresholds.rejection_rate.warning == 0.20
        assert thresholds.auto_acceptance_rate.critical == 0.40
        assert thresholds.review_rate.direction == "below"

    # -------------------------------------------------------------------------
    # from_settings() factory method tests
    # -------------------------------------------------------------------------

    def test_from_settings_loads_values(self) -> None:
        """from_settings() loads values from Settings object."""
        mock_settings = MagicMock()
        mock_settings.PLAYBOOK_REJECTION_WARNING = 0.25
        mock_settings.PLAYBOOK_REJECTION_CRITICAL = 0.40
        mock_settings.PLAYBOOK_AUTO_ACCEPTANCE_WARNING = 0.15
        mock_settings.PLAYBOOK_AUTO_ACCEPTANCE_CRITICAL = 0.35
        mock_settings.PLAYBOOK_REVIEW_WARNING = 0.85
        mock_settings.PLAYBOOK_REVIEW_CRITICAL = 0.65

        thresholds = PlaybookThresholds.from_settings(mock_settings)

        assert thresholds.rejection_rate.warning == 0.25
        assert thresholds.rejection_rate.critical == 0.40
        assert thresholds.rejection_rate.direction == "above"

        assert thresholds.auto_acceptance_rate.warning == 0.15
        assert thresholds.auto_acceptance_rate.critical == 0.35
        assert thresholds.auto_acceptance_rate.direction == "above"

        assert thresholds.review_rate.warning == 0.85
        assert thresholds.review_rate.critical == 0.65
        assert thresholds.review_rate.direction == "below"

    def test_from_settings_with_default_values(self) -> None:
        """from_settings() works with production default values."""
        mock_settings = MagicMock()
        mock_settings.PLAYBOOK_REJECTION_WARNING = 0.20
        mock_settings.PLAYBOOK_REJECTION_CRITICAL = 0.35
        mock_settings.PLAYBOOK_AUTO_ACCEPTANCE_WARNING = 0.20
        mock_settings.PLAYBOOK_AUTO_ACCEPTANCE_CRITICAL = 0.40
        mock_settings.PLAYBOOK_REVIEW_WARNING = 0.80
        mock_settings.PLAYBOOK_REVIEW_CRITICAL = 0.60

        thresholds = PlaybookThresholds.from_settings(mock_settings)

        # Verify default values match playbook
        assert thresholds.rejection_rate.warning == 0.20
        assert thresholds.rejection_rate.critical == 0.35
        assert thresholds.auto_acceptance_rate.warning == 0.20
        assert thresholds.auto_acceptance_rate.critical == 0.40
        assert thresholds.review_rate.warning == 0.80
        assert thresholds.review_rate.critical == 0.60

    def test_from_settings_rejects_invalid_ordering(self) -> None:
        """from_settings() rejects mis-ordered thresholds from Settings."""
        mock_settings = MagicMock()
        mock_settings.PLAYBOOK_REJECTION_WARNING = 0.40  # Invalid: warning > critical
        mock_settings.PLAYBOOK_REJECTION_CRITICAL = 0.30
        mock_settings.PLAYBOOK_AUTO_ACCEPTANCE_WARNING = 0.20
        mock_settings.PLAYBOOK_AUTO_ACCEPTANCE_CRITICAL = 0.40
        mock_settings.PLAYBOOK_REVIEW_WARNING = 0.80
        mock_settings.PLAYBOOK_REVIEW_CRITICAL = 0.60

        with pytest.raises(ValidationError):
            PlaybookThresholds.from_settings(mock_settings)

    # -------------------------------------------------------------------------
    # with_overrides() method tests
    # -------------------------------------------------------------------------

    def test_with_overrides_replaces_single_metric(self) -> None:
        """with_overrides() replaces only specified metrics."""
        base = PlaybookThresholds(
            rejection_rate=MetricThreshold(warning=0.20, critical=0.35, direction="above"),
            auto_acceptance_rate=MetricThreshold(warning=0.20, critical=0.40, direction="above"),
            review_rate=MetricThreshold(warning=0.80, critical=0.60, direction="below"),
        )

        custom = base.with_overrides(
            {"rejection_rate": MetricThreshold(warning=0.25, critical=0.45, direction="above")}
        )

        # Override applied
        assert custom.rejection_rate.warning == 0.25
        assert custom.rejection_rate.critical == 0.45

        # Other metrics unchanged
        assert custom.auto_acceptance_rate.warning == 0.20
        assert custom.review_rate.warning == 0.80

    def test_with_overrides_replaces_multiple_metrics(self) -> None:
        """with_overrides() can replace multiple metrics."""
        base = PlaybookThresholds(
            rejection_rate=MetricThreshold(warning=0.20, critical=0.35, direction="above"),
            auto_acceptance_rate=MetricThreshold(warning=0.20, critical=0.40, direction="above"),
            review_rate=MetricThreshold(warning=0.80, critical=0.60, direction="below"),
        )

        custom = base.with_overrides(
            {
                "rejection_rate": MetricThreshold(warning=0.30, critical=0.50, direction="above"),
                "review_rate": MetricThreshold(warning=0.75, critical=0.55, direction="below"),
            }
        )

        assert custom.rejection_rate.warning == 0.30
        assert custom.auto_acceptance_rate.warning == 0.20  # unchanged
        assert custom.review_rate.warning == 0.75

    def test_with_overrides_returns_new_instance(self) -> None:
        """with_overrides() returns new instance, doesn't modify original."""
        base = PlaybookThresholds(
            rejection_rate=MetricThreshold(warning=0.20, critical=0.35, direction="above"),
            auto_acceptance_rate=MetricThreshold(warning=0.20, critical=0.40, direction="above"),
            review_rate=MetricThreshold(warning=0.80, critical=0.60, direction="below"),
        )

        custom = base.with_overrides(
            {"rejection_rate": MetricThreshold(warning=0.30, critical=0.50, direction="above")}
        )

        # Original unchanged
        assert base.rejection_rate.warning == 0.20
        # New instance has override
        assert custom.rejection_rate.warning == 0.30
        # Different objects
        assert base is not custom

    def test_with_overrides_empty_dict(self) -> None:
        """with_overrides() with empty dict returns equivalent instance."""
        base = PlaybookThresholds(
            rejection_rate=MetricThreshold(warning=0.20, critical=0.35, direction="above"),
            auto_acceptance_rate=MetricThreshold(warning=0.20, critical=0.40, direction="above"),
            review_rate=MetricThreshold(warning=0.80, critical=0.60, direction="below"),
        )

        custom = base.with_overrides({})

        assert custom.rejection_rate.warning == 0.20
        assert custom.auto_acceptance_rate.warning == 0.20
        assert custom.review_rate.warning == 0.80


class TestHealthIndicators:
    """Tests for HealthIndicators model."""

    def test_valid_construction(self) -> None:
        """Valid HealthIndicators with all statuses."""
        indicators = HealthIndicators(
            rejection_rate="healthy",
            auto_acceptance_rate="warning",
            review_rate="critical",
        )

        assert indicators.rejection_rate == "healthy"
        assert indicators.auto_acceptance_rate == "warning"
        assert indicators.review_rate == "critical"

    def test_unknown_status(self) -> None:
        """HealthIndicators accepts 'unknown' status."""
        indicators = HealthIndicators(
            rejection_rate="unknown",
            auto_acceptance_rate="unknown",
            review_rate="unknown",
        )

        assert indicators.rejection_rate == "unknown"

    def test_model_dump(self) -> None:
        """HealthIndicators can be serialized to dict."""
        indicators = HealthIndicators(
            rejection_rate="healthy",
            auto_acceptance_rate="warning",
            review_rate="critical",
        )

        result = indicators.model_dump()

        assert result == {
            "rejection_rate": "healthy",
            "auto_acceptance_rate": "warning",
            "review_rate": "critical",
        }

    def test_rejects_invalid_status(self) -> None:
        """HealthIndicators rejects invalid status values."""
        with pytest.raises(ValidationError):
            HealthIndicators(
                rejection_rate="invalid",  # type: ignore[arg-type]
                auto_acceptance_rate="healthy",
                review_rate="healthy",
            )
