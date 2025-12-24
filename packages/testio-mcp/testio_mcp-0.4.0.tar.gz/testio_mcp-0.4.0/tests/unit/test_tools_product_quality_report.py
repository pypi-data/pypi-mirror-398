"""Unit tests for generate_quality_report tool file export functionality.

PQR Refactor: Updated for multi-product support and new interface.
Tests verify error transformations, parameter validation, and service delegation.
"""

from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.tools.product_quality_report_tool import (
    generate_quality_report as generate_quality_report_tool,
)
from tests.unit.test_utils import mock_service_context

generate_quality_report = generate_quality_report_tool.fn


def create_mock_thresholds() -> dict:
    """Helper to create mock playbook thresholds."""
    return {
        "rejection_rate": {"warning": 0.20, "critical": 0.35, "direction": "above"},
        "auto_acceptance_rate": {"warning": 0.20, "critical": 0.40, "direction": "above"},
        "review_rate": {"warning": 0.80, "critical": 0.60, "direction": "below"},
    }


def create_mock_summary(
    product_ids: list[int] | None = None,
    products: list[dict] | None = None,
    **kwargs: dict,
) -> dict:
    """Helper to create mock summary."""
    if product_ids is None:
        product_ids = [123]
    if products is None:
        products = [{"id": 123, "title": "Test Product"}]

    return {
        "product_ids": product_ids,
        "products": products,
        "total_tests": kwargs.get("total_tests", 2),
        "tests_by_status": kwargs.get("tests_by_status", {"locked": 2}),
        "statuses_applied": kwargs.get("statuses_applied", "all"),
        "total_bugs": kwargs.get("total_bugs", 5),
        "bugs_by_status": kwargs.get(
            "bugs_by_status",
            {
                "active_accepted": 3,
                "auto_accepted": 1,
                "rejected": 1,
                "open": 0,
            },
        ),
        "bugs_by_severity": {},
        "tests_by_type": {},
        "total_accepted": 4,
        "reviewed": 4,
        "active_acceptance_rate": 0.6,
        "auto_acceptance_rate": 0.25,
        "overall_acceptance_rate": 0.8,
        "rejection_rate": 0.2,
        "review_rate": 0.8,
        "avg_bugs_per_test": 2.5,
        "period": "all time",
        "health_indicators": {
            "rejection": "healthy",
            "auto_acceptance": "healthy",
            "review": "healthy",
        },
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_delegates_to_service(tmp_path: Path) -> None:
    """Verify tool delegates file export to service layer."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()

    mock_service.get_product_quality_report.return_value = {
        "file_path": str(tmp_path / "report.json"),
        "summary": create_mock_summary(),
        "product_ids": [123],
        "products": [{"id": 123, "title": "Test Product"}],
        "test_ids": [1, 2],
        "by_product": None,
        "record_count": 2,
        "file_size_bytes": 1024,
        "format": "json",
        "thresholds": create_mock_thresholds(),
    }

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await generate_quality_report(
            product_ids=123,
            output_file="report.json",
            ctx=mock_ctx,
        )

        mock_service.get_product_quality_report.assert_called_once_with(
            product_ids=[123],
            test_ids=None,
            start_date=None,
            end_date=None,
            statuses=None,
            output_file="report.json",
            progress=ANY,
            include_test_data=False,
        )

        assert "file_path" in result
        assert "summary" in result
        assert "record_count" in result
        assert "file_size_bytes" in result
        assert "format" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_permission_error_transformation() -> None:
    """Verify PermissionError is transformed to ToolError with clear message."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.side_effect = PermissionError("Permission denied")

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(
                product_ids=123,
                output_file="report.json",
                ctx=mock_ctx,
            )

        error_msg = str(exc_info.value)
        assert "permission" in error_msg.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_oserror_transformation() -> None:
    """Verify OSError (disk full) is transformed to ToolError with helpful message."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.side_effect = OSError("No space left on device")

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(
                product_ids=123,
                output_file="report.json",
                ctx=mock_ctx,
            )

        error_msg = str(exc_info.value)
        assert "I/O" in error_msg or "disk" in error_msg.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_valueerror_path_transformation() -> None:
    """Verify ValueError (invalid path) is transformed to ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.side_effect = ValueError("Path traversal detected")

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(
                product_ids=123,
                output_file="../../../etc/passwd",
                ctx=mock_ctx,
            )

        error_msg = str(exc_info.value)
        assert "Invalid output file path" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_export_valueerror_date_parsing_caught_early() -> None:
    """Verify date parsing errors are caught by Pydantic validation."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError, match="Invalid input"):
            await generate_quality_report(
                product_ids=123,
                start_date="invalid-date",
                ctx=mock_ctx,
            )

        mock_service.get_product_quality_report.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_returns_json_response_without_file() -> None:
    """Verify tool returns JSON response when output_file is None."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()

    mock_service.get_product_quality_report.return_value = {
        "summary": create_mock_summary(),
        "product_ids": [123],
        "products": [{"id": 123, "title": "Test Product"}],
        "test_ids": [1, 2],
        "by_product": None,
        "thresholds": create_mock_thresholds(),
    }

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await generate_quality_report(
            product_ids=123,
            output_file=None,
            ctx=mock_ctx,
        )

        assert "summary" in result
        assert "product_ids" in result
        assert "test_ids" in result
        assert "thresholds" in result

        # NOT file metadata structure
        assert "file_path" not in result
        assert "record_count" not in result
        assert "file_size_bytes" not in result
        assert "format" not in result
