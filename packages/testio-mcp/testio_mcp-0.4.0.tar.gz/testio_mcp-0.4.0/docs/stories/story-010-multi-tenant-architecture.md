---
story_id: STORY-010
epic_id: NONE
title: Multi-Tenant Architecture for HTTP Deployments
status: todo
created: 2025-11-05
updated: 2025-01-19
estimate: 1.5-2.5 days (12-20 hours)
assignee: architect
dependencies: [STORY-023e, STORY-023f]
related_adr: ADR-008
priority: medium
implementation_difficulty: 6/10 (moderately high)
reviewed_by: [codex, gemini]
---

# STORY-010: Multi-Tenant Architecture for HTTP Deployments

## ⚠️ DESIGN RECONCILIATION REQUIRED

**This story was written before EPIC-004 (Production Architecture Rewrite).**

**Original Assumptions (Now Outdated):**
- ❌ `InMemoryCache` with tenant-scoped string keys
- ❌ `ctx["client_pool"]` dict-based context access
- ❌ No persistent storage (cache-only architecture)

**Current Reality (Post-EPIC-004):**
- ✅ `PersistentCache` (SQLite) with `customer_id` column filtering (STORY-021, STORY-024)
- ✅ `ServerContext` TypedDict with `testio_client` + `cache` (ADR-007)
- ✅ Background sync tied to single `customer_id` in lifespan
- ✅ `TestRepository` + `BugRepository` with per-query `customer_id` filtering

**Architecture Assessment: 8/10** ✅
- SQLite schema is already multi-tenant ready (`customer_id` everywhere)
- Repository pattern supports per-request tenant context
- Background sync is straightforward (loop over customer IDs)
- Main work: ClientPool + tool signature changes

**Updated Implementation Difficulty: 6/10** (Moderately High, down from 7/10)
- ClientPool implementation + LRU eviction
- Tool signature changes (`customer_id` parameter)
- Tenant isolation testing (critical!)
- DI refactoring for tenant-aware service creation

**Key Design Decisions (Updated):**
1. **Storage:** Single SQLite DB with `customer_id` filtering (schema supports this)
2. **Customer Registry:** YAML file (gitignored, like `.env`) NOT environment variables
3. **Background Sync:** Simple loop over customers (existing sync logic unchanged)
4. **Cache Strategy:** Single `PersistentCache` instance, queries filtered by `customer_id`
5. **Customer ID Discovery:** Auto-generated from API token hash for single-tenant (see below)

**⚠️ CUSTOMER ID DISCOVERY CHALLENGE (2025-11-20):**

**Problem:** TestIO Customer API has no `/me` or `/whoami` endpoint to auto-discover customer ID. Customers don't know their customer ID (internal TestIO/Cirro identifier).

**Solution: Simple Default Value (customer_id=1)**

**For Single-Tenant (Current MVP):**
- `TESTIO_CUSTOMER_ID` defaults to `1` (no configuration needed)
- Simple, predictable, survives token rotation
- Customer ID is just for local database isolation, doesn't need to match TestIO's internal ID

**For Multi-Tenant (STORY-010):**
- Internal company users explicitly set unique customer IDs (2, 3, 4...)
- YAML config maps `customer_id → api_token`
- Each customer gets unique ID for database isolation

**Implementation:**
```python
# config.py
TESTIO_CUSTOMER_ID: int = Field(
    default=1,
    gt=0,
    description="Customer ID for local database isolation (default: 1). "
    "For single-tenant: default is sufficient. "
    "For multi-tenant: use unique IDs per customer."
)
```

**Benefits:**
- ✅ Zero configuration for single-tenant users
- ✅ Survives API token rotation (no orphaned databases)
- ✅ Simple and predictable
- ✅ Multi-tenant ready (just use different IDs)

**Before Implementation:**
1. ✅ Document customer ID discovery challenge (done above)
2. Update this story file with SQLite-first design
3. Create ADR-008 documenting multi-tenant architecture decision
4. Team review of updated design
5. Security review of CustomerRegistry and data isolation patterns

## User Story

**As a** TestIO MCP Server administrator
**I want** to deploy the MCP server over HTTP with support for multiple tenants (organizations)
**So that** different organizations can use the same server instance with their own API tokens and isolated data

## Context

The current implementation (after STORY-003c) uses a **single-tenant architecture**:
- Single TestIOClient initialized from `.env` file (`TESTIO_CUSTOMER_API_TOKEN`)
- Shared client and cache across all requests
- Suitable for stdio CLI usage and single-organization deployments

**This works for:**
- Development and testing
- Single-organization stdio CLI usage
- Internal tools with one API token

**This does NOT work for:**
- HTTP deployments serving multiple organizations
- SaaS-style deployments where each customer has their own TestIO API token
- Multi-tenant environments with data isolation requirements

**Conversation Context:** This story implements the multi-tenancy architecture discussed in the conversation about "different clients needing different API tokens" and builds on the Context injection pattern established in STORY-003c.

---

## Goals

### Primary Goals
1. Support per-request authentication (each request can use a different API token)
2. Connection pooling per tenant (reuse HTTP connections for same tenant)
3. Global concurrency control (limit total concurrent API requests across all tenants)
4. Cache isolation (tenants don't see each other's cached data)

### Secondary Goals
5. LRU eviction for inactive tenants (prevent memory leaks)
6. Per-tenant rate limiting (optional, prevent one tenant from monopolizing resources)
7. HTTP deployment ready (FastAPI/Starlette integration)

### Non-Goals (Deferred to Future Stories)
- Authentication/authorization middleware (assume trusted client provides valid API token)
- Tenant usage metrics/billing
- Tenant-specific configuration (rate limits, cache TTLs)
- Multi-region deployments

---

## Architecture Overview

### Current Architecture (Single-Tenant, Post-EPIC-004)
```
Lifespan → TestIOClient (single, settings.TESTIO_CUSTOMER_API_TOKEN)
         → PersistentCache (SQLite, single customer_id)
         → Background Sync (for single customer)

ServerContext:
  testio_client: TestIOClient
  cache: PersistentCache

Tool Call → get_service(ctx, TestService)
          → TestService(client, test_repo, bug_repo)
          → Repository queries filter by self.customer_id
```

### Proposed Architecture (Multi-Tenant, SQLite-First)
```
Lifespan → ClientPool (manages TestIOClient per tenant)
         → PersistentCache (single SQLite DB, filtered by customer_id)
         → CustomerRegistry (YAML: customer_id → api_token mapping)
         → Global Semaphore (shared across all tenants)
         → Background Sync (loops over all customers)

ServerContext:
  client_pool: ClientPool
  cache: PersistentCache
  customer_registry: CustomerRegistry

Tool Call (customer_id=123)
  → Registry.get_token(customer_id) → api_token
  → ClientPool.get_client(api_token) → Tenant-specific TestIOClient
  → TestService(client, test_repo, bug_repo) where test_repo filters by customer_id
  → Repository: SELECT * FROM tests WHERE customer_id = 123 AND ...
```

**Key Changes:**
- ✅ Tools accept `customer_id: int` parameter (user-facing tenant identifier)
- ✅ CustomerRegistry maps `customer_id → api_token` securely
- ✅ ClientPool creates/caches `TestIOClient` per tenant (LRU eviction)
- ✅ Single SQLite DB with `customer_id` filtering (already implemented!)
- ✅ Background sync loops over customers (simple iteration)

---

## Acceptance Criteria

### AC1: Create ClientPool Class

- [ ] Implement `ClientPool` class in `src/testio_mcp/client_pool.py`
- [ ] Constructor accepts:
  - `max_clients: int` - Maximum number of tenant clients to cache (default: 100)
  - `semaphore: asyncio.Semaphore` - Shared global concurrency control
- [ ] Key methods:
  - `async get_client(api_token: str) -> TestIOClient` - Get or create client for tenant
  - `async cleanup() -> None` - Close all tenant clients (called on shutdown)
  - `async evict_inactive(ttl_seconds: int) -> int` - LRU eviction (optional)
- [ ] Client identification:
  - Hash API token for tenant key (don't store plaintext): `hashlib.sha256(api_token.encode()).hexdigest()[:16]`
  - Use tenant key for client caching and cache key prefixes
- [ ] Thread-safe client creation (asyncio.Lock for dictionary access)
- [ ] Example implementation:
  ```python
  class ClientPool:
      """Manages TestIOClient instances per tenant for multi-tenancy."""

      def __init__(
          self,
          max_clients: int = 100,
          semaphore: asyncio.Semaphore | None = None,
      ):
          self._clients: dict[str, TestIOClient] = {}
          self._max_clients = max_clients
          self._semaphore = semaphore
          self._lock = asyncio.Lock()
          self._last_used: dict[str, float] = {}  # For LRU eviction

      async def get_client(self, api_token: str) -> TestIOClient:
          """Get or create TestIOClient for this tenant."""
          tenant_key = self._hash_token(api_token)

          async with self._lock:
              if tenant_key not in self._clients:
                  # Evict oldest client if at capacity
                  if len(self._clients) >= self._max_clients:
                      await self._evict_oldest()

                  # Create new client for tenant
                  client = TestIOClient(
                      base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
                      api_token=api_token,  # Tenant-specific token
                      semaphore=self._semaphore,  # Shared global limit
                      ...
                  )
                  await client.__aenter__()
                  self._clients[tenant_key] = client

              self._last_used[tenant_key] = time.time()
              return self._clients[tenant_key]

      def _hash_token(self, api_token: str) -> str:
          """Hash API token for tenant identification."""
          return hashlib.sha256(api_token.encode()).hexdigest()[:16]

      async def cleanup(self) -> None:
          """Close all tenant clients on shutdown."""
          for client in self._clients.values():
              await client.__aexit__(None, None, None)
  ```

### AC2: Update Lifespan Handler for Multi-Tenancy

- [ ] Replace single TestIOClient with ClientPool in lifespan
- [ ] Store ClientPool in `app.context["client_pool"]`
- [ ] Remove `app.context["testio_client"]` (replaced by pool)
- [ ] Keep shared cache: `app.context["cache"]`
- [ ] Keep shared semaphore for global concurrency control
- [ ] File: `src/testio_mcp/server.py`
- [ ] Example:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastMCP):
      """Manage multi-tenant resources during server lifecycle."""
      logger.info("Initializing multi-tenant server dependencies")

      # Create shared resources
      shared_semaphore = get_global_semaphore()
      client_pool = ClientPool(
          max_clients=100,
          semaphore=shared_semaphore,
      )
      cache = InMemoryCache()

      # Store in context
      app.context["client_pool"] = client_pool
      app.context["cache"] = cache

      logger.info("Multi-tenant dependencies initialized")

      yield

      # Cleanup: Close all tenant clients
      await client_pool.cleanup()
      logger.info("Multi-tenant dependencies cleaned up")
  ```

### AC3: Create list_customers Tool (For YAML Config Approach)

- [ ] Create new tool `list_customers()` to show available customers from config file
- [ ] Returns customer metadata (id, name, description) WITHOUT tokens (security)
- [ ] Add search/filter parameters for CSMs managing many customers
- [ ] Tool signature:
  ```python
  @mcp.tool()
  async def list_customers(
      search: str | None = None,
      ctx: Context = None,
  ) -> dict[str, Any]:
      """List available customers configured in customers.yaml.

      Returns customer metadata to help users know which customer_id values
      are available for querying. Does NOT return API tokens (security).

      Useful for CSMs managing multiple customers who need to find the
      correct customer_id for queries.

      Args:
          search: Optional search term (filters by name/description, case-insensitive)
          ctx: FastMCP context (injected automatically)

      Returns:
          Dictionary with:
          - customers: List of customer objects with id, name, description
          - total_count: Number of customers returned
          - filters_applied: Which filters were used

      Examples:
          >>> # List all customers
          >>> result = await list_customers()
          >>> print(result["total_count"])
          50

          >>> # Search for specific customer
          >>> result = await list_customers(search="acme")
          >>> print(result)
          {
              "customers": [
                  {"id": 1, "name": "AcmeCorp", "description": "Main production customer"}
              ],
              "total_count": 1,
              "filters_applied": {"search": "acme"}
          }
      """
      customer_registry = ctx["customer_registry"]

      # Get all customers (without tokens)
      customers = customer_registry.list_customers()

      # Apply search filter if provided
      if search:
          search_lower = search.lower()
          customers = [
              c for c in customers
              if search_lower in c["name"].lower()
              or search_lower in c.get("description", "").lower()
          ]

      return {
          "customers": customers,
          "total_count": len(customers),
          "filters_applied": {"search": search} if search else {},
      }
  ```
- [ ] CustomerRegistry must sanitize output (exclude token field)
- [ ] Search filters by customer name and description (case-insensitive)
- [ ] Add to tool registration in server.py
- [ ] File: `src/testio_mcp/tools/list_customers_tool.py` (new file)

### AC4: Add api_token Parameter to All Tools

- [ ] Add `api_token: str` parameter to all 4 existing tools
- [ ] Extract tenant-specific client from ClientPool
- [ ] Update all tool signatures:
  - `health_check(api_token: str, ctx: Context)`
  - `get_test_status(test_id: int, api_token: str, ctx: Context)`
  - `list_products(search: str | None, product_type: str | None, api_token: str, ctx: Context)`
  - `list_tests(product_id: int, statuses: list | None, include_bug_counts: bool, api_token: str, ctx: Context)`
- [ ] Update docstrings to document `api_token` parameter
- [ ] **Note:** When using YAML config approach (idea #4), tools would accept `customer_id: int` instead:
  ```python
  # Alternative signature for YAML config approach
  async def list_tests(
      customer_id: int,  # Config maps customer_id → api_token
      product_id: int,
      statuses: list | None = None,
      ctx: Context = None,
  ):
      customer_registry = ctx["customer_registry"]
      api_token = customer_registry.get_token(customer_id)
      client = await ctx["client_pool"].get_client(api_token)
      # ...
  ```
- [ ] Example pattern:
  ```python
  @mcp.tool()
  async def list_tests(
      product_id: int,
      api_token: str,  # NEW: Required for multi-tenancy
      statuses: list[Literal[...]] | None = None,
      include_bug_counts: bool = False,
      ctx: Context = None,
  ) -> dict[str, Any]:
      """List tests for a specific product with status filtering.

      Args:
          product_id: The product ID
          api_token: TestIO Customer API token for authentication
          statuses: Filter by test statuses (default: ["running"])
          include_bug_counts: Include bug count summary
          ctx: FastMCP context (injected automatically)
      """
      client_pool = ctx["client_pool"]
      cache = ctx["cache"]

      # Get tenant-specific client
      client = await client_pool.get_client(api_token)

      # Delegate to service (unchanged)
      service = ProductService(client=client, cache=cache)
      # ...
  ```

### AC4: Implement Tenant-Scoped Cache Keys

- [ ] Update ProductService to accept optional `tenant_id` parameter
- [ ] Update TestService to accept optional `tenant_id` parameter
- [ ] Modify cache key format to include tenant scope:
  - Before: `product:{id}:tests:running`
  - After: `tenant:{hash}:product:{id}:tests:running`
- [ ] Tenant ID is hash of API token (from ClientPool)
- [ ] Services receive tenant_id from tool layer
- [ ] Files to modify:
  - `src/testio_mcp/services/product_service.py`
  - `src/testio_mcp/services/test_service.py`
- [ ] Example:
  ```python
  class ProductService:
      def __init__(
          self,
          client: TestIOClient,
          cache: InMemoryCache,
          tenant_id: str | None = None,  # NEW: For cache key scoping
      ):
          self.client = client
          self.cache = cache
          self.tenant_id = tenant_id

      async def list_tests(self, product_id: int, ...) -> dict[str, Any]:
          # Build tenant-scoped cache key
          statuses_key = "_".join(sorted(statuses or []))
          cache_key = f"tenant:{self.tenant_id}:product:{product_id}:tests:{statuses_key}"

          # Rest of method unchanged...
  ```
- [ ] Tool layer passes tenant_id to service:
  ```python
  tenant_id = hashlib.sha256(api_token.encode()).hexdigest()[:16]
  service = ProductService(client=client, cache=cache, tenant_id=tenant_id)
  ```

### AC5: Update Integration Tests for Multi-Tenancy

- [ ] Integration tests must provide `api_token` parameter
- [ ] Use `settings.TESTIO_CUSTOMER_API_TOKEN` as test api_token
- [ ] Update all integration test files:
  - `tests/integration/test_get_test_status_integration.py`
  - `tests/integration/test_list_products_integration.py`
  - `tests/integration/test_list_tests_integration.py`
- [ ] Example:
  ```python
  @pytest.mark.integration
  async def test_list_tests_with_real_api():
      """Integration test with real API (multi-tenant mode)."""
      from testio_mcp.config import settings
      from testio_mcp.tools.list_tests_tool import list_tests

      # Create context with ClientPool
      ctx = Context()
      ctx["client_pool"] = ClientPool(...)
      ctx["cache"] = InMemoryCache()

      result = await list_tests(
          product_id=22,
          api_token=settings.TESTIO_CUSTOMER_API_TOKEN,  # Test tenant
          statuses=["running"],
          ctx=ctx,
      )

      assert "tests" in result
  ```

### AC6: Update Unit Tests (Verify No Changes Needed)

- [ ] Unit tests should NOT need changes (test services directly, not tools)
- [ ] Service tests can mock `tenant_id` parameter if needed
- [ ] Verify all 48 existing unit tests still pass
- [ ] Add new unit tests for ClientPool class:
  - Test client creation and caching
  - Test LRU eviction when at capacity
  - Test thread-safe client access (concurrent get_client calls)
  - Test cleanup closes all clients

### AC7: HTTP Deployment Example (FastAPI)

- [ ] Create example FastAPI integration in `examples/fastapi_server.py`
- [ ] Show how to mount MCP server with lifespan
- [ ] Show how to extract API token from Authorization header
- [ ] Example:
  ```python
  from fastapi import FastAPI, Header, HTTPException
  from testio_mcp.server import mcp

  # Create MCP ASGI app
  mcp_app = mcp.http_app(path='/mcp')

  # Create FastAPI app with MCP lifespan
  app = FastAPI(lifespan=mcp_app.lifespan)

  # Mount MCP server
  app.mount("/mcp-server", mcp_app)

  # Health check endpoint showing tenant auth
  @app.get("/health")
  async def health_check(authorization: str = Header(...)):
      """Example of extracting API token from header."""
      if not authorization.startswith("Bearer "):
          raise HTTPException(401, "Invalid authorization header")

      api_token = authorization[7:]  # Remove "Bearer "

      # Call MCP tool with api_token
      result = await health_check_tool(api_token=api_token, ctx=...)
      return result
  ```

### AC8: Documentation Updates

- [ ] Create ADR-008: Multi-Tenant Architecture
- [ ] Update `CLAUDE.md` with multi-tenant tool pattern
- [ ] Update `ARCHITECTURE.md` to document ClientPool design
- [ ] Add deployment guide: `docs/deployment/HTTP_MULTI_TENANT.md`
- [ ] Update all future story templates to include `api_token` parameter

### AC9: Performance Testing

- [ ] Test with multiple concurrent tenants (e.g., 10 tenants, 100 requests each)
- [ ] Verify global semaphore limits total concurrent API requests
- [ ] Verify cache isolation (tenant A can't see tenant B's cached data)
- [ ] Verify connection pooling per tenant (reuse connections for same tenant)
- [ ] Measure overhead of ClientPool vs. single-tenant (should be minimal)

### AC10: Manual Testing with MCP Inspector

- [ ] Test health_check with different api_token values
- [ ] Verify different tokens get different clients (cache different tenant data)
- [ ] Test all 4 tools work with multi-tenant parameters
- [ ] Verify server startup/shutdown logs show ClientPool initialization

---

## Technical Design

### ClientPool Design Decisions

**Why hash API tokens?**
- Security: Don't store plaintext tokens in memory longer than necessary
- Privacy: Logs and debugging won't expose full tokens
- Consistent tenant identification across services

**Why LRU eviction?**
- Prevent memory leaks if server runs for long periods
- Handle scenarios with 1000+ tenants over time
- Configurable max_clients (default: 100 active tenants)

**Why shared semaphore?**
- Global concurrency control across ALL tenants (ADR-002)
- Prevents any single tenant from monopolizing API resources
- Fair resource sharing (first-come-first-served)

### Cache Isolation Strategy

**Tenant-scoped keys:**
```
tenant:abc123:product:22:tests:running
tenant:def456:product:22:tests:running
```

**Benefits:**
- Tenants can't accidentally see each other's data
- Cache hits work correctly per-tenant
- Same product ID for different tenants = separate cache entries

**Tradeoff:**
- Slightly larger cache (duplicate data for same product across tenants)
- Acceptable: Cache is in-memory, TTL-based (expires quickly)

---

## Testing Strategy

### Unit Tests (New: ClientPool)
- Test ClientPool.get_client() creates and caches clients
- Test LRU eviction when max_clients reached
- Test thread-safe client access (asyncio.Lock)
- Test cleanup() closes all clients
- Test tenant_id hashing is consistent

### Integration Tests (Updated: Add api_token)
- All 15 existing integration tests updated to pass api_token
- Test with real API (use TESTIO_CUSTOMER_API_TOKEN as test tenant)
- Verify multi-tenant cache isolation (future: add 2-tenant test)

### Manual Testing (Critical)
- Test with MCP Inspector (different api_token values)
- Deploy to staging with FastAPI example
- Test 10+ concurrent tenants
- Verify no cache leakage between tenants

---

## Definition of Done

- [ ] ADR-008 created and approved
- [ ] All acceptance criteria met (AC1-10)
- [ ] ClientPool class implemented with LRU eviction
- [ ] All 4 tools accept `api_token` parameter
- [ ] Services use tenant-scoped cache keys
- [ ] All tests pass (unit + integration)
- [ ] Code passes ruff format, ruff check, mypy --strict
- [ ] Documentation updated (ADR, CLAUDE.md, ARCHITECTURE.md, deployment guide)
- [ ] FastAPI example created and tested
- [ ] Performance testing shows acceptable overhead
- [ ] Manual testing confirms multi-tenant isolation
- [ ] Peer review completed

---

## References

- **Prerequisite:** STORY-003c (Context Injection Pattern)
- **ADR:** `docs/architecture/adrs/ADR-008-multi-tenant-architecture.md` (create with this story)
- **Design Conversation:** "Multi-tenancy where different clients need different API tokens"
- **FastMCP HTTP Docs:** https://gofastmcp.com/deployment/http
- **Related ADRs:** ADR-001 (Dependency Injection), ADR-002 (Concurrency Control), ADR-007 (Context Injection)

---

## Migration Path

### From Single-Tenant (STORY-003c) to Multi-Tenant (STORY-010)

**Code Changes:**
1. Replace `TestIOClient` with `ClientPool` in lifespan
2. Add `api_token: str` parameter to all tools
3. Update services to accept `tenant_id` parameter
4. Update integration tests to pass `api_token`

**Backward Compatibility:**
- stdio mode: Can use single api_token from .env (works like before)
- HTTP mode: Supports multiple tenants with per-request tokens

**Rollback Plan:**
- git revert to STORY-003c if critical issues
- Single-tenant mode is stable and works correctly

---

## CustomerRegistry Implementation (YAML Config - SELECTED APPROACH)

**Decision:** We're implementing **Option #4** (YAML configuration file) for MVP multi-tenancy.

**Why YAML Instead of Environment Variables:**
- ✅ Single file vs 100+ env vars (`TESTIO_TENANT_1_ID`, `TESTIO_TENANT_1_TOKEN`, ...)
- ✅ Metadata support (name, description, contact info)
- ✅ Easy to audit/review tenant list
- ✅ Works with config management tools (Ansible, Chef)
- ✅ Same security as `.env` (gitignored, file permissions)
- ❌ Requires YAML parsing library (acceptable tradeoff)

**Configuration:**
```yaml
# customers.yaml (gitignored, like .env)
customers:
  - id: 1
    name: "AcmeCorp"
    api_token: "testio-token-for-acme-corp"
    description: "Main production customer"
  - id: 2
    name: "GlobexInc"
    api_token: "testio-token-for-globex-inc"
    description: "Enterprise client"
  - id: 3
    name: "InitechLLC"
    api_token: "testio-token-for-initech-llc"
    description: "Development/staging customer"
```

**Implementation:**
```python
# src/testio_mcp/auth.py
from pydantic import BaseModel, SecretStr

class TenantConfig(BaseModel):
    id: int
    name: str
    api_token: SecretStr
    description: str | None = None

class CustomerRegistry:
    def __init__(self, configs: list[TenantConfig]):
        self._configs = {cfg.id: cfg for cfg in configs}
        # Validate unique IDs
        if len(self._configs) != len(configs):
            raise ValueError("Duplicate customer IDs in config")

    @classmethod
    def from_yaml_file(cls, path: Path) -> Self:
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f)
        configs = [TenantConfig(**c) for c in data["customers"]]
        return cls(configs)

    def get_token(self, customer_id: int) -> str:
        config = self._configs.get(customer_id)
        if config is None:
            raise ValueError(f"Unknown customer_id: {customer_id}")
        return config.api_token.get_secret_value()

    def list_customers(self) -> list[dict]:
        """Return customer metadata WITHOUT tokens (security)."""
        return [
            {"id": cfg.id, "name": cfg.name, "description": cfg.description}
            for cfg in self._configs.values()
        ]
```

**Configuration:**
```python
# config.py
TESTIO_CUSTOMERS_CONFIG_PATH: str = Field(
    default="customers.yaml",
    description="Path to customers YAML file"
)
```

**.gitignore:**
```gitignore
.env
customers.yaml
customers.yml
```

**Security:**
- File permissions: `chmod 600 customers.yaml` (owner read/write only)
- Never commit to git (gitignored)
- Use `SecretStr` from Pydantic (prevents accidental logging)
- CustomerRegistry sanitizes output (excludes tokens from `list_customers()`)

## Multi-Tenant Background Sync (Simple Loop Pattern)

**Current (Single-Tenant):**
```python
async def initial_sync(self) -> dict:
    """Sync for single customer_id."""
    product_ids = await self._get_product_ids_to_sync()
    for product_id in product_ids:
        await self.sync_product_tests(product_id)
    return {"total_products": len(product_ids), ...}
```

**Updated (Multi-Tenant):**
```python
async def initial_sync_multi_tenant(
    self,
    client_pool: ClientPool,
    customer_registry: CustomerRegistry,
) -> dict[int, dict]:
    """Sync all customers in registry."""
    results = {}

    for customer_id, config in customer_registry.items():
        logger.info(f"Starting sync for customer {customer_id} ({config.name})")

        # Get tenant-specific client
        client = await client_pool.get_client(config.api_token)

        # Set cache context for this customer (reuses existing sync logic!)
        self.client = client
        self.customer_id = customer_id
        self.customer_name = config.name

        # Reinitialize repository with new customer context
        self.repo = TestRepository(
            db=self.db,
            client=self.client,
            customer_id=self.customer_id
        )

        # Run existing sync logic (UNCHANGED!)
        result = await self.initial_sync()
        results[customer_id] = result

    return results
```

**Background Refresh:**
```python
async def run_background_refresh_multi_tenant(
    self,
    interval_seconds: int,
    client_pool: ClientPool,
    customer_registry: CustomerRegistry,
) -> None:
    """Periodic refresh for all customers."""
    while True:
        await asyncio.sleep(interval_seconds)

        for customer_id, config in customer_registry.items():
            try:
                client = await client_pool.get_client(config.api_token)
                self.client = client
                self.customer_id = customer_id
                self.repo = TestRepository(db=self.db, client=client, customer_id=customer_id)

                # Refresh mutable tests for this customer
                await self.refresh_mutable_tests()
            except Exception as e:
                logger.error(f"Refresh failed for customer {customer_id}: {e}")
                continue  # Don't block other customers
```

**Why This Works:**
- ✅ Existing sync logic is already customer-scoped (uses `self.customer_id`)
- ✅ TestRepository queries filter by `customer_id`
- ✅ Single SQLite DB works fine (WAL mode handles concurrent writes)
- ✅ No architectural changes - just iteration + context switching

**Performance Considerations:**
- Sync time scales linearly with tenant count (10 tenants = 10x time)
- For 50+ tenants: Parallelize with `asyncio.gather()` (bounded concurrency)
- For 100+ tenants: Consider separate sync service or staggered refresh

## Open Design Questions (Future Work, Not MVP)

**Note:** The following patterns are **deferred to future stories**. MVP implements YAML-based CustomerRegistry with simple `customer_id` parameter on tools.

### Future: Multi-User Access Control

**Scenario:** A single MCP user needs access to multiple customers (CSM managing 10+ accounts).

**Possible Future Patterns:**

1. **Master customer_id parameter on all tools:**
   ```python
   async def list_tests(
       customer_id: str,  # NEW: Logical customer identifier
       product_id: int,
       ctx: Context,
   ):
       # Middleware maps customer_id -> TestIO API token
       api_token = await ctx["auth_middleware"].get_token_for_customer(customer_id)
       client = await ctx["client_pool"].get_client(api_token)
   ```

2. **MCP-level authentication:**
   - Implement MCP token system (separate from TestIO API tokens)
   - MCP token identifies the user: `mcp_token: "user-alice-token-xyz"`
   - Server-side mapping: `{"user-alice-token-xyz": {"allowed_customers": ["cust-a", "cust-b"]}}`
   - Securely stored data structure maps MCP tokens → allowed TestIO API tokens

3. **Middleware layer:**
   - Intercepts requests before tools execute
   - Validates MCP token has access to requested customer_id
   - Retrieves appropriate TestIO API token from secure storage
   - Injects TestIO API token into request context

4. **Configuration file mapping (stopgap for local/stdio usage):**
   - Allow multiple API keys in a YAML/JSON config file
   - Parse on startup into dict: `customer_id → customer_config`
   - Example `customers.yaml` configuration:
     ```yaml
     customers:
       AcmeCorp:
         id: 1
         token: "testio-token-for-acme-corp"
         description: "Main production customer"
       GlobexInc:
         id: 2
         token: "testio-token-for-globex-inc"
         description: "Enterprise client"
       InitechLLC:
         id: 3
         token: "testio-token-for-initech-llc"
         description: "Development/staging customer"
     ```
   - **Key structure:** Human-readable customer name as YAML key, numeric `id` field for API queries
   - Config service loads on startup: `CustomerRegistry.load("customers.yaml")`
   - Tools accept `customer_id` parameter (integer, e.g., `customer_id=1`), config service maps to appropriate token
   - Lookup flow: `customer_id=1` → find entry with `id: 1` → return `token` field
   - File location configurable via env var: `TESTIO_CUSTOMERS_CONFIG=./customers.yaml`
   - Add `customers.yaml` to `.gitignore` to prevent committing secrets
   - **Validation:** Ensure `id` field is unique across all customers (prevent config errors)
   - **Pros:**
     - More structured than environment variables
     - Can include metadata (customer name, description, contact info)
     - Easier to manage multiple customers (vs. many env vars)
     - Simple to implement for local/stdio usage
     - No database or secrets manager required
     - Works immediately for development and single-user deployments
   - **Cons:**
     - Still stores secrets in config files (not secure for hosted)
     - No per-user access control (everyone with file access sees all tokens)
     - Not suitable for production HTTP deployments
     - Requires YAML parsing library
   - **Use case:** Good stopgap for stdio CLI where user manages their own config file
   - **Alternative:** Could also support JSON format or environment variables as fallback:
     ```bash
     # Env var approach (less structured but works)
     TESTIO_CUSTOMER_acme_API_KEY=token-for-acme-corp
     TESTIO_CUSTOMER_globex_API_KEY=token-for-globex-inc
     ```

5. **Security considerations:**
   - Where to store MCP token → API token mappings? (database, secrets manager)
   - How to rotate TestIO API tokens without breaking MCP tokens?
   - How to audit which MCP user accessed which customer data?

**Decision:** These patterns are **deferred to future design discussions**. Current story (STORY-010) implements simple 1:1 mapping (one api_token per request). Multi-customer access will be addressed in a separate story/ADR when requirements are clearer.

**References:**
- Discussion: "A client should be able to query multiple customers"
- Future: STORY-011 or EPIC-003 (Multi-Customer Access Control)

---

## Risks and Mitigations

### Risk: Memory leak with unlimited tenants
**Mitigation:** LRU eviction with configurable max_clients (default: 100)

### Risk: One tenant monopolizes API resources
**Mitigation:** Global semaphore limits total concurrent requests across all tenants

### Risk: Cache leakage between tenants
**Mitigation:** Tenant-scoped cache keys with hashed tenant_id, comprehensive testing

### Risk: Performance overhead of ClientPool
**Mitigation:** Connection pooling per tenant, shared semaphore (minimal overhead expected)

### Risk: Current design doesn't support multi-customer access
**Mitigation:** Acknowledged limitation. Will be addressed in future story when requirements are finalized. Current simple design is easier to extend later than to over-engineer now.

---

## Estimated Effort

**Total:** 8 hours

- AC1 (ClientPool): 2 hours
- AC2 (Update lifespan): 30 min
- AC3 (Add api_token to tools): 1.5 hours
- AC4 (Tenant-scoped cache keys): 1.5 hours
- AC5 (Integration tests): 1 hour
- AC6 (Unit tests for ClientPool): 30 min
- AC7 (FastAPI example): 30 min
- AC8 (Documentation): 30 min
- AC9 (Performance testing): 30 min
- AC10 (Manual testing): 30 min

**Complexity:** Medium (new architecture pattern, affects all tools)

**Risk:** Medium (cache isolation is critical, needs thorough testing)
