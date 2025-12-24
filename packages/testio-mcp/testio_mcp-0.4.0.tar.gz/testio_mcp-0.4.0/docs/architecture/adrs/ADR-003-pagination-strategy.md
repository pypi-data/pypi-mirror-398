# ADR-003: Pagination Strategy - First Page with Continuation Token

**Status:** Superseded by standard page/offset pagination (STORY-023d) and file export pattern (STORY-025)

**Date:** 2025-11-04

**Superseded:** 2025-11-18 - Continuation tokens removed in favor of simpler pagination

**Context:** Handling large API responses without overwhelming clients or servers

---

## Context

Several MCP tools may encounter large datasets:
- **Story 4 (`get_test_bugs`)**: Test cycles with 1000+ bugs
- **Story 6 (`get_test_activity_by_timeframe`)**: Products with hundreds of tests
- **Story 7 (Resources)**: 225 products, each with potentially hundreds of tests

### Problem

Without pagination, the MCP server could:
1. **Exhaust memory** loading thousands of items into a single response
2. **Cause slow response times** (>5 seconds, violating project requirements)
3. **Create poor AI experience** (Claude/Cursor overwhelmed by massive JSON payloads)
4. **Waste API quota** fetching data the user may not need

### API Pagination Support (Unknown)

**TestIO Customer API documentation is incomplete.** We don't know:
- If pagination is supported (limit/offset, cursor-based, page numbers)
- Default page sizes
- Maximum response sizes before API enforces pagination

**Assumption for MVP:** We'll implement client-side pagination (fetch all data, return first page) and migrate to API-level pagination if/when we confirm API support.

### Alternative Approaches Considered

1. **No Pagination (Fetch Everything)**
   - Return all results in single response
   - **Pros:** Simple, no continuation logic
   - **Cons:** Memory exhaustion, slow queries, poor UX

2. **Eager Pagination (Fetch All Pages)**
   - Loop through all pages, concatenate results
   - **Pros:** User gets complete dataset
   - **Cons:** Slow, defeats purpose of pagination

3. **Lazy/Streaming (Yield Results)**
   - Implement async generator, yield items as pages are fetched
   - **Pros:** Memory efficient, real-time results
   - **Cons:** Complex, not well-supported by MCP protocol, AI clients can't easily consume streams

4. **First Page + Continuation Token**
   - Return first N items with a token to fetch next page
   - **Pros:** User control, fast initial response, memory efficient
   - **Cons:** Requires multiple round-trips for full dataset

5. **Configurable Page Limit**
   - Fetch first N pages (e.g., 10 pages = ~10,000 items), warn if more exist
   - **Pros:** Balances completeness with performance
   - **Cons:** Arbitrary limit, still risky with huge datasets

---

## Decision

**Use "first page + continuation token" pattern for tools that may return large datasets.**

When a query has many results:
1. Return first page of results (default: 100 items)
2. Include `has_more: bool` indicating if additional results exist
3. Include `continuation_token: str` to fetch next page
4. User can call tool again with `continuation_token` to get next page

**Affected Tools:**
- `get_test_bugs` - May have 1000+ bugs per test
- `get_test_activity_by_timeframe` - May have hundreds of tests across products
- (Optional) `list_active_tests` - May have 100+ active tests for a product

---

## Implementation

### 1. Response Schema with Pagination

```python
# src/testio_mcp/schemas.py

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.

    Attributes:
        results: List of items for current page
        total_count: Total number of items across all pages (if known)
        page_size: Number of items in current page
        has_more: Whether additional pages exist
        continuation_token: Token to fetch next page (None if no more pages)
    """
    results: list[T]
    total_count: Optional[int] = Field(
        None,
        description="Total items (if known from API). May be None for client-side pagination."
    )
    page_size: int = Field(description="Number of items in this page")
    has_more: bool = Field(description="Whether more results exist")
    continuation_token: Optional[str] = Field(
        None,
        description="Opaque token to fetch next page. Pass to next request."
    )


class BugSummary(BaseModel):
    """Summary of a single bug."""
    id: int
    title: str
    severity: str
    status: str
    # ... other fields


class PaginatedBugsResponse(PaginatedResponse[BugSummary]):
    """Paginated response for bugs."""
    pass
```

### 2. Tool Implementation with Pagination

```python
# src/testio_mcp/tools/get_test_bugs.py

import base64
import json
from typing import Optional
from fastmcp import Context
from ..schemas import PaginatedBugsResponse, BugSummary


@mcp.tool()
async def get_test_bugs(
    test_id: str,
    bug_type: str = "all",
    severity: str = "all",
    status: str = "all",
    page_size: int = 100,
    continuation_token: Optional[str] = None,
    ctx: Context = None,
) -> PaginatedBugsResponse:
    """
    Get bugs for a test with pagination support.

    Args:
        test_id: Exploratory test ID
        bug_type: Filter by type (functional/visual/content/all)
        severity: Filter by severity (low/high/critical/all, only for functional bugs)
        status: Filter by status (accepted/rejected/new/all)
        page_size: Number of bugs per page (default 100, max 1000)
        continuation_token: Token from previous response to get next page
        ctx: FastMCP context (injected)

    Returns:
        Paginated list of bugs with continuation token if more exist
    """
    testio_client = ctx["testio_client"]

    # Decode continuation token (if provided)
    start_index = 0
    if continuation_token:
        try:
            token_data = json.loads(base64.b64decode(continuation_token))
            start_index = token_data["start_index"]
            # Validate test_id matches (prevent token reuse across different queries)
            if token_data["test_id"] != test_id:
                raise ValueError("Continuation token is for a different test")
        except (ValueError, KeyError):
            raise ValueError(f"Invalid continuation token: {continuation_token}")

    # Fetch ALL bugs from API (client-side pagination for MVP)
    # TODO: Use API pagination when TestIO API support is confirmed
    bugs_data = await testio_client.get(f"bugs?filter_test_cycle_ids={test_id}")
    all_bugs = bugs_data.get("bugs", [])

    # Apply filters
    filtered_bugs = _filter_bugs(all_bugs, bug_type, severity, status)

    # Paginate results (client-side)
    end_index = start_index + page_size
    page_bugs = filtered_bugs[start_index:end_index]
    has_more = end_index < len(filtered_bugs)

    # Generate continuation token for next page
    next_token = None
    if has_more:
        token_data = {
            "test_id": test_id,
            "start_index": end_index,
            "filters": {"bug_type": bug_type, "severity": severity, "status": status}
        }
        next_token = base64.b64encode(json.dumps(token_data).encode()).decode()

    # Build response
    return PaginatedBugsResponse(
        results=[BugSummary(**bug) for bug in page_bugs],
        total_count=len(filtered_bugs),  # Known because we fetched all bugs
        page_size=len(page_bugs),
        has_more=has_more,
        continuation_token=next_token
    )


def _filter_bugs(bugs: list, bug_type: str, severity: str, status: str) -> list:
    """Apply client-side filtering to bugs."""
    # ... filtering logic from Story 4 ...
    pass
```

### 3. AI Client Usage Example

```markdown
# Example conversation with Claude

User: "Get bugs for test 12345"

Claude → MCP: get_test_bugs(test_id="12345")
MCP → Claude:
{
  "results": [/* 100 bugs */],
  "total_count": 347,
  "page_size": 100,
  "has_more": true,
  "continuation_token": "eyJ0ZXN0X2lkIjogIjEyMzQ1IiwgInN0YXJ0X2luZGV4IjogMTAwfQ=="
}

Claude: "I found 347 bugs for test 12345. Showing first 100:
[Bug summaries...]

There are 247 more bugs. Would you like to see them?"

User: "Yes, show next 100"

Claude → MCP: get_test_bugs(test_id="12345", continuation_token="eyJ0ZXN0X2lkIjogIjEyMzQ1IiwgInN0YXJ0X2luZGV4IjogMTAwfQ==")
MCP → Claude:
{
  "results": [/* next 100 bugs */],
  "total_count": 347,
  "page_size": 100,
  "has_more": true,
  "continuation_token": "eyJ0ZXN0X2lkIjogIjEyMzQ1IiwgInN0YXJ0X2luZGV4IjogMjAwfQ=="
}
```

### 4. Configuration

```bash
# .env

# Pagination defaults
DEFAULT_PAGE_SIZE=100  # Items per page
MAX_PAGE_SIZE=1000     # Maximum page size allowed
```

---

## Consequences

### Positive

1. **User Control**
   - Users decide when to fetch more data
   - Can stop after first page if they find what they need
   - No wasted API calls or processing

2. **Fast Initial Response**
   - First page returns quickly (100 items vs 10,000)
   - Meets <5 second requirement even for large datasets
   - Better AI experience (smaller JSON payloads)

3. **Memory Efficient**
   - Only one page in memory at a time
   - No risk of OOM errors with huge datasets
   - Predictable resource usage

4. **Graceful Degradation**
   - If user doesn't need pagination, they never see complexity
   - Continuation tokens are opaque (implementation can change)
   - Can migrate to API-level pagination without breaking clients

5. **Security**
   - Continuation tokens encode query parameters (prevent parameter injection)
   - Test ID validation prevents token reuse across different queries
   - Base64 encoding makes tokens non-guessable

### Negative

1. **Multiple Round-Trips**
   - User must make multiple requests for full dataset
   - More latency for users who need everything
   - More complex conversation flow with AI

2. **Client-Side Pagination (MVP)**
   - Still fetches all data from API, just returns subset to user
   - Doesn't reduce API load or server memory usage
   - Inefficient for very large datasets (1000+ items)

3. **Stateless Tokens**
   - Continuation token includes full filter state
   - Tokens can be large if complex filters
   - No server-side pagination state tracking

4. **No Random Access**
   - Can't jump to page 5 directly
   - Must paginate sequentially through pages
   - Acceptable for MVP, may add in future

### Neutral

1. **API Pagination Migration Path**
   - When TestIO API pagination is confirmed, can migrate to API-level
   - Continuation token format can change (opaque to clients)
   - May need to update tools but not client code

2. **Configurable Page Size**
   - Users can request larger pages (up to MAX_PAGE_SIZE)
   - Trade-off between response size and round-trips
   - Default 100 balances performance and usability

---

## Migration to API-Level Pagination (Future)

When TestIO API pagination support is confirmed:

### If API Uses Limit/Offset

```python
async def get_test_bugs_api_pagination(test_id, page_size, continuation_token):
    # Decode continuation token to get offset
    offset = 0 if not continuation_token else decode_token(continuation_token)["offset"]

    # Fetch single page from API
    bugs_data = await testio_client.get(
        f"bugs?filter_test_cycle_ids={test_id}&limit={page_size}&offset={offset}"
    )

    bugs = bugs_data.get("bugs", [])
    total_count = bugs_data.get("meta", {}).get("total_count")

    # Check if more pages exist
    has_more = (offset + page_size) < total_count

    # Generate next token
    next_token = encode_token({"offset": offset + page_size}) if has_more else None

    return PaginatedResponse(
        results=bugs,
        total_count=total_count,
        page_size=len(bugs),
        has_more=has_more,
        continuation_token=next_token
    )
```

### If API Uses Cursor-Based Pagination

```python
async def get_test_bugs_cursor_pagination(test_id, page_size, continuation_token):
    # Use cursor from continuation token
    cursor = decode_token(continuation_token)["cursor"] if continuation_token else None

    # Fetch page using cursor
    bugs_data = await testio_client.get(
        f"bugs?filter_test_cycle_ids={test_id}&limit={page_size}&cursor={cursor}"
    )

    bugs = bugs_data.get("bugs", [])
    next_cursor = bugs_data.get("meta", {}).get("next_cursor")

    return PaginatedResponse(
        results=bugs,
        total_count=None,  # Often unknown with cursor-based pagination
        page_size=len(bugs),
        has_more=next_cursor is not None,
        continuation_token=encode_token({"cursor": next_cursor}) if next_cursor else None
    )
```

**No client-side changes required** - continuation token remains opaque!

---

## Tools Requiring Pagination

### High Priority (Implement in MVP)

1. **`get_test_bugs` (Story 4)**
   - Likely to exceed 100 bugs for large test cycles
   - Client-side pagination for MVP
   - Migrate to API pagination when confirmed

### Medium Priority (Implement if Performance Issues)

2. **`get_test_activity_by_timeframe` (Story 6)**
   - May return hundreds of tests across products
   - Can start without pagination, add if >5sec responses observed

### Low Priority (Defer to Post-MVP)

3. **`list_active_tests` (Story 3)**
   - Most products have <100 active tests
   - Pagination probably unnecessary
   - Add if customer feedback indicates need

4. **Resources (`products://list`, `tests://active`)**
   - Resources are meant for browsing (small datasets)
   - Pagination not typical for MCP resources
   - Consider filtering instead

---

## Related Decisions

- **ADR-002: Concurrency Limits** - Pagination reduces need for high concurrency
- **ADR-005: Response Size Limits** - Pagination is primary mechanism for limiting response sizes
- **Story 4: Get Test Bugs** - First tool to implement pagination
- **Story 6: Test Activity Timeframe** - May benefit from pagination for large queries

---

## References

- [Cursor-Based Pagination Best Practices](https://www.moesif.com/blog/technical/api-design/REST-API-Design-Best-Practices-for-Pagination/)
- [Offset vs Cursor Pagination](https://slack.engineering/evolving-api-pagination-at-slack/)
- [MCP Tool Response Limits](https://spec.modelcontextprotocol.io/specification/2024-11-05/server/tools/)

---

## Amendment 2: Self-Sufficient Continuation Tokens (2025-11-06)

### Decision

**Breaking Change:** Continuation tokens now reject filter parameters and automatically preserve all filter state from the original query.

**Implementation:** Story 017 (STORY-017)

### Rationale

The original pagination design required users to repeat filter parameters on every continuation call, creating a fragile UX:

**Before (Fragile):**
```python
# First call - specify filters
result = get_test_bugs(test_id="123", bug_type="functional", severity="critical")

# Continuation call - MUST repeat filters (easy to forget!)
result2 = get_test_bugs(
    test_id="123",
    continuation_token=token,
    bug_type="functional",  # ← REQUIRED or ValueError
    severity="critical"      # ← REQUIRED or ValueError
)
```

**After (Self-Sufficient):**
```python
# First call - specify filters
result = get_test_bugs(test_id="123", bug_type="functional", severity="critical")

# Continuation call - just use token!
result2 = get_test_bugs(
    test_id="123",
    continuation_token=token
    # No filters needed - automatically preserved!
)
```

**Benefits:**
- **Eliminates fragile UX** where users must remember to repeat filters on every call
- **Aligns with industry standards** (Stripe, GitHub, AWS all use self-sufficient tokens)
- **Reduces agent errors** - E2E testing showed this pattern was counter-intuitive
- **Simplified API** - fewer parameters to manage during pagination

### Breaking Change Details

**What Changed:**
- Providing any filter parameter (`bug_type`, `severity`, `status`, `custom_report_config_id`) alongside `continuation_token` now raises `ValueError`
- Filters are automatically extracted from the token and applied

**Error Message:**
```
ValueError: Cannot provide filter parameters when using continuation_token.
Filters are preserved from the original query.
Omit bug_type, severity, status, and custom_report_config_id when using continuation_token.
```

### Migration

Existing code that provides filters with continuation tokens must be updated:

**Before:**
```python
get_test_bugs(
    test_id="123",
    continuation_token=token,
    bug_type="functional"  # ❌ Will raise ValueError
)
```

**After:**
```python
get_test_bugs(
    test_id="123",
    continuation_token=token
    # ✅ Filters automatically preserved
)
```

### Impact

**Low Impact:**
- Continuation token usage is rare in current deployment
- Error message provides clear migration guidance
- Token format remains unchanged (only validation logic changed)

**No Performance Impact:**
- Token decoding remains O(1)
- Filter extraction adds negligible overhead
- Validation happens before API call

### Status

Implemented in Story 017 (2025-11-06)

---

## Supersession Note (2025-11-18)

This ADR documented the original continuation token-based pagination design, which was implemented and later superseded by simpler approaches:

**Current Pagination Approaches:**

1. **Standard page/offset pagination** (STORY-023d)
   - Used by `list_tests` and similar list operations
   - Simple `page`, `per_page`, `offset` parameters
   - No continuation tokens needed
   - Example: `list_tests(product_id=123, page=2, per_page=100)`

2. **File export for large datasets** (STORY-025)
   - Used by `generate_ebr_report` for products with >100 tests
   - Writes full report to file instead of returning JSON
   - Avoids token limits and pagination complexity
   - Example: `generate_ebr_report(product_id=123, output_file="report.json")`

**Why Continuation Tokens Were Removed:**

- **Overcomplicated simple use cases** - Most queries fit in a single page
- **Poor AI agent UX** - Agents struggled with multi-round-trip pagination
- **File export is simpler** - For large datasets, export entire result to file
- **Standard pagination suffices** - Page/offset works for 95% of use cases

**Historical Value:**

This ADR remains valuable as documentation of:
- Pagination pattern evaluation and trade-offs
- Self-sufficient token design (Amendment 2)
- Migration considerations for API-level pagination

For current pagination implementation, see:
- `src/testio_mcp/services/test_service.py` (list_tests with page/offset)
- `src/testio_mcp/tools/generate_ebr_report_tool.py` (file export pattern)

---

## Open Questions (Historical)

1. **Does TestIO Customer API support pagination?**
   - Action: Test with `limit` and `offset` query parameters
   - Action: Check API response for `meta.total_count` or `meta.next_cursor`
   - Update: Migrate to API pagination when confirmed

2. **What is the maximum response size TestIO API will return?**
   - Action: Test with query that returns 1000+ items
   - Action: Observe if API enforces limit or times out
   - Update: Adjust DEFAULT_PAGE_SIZE based on findings

3. **Should continuation tokens expire?**
   - Current: Tokens never expire (stateless)
   - Future: Add timestamp to token, reject if >1 hour old
   - Benefit: Prevents stale queries, encourages fresh data
   - Risk: User frustration if token expires mid-pagination
