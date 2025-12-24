"""Unit tests for STORY-082: Rate Metrics in query_metrics.

Tests verify that:
1. All 5 rate metrics are registered with descriptions and formulas (AC1)
2. Rate metrics can be queried with dimensions like month/feature (AC2)
3. Rate metrics return None when total_bugs=0 (AC3)
4. Multiple rate metrics can be queried together (AC2)
5. Auto acceptance rate uses special denominator (accepted bugs only)

Epic: EPIC-014 (MCP Usability Improvements)
STORY-082: Rate Metrics in query_metrics
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from testio_mcp.services.analytics_service import AnalyticsService


def _create_mock_row(**kwargs) -> MagicMock:  # type: ignore[misc]
    """Create a mock row object with attribute access."""
    mock = MagicMock()
    for key, value in kwargs.items():
        setattr(mock, key, value)
    return mock


@pytest.mark.unit
def test_rate_metrics_in_registry() -> None:
    """Test that all 5 rate metrics are present in registry (AC1)."""
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    metrics = service._metrics

    # Verify all 5 rate metrics exist
    rate_metrics = [
        "overall_acceptance_rate",
        "rejection_rate",
        "review_rate",
        "active_acceptance_rate",
        "auto_acceptance_rate",
    ]

    for rate_metric in rate_metrics:
        assert rate_metric in metrics, f"Rate metric '{rate_metric}' not found in registry"

    # Verify each has description and formula
    for rate_metric in rate_metrics:
        metric_def = metrics[rate_metric]
        assert metric_def.description, f"Rate metric '{rate_metric}' missing description"
        assert metric_def.formula, f"Rate metric '{rate_metric}' missing formula"
        assert "NULLIF" in metric_def.formula, (
            f"Rate metric '{rate_metric}' formula should use NULLIF for null handling"
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_query_rejection_rate_by_month() -> None:
    """Test querying rejection_rate metric by month dimension (AC2)."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(month="2024-11", rejection_rate=0.15),
        _create_mock_row(month="2024-12", rejection_rate=0.25),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute query
    result = await service.query_metrics(
        metrics=["rejection_rate"],
        dimensions=["month"],
        filters={"product_id": 598},
    )

    # Verify response structure
    assert result.metadata.metrics_used == ["rejection_rate"]
    assert result.metadata.dimensions_used == ["month"]
    assert result.metadata.total_rows == 2

    # Verify data
    assert result.data[0]["month"] == "2024-11"
    assert result.data[0]["rejection_rate"] == 0.15


@pytest.mark.unit
@pytest.mark.asyncio
async def test_multiple_rate_metrics_together() -> None:
    """Test querying multiple rate metrics together (AC2)."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(
            month="2024-11",
            rejection_rate=0.15,
            overall_acceptance_rate=0.80,
            review_rate=0.90,
        ),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute query with multiple rate metrics
    result = await service.query_metrics(
        metrics=["rejection_rate", "overall_acceptance_rate", "review_rate"],
        dimensions=["month"],
    )

    # Verify all metrics present
    assert "rejection_rate" in result.data[0]
    assert "overall_acceptance_rate" in result.data[0]
    assert "review_rate" in result.data[0]

    # Verify values
    assert result.data[0]["rejection_rate"] == 0.15
    assert result.data[0]["overall_acceptance_rate"] == 0.80
    assert result.data[0]["review_rate"] == 0.90


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_metrics_null_handling_zero_bugs() -> None:
    """Test that rate metrics return None when total_bugs=0 (AC3)."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # Month with 0 bugs returns None for rate metrics
    mock_result.all.return_value = [
        _create_mock_row(month="2024-10", rejection_rate=None, overall_acceptance_rate=None),
        _create_mock_row(month="2024-11", rejection_rate=0.15, overall_acceptance_rate=0.80),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute query
    result = await service.query_metrics(
        metrics=["rejection_rate", "overall_acceptance_rate"],
        dimensions=["month"],
    )

    # Verify null handling for month with 0 bugs
    assert result.data[0]["month"] == "2024-10"
    assert result.data[0]["rejection_rate"] is None
    assert result.data[0]["overall_acceptance_rate"] is None

    # Verify normal values for month with bugs
    assert result.data[1]["month"] == "2024-11"
    assert result.data[1]["rejection_rate"] == 0.15
    assert result.data[1]["overall_acceptance_rate"] == 0.80


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rate_metrics_by_feature() -> None:
    """Test rate metrics grouped by feature dimension."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(
            feature_id=1,
            feature="Login",
            rejection_rate=0.25,
            overall_acceptance_rate=0.70,
        ),
        _create_mock_row(
            feature_id=2,
            feature="Dashboard",
            rejection_rate=0.10,
            overall_acceptance_rate=0.85,
        ),
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute query
    result = await service.query_metrics(
        metrics=["rejection_rate", "overall_acceptance_rate"],
        dimensions=["feature"],
    )

    # Verify feature dimension with rate metrics
    assert result.metadata.dimensions_used == ["feature"]
    assert result.data[0]["feature"] == "Login"
    assert result.data[0]["rejection_rate"] == 0.25
    assert result.data[1]["feature"] == "Dashboard"
    assert result.data[1]["rejection_rate"] == 0.10


@pytest.mark.unit
@pytest.mark.asyncio
async def test_auto_acceptance_rate_metric() -> None:
    """Test auto_acceptance_rate metric with special denominator (accepted bugs only)."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [
        _create_mock_row(month="2024-11", auto_acceptance_rate=0.20),  # 3/15 = 0.20
    ]
    mock_session.exec.return_value = mock_result

    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    # Execute query
    result = await service.query_metrics(
        metrics=["auto_acceptance_rate"],
        dimensions=["month"],
    )

    # Verify auto_acceptance_rate uses accepted bugs as denominator
    assert result.data[0]["auto_acceptance_rate"] == 0.20

    # Verify formula uses COUNT(DISTINCT) pattern for cardinality fix
    metric_def = service._metrics["auto_acceptance_rate"]
    assert "COUNT(DISTINCT" in metric_def.formula


@pytest.mark.unit
def test_rate_metrics_have_correct_formulas() -> None:
    """Verify rate metrics use COUNT(DISTINCT) pattern for cardinality fix.

    Bug fix: Platform and feature dimensions have many-to-many relationships
    with tests. Without COUNT(DISTINCT) in the numerator, the same bug would
    be counted multiple times, causing rates > 100%.

    Solution: Use COUNT(DISTINCT CASE WHEN ... THEN bug_id END) pattern
    to ensure both numerator and denominator count distinct bugs.
    """
    mock_session = AsyncMock()
    mock_client = AsyncMock()
    service = AnalyticsService(session=mock_session, customer_id=123, client=mock_client)

    metrics = service._metrics

    # Verify all rate metrics use COUNT(DISTINCT) pattern
    rate_metrics = [
        "overall_acceptance_rate",
        "rejection_rate",
        "review_rate",
        "active_acceptance_rate",
        "auto_acceptance_rate",
    ]

    for metric_key in rate_metrics:
        metric_def = metrics[metric_key]
        formula = metric_def.formula

        # Verify formula uses COUNT(DISTINCT) pattern
        assert "COUNT(DISTINCT" in formula, (
            f"Rate metric '{metric_key}' should use COUNT(DISTINCT) pattern. Got: {formula}"
        )
