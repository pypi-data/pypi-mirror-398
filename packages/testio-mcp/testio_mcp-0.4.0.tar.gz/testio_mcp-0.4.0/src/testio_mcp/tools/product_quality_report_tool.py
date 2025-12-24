"""MCP tool for generating Product Quality Reports.

This module implements the generate_quality_report tool following the service
layer pattern (ADR-006). The tool is a thin wrapper that:
1. Validates input with Pydantic
2. Extracts dependencies from server context (ADR-007)
3. Delegates to MultiTestReportService
4. Converts exceptions to user-friendly error format

PQR Refactor: Multi-product support, test_ids filtering, cleaner MCP response.
"""

from datetime import datetime
from typing import Annotated, Any, Literal

from fastmcp import Context
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, field_validator, model_validator

from testio_mcp.exceptions import (
    ProductNotFoundException,
    TestIOAPIError,
    TestNotFoundException,
    TestProductMismatchError,
    ValidationError,
)
from testio_mcp.server import mcp
from testio_mcp.services.multi_test_report_service import MultiTestReportService
from testio_mcp.utilities import ProgressReporter, get_service_context
from testio_mcp.utilities.date_utils import parse_flexible_date
from testio_mcp.utilities.parsing import parse_int_list_input
from testio_mcp.utilities.schema_utils import inline_schema_refs

# Type aliases for valid values (using Literal to avoid $defs in JSON schema)
TestStatus = Literal[
    "running", "locked", "archived", "cancelled", "customer_finalized", "initialized"
]

HealthStatus = Literal["healthy", "warning", "critical", "unknown"]
ThresholdDirection = Literal["above", "below"]


class GenerateQualityReportInput(BaseModel):
    """Input validation for generate_quality_report tool.

    Validates:
    1. Per-field: Normalizes product_ids (int → list), validates test_ids
    2. Cross-field: Validates date range (start_date <= end_date) after parsing
    """

    product_ids: list[int] = Field(min_length=1)
    test_ids: list[int] | None = None
    start_date: str | None = None
    end_date: str | None = None
    statuses: str | list[str] | None = None
    output_file: str | None = None

    @field_validator("product_ids", mode="before")
    @classmethod
    def normalize_product_ids(cls, v: int | list[int]) -> list[int]:
        """Normalize product_ids to list and dedupe.

        Args:
            v: Single int or list of ints

        Returns:
            Deduped list of product IDs
        """
        if isinstance(v, int):
            return [v]
        # Dedupe while preserving order
        return list(dict.fromkeys(v))

    @field_validator("test_ids", mode="before")
    @classmethod
    def validate_test_ids(cls, v: list[int] | None) -> list[int] | None:
        """Validate test_ids: reject empty list, dedupe non-empty.

        Args:
            v: List of test IDs or None

        Returns:
            Deduped list of test IDs or None

        Raises:
            ValueError: If test_ids is empty list
        """
        if v is None:
            return None
        if len(v) == 0:
            raise ValueError("Empty test_ids invalid. Use None for all tests")
        # Dedupe while preserving order
        return list(dict.fromkeys(v))

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate date format and reject ambiguous year-only inputs.

        Args:
            v: Date string value

        Returns:
            Original date string if valid (or None)

        Raises:
            ValueError: If date is year-only format (ambiguous)
        """
        if v is None:
            return v

        try:
            parse_flexible_date(v, start_of_day=True)
            return v
        except ToolError as e:
            raise ValueError(str(e)) from e

    @model_validator(mode="after")
    def validate_date_range(self) -> "GenerateQualityReportInput":
        """Validate that start_date <= end_date after parsing flexible formats.

        Raises:
            ValueError: If start_date > end_date or date parsing fails
        """
        if self.start_date and self.end_date:
            try:
                parsed_start = parse_flexible_date(self.start_date, start_of_day=True)
                parsed_end = parse_flexible_date(self.end_date, start_of_day=False)

                start_dt = datetime.fromisoformat(parsed_start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(parsed_end.replace("Z", "+00:00"))

                if start_dt > end_dt:
                    raise ValueError(
                        f"start_date is after end_date: "
                        f"start_date='{self.start_date}' ({parsed_start}) > "
                        f"end_date='{self.end_date}' ({parsed_end}). "
                        f"Ensure start_date comes before or equals end_date."
                    )
            except ToolError as e:
                raise ValueError(str(e)) from e

        return self


# Output Models


class ProductInfo(BaseModel):
    """Product info in response."""

    id: int = Field(gt=0, description="Product ID")
    title: str = Field(description="Product name/title")


class MetricThreshold(BaseModel):
    """Threshold configuration for a single metric."""

    warning: float = Field(ge=0.0, le=1.0, description="Warning threshold")
    critical: float = Field(ge=0.0, le=1.0, description="Critical threshold")
    direction: ThresholdDirection = Field(description="'above' = high is bad, 'below' = low is bad")


class PlaybookThresholdsOutput(BaseModel):
    """Playbook threshold configuration included in response for transparency."""

    rejection_rate: MetricThreshold = Field(description="Rejection rate thresholds")
    auto_acceptance_rate: MetricThreshold = Field(description="Auto-acceptance rate thresholds")
    review_rate: MetricThreshold = Field(description="Review rate thresholds")


class ProductBreakdown(BaseModel):
    """Per-product breakdown for multi-product queries."""

    product_id: int = Field(gt=0, description="Product ID")
    product_title: str = Field(description="Product name/title")
    total_tests: int = Field(ge=0, description="Tests in this product")
    total_bugs: int = Field(ge=0, description="Total bugs in this product")
    bugs_by_severity: dict[str, int] = Field(default_factory=dict, description="Bugs by severity")
    tests_by_status: dict[str, int] = Field(default_factory=dict, description="Tests by status")
    tests_by_type: dict[str, int] = Field(default_factory=dict, description="Tests by type")
    health_indicators: dict[str, HealthStatus] = Field(
        default_factory=dict, description="Health status for key metrics"
    )
    active_acceptance_rate: float | None = Field(
        default=None, description="active_accepted / total_bugs", ge=0.0, le=1.0
    )
    auto_acceptance_rate: float | None = Field(
        default=None, description="auto_accepted / (active + auto)", ge=0.0, le=1.0
    )
    overall_acceptance_rate: float | None = Field(
        default=None, description="(active + auto) / total_bugs", ge=0.0, le=1.0
    )
    rejection_rate: float | None = Field(
        default=None, description="rejected / total_bugs", ge=0.0, le=1.0
    )
    review_rate: float | None = Field(
        default=None, description="(active + rejected) / total_bugs", ge=0.0, le=1.0
    )


class QualityReportSummary(BaseModel):
    """Summary metrics aggregated across all products and tests."""

    product_ids: list[int] = Field(description="Product IDs included in report")
    products: list[ProductInfo] = Field(description="Products included in report")
    total_tests: int = Field(ge=0, description="Tests in report")
    tests_by_status: dict[str, int] = Field(description="Tests by status")
    statuses_applied: list[str] | str = Field(
        description="Statuses included (default: excludes initialized, cancelled)"
    )
    total_bugs: int = Field(ge=0, description="Total bugs")
    bugs_by_status: dict[str, int] = Field(description="Bugs by classification")
    bugs_by_severity: dict[str, int] = Field(default_factory=dict, description="Bugs by severity")
    tests_by_type: dict[str, int] = Field(default_factory=dict, description="Tests by type")
    total_accepted: int = Field(ge=0, description="Active + auto")
    reviewed: int = Field(ge=0, description="Active + rejected")
    active_acceptance_rate: float | None = Field(
        default=None, description="active_accepted / total_bugs", ge=0.0, le=1.0
    )
    auto_acceptance_rate: float | None = Field(
        default=None, description="auto_accepted / (active + auto)", ge=0.0, le=1.0
    )
    overall_acceptance_rate: float | None = Field(
        default=None, description="(active + auto) / total_bugs", ge=0.0, le=1.0
    )
    rejection_rate: float | None = Field(
        default=None, description="rejected / total_bugs", ge=0.0, le=1.0
    )
    review_rate: float | None = Field(
        default=None, description="(active + rejected) / total_bugs", ge=0.0, le=1.0
    )
    avg_bugs_per_test: float | None = Field(
        default=None, description="Average bugs per test", ge=0.0
    )
    period: str = Field(description="Report period")
    health_indicators: dict[str, HealthStatus] = Field(description="Health status for key metrics")


class GenerateQualityReportOutput(BaseModel):
    """Product Quality Report output."""

    summary: QualityReportSummary = Field(description="Aggregate metrics")
    product_ids: list[int] = Field(description="Product IDs in report")
    products: list[ProductInfo] = Field(description="Products in report")
    test_ids: list[int] = Field(description="Test IDs included in report")
    by_product: list[ProductBreakdown] | None = Field(
        default=None, description="Per-product breakdown (multi-product queries only)"
    )
    thresholds: PlaybookThresholdsOutput = Field(description="Playbook threshold configuration")

    # File export fields
    file_path: str | None = Field(default=None, description="Export file path")
    record_count: int | None = Field(default=None, ge=0, description="Tests exported")
    file_size_bytes: int | None = Field(default=None, ge=0, description="File size (bytes)")
    format: Literal["json"] | None = Field(default=None, description="File format")


# MCP Tool
@mcp.tool(output_schema=inline_schema_refs(GenerateQualityReportOutput.model_json_schema()))
async def generate_quality_report(
    product_ids: Annotated[
        list[int] | str | int,
        Field(
            description=(
                "Product ID(s) to analyze. Accepts: list [598, 599], single int 598, "
                "comma-separated string '598,599', or JSON array '[598, 599]'"
            ),
            examples=[598, [598, 599], "598,599", "[598, 599]"],
        ),
    ],
    ctx: Context,
    test_ids: Annotated[
        list[int] | str | int | None,
        Field(
            description=(
                "Filter to specific test IDs. Must belong to product_ids. "
                "Accepts: list [141290], single int, comma-separated '141290,141285', "
                "or JSON array '[141290, 141285]'"
            ),
            examples=[[141290, 141285], "141290,141285"],
        ),
    ] = None,
    start_date: Annotated[
        str | None,
        Field(
            description="Start date (ISO 8601 or business terms). No year-only values",
            examples=["2025-07-01", "last 30 days", "this quarter"],
        ),
    ] = None,
    end_date: Annotated[
        str | None,
        Field(
            description="End date (ISO 8601 or business terms). No year-only values",
            examples=["2025-10-31", "today"],
        ),
    ] = None,
    statuses: Annotated[
        str | list[TestStatus] | None,
        Field(
            description=(
                "Filter by status. Default: excludes initialized, cancelled. "
                "Comma-separated or array"
            ),
            examples=["locked", "running,locked", ["locked"], ["running", "locked"]],
        ),
    ] = None,
    output_file: Annotated[
        str | None,
        Field(
            description=(
                "Export to file (includes full per-test data). "
                "Relative paths → ~/.testio-mcp/reports/"
            ),
            examples=["canva-q3-2025.json", "q3-2025/portfolio.json"],
        ),
    ] = None,
) -> dict[str, Any]:
    """Generate quality report with bug metrics and acceptance rates.

    Supports single-product or multi-product (portfolio) analysis.
    Returns aggregate metrics without per-test data for token efficiency.

    For per-test data:
    - Use output_file to export full report to JSON
    - Use REST API: GET /api/quality-report?product_ids=...

    Date filters support ISO 8601 or business terms (e.g., 'last 30 days').
    Date filtering is based on test end_at (when test completed).
    Default excludes initialized/cancelled tests (executed tests only).

    Uses intelligent caching (10-30s for 100+ tests). For fresh data, call sync_data first.
    """
    # Normalize product_ids input (accepts string, int, list, comma-separated, JSON array)
    try:
        product_ids_list = parse_int_list_input(product_ids)
        if product_ids_list is None:
            raise ValueError("product_ids is required and cannot be empty")
    except ValueError as e:
        raise ToolError(
            f"❌ Invalid product_ids format\n"
            f"ℹ️ {e}\n"
            f"💡 Use: [598, 599], 598, '598,599', or '[598, 599]'"
        ) from e

    # Normalize test_ids input (same flexible formats)
    # Reject empty list explicitly (parse_int_list_input converts [] → None)
    if isinstance(test_ids, list) and len(test_ids) == 0:
        raise ToolError(
            "❌ Invalid test_ids: empty list\n"
            "ℹ️ Empty test_ids list is not allowed\n"
            "💡 Omit test_ids parameter to include all tests, or provide specific IDs"
        )
    try:
        test_ids_list = parse_int_list_input(test_ids)
    except ValueError as e:
        raise ToolError(
            f"❌ Invalid test_ids format\n"
            f"ℹ️ {e}\n"
            f"💡 Use: [141290], 141290, '141290,141285', or '[141290, 141285]'"
        ) from e

    # Convert TestStatus Literal types to strings for Pydantic model
    statuses_for_validation: str | list[str] | None = None
    if statuses is not None:
        if isinstance(statuses, str):
            statuses_for_validation = statuses
        else:
            statuses_for_validation = [str(s) for s in statuses]

    try:
        validated_input = GenerateQualityReportInput(
            product_ids=product_ids_list,
            test_ids=test_ids_list,
            start_date=start_date,
            end_date=end_date,
            statuses=statuses_for_validation,
            output_file=output_file,
        )
    except ValueError as e:
        error_msg = str(e)
        if "start_date is after end_date" in error_msg:
            raise ToolError(
                f"❌ Invalid date range: {error_msg}\n"
                f"ℹ️  The start date must come before or equal to the end date\n"
                f"💡 For single-day reports, use the same date for both parameters."
            ) from e
        if "Empty test_ids" in error_msg:
            raise ToolError(
                f"❌ Invalid test_ids: {error_msg}\n"
                f"ℹ️  Empty test_ids list is not allowed\n"
                f"💡 Omit test_ids parameter to include all tests, or provide specific IDs."
            ) from e
        raise ToolError(
            f"❌ Invalid input: {error_msg}\n"
            f"ℹ️  Check your parameter values\n"
            f"💡 Ensure all parameters are in the correct format"
        ) from e

    reporter = ProgressReporter.from_context(ctx)

    # Create service with managed AsyncSession lifecycle
    async with get_service_context(ctx, MultiTestReportService) as service:
        # Parse comma-separated string to list if needed
        statuses_list: list[str] | None = None
        if validated_input.statuses is not None:
            if isinstance(validated_input.statuses, str):
                # Filter empty strings (e.g., "running,," → ["running"])
                statuses_list = [
                    s.strip() for s in validated_input.statuses.split(",") if s.strip()
                ]
            else:
                # List of TestStatus literals - convert to strings
                statuses_list = [str(s) for s in validated_input.statuses]

            # Reject empty list after filtering (e.g., ",,")
            if statuses_list is not None and len(statuses_list) == 0:
                raise ToolError(
                    "❌ Invalid statuses: empty after parsing\n"
                    "ℹ️ Input like ',,' or whitespace-only yields no valid statuses\n"
                    "💡 Omit the parameter to use default (executed tests only)"
                )

        try:
            service_result = await service.get_product_quality_report(
                product_ids=validated_input.product_ids,
                test_ids=validated_input.test_ids,
                start_date=start_date,
                end_date=end_date,
                statuses=statuses_list,
                output_file=output_file,
                progress=reporter,
                include_test_data=False,  # MCP tool doesn't include per-test data
            )

            # Build thresholds output from service result
            thresholds_data = service_result["thresholds"]
            thresholds_output = PlaybookThresholdsOutput(
                rejection_rate=MetricThreshold(
                    warning=thresholds_data["rejection_rate"]["warning"],
                    critical=thresholds_data["rejection_rate"]["critical"],
                    direction=thresholds_data["rejection_rate"]["direction"],
                ),
                auto_acceptance_rate=MetricThreshold(
                    warning=thresholds_data["auto_acceptance_rate"]["warning"],
                    critical=thresholds_data["auto_acceptance_rate"]["critical"],
                    direction=thresholds_data["auto_acceptance_rate"]["direction"],
                ),
                review_rate=MetricThreshold(
                    warning=thresholds_data["review_rate"]["warning"],
                    critical=thresholds_data["review_rate"]["critical"],
                    direction=thresholds_data["review_rate"]["direction"],
                ),
            )

            # Build products list
            products_list = [
                ProductInfo(id=p["id"], title=p["title"]) for p in service_result["products"]
            ]

            # Build by_product list (if present)
            by_product_list: list[ProductBreakdown] | None = None
            if service_result.get("by_product"):
                by_product_list = [
                    ProductBreakdown(
                        product_id=bp["product_id"],
                        product_title=bp["product_title"],
                        total_tests=bp["total_tests"],
                        total_bugs=bp["total_bugs"],
                        bugs_by_severity=bp.get("bugs_by_severity", {}),
                        tests_by_status=bp.get("tests_by_status", {}),
                        tests_by_type=bp.get("tests_by_type", {}),
                        health_indicators=bp.get("health_indicators", {}),
                        active_acceptance_rate=bp.get("active_acceptance_rate"),
                        auto_acceptance_rate=bp.get("auto_acceptance_rate"),
                        overall_acceptance_rate=bp.get("overall_acceptance_rate"),
                        rejection_rate=bp.get("rejection_rate"),
                        review_rate=bp.get("review_rate"),
                    )
                    for bp in service_result["by_product"]
                ]

            # Build summary
            summary = service_result["summary"]
            summary_output = QualityReportSummary(
                product_ids=summary.get("product_ids", service_result["product_ids"]),
                products=[
                    ProductInfo(id=p["id"], title=p["title"])
                    for p in summary.get("products", service_result["products"])
                ],
                total_tests=summary["total_tests"],
                tests_by_status=summary["tests_by_status"],
                statuses_applied=summary["statuses_applied"],
                total_bugs=summary["total_bugs"],
                bugs_by_status=summary["bugs_by_status"],
                bugs_by_severity=summary.get("bugs_by_severity", {}),
                tests_by_type=summary.get("tests_by_type", {}),
                total_accepted=summary["total_accepted"],
                reviewed=summary["reviewed"],
                active_acceptance_rate=summary.get("active_acceptance_rate"),
                auto_acceptance_rate=summary.get("auto_acceptance_rate"),
                overall_acceptance_rate=summary.get("overall_acceptance_rate"),
                rejection_rate=summary.get("rejection_rate"),
                review_rate=summary.get("review_rate"),
                avg_bugs_per_test=summary.get("avg_bugs_per_test"),
                period=summary["period"],
                health_indicators=summary["health_indicators"],
            )

            # Build output
            output = GenerateQualityReportOutput(
                summary=summary_output,
                product_ids=service_result["product_ids"],
                products=products_list,
                test_ids=service_result["test_ids"],
                by_product=by_product_list,
                thresholds=thresholds_output,
                # File export fields (if applicable)
                file_path=service_result.get("file_path"),
                record_count=service_result.get("record_count"),
                file_size_bytes=service_result.get("file_size_bytes"),
                format=service_result.get("format"),
            )

            return output.model_dump(by_alias=True, exclude_none=True)

        except ValidationError as e:
            # Convert domain validation error to ToolError
            raise ToolError(
                f"❌ Validation error: {e.message}\n"
                f"ℹ️  Field: {e.field}\n"
                f"💡 Check your input parameters"
            ) from e

        except ProductNotFoundException as e:
            raise ToolError(
                f"❌ Product ID '{e.product_id}' not found\n"
                f"ℹ️  This product may not exist or you don't have access to it\n"
                f"💡 Use the list_products tool to see available products"
            ) from e

        except TestNotFoundException as e:
            raise ToolError(
                f"❌ Test ID '{e.test_id}' not found\n"
                f"ℹ️  This test may not exist or may not be synced yet\n"
                f"💡 Use list_tests to see available tests for the product"
            ) from e

        except TestProductMismatchError as e:
            raise ToolError(
                f"❌ Test {e.test_id} belongs to product {e.actual_product_id}, "
                f"not in product_ids {e.allowed_product_ids}\n"
                f"ℹ️  The test_ids filter must only include tests from the specified products\n"
                f"💡 Either remove test ID {e.test_id} from test_ids, "
                f"or add product {e.actual_product_id} to product_ids"
            ) from e

        except TestIOAPIError as e:
            raise ToolError(
                f"❌ API error: {e.message}\n"
                f"ℹ️  HTTP status code: {e.status_code}\n"
                f"💡 Check API status and try again. If the problem persists, contact support."
            ) from e

        except (PermissionError, OSError) as e:
            error_type = "permission" if isinstance(e, PermissionError) else "I/O"
            raise ToolError(
                f"❌ File export failed: {error_type} error\n"
                f"ℹ️  Cannot write to file: {str(e)}\n"
                f"💡 Check file permissions and disk space. "
                f"For relative paths, ensure ~/.testio-mcp/reports/ is writable."
            ) from e

        except ValueError as e:
            if "path" in str(e).lower() or "extension" in str(e).lower():
                raise ToolError(
                    f"❌ Invalid output file path\n"
                    f"ℹ️  {str(e)}\n"
                    f"💡 Use absolute paths or relative paths under ~/.testio-mcp/reports/. "
                    f"Supported extensions: .json"
                ) from e
            raise

        except ToolError:
            raise

        except Exception as e:
            raise ToolError(
                f"❌ Unexpected error: {str(e)}\n"
                f"ℹ️  An unexpected error occurred while generating PQR\n"
                f"💡 Please try again or contact support if the problem persists"
            ) from e
