"""Unit tests for generate_quality_report MCP tool.

PQR Refactor: Updated for multi-product support and new interface.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from testio_mcp.exceptions import (
    ProductNotFoundException,
    TestIOAPIError,
    TestNotFoundException,
    TestProductMismatchError,
)
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
    total_tests: int = 0,
    tests_by_status: dict[str, int] | None = None,
    statuses_applied: list[str] | str = "all",
    total_bugs: int = 0,
    active_accepted: int = 0,
    auto_accepted: int = 0,
    rejected: int = 0,
    open_bugs: int = 0,
    period: str = "all time",
) -> dict:
    """Helper to create mock PQR summary with all required fields."""
    if product_ids is None:
        product_ids = [598]
    if products is None:
        products = [{"id": 598, "title": "Test Product"}]
    if tests_by_status is None:
        tests_by_status = {}

    total_accepted = active_accepted + auto_accepted
    reviewed = active_accepted + rejected

    bugs_by_status = {
        "active_accepted": active_accepted,
        "auto_accepted": auto_accepted,
        "rejected": rejected,
        "open": open_bugs,
    }

    total_bugs_count = active_accepted + auto_accepted + rejected + open_bugs
    rates: dict | None = None
    if total_bugs_count > 0:
        rates = {
            "active_acceptance_rate": active_accepted / total_bugs_count,
            "auto_acceptance_rate": auto_accepted / total_accepted if total_accepted > 0 else None,
            "overall_acceptance_rate": total_accepted / total_bugs_count,
            "rejection_rate": rejected / total_bugs_count,
        }

    user_reviewed = active_accepted + rejected
    review_rate = user_reviewed / total_bugs if total_bugs > 0 else None

    return {
        "product_ids": product_ids,
        "products": products,
        "total_tests": total_tests,
        "tests_by_status": tests_by_status,
        "statuses_applied": statuses_applied,
        "total_bugs": total_bugs,
        "bugs_by_status": bugs_by_status,
        "bugs_by_severity": {},
        "tests_by_type": {},
        "total_accepted": total_accepted,
        "reviewed": reviewed,
        "active_acceptance_rate": rates["active_acceptance_rate"] if rates else None,
        "auto_acceptance_rate": rates["auto_acceptance_rate"] if rates else None,
        "overall_acceptance_rate": rates["overall_acceptance_rate"] if rates else None,
        "rejection_rate": rates["rejection_rate"] if rates else None,
        "review_rate": review_rate,
        "avg_bugs_per_test": total_bugs / total_tests if total_tests > 0 else 0.0,
        "period": period,
        "health_indicators": {
            "rejection": "healthy",
            "auto_acceptance": "healthy",
            "review": "healthy",
        },
    }


def create_mock_service_result(
    product_ids: list[int] | None = None,
    products: list[dict] | None = None,
    test_ids: list[int] | None = None,
    by_product: list[dict] | None = None,
    **summary_kwargs: dict,
) -> dict:
    """Helper to create mock service result."""
    if product_ids is None:
        product_ids = [598]
    if products is None:
        products = [{"id": 598, "title": "Test Product"}]
    if test_ids is None:
        test_ids = []

    return {
        "summary": create_mock_summary(
            product_ids=product_ids, products=products, **summary_kwargs
        ),
        "product_ids": product_ids,
        "products": products,
        "test_ids": test_ids,
        "by_product": by_product,
        "thresholds": create_mock_thresholds(),
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_product_not_found_to_tool_error() -> None:
    """Verify ProductNotFoundException -> ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.side_effect = ProductNotFoundException(product_id=999)

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(product_ids=999, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower()
        assert "list_products" in error_msg.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_test_not_found_to_tool_error() -> None:
    """Verify TestNotFoundException -> ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.side_effect = TestNotFoundException(test_id=12345)

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(product_ids=598, test_ids=[12345], ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "12345" in error_msg
        assert "not found" in error_msg.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_test_product_mismatch_to_tool_error() -> None:
    """Verify TestProductMismatchError -> ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.side_effect = TestProductMismatchError(
        test_id=123,
        actual_product_id=999,
        allowed_product_ids=[598],
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(product_ids=598, test_ids=[123], ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "123" in error_msg
        assert "999" in error_msg
        assert "598" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_api_error_to_tool_error() -> None:
    """Verify TestIOAPIError -> ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.side_effect = TestIOAPIError(
        message="Server error", status_code=503
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(product_ids=123, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "503" in error_msg


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_single_product_id() -> None:
    """Verify tool accepts single int and normalizes to list."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result()

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids=598, ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["product_ids"] == [598]
        assert call_args.kwargs["test_ids"] is None
        assert call_args.kwargs["include_test_data"] is False  # MCP doesn't include test_data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_multiple_product_ids() -> None:
    """Verify tool passes multiple product IDs to service."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result(
        product_ids=[598, 599],
        products=[
            {"id": 598, "title": "Product A"},
            {"id": 599, "title": "Product B"},
        ],
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids=[598, 599], ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["product_ids"] == [598, 599]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_test_ids_filter() -> None:
    """Verify tool passes test_ids filter to service."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result(
        test_ids=[141290, 141285],
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids=598, test_ids=[141290, 141285], ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["test_ids"] == [141290, 141285]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rejects_empty_test_ids() -> None:
    """Verify tool rejects empty test_ids list."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(product_ids=598, test_ids=[], ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "empty" in error_msg.lower()
        assert "💡" in error_msg  # Suggests correct format


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_date_filters() -> None:
    """Verify tool passes date filters to service."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result(
        period="2024-01-01 to 2024-12-31",
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(
            product_ids=598,
            start_date="2024-01-01",
            end_date="2024-12-31",
            ctx=mock_ctx,
        )

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["start_date"] == "2024-01-01"
        assert call_args.kwargs["end_date"] == "2024-12-31"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delegates_with_status_filter() -> None:
    """Verify tool passes status filter to service."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result()

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids=598, statuses=["locked"], ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["statuses"] == ["locked"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parses_comma_separated_statuses() -> None:
    """Verify tool parses comma-separated status string."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result()

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids=598, statuses="locked,running", ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["statuses"] == ["locked", "running"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_returns_formatted_output() -> None:
    """Verify tool formats service result to Pydantic output."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result(
        product_ids=[598],
        products=[{"id": 598, "title": "Test Product"}],
        test_ids=[123, 456],
        total_tests=2,
        tests_by_status={"locked": 2},
        total_bugs=15,
        active_accepted=12,
        auto_accepted=3,
        period="2024-01-01 to 2024-12-31",
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await generate_quality_report(product_ids=598, ctx=mock_ctx)

        # Verify output structure - MCP response doesn't include test_data
        assert "summary" in result
        assert "product_ids" in result
        assert "products" in result
        assert "test_ids" in result
        assert "thresholds" in result

        # Verify summary fields
        assert result["summary"]["total_tests"] == 2
        assert result["summary"]["total_bugs"] == 15

        # Verify product_ids and test_ids in response
        assert result["product_ids"] == [598]
        assert result["test_ids"] == [123, 456]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handles_multi_product_by_product_breakdown() -> None:
    """Verify tool includes by_product for multi-product queries."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = {
        "summary": create_mock_summary(
            product_ids=[598, 599],
            products=[
                {"id": 598, "title": "Product A"},
                {"id": 599, "title": "Product B"},
            ],
            total_tests=5,
            total_bugs=20,
        ),
        "product_ids": [598, 599],
        "products": [
            {"id": 598, "title": "Product A"},
            {"id": 599, "title": "Product B"},
        ],
        "test_ids": [1, 2, 3, 4, 5],
        "by_product": [
            {
                "product_id": 598,
                "product_title": "Product A",
                "total_tests": 3,
                "total_bugs": 12,
                "bugs_by_severity": {},
                "tests_by_status": {"locked": 3},
                "tests_by_type": {},
            },
            {
                "product_id": 599,
                "product_title": "Product B",
                "total_tests": 2,
                "total_bugs": 8,
                "bugs_by_severity": {},
                "tests_by_status": {"locked": 2},
                "tests_by_type": {},
            },
        ],
        "thresholds": create_mock_thresholds(),
    }

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        result = await generate_quality_report(product_ids=[598, 599], ctx=mock_ctx)

        # Verify by_product breakdown is included
        assert "by_product" in result
        assert len(result["by_product"]) == 2
        assert result["by_product"][0]["product_id"] == 598
        assert result["by_product"][1]["product_id"] == 599


@pytest.mark.unit
@pytest.mark.asyncio
async def test_transforms_unexpected_error_to_tool_error() -> None:
    """Verify unexpected exceptions -> ToolError."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.side_effect = RuntimeError("Unexpected error")

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(product_ids=598, ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "Unexpected error" in error_msg


# ============================================================================
# Flexible Input Format Tests (parse_int_list_input support)
# ============================================================================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accepts_comma_separated_product_ids() -> None:
    """Verify tool accepts comma-separated string product_ids."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result(
        product_ids=[598, 599],
        products=[
            {"id": 598, "title": "Product A"},
            {"id": 599, "title": "Product B"},
        ],
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids="598,599", ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["product_ids"] == [598, 599]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accepts_json_array_product_ids() -> None:
    """Verify tool accepts JSON array string product_ids."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result(
        product_ids=[598, 599],
        products=[
            {"id": 598, "title": "Product A"},
            {"id": 599, "title": "Product B"},
        ],
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids="[598, 599]", ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["product_ids"] == [598, 599]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accepts_single_string_product_id() -> None:
    """Verify tool accepts single string product_id."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result()

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids="598", ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["product_ids"] == [598]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accepts_comma_separated_test_ids() -> None:
    """Verify tool accepts comma-separated string test_ids."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result(
        test_ids=[141290, 141285],
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids=598, test_ids="141290,141285", ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["test_ids"] == [141290, 141285]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accepts_json_array_test_ids() -> None:
    """Verify tool accepts JSON array string test_ids."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result(
        test_ids=[141290, 141285],
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids=598, test_ids="[141290, 141285]", ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["test_ids"] == [141290, 141285]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accepts_single_int_test_id() -> None:
    """Verify tool accepts single int test_id."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()
    mock_service.get_product_quality_report.return_value = create_mock_service_result(
        test_ids=[141290],
    )

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        await generate_quality_report(product_ids=598, test_ids=141290, ctx=mock_ctx)

        call_args = mock_service.get_product_quality_report.call_args
        assert call_args.kwargs["test_ids"] == [141290]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rejects_invalid_product_ids_format() -> None:
    """Verify tool rejects invalid product_ids format with clear error."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(product_ids="not_a_number", ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "Invalid product_ids" in error_msg
        assert "💡" in error_msg  # Suggests correct format


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rejects_invalid_test_ids_format() -> None:
    """Verify tool rejects invalid test_ids format with clear error."""
    mock_ctx = MagicMock()
    mock_service = AsyncMock()

    with patch(
        "testio_mcp.tools.product_quality_report_tool.get_service_context",
        return_value=mock_service_context(mock_service),
    ):
        with pytest.raises(ToolError) as exc_info:
            await generate_quality_report(product_ids=598, test_ids="not_a_number", ctx=mock_ctx)

        error_msg = str(exc_info.value)
        assert "❌" in error_msg
        assert "Invalid test_ids" in error_msg
        assert "💡" in error_msg  # Suggests correct format
