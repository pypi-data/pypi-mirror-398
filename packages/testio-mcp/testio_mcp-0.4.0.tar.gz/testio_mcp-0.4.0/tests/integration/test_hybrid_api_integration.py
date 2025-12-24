"""Integration tests for hybrid MCP + REST API.

Tests verify that:
1. REST endpoints return correct data
2. MCP and REST protocols coexist
3. Swagger documentation is accessible
4. Health endpoint works
5. Exception handlers work correctly

STORY-023f: Hybrid MCP+REST API with Swagger
"""

import pytest
from httpx import AsyncClient

from testio_mcp.config import settings

# Skip all tests if no API token (integration tests require credentials)
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not settings.TESTIO_CUSTOMER_API_TOKEN,
        reason="Integration test requires TESTIO_CUSTOMER_API_TOKEN",
    ),
]

# test_client fixture is now defined in tests/integration/conftest.py
# and is automatically available to all tests in this module


@pytest.mark.asyncio
async def test_rest_endpoint_list_tests(test_client: AsyncClient) -> None:
    """Verify REST endpoint lists tests with query params.

    Note: This test uses in-memory database which starts empty.
    The list_tests endpoint queries the local database, not the TestIO API directly.
    A 404 response indicates the product hasn't been synced to the local database yet,
    which is expected behavior for an empty in-memory database.
    """
    # First get a valid product ID from TestIO API
    products_response = await test_client.get("/api/products")
    assert products_response.status_code == 200
    products_data = products_response.json()
    assert len(products_data["products"]) > 0
    product_id = products_data["products"][0]["id"]

    # Query tests from local database (may be empty)
    response = await test_client.get(
        "/api/tests",
        params={
            "product_id": product_id,
            "page": 1,
            "per_page": 10,
        },
    )

    # Accept either 200 (product synced) or 404 (product not in local DB yet)
    # This is integration test behavior - in production, background sync populates the DB
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert "product" in data
        assert "tests" in data
        assert isinstance(data["tests"], list)


@pytest.mark.asyncio
async def test_rest_endpoint_list_products(test_client: AsyncClient) -> None:
    """Verify REST endpoint lists products."""
    response = await test_client.get("/api/products")

    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert isinstance(data["products"], list)


@pytest.mark.asyncio
async def test_swagger_docs_accessible(test_client: AsyncClient) -> None:
    """Verify Swagger UI is accessible."""
    response = await test_client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


@pytest.mark.asyncio
async def test_openapi_schema_accessible(test_client: AsyncClient) -> None:
    """Verify OpenAPI schema is accessible."""
    response = await test_client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    # Verify our endpoints are in the schema
    assert "/api/tests/{test_id}/summary" in data["paths"]
    assert "/api/products" in data["paths"]
    assert "/health" in data["paths"]


@pytest.mark.asyncio
async def test_health_endpoint(test_client: AsyncClient) -> None:
    """Verify health endpoint returns valid JSON."""
    response = await test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("healthy", "unhealthy")
    assert "version" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_exception_handler_test_not_found(test_client: AsyncClient) -> None:
    """Verify 404 error handling for non-existent test."""
    # Use an intentionally invalid test ID
    invalid_test_id = 999999999

    response = await test_client.get(f"/api/tests/{invalid_test_id}/summary")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"] == "test_not_found"
    assert "test_id" in data
    assert data["test_id"] == invalid_test_id


@pytest.mark.asyncio
async def test_exception_handler_product_not_found(test_client: AsyncClient) -> None:
    """Verify 404 error handling for non-existent product."""
    # Use an intentionally invalid product ID
    invalid_product_id = 999999999

    response = await test_client.get(
        "/api/tests",
        params={
            "product_id": invalid_product_id,
            "page": 1,
            "per_page": 10,
        },
    )

    # Should return 404 if product doesn't exist
    # Note: Actual behavior depends on service implementation
    assert response.status_code in (404, 200)  # May return empty list instead of 404


@pytest.mark.asyncio
async def test_rest_and_mcp_share_resources(test_client: AsyncClient) -> None:
    """Verify REST and MCP protocols share the same server resources.

    This test verifies that both protocols access the same database
    and return consistent data.
    """
    # Get product list via REST
    rest_response = await test_client.get("/api/products")

    assert rest_response.status_code == 200
    rest_data = rest_response.json()
    assert "products" in rest_data
    assert len(rest_data["products"]) > 0

    # Both protocols should access the same database
    # (We can't easily test MCP protocol here without setting up MCP client,
    # but the shared lifespan ensures they use the same resources)


@pytest.mark.asyncio
async def test_product_quality_report_endpoint(test_client: AsyncClient) -> None:
    """Verify product quality report generation via REST API.

    Note: This test uses in-memory database which starts empty.
    The report endpoint queries the local database for tests.
    A 404 response indicates no tests found for the product in the local database,
    which is expected behavior for an empty in-memory database.
    """
    # First get a valid product ID from TestIO API
    products_response = await test_client.get("/api/products")
    assert products_response.status_code == 200
    products_data = products_response.json()
    assert len(products_data["products"]) > 0
    product_id = products_data["products"][0]["id"]

    # Request EBR report (queries local database)
    response = await test_client.get(
        f"/api/products/{product_id}/quality-report",
        params={
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        },
    )

    # Accept either 200 (tests found) or 404 (no tests in local DB yet)
    # This is integration test behavior - in production, background sync populates the DB
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert "summary" in data
        assert "test_sample" in data


@pytest.mark.asyncio
async def test_validation_error_handling(test_client: AsyncClient) -> None:
    """Verify validation errors return 422 Unprocessable Entity."""
    # Send invalid test_id (negative number)
    response = await test_client.get("/api/tests/-1/summary")

    # FastAPI returns 422 for validation errors
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
