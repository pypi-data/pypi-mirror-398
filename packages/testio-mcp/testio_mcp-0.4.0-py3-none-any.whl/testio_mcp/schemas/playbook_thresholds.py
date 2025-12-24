"""Playbook threshold configuration for health indicators.

This module defines the threshold configuration used to compute health status
(healthy/warning/critical) for key quality metrics like rejection rate,
auto-acceptance rate, and review rate.

Thresholds are loaded from environment variables via config.py, enabling
deployment-time customization without code changes.

Future Extension (per-product thresholds):
    The data model supports per-product overrides via SQLite storage.
    When needed, add a `playbook_overrides` table and use `with_overrides()`
    to merge base thresholds with product-specific values.

Reference: UX Design Specification - Visual Design Foundation - Playbook Semantics
"""

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from testio_mcp.config import Settings

# Type aliases for health status values
HealthStatus = Literal["healthy", "warning", "critical", "unknown"]
ThresholdDirection = Literal["above", "below"]


class MetricThreshold(BaseModel):
    """Threshold configuration for a single metric.

    Attributes:
        warning: Threshold value that triggers warning status
        critical: Threshold value that triggers critical status
        direction: How to interpret the thresholds
            - "above": High values are bad (e.g., rejection_rate >= 35% = critical)
            - "below": Low values are bad (e.g., review_rate <= 60% = critical)

    Threshold Ordering:
        For direction="above": warning must be < critical (lower values trigger warning first)
        For direction="below": warning must be > critical (higher values trigger warning first)

    Example:
        >>> threshold = MetricThreshold(warning=0.20, critical=0.35, direction="above")
        >>> # For rejection_rate=0.20: warning (at or above 0.20)
        >>> # For rejection_rate=0.35: critical (at or above 0.35)
    """

    warning: float = Field(ge=0.0, le=1.0, description="Warning threshold (0.0-1.0)")
    critical: float = Field(ge=0.0, le=1.0, description="Critical threshold (0.0-1.0)")
    direction: ThresholdDirection = Field(
        description="'above' = high is bad (rejection), 'below' = low is bad (review)"
    )

    @model_validator(mode="after")
    def validate_threshold_ordering(self) -> "MetricThreshold":
        """Validate that thresholds are ordered correctly for the direction.

        For direction="above" (high is bad): warning < critical
            - Values hit warning first, then critical as they increase
        For direction="below" (low is bad): warning > critical
            - Values hit warning first, then critical as they decrease

        Raises:
            ValueError: If thresholds are mis-ordered for the direction
        """
        if self.direction == "above":
            if self.warning >= self.critical:
                raise ValueError(
                    f"For direction='above', warning ({self.warning}) must be < "
                    f"critical ({self.critical}). Higher values are worse, so "
                    f"warning threshold should be lower than critical."
                )
        else:  # direction == "below"
            if self.warning <= self.critical:
                raise ValueError(
                    f"For direction='below', warning ({self.warning}) must be > "
                    f"critical ({self.critical}). Lower values are worse, so "
                    f"warning threshold should be higher than critical."
                )
        return self


class PlaybookThresholds(BaseModel):
    """Complete playbook threshold configuration for all health metrics.

    This class holds threshold definitions for the three key playbook metrics:
    - rejection_rate: High rejection indicates noisy cycles or unclear instructions
    - auto_acceptance_rate: High auto-acceptance indicates bandwidth/engagement issues
    - review_rate: Low review rate indicates customer disengagement

    Default thresholds (from CSM Playbook):
        | Metric              | Healthy | Warning | Critical |
        |---------------------|---------|---------|----------|
        | rejection_rate      | <20%    | 20-35%  | >35%     |
        | auto_acceptance_rate| <20%    | 20-40%  | >40%     |
        | review_rate         | >80%    | 60-80%  | <60%     |

    Example:
        >>> from testio_mcp.config import settings
        >>> thresholds = PlaybookThresholds.from_settings(settings)
        >>> thresholds.rejection_rate.warning
        0.2
    """

    rejection_rate: MetricThreshold = Field(description="Rejection rate thresholds (high is bad)")
    auto_acceptance_rate: MetricThreshold = Field(
        description="Auto-acceptance rate thresholds (high is bad)"
    )
    review_rate: MetricThreshold = Field(description="Review rate thresholds (low is bad)")

    @classmethod
    def from_settings(cls, settings: "Settings") -> "PlaybookThresholds":  # noqa: F821
        """Build PlaybookThresholds from config.py settings (env vars).

        Args:
            settings: Settings instance with PLAYBOOK_* env vars

        Returns:
            PlaybookThresholds with values from environment configuration
        """
        return cls(
            rejection_rate=MetricThreshold(
                warning=settings.PLAYBOOK_REJECTION_WARNING,
                critical=settings.PLAYBOOK_REJECTION_CRITICAL,
                direction="above",
            ),
            auto_acceptance_rate=MetricThreshold(
                warning=settings.PLAYBOOK_AUTO_ACCEPTANCE_WARNING,
                critical=settings.PLAYBOOK_AUTO_ACCEPTANCE_CRITICAL,
                direction="above",
            ),
            review_rate=MetricThreshold(
                warning=settings.PLAYBOOK_REVIEW_WARNING,
                critical=settings.PLAYBOOK_REVIEW_CRITICAL,
                direction="below",
            ),
        )

    def with_overrides(self, overrides: dict[str, "MetricThreshold"]) -> "PlaybookThresholds":
        """Create new PlaybookThresholds with per-product overrides applied.

        This method supports future per-product threshold customization.
        Overrides are merged with base thresholds - only specified metrics
        are replaced.

        Args:
            overrides: Dict mapping metric names to custom MetricThreshold values
                      e.g., {"rejection_rate": MetricThreshold(warning=0.25, ...)}

        Returns:
            New PlaybookThresholds instance with overrides applied

        Example:
            >>> base = PlaybookThresholds.from_settings(settings)
            >>> custom = base.with_overrides({
            ...     "rejection_rate": MetricThreshold(
            ...         warning=0.25, critical=0.40, direction="above"
            ...     )
            ... })
            >>> custom.rejection_rate.warning
            0.25
        """
        return PlaybookThresholds(
            rejection_rate=overrides.get("rejection_rate", self.rejection_rate),
            auto_acceptance_rate=overrides.get("auto_acceptance_rate", self.auto_acceptance_rate),
            review_rate=overrides.get("review_rate", self.review_rate),
        )


class HealthIndicators(BaseModel):
    """Health status indicators for all playbook metrics.

    This is the response structure included in API responses to communicate
    the computed health status for each metric.

    Example API response:
        {
            "summary": {
                "rejection_rate": 0.28,
                "health_indicators": {
                    "rejection_rate": "warning",
                    "auto_acceptance_rate": "healthy",
                    "review_rate": "warning"
                }
            }
        }
    """

    rejection_rate: HealthStatus = Field(description="Health status for rejection rate")
    auto_acceptance_rate: HealthStatus = Field(description="Health status for auto-acceptance rate")
    review_rate: HealthStatus = Field(description="Health status for review rate")
