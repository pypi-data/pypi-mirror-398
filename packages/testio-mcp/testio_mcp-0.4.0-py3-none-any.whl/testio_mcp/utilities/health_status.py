"""Health status computation utilities for playbook metrics.

This module provides functions to compute health status (healthy/warning/critical)
based on metric values and threshold configuration.

The computation logic is centralized here to ensure consistency across:
- API responses (get_product_quality_report)
- AI agent prompts (analyze_product_quality)
- Future: PlaybookAlerts component in testio-agui

Reference: CSM Playbook - Quick Reference: Key Thresholds
"""

from testio_mcp.schemas.playbook_thresholds import (
    HealthIndicators,
    HealthStatus,
    MetricThreshold,
    PlaybookThresholds,
)


def compute_health_status(
    value: float | None,
    threshold: MetricThreshold,
) -> HealthStatus:
    """Compute health status for a single metric value.

    Args:
        value: The metric value (0.0-1.0 for rates), or None if unavailable
        threshold: Threshold configuration with warning/critical bounds and direction

    Returns:
        HealthStatus: One of "healthy", "warning", "critical", or "unknown"

    Examples:
        >>> # Rejection rate: high is bad (direction="above")
        >>> threshold = MetricThreshold(warning=0.20, critical=0.35, direction="above")
        >>> compute_health_status(0.15, threshold)
        'healthy'
        >>> compute_health_status(0.20, threshold)  # At warning boundary
        'warning'
        >>> compute_health_status(0.28, threshold)
        'warning'
        >>> compute_health_status(0.35, threshold)  # At critical boundary
        'critical'
        >>> compute_health_status(0.42, threshold)
        'critical'
        >>> compute_health_status(None, threshold)
        'unknown'

        >>> # Review rate: low is bad (direction="below")
        >>> threshold = MetricThreshold(warning=0.80, critical=0.60, direction="below")
        >>> compute_health_status(0.85, threshold)
        'healthy'
        >>> compute_health_status(0.80, threshold)  # At warning boundary
        'warning'
        >>> compute_health_status(0.72, threshold)
        'warning'
        >>> compute_health_status(0.60, threshold)  # At critical boundary
        'critical'
        >>> compute_health_status(0.55, threshold)
        'critical'
    """
    if value is None:
        return "unknown"

    if threshold.direction == "above":
        # High values are bad (rejection_rate, auto_acceptance_rate)
        # Critical if at or above critical threshold
        # Warning if at or above warning threshold but below critical
        # Uses >= to match playbook bands: "20-35% = warning" means 20% is warning
        if value >= threshold.critical:
            return "critical"
        if value >= threshold.warning:
            return "warning"
    else:
        # Low values are bad (review_rate)
        # Critical if at or below critical threshold
        # Warning if at or below warning threshold but above critical
        # Uses <= to match playbook bands: "60-80% = warning" means 80% is warning
        if value <= threshold.critical:
            return "critical"
        if value <= threshold.warning:
            return "warning"

    return "healthy"


def compute_health_indicators(
    rejection_rate: float | None,
    auto_acceptance_rate: float | None,
    review_rate: float | None,
    thresholds: PlaybookThresholds,
) -> HealthIndicators:
    """Compute health indicators for all playbook metrics.

    This is the main entry point for computing health status across all metrics.
    It returns a structured HealthIndicators object suitable for API responses.

    Args:
        rejection_rate: Rejection rate (0.0-1.0) or None
        auto_acceptance_rate: Auto-acceptance rate (0.0-1.0) or None
        review_rate: Review rate (0.0-1.0) or None
        thresholds: PlaybookThresholds configuration

    Returns:
        HealthIndicators with status for each metric

    Example:
        >>> from testio_mcp.config import settings
        >>> thresholds = PlaybookThresholds.from_settings(settings)
        >>> indicators = compute_health_indicators(
        ...     rejection_rate=0.28,
        ...     auto_acceptance_rate=0.15,
        ...     review_rate=0.72,
        ...     thresholds=thresholds
        ... )
        >>> indicators.rejection_rate
        'warning'
        >>> indicators.auto_acceptance_rate
        'healthy'
        >>> indicators.review_rate
        'warning'
    """
    return HealthIndicators(
        rejection_rate=compute_health_status(rejection_rate, thresholds.rejection_rate),
        auto_acceptance_rate=compute_health_status(
            auto_acceptance_rate, thresholds.auto_acceptance_rate
        ),
        review_rate=compute_health_status(review_rate, thresholds.review_rate),
    )


def compute_health_indicators_dict(
    rejection_rate: float | None,
    auto_acceptance_rate: float | None,
    review_rate: float | None,
    thresholds: PlaybookThresholds,
) -> dict[str, HealthStatus]:
    """Compute health indicators as a plain dictionary.

    Convenience function that returns a dict instead of HealthIndicators model.
    Useful for direct JSON serialization in API responses.

    Args:
        rejection_rate: Rejection rate (0.0-1.0) or None
        auto_acceptance_rate: Auto-acceptance rate (0.0-1.0) or None
        review_rate: Review rate (0.0-1.0) or None
        thresholds: PlaybookThresholds configuration

    Returns:
        Dict with health status for each metric

    Example:
        >>> compute_health_indicators_dict(0.28, 0.15, 0.72, thresholds)
        {
            'rejection_rate': 'warning',
            'auto_acceptance_rate': 'healthy',
            'review_rate': 'warning'
        }
    """
    indicators = compute_health_indicators(
        rejection_rate=rejection_rate,
        auto_acceptance_rate=auto_acceptance_rate,
        review_rate=review_rate,
        thresholds=thresholds,
    )
    return indicators.model_dump()
