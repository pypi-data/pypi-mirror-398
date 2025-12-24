# REST API Reference

**Version:** 1.1.0
**Last Updated:** 2025-12-21
**Status:** Production Ready

## Overview

The TestIO MCP Server provides a REST API with **full parity** to MCP tools. All 17 MCP tools have corresponding REST endpoints, enabling programmatic access for web applications, scripts, and automation.

### Access Points

| Endpoint | Purpose |
|----------|---------|
| `http://localhost:8080/docs` | Swagger UI (interactive explorer) |
| `http://localhost:8080/openapi.json` | OpenAPI 3.0 specification |
| `http://localhost:8080/redoc` | ReDoc documentation |
| `http://localhost:8080/health` | Health check |
| `http://localhost:8080/api/*` | REST API endpoints |

### Starting the Server

```bash
# HTTP mode (required for REST API)
uv run python -m testio_mcp serve --transport http --port 8080

# Production
uvx testio-mcp serve --transport http --port 8080
```

---

## Endpoints Summary

### Products

| Method | Endpoint | Description | MCP Equivalent |
|--------|----------|-------------|----------------|
| GET | `/api/products` | List products with filtering | `list_products` |
| GET | `/api/products/{id}/summary` | Product metadata with counts | `get_product_summary` |
| GET | `/api/products/{id}/tests` | List tests for product | `list_tests` |
| GET | `/api/products/{id}/features` | List features for product | `list_features` |

### Quality Reports

| Method | Endpoint | Description | MCP Equivalent |
|--------|----------|-------------|----------------|
| GET | `/api/quality-report` | Generate quality report (multi-product) | `generate_quality_report` |

**Query Parameters:**
- `product_ids` (required): Comma-separated product IDs (e.g., `598,599,600`)
- `test_ids` (optional): Filter to specific tests
- `start_date`, `end_date`: Date range filters
- `statuses`: Comma-separated test statuses

### Bugs

| Method | Endpoint | Description | MCP Equivalent |
|--------|----------|-------------|----------------|
| GET | `/api/bugs` | List bugs with filtering | `list_bugs` |
| GET | `/api/bugs/{id}/summary` | Detailed bug information | `get_bug_summary` |

### Thresholds

| Method | Endpoint | Description | MCP Equivalent |
|--------|----------|-------------|----------------|
| GET | `/api/thresholds` | Playbook health thresholds | - |

### Tests

| Method | Endpoint | Description | MCP Equivalent |
|--------|----------|-------------|----------------|
| GET | `/api/tests` | List tests (requires product_id) | `list_tests` |
| GET | `/api/tests/{id}/summary` | Test details with bugs | `get_test_summary` |

### Features

| Method | Endpoint | Description | MCP Equivalent |
|--------|----------|-------------|----------------|
| GET | `/api/features/{id}/summary` | Feature metadata with user stories | `get_feature_summary` |

### Users

| Method | Endpoint | Description | MCP Equivalent |
|--------|----------|-------------|----------------|
| GET | `/api/users` | List users (testers/customers) | `list_users` |
| GET | `/api/users/{id}/summary` | User metadata with activity | `get_user_summary` |

### Analytics

| Method | Endpoint | Description | MCP Equivalent |
|--------|----------|-------------|----------------|
| POST | `/api/analytics/query` | Custom metrics query | `query_metrics` |
| GET | `/api/analytics/capabilities` | Available dimensions/metrics | `get_analytics_capabilities` |

### Search

| Method | Endpoint | Description | MCP Equivalent |
|--------|----------|-------------|----------------|
| GET | `/api/search` | Full-text search (FTS5) | `search` |

### Server Management

| Method | Endpoint | Description | MCP Equivalent |
|--------|----------|-------------|----------------|
| GET | `/api/diagnostics` | Server health and stats | `get_server_diagnostics` |
| GET | `/api/sync/problematic` | Tests that failed to sync | `get_problematic_tests` |
| GET | `/health` | Basic health check | - |

---

## Common Parameters

### Pagination

Most list endpoints support pagination:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (1-indexed) |
| `per_page` | int | 100 | Items per page (max 200) |
| `offset` | int | 0 | Alternative: skip N items |

```bash
# Page-based
curl "http://localhost:8080/api/products?page=2&per_page=50"

# Offset-based
curl "http://localhost:8080/api/products?offset=50&per_page=50"
```

### Sorting

| Parameter | Type | Description |
|-----------|------|-------------|
| `sort_by` | string | Field to sort by |
| `sort_order` | string | `asc` or `desc` |

```bash
curl "http://localhost:8080/api/products?sort_by=title&sort_order=asc"
```

### Filtering

Filters vary by endpoint. Common patterns:

```bash
# Status filter (comma-separated or repeated)
curl "http://localhost:8080/api/tests?product_id=598&statuses=running,locked"
curl "http://localhost:8080/api/tests?product_id=598&statuses=running&statuses=locked"

# Type filter
curl "http://localhost:8080/api/products?product_type=website"

# Date filters (quality report)
curl "http://localhost:8080/api/quality-report?product_ids=598&start_date=2025-01-01&end_date=2025-12-31"

# Multi-product quality report
curl "http://localhost:8080/api/quality-report?product_ids=598,599,600"
```

---

## Example Requests

### List Products

```bash
curl -s "http://localhost:8080/api/products" | python3 -m json.tool
```

Response:
```json
{
  "total_count": 5,
  "page": 1,
  "per_page": 100,
  "products": [
    {
      "id": 598,
      "title": "Canva Web",
      "product_type": "website",
      "test_count": 150,
      "feature_count": 45
    }
  ]
}
```

### Get Test Summary

```bash
curl -s "http://localhost:8080/api/tests/109363/summary" | python3 -m json.tool
```

Response:
```json
{
  "test": {
    "id": 109363,
    "title": "Sprint 45 Regression",
    "status": "archived",
    "testing_type": "coverage"
  },
  "bugs": {
    "total_count": 23,
    "by_severity": {"critical": 2, "high": 8, "low": 13},
    "by_status": {"accepted": 20, "rejected": 3}
  }
}
```

### Query Metrics (POST)

```bash
curl -s -X POST "http://localhost:8080/api/analytics/query" \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": ["feature"],
    "metrics": ["bug_count", "test_count"],
    "filters": {"product_id": 598},
    "limit": 10
  }' | python3 -m json.tool
```

### Search

```bash
curl -s "http://localhost:8080/api/search?query=login&entities=bug,feature&limit=20"
```

---

## Error Handling

REST API uses standard HTTP status codes:

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | Request completed |
| 400 | Bad Request | Invalid parameters |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Schema validation failed |
| 500 | Server Error | Internal error |

### Error Response Format

```json
{
  "detail": "Product with ID 99999 not found"
}
```

For validation errors (422):
```json
{
  "detail": [
    {
      "loc": ["query", "product_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Python Client Example

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8080") as client:
        # List products
        products = await client.get("/api/products")
        print(products.json())

        # Get test summary
        test = await client.get("/api/tests/109363/summary")
        print(test.json())

        # Query metrics
        metrics = await client.post("/api/analytics/query", json={
            "dimensions": ["feature"],
            "metrics": ["bug_count"],
            "filters": {"product_id": 598}
        })
        print(metrics.json())

asyncio.run(main())
```

---

## OpenAPI Schema

The full OpenAPI 3.0 specification is available at:
- **JSON:** `http://localhost:8080/openapi.json`
- **Interactive:** `http://localhost:8080/docs` (Swagger UI)

All Pydantic models are auto-documented with:
- Field descriptions
- Type constraints (min/max, patterns)
- Example values
- Nested schema structures

---

## Related Documentation

- **[CLAUDE.md](../../CLAUDE.md)** - MCP tool catalog and usage
- **[MCP.md](MCP.md)** - MCP implementation patterns
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[MCP_SETUP.md](../../MCP_SETUP.md)** - Client configuration

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-21 | 1.1.0 | Updated for v0.4.0: Quality report endpoint refactored (`/api/quality-report`), added bugs/thresholds endpoints |
| 2025-12-03 | 1.0.0 | Initial REST API documentation |
