# ADR-005: Response Size Limits with Soft Warnings

**Status:** Partially Superseded - Continuation tokens removed, file export added

**Date:** 2025-11-04

**Updated:** 2025-11-18 - Continuation token examples replaced with current patterns

**Context:** Protecting users and systems from overwhelming responses while maintaining flexibility

---

## Context

Several MCP tools can return large datasets:
- `get_test_bugs`: Tests with 1000+ bugs
- `list_active_tests`: Products with 100+ active tests
- `get_test_activity_by_timeframe`: Hundreds of tests across many products
- Resources (`tests://active`): 225 products × 100+ tests each

### Problem

Large responses cause:
1. **Memory exhaustion** (server-side)
2. **Slow response times** (>5 seconds violates project requirements)
3. **Poor AI experience** (Claude/Cursor overwhelmed by massive JSON)
4. **Token waste** (AI context filled with data user may not need)
5. **API quota waste** (fetching thousands of items when user needs dozens)

### Alternative Approaches Considered

1. **No Limits**
   - Return everything, regardless of size
   - **Pros:** Complete data, simple
   - **Cons:** Memory issues, slow, poor UX

2. **Hard Limits with Errors**
   - Return error if result would exceed limit
   - **Pros:** Protects resources
   - **Cons:** Frustrating UX, no workaround for legitimate large queries

3. **Automatic Pagination (No User Control)**
   - Always paginate at fixed size (e.g., 100 items)
   - **Pros:** Predictable response sizes
   - **Cons:** Forces pagination even when user wants full dataset

4. **Soft Limits with Warnings**
   - Default limits with warnings when exceeded, allow override via parameter
   - **Pros:** Balances safety with flexibility, clear guidance
   - **Cons:** Slightly more complex implementation

5. **Configurable Limits per Tool**
   - Each tool has different default/max limits
   - **Pros:** Tool-specific optimization
   - **Cons:** Inconsistent UX, hard to configure

---

## Decision

**Use soft limits with warnings and user override capability.**

Each tool that returns variable-sized datasets will:
1. **Default to reasonable page size** (e.g., 100 items)
2. **Warn when results truncated** (clear message indicating more data exists)
3. **Allow user override** via `page_size` or `max_items` parameter
4. **Enforce maximum limit** (e.g., 1000 items) to prevent abuse
5. **Use pagination** (ADR-003) to provide access to remaining data

---

## Implementation

### 1. Configuration

```python
# src/testio_mcp/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ... existing settings ...

    # Response Size Limits
    DEFAULT_PAGE_SIZE: int = 100        # Default items per page
    MAX_PAGE_SIZE: int = 1000           # Maximum items user can request
    MAX_PRODUCTS_PER_QUERY: int = 50    # Max products for timeframe queries

    # Warning Thresholds
    WARN_RESPONSE_SIZE_MB: float = 5.0  # Warn if response > 5MB

    class Config:
        env_file = ".env"


settings = Settings()
```

### 2. Tool Implementation with Soft Limits (Updated 2025-11-18)

**Note:** Continuation tokens were removed. Current implementation uses standard pagination or file export.

```python
# Current approach: Standard pagination (list_tests example)

@mcp.tool()
async def list_tests(
    product_id: int,
    page: int = 1,
    per_page: int = DEFAULT_PAGE_SIZE,  # 100
    offset: int = 0,
    statuses: list[str] | None = None,
    ctx: Context = None,
) -> dict:
    """
    List tests with standard pagination.

    Args:
        product_id: Product identifier
        page: Page number (1-indexed)
        per_page: Items per page (default 100, max 200)
        offset: Additional offset for fine control
        statuses: Filter by test status
        ctx: FastMCP context

    Returns:
        Paginated list of tests
    """
    # Enforce maximum page size
    if per_page > MAX_PAGE_SIZE:  # 200
        raise ToolError(
            f"❌ per_page {per_page} exceeds maximum {MAX_PAGE_SIZE}\n"
            f"💡 Reduce per_page to {MAX_PAGE_SIZE} or less"
        )

    service = get_service(ctx, TestService)
    return await service.list_tests(
        product_id=product_id,
        page=page,
        per_page=per_page,
        offset=offset,
        statuses=statuses
    )
```

**For large datasets (>200 items), use file export instead:**

```python
# Current approach: File export (generate_ebr_report example)

@mcp.tool()
async def generate_ebr_report(
    product_id: int,
    output_file: str | None = None,  # Export to file for large reports
    ctx: Context = None,
) -> dict:
    """
    Generate EBR report with optional file export.

    For products with >100 tests, use output_file to avoid token limits.

    Args:
        product_id: Product identifier
        output_file: Optional path to export full report
                     (relative to ~/.testio-mcp/reports/ or absolute path)
        ctx: FastMCP context

    Returns:
        Report metadata if output_file specified, else full report JSON
    """
    service = get_service(ctx, ReportService)
    report = await service.generate_ebr_report(product_id)

    if output_file:
        # Write to file and return metadata only
        file_path = resolve_output_path(output_file)
        write_json_file(file_path, report)
        return {
            "file_path": str(file_path),
            "summary": report["summary"],
            "record_count": len(report["by_test"]),
            "file_size_bytes": file_path.stat().st_size,
        }

    # Return full report (may be truncated if too large)
    return report
```

### 3. Multi-Product Query Limits

```python
# src/testio_mcp/tools/get_test_activity_by_timeframe.py

@mcp.tool()
async def get_test_activity_by_timeframe(
    product_ids: list[str],
    start_date: str,
    end_date: str,
    include_bugs: bool = False,
    ctx: Context = None,
) -> dict:
    """
    Query test activity across products with soft limits.

    Args:
        product_ids: List of product IDs (max 50)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        include_bugs: Include bug counts
        ctx: FastMCP context

    Returns:
        Activity summary with warnings if applicable
    """
    # Enforce product limit
    if len(product_ids) > settings.MAX_PRODUCTS_PER_QUERY:
        return {
            "error": (
                f"❌ Query includes {len(product_ids)} products but maximum is "
                f"{settings.MAX_PRODUCTS_PER_QUERY}"
            ),
            "hint": (
                f"💡 Reduce number of products or split into multiple queries. "
                f"Example: First 50, then next 50"
            ),
            "products_requested": len(product_ids),
            "max_allowed": settings.MAX_PRODUCTS_PER_QUERY
        }

    # Validate date range (prevent years-long queries)
    from datetime import datetime, timedelta

    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    days_diff = (end - start).days

    if days_diff > 365:
        return {
            "error": f"❌ Date range {days_diff} days exceeds maximum 365 days",
            "hint": "💡 Reduce date range to 1 year or less for better performance",
            "date_range_days": days_diff,
            "max_allowed_days": 365
        }

    # Fetch activity (with concurrency limits from ADR-002)
    # ...

    # Build response with warnings
    result = {
        "products_queried": len(product_ids),
        "date_range": {"start": start_date, "end": end_date},
        "activity": activity_data,
    }

    # Warn if query is large (approaching limits)
    if len(product_ids) > 30:
        result["warning"] = (
            f"⚠️ Query includes {len(product_ids)} products (max {settings.MAX_PRODUCTS_PER_QUERY}). "
            "Consider filtering to specific products for faster results."
        )

    return result
```

### 4. Response Size Validation

```python
# src/testio_mcp/tools/helpers.py

import sys
from typing import Any


def validate_response_size(response: Any, max_size_mb: float = 5.0) -> dict:
    """
    Check response size and add warning if large.

    Args:
        response: Response object to check
        max_size_mb: Maximum size in MB before warning

    Returns:
        Response with added warning if too large
    """
    import json

    # Estimate size
    response_json = json.dumps(response)
    size_bytes = sys.getsizeof(response_json)
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > max_size_mb:
        if isinstance(response, dict):
            response["size_warning"] = (
                f"⚠️ Response size {size_mb:.1f}MB exceeds recommended {max_size_mb}MB. "
                "Consider using pagination or filtering to reduce size."
            )

    return response
```

---

## Consequences

### Positive

1. **Resource Protection**
   - Prevents memory exhaustion
   - Ensures response times meet <5 second requirement
   - Protects both server and AI client

2. **User Guidance**
   - Clear warnings explain *why* results are limited
   - Actionable hints tell users *how* to get more data
   - Empowers users to override when needed

3. **Flexibility**
   - Users can increase page_size for legitimate large queries
   - Maximum limit prevents abuse while allowing reasonable use
   - Pagination provides access to complete dataset

4. **Consistent UX**
   - All tools follow same limit/warning pattern
   - Predictable behavior across tools
   - Clear error messages with emojis (❌⚠️💡)

5. **Performance**
   - Default page size (100) balances completeness and speed
   - Forces users to think about what they actually need
   - Reduces wasted API calls and processing

### Negative

1. **Extra Parameters**
   - Tools have more parameters (page_size, max_items)
   - Slightly more complex for users
   - Need to document limits

2. **Not Foolproof**
   - Users can still request max_page_size (1000) and get slow responses
   - Can't prevent every performance issue
   - Relies on users reading warnings

3. **Arbitrary Limits**
   - Default 100 / max 1000 are somewhat arbitrary
   - May need tuning based on actual usage
   - Different tools may need different limits

### Neutral

1. **Tunable**
   - Limits are configurable via environment variables
   - Can adjust based on feedback
   - Easy to increase if TestIO API proves robust

2. **Composable with Other ADRs**
   - Works with pagination (ADR-003)
   - Complements concurrency limits (ADR-002)
   - Reduces cache pressure (ADR-004)

---

## User Experience Examples (Updated 2025-11-18)

### Example 1: Small Dataset (No Pagination Needed)

```json
// User queries product with 45 tests
{
  "product": {"id": 123, "name": "My Product"},
  "tests": [/* 45 tests */],
  "total_tests": 45,
  "page": 1,
  "per_page": 100,
  "total_pages": 1
}
```

**User sees:** All tests in one response. Simple and clean.

---

### Example 2: Large Dataset (Standard Pagination)

```json
// User queries product with 347 tests (default per_page=100)
{
  "product": {"id": 123, "name": "My Product"},
  "tests": [/* 100 tests */],
  "total_tests": 347,
  "page": 1,
  "per_page": 100,
  "total_pages": 4
}
```

**User sees:** First page of results with pagination info.

**To get next page:**
```
list_tests(product_id=123, page=2)
```

---

### Example 3: Large Dataset (File Export)

```json
// User exports EBR report to file (216 tests, avoids token limits)
{
  "file_path": "/Users/username/.testio-mcp/reports/canva-q3-2025.json",
  "summary": {
    "total_tests": 216,
    "total_bugs": 1840,
    "overall_acceptance_rate": 0.764
  },
  "record_count": 216,
  "file_size_bytes": 524288
}
```

**User sees:** File metadata only. Full report written to disk.

**Benefits:** No token limits, complete data, easy sharing.

---

### Example 4: Limit Exceeded (Error)

```json
// User requests per_page=500 (exceeds max_page_size=200)
// Raises ToolError exception
```

**Error message:**
```
❌ per_page 500 exceeds maximum 200
💡 Reduce per_page to 200 or less
```

**User sees:** Clear error with actionable guidance.

---

### Example 5: Date Range Too Large (Error)

```json
// User requests 2-year date range (exceeds 365 days max)
{
  "error": "❌ Date range 730 days exceeds maximum 365 days",
  "hint": "💡 Reduce date range to 1 year or less for better performance",
  "date_range_days": 730,
  "max_allowed_days": 365
}
```

**User sees:** Clear error with guidance on how to split query.

---

## Configuration Examples

### Development (Higher Limits)

```bash
# .env.development

DEFAULT_PAGE_SIZE=200           # Larger default for dev convenience
MAX_PAGE_SIZE=2000              # Higher max for testing
MAX_PRODUCTS_PER_QUERY=100      # Allow larger queries
WARN_RESPONSE_SIZE_MB=10.0      # Higher warning threshold
```

### Production (Conservative)

```bash
# .env.production

DEFAULT_PAGE_SIZE=100           # Balanced default
MAX_PAGE_SIZE=1000              # Reasonable max
MAX_PRODUCTS_PER_QUERY=50       # Prevent runaway queries
WARN_RESPONSE_SIZE_MB=5.0       # Conservative warning
```

### CI/CD (Very Conservative)

```bash
# .env.ci

DEFAULT_PAGE_SIZE=50            # Small pages for fast tests
MAX_PAGE_SIZE=200               # Low max to catch issues
MAX_PRODUCTS_PER_QUERY=10       # Prevent long-running tests
WARN_RESPONSE_SIZE_MB=1.0       # Low threshold to catch bloat
```

---

## Monitoring Recommendations

Track these metrics to validate/adjust limits:

1. **Page Size Distribution**
   - How often users override default page_size?
   - What page_size do they request?
   - Action: If >50% override, increase default

2. **Warning Frequency**
   - How often do warnings appear?
   - Do users fetch next page or stop?
   - Action: If warnings are ignored, may need hard limits

3. **Error Rate (Limit Exceeded)**
   - How often do users hit max_page_size?
   - Which tools trigger errors most?
   - Action: Increase max_page_size or improve docs

4. **Response Times by Size**
   - P95/P99 latency for different page sizes
   - When does performance degrade?
   - Action: Adjust limits based on observed performance

5. **Memory Usage**
   - Peak memory during large queries
   - Correlation with page_size
   - Action: Reduce limits if memory issues observed

---

## Related Decisions

- **ADR-002: Concurrency Limits** - Prevents overwhelming API with large queries
- **ADR-003: Pagination Strategy** - SUPERSEDED by standard pagination and file export
- **ADR-004: Cache Strategy** - Caching reduces need for large queries
- **STORY-023d: List Tests** - Implements standard page/offset pagination
- **STORY-025: File Export** - Handles large datasets via file export instead of pagination

---

## References

- [API Response Size Best Practices](https://cloud.google.com/blog/products/api-management/api-design-choosing-between-names-and-identifiers-in-urls)
- [Pagination vs Response Size Limits](https://www.moesif.com/blog/technical/api-design/REST-API-Design-Best-Practices-for-Pagination/)
- [Error Message UX Guidelines](https://uxdesign.cc/how-to-write-good-error-messages-858e4551cd4)

---

## Open Questions

1. **Should limits differ by tool?**
   - Current: Same default/max for all tools
   - Future: Tool-specific limits (bugs: 1000, tests: 500, etc.)
   - Decision: Start uniform, specialize if needed

2. **Should we add response size monitoring?**
   - Current: Optional size warning (not enforced)
   - Future: Track actual response sizes, alert if >10MB
   - Decision: Add in Story 8 (Error Handling & Polish)

3. **Should we support "unlimited" mode for admin users?**
   - Current: Max limits apply to everyone
   - Future: Allow trusted users to bypass limits
   - Decision: Defer to post-MVP (no multi-tenancy in MVP)

4. **Should warnings be opt-out?**
   - Current: Warnings always appear when results truncated
   - Future: Add `suppress_warnings=true` parameter
   - Decision: Defer until user feedback indicates warnings are annoying
