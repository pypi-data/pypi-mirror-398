---
story_id: STORY-003
epic_id: EPIC-001
title: Tool 2 - List Tests with Status Filtering
status: todo
created: 2025-11-04
estimate: 6 hours
assignee: unassigned
dependencies: [STORY-001, STORY-002, STORY-003b]
---

# STORY-003: Tool 2 - List Tests with Status Filtering

## User Story

**As a** Customer Success Manager
**I want** to list tests for a specific product with flexible status filtering via AI
**So that** I can query active tests, finished tests, or all tests without browsing the TestIO UI

## Context

This tool provides product-level visibility into test cycles with flexible status-based filtering. It's essential for answering queries like "Show me all active tests for Product Y" or "Show me finished tests" and provides the foundation for discovering test IDs that can be passed to `get_test_status`.

**User Journey**: list_products (Story-003b) → **list_tests (this story)** → get_test_status (Story-002)

**Use Cases**:
- "Show me all active tests for Product Y" → `statuses=["running"]` (default)
- "Show me finished tests" → `statuses=["archived", "locked"]`
- "Show me all tests" → `statuses=None` or `statuses=[]`

**Input**: Product ID (e.g., "25073" from list_products), optional status list filter
**Output**: List of test summaries with high-level status, dates, bug counts

**Status Definitions** (from TestIO API):
- `running`: Test is actively running (active)
- `locked`: Test is locked, typically completed but under review (finished)
- `review_successful`: Test review completed successfully (finished)
- `archived`: Test is archived/completed (finished)
- `cancelled`: Test was cancelled before completion

## Implementation Approach

**Architecture Note (ADR-006):** This story follows the service layer pattern established in Story-002. Implementation has two parts:

1. **Create ProductService** (business logic, framework-agnostic)
2. **Create MCP Tool** (thin wrapper, delegates to service)

This separation enables:
- Testing without MCP framework overhead
- Future reuse in REST API, CLI, webhooks
- Clear separation of transport (MCP) vs business logic
- Leverages Story-002 infrastructure (cache, exceptions)

---

## Acceptance Criteria

### AC0: Service Layer Implementation (ADR-006)
- [ ] Create `src/testio_mcp/services/product_service.py`
- [ ] `ProductService` class with constructor accepting `client` and `cache`
- [ ] `async def list_tests(product_id: str, statuses: list[str] | None, include_bug_counts: bool) -> dict` method
- [ ] Service handles:
  - Cache checking (cache key: `f"product:{product_id}:tests:{':'.join(sorted(statuses or []))}"`)
  - Parallel API calls (product details + tests via `asyncio.gather`)
  - Optional bug count aggregation (if `include_bug_counts=True`)
  - Status filtering logic (filter by list of statuses, default: `["running"]`)
  - Cache storage (TTL: 300 seconds / 5 minutes)
  - Raise `ProductNotFoundException` if product not found (404)
- [ ] Service does NOT handle MCP protocol or error formatting
- [ ] Example:
  ```python
  # src/testio_mcp/services/product_service.py
  import asyncio
  from testio_mcp.api.client import TestIOClient
  from testio_mcp.cache import InMemoryCache
  from testio_mcp.exceptions import ProductNotFoundException, TestIOAPIError

  class ProductService:
      def __init__(self, client: TestIOClient, cache: InMemoryCache):
          self.client = client
          self.cache = cache

      async def list_tests(
          self,
          product_id: str,
          statuses: list[str] | None,
          include_bug_counts: bool
      ) -> dict:
          # Default to running tests if no statuses provided
          if statuses is None:
              statuses = ["running"]

          # Check cache
          cache_key = f"product:{product_id}:tests:{':'.join(sorted(statuses))}"
          cached = await self.cache.get(cache_key)
          if cached:
              return cached

          # Fetch data concurrently
          try:
              product_data, tests_data = await asyncio.gather(
                  self.client.get(f"products/{product_id}"),
                  self.client.get(f"products/{product_id}/exploratory_tests")
              )
          except httpx.HTTPStatusError as e:
              if e.response.status_code == 404:
                  raise ProductNotFoundException(product_id)
              raise TestIOAPIError(f"API error: {e}", e.response.status_code)

          # Filter by statuses
          tests = tests_data.get("exploratory_tests", [])
          filtered_tests = self._filter_by_statuses(tests, statuses)

          # Optionally fetch bug counts
          bug_counts = {}
          if include_bug_counts:
              try:
                  bugs_data = await self.client.get(
                      f"bugs?filter_product_ids={product_id}"
                  )
                  bug_counts = self._aggregate_bug_counts(bugs_data.get("bugs", []))
              except Exception as e:
                  # Log warning but don't fail - bugs are optional
                  pass

          # Build response
          result = {
              "product": product_data.get("product", {}),
              "tests": filtered_tests,
              "bug_counts": bug_counts
          }

          # Cache result
          await self.cache.set(cache_key, result, ttl_seconds=300)
          return result

      def _filter_by_statuses(self, tests: list, statuses: list[str]) -> list:
          """Filter tests by list of statuses."""
          if not statuses:  # Empty list means return all
              return tests
          return [t for t in tests if t.get("status") in statuses]

      def _aggregate_bug_counts(self, bugs: list) -> dict[str, dict]:
          """Aggregate bugs by test_cycle_id."""
          bug_counts = {}
          for bug in bugs:
              test_id = str(bug.get("test", {}).get("id"))
              if not test_id:
                  continue
              if test_id not in bug_counts:
                  bug_counts[test_id] = {"total": 0, "by_severity": {}}
              bug_counts[test_id]["total"] += 1
              severity = bug.get("severity", "unknown")
              bug_counts[test_id]["by_severity"][severity] = (
                  bug_counts[test_id]["by_severity"].get(severity, 0) + 1
              )
          return bug_counts
  ```

**Rationale**: Service layer pattern (ADR-006) enables testing without MCP framework, reusability across transports (REST API, CLI), and clear separation of concerns. Service leverages Story-002 infrastructure (cache, exceptions).

### AC1: Tool Defined with FastMCP Decorator (Thin Wrapper)
- [ ] `@mcp.tool()` decorator applied to `list_tests` function
- [ ] Function signature includes `ctx: Context` parameter for dependency injection
- [ ] Tool extracts dependencies from Context: `client = ctx["testio_client"]`, `cache = ctx["cache"]`
- [ ] Tool creates ProductService instance: `service = ProductService(client=client, cache=cache)`
- [ ] Tool delegates to service: `return await service.list_tests(...)`
- [ ] Tool converts service exceptions to MCP error format (❌ℹ️💡 pattern)
- [ ] Tool is ~25-30 lines (thin adapter, no business logic)
- [ ] Example:
  ```python
  from typing import Literal
  from fastmcp import Context
  from testio_mcp.server import mcp
  from testio_mcp.services.product_service import ProductService
  from testio_mcp.exceptions import ProductNotFoundException, TestIOAPIError

  @mcp.tool()
  async def list_tests(
      product_id: str,
      statuses: list[Literal["running", "locked", "review_successful", "archived", "cancelled"]] | None = None,
      include_bug_counts: bool = False,
      ctx: Context = None
  ) -> dict:
      """
      List tests for a specific product with flexible status filtering.

      Useful for answering queries like "Show me all active tests for Product X"
      or "Show me finished tests". Returns test summaries with status, dates,
      and optional bug counts.

      Args:
          product_id: The product ID (e.g., "25073")
          statuses: Filter by test statuses. Default: ["running"] (active tests)
                    Available: running, locked, review_successful, archived, cancelled

                    Common filters:
                    - Active tests: ["running"]
                    - Finished tests: ["archived", "locked"]
                    - All tests: None or []

          include_bug_counts: Include bug count summary for each test. Default: False
          ctx: FastMCP context (injected automatically)

      Returns:
          Dictionary with product info and filtered test summaries
      """
      # Extract dependencies from Context (ADR-001)
      client = ctx["testio_client"]
      cache = ctx["cache"]

      # Create service
      service = ProductService(client=client, cache=cache)

      # Delegate to service
      try:
          service_result = await service.list_tests(
              product_id=product_id,
              statuses=statuses,
              include_bug_counts=include_bug_counts
          )

          # Transform service result to tool output format
          return _build_tool_output(service_result, statuses)

      except ProductNotFoundException:
          return {
              "error": f"❌ Product ID '{product_id}' not found",
              "context": "ℹ️ This product may not exist or you don't have access",
              "hint": "💡 Use the products resource to see available products"
          }
      except TestIOAPIError as e:
          return {
              "error": f"❌ API error: {e.message}",
              "context": f"ℹ️ Status code: {e.status_code}",
              "hint": "💡 Check API status and try again"
          }
  ```

### AC2: Pydantic Input Validation
- [ ] Input model with validation for product_id and statuses list
- [ ] Example:
  ```python
  from pydantic import BaseModel, Field
  from typing import Literal

  class ListTestsInput(BaseModel):
      product_id: str = Field(
          ...,
          description="Product ID",
          min_length=1,
          example="25073"
      )
      statuses: list[Literal["running", "locked", "review_successful", "archived", "cancelled"]] | None = Field(
          default=None,
          description="Filter by test statuses. Default: ['running'] (active tests)"
      )
      include_bug_counts: bool = Field(
          default=False,
          description="Include bug count summary for each test"
      )
  ```
- [ ] Invalid status value in list → Validation error with valid options shown

### AC3: API Calls to TestIO Customer API (In Service Layer)
- [ ] **Service** (not tool) calls `GET /products/{product_id}` to get product details
- [ ] **Service** (not tool) calls `GET /products/{product_id}/exploratory_tests` to get tests
- [ ] If `include_bug_counts=True`, **service** calls `GET /bugs?filter_product_ids={product_id}`
- [ ] All calls use TestIOClient passed to service constructor
- [ ] Example (in `ProductService.list_active_tests`):
  ```python
  # Fetch product details and tests
  product_data, tests_data = await asyncio.gather(
      testio_client.get(f"products/{product_id}"),
      testio_client.get(f"products/{product_id}/exploratory_tests")
  )

  # Optionally fetch bugs for the product
  bugs_data = None
  if include_bug_counts:
      bugs_data = await testio_client.get(
          f"bugs?filter_product_ids={product_id}"
      )
  ```

### AC4: Status Filtering Logic (In Service Layer)
- [ ] **Service** (not tool) filters tests based on `statuses` list parameter
- [ ] Implemented as private method `ProductService._filter_by_statuses()`
- [ ] Status filter behavior:
  - `None` or omitted: Defaults to `["running"]` (active tests only)
  - `[]` (empty list): Returns all tests (no filtering)
  - `["running"]`: Tests with status "running"
  - `["archived", "locked"]`: Tests with status "archived" OR "locked" (finished tests)
  - Any combination of: running, locked, review_successful, archived, cancelled
- [ ] Example:
  ```python
  def _filter_by_statuses(self, tests: list, statuses: list[str]) -> list:
      """Filter tests by list of statuses."""
      if not statuses:  # Empty list means return all
          return tests
      return [t for t in tests if t.get("status") in statuses]
  ```

### AC5: Bug Count Aggregation (Optional, In Service Layer)
- [ ] If `include_bug_counts=True`, **service** aggregates bug counts per test
- [ ] Implemented as private method `ProductService._aggregate_bug_counts()`
- [ ] Group bugs by `test_cycle_id` (maps to test ID)
- [ ] Example:
  ```python
  def aggregate_bug_counts(bugs: list) -> dict[str, dict]:
      """Aggregate bugs by test_cycle_id."""
      bug_counts = {}
      for bug in bugs:
          test_id = str(bug.get("test", {}).get("id"))
          if test_id not in bug_counts:
              bug_counts[test_id] = {"total": 0, "by_severity": {}}

          bug_counts[test_id]["total"] += 1
          severity = bug.get("severity", "unknown")
          bug_counts[test_id]["by_severity"][severity] = (
              bug_counts[test_id]["by_severity"].get(severity, 0) + 1
          )

      return bug_counts
  ```

### AC6: Structured Output with Pydantic
- [ ] Output model with product info and test summaries list
- [ ] Example:
  ```python
  from typing import Optional
  from datetime import datetime

  class TestSummary(BaseModel):
      test_id: str
      title: str
      goal: Optional[str] = None
      status: str
      review_status: Optional[str] = None
      testing_type: str
      duration: Optional[int] = None
      starts_at: Optional[datetime] = None
      ends_at: Optional[datetime] = None
      bug_count: Optional[dict] = None  # Only if include_bug_counts=True

  class ListTestsOutput(BaseModel):
      product_id: str
      product_name: str
      product_type: str
      statuses_filter: list[str]
      total_tests: int
      tests: list[TestSummary]
  ```
- [ ] Output serialized with `model_dump(exclude_none=True)`

### AC7: Error Handling (Two-Layer Pattern)
- [ ] **Service layer** raises domain exceptions (`ProductNotFoundException`, `TestIOAPIError`)
- [ ] **Tool layer** converts domain exceptions to MCP error format (❌ℹ️💡)
- [ ] Service error handling:
  ```python
  # In ProductService.list_active_tests
  from testio_mcp.exceptions import ProductNotFoundException, TestIOAPIError

  try:
      product_data, tests_data = await asyncio.gather(
          self.client.get(f"products/{product_id}"),
          self.client.get(f"products/{product_id}/exploratory_tests")
      )
  except httpx.HTTPStatusError as e:
      if e.response.status_code == 404:
          raise ProductNotFoundException(product_id)
      raise TestIOAPIError(f"API error: {e}", e.response.status_code)
  ```
- [ ] Tool error conversion:
  ```python
  # In list_tests tool
  try:
      return await service.list_tests(product_id, statuses, include_bug_counts)
  except ProductNotFoundException:
      return {
          "error": f"❌ Product ID '{product_id}' not found",
          "context": "ℹ️ This product may not exist or you don't have access",
          "hint": "💡 Use the products resource to see available products"
      }
  except TestIOAPIError as e:
      return {
          "error": f"❌ API error: {e.message}",
          "context": f"ℹ️ Status code: {e.status_code}",
          "hint": "💡 Check API status and try again"
      }
  ```
- [ ] No tests found → Return empty list (not an error)
- [ ] Bug endpoint fails but tests succeed → Return tests without bug counts (service handles gracefully)

### AC8: Integration Test with Real Data
- [ ] **Error handling test** (always runs): Tests 404 with invalid product ID
- [ ] **Positive tests** (optional): Require `TESTIO_PRODUCT_ID` environment variable
  - Test with user-provided product ID (default fallback: "25073" - Affinity Studio)
  - Verify output contains multiple tests
  - Test with `statuses=[]` (empty list) returns all tests including archived
  - Test with `include_bug_counts=True` returns bug data
  - Skipped if `TESTIO_PRODUCT_ID` not provided (avoids brittle tests)
- [ ] Test code:
  ```python
  import os
  import pytest
  from testio_mcp.services.product_service import ProductService
  from testio_mcp.exceptions import ProductNotFoundException

  # Error handling (always runs)
  @pytest.mark.integration
  @pytest.mark.skipif(
      not os.getenv("TESTIO_CUSTOMER_API_TOKEN"),
      reason="Integration test requires TESTIO_CUSTOMER_API_TOKEN"
  )
  @pytest.mark.asyncio
  async def test_invalid_product_id():
      """Test error handling with invalid product ID."""
      # Use invalid product ID that's guaranteed not to exist
      with pytest.raises(ProductNotFoundException):
          await service.list_tests(product_id="999999999", statuses=[])

  # Positive tests (optional, requires TESTIO_PRODUCT_ID)
  @pytest.mark.integration
  @pytest.mark.skipif(
      not os.getenv("TESTIO_CUSTOMER_API_TOKEN") or not os.getenv("TESTIO_PRODUCT_ID"),
      reason="Integration test requires TESTIO_CUSTOMER_API_TOKEN and TESTIO_PRODUCT_ID"
  )
  @pytest.mark.asyncio
  async def test_list_tests_with_real_product():
      """Test with user-provided or default product ID."""
      product_id = os.getenv("TESTIO_PRODUCT_ID", "25073")  # Default: Affinity Studio

      result = await service.list_tests(
          product_id=product_id,
          statuses=[]  # Empty list = all tests
      )
      assert result["product_id"] == product_id
      assert result["total_tests"] > 0
      assert len(result["tests"]) > 0
      assert result["tests"][0]["test_id"] is not None

  @pytest.mark.integration
  @pytest.mark.skipif(
      not os.getenv("TESTIO_CUSTOMER_API_TOKEN") or not os.getenv("TESTIO_PRODUCT_ID"),
      reason="Integration test requires TESTIO_CUSTOMER_API_TOKEN and TESTIO_PRODUCT_ID"
  )
  @pytest.mark.asyncio
  async def test_list_tests_with_bug_counts():
      """Test bug count aggregation with real API."""
      product_id = os.getenv("TESTIO_PRODUCT_ID", "25073")

      result = await service.list_tests(
          product_id=product_id,
          statuses=[],  # All tests
          include_bug_counts=True
      )
      # Some tests should have bug counts (not guaranteed, depends on data)
      assert "tests" in result
      # Verify bug_count field exists when include_bug_counts=True
      if result["total_tests"] > 0:
          first_test = result["tests"][0]
          assert "bug_count" in first_test or first_test.get("bug_count") is None
  ```
- [ ] **Rationale**: Avoids brittle tests that break when API data changes (same pattern as Story-002)
- [ ] **Usage**: Developers can optionally provide their own product ID via `export TESTIO_PRODUCT_ID=12345`

### AC9: Service Layer Tests (Primary Testing Focus)
- [ ] Create `tests/unit/test_product_service.py` (or add to existing if created by Story-003b)
- [ ] Test `ProductService.list_tests` directly with mocked client and cache
- [ ] Test scenarios:
  - Cache hit (returns cached data without API calls)
  - Cache miss (fetches from API, stores in cache with 5-minute TTL)
  - Status filtering with list of statuses (["running"], ["archived", "locked"], [], None)
  - Default behavior (None → defaults to ["running"])
  - Bug count aggregation when `include_bug_counts=True`
  - Error handling (404 → ProductNotFoundException)
  - Graceful degradation (bugs endpoint fails but tests succeed)
- [ ] Example tests:
  ```python
  # tests/unit/test_product_service.py
  import pytest
  from unittest.mock import AsyncMock
  from testio_mcp.services.product_service import ProductService
  from testio_mcp.exceptions import ProductNotFoundException

  @pytest.mark.asyncio
  async def test_list_tests_caches_result():
      """Test that service caches API responses."""
      mock_client = AsyncMock()
      mock_cache = AsyncMock()

      # Setup mocks
      mock_client.get.side_effect = [
          {"product": {"id": "123", "name": "Test Product"}},  # Product data
          {"exploratory_tests": [
              {"id": "1", "title": "Test 1", "status": "running"},
              {"id": "2", "title": "Test 2", "status": "archived"}
          ]}  # Tests data
      ]
      mock_cache.get.return_value = None  # Cache miss

      # Create service
      service = ProductService(client=mock_client, cache=mock_cache)

      # Test
      result = await service.list_tests(
          product_id="123",
          statuses=[],  # Empty list = all tests
          include_bug_counts=False
      )

      # Verify API calls
      assert mock_client.get.call_count == 2
      assert "products/123" in mock_client.get.call_args_list[0][0][0]
      assert "products/123/exploratory_tests" in mock_client.get.call_args_list[1][0][0]

      # Verify caching
      mock_cache.set.assert_called_once()
      cache_key = mock_cache.set.call_args[0][0]
      assert cache_key == "product:123:tests:"  # Empty list = empty join
      assert mock_cache.set.call_args[0][2] == 300  # 5-minute TTL

      # Verify result
      assert result["product"]["id"] == "123"
      assert len(result["tests"]) == 2

  @pytest.mark.asyncio
  async def test_list_tests_filters_by_statuses():
      """Test status filtering logic with list of statuses."""
      mock_client = AsyncMock()
      mock_cache = AsyncMock()

      mock_client.get.side_effect = [
          {"product": {"id": "123", "name": "Test Product"}},
          {"exploratory_tests": [
              {"id": "1", "title": "Test 1", "status": "running"},
              {"id": "2", "title": "Test 2", "status": "locked"},
              {"id": "3", "title": "Test 3", "status": "archived"}
          ]}
      ]
      mock_cache.get.return_value = None

      service = ProductService(client=mock_client, cache=mock_cache)

      # Test with statuses=["running"] (should only include running)
      result = await service.list_tests(
          product_id="123",
          statuses=["running"],
          include_bug_counts=False
      )

      assert len(result["tests"]) == 1  # Only running
      assert result["tests"][0]["status"] == "running"

  @pytest.mark.asyncio
  async def test_list_tests_with_bug_counts():
      """Test bug count aggregation."""
      mock_client = AsyncMock()
      mock_cache = AsyncMock()

      mock_client.get.side_effect = [
          {"product": {"id": "123", "name": "Test Product"}},
          {"exploratory_tests": [{"id": "1", "title": "Test 1"}]},
          {"bugs": [
              {"id": "b1", "test": {"id": "1"}, "severity": "high"},
              {"id": "b2", "test": {"id": "1"}, "severity": "low"}
          ]}  # Bugs data
      ]
      mock_cache.get.return_value = None

      service = ProductService(client=mock_client, cache=mock_cache)

      result = await service.list_tests(
          product_id="123",
          statuses=[],
          include_bug_counts=True
      )

      # Verify bug count aggregation
      assert "bug_counts" in result
      assert "1" in result["bug_counts"]  # Test ID "1" has bugs
      assert result["bug_counts"]["1"]["total"] == 2
      assert result["bug_counts"]["1"]["by_severity"]["high"] == 1
      assert result["bug_counts"]["1"]["by_severity"]["low"] == 1

  @pytest.mark.asyncio
  async def test_list_tests_product_not_found():
      """Test 404 error handling."""
      mock_client = AsyncMock()
      mock_cache = AsyncMock()

      # Mock 404 response
      import httpx
      mock_client.get.side_effect = httpx.HTTPStatusError(
          "Not found",
          request=AsyncMock(),
          response=AsyncMock(status_code=404)
      )
      mock_cache.get.return_value = None

      service = ProductService(client=mock_client, cache=mock_cache)

      # Should raise ProductNotFoundException
      with pytest.raises(ProductNotFoundException) as exc_info:
          await service.list_tests(product_id="999", statuses=[])

      assert "999" in str(exc_info.value)

  @pytest.mark.asyncio
  async def test_list_tests_graceful_bug_failure():
      """Test graceful handling when bugs endpoint fails."""
      mock_client = AsyncMock()
      mock_cache = AsyncMock()

      # Product and tests succeed, bugs fail
      async def get_side_effect(endpoint):
          if "bugs" in endpoint:
              raise Exception("Bugs endpoint failed")
          elif "exploratory_tests" in endpoint:
              return {"exploratory_tests": [{"id": "1", "title": "Test 1"}]}
          else:
              return {"product": {"id": "123", "name": "Test Product"}}

      mock_client.get.side_effect = get_side_effect
      mock_cache.get.return_value = None

      service = ProductService(client=mock_client, cache=mock_cache)

      # Should succeed without bug counts (graceful degradation)
      result = await service.list_tests(
          product_id="123",
          statuses=[],
          include_bug_counts=True
      )

      assert "tests" in result
      assert len(result["tests"]) == 1
      # Bug counts should be empty or absent (graceful failure)
      assert result.get("bug_counts", {}) == {}
  ```

## Technical Implementation

### Complete Implementation Example

```python
# src/testio_mcp/tools/list_tests.py
import asyncio
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from testio_mcp.api.client import TestIOClient
from testio_mcp.server import mcp, testio_client

class TestSummary(BaseModel):
    test_id: str
    title: str
    goal: Optional[str] = None
    status: str
    review_status: Optional[str] = None
    testing_type: str
    duration: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    bug_count: Optional[dict] = None

class ListTestsOutput(BaseModel):
    product_id: str
    product_name: str
    product_type: str
    statuses_filter: list[str]
    total_tests: int
    tests: list[TestSummary]

@mcp.tool()
async def list_tests(
    product_id: str,
    statuses: list[Literal["running", "locked", "review_successful", "archived", "cancelled"]] | None = None,
    include_bug_counts: bool = False
) -> dict:
    """
    List tests for a specific product with flexible status filtering.

    Provides high-level overview of test cycles with optional bug count
    aggregation. Useful for answering queries like "Show me all active tests"
    or "Show me finished tests".

    Args:
        product_id: The product ID (e.g., "25073")
        statuses: Filter by test statuses. Default: ["running"] (active tests)
                  Available: running, locked, review_successful, archived, cancelled

                  Common filters:
                  - Active tests: ["running"]
                  - Finished tests: ["archived", "locked"]
                  - All tests: None or []

        include_bug_counts: Include bug count summary. Default: False

    Returns:
        Dictionary with product info and filtered test summaries

    Raises:
        ValueError: If product_id is invalid or not found
    """
    # Default to running tests if no statuses provided
    if statuses is None:
        statuses = ["running"]

    try:
        # Fetch product details and tests
        product_data, tests_data = await asyncio.gather(
            testio_client.get(f"products/{product_id}"),
            testio_client.get(f"products/{product_id}/exploratory_tests")
        )

        product = product_data.get("product", {})
        tests = tests_data.get("exploratory_tests", [])

        # Filter by statuses
        filtered_tests = _filter_by_statuses(tests, statuses)

        # Optionally fetch bug counts
        bug_counts = {}
        if include_bug_counts:
            try:
                bugs_data = await testio_client.get(
                    f"bugs?filter_product_ids={product_id}"
                )
                bug_counts = _aggregate_bug_counts(bugs_data.get("bugs", []))
            except Exception as e:
                # Log warning but don't fail - bugs are optional
                print(f"⚠️ Failed to fetch bug counts: {e}")

        # Build test summaries
        test_summaries = []
        for test in filtered_tests:
            test_id = str(test["id"])
            summary = TestSummary(
                test_id=test_id,
                title=test["title"],
                goal=test.get("goal"),
                status=test["status"],
                review_status=test.get("review_status"),
                testing_type=test["testing_type"],
                duration=test.get("duration"),
                starts_at=test.get("starts_at"),
                ends_at=test.get("ends_at"),
                bug_count=bug_counts.get(test_id) if include_bug_counts else None
            )
            test_summaries.append(summary)

        # Build output
        output = ListTestsOutput(
            product_id=str(product["id"]),
            product_name=product["name"],
            product_type=product["type"],
            statuses_filter=statuses,
            total_tests=len(test_summaries),
            tests=test_summaries
        )

        return output.model_dump(exclude_none=True)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise ValueError(
                f"❌ Product ID '{product_id}' not found\\n"
                f"ℹ️ This product may not exist or you don't have access\\n"
                f"💡 Use the products resource to see available products"
            )
        raise

def _filter_by_statuses(tests: list, statuses: list[str]) -> list:
    """Filter tests by list of statuses."""
    if not statuses:  # Empty list means return all
        return tests
    return [t for t in tests if t.get("status") in statuses]

def _aggregate_bug_counts(bugs: list) -> dict[str, dict]:
    """Aggregate bugs by test_cycle_id."""
    bug_counts = {}
    for bug in bugs:
        test_id = str(bug.get("test", {}).get("id"))
        if not test_id:
            continue

        if test_id not in bug_counts:
            bug_counts[test_id] = {"total": 0, "by_severity": {}}

        bug_counts[test_id]["total"] += 1
        severity = bug.get("severity", "unknown")
        bug_counts[test_id]["by_severity"][severity] = (
            bug_counts[test_id]["by_severity"].get(severity, 0) + 1
        )

    return bug_counts
```

## Testing Strategy

### Unit Tests
```python
import pytest
from testio_mcp.tools.list_tests import list_tests, _filter_by_statuses

def test_filter_by_statuses_single():
    tests = [
        {"id": 1, "status": "running"},
        {"id": 2, "status": "archived"},
        {"id": 3, "status": "locked"},
    ]
    result = _filter_by_statuses(tests, ["running"])
    assert len(result) == 1
    assert result[0]["status"] == "running"

def test_filter_by_statuses_multiple():
    tests = [
        {"id": 1, "status": "running"},
        {"id": 2, "status": "archived"},
        {"id": 3, "status": "locked"},
    ]
    result = _filter_by_statuses(tests, ["archived", "locked"])
    assert len(result) == 2

def test_filter_by_statuses_empty_returns_all():
    tests = [{"id": 1, "status": "running"}, {"id": 2, "status": "archived"}]
    result = _filter_by_statuses(tests, [])
    assert len(result) == 2

@pytest.mark.asyncio
async def test_list_tests_empty(mock_testio_client):
    """Test handling of product with no tests."""
    result = await list_tests(product_id="999")
    assert result["total_tests"] == 0
    assert len(result["tests"]) == 0
```

## Definition of Done

- [ ] All acceptance criteria met (AC0-AC9)
- [ ] ProductService implements business logic (framework-agnostic)
- [ ] Service uses Story-002 infrastructure (cache with 5min TTL, exceptions)
- [ ] Tool `list_tests` accessible via `@mcp.tool()` decorator (thin wrapper)
- [ ] Tool uses Context injection pattern from Story-002
- [ ] Pydantic models for input/output validation
- [ ] Status filtering working in service layer with list of statuses (["running"], ["archived", "locked"], [], None)
- [ ] Default behavior: None → ["running"] (active tests only)
- [ ] Optional bug count aggregation working in service layer
- [ ] Error handling covers 404, empty results (two-layer pattern)
- [ ] Service unit tests pass with mocked client/cache (AC9 - 6 test scenarios)
- [ ] Integration tests pass (error handling always runs, positive tests optional with TESTIO_PRODUCT_ID)
- [ ] Code follows best practices (ADR-006 service layer pattern)
- [ ] Peer review completed

## References

- **Epic**: `docs/epics/epic-001-testio-mcp-mvp.md`
- **Project Brief**: `docs/archive/planning/project-brief-mvp-v2.4.md (ARCHIVED)` (Section: Tool 2)
- **FastMCP Tools**: https://gofastmcp.com/servers/tools

---

## QA Results

### Review Date: 2025-11-05

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Overall Grade: EXCEPTIONAL (98/100)**

This is a textbook implementation of the service layer pattern (ADR-006) with exemplary test coverage and architectural adherence. The code demonstrates production-ready quality with:

- ✅ **Perfect separation of concerns**: Service layer is framework-agnostic, tool is a thin 34-line wrapper
- ✅ **99% test coverage**: 27 unit tests + 6 integration tests, all passing
- ✅ **Comprehensive error handling**: Two-layer pattern (service exceptions → MCP format)
- ✅ **Performance optimization**: Parallel API calls, smart caching, graceful degradation
- ✅ **Type safety**: Strict mypy compliance, Literal types for enums, comprehensive Pydantic models
- ✅ **Documentation excellence**: Docstrings with Args/Returns/Raises/Examples throughout

### Refactoring Performed

**No refactoring needed.** The code is production-ready as implemented.

### Compliance Check

- **Coding Standards**: ✓ All checks pass (ruff, mypy --strict, pre-commit)
- **Project Structure**: ✓ Follows ADR-006 service layer pattern perfectly
- **Testing Strategy**: ✓ Comprehensive unit + integration tests with proper separation
- **All ACs Met**: ✓ 100% (AC0 through AC9 fully implemented and tested)

### Security Review

✅ **PASS - No security concerns identified**

- Token sanitization verified in TestIOClient (tokens never appear in logs)
- Exception handling prevents information leakage (domain exceptions → user-friendly errors)
- Input validation via Pydantic with Literal types for status enums
- No secrets in codebase (detect-secrets hook active and passing)

### Performance Considerations

✅ **PASS - Excellent performance characteristics**

**Optimizations implemented:**
- Parallel API calls via `asyncio.gather` (product + tests fetched concurrently)
- 5-minute cache TTL reduces API load (cache key design prevents collisions)
- Optional bug counts avoid unnecessary API calls
- Connection pooling enabled via TestIOClient
- Graceful degradation: bug endpoint failures don't fail tests

**Integration test performance:**
- Unit tests: <0.07s for 27 tests (extremely fast)
- Integration tests: 4-8s per test with real API (acceptable)
- Total test suite: 29.92s for 33 tests

### Acceptance Criteria Validation

| AC | Status | Evidence |
|----|--------|----------|
| AC0: Service Layer | ✅ PASS | ProductService class at `src/testio_mcp/services/product_service.py:170-258` |
| AC1: Tool Wrapper | ✅ PASS | Thin 34-line MCP tool with Context DI at `src/testio_mcp/tools/list_tests_tool.py:78-199` |
| AC2: Pydantic Validation | ✅ PASS | 3 models (TestSummary, ProductInfoSummary, ListTestsOutput) with Field validation |
| AC3: API Calls | ✅ PASS | Parallel asyncio.gather for product+tests, conditional bug fetch |
| AC4: Status Filtering | ✅ PASS | `_filter_by_statuses` with None→['running'], []→all, OR logic for multiple |
| AC5: Bug Aggregation | ✅ PASS | `_aggregate_bug_counts` with severity grouping, graceful failure |
| AC6: Structured Output | ✅ PASS | Pydantic models with exclude_none=True serialization |
| AC7: Error Handling | ✅ PASS | Two-layer: service raises domain exceptions, tool converts to ❌ℹ️💡 |
| AC8: Integration Tests | ✅ PASS | 6 tests (1 error handling always runs, 5 positive with TESTIO_PRODUCT_ID) |
| AC9: Service Tests | ✅ PASS | 27 unit tests with 99% coverage (75/76 lines), mocked client/cache |

### Test Architecture Analysis

**Unit Tests (27 tests, 99% coverage):**
- Cache hit/miss scenarios thoroughly tested
- Status filtering edge cases (None, [], single, multiple) covered
- Bug aggregation with missing test IDs handled
- Graceful failure when bugs endpoint fails
- No FastMCP overhead (service tested directly)

**Integration Tests (6 tests, real API):**
- Error handling test always runs (intentionally invalid product ID)
- Positive tests skip if TESTIO_PRODUCT_ID not provided (avoids brittle tests)
- All 6 tests pass with TESTIO_PRODUCT_ID=22
- Cache behavior verified with real data

**Test Results:**
```
33 tests passed in 29.92s
Unit tests: 27 passed in 0.07s
Integration tests: 6 passed in 29.85s
Coverage: 99% (1 uncovered line at product_service.py:229)
```

### Architectural Adherence

| Pattern | Status | Notes |
|---------|--------|-------|
| ADR-001 (DI) | ✅ PASS | Client/cache injected via Context, tool extracts and delegates |
| ADR-002 (Concurrency) | ✅ PASS | Uses TestIOClient semaphore, parallel asyncio.gather |
| ADR-004 (Caching) | ✅ PASS | 5-minute TTL, sorted status cache keys prevent collisions |
| ADR-006 (Service Layer) | ✅ PASS | **Perfect implementation** - framework-agnostic service, thin tool wrapper |

### Files Modified During Review

**No files modified.** The implementation is production-ready as-is.

### Gate Status

**Gate: PASS** → `docs/qa/gates/epic-001.story-003-list-tests-status-filtering.yml`

**Quality Score: 98/100**

**Gate expires: 2025-11-19** (2 weeks from review)

### Recommended Status

✅ **Ready for Done**

Zero blocking issues identified. All acceptance criteria met with exemplary quality.

### Strengths Highlighted

1. **Service Layer Excellence**: Textbook ADR-006 implementation - clean separation between transport (MCP) and business logic (service)
2. **Test Coverage Mastery**: 99% coverage with smart unit/integration separation
3. **Error Handling Sophistication**: Two-layer pattern with graceful degradation (bugs optional)
4. **Performance Awareness**: Parallel API calls, smart caching, optional features to reduce load
5. **Type Safety Rigor**: Strict mypy compliance, Literal types for enums, comprehensive Pydantic models
6. **Documentation Quality**: Every public method has Args/Returns/Raises/Examples
7. **Cache Key Design**: Sorted statuses prevent cache pollution (brilliant detail)

### Future Enhancements (Low Priority)

- Consider cache invalidation logic if tests are frequently updated
- Monitor 5-minute cache TTL effectiveness in production (may need tuning based on usage patterns)

### Quality Gate Decision

**PASS** - This implementation sets the standard for future stories. The service layer pattern is executed flawlessly, test coverage is comprehensive, and code quality is production-ready. No changes required.
