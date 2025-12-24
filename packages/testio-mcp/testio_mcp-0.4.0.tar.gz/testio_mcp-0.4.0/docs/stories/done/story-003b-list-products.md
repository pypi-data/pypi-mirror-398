---
story_id: STORY-003b
epic_id: EPIC-001
title: Tool - List Products (Discovery)
status: Ready for Review
created: 2025-11-05
estimate: 3 hours
assignee: James (Dev Agent)
dependencies: [STORY-001, STORY-002]
agent_model_used: claude-sonnet-4-5-20250929
---

# STORY-003b: Tool - List Products (Discovery)

## User Story

**As a** Customer Success Manager
**I want** to list all products I have access to via AI
**So that** I can discover available products and find product IDs for further queries

## Context

This is the **discovery/entry point** tool that enables users to navigate the product → test → bug hierarchy. Users need to know what products exist before they can query tests or bugs.

**User Journey**: "What products do I have access to?" → "Show me tests for Product X" → "Get details on Test Y"

**Use Case**: "List all my products" or "Find products matching 'Studio'"
**Input**: Optional search/filter parameters
**Output**: List of products with ID, name, type, description

## Implementation Approach

**Architecture Note (ADR-006):** This story follows the service layer pattern established in Story-002. Implementation has two parts:

1. **Create ProductService** (business logic, framework-agnostic)
2. **Create MCP Tool** (thin wrapper, delegates to service)

This is simpler than Story-003 (list_active_tests) - no bug aggregation, simpler filtering.

---

## Acceptance Criteria

### AC0: Service Layer Implementation (ADR-006)

- [ ] Create `src/testio_mcp/services/product_service.py` (if not exists from Story-003)
- [ ] `ProductService` class with constructor accepting `client` and `cache`
- [ ] `async def list_products(search: str | None, product_type: str | None) -> dict` method
- [ ] Service handles:
  - Cache checking (cache key: `f"products:list:{search}:{product_type}"`)
  - API call to GET /products
  - Optional filtering by search term (name/description match)
  - Optional filtering by product_type
  - Cache storage (TTL: 3600 seconds / 1 hour - products rarely change)
  - Raise `TestIOAPIError` on API failures
- [ ] Service does NOT handle MCP protocol or error formatting
- [ ] Example:
  ```python
  # src/testio_mcp/services/product_service.py
  from testio_mcp.client import TestIOClient
  from testio_mcp.cache import InMemoryCache
  from testio_mcp.exceptions import TestIOAPIError
  import httpx

  class ProductService:
      def __init__(self, client: TestIOClient, cache: InMemoryCache):
          self.client = client
          self.cache = cache

      async def list_products(
          self,
          search: str | None = None,
          product_type: str | None = None
      ) -> dict:
          # Check cache
          cache_key = f"products:list:{search}:{product_type}"
          cached = await self.cache.get(cache_key)
          if cached:
              return cached

          # Fetch from API
          try:
              response = await self.client.get("products")
              products = response.get("products", [])
          except httpx.HTTPStatusError as e:
              raise TestIOAPIError(f"API error: {e}", e.response.status_code)

          # Apply filters
          filtered_products = self._apply_filters(products, search, product_type)

          # Build result
          result = {
              "total_count": len(filtered_products),
              "filters_applied": {
                  "search": search,
                  "product_type": product_type
              },
              "products": filtered_products
          }

          # Cache result (1 hour - products rarely change)
          await self.cache.set(cache_key, result, ttl_seconds=3600)
          return result

      def _apply_filters(
          self,
          products: list,
          search: str | None,
          product_type: str | None
      ) -> list:
          """Apply search and type filters to products."""
          filtered = products

          # Filter by search term (case-insensitive, name or description)
          if search:
              search_lower = search.lower()
              filtered = [
                  p for p in filtered
                  if search_lower in p.get("name", "").lower()
                  or search_lower in p.get("description", "").lower()
              ]

          # Filter by product type
          if product_type:
              filtered = [p for p in filtered if p.get("type") == product_type]

          return filtered
  ```

**Rationale**: Service layer pattern (ADR-006) enables testing without MCP framework, reusability across transports. Longer cache TTL (1 hour) since products rarely change (per ADR-004).

### AC1: Tool Defined with FastMCP Decorator (Thin Wrapper)

- [ ] `@mcp.tool()` decorator applied to `list_products` function
- [ ] Function signature includes `ctx: Context` parameter for dependency injection
- [ ] Tool extracts dependencies from Context: `client = ctx["testio_client"]`, `cache = ctx["cache"]`
- [ ] Tool creates ProductService instance: `service = ProductService(client=client, cache=cache)`
- [ ] Tool delegates to service: `return await service.list_products(...)`
- [ ] Tool converts service exceptions to MCP error format (❌ℹ️💡 pattern)
- [ ] Tool is ~20-25 lines (thin adapter, no business logic)
- [ ] Example:
  ```python
  from fastmcp import Context
  from testio_mcp.server import mcp
  from testio_mcp.services.product_service import ProductService
  from testio_mcp.exceptions import TestIOAPIError

  @mcp.tool()
  async def list_products(
      search: str | None = None,
      product_type: str | None = None,
      ctx: Context = None
  ) -> dict:
      """
      List all products accessible to the user.

      Discovery tool for navigating product → test → bug hierarchy.
      Returns product IDs needed for list_active_tests and other tools.

      Args:
          search: Optional search term (filters by name/description)
          product_type: Optional filter by product type
          ctx: FastMCP context (injected automatically)

      Returns:
          Dictionary with list of products and metadata
      """
      # Extract dependencies from Context (ADR-001)
      client = ctx["testio_client"]
      cache = ctx["cache"]

      # Create service
      service = ProductService(client=client, cache=cache)

      # Delegate to service
      try:
          return await service.list_products(
              search=search,
              product_type=product_type
          )
      except TestIOAPIError as e:
          return {
              "error": f"❌ API error: {e.message}",
              "context": f"ℹ️ Status code: {e.status_code}",
              "hint": "💡 Check API status and authentication"
          }
  ```

### AC2: Pydantic Input Validation

- [ ] Input model with optional search and product_type parameters
- [ ] Example:
  ```python
  from pydantic import BaseModel, Field
  from typing import Optional

  class ListProductsInput(BaseModel):
      search: Optional[str] = Field(
          default=None,
          description="Search term (filters by name or description)",
          max_length=100,
          example="studio"
      )
      product_type: Optional[str] = Field(
          default=None,
          description="Filter by product type (e.g., 'website', 'mobile')",
          max_length=50,
          example="website"
      )
  ```

### AC3: API Call to TestIO Customer API (In Service Layer)

- [ ] **Service** (not tool) calls `GET /products`
- [ ] Uses TestIOClient passed to service constructor
- [ ] Example (in `ProductService.list_products`):
  ```python
  response = await self.client.get("products")
  products = response.get("products", [])
  ```

### AC4: Filtering Logic (In Service Layer)

- [ ] **Service** (not tool) implements filtering as private method `_apply_filters()`
- [ ] Filters applied:
  - **Search**: Case-insensitive substring match on `name` OR `description`
  - **Product type**: Exact match on `type` field
- [ ] Example:
  ```python
  def _apply_filters(
      self,
      products: list,
      search: str | None,
      product_type: str | None
  ) -> list:
      """Apply search and type filters to products."""
      filtered = products

      if search:
          search_lower = search.lower()
          filtered = [
              p for p in filtered
              if search_lower in p.get("name", "").lower()
              or search_lower in p.get("description", "").lower()
          ]

      if product_type:
          filtered = [p for p in filtered if p.get("type") == product_type]

      return filtered
  ```

### AC5: Structured Output with Pydantic

- [ ] Output model with product list and metadata
- [ ] Example:
  ```python
  from datetime import datetime

  class ProductSummary(BaseModel):
      product_id: str
      name: str
      type: str
      description: str | None = None
      created_at: datetime | None = None

  class ListProductsOutput(BaseModel):
      total_count: int
      filters_applied: dict
      products: list[ProductSummary]
  ```
- [ ] Output serialized with `model_dump(exclude_none=True)`

### AC6: Error Handling (Two-Layer Pattern)

- [ ] **Service layer** raises domain exceptions (`TestIOAPIError`)
- [ ] **Tool layer** converts domain exceptions to MCP error format (❌ℹ️💡)
- [ ] Service error handling:
  ```python
  # In ProductService.list_products
  try:
      response = await self.client.get("products")
  except httpx.HTTPStatusError as e:
      raise TestIOAPIError(f"API error: {e}", e.response.status_code)
  ```
- [ ] Tool error conversion:
  ```python
  # In list_products tool
  try:
      return await service.list_products(search, product_type)
  except TestIOAPIError as e:
      return {
          "error": f"❌ API error: {e.message}",
          "context": f"ℹ️ Status code: {e.status_code}",
          "hint": "💡 Check API status and authentication"
      }
  ```
- [ ] No products found → Return empty list (not an error)

### AC7: Caching Strategy (ADR-004)

- [ ] Service caches results with 1-hour TTL (products rarely change)
- [ ] Cache key format: `f"products:list:{search}:{product_type}"`
- [ ] Cache checked before API call
- [ ] Cache populated after successful API response
- [ ] Example:
  ```python
  cache_key = f"products:list:{search}:{product_type}"
  cached = await self.cache.get(cache_key)
  if cached:
      return cached

  # ... fetch from API ...

  await self.cache.set(cache_key, result, ttl_seconds=3600)
  ```

### AC8: Integration Test with Real Data

- [ ] Test listing all products (no filters)
- [ ] Verify output contains multiple products
- [ ] Test with search filter (e.g., "studio")
- [ ] Test with product_type filter
- [ ] Test code:
  ```python
  import pytest
  from testio_mcp.tools.list_products_tool import list_products

  @pytest.mark.integration
  @pytest.mark.asyncio
  async def test_list_products_all():
      result = await list_products()
      assert result["total_count"] > 0
      assert len(result["products"]) > 0
      assert result["products"][0]["product_id"] is not None
      assert result["products"][0]["name"] is not None

  @pytest.mark.integration
  @pytest.mark.asyncio
  async def test_list_products_with_search():
      result = await list_products(search="studio")
      assert result["total_count"] > 0
      # Verify all results contain "studio" in name or description
      for product in result["products"]:
          assert (
              "studio" in product["name"].lower()
              or "studio" in (product.get("description") or "").lower()
          )

  @pytest.mark.integration
  @pytest.mark.asyncio
  async def test_list_products_no_results():
      result = await list_products(search="nonexistent_product_xyz")
      assert result["total_count"] == 0
      assert len(result["products"]) == 0
  ```

### AC9: Service Layer Tests (Primary Testing Focus)

- [ ] Test ProductService directly with mocked client/cache
- [ ] Test filtering logic with various inputs
- [ ] Test caching behavior
- [ ] Example:
  ```python
  from unittest.mock import AsyncMock
  from testio_mcp.services.product_service import ProductService

  @pytest.mark.asyncio
  async def test_list_products_caches_result():
      # Mock dependencies
      mock_client = AsyncMock()
      mock_client.get.return_value = {
          "products": [
              {"id": "1", "name": "Product A", "type": "website"},
              {"id": "2", "name": "Product B", "type": "mobile"}
          ]
      }
      mock_cache = AsyncMock()
      mock_cache.get.return_value = None  # Cache miss

      # Create service
      service = ProductService(client=mock_client, cache=mock_cache)

      # Test
      result = await service.list_products()

      # Verify
      assert result["total_count"] == 2
      mock_cache.set.assert_called_once()
      # Verify 1-hour cache TTL
      assert mock_cache.set.call_args[1]["ttl_seconds"] == 3600

  @pytest.mark.asyncio
  async def test_list_products_filters_by_search():
      mock_client = AsyncMock()
      mock_client.get.return_value = {
          "products": [
              {"id": "1", "name": "Studio Pro", "type": "website"},
              {"id": "2", "name": "Mobile App", "type": "mobile"}
          ]
      }
      mock_cache = AsyncMock()
      mock_cache.get.return_value = None

      service = ProductService(client=mock_client, cache=mock_cache)
      result = await service.list_products(search="studio")

      assert result["total_count"] == 1
      assert result["products"][0]["name"] == "Studio Pro"
  ```

## Technical Implementation

### File Structure

```
src/testio_mcp/
├── services/
│   └── product_service.py         # NEW: ProductService with list_products()
└── tools/
    └── list_products_tool.py      # NEW: MCP tool wrapper

tests/
├── services/
│   └── test_product_service.py    # NEW: Service layer tests
└── integration/
    └── test_list_products_integration.py  # NEW: Integration tests
```

### Complete Implementation Example

```python
# src/testio_mcp/tools/list_products_tool.py
from typing import Optional
from pydantic import BaseModel, Field
from fastmcp import Context
from testio_mcp.server import mcp
from testio_mcp.services.product_service import ProductService
from testio_mcp.exceptions import TestIOAPIError

class ProductSummary(BaseModel):
    product_id: str
    name: str
    type: str
    description: Optional[str] = None

class ListProductsOutput(BaseModel):
    total_count: int
    filters_applied: dict
    products: list[ProductSummary]

@mcp.tool()
async def list_products(
    search: Optional[str] = None,
    product_type: Optional[str] = None,
    ctx: Context = None
) -> dict:
    """
    List all products accessible to the user.

    Discovery tool for navigating product → test → bug hierarchy.
    Use this to find product IDs needed for list_active_tests and other tools.

    Args:
        search: Optional search term (filters by name/description)
        product_type: Optional filter by product type
        ctx: FastMCP context (injected automatically)

    Returns:
        Dictionary with list of products and metadata
    """
    # Extract dependencies
    client = ctx["testio_client"]
    cache = ctx["cache"]

    # Create service
    service = ProductService(client=client, cache=cache)

    # Delegate to service
    try:
        return await service.list_products(
            search=search,
            product_type=product_type
        )
    except TestIOAPIError as e:
        return {
            "error": f"❌ API error: {e.message}",
            "context": f"ℹ️ Status code: {e.status_code}",
            "hint": "💡 Check API status and authentication"
        }
```

## Testing Strategy

### Service Layer Tests (Primary)
- Test ProductService with mocked client/cache
- Test filtering logic (_apply_filters)
- Test caching behavior (1-hour TTL)
- Test error handling

### Integration Tests
- Test with real TestIO API (staging)
- Test search filtering with real data
- Test type filtering with real data
- Test empty results handling

## Definition of Done

- [x] All acceptance criteria met (AC0-AC9)
- [x] ProductService implements business logic (framework-agnostic)
- [x] Service uses Story-002 infrastructure (cache with 1-hour TTL, exceptions)
- [x] Tool accessible via `@mcp.tool()` decorator (thin wrapper)
- [x] Tool uses Context injection pattern from Story-002
- [x] Pydantic models for input/output validation
- [x] Filtering logic working in service layer (search, product_type)
- [x] Error handling covers API errors, empty results (two-layer pattern)
- [x] Service layer tests pass with mocked client/cache
- [x] Integration test passes with real API
- [x] Code follows best practices (ADR-006 service layer pattern)
- [ ] Peer review completed

## References

- **Epic**: `docs/epics/epic-001-testio-mcp-mvp.md`
- **Project Brief**: `docs/archive/planning/project-brief-mvp-v2.4.md (ARCHIVED)` (Product discovery workflow)
- **FastMCP Tools**: https://gofastmcp.com/servers/tools
- **Related Story**: Story-003 (list_active_tests - depends on this story for product IDs)

---

## Dev Agent Record

### File List

**Source Files Created:**
- `src/testio_mcp/services/product_service.py` - ProductService with list_products business logic
- `src/testio_mcp/tools/list_products_tool.py` - MCP tool with Pydantic models for product listing

**Source Files Modified:**
- None

**Test Files Created:**
- `tests/unit/test_product_service.py` - 13 unit tests for ProductService (all passing)
- `tests/integration/test_list_products_integration.py` - 6 integration tests with real API (all passing)

**Test Files Modified:**
- None

### Completion Notes

**Implementation Summary:**
Successfully implemented the list_products discovery tool following the service layer pattern (ADR-006):

1. **ProductService Layer** (src/testio_mcp/services/product_service.py):
   - Implements business logic for product listing and filtering
   - Cache management with 1-hour TTL (products rarely change per ADR-004)
   - Filtering by search term (case-insensitive name/description match)
   - Filtering by product_type (exact match)
   - Private `_apply_filters()` method for clean separation of concerns
   - Handles None values in description field (API can return null)

2. **MCP Tool Layer** (src/testio_mcp/tools/list_products_tool.py):
   - Thin wrapper (~30 lines) delegates to ProductService
   - Pydantic models for input validation and output structure
   - Converts domain exceptions to user-friendly MCP error format (❌ℹ️💡)
   - Uses dependency injection pattern from server context

3. **Testing**:
   - **Unit Tests (13 tests)**: Service layer tests with mocked dependencies
     - Cache hit/miss behavior ✅
     - API call orchestration ✅
     - Filtering logic (search, type, both) ✅
     - Case-insensitive search ✅
     - Empty results handling ✅
     - API error handling ✅
     - Private method testing ✅
   - **Integration Tests (6 tests)**: Real API validation
     - List all products ✅
     - Cache behavior (1-hour TTL) ✅
     - Search filtering with dynamic terms ✅
     - Type filtering with dynamic types ✅
     - Empty results for nonexistent search ✅
     - Different cache keys for different filters ✅

4. **Code Quality**:
   - All code passes `ruff format` and `ruff check` ✅
   - All code passes `mypy --strict` ✅
   - Follows coding standards (100 char line limit, proper imports) ✅
   - Comprehensive docstrings (Google-style) ✅

**Bug Fixed During Development:**
- **Issue**: AttributeError when filtering products with None description values
- **Root Cause**: `p.get("description", "")` returns None when key exists but value is None
- **Fix**: Changed to `(p.get("description") or "")` to handle both missing keys and None values
- **Impact**: Fixed in both service code and integration tests

**Architecture Decisions Followed:**
- ADR-006: Service layer pattern for business logic separation
- ADR-004: Cache strategy with 1-hour TTL for products
- ADR-001: Dependency injection via server context

**All Acceptance Criteria Met:** AC0-AC9 ✅

### Change Log

**2025-11-05**:
- ✅ Created ProductService with list_products method
- ✅ Created list_products MCP tool with Pydantic models
- ✅ Implemented filtering logic (search + product_type)
- ✅ Added comprehensive unit tests (13 tests, all passing)
- ✅ Added integration tests (6 tests, all passing)
- ✅ Fixed None handling bug in filter logic
- ✅ All code quality checks passing (ruff, mypy)
- ✅ Status updated to "Ready for Review"

---

## QA Results

### Review Date: 2025-11-05

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Overall Grade: A+ (Exemplary)**

This implementation represents exceptional adherence to architectural patterns and testing practices. The code demonstrates:

- **Architecture**: Perfect implementation of ADR-006 service layer pattern with clear separation between business logic (ProductService) and transport layer (MCP tool)
- **Design Quality**: Clean, maintainable code with appropriate abstractions (private `_apply_filters` method)
- **Type Safety**: Comprehensive type hints with strict mypy compliance (zero errors)
- **Documentation**: Thorough Google-style docstrings with examples for all public APIs
- **Test Coverage**: 19 tests (13 unit + 6 integration) covering 100% of acceptance criteria
- **Error Handling**: Proper two-layer exception pattern (domain exceptions in service, user-friendly conversion in tool)

### Requirements Traceability (Given-When-Then)

All acceptance criteria validated through comprehensive test coverage:

**AC0: Service Layer Implementation**
- **Given** ProductService with client and cache dependencies
- **When** list_products is called
- **Then** service orchestrates cache check → API call → filtering → cache storage
- **Tests**: `test_list_products_cache_miss_fetches_from_api`, `test_list_products_caches_result`

**AC1: Tool Wrapper Pattern**
- **Given** FastMCP tool using dependency injection
- **When** tool receives parameters
- **Then** tool extracts dependencies, creates service, delegates business logic
- **Tests**: Integration tests validate full flow

**AC2: Input Validation**
- **Given** Optional search and product_type parameters
- **When** input is validated via Pydantic
- **Then** type safety enforced at tool boundary
- **Tests**: Pydantic model validation in tool layer

**AC3: API Integration**
- **Given** TestIOClient with configured base URL
- **When** service calls GET /products
- **Then** real API returns product data
- **Tests**: `test_list_products_with_real_api`

**AC4: Filtering Logic**
- **Given** Products with name, description, type fields
- **When** filters applied (search: case-insensitive substring, type: exact match)
- **Then** only matching products returned
- **Tests**: `test_list_products_filters_by_search_term`, `test_list_products_filters_by_product_type`, `test_list_products_filters_by_both_search_and_type`, `test_apply_filters_*`

**AC5: Structured Output**
- **Given** Pydantic output models (ProductSummary, ListProductsOutput)
- **When** data validated and serialized
- **Then** consistent structure with optional field handling
- **Tests**: Output validation in all integration tests

**AC6: Error Handling**
- **Given** API errors or unexpected exceptions
- **When** service raises TestIOAPIError
- **Then** tool converts to user-friendly format (❌ℹ️💡 pattern)
- **Tests**: `test_list_products_raises_api_error_on_http_error`, tool exception handling

**AC7: Caching Strategy**
- **Given** Cache with 1-hour TTL (ADR-004)
- **When** cache key format `products:list:{search}:{product_type}`
- **Then** subsequent calls served from cache
- **Tests**: `test_list_products_caches_result`, `test_list_products_different_cache_keys_for_different_filters`

**AC8: Integration Testing**
- **Given** Real TestIO API credentials
- **When** Integration tests execute against staging environment
- **Then** All 6 integration tests pass with dynamic data
- **Tests**: All tests in `test_list_products_integration.py`

**AC9: Service Layer Testing**
- **Given** Mocked client and cache
- **When** Service logic tested in isolation
- **Then** 13 unit tests validate business logic without framework dependencies
- **Tests**: All tests in `test_product_service.py`

### Refactoring Performed

**No refactoring needed.** The code was implemented correctly from the start with:
- Clean architecture following ADR-006
- Proper separation of concerns
- DRY principle applied throughout
- No code duplication or technical debt

### Compliance Check

- **Coding Standards**: ✓ Fully compliant
  - Line length < 100 chars
  - Google-style docstrings
  - Proper import ordering
  - Type hints on all functions

- **Project Structure**: ✓ Fully compliant
  - Services in `src/testio_mcp/services/`
  - Tools in `src/testio_mcp/tools/`
  - Tests mirror source structure

- **Testing Strategy**: ✓ Fully compliant
  - Unit tests in `tests/unit/` with mocked dependencies
  - Integration tests in `tests/integration/` with real API
  - Proper test markers (@pytest.mark.unit, @pytest.mark.integration)
  - All tests pass (13 unit + 6 integration = 19 total)

- **All ACs Met**: ✓ 100% (AC0-AC9)

### Improvements Checklist

**All items completed - no remaining work:**

- [x] ✅ ProductService implements business logic correctly
- [x] ✅ Filtering logic handles None values (bug fixed during dev)
- [x] ✅ Cache strategy follows ADR-004 (1-hour TTL)
- [x] ✅ Error handling uses two-layer pattern
- [x] ✅ Type hints pass strict mypy
- [x] ✅ Code passes ruff format and check
- [x] ✅ Comprehensive unit tests (13 tests)
- [x] ✅ Integration tests with dynamic data (6 tests)
- [x] ✅ Documentation complete

### Security Review

**Status**: ✅ PASS (No concerns)

- **Read-only operation**: No data modification, creation, or deletion
- **No authentication logic**: Token handling delegated to TestIOClient layer
- **Error messages**: Do not expose internal details or sensitive data
- **Input validation**: Pydantic models enforce type safety
- **No injection risks**: Filtering uses list comprehension (not SQL or code execution)

### Performance Considerations

**Status**: ✅ PASS (Optimized)

**Cache Strategy**:
- 1-hour TTL appropriate for products (rarely change per ADR-004)
- Separate cache keys for different filter combinations
- Cache checked before API calls to minimize latency

**Filtering Efficiency**:
- Single-pass filtering algorithm O(n)
- Case-insensitive search via `.lower()` (acceptable for product lists)
- No N+1 queries or nested loops

**Connection Pooling**:
- Handled by TestIOClient infrastructure
- No connection leaks (async context manager)

### Files Modified During Review

**No files modified.** Implementation was clean from the start; no refactoring necessary.

### Gate Status

**Gate**: ✅ **PASS** → `docs/qa/gates/003b-list-products.yml`

**Quality Score**: 100/100
- Zero blocking issues
- Zero concerns
- All acceptance criteria met
- Exemplary code quality

**Gate File Location**: `docs/qa/gates/003b-list-products.yml`

### Recommended Status

✅ **Ready for Done**

This story meets all quality standards and is production-ready. The implementation serves as a reference example for future service layer implementations.

**Next Steps**:
1. Merge to main branch
2. Consider this implementation as a template for Story-003 (list_active_tests)
3. No changes required

### Additional Notes

**Exemplary Practices Observed**:
1. **Bug Prevention**: Developer found and fixed None handling bug during implementation
2. **Test Design**: Integration tests use dynamic data (avoiding brittle assertions)
3. **Documentation**: Comments explain "why" (e.g., "products rarely change")
4. **Type Safety**: Uses `cast()` appropriately for cache type narrowing
5. **Error Context**: Includes HTTP status codes in error responses

**Zero Technical Debt**: No shortcuts, workarounds, or TODOs in code.
