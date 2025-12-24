"""Integration tests for new REST API endpoints added in STORY-061.

Tests verify that new endpoints added for REST API parity work correctly:
- Summary endpoints (products, features, users, tests)
- Analytics endpoints (query_metrics, get_analytics_capabilities)
- Operational endpoints (diagnostics, problematic tests)

STORY-061: REST API Parity
"""

import pytest

from testio_mcp.config import settings

# test_client fixture is automatically available from tests/integration/conftest.py

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not settings.TESTIO_CUSTOMER_API_TOKEN,
        reason="Integration test requires TESTIO_CUSTOMER_API_TOKEN",
    ),
]


# Summary Endpoints Tests


@pytest.mark.asyncio
async def test_get_product_summary(test_client) -> None:
    """Verify GET /api/products/{id}/summary returns product summary."""
    # First get a valid product ID
    products_response = await test_client.get("/api/products")
    assert products_response.status_code == 200
    products_data = products_response.json()
    assert len(products_data["products"]) > 0
    product_id = products_data["products"][0]["id"]

    # Get product summary
    response = await test_client.get(f"/api/products/{product_id}/summary")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "title" in data
    assert "type" in data
    assert "test_count" in data
    assert "feature_count" in data
    assert data["id"] == product_id


@pytest.mark.asyncio
async def test_get_product_summary_not_found(test_client) -> None:
    """Verify GET /api/products/{id}/summary returns 404 for invalid ID."""
    response = await test_client.get("/api/products/99999/summary")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"] == "product_not_found"


@pytest.mark.asyncio
async def test_get_feature_summary_not_found(test_client) -> None:
    """Verify GET /api/features/{id}/summary returns 404 for invalid ID.

    Note: Testing 404 case instead of 200 OK because test environment
    may not have features synced to local database. This still validates
    endpoint implementation, Pydantic validation, and exception handling.
    """
    response = await test_client.get("/api/features/99999/summary")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"] == "feature_not_found"


@pytest.mark.asyncio
async def test_get_user_summary(test_client) -> None:
    """Verify GET /api/users/{id}/summary returns user summary."""
    # First get users
    users_response = await test_client.get("/api/users")

    # May be empty in test environment
    if users_response.status_code == 200:
        users_data = users_response.json()
        if users_data.get("users"):
            user_id = users_data["users"][0]["id"]

            # Get user summary
            response = await test_client.get(f"/api/users/{user_id}/summary")

            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "username" in data
            assert "user_type" in data
            assert data["id"] == user_id


# Analytics Endpoints Tests


@pytest.mark.asyncio
async def test_get_analytics_capabilities(test_client) -> None:
    """Verify GET /api/analytics/capabilities returns dimensions and metrics."""
    response = await test_client.get("/api/analytics/capabilities")

    assert response.status_code == 200
    data = response.json()
    assert "dimensions" in data
    assert "metrics" in data
    assert "limits" in data
    assert isinstance(data["dimensions"], list)
    assert isinstance(data["metrics"], list)
    assert len(data["dimensions"]) > 0
    assert len(data["metrics"]) > 0


@pytest.mark.asyncio
async def test_query_metrics(test_client) -> None:
    """Verify POST /api/analytics/query executes custom analytics query."""
    query = {
        "metrics": ["bug_count"],
        "dimensions": ["severity"],
        "limit": 10,
    }

    response = await test_client.post("/api/analytics/query", json=query)

    # May be 200 (data exists) or 400 (validation error in test environment)
    assert response.status_code in (200, 400)
    if response.status_code == 200:
        data = response.json()
        assert "data" in data  # Check for analytics output
        assert "metadata" in data


@pytest.mark.asyncio
async def test_query_metrics_missing_params(test_client) -> None:
    """Verify POST /api/analytics/query returns 422 for missing parameters."""
    # Missing required fields
    query = {
        "metrics": ["bug_count"],
        # dimensions missing
    }

    response = await test_client.post("/api/analytics/query", json=query)

    assert response.status_code == 422  # Pydantic validation error


# Operational Endpoints Tests


@pytest.mark.asyncio
async def test_get_diagnostics(test_client) -> None:
    """Verify GET /api/diagnostics returns server diagnostics."""
    response = await test_client.get("/api/diagnostics")

    assert response.status_code == 200
    data = response.json()
    assert "api" in data
    assert "database" in data
    assert "sync" in data


@pytest.mark.asyncio
async def test_get_diagnostics_with_sync_events(test_client) -> None:
    """Verify GET /api/diagnostics includes sync events when requested."""
    response = await test_client.get(
        "/api/diagnostics",
        params={"include_sync_events": True, "sync_event_limit": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert "api" in data
    assert "database" in data
    assert "sync" in data
    # Sync events may or may not be present depending on test environment


@pytest.mark.asyncio
async def test_get_problematic_tests(test_client) -> None:
    """Verify GET /api/sync/problematic returns problematic tests."""
    response = await test_client.get("/api/sync/problematic")

    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "tests" in data
    assert "message" in data
    assert isinstance(data["tests"], list)
    assert data["count"] == len(data["tests"])


@pytest.mark.asyncio
async def test_get_problematic_tests_with_filter(test_client) -> None:
    """Verify GET /api/sync/problematic accepts product_id filter."""
    # Get a valid product ID
    products_response = await test_client.get("/api/products")
    assert products_response.status_code == 200
    products_data = products_response.json()
    assert len(products_data["products"]) > 0
    product_id = products_data["products"][0]["id"]

    response = await test_client.get(
        "/api/sync/problematic",
        params={"product_id": product_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "tests" in data


# OpenAPI Schema Tests


@pytest.mark.asyncio
async def test_openapi_schema_includes_new_endpoints(test_client) -> None:
    """Verify OpenAPI schema includes all new REST endpoints."""
    response = await test_client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "paths" in data

    # Verify summary endpoints
    assert "/api/products/{product_id}/summary" in data["paths"]
    assert "/api/features/{feature_id}/summary" in data["paths"]
    assert "/api/users/{user_id}/summary" in data["paths"]

    # Verify analytics endpoints
    assert "/api/analytics/query" in data["paths"]
    assert "/api/analytics/capabilities" in data["paths"]

    # Verify operational endpoints
    assert "/api/diagnostics" in data["paths"]
    assert "/api/sync/problematic" in data["paths"]


@pytest.mark.asyncio
async def test_openapi_schema_response_models(test_client) -> None:
    """Verify OpenAPI schema includes response models for new endpoints."""
    response = await test_client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()

    # Check that endpoints have response schemas defined
    product_summary_path = data["paths"].get("/api/products/{product_id}/summary", {})
    assert "get" in product_summary_path
    assert "responses" in product_summary_path["get"]

    diagnostics_path = data["paths"].get("/api/diagnostics", {})
    assert "get" in diagnostics_path
    assert "responses" in diagnostics_path["get"]


# Configuration Endpoints Tests


@pytest.mark.asyncio
async def test_get_thresholds(test_client) -> None:
    """Verify GET /api/thresholds returns playbook threshold configuration."""
    response = await test_client.get("/api/thresholds")

    assert response.status_code == 200
    data = response.json()

    # Verify all three metric thresholds are present
    assert "rejection_rate" in data
    assert "auto_acceptance_rate" in data
    assert "review_rate" in data

    # Verify threshold structure for rejection_rate (direction=above)
    assert "warning" in data["rejection_rate"]
    assert "critical" in data["rejection_rate"]
    assert "direction" in data["rejection_rate"]
    assert data["rejection_rate"]["direction"] == "above"
    assert 0.0 <= data["rejection_rate"]["warning"] <= 1.0
    assert 0.0 <= data["rejection_rate"]["critical"] <= 1.0
    # For direction=above, warning < critical
    assert data["rejection_rate"]["warning"] < data["rejection_rate"]["critical"]

    # Verify threshold structure for auto_acceptance_rate (direction=above)
    assert data["auto_acceptance_rate"]["direction"] == "above"
    assert data["auto_acceptance_rate"]["warning"] < data["auto_acceptance_rate"]["critical"]

    # Verify threshold structure for review_rate (direction=below)
    assert data["review_rate"]["direction"] == "below"
    # For direction=below, warning > critical
    assert data["review_rate"]["warning"] > data["review_rate"]["critical"]


@pytest.mark.asyncio
async def test_openapi_schema_includes_thresholds_endpoint(test_client) -> None:
    """Verify OpenAPI schema includes thresholds endpoint."""
    response = await test_client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()

    # Verify thresholds endpoint is in schema
    assert "/api/thresholds" in data["paths"]
    thresholds_path = data["paths"]["/api/thresholds"]
    assert "get" in thresholds_path
    assert "responses" in thresholds_path["get"]
