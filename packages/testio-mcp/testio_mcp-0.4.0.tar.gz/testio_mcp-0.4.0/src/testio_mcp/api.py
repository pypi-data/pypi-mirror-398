"""FastAPI wrapper for hybrid MCP + REST API server.

This module provides a FastAPI application that serves both:
1. MCP protocol at /mcp (for AI clients like Claude, Cursor)
2. REST API at /api/* (for web apps, curl, Postman)
3. Swagger documentation at /docs (auto-generated)
4. Health check at /health (for monitoring)

Architecture (STORY-023f):
- Shares lifespan handler with MCP server (single resource set)
- Reuses existing services (TestService, ProductService, etc.)
- Delegates all business logic to service layer
- Exception handlers convert domain exceptions to HTTP status codes

Key Design Decisions:
- NESTED lifespan pattern: MCP lifespan is outer context
- No CORS middleware (FastMCP handles it internally)
- FastAPI response_model uses Pydantic models directly (no inline_schema_refs needed)
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import monotonic
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from testio_mcp.config import settings
from testio_mcp.exceptions import (
    BugNotFoundException,
    FeatureNotFoundException,
    InvalidSearchQueryError,
    ProductNotFoundException,
    TestIOAPIError,
    TestNotFoundException,
    TestProductMismatchError,
    UserNotFoundException,
    ValidationError,
)
from testio_mcp.schemas.api import (
    ListBugsOutput,
    ListTestsOutput,
    PaginationInfo,
    ProductInfoSummary,
    TestStatusOutput,
)
from testio_mcp.schemas.constants import VALID_TEST_STATUSES
from testio_mcp.schemas.playbook_thresholds import PlaybookThresholds
from testio_mcp.server import ServerContext, mcp
from testio_mcp.server import lifespan as mcp_lifespan
from testio_mcp.services.analytics_service import AnalyticsService
from testio_mcp.services.bug_service import BugService
from testio_mcp.services.diagnostics_service import DiagnosticsService, ServerDiagnostics
from testio_mcp.services.feature_service import FeatureService
from testio_mcp.services.multi_test_report_service import MultiTestReportService
from testio_mcp.services.product_service import ProductService
from testio_mcp.services.search_service import SearchService
from testio_mcp.services.test_service import TestService
from testio_mcp.services.user_service import UserService
from testio_mcp.tools.cache_tools import ProblematicTestsOutput
from testio_mcp.tools.feature_summary_tool import FeatureSummaryOutput
from testio_mcp.tools.get_bug_summary_tool import BugSummaryOutput
from testio_mcp.tools.list_features_tool import ListFeaturesOutput
from testio_mcp.tools.list_products_tool import ListProductsOutput
from testio_mcp.tools.product_quality_report_tool import (
    MetricThreshold,
    PlaybookThresholdsOutput,
    ProductBreakdown,
    ProductInfo,
    QualityReportSummary,
)
from testio_mcp.tools.product_summary_tool import ProductSummaryOutput
from testio_mcp.tools.search_tool import SearchOutput
from testio_mcp.tools.user_summary_tool import UserSummaryOutput
from testio_mcp.transformers import to_test_summary_list
from testio_mcp.utilities import parse_status_input
from testio_mcp.utilities.service_helpers import get_service_context_from_server_context


# Pydantic models for REST API request/response
class DatabaseInfo(BaseModel):
    """Database connection and statistics."""

    connected: bool = Field(description="Database connection status", examples=[True])
    total_tests: int | None = Field(
        default=None, description="Total tests in database", examples=[712]
    )
    total_products: int | None = Field(
        default=None, description="Total products in database", examples=[6]
    )
    database_size_mb: float | None = Field(
        default=None, description="Database size in MB", examples=[309.18]
    )


class HealthCheckOutput(BaseModel):
    """Health check response."""

    status: str = Field(description="Health status", examples=["healthy"])
    version: str = Field(description="Server version", examples=["0.4.0"])
    uptime_seconds: float | None = Field(
        default=None, description="Server uptime in seconds", examples=[1234.56]
    )
    database: DatabaseInfo = Field(description="Database connection and stats")
    error: str | None = Field(default=None, description="Error message if unhealthy")


class MetricThresholdOutput(BaseModel):
    """Threshold configuration for a single metric."""

    warning: float = Field(
        ge=0.0,
        le=1.0,
        description="Warning threshold (0.0-1.0)",
        examples=[0.20],
    )
    critical: float = Field(
        ge=0.0,
        le=1.0,
        description="Critical threshold (0.0-1.0)",
        examples=[0.35],
    )
    direction: str = Field(
        description="Threshold direction: 'above' = high is bad, 'below' = low is bad",
        examples=["above"],
    )


class ThresholdsOutput(BaseModel):
    """Playbook threshold configuration for health indicators.

    These thresholds determine when metrics trigger warning/critical status:
    - rejection_rate: High rejection indicates noisy cycles or unclear instructions
    - auto_acceptance_rate: High auto-acceptance indicates bandwidth/engagement issues
    - review_rate: Low review rate indicates customer disengagement

    Default thresholds (from CSM Playbook):
        | Metric              | Healthy | Warning | Critical |
        |---------------------|---------|---------|----------|
        | rejection_rate      | <20%    | 20-35%  | >35%     |
        | auto_acceptance_rate| <20%    | 20-40%  | >40%     |
        | review_rate         | >80%    | 60-80%  | <60%     |
    """

    rejection_rate: MetricThresholdOutput = Field(
        description="Rejection rate thresholds (high is bad)"
    )
    auto_acceptance_rate: MetricThresholdOutput = Field(
        description="Auto-acceptance rate thresholds (high is bad)"
    )
    review_rate: MetricThresholdOutput = Field(description="Review rate thresholds (low is bad)")


class TestDataItem(BaseModel):
    """Per-test data in REST quality report response."""

    test_id: int = Field(gt=0, description="Test ID")
    product_id: int | None = Field(default=None, gt=0, description="Product ID")
    title: str = Field(description="Test title")
    status: str = Field(description="Test status")
    testing_type: str | None = Field(
        default=None, description="Testing type (rapid, focused, coverage, usability)"
    )
    start_at: str | None = Field(default=None, description="Test start date")
    end_at: str | None = Field(default=None, description="Test end date")
    bugs_count: int = Field(ge=0, description="Total bugs for this test")
    bugs: dict[str, int] = Field(description="Bug counts by classification")
    test_environment: dict[str, Any] | None = Field(
        default=None, description="Test environment info (id, title)"
    )
    active_acceptance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    auto_acceptance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    overall_acceptance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    rejection_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    review_rate: float | None = Field(default=None, ge=0.0, le=1.0)


class QualityReportRESTOutput(BaseModel):
    """Product Quality Report REST API output (includes test_data)."""

    summary: QualityReportSummary = Field(description="Aggregate metrics")
    product_ids: list[int] = Field(description="Product IDs in report")
    products: list[ProductInfo] = Field(description="Products in report")
    test_ids: list[int] = Field(description="Test IDs included in report")
    by_product: list[ProductBreakdown] | None = Field(
        default=None, description="Per-product breakdown (multi-product queries only)"
    )
    test_data: list[TestDataItem] | None = Field(
        default=None, description="Per-test data (REST API only)"
    )
    thresholds: PlaybookThresholdsOutput = Field(description="Playbook threshold configuration")

    # File export fields
    file_path: str | None = Field(default=None, description="Export file path")
    record_count: int | None = Field(default=None, ge=0, description="Tests exported")
    file_size_bytes: int | None = Field(default=None, ge=0, description="File size (bytes)")
    format: str | None = Field(default=None, description="File format")


class QueryMetricsInput(BaseModel):
    """Request body for POST /api/analytics/query."""

    metrics: list[str] = Field(
        min_length=1,
        description="Metrics to measure",
        examples=[["bug_count"]],
    )
    dimensions: list[str] = Field(
        min_length=1,
        max_length=2,
        description="Dimensions to group by (max 2)",
        examples=[["feature"]],
    )
    filters: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Filter by dimension values, product_id, or status. "
            "Default status filter: excludes initialized and cancelled tests. "
            "Override with status=['initialized', 'cancelled', ...] to include them."
        ),
        examples=[
            {"severity": "critical"},
            {"product_id": 598},
            {"status": ["initialized", "cancelled"]},
        ],
    )
    start_date: str | None = Field(
        default=None,
        description="Start date (ISO or natural language). Filters on test end_at.",
        examples=["2024-11-01", "3 months ago"],
    )
    end_date: str | None = Field(
        default=None,
        description="End date (ISO or natural language). Filters on test end_at.",
        examples=["today"],
    )
    sort_by: str | None = Field(
        default=None,
        description="Sort by metric/dimension",
        examples=["bug_count"],
    )
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order (asc or desc)",
    )
    limit: int | None = Field(
        default=None,
        ge=1,
        description="Max rows (default: 1000)",
        examples=[10],
    )
    tests_limit: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Limit metrics to most recent N tests (by end_at DESC). "
            "If combined with date filters, applies limit after date filtering."
        ),
        examples=[5, 10],
    )

    @field_validator("filters", mode="before")
    @classmethod
    def validate_status_values(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate status filter values if present.

        Args:
            v: Filters dictionary

        Returns:
            Original filters if valid

        Raises:
            ValueError: If status contains invalid values
        """
        if v is None:
            return v

        if "status" in v:
            status_values = v["status"]
            # Convert single string to list for validation
            if isinstance(status_values, str):
                status_values = [status_values]

            if not isinstance(status_values, list):
                raise ValueError(
                    f"status filter must be a string or list of strings, got {type(status_values)}"
                )

            # Validate each status value
            invalid = [s for s in status_values if s not in VALID_TEST_STATUSES]
            if invalid:
                raise ValueError(
                    f"Invalid status values: {invalid}. "
                    f"Valid statuses: {', '.join(VALID_TEST_STATUSES)}"
                )

        return v


# Create MCP HTTP app with path='/' since it will be mounted at /mcp
# The path parameter tells MCP what internal path to use
# When mounted at /mcp, requests to /mcp/ will be handled
mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def hybrid_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Share MCP lifespan with FastAPI.

    CRITICAL: This ensures single TestIOClient/PersistentCache instance
    and one set of background tasks (no duplication).

    Pattern: NESTED async context manager
    - MCP server lifespan is OUTER context (initializes resources)
    - MCP app lifespan is INNER context (initializes session manager)
    - Ensures resources exist before FastAPI routes start
    - ServerContext stored in app.state for REST endpoint access

    Source: https://gofastmcp.com/integrations/fastapi.md
    """
    start_time = monotonic()

    # Use the same lifespan as MCP (single resource set)
    # CRITICAL: Must nest both mcp_lifespan AND mcp_app.lifespan
    async with mcp_lifespan(mcp) as server_ctx:
        # Initialize MCP app's session manager
        async with mcp_app.lifespan(app):
            # Expose ServerContext to FastAPI endpoints
            app.state.server_context = server_ctx
            app.state.start_time = start_time
            yield


# Create FastAPI wrapper
api = FastAPI(
    title="TestIO MCP Server",
    description="Hybrid MCP + REST API for TestIO Customer API",
    version="0.4.0",
    lifespan=hybrid_lifespan,  # ⚠️ CRITICAL: Share lifespan
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@api.middleware("http")
async def trailing_slash_middleware(request: Request, call_next: Any) -> Any:
    """Rewrite /mcp to /mcp/ to avoid 307 redirect for mounted MCP app.

    This allows MCP clients that don't follow redirects to connect to /mcp
    without the trailing slash. Updates both scope["path"] and scope["raw_path"]
    for internal consistency and to work correctly behind proxies.
    """
    # Check scope["path"] directly (works correctly behind proxies)
    if request.scope["path"] == "/mcp":
        # Update both path and raw_path for consistency
        request.scope["path"] = "/mcp/"
        request.scope["raw_path"] = b"/mcp/"

    return await call_next(request)


# Mount MCP protocol at /mcp (handles both /mcp and /mcp/)
# Note: FastAPI's mount() requires exact path match, so we mount at root of /mcp
# and the MCP app handles its own routing from there
api.mount("/mcp", mcp_app)


# Helper to get ServerContext from request
def get_server_context_from_request(request: Request) -> ServerContext:
    """Extract ServerContext from FastAPI app state.

    Args:
        request: FastAPI request object

    Returns:
        ServerContext with testio_client and cache

    Raises:
        RuntimeError: If server context not initialized
    """
    server_ctx = getattr(request.app.state, "server_context", None)
    if server_ctx is None:
        raise RuntimeError("Server context not initialized")
    return cast(ServerContext, server_ctx)


# Exception handlers


@api.exception_handler(TestNotFoundException)
async def handle_test_not_found(_: Request, exc: TestNotFoundException) -> JSONResponse:
    """Convert TestNotFoundException to HTTP 404."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "test_not_found",
            "message": exc.message,
            "test_id": exc.test_id,
        },
    )


@api.exception_handler(BugNotFoundException)
async def handle_bug_not_found(_: Request, exc: BugNotFoundException) -> JSONResponse:
    """Convert BugNotFoundException to HTTP 404."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "bug_not_found",
            "message": exc.message,
            "bug_id": exc.bug_id,
        },
    )


@api.exception_handler(ProductNotFoundException)
async def handle_product_not_found(_: Request, exc: ProductNotFoundException) -> JSONResponse:
    """Convert ProductNotFoundException to HTTP 404."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "product_not_found",
            "message": exc.message,
            "product_id": exc.product_id,
        },
    )


@api.exception_handler(FeatureNotFoundException)
async def handle_feature_not_found(_: Request, exc: FeatureNotFoundException) -> JSONResponse:
    """Convert FeatureNotFoundException to HTTP 404."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "feature_not_found",
            "message": exc.message,
            "feature_id": exc.feature_id,
        },
    )


@api.exception_handler(UserNotFoundException)
async def handle_user_not_found(_: Request, exc: UserNotFoundException) -> JSONResponse:
    """Convert UserNotFoundException to HTTP 404."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "user_not_found",
            "message": exc.message,
            "user_id": exc.user_id,
        },
    )


@api.exception_handler(TestIOAPIError)
async def handle_api_error(_: Request, exc: TestIOAPIError) -> JSONResponse:
    """Convert TestIOAPIError to appropriate HTTP status code."""
    # Use original status code if it's a valid HTTP error (4xx/5xx)
    # Otherwise, treat as 502 Bad Gateway (upstream error)
    status = exc.status_code if 400 <= exc.status_code < 600 else 502
    return JSONResponse(
        status_code=status,
        content={
            "error": "upstream_api_error",
            "message": exc.message,
            "status_code": exc.status_code,
        },
    )


@api.exception_handler(InvalidSearchQueryError)
async def handle_invalid_search_query(_: Request, exc: InvalidSearchQueryError) -> JSONResponse:
    """Convert InvalidSearchQueryError to HTTP 400."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_search_query",
            "message": exc.message,
        },
    )


@api.exception_handler(TestProductMismatchError)
async def handle_test_product_mismatch(_: Request, exc: TestProductMismatchError) -> JSONResponse:
    """Convert TestProductMismatchError to HTTP 400."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "test_product_mismatch",
            "message": exc.message,
            "test_id": exc.test_id,
            "actual_product_id": exc.actual_product_id,
            "allowed_product_ids": exc.allowed_product_ids,
        },
    )


@api.exception_handler(ValidationError)
async def handle_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
    """Convert ValidationError to HTTP 400."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": exc.message,
            "field": exc.field,
        },
    )


# REST Endpoints (Task 4)
# Test Endpoints


@api.get("/api/tests/{test_id}/summary", response_model=TestStatusOutput)
async def get_test_summary_rest(
    request: Request,
    test_id: int = Path(..., description="Test ID", gt=0),
) -> TestStatusOutput:
    """Get test summary via REST API.

    Returns test details with bugs, same as MCP tool.
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Create service using DI helper with proper session cleanup (TD-001)
    async with get_service_context_from_server_context(server_ctx, TestService) as service:
        # Delegate to service (exception handlers convert to HTTP errors)
        result = await service.get_test_summary(test_id)

        # Service returns dict that matches TestStatusOutput structure
        return TestStatusOutput(**result)


@api.get("/api/tests", response_model=ListTestsOutput)
async def list_tests_rest(
    request: Request,
    product_id: int = Query(..., description="Product ID", gt=0),
    statuses: str | None = Query(
        None,
        description="Comma-separated test statuses (e.g., 'running,locked')",
    ),
    page: int = Query(1, description="Page number (1-indexed)", ge=1),
    per_page: int = Query(100, description="Items per page", ge=1, le=200),
) -> ListTestsOutput:
    """List tests for a product with filtering.

    Query parameters:
    - product_id: Product ID (required)
    - statuses: Comma-separated status values (optional)
    - page: Page number, 1-indexed (default: 1)
    - per_page: Items per page (default: 100, max: 200)
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Parse statuses using centralized parser with error handling
    try:
        status_list = parse_status_input(statuses)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status parameter: {e}",
        ) from e

    # Create service with proper session cleanup (TD-001)
    async with get_service_context_from_server_context(server_ctx, TestService) as service:
        # Delegate to service
        service_result = await service.list_tests(
            product_id=product_id,
            statuses=status_list,  # type: ignore[arg-type]
            page=page,
            per_page=per_page,
        )

        # Extract service result
        product = service_result["product"]
        tests = service_result["tests"]
        statuses_filter = service_result["statuses_filter"]
        total_count = service_result["total_count"]
        offset = service_result["offset"]
        has_more = service_result["has_more"]

        # Transform using centralized transformer
        test_summaries = to_test_summary_list(tests)

        # Build pagination info
        pagination = PaginationInfo(
            page=page,
            per_page=per_page,
            offset=offset,
            start_index=offset,
            end_index=offset + len(tests) - 1 if tests else -1,
            total_count=total_count,
            has_more=has_more,
        )

    # Build product info
    product_info = ProductInfoSummary(
        id=product["id"],
        name=product["name"],
        type=product["type"],
    )

    # Return validated Pydantic model
    return ListTestsOutput(
        product=product_info,
        statuses_filter=statuses_filter,
        pagination=pagination,
        total_tests=len(test_summaries),
        tests=test_summaries,
    )


# Bug Endpoints


@api.get("/api/bugs", response_model=ListBugsOutput)
async def list_bugs_rest(
    request: Request,
    test_ids: str = Query(
        ...,
        description="Required comma-separated test IDs (e.g., '123,456')",
    ),
    status: str | None = Query(
        None,
        description="Comma-separated bug statuses (e.g., 'rejected,forwarded')",
    ),
    severity: str | None = Query(
        None,
        description="Comma-separated severities (e.g., 'critical,high')",
    ),
    rejection_reason: str | None = Query(
        None,
        description="Comma-separated rejection reasons",
    ),
    reported_by_user_id: int | None = Query(
        None,
        description="Filter by reporting user ID",
        gt=0,
    ),
    page: int = Query(1, description="Page number (1-indexed)", ge=1),
    per_page: int = Query(100, description="Items per page", ge=1, le=200),
    offset: int = Query(0, description="Starting offset (0-indexed)", ge=0),
    sort_by: str = Query(
        "reported_at",
        description="Sort field (reported_at, severity, status, title)",
    ),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
) -> ListBugsOutput:
    """List bugs for specified tests with filters and pagination.

    Query parameters:
    - test_ids: Required comma-separated test IDs
    - status: Comma-separated bug statuses (optional)
    - severity: Comma-separated severities (optional)
    - rejection_reason: Comma-separated rejection reasons (optional)
    - reported_by_user_id: Filter by reporter (optional)
    - page: Page number, 1-indexed (default: 1)
    - per_page: Items per page (default: 100, max: 200)
    - offset: Starting offset (default: 0)
    - sort_by: Sort field (default: reported_at)
    - sort_order: Sort order (default: desc)
    """
    from testio_mcp.config import settings
    from testio_mcp.schemas.api import BugListItem

    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Parse test_ids (required, comma-separated string to list of ints)
    try:
        test_id_list = [int(t.strip()) for t in test_ids.split(",") if t.strip()]
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid test_ids: {str(e)}. Must be comma-separated integers.",
        ) from e

    if not test_id_list:
        raise HTTPException(
            status_code=400,
            detail="test_ids is required. Provide comma-separated test IDs.",
        )

    # Parse optional comma-separated filter strings to lists
    status_list = [s.strip() for s in status.split(",") if s.strip()] if status else None
    severity_list = [s.strip() for s in severity.split(",") if s.strip()] if severity else None
    rejection_reason_list = (
        [r.strip() for r in rejection_reason.split(",") if r.strip()] if rejection_reason else None
    )

    # Use default per_page from settings if not specified
    effective_per_page = per_page if per_page > 0 else settings.TESTIO_DEFAULT_PAGE_SIZE

    # Create service with proper session cleanup
    async with get_service_context_from_server_context(server_ctx, BugService) as service:
        service_result = await service.list_bugs(
            test_ids=test_id_list,
            status=status_list,
            severity=severity_list,
            rejection_reason=rejection_reason_list,
            reported_by_user_id=reported_by_user_id,
            page=page,
            per_page=effective_per_page,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Extract components from service result
        bugs = service_result["bugs"]
        pagination = service_result["pagination"]
        filters_applied = service_result["filters_applied"]
        warnings = service_result.get("warnings")

        # Build validated output using BugListItem
        bug_items = [
            BugListItem(
                id=bug["id"],
                title=bug["title"],
                severity=bug["severity"],
                status=bug["status"],
                test_id=bug["test_id"],
                reported_at=bug["reported_at"],
            )
            for bug in bugs
        ]

        return ListBugsOutput(
            bugs=bug_items,
            pagination=pagination,
            filters_applied=filters_applied,
            warnings=warnings,
        )


@api.get("/api/bugs/{bug_id}/summary", response_model=BugSummaryOutput)
async def get_bug_summary_rest(
    request: Request,
    bug_id: int = Path(..., description="Bug ID", gt=0),
) -> BugSummaryOutput:
    """Get bug summary with full details, related entities, and metadata.

    Path parameters:
    - bug_id: Bug ID

    Returns comprehensive bug information:
    - Core fields (id, title, severity, status, known)
    - Detail fields (actual_result, expected_result, steps)
    - Rejection field (rejection_reason if rejected)
    - Related entities (reported_by_user, test, feature)
    - Metadata (reported_at, data_as_of)
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Create service using async context manager for proper resource cleanup
    async with get_service_context_from_server_context(server_ctx, BugService) as service:
        # Delegate to service (exception handlers convert to HTTP errors)
        result = await service.get_bug_summary(bug_id)

        # Service returns dict that matches BugSummaryOutput structure
        return BugSummaryOutput(**result)


# Product Endpoints


@api.get("/api/products", response_model=ListProductsOutput)
async def list_products_rest(
    request: Request,
    search: str | None = Query(None, description="Search term for product name/description"),
    product_type: str | None = Query(
        None,
        description="Comma-separated product types (e.g., 'website,mobile_app_ios')",
    ),
    sort_by: str | None = Query(
        None, description="Sort by field (title, product_type, last_synced)"
    ),
    sort_order: str = Query("asc", description="Sort order (asc, desc)"),
    page: int = Query(1, description="Page number (1-indexed)", ge=1),
    per_page: int = Query(50, description="Items per page", ge=1, le=100),
    offset: int = Query(0, description="Starting offset (0-indexed)", ge=0),
) -> Any:
    """List products with optional filtering, sorting, and pagination.

    Query parameters:
    - search: Search term (optional)
    - product_type: Comma-separated product types (optional)
    - sort_by: Sort field (optional)
    - sort_order: Sort order (default: asc)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50)
    - offset: Starting offset (default: 0)
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Parse product types (comma-separated string to list)
    type_list = None
    if product_type:
        type_list = [t.strip() for t in product_type.split(",") if t.strip()]

    # Create service with proper session cleanup (TD-001)
    async with get_service_context_from_server_context(server_ctx, ProductService) as service:
        # STORY-058: Service handles default sort_by to ensure enriched counts
        result = await service.list_products(
            search=search,
            product_type=type_list,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page,
            offset=offset,
        )

        # Service returns dict that matches ListProductsOutput structure
        return ListProductsOutput(**result)


@api.get("/api/products/{product_id}/tests", response_model=ListTestsOutput)
async def list_product_tests_rest(
    request: Request,
    product_id: int = Path(..., description="Product ID", gt=0),
    statuses: str | None = Query(
        None,
        description="Comma-separated test statuses (e.g., 'running,locked')",
    ),
    testing_type: str | None = Query(
        None,
        description="Filter by testing type (coverage, focused, rapid)",
    ),
    page: int = Query(1, description="Page number (1-indexed)", ge=1),
    per_page: int = Query(100, description="Items per page", ge=1, le=200),
    offset: int = Query(0, description="Starting offset (0-indexed)", ge=0),
    sort_by: str = Query("end_at", description="Sort field (start_at, end_at, status, title)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
) -> ListTestsOutput:
    """List tests for a specific product.

    Path parameters:
    - product_id: Product ID

    Query parameters:
    - statuses: Comma-separated status values (optional)
    - testing_type: Filter by testing type (optional)
    - page: Page number, 1-indexed (default: 1)
    - per_page: Items per page (default: 100, max: 200)
    - offset: Starting offset (default: 0)
    - sort_by: Sort field (default: end_at)
    - sort_order: Sort order (default: desc)
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Parse statuses using centralized parser with error handling
    try:
        status_list = parse_status_input(statuses)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status parameter: {e}",
        ) from e

    # Create service with proper session cleanup (TD-001)
    async with get_service_context_from_server_context(server_ctx, TestService) as service:
        # Delegate to service
        service_result = await service.list_tests(
            product_id=product_id,
            statuses=status_list,  # type: ignore[arg-type]
            testing_type=testing_type,
            page=page,
            per_page=per_page,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Extract service result
        product = service_result["product"]
        tests = service_result["tests"]
        statuses_filter = service_result["statuses_filter"]
        total_count = service_result["total_count"]
        offset = service_result["offset"]
        has_more = service_result["has_more"]

        # Transform using centralized transformer
        test_summaries = to_test_summary_list(tests)

        # Build pagination info
        pagination = PaginationInfo(
            page=page,
            per_page=per_page,
            offset=offset,
            start_index=offset,
            end_index=offset + len(tests) - 1 if tests else -1,
            total_count=total_count,
            has_more=has_more,
        )

    # Build product info
    product_info = ProductInfoSummary(
        id=product["id"],
        name=product["name"],
        type=product["type"],
    )

    # Return validated Pydantic model
    return ListTestsOutput(
        product=product_info,
        statuses_filter=statuses_filter,
        pagination=pagination,
        total_tests=len(test_summaries),
        tests=test_summaries,
    )


# Report Endpoints


@api.get("/api/quality-report", response_model=QualityReportRESTOutput)
async def generate_quality_report_rest(
    request: Request,
    product_ids: str = Query(
        ...,
        description="Required comma-separated product IDs (e.g., '598' or '598,599')",
    ),
    test_ids: str | None = Query(
        None,
        description="Comma-separated test IDs to filter to specific tests",
    ),
    start_date: str | None = Query(
        None,
        description="Start date (ISO format or business terms like 'last 30 days'). "
        "Filters on test end_at.",
    ),
    end_date: str | None = Query(
        None,
        description="End date (ISO format or business terms like 'today'). Filters on test end_at.",
    ),
    statuses: str | None = Query(
        None,
        description="Comma-separated test statuses (default: excludes 'initialized' and "
        "'cancelled')",
    ),
    output_file: str | None = Query(
        None,
        description="Optional file path to export report (for large products >100 tests)",
    ),
) -> QualityReportRESTOutput:
    """Generate Product Quality Report for one or more products.

    Query parameters:
    - product_ids: Required comma-separated product IDs
    - test_ids: Optional comma-separated test IDs (must belong to product_ids)
    - start_date: Start date filter (optional, filters on end_at)
    - end_date: End date filter (optional, filters on end_at)
    - statuses: Comma-separated test statuses (optional)
    - output_file: Export to file (optional, for large products)

    For fresh data, call /api/sync first with product_ids parameter.

    Response includes per-test data (test_data field). For MCP tool, use
    generate_quality_report which returns aggregate metrics only.
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Parse product_ids (required, comma-separated string to list of ints)
    try:
        product_id_list = [int(p.strip()) for p in product_ids.split(",") if p.strip()]
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid product_ids: {str(e)}. Must be comma-separated integers.",
        ) from e

    if not product_id_list:
        raise HTTPException(
            status_code=400,
            detail="product_ids is required. Provide comma-separated product IDs.",
        )

    # Parse test_ids (optional, comma-separated string to list of ints)
    test_id_list: list[int] | None = None
    if test_ids:
        try:
            test_id_list = [int(t.strip()) for t in test_ids.split(",") if t.strip()]
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid test_ids: {str(e)}. Must be comma-separated integers.",
            ) from e

        if not test_id_list:
            raise HTTPException(
                status_code=400,
                detail="Empty test_ids is invalid. Omit parameter for all tests.",
            )

    # Parse statuses (comma-separated string to list)
    # Filter empty strings (e.g., "running,," → ["running"])
    status_list: list[str] | None = None
    if statuses:
        status_list = [s.strip() for s in statuses.split(",") if s.strip()]
        # Reject empty list after filtering (e.g., ",,")
        if len(status_list) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty statuses after parsing. Omit parameter for default (executed tests).",
            )

    # Create service with proper session cleanup (TD-001)
    async with get_service_context_from_server_context(
        server_ctx, MultiTestReportService
    ) as service:
        # Delegate to service - REST includes per-test data
        result = await service.get_product_quality_report(
            product_ids=product_id_list,
            test_ids=test_id_list,
            start_date=start_date,
            end_date=end_date,
            statuses=status_list,
            output_file=output_file,
            include_test_data=True,  # REST API includes per-test data
        )

        # Build response models from service result
        thresholds_data = result["thresholds"]
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
        products_list = [ProductInfo(id=p["id"], title=p["title"]) for p in result["products"]]

        # Build by_product list (if present)
        by_product_list: list[ProductBreakdown] | None = None
        if result.get("by_product"):
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
                for bp in result["by_product"]
            ]

        # Build test_data list (if present)
        test_data_list: list[TestDataItem] | None = None
        if result.get("test_data"):
            test_data_list = [
                TestDataItem(
                    test_id=td["test_id"],
                    product_id=td.get("product_id"),
                    title=td["title"],
                    status=td["status"],
                    testing_type=td.get("testing_type"),
                    start_at=td.get("start_at"),
                    end_at=td.get("end_at"),
                    bugs_count=td["bugs_count"],
                    bugs=td["bugs"],
                    test_environment=td.get("test_environment"),
                    active_acceptance_rate=td.get("active_acceptance_rate"),
                    auto_acceptance_rate=td.get("auto_acceptance_rate"),
                    overall_acceptance_rate=td.get("overall_acceptance_rate"),
                    rejection_rate=td.get("rejection_rate"),
                    review_rate=td.get("review_rate"),
                )
                for td in result["test_data"]
            ]

        # Build summary
        summary = result["summary"]
        summary_output = QualityReportSummary(
            product_ids=summary.get("product_ids", result["product_ids"]),
            products=[
                ProductInfo(id=p["id"], title=p["title"])
                for p in summary.get("products", result["products"])
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
        return QualityReportRESTOutput(
            summary=summary_output,
            product_ids=result["product_ids"],
            products=products_list,
            test_ids=result["test_ids"],
            by_product=by_product_list,
            test_data=test_data_list,
            thresholds=thresholds_output,
            # File export fields (if applicable)
            file_path=result.get("file_path"),
            record_count=result.get("record_count"),
            file_size_bytes=result.get("file_size_bytes"),
            format=result.get("format"),
        )


# Feature Endpoints (STORY-037)


@api.get("/api/products/{product_id}/features", response_model=ListFeaturesOutput)
async def get_product_features_rest(
    request: Request,
    product_id: int = Path(..., description="Product ID", gt=0),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(0, ge=0, le=200, description="Items per page (0=default, max 200)"),
    offset: int = Query(0, ge=0, description="Starting offset (combines with page)"),
    sort_by: str | None = Query(
        None, description="Sort field (title, test_count, bug_count, last_synced)"
    ),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order (asc or desc)"),
    has_user_stories: bool | None = Query(
        None, description="Filter by user story presence (true=only with stories)"
    ),
) -> ListFeaturesOutput:
    """Get features for a product with pagination and sorting.

    Path parameters:
    - product_id: Product ID

    Query parameters:
    - page: Page number (1-indexed, default: 1)
    - per_page: Items per page (0=use default from settings, max: 200)
    - offset: Starting offset (combines with page)
    - sort_by: Sort field (title, test_count, bug_count, last_synced)
    - sort_order: Sort order (asc or desc, default: asc)
    - has_user_stories: Filter by user story presence

    Returns features with id, title, description, howtofind, user_story_count, pagination metadata.
    """
    from testio_mcp.config import settings
    from testio_mcp.services.feature_service import FeatureService

    server_ctx = get_server_context_from_request(request)

    # Use default per_page from settings if not specified (0 = use default)
    effective_per_page = per_page if per_page > 0 else settings.TESTIO_DEFAULT_PAGE_SIZE

    async with get_service_context_from_server_context(server_ctx, FeatureService) as service:
        result = await service.list_features(
            product_id=product_id,
            page=page,
            per_page=effective_per_page,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            has_user_stories=has_user_stories,
        )

        # Build pagination metadata (matching MCP tool format)
        total_count = result.get("total_count", 0)
        actual_offset = result.get("offset", 0)
        has_more = result.get("has_more", False)
        features = result.get("features", [])

        # Build pagination info
        pagination = PaginationInfo(
            page=page,
            per_page=effective_per_page,
            offset=actual_offset,
            start_index=actual_offset,
            end_index=actual_offset + len(features) - 1 if features else actual_offset,
            total_count=total_count,
            has_more=has_more,
        )

        # Return Pydantic model (matches MCP tool output)
        return ListFeaturesOutput(
            product_id=product_id,
            pagination=pagination,
            features=features,
            total=len(features),
        )


@api.get("/api/products/{product_id}/user_stories")
async def get_product_user_stories_rest(
    request: Request,
    product_id: int = Path(..., description="Product ID", gt=0),
    feature_id: int | None = Query(None, description="Optional feature ID filter"),
) -> Any:
    """Get user stories for a product.

    Path parameters:
    - product_id: Product ID

    Query parameters:
    - feature_id: Optional feature ID to filter by specific feature

    Returns user stories with title, feature_id, feature_title.
    """
    from testio_mcp.services.user_story_service import UserStoryService

    server_ctx = get_server_context_from_request(request)

    async with get_service_context_from_server_context(server_ctx, UserStoryService) as service:
        return await service.list_user_stories(product_id=product_id, feature_id=feature_id)


@api.get("/api/users")
async def get_users_rest(
    request: Request,
    user_type: str | None = Query(
        None, description="Optional user type filter ('tester' or 'customer')"
    ),
    days: int = Query(365, description="Days lookback period", gt=0),
) -> Any:
    """Get users (testers and customers).

    Query parameters:
    - user_type: Optional filter ('tester' for bug reporters, 'customer' for test creators)
    - days: Number of days to look back for active users (default: 365)

    Returns users with id, username, user_type, first_seen, last_seen.
    """
    from testio_mcp.services.user_service import UserService

    server_ctx = get_server_context_from_request(request)

    async with get_service_context_from_server_context(server_ctx, UserService) as service:
        return await service.list_users(user_type=user_type, days=days)


# Summary Endpoints (STORY-061: AC #3)


@api.get("/api/products/{product_id}/summary", response_model=ProductSummaryOutput)
async def get_product_summary_rest(
    request: Request,
    product_id: int = Path(..., description="Product ID", gt=0),
) -> ProductSummaryOutput:
    """Get product summary with metadata and counts.

    Path parameters:
    - product_id: Product ID

    Returns product metadata (id, title, type, description) along with computed counts:
    - test_count: Total tests for this product
    - bug_count: Total bugs across all tests
    - feature_count: Total features
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Create service using async context manager (ProductService requires session)
    async with get_service_context_from_server_context(server_ctx, ProductService) as service:
        # Delegate to service (exception handlers convert to HTTP errors)
        result = await service.get_product_summary(product_id)

        # Service returns dict that matches ProductSummaryOutput structure
        return ProductSummaryOutput(**result)


@api.get("/api/features/{feature_id}/summary", response_model=FeatureSummaryOutput)
async def get_feature_summary_rest(
    request: Request,
    feature_id: int = Path(..., description="Feature ID", gt=0),
) -> FeatureSummaryOutput:
    """Get feature summary with metadata and counts.

    Path parameters:
    - feature_id: Feature ID

    Returns feature metadata (id, title, description, howtofind) along with:
    - user_stories: List of user story titles
    - test_count: Total tests covering this feature
    - bug_count: Total bugs related to this feature
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Create service using async context manager (FeatureService requires repository)
    async with get_service_context_from_server_context(server_ctx, FeatureService) as service:
        # Delegate to service (exception handlers convert to HTTP errors)
        result = await service.get_feature_summary(feature_id)

        # Service returns dict that matches FeatureSummaryOutput structure
        return FeatureSummaryOutput(**result)


@api.get("/api/users/{user_id}/summary", response_model=UserSummaryOutput)
async def get_user_summary_rest(
    request: Request,
    user_id: int = Path(..., description="User ID", gt=0),
) -> UserSummaryOutput:
    """Get user summary with metadata and activity counts.

    Path parameters:
    - user_id: User ID

    Returns user metadata (id, username, user_type) along with activity counts:
    - For customers: tests_created_count, tests_submitted_count, last_activity
    - For testers: bugs_reported_count, last_activity
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Create service using async context manager (UserService requires repository)
    async with get_service_context_from_server_context(server_ctx, UserService) as service:
        # Delegate to service (exception handlers convert to HTTP errors)
        result = await service.get_user_summary(user_id)

        # Service returns dict that matches UserSummaryOutput structure
        return UserSummaryOutput(**result)


# Search Endpoint (STORY-065)


@api.get("/api/search", response_model=SearchOutput)
async def search_rest(
    request: Request,
    query: str = Query(..., description="Search query (required)"),
    entities: str | None = Query(
        None, description="Comma-separated entity types (e.g., 'feature,bug')"
    ),
    product_ids: str | None = Query(
        None, description="Comma-separated product IDs (e.g., '598,601')"
    ),
    start_date: str | None = Query(
        None,
        description="Start date (ISO or natural language). "
        "Note: Products/Features excluded from date filtering.",
    ),
    end_date: str | None = Query(
        None,
        description="End date (ISO or natural language). "
        "Note: Products/Features excluded from date filtering.",
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum results (default: 20, max: 100)"),
    match_mode: str = Query(
        "simple",
        pattern="^(simple|raw)$",
        description="Query mode: 'simple' (sanitized) or 'raw' (FTS5 syntax)",
    ),
) -> SearchOutput:
    """Full-text search across TestIO entities.

    Query parameters:
    - query: Search query (required)
    - entities: Comma-separated entity types (product, feature, test, bug)
    - product_ids: Comma-separated product IDs to scope search
    - start_date: Start date filter (ISO or natural language)
    - end_date: End date filter (ISO or natural language)
    - limit: Maximum results (default: 20, max: 100)
    - match_mode: 'simple' (default, sanitized) or 'raw' (FTS5 syntax)

    Returns ranked results sorted by BM25 relevance.

    Note: Products and Features don't have timestamps, so they are excluded
    when start_date or end_date is specified. Only Tests and Bugs support date filtering.

    Example:
        GET /api/search?query=borders&entities=feature,bug
        GET /api/search?query=video%20mode&product_ids=598,601&start_date=last%20week
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Parse comma-separated parameters
    entity_list: list[str] | None = None
    if entities:
        entity_list = [e.strip() for e in entities.split(",") if e.strip()]

    product_id_list: list[int] | None = None
    if product_ids:
        try:
            product_id_list = [int(p.strip()) for p in product_ids.split(",") if p.strip()]
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid product_ids: {str(e)}. Must be comma-separated integers.",
            ) from e

    # Create service using async context manager for proper resource cleanup
    async with get_service_context_from_server_context(server_ctx, SearchService) as service:
        try:
            result = await service.search(
                query=query,
                entities=entity_list,
                product_ids=product_id_list,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                match_mode=match_mode,
            )

            # Service returns dict that matches SearchOutput structure
            return SearchOutput(**result)

        except ValueError as e:
            # Entity type validation errors
            raise HTTPException(
                status_code=400,
                detail=str(e),
            ) from e


# Analytics Endpoints (STORY-061: AC #5)


@api.post("/api/analytics/query")
async def query_metrics_rest(
    request: Request,
    query_input: QueryMetricsInput,
) -> dict[str, Any]:
    """Query custom analytics with pivot tables.

    Request body: QueryMetricsInput (Pydantic validated)

    - metrics: List of metrics to measure (e.g., ["bug_count"])
    - dimensions: List of dimensions to group by (max 2, e.g., ["feature"])
    - start_date: Optional start date (ISO or natural language)
    - end_date: Optional end date
    - filters: Optional filters by dimension values, product_id, or status
    - sort_by: Optional sort by metric/dimension
    - sort_order: Sort order (asc or desc, default: desc)
    - limit: Max rows (default: 1000)

    Filter examples:
    - {"product_id": 598} - Scope to specific product
    - {"status": ["running", "locked"]} - Filter by test status
    - {"severity": "critical"} - Filter by bug severity

    Default: Excludes initialized/cancelled tests. Override with status filter.

    Returns pivot table with requested metrics aggregated by dimensions.
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Create service using async context manager for proper resource cleanup
    async with get_service_context_from_server_context(server_ctx, AnalyticsService) as service:
        # Delegate to service
        try:
            result = await service.query_metrics(
                metrics=query_input.metrics,
                dimensions=query_input.dimensions,
                filters=query_input.filters or {},
                start_date=query_input.start_date,
                end_date=query_input.end_date,
                sort_by=query_input.sort_by,
                sort_order=query_input.sort_order,
                limit=query_input.limit,
                tests_limit=query_input.tests_limit,
            )
            # Service returns QueryResponse Pydantic model
            return result.model_dump(exclude_none=True)
        except ValueError as e:
            # Validation errors from service (invalid dimensions/metrics)
            raise HTTPException(
                status_code=400,
                detail=(
                    f"❌ Invalid query parameters\n"
                    f"ℹ️ {str(e)}\n"
                    f"💡 Use GET /api/analytics/capabilities to see valid dimensions and metrics"
                ),
            ) from e


@api.get("/api/analytics/capabilities")
async def get_analytics_capabilities_rest(request: Request) -> dict[str, Any]:
    """Get available analytics dimensions and metrics.

    Returns all available dimensions and metrics that can be used in query_metrics.
    Useful for building dynamic query interfaces.
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Create service using DI helper and access registries (same as MCP tool)
    async with get_service_context_from_server_context(server_ctx, AnalyticsService) as service:
        # Get registries (same implementation as MCP tool)
        dimensions = [
            {
                "key": dim.key,
                "description": dim.description,
                "example": dim.example,
            }
            for dim in service._dimensions.values()
        ]

        metrics = [
            {
                "key": metric.key,
                "description": metric.description,
                "formula": metric.formula,
            }
            for metric in service._metrics.values()
        ]

        return {
            "dimensions": dimensions,
            "metrics": metrics,
            "limits": {
                "max_dimensions": 2,
                "max_rows": 1000,
                "timeout_seconds": 90,
            },
        }


# Operational/Diagnostic Endpoints (STORY-061: AC #6)


@api.get("/api/diagnostics", response_model=ServerDiagnostics)
async def get_server_diagnostics_rest(
    request: Request,
    include_sync_events: bool = Query(
        False,
        description="Include recent sync event history",
    ),
    sync_event_limit: int = Query(
        5,
        description="Max sync events to include (if include_sync_events=true)",
        ge=1,
        le=20,
    ),
) -> ServerDiagnostics:
    """Get server diagnostics (API health, database stats, sync status).

    Query parameters:
    - include_sync_events: Include recent sync history (default: false)
    - sync_event_limit: Max sync events (default: 5, max: 20)

    Returns consolidated diagnostics:
    - API authentication status
    - Database statistics (size, counts, freshness)
    - Sync status (last sync, problematic tests)
    - Optional sync event history
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Create service using async context manager for proper resource cleanup
    async with get_service_context_from_server_context(server_ctx, DiagnosticsService) as service:
        # Delegate to service (exception handlers convert to HTTP errors)
        result = await service.get_server_diagnostics(
            include_sync_events=include_sync_events,
            sync_event_limit=sync_event_limit,
        )

        # Service returns dict that matches ServerDiagnostics structure
        return ServerDiagnostics(**result)


@api.get("/api/sync/problematic", response_model=ProblematicTestsOutput)
async def get_problematic_tests_rest(
    request: Request,
    product_id: int | None = Query(None, description="Optional product ID filter", gt=0),
) -> ProblematicTestsOutput:
    """Get tests that failed to sync (API 500 errors).

    Query parameters:
    - product_id: Optional product filter

    Returns tests with boundary IDs for debugging sync failures.
    """
    # Get ServerContext from FastAPI app state
    server_ctx = get_server_context_from_request(request)

    # Access cache directly (same pattern as MCP tool)
    cache = server_ctx["cache"]

    # Get problematic tests
    problematic = await cache.get_problematic_tests(product_id=product_id)

    # Build result (same as MCP tool)
    result = ProblematicTestsOutput(
        count=len(problematic),
        tests=problematic,
        message="Tests with 500 errors during sync. Use boundary IDs for debugging.",
    )
    return result


# Health Endpoint (Task 5)


@api.get("/health", response_model=HealthCheckOutput)
async def health_check_rest(request: Request) -> HealthCheckOutput:
    """Health check endpoint for monitoring.

    Returns:
        Health status, version, uptime, and database statistics.
    """
    try:
        # Get ServerContext
        server_ctx = get_server_context_from_request(request)
        cache = server_ctx["cache"]

        # Calculate uptime
        start_time = getattr(request.app.state, "start_time", monotonic())
        uptime_seconds = monotonic() - start_time

        # Get database stats (call cache methods directly)
        total_tests = await cache.count_tests()
        total_products = await cache.count_products()
        db_size_mb = await cache.get_db_size_mb()

        return HealthCheckOutput(
            status="healthy",
            version="0.4.0",
            uptime_seconds=round(uptime_seconds, 2),
            database=DatabaseInfo(
                connected=True,
                total_tests=total_tests,
                total_products=total_products,
                database_size_mb=db_size_mb,
            ),
        )
    except Exception as e:
        # Return unhealthy status if anything fails
        return HealthCheckOutput(
            status="unhealthy",
            version="0.4.0",
            error=str(e),
            database=DatabaseInfo(connected=False),
        )


# Configuration Endpoints


@api.get("/api/thresholds", response_model=ThresholdsOutput)
async def get_thresholds() -> ThresholdsOutput:
    """Get playbook threshold configuration for health indicators.

    Returns the current threshold values used to compute health status
    (healthy/warning/critical) for key quality metrics.

    These thresholds are used by:
    - get_product_quality_report (health_indicators field)
    - AI agents for contextual interpretation of metrics

    Thresholds can be customized via environment variables:
    - PLAYBOOK_REJECTION_WARNING, PLAYBOOK_REJECTION_CRITICAL
    - PLAYBOOK_AUTO_ACCEPTANCE_WARNING, PLAYBOOK_AUTO_ACCEPTANCE_CRITICAL
    - PLAYBOOK_REVIEW_WARNING, PLAYBOOK_REVIEW_CRITICAL

    Future: Per-product threshold overrides via GET /api/products/{id}/thresholds
    """
    # Load thresholds from settings (env vars)
    thresholds = PlaybookThresholds.from_settings(settings)

    return ThresholdsOutput(
        rejection_rate=MetricThresholdOutput(
            warning=thresholds.rejection_rate.warning,
            critical=thresholds.rejection_rate.critical,
            direction=thresholds.rejection_rate.direction,
        ),
        auto_acceptance_rate=MetricThresholdOutput(
            warning=thresholds.auto_acceptance_rate.warning,
            critical=thresholds.auto_acceptance_rate.critical,
            direction=thresholds.auto_acceptance_rate.direction,
        ),
        review_rate=MetricThresholdOutput(
            warning=thresholds.review_rate.warning,
            critical=thresholds.review_rate.critical,
            direction=thresholds.review_rate.direction,
        ),
    )
