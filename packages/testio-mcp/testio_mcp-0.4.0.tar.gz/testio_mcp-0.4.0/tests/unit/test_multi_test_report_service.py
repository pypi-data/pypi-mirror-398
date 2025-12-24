"""Unit tests for MultiTestReportService."""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from testio_mcp.exceptions import ProductNotFoundException
from testio_mcp.services.multi_test_report_service import MultiTestReportService


def setup_repo_mocks(
    tests: list[dict[str, Any]] | None = None,
    bugs_by_test: dict[int, list[dict[str, Any]]] | None = None,
    test_aggregates: dict[str, Any] | None = None,
    bug_aggregates: dict[str, Any] | None = None,
) -> tuple[AsyncMock, AsyncMock, AsyncMock]:
    """Create mock repositories with standard responses for PQR tests.

    Args:
        tests: List of test dicts for query_tests_for_products (also used for test_data)
        bugs_by_test: Dict of test_id -> list of bug dicts
        test_aggregates: Override for get_test_aggregates_for_products response
        bug_aggregates: Override for get_bug_aggregates_for_tests response

    Returns:
        Tuple of (mock_test_repo, mock_bug_repo, mock_product_repo)
    """
    tests = tests or []
    bugs_by_test = bugs_by_test or {}

    test_ids = [t["id"] for t in tests if t.get("id")]

    # Count tests by status
    tests_by_status: dict[str, int] = {}
    tests_by_type: dict[str, int] = {}
    for t in tests:
        status = t.get("status", "unknown")
        tests_by_status[status] = tests_by_status.get(status, 0) + 1
        ttype = t.get("testing_type", "unknown")
        tests_by_type[ttype] = tests_by_type.get(ttype, 0) + 1

    # Count bugs by status/severity
    total_bugs = sum(len(bugs) for bugs in bugs_by_test.values())
    bugs_by_status: dict[str, int] = {}
    bugs_by_severity: dict[str, int] = {}
    for bugs in bugs_by_test.values():
        for bug in bugs:
            status = bug.get("status", "unknown")
            bugs_by_status[status] = bugs_by_status.get(status, 0) + 1
            severity = bug.get("severity", "unknown")
            bugs_by_severity[severity] = bugs_by_severity.get(severity, 0) + 1

    mock_test_repo = AsyncMock()
    mock_test_repo.get_test_aggregates_for_products.return_value = test_aggregates or {
        "total_tests": len(tests),
        "tests_by_status": tests_by_status,
        "tests_by_type": tests_by_type,
    }
    mock_test_repo.get_test_ids_for_products.return_value = test_ids
    mock_test_repo.query_tests_for_products.return_value = tests

    mock_bug_repo = AsyncMock()
    mock_bug_repo.get_bug_aggregates_for_tests.return_value = bug_aggregates or {
        "total_bugs": total_bugs,
        "bugs_by_status": bugs_by_status,
        "bugs_by_severity": bugs_by_severity,
    }
    mock_bug_repo.get_bugs_cached_or_refresh.return_value = (
        bugs_by_test,
        {
            "total_tests": len(test_ids),
            "cache_hits": len(test_ids),
            "api_calls": 0,
            "cache_hit_rate": 100.0 if test_ids else 0.0,
            "breakdown": {"immutable_cached": len(test_ids)},
        },
    )

    mock_product_repo = AsyncMock()
    mock_product_repo.get_product_info.return_value = {
        "id": 598,
        "name": "Test Product",
        "type": "web",
    }

    return mock_test_repo, mock_bug_repo, mock_product_repo


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_aggregates_bugs() -> None:
    """Verify EBR aggregates bugs across multiple tests."""
    # Mock repositories
    mock_test_repo = AsyncMock()

    # New aggregate methods for summary computation
    mock_test_repo.get_test_aggregates_for_products.return_value = {
        "total_tests": 2,
        "tests_by_status": {"locked": 2},
        "tests_by_type": {"coverage": 2},
    }
    mock_test_repo.get_test_ids_for_products.return_value = [123, 124]

    # Sample tests for test_data (limited fetch)
    mock_test_repo.query_tests_for_products.return_value = [
        {"id": 123, "title": "Test 1", "status": "locked"},
        {"id": 124, "title": "Test 2", "status": "locked"},
    ]

    mock_bug_repo = AsyncMock()
    # Bug aggregates for summary (from ALL tests)
    mock_bug_repo.get_bug_aggregates_for_tests.return_value = {
        "total_bugs": 2,
        "bugs_by_status": {"accepted": 1, "rejected": 1},
        "bugs_by_severity": {"high": 2},
    }
    # Bugs for sample tests only
    mock_bug_repo.get_bugs_cached_or_refresh.return_value = (
        {
            123: [{"status": "accepted"}],
            124: [{"status": "rejected"}],
        },
        {
            "total_tests": 2,
            "cache_hits": 2,
            "api_calls": 0,
            "cache_hit_rate": 100.0,
            "breakdown": {"immutable_cached": 2},
        },
    )

    mock_product_repo = AsyncMock()
    mock_product_repo.get_product_info.return_value = {
        "id": 598,
        "name": "Test Product",
        "type": "web",
    }

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    result = await service.get_product_quality_report(product_ids=[598])

    # Verify summary aggregation (from aggregate queries)
    assert result["summary"]["total_tests"] == 2
    assert result["summary"]["total_bugs"] == 2
    assert result["summary"]["bugs_by_status"]["active_accepted"] == 1
    assert result["summary"]["bugs_by_status"]["rejected"] == 1
    assert result["summary"]["reviewed"] == 2
    assert result["summary"]["overall_acceptance_rate"] == 0.5  # 1/2

    # Verify test_data (renamed from by_test)
    assert len(result["test_data"]) == 2
    assert result["test_data"][0]["test_id"] == 123
    assert result["test_data"][0]["bugs"]["active_accepted"] == 1
    assert result["test_data"][1]["test_id"] == 124
    assert result["test_data"][1]["bugs"]["rejected"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_filters_by_date() -> None:
    """Verify date filtering works with flexible formats."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Use parse_flexible_date internally (via service)
    await service.get_product_quality_report(
        product_ids=[598],
        start_date="last 30 days",
        end_date="today",
    )

    # Verify TestRepository was called with parsed dates
    call_args = mock_test_repo.query_tests_for_products.call_args
    assert call_args.kwargs["start_date"] is not None
    assert call_args.kwargs["end_date"] is not None
    assert isinstance(call_args.kwargs["start_date"], datetime)
    assert isinstance(call_args.kwargs["end_date"], datetime)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_filters_by_status() -> None:
    """Verify status filtering is passed to repository."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    await service.get_product_quality_report(
        product_ids=[598],
        statuses=["locked", "running"],
    )

    # Verify statuses passed to repository
    call_args = mock_test_repo.query_tests_for_products.call_args
    assert call_args.kwargs["statuses"] == ["locked", "running"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_handles_no_tests() -> None:
    """Verify EBR handles empty test list gracefully."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    result = await service.get_product_quality_report(product_ids=[598])

    # Verify empty summary
    assert result["summary"]["total_tests"] == 0
    assert result["summary"]["total_bugs"] == 0
    assert result["summary"]["reviewed"] == 0
    assert result["summary"]["overall_acceptance_rate"] is None
    assert result["test_data"] == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_handles_test_with_no_bugs() -> None:
    """Verify EBR handles test with no bugs (acceptance rate should be None)."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks(
        tests=[{"id": 123, "title": "Test 1", "status": "locked"}],
        bugs_by_test={123: []},
    )

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    result = await service.get_product_quality_report(product_ids=[598])

    # Verify summary
    assert result["summary"]["total_tests"] == 1
    assert result["summary"]["total_bugs"] == 0

    # STORY-081: All rate fields should be None (not 0.0) when no bugs exist
    assert result["summary"]["active_acceptance_rate"] is None
    assert result["summary"]["auto_acceptance_rate"] is None
    assert result["summary"]["overall_acceptance_rate"] is None
    assert result["summary"]["rejection_rate"] is None
    assert result["summary"]["review_rate"] is None

    # Verify test_data metrics
    assert result["test_data"][0]["bugs"]["reviewed"] == 0

    # STORY-081: All rate fields should be None (not 0.0) when test has no bugs
    assert result["test_data"][0]["active_acceptance_rate"] is None
    assert result["test_data"][0]["auto_acceptance_rate"] is None
    assert result["test_data"][0]["overall_acceptance_rate"] is None
    assert result["test_data"][0]["rejection_rate"] is None
    assert result["test_data"][0]["review_rate"] is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_calculates_acceptance_rates() -> None:
    """Verify acceptance rate calculations match shared utilities."""
    # 12 active accepted, 3 auto accepted, 3 rejected
    bugs = (
        [{"status": "accepted"}] * 12
        + [{"status": "auto_accepted"}] * 3
        + [{"status": "rejected"}] * 3
    )
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks(
        tests=[{"id": 123, "title": "Test 1", "status": "locked"}],
        bugs_by_test={123: bugs},
    )

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    result = await service.get_product_quality_report(product_ids=[598])

    # Verify test_data counts
    assert result["test_data"][0]["bugs"]["active_accepted"] == 12
    assert result["test_data"][0]["bugs"]["auto_accepted"] == 3
    assert result["test_data"][0]["bugs"]["rejected"] == 3
    assert result["test_data"][0]["bugs"]["reviewed"] == 15

    # Verify rates
    assert abs(result["test_data"][0]["active_acceptance_rate"] - (12 / 18)) < 0.001
    assert abs(result["test_data"][0]["auto_acceptance_rate"] - (3 / 15)) < 0.001
    assert abs(result["test_data"][0]["overall_acceptance_rate"] - (15 / 18)) < 0.001
    assert abs(result["test_data"][0]["rejection_rate"] - (3 / 18)) < 0.001


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_handles_open_bugs() -> None:
    """Verify open (forwarded) bugs are excluded from reviewed count."""
    bugs = [{"status": "accepted"}] * 5 + [{"status": "forwarded"}] * 5
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks(
        tests=[{"id": 123, "title": "Test 1", "status": "locked"}],
        bugs_by_test={123: bugs},
    )

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    result = await service.get_product_quality_report(product_ids=[598])

    # Verify test_data counts
    assert result["test_data"][0]["bugs"]["active_accepted"] == 5
    assert result["test_data"][0]["bugs"]["open"] == 5
    assert result["test_data"][0]["bugs"]["reviewed"] == 5
    assert result["test_data"][0]["overall_acceptance_rate"] == 0.5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_raises_product_not_found() -> None:
    """Verify ProductNotFoundException is raised for missing product."""
    mock_test_repo = AsyncMock()

    mock_bug_repo = AsyncMock()
    mock_bug_repo.get_bugs_cached_or_refresh.return_value = (
        {},
        {
            "total_tests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "cache_hit_rate": 0.0,
            "breakdown": {},
        },
    )

    mock_product_repo = AsyncMock()
    mock_product_repo.get_product_info.return_value = None  # Product not found (STORY-032A)

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    with pytest.raises(ProductNotFoundException) as exc_info:
        await service.get_product_quality_report(product_ids=[999])

    assert exc_info.value.product_id == 999


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_formats_period_string() -> None:
    """Verify period string formatting for various date combinations."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Test all combinations
    result = await service.get_product_quality_report(product_ids=[598])
    assert result["summary"]["period"] == "all time"

    result = await service.get_product_quality_report(product_ids=[598], start_date="2024-01-01")
    assert result["summary"]["period"] == "2024-01-01 to present"

    result = await service.get_product_quality_report(product_ids=[598], end_date="2024-12-31")
    assert result["summary"]["period"] == "through 2024-12-31"

    result = await service.get_product_quality_report(
        product_ids=[598], start_date="2024-01-01", end_date="2024-12-31"
    )
    assert result["summary"]["period"] == "2024-01-01 to 2024-12-31"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_uses_shared_utilities() -> None:
    """Verify EBR uses shared utilities from STORY-023b."""
    bugs = [{"status": "accepted"}] * 10
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks(
        tests=[{"id": 123, "title": "Test 1", "status": "locked"}],
        bugs_by_test={123: bugs},
    )

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Patch utilities to verify they're called
    with patch("testio_mcp.services.multi_test_report_service.classify_bugs") as mock_classify:
        with patch(
            "testio_mcp.services.multi_test_report_service.calculate_acceptance_rates"
        ) as mock_calc_rates:
            # Set up mock return values
            mock_classify.return_value = {
                "active_accepted": 10,
                "auto_accepted": 0,
                "rejected": 0,
                "open": 0,
                "total_accepted": 10,
                "reviewed": 10,
            }
            mock_calc_rates.return_value = {
                "active_acceptance_rate": 1.0,
                "auto_acceptance_rate": 0.0,
                "overall_acceptance_rate": 1.0,
                "rejection_rate": 0.0,
                "review_rate": 1.0,  # Now included in shared utility
            }

            await service.get_product_quality_report(product_ids=[598])

            # Verify utilities were called
            assert mock_classify.call_count >= 1
            assert mock_calc_rates.call_count >= 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_parses_iso_date() -> None:
    """Verify ISO 8601 date parsing works correctly."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    await service.get_product_quality_report(
        product_ids=[598],
        start_date="2024-01-01",
        end_date="2024-12-31",
    )

    # Verify dates were parsed
    call_args = mock_test_repo.query_tests_for_products.call_args
    start_dt = call_args.kwargs["start_date"]
    end_dt = call_args.kwargs["end_date"]

    assert start_dt.year == 2024
    assert start_dt.month == 1
    assert start_dt.day == 1
    assert start_dt.hour == 0  # Start of day

    assert end_dt.year == 2024
    assert end_dt.month == 12
    assert end_dt.day == 31
    assert end_dt.hour == 23  # End of day


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_enhancements() -> None:
    """Verify enhancements: bugs_by_severity, tests_by_type, avg_bugs_per_test."""
    # Test 1: Rapid, 2 bugs (Critical, Low)
    # Test 2: Focused, 1 bug (High)
    # Test 3: Rapid, 0 bugs
    tests = [
        {"id": 101, "title": "Test 1", "status": "locked", "testing_type": "rapid"},
        {"id": 102, "title": "Test 2", "status": "locked", "testing_type": "focused"},
        {"id": 103, "title": "Test 3", "status": "locked", "testing_type": "rapid"},
    ]
    bugs_map = {
        101: [
            {"id": 1, "severity": "critical", "status": "accepted", "known": False},
            {"id": 2, "severity": "low", "status": "rejected", "known": False},
        ],
        102: [
            {"id": 3, "severity": "high", "status": "accepted", "known": False},
        ],
        103: [],
    }
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks(
        tests=tests,
        bugs_by_test=bugs_map,
    )

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Execute
    report = await service.get_product_quality_report(product_ids=[1])
    summary = report["summary"]

    # Verify Tests by Type
    assert summary["tests_by_type"] == {"rapid": 2, "focused": 1}

    # Verify Bugs by Severity
    # Total bugs = 3 (Critical, Low, High)
    assert summary["bugs_by_severity"] == {"critical": 1, "low": 1, "high": 1}

    # Verify Avg Bugs per Test
    # Total bugs = 3, Total tests = 3 -> Avg = 1.0
    assert summary["avg_bugs_per_test"] == 1.0

    # Verify Total Bugs
    assert summary["total_bugs"] == 3


# =============================================================================
# Mutual Exclusivity Validation Tests (Post-Review Fixes)
# =============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_rejects_test_ids_with_start_date() -> None:
    """Verify test_ids + start_date raises ValidationError."""
    from testio_mcp.exceptions import ValidationError

    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    with pytest.raises(ValidationError) as exc_info:
        await service.get_product_quality_report(
            product_ids=[598],
            test_ids=[123, 456],
            start_date="2024-01-01",
        )

    assert exc_info.value.field == "test_ids"
    assert "date" in exc_info.value.message.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_rejects_test_ids_with_end_date() -> None:
    """Verify test_ids + end_date raises ValidationError."""
    from testio_mcp.exceptions import ValidationError

    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    with pytest.raises(ValidationError) as exc_info:
        await service.get_product_quality_report(
            product_ids=[598],
            test_ids=[123, 456],
            end_date="2024-12-31",
        )

    assert exc_info.value.field == "test_ids"
    assert "date" in exc_info.value.message.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_rejects_test_ids_with_statuses() -> None:
    """Verify test_ids + statuses raises ValidationError."""
    from testio_mcp.exceptions import ValidationError

    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    with pytest.raises(ValidationError) as exc_info:
        await service.get_product_quality_report(
            product_ids=[598],
            test_ids=[123, 456],
            statuses=["locked", "archived"],
        )

    assert exc_info.value.field == "test_ids"
    assert "status" in exc_info.value.message.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_accepts_test_ids_alone() -> None:
    """Verify test_ids without filters works correctly."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks(
        tests=[{"id": 123, "title": "Test 1", "status": "locked"}],
    )
    # Configure validate_tests_belong_to_products to pass
    mock_test_repo.validate_tests_belong_to_products = AsyncMock()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Should not raise
    result = await service.get_product_quality_report(
        product_ids=[598],
        test_ids=[123],
    )

    assert result is not None
    assert "summary" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_product_quality_report_accepts_filters_without_test_ids() -> None:
    """Verify date/status filters without test_ids works correctly."""
    mock_test_repo, mock_bug_repo, mock_product_repo = setup_repo_mocks()

    service = MultiTestReportService(
        client=AsyncMock(),
        test_repo=mock_test_repo,
        bug_repo=mock_bug_repo,
        product_repo=mock_product_repo,
    )

    # Should not raise
    result = await service.get_product_quality_report(
        product_ids=[598],
        start_date="2024-01-01",
        end_date="2024-12-31",
        statuses=["locked", "archived"],
    )

    assert result is not None
    assert "summary" in result
