# TestIO MCP Server - System Architecture

**Version:** 3.1.0
**Last Updated:** 2025-12-21
**Status:** ✅ Production Ready (v0.4.0+)

**Summary:** This document was fully validated against the live codebase on 2025-12-03 via BMAD document-project workflow. All sections reflect current implementation: **17 MCP tools, 2 prompts, 2 resources**, REST endpoints with full parity, hybrid server architecture, SQLite-first data access with FTS5 search, 13 services, and comprehensive test coverage.

**Recent Changes:**
- **v3.1.0 (2025-12-21):** v0.4.0 updates - PQR refactor, REST API additions
  - Quality report endpoint: `/api/products/{id}/quality-report` → `/api/quality-report?product_ids=...`
  - Added `/api/bugs`, `/api/bugs/{id}/summary`, `/api/thresholds` endpoints
  - Multi-product portfolio analysis support
- **v3.0.0 (2025-12-03):** Major update - validated via BMAD workflow
  - Updated tool count: 8 → 17 active tools (categorized by function)
  - Added MCP prompts (analyze-product-quality, prep-meeting) and resources (playbook, programmatic-access)
  - Updated service count: 3 → 13 services
  - Added FTS5 full-text search capability
  - Added 3-phase sync model with read-through caching (ADR-017)
- **v2.1.1 (2025-11-20):** Content consolidation - See bottom of document for full changelog
- **v2.0 (2025-11-18):** SQLite-first architecture
- **v1.1 (2025-11-04):** Service layer pattern
- **v1.0 (2025-11-04):** Initial document

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [API Client Design](#api-client-design)
5. [Concurrency & Performance](#concurrency--performance)
6. [Local Data Store Strategy](#local-data-store-strategy)
7. [Error Handling](#error-handling)
8. [Security Considerations](#security-considerations)
9. [Deployment Architecture](#deployment-architecture)
10. [Testing Strategy](#testing-strategy)
11. [Architecture Decision Records](#architecture-decision-records)

---

## System Overview

### Purpose

The TestIO MCP Server is an **AI-first integration layer** that provides Model Context Protocol (MCP) access to TestIO's Customer API. It enables non-developer stakeholders (CSMs, PMs, QA leads) to query test status, bug information, and activity metrics through AI tools like Claude and Cursor.

### Key Design Principles

1. **AI-First UX** - Responses optimized for AI consumption (structured, paginated, clear errors)
2. **Read-Only MVP** - Focus on visibility, defer write operations to future phases
3. **Conservative Defaults** - Protect APIs and resources with sensible limits
4. **User Control** - Allow overrides with clear guidance and warnings
5. **Simple First** - Start with in-memory solutions, add complexity when proven necessary

### Technology Stack

- **Language:** Python 3.12+
- **MCP Framework:** FastMCP (Model Context Protocol server framework)
- **HTTP Client:** httpx (async HTTP with connection pooling)
- **Configuration:** Pydantic Settings (type-safe configuration)
- **Testing:** pytest, pytest-asyncio
- **Code Quality:** mypy (strict), ruff (linting), pre-commit hooks

**See [TECH-STACK.md](TECH-STACK.md) for detailed technology decisions and rationales.**

---

## Component Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│            AI Clients (Claude, Cursor) + Web Apps/Curl                   │
│                                                                          │
│     MCP Protocol (JSON-RPC)           HTTP REST API                      │
└────────────────┬─────────────────────────────────┬───────────────────────┘
                 │                                 │
                 │ /mcp (MCP endpoint)             │ /api/* (REST endpoints)
                 │                                 │ /docs (Swagger UI)
                 │                                 │ /health (monitoring)
                 │                                 │
┌────────────────▼─────────────────────────────────▼────────────────────────┐
│                  Hybrid Server (FastAPI + FastMCP)                        │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                        Lifespan Manager                              │ │
│  │  - Initialize TestIOClient (dependency injection)                    │ │
│  │  - Initialize PersistentCache (SQLite database)                      │ │
│  │  - Start background sync tasks                                       │ │
│  │  - Cleanup on shutdown                                               │ │
│  │  - SHARED across MCP and REST (single resource set)                  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │               MCP Tools (17) - THIN WRAPPERS                         │ │
│  │                                                                      │ │
│  │  • Data Discovery (5)      • Entity Summaries (5)                    │ │
│  │  • Analytics & Reporting (4)   • Server Management (3)               │ │
│  │                                                                      │ │
│  │  See CLAUDE.md for complete tool catalog                             │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  MCP Prompts (2)              │  MCP Resources (2)                   │ │
│  │  Interactive workflows        │  Static knowledge bases              │ │
│  │  See CLAUDE.md for details    │  See CLAUDE.md for details           │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │              REST API Endpoints (8 endpoints)                        │ │
│  │                                                                      │ │
│  │  GET  /health              - Health check with database stats        │ │
│  │  GET  /api/tests/{id}/summary - Get test status                      │ │
│  │  GET  /api/products        - List products                           │ │
│  │  GET  /api/products/{id}/tests - List tests for product              │ │
│  │  GET  /api/quality-report?product_ids=... - Generate quality report  │ │
│  │  GET  /api/database/stats  - Database statistics                     │ │
│  │  GET  /api/sync/history    - Sync event history                      │ │
│  │  GET  /api/sync/problematic - Problematic tests                      │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬──────────────────────────────────────────────┘
                             │
                             │ (Extract from Context)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                  Service Layer - BUSINESS LOGIC                 │
│                     (Framework-Agnostic, 13 services)           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  CORE SERVICES:                                            │ │
│  │    BaseService          - Minimal DI base class            │ │
│  │    TestService          - Test status, queries (~400 LOC)  │ │
│  │    ProductService       - Product listing (~300 LOC)       │ │
│  │    BugService           - Bug listing/details (~250 LOC)   │ │
│  │    FeatureService       - Feature operations (~200 LOC)    │ │
│  │    UserService          - User operations (~200 LOC)       │ │
│  │                                                            │ │
│  │  ANALYTICS SERVICES:                                       │ │
│  │    AnalyticsService     - Dynamic metrics (~825 LOC)       │ │
│  │    QueryBuilder         - Dynamic SQL construction (~400)  │ │
│  │    MultiTestReportService - EBR aggregation (~500 LOC)     │ │
│  │                                                            │ │
│  │  INFRASTRUCTURE SERVICES:                                  │ │
│  │    SyncService          - Unified sync orchestration       │ │
│  │                           (~1300 LOC, 3-phase model)       │ │
│  │    DiagnosticsService   - Server health (~300 LOC)         │ │
│  │    SearchService        - FTS5 search (~200 LOC)           │ │
│  │    UserStoryService     - User story extraction (~150 LOC) │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Responsibilities:                                              │
│  - Domain operations (test queries, product filtering)          │
│  - Business logic (aggregations, classifications)               │
│  - Data access patterns (SQLite first, API fallback)            │
│  - Orchestration (combine multiple data sources)                │
│  - Raise domain exceptions (TestNotFoundException, etc.)        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
         ┌──────────▼─────────┐  ┌───▼──────────────┐
         │   TestIOClient     │  │ PersistentCache  │
         │  (HTTP wrapper)    │  │ (SQLite DB)      │
         │                    │  │                  │
         │  - Connection pool │  │  - Products      │
         │  - Concurrency     │  │  - Tests         │
         │    control (sem)   │  │  - Sync metadata │
         │  - Error handling  │  │  - WAL mode      │
         └──────────┬─────────┘  └──────────────────┘
                    │
         ┌──────────▼─────────┐
         │  httpx.AsyncClient │
         │                    │
         │  - Connection pool │
         │    (100 max conn)  │
         │  - Keep-alive (20) │
         │  - 30s timeout     │
         └──────────┬─────────┘
                    │
                    │ HTTPS
                    │
         ┌──────────▼─────────────────────────────┐
         │  TestIO Customer API (v2)              │
         │  https://api.test.io/customer/v2       │
         │                                        │
         │  - Products                            │
         │  - Exploratory Tests                   │
         │  - Bugs                                │
         │  - Features                            │
         └────────────────────────────────────────┘
```

### Component Responsibilities

#### 1. FastMCP Server
- **Purpose:** MCP protocol handler and request router
- **Responsibilities:**
  - Handle MCP JSON-RPC requests from AI clients
  - Route tool calls to appropriate handlers
  - Manage server lifecycle (startup/shutdown)
  - Provide dependency injection context

#### 2. Lifespan Manager
- **Purpose:** Initialize and cleanup shared resources
- **Responsibilities:**
  - Create `TestIOClient` with connection pool
  - Create `PersistentCache` instance (SQLite database)
  - Initialize database schema and run VACUUM
  - Start background sync tasks (initial sync, periodic refresh)
  - Store in FastMCP context for dependency injection
  - Close HTTP client and database on shutdown

#### 3. MCP Tools (17 Tools)
- **Purpose:** Thin transport layer adapters for MCP protocol
- **Categories:** Data Discovery (5), Entity Summaries (5), Analytics & Reporting (4), Server Management (3)
- **Responsibilities:**
  - Extract dependencies from FastMCP context
  - Create service instances (per-request)
  - Delegate to service layer for business logic
  - Convert service exceptions to MCP error format (❌ℹ️💡)
  - Return structured MCP responses

**What tools should NOT do:** Business logic, caching decisions, direct API calls, complex orchestration

**See:** [CLAUDE.md](../../CLAUDE.md) for tool catalog, [MCP.md](MCP.md) for implementation patterns

#### 3a. MCP Prompts (2) & Resources (2)
- **Prompts:** Interactive workflows guiding multi-step analysis
- **Resources:** Static knowledge bases (markdown files served via MCP)
- **See:** [CLAUDE.md](../../CLAUDE.md) for catalog, [MCP.md](MCP.md) for implementation patterns

#### 4. REST API Endpoints (8 Endpoints)
- **Purpose:** HTTP REST interface for web applications, curl, Postman
- **Responsibilities:**
  - Provide HTTP/JSON API for non-MCP clients
  - Reuse service layer (same business logic as MCP tools)
  - Convert service exceptions to HTTP status codes (404, 400, 500)
  - Return Pydantic-validated JSON responses
  - Swagger documentation auto-generated from Pydantic models

**Key Features:**
  - Shared lifespan with MCP server (single resource set)
  - Exception handlers for domain exceptions → HTTP errors
  - Response validation via Pydantic models
  - Auto-generated OpenAPI/Swagger docs at `/docs`

#### 5. Service Layer (ADR-006)
- **Purpose:** Framework-agnostic business logic layer separating domain operations from transport mechanisms
- **Services (13 total):**
  - **Core:** BaseService, TestService, ProductService, BugService, FeatureService, UserService
  - **Analytics:** AnalyticsService, QueryBuilder, MultiTestReportService
  - **Infrastructure:** SyncService, DiagnosticsService, SearchService, UserStoryService
- **Pattern:** Stateless services with constructor-injected dependencies (client, repositories)
- **Key Benefit:** Reusable across MCP tools, REST endpoints, CLI, and webhooks

**See:** [SERVICE_LAYER_SUMMARY.md](SERVICE_LAYER_SUMMARY.md) for complete service architecture, patterns, repository integration, and code examples.

#### 6. TestIOClient
- **Purpose:** HTTP client wrapper for TestIO Customer API
- **Responsibilities:**
  - Manage httpx.AsyncClient lifecycle
  - Enforce concurrency limits (semaphore)
  - Add authentication headers
  - Handle HTTP errors
  - Retry on transient failures

#### 7. PersistentCache (SQLite Database)
- **Purpose:** Local data store for products, tests, bugs, features, users, and sync metadata
- **Responsibilities:**
  - Store entities in SQLite database with 9 ORM models
  - Provide repository interfaces for all entity types
  - Full-text search via FTS5 (BM25 ranking)
  - Track sync metadata and sync events (observability)
  - Manage problematic tests (500 error tracking)
  - Enable concurrent reads (WAL mode)
  - Auto-VACUUM on startup (reclaim space)

**Architecture:**
- **Database:** SQLite with WAL mode + FTS5 for concurrent reads and search
- **ORM:** SQLModel + SQLAlchemy 2.0 async with 18 Alembic migrations
- **Models (9):** Product, Test, Bug, Feature, TestFeature, User, TestPlatform, SyncMetadata, SyncEvent
- **FTS5 Search:** `search_index` table with 12 triggers, indexes product/feature/test/bug entities
- **Sync Strategy:** Hybrid (3-phase background discovery + on-demand refresh)
- **Data Freshness:** 3-phase background sync (1 hour) + read-through caching (TTL-based)
- **Customer Isolation:** Default customer_id=1 (single-tenant MVP)

**See:**
- [STORY-021: Local Data Store](../stories/done/story-021-local-data-store.md) for implementation details
- [CUSTOMER_ID_STRATEGY.md](CUSTOMER_ID_STRATEGY.md) for rationale behind default customer_id=1

---

## Data Flow

### Typical Request Flow (SQLite-First Architecture)

```
1. User asks Claude: "What's the status of test 12345?"
   │
2. Claude → MCP Server: get_test_summary(test_id=12345)
   │
3. MCP Tool Handler (get_test_summary)
   │
   ├─→ Extract dependencies from FastMCP Context
   │   ├─→ testio_client = ctx["testio_client"]
   │   └─→ cache = ctx["cache"]  # PersistentCache (SQLite)
   │
   ├─→ Create TestService instance with repositories
   │   └─→ service = TestService(
   │           client=testio_client,
   │           test_repo=TestRepository(cache),
   │           bug_repo=BugRepository(cache)
   │       )
   │
   └─→ Delegate to service
       │
4. TestService.get_test_status(test_id=12345)
   │
   ├─→ Query local SQLite database (fast, ~10ms)
   │   └─→ test_repo.get_test_by_id(12345)
   │       ├─→ SELECT * FROM tests WHERE id = 12345
   │       └─→ Test found? → Return immediately ✨ FAST PATH
   │
   ├─→ If not in database: Fallback to API (rare)
   │   ├─→ TestIOClient.get("exploratory_tests/12345")
   │   │   ├─→ Acquire semaphore slot (concurrency control)
   │   │   ├─→ httpx.AsyncClient (from connection pool)
   │   │   └─→ TestIO API: GET /customer/v2/exploratory_tests/12345
   │   │       └─→ Returns: {id, title, status, review_status, ...}
   │   │
   │   └─→ Store in SQLite for future queries
   │       └─→ test_repo.insert_test(test_data)
   │
   ├─→ Aggregate bug data from database
   │   └─→ bug_repo.get_bugs_for_test(12345)
   │       └─→ service._aggregate_bug_summary(bugs)
   │
   └─→ Return structured response to tool
       │
5. MCP Tool returns response to Claude (or converts errors to ToolError format)
   │
6. Claude → User: "Test 12345 'Mobile Checkout Flow' is currently running.
                   Status: review_successful
                   Bugs found: 23 (8 high, 15 low)
                   Started: 2024-11-01, Ends: 2024-11-08"
```

**Key Benefits of SQLite-First Architecture:**
- **Fast queries (~10ms)** - Local database, no network latency
- **Persistent data** - Survives server restarts
- **Hybrid freshness** - Background discovery (1 hour) + on-demand refresh when queried (TTL-based)
- **Repository pattern** - Clean separation of data access logic
- **Framework-agnostic** - Services can be reused in REST API, CLI, webhooks
- **Testable** - Services tested with mock repositories (no database dependency)

### Concurrent Request Flow

```
User queries 3 tests simultaneously via generate_status_report:

Tool spawns 3 concurrent fetch tasks:
┌─────────────────┬─────────────────┬─────────────────┐
│ get_test(123)   │ get_test(456)   │ get_test(789)   │
└────────┬────────┴────────┬────────┴────────┬────────┘
         │                 │                 │
         ├─────────────────┼─────────────────┤
         │    Global Semaphore (max 10)      │
         └─────────────────┬─────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
    │ Slot 1  │       │ Slot 2  │      │ Slot 3  │
    │ (123)   │       │ (456)   │      │ (789)   │
    └────┬────┘       └────┬────┘      └────┬────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                    TestIO API

All 3 requests run concurrently, but only 10 total concurrent
requests allowed across ALL tools (protects API).
```

### Pagination Flow (Updated 2025-11-18)

**Standard Page/Offset Pagination:**

```
User: "List tests for product 123"

Request 1 (First Page):
list_tests(product_id=123, page=1, per_page=100)
└─→ Returns: {
      product: {id: 123, name: "My Product"},
      tests: [100 tests],
      total_tests: 347,
      page: 1,
      per_page: 100,
      total_pages: 4
    }

User: "Show me more"

Request 2 (Next Page):
list_tests(product_id=123, page=2, per_page=100)
└─→ Returns: {
      product: {id: 123, name: "My Product"},
      tests: [next 100 tests],
      total_tests: 347,
      page: 2,
      per_page: 100,
      total_pages: 4
    }
```

**File Export for Large Datasets:**

```
User: "Generate Product Quality Report for products 598 and 599"

Request (File Export):
generate_quality_report(product_ids=[598, 599], output_file="report.json")
└─→ Writes full report to ~/.testio-mcp/reports/report.json
└─→ Returns: {
      file_path: "/Users/username/.testio-mcp/reports/report.json",
      summary: {total_tests: 216, total_bugs: 1840, ...},
      by_product: [{product_id: 598, ...}, {product_id: 599, ...}],
      record_count: 216,
      file_size_bytes: 524288
    }
```

**Note:** Continuation tokens were removed in favor of standard pagination (STORY-023d) and file export (STORY-025). See ADR-003 for historical context.

---

## API Client Design

**See:**
- [ADR-001: API Client Dependency Injection](adrs/ADR-001-api-client-dependency-injection.md)
- [ADR-007: FastMCP Context Injection Pattern](adrs/ADR-007-fastmcp-context-injection.md)

### Key Design Decisions

1. **Dependency Injection** (not singleton)
   - Client passed to tools via FastMCP Context parameter (ADR-007)
   - Lifecycle managed by lifespan handler
   - Easy to test with mocked clients

2. **Connection Pooling**
   - Single httpx.AsyncClient instance per server
   - Default: 20 max connections, 20 keep-alive (configurable via env vars)
   - Reduces latency by 50-200ms per request

3. **Async Context Manager**
   - `async with TestIOClient(...) as client:`
   - Automatic cleanup on shutdown
   - Prevents connection leaks

### Configuration

```python
# TestIOClient initialization (from config.py Settings)
client = TestIOClient(
    base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,  # Default: https://api.stage-a.space/customer/v2
    api_token=settings.TESTIO_CUSTOMER_API_TOKEN,    # Required (no default)
    max_concurrent_requests=10,      # Semaphore limit (ADR-002, configurable)
    max_connections=20,               # HTTP connection pool size (default: 20)
    max_keepalive_connections=20,     # Idle connections to maintain (default: 20)
    timeout=90.0,                     # Request timeout (default: 90s)
)
```

---

## Concurrency & Performance

**See:** [ADR-002: Concurrency Limits](adrs/ADR-002-concurrency-limits.md)

### Concurrency Control

**Global Semaphore:** Limits concurrent API requests to 10 (configurable)

**Why 10?**
- TestIO API rate limits are unknown
- Conservative starting point
- Can increase based on monitoring
- Prevents overwhelming API

**Implementation:**
```python
# In TestIOClient
self._semaphore = asyncio.Semaphore(max_concurrent_requests)

async def get(self, endpoint: str, **kwargs):
    async with self._semaphore:  # Acquire slot
        response = await self._client.get(endpoint, **kwargs)
        return response.json()
```

### Performance Targets

- **Response Time:** 99% of queries < 5 seconds (P99 latency)
- **Local Queries:** ~10ms (SQLite-first architecture)
- **Error Rate:** Monitored via `get_sync_history` tool

**See [PERFORMANCE.md](PERFORMANCE.md) for optimization strategies, benchmarks, troubleshooting, and comprehensive monitoring recommendations.**

---

## Local Data Store Strategy

**See:** [STORY-021: Local Data Store](../stories/done/story-021-local-data-store.md)

### SQLite Database (PersistentCache)

**Design:** SQLite database with repository pattern for data access

**Schema:**
- **products** - All products accessible to customer
- **tests** - Exploratory tests for each product
- **bugs** - Bugs associated with tests
- **sync_metadata** - Track last sync timestamp per product
- **problematic_tests** - Track tests that failed to sync (500 errors)

**Data Freshness (ADR-017):**
- **Background sync** - Every hour (configurable via `TESTIO_REFRESH_INTERVAL_SECONDS`)
- **Initial sync** - On server startup (non-blocking)
- **Manual sync** - Via CLI: `testio-mcp sync`
- **On-demand refresh** - Read-through caching with TTL-based staleness checks

**Background Sync (3 Phases):**
1. **Phase 1:** Refresh product metadata (always)
2. **Phase 2:** Refresh features (TTL-gated, default 1 hour)
3. **Phase 3:** Discover new tests (incremental)

**Read-Through Caching (On-Demand):**
- `BugRepository.get_bugs_cached_or_refresh()` - Refreshes stale bugs when queried
- `TestRepository.get_tests_cached_or_refresh()` - Refreshes stale test metadata
- `FeatureRepository.get_features_cached_or_refresh()` - Refreshes stale features

**CLI Sync Modes:**
- **Incremental sync** - Fetch only new tests (stops at known boundary + 2 safety pages)
- **Force refresh** - Update all tests for product (`--force` flag)
- **Hybrid refresh** - Discover new tests + update mutable tests (`--refresh` flag)

**Why SQLite (not Redis)?**
- **Persistent data** - Survives server restarts (no cold start penalty)
- **TTL-based staleness** - Unified `CACHE_TTL_SECONDS` (default: 1 hour) for on-demand refresh
- **Fast queries** - ~10ms at our scale (imperceptible)
- **Simple deployment** - Single file, no external service
- **WAL mode** - Concurrent reads during background writes

**Migration Triggers (Future):**
- Multi-instance deployment (shared database needed)
- Database size > 500MB (consider PostgreSQL)
- Complex querying needs (full-text search, analytics)

### Repository Pattern

```python
# Repository interfaces for data access
class TestRepository(BaseRepository):
    # Test operations
    async def get_test_by_id(self, test_id: int) -> dict | None
    async def list_tests(self, product_id: int, filters: dict) -> list[dict]
    async def insert_test(self, test: dict, product_id: int) -> None
    async def update_test(self, test: dict, product_id: int) -> None

    # Product operations (stored in separate products table)
    async def get_product_info(self, product_id: int) -> dict | None
    async def get_synced_products_info(self) -> list[dict]
    async def count_products(self) -> int

    # Sync metadata
    async def get_product_last_synced(self, product_id: int) -> str | None
    async def update_product_last_synced(self, product_id: int) -> None

class BugRepository(BaseRepository):
    async def get_bugs_for_test(self, test_id: int) -> list[dict]
    async def insert_bugs(self, bugs: list[dict], test_id: int) -> None
    async def count_bugs_for_test(self, test_id: int) -> int
```

**Design Notes:**
- **2 repositories:** TestRepository (tests + products), BugRepository (bugs)
- **5 database tables:** tests, products, bugs, sync_metadata, sync_events
- **No ProductRepository:** Product operations handled by TestRepository for simplicity
- **Inheritance:** Both inherit from BaseRepository for shared connection/customer_id

### Data Access Pattern

```python
# Service usage pattern (SQLite-first)
class TestService:
    def __init__(self, client, test_repo, bug_repo):
        self.client = client
        self.test_repo = test_repo
        self.bug_repo = bug_repo

    async def get_test_status(self, test_id: int):
        # 1. Query local database (fast, ~10ms)
        test = await self.test_repo.get_test_by_id(test_id)

        # 2. If not found, fallback to API (rare)
        if not test:
            test_data = await self.client.get(f"exploratory_tests/{test_id}")
            await self.test_repo.insert_test(test_data)
            test = test_data

        # 3. Get bugs from database
        bugs = await self.bug_repo.get_bugs_for_test(test_id)

        # 4. Aggregate and return
        return {"test": test, "bugs": bugs, "summary": self._aggregate(bugs)}
```

### Read-Through Caching Pattern (ADR-017)

Data freshness is maintained through a hybrid approach combining background discovery with on-demand refresh:

**Background Sync (3 Phases):**
```
┌────────────────────────────────────────────────────────────────┐
│ Phase 1: Refresh product metadata (always)                     │
│ Phase 2: Refresh features (TTL-gated, default 1 hour)          │
│ Phase 3: Discover new tests (incremental)                      │
│ Phase 4: REMOVED - bugs/tests refresh on-demand                │
└────────────────────────────────────────────────────────────────┘
```

**On-Demand Refresh (Read-Through):**
```python
# In AnalyticsService or TestService
async def query_data(self, test_ids: list[int]):
    # 1. Check staleness + refresh if needed (single method call)
    bugs, cache_stats = await bug_repo.get_bugs_cached_or_refresh(test_ids)

    # 2. Include staleness warning if data was refreshed
    if cache_stats["api_calls"] > 0:
        warnings.append(f"Refreshed {cache_stats['api_calls']} stale tests")

    return results, warnings
```

**Per-Entity Locks:**
- Prevent duplicate API calls for concurrent requests
- Stored in `PersistentCache._refresh_locks` registry
- Key: `(customer_id, entity_type, entity_id)`

```python
# In PersistentCache
def get_refresh_lock(self, entity_type: str, entity_id: int) -> asyncio.Lock:
    key = (self.customer_id, entity_type, entity_id)
    return self._refresh_locks.setdefault(key, asyncio.Lock())
```

**See:** [ADR-017: Background Sync Optimization](adrs/ADR-017-background-sync-optimization-pull-model.md)

### Async Session Management (STORY-062)

**CRITICAL:** `AsyncSession` is NOT concurrency-safe. Sharing one session across `asyncio.gather()` tasks causes database corruption:
- `sqlite3.ProgrammingError: Cannot operate on a closed database`
- `SAWarning: Attribute history events accumulated on previously clean instances`

**Per-Operation Session Pattern:**

When concurrent database writes are needed (e.g., batch refresh operations), each task MUST create its own isolated session:

```python
async def get_features_cached_or_refresh(self, product_ids: list[int]):
    async def refresh_product(product_id: int):
        # ✅ CORRECT: Each task creates its own session
        async with self.cache.async_session_maker() as session:
            repo = FeatureRepository(session, self.client, self.customer_id)
            await repo.sync_features(product_id)

    # Safe: Each task is isolated
    await asyncio.gather(*[refresh_product(pid) for pid in products_to_refresh])
```

**Session Lifecycle Rules:**

| Scenario | Pattern | Who Commits |
|----------|---------|-------------|
| Simple operations | Repository receives session | Repository commits |
| Batch operations | Per-item isolated session | Each isolated session commits |
| Sequential phases | Shared session | Last operation or explicit commit |

**SQLite Write Serialization:**

SQLite serializes all writes even with WAL mode. The benefit of `asyncio.gather()` is overlapping API I/O, not parallel DB writes. The HTTP client semaphore (~10 concurrent calls) naturally throttles commit contention.

**Files Using This Pattern:**
- `feature_repository.py:get_features_cached_or_refresh()`
- `bug_repository.py:get_bugs_cached_or_refresh()`

**See:** CLAUDE.md "Async Session Management" section for complete documentation, code examples, and rationale.

---

## Error Handling

**See:** [Story 8: Error Handling & Polish](../stories/story-008-error-handling.md)

### Error Message Format

All errors follow 3-part format:

1. **❌ Error** - What went wrong
2. **ℹ️ Context** - Why it happened
3. **💡 Hint** - How to fix it

**Example:**
```json
{
  "error": "❌ Test ID '12345' not found",
  "context": "ℹ️ The test may have been deleted or you may not have access",
  "hint": "💡 Use list_active_tests to see available tests for this product"
}
```

### Error Handling Layers

```
Layer 1: HTTP Client (TestIOClient)
├─ Catches httpx.HTTPStatusError
├─ Always raises TestIOAPIError with status_code
├─ NO domain logic (e.g., no special handling for test vs product endpoints)
├─ Token sanitization in error messages (SEC-002)
└─ Example: HTTPStatusError(404) → TestIOAPIError(message="...", status_code=404)

Layer 2: Service Layer (Business Logic)
├─ Translates TestIOAPIError → domain exceptions
├─ Example: TestIOAPIError(404) → TestNotFoundException or ProductNotFoundException
├─ Services decide which domain exception to raise based on context
└─ Raises domain exceptions for tool layer to handle

Layer 3: Tool Layer (MCP Interface)
├─ Catches domain exceptions (TestNotFoundException, ProductNotFoundException)
├─ Converts to user-friendly ❌ℹ️💡 format
├─ Input validation via Pydantic
└─ Example: TestNotFoundException → {"error": "❌ Test not found", "context": "ℹ️ ...", "hint": "💡 ..."}
```

**Key Principle**: Clean separation of concerns
- Client = Transport errors only (HTTP status codes)
- Service = Domain logic (which 404 means what?)
- Tool = User-facing messages

### Retry Strategy

```python
# Exponential backoff for retryable errors (Story 8: planned feature)
# NOTE: Client layer currently does not implement retries (MVP scope)
# Services catch TestIOAPIError and can implement retry logic as needed

async def get_with_retry(endpoint, max_retries=3):
    """Example retry implementation for future use."""
    for attempt in range(max_retries):
        try:
            return await client.get(endpoint)
        except TestIOAPIError as e:
            if e.status_code == 429:  # Rate limit
                wait = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait)
                continue
            elif e.status_code >= 500:  # Server error
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            raise
        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                continue
            raise
```

---

## Security Considerations

**See:** [SECURITY.md](SECURITY.md)

### Authentication

- **Method:** Token-based (`Authorization: Token <token>`)
- **Storage:** Environment variable (`TESTIO_CUSTOMER_API_TOKEN`)
- **Rotation:** Manual (no automated rotation in MVP)

### Input Validation

```python
# All tool inputs validated via Pydantic
class GetTestBugsInput(BaseModel):
    test_id: str = Field(pattern=r"^\d+$")  # Only digits
    bug_type: Literal["functional", "visual", "content", "all"]
    severity: Literal["low", "high", "critical", "all"]
    page_size: int = Field(ge=1, le=1000)  # Between 1-1000
```

### Output Sanitization

**Risk:** Bug titles/descriptions may contain user-generated content

**Mitigation:**
- MCP protocol handles JSON encoding (prevents injection)
- AI clients (Claude) sanitize for display
- No direct HTML rendering in MVP

### Secrets Management

**MVP:** `.env` file (not committed to git)

**Production Options:**
- AWS Secrets Manager
- HashiCorp Vault
- Environment variables in container orchestration

---

## Deployment Architecture

### stdio Mode (Single MCP Client)

**Use Case:** One MCP client (Claude Code OR Cursor, not both simultaneously)

```
┌─────────────────────────────────────┐
│  Developer Machine / CSM Laptop     │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  Claude Desktop / Cursor      │  │
│  │  (AI Client)                  │  │
│  └──────────────┬────────────────┘  │
│                 │ MCP (stdio)       │
│  ┌──────────────▼────────────────┐  │
│  │  TestIO MCP Server            │  │
│  │  (Python process)             │  │
│  │                               │  │
│  │  - Transport: stdio           │  │
│  │  - Database: ~/.testio-mcp/   │  │
│  │  - Config: .env file          │  │
│  └──────────────┬────────────────┘  │
│                 │ HTTPS             │
└─────────────────┼───────────────────┘
                  │
          ┌───────▼────────┐
          │  TestIO API    │
          │  (Production)  │
          └────────────────┘
```

**Characteristics:**
- Single-user, single-client deployment
- No network exposure (stdio = inter-process communication)
- Configuration via `.env` file
- SQLite database: `~/.testio-mcp/cache.db`
- Logs hidden by stdio transport (use `tail -f ~/.testio-mcp/logs/server.log`)

**Limitations:**
- Can't run multiple MCP clients simultaneously (database lock conflicts)
- Logs not visible in terminal (captured by MCP framework)

---

### HTTP Mode (Multiple MCP Clients) - RECOMMENDED

**Use Case:** Multiple MCP clients (Claude Code + Cursor + Inspector)

```
┌─────────────────────────────────────┐
│  Developer Machine / CSM Laptop     │
│                                     │
│  ┌──────────┐  ┌──────────┐  ┌────┐ │
│  │  Claude  │  │  Cursor  │  │Insp│ │
│  │  Code    │  │          │  │ect │ │
│  └────┬─────┘  └────┬─────┘  └─┬──┘ │
│       │ HTTP        │ HTTP     │    │
│       └─────────────┼──────────┘    │
│                     │               │
│       ┌─────────────▼────────────┐  │
│       │  TestIO MCP Server       │  │
│       │  (Python process)        │  │
│       │                          │  │
│       │  - Transport: HTTP       │  │
│       │  - Port: 8080            │  │
│       │  - URL: /mcp             │  │
│       │  - Database: shared      │  │
│       └──────────┬───────────────┘  │
│                  │ HTTPS            │
└──────────────────┼──────────────────┘
                   │
           ┌───────▼────────┐
           │  TestIO API    │
           │  (Production)  │
           └────────────────┘
```

**Start HTTP server:**
```bash
# Terminal 1: Start MCP server
uv run python -m testio_mcp serve --transport http --port 8080

# Terminal 2: Watch logs
tail -f ~/.testio-mcp/logs/server.log
```

**Configure clients:**
```json
// .claude/config.json or .cursor/config.json
{
  "mcpServers": {
    "testio": {
      "url": "http://127.0.0.1:8080/mcp"
    }
  }
}
```

**Characteristics:**
- Multi-client deployment (all clients share same server)
- HTTP on localhost only (127.0.0.1:8080)
- **No database lock conflicts** (single process handles all clients)
- **No redundant API calls** (single background sync process)
- **Logs visible in terminal** (not captured by stdio)
- SQLite database shared across all clients
- **Hybrid API mode** - MCP + REST + Swagger docs (default)

**Benefits over stdio mode:**
- ✅ Run Claude Code + Cursor + Inspector simultaneously
- ✅ Single background sync (efficient)
- ✅ Logs visible for debugging
- ✅ Better resource utilization
- ✅ REST API available for web apps, curl, Postman
- ✅ Interactive API docs at http://localhost:8080/docs

**Access Points:**
- **MCP Protocol:** `http://localhost:8080/mcp` (AI clients)
- **REST API:** `http://localhost:8080/api/*` (web apps, curl)
- **Swagger Docs:** `http://localhost:8080/docs` (interactive explorer)
- **Health Check:** `http://localhost:8080/health` (monitoring)

**See:** [STORY-023a: HTTP Transport](../stories/done/story-023a-http-transport.md) and [STORY-023f: REST API](../stories/done/story-023f-rest-api.md) for implementation details.

### Future: Multi-User Deployment (Cloud-Hosted)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  CSM User 1  │  │  CSM User 2  │  │  PM User 3   │
│  (Claude)    │  │  (Cursor)    │  │  (Claude)    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │ HTTPS           │ HTTPS           │ HTTPS
       └─────────────────┼─────────────────┘
                         │
              ┌──────────▼──────────┐
              │  Load Balancer      │
              └──────────┬──────────┘
                         │
       ┌─────────────────┼────────────────┐
       │                 │                │
┌──────▼─────┐   ┌───────▼──────┐  ┌──────▼─────┐
│ MCP Server │   │ MCP Server   │  │ MCP Server │
│ Instance 1 │   │ Instance 2   │  │ Instance 3 │
└──────┬─────┘   └───────┬──────┘  └──────┬─────┘
       │                 │                │
       └─────────────────┼────────────────┘
                         │
              ┌──────────▼──────────┐
              │  PostgreSQL         │
              │  (Shared Database)  │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  TestIO API         │
              └─────────────────────┘
```

**Future Requirements:**
- **Shared database** - PostgreSQL (SQLite doesn't support multi-instance writes)
- **Migration strategy** - SQLite → PostgreSQL with minimal code changes
- **Load balancing** - Distribute requests across instances
- **Health checks** - Monitor instance health
- **Monitoring/alerting** - Track performance, errors, sync status
- **Secret management** - Secure API token distribution

---

## Testing Strategy

### Testing Pyramid (Current State)

```
           ┌───────────┐
          ╱  E2E Tests  ╲      ~10 tests
         ╱   (MCP+REST)  ╲     (Full protocol)
        ┌─────────────────┐
       ╱    Integration    ╲    53 tests
      ╱     (Tools+API)     ╲   (Real API calls)
     ┌───────────────────────┐
    ╱      Service Tests      ╲  ~90 tests
   ╱     (Mock client/cache)   ╲ (Business logic)
  ┌──────────────────────────────┐
 ╱     Unit Tests (Tools+Utils)   ╲ 304 tests
╱     (Tool wrappers, helpers)     ╲ (Fastest)
└───────────────────────────────────┘

Total: 448+ tests
```

### Key Testing Principles

- **Service layer focus:** Primary test coverage at service layer (90 tests) with mocked dependencies
- **Fast feedback:** Unit tests run in <1 second, service tests in <2 seconds
- **Behavioral testing:** Test outcomes and behaviors, not implementation details
- **High coverage:** ≥85% overall, ≥90% for services
- **Test organization:** `tests/unit/`, `tests/services/`, `tests/integration/`, `tests/e2e/`

**See [TESTING.md](TESTING.md) for comprehensive testing guidelines** including behavioral testing principles, anti-patterns, coverage requirements, test organization, and practical examples.

---

## Architecture Decision Records

All critical architectural decisions are documented as ADRs:

1. **[ADR-001: API Client Dependency Injection](adrs/ADR-001-api-client-dependency-injection.md)**
   - Use FastMCP context for dependency injection
   - Connection pooling via httpx.AsyncClient
   - Lifecycle managed by lifespan events
   - **Updated:** Service layer pattern examples added

2. **[ADR-002: Concurrency Limits](adrs/ADR-002-concurrency-limits.md)**
   - Global semaphore limiting to 10 concurrent requests
   - Configurable via `MAX_CONCURRENT_API_REQUESTS`
   - Protects TestIO API (unknown rate limits)

3. **[ADR-003: Pagination Strategy](adrs/ADR-003-pagination-strategy.md)** *(Superseded - See note)*
   - **Original:** First page + continuation token pattern
   - **Current:** Standard page/offset pagination (STORY-023d) + file export (STORY-025)
   - **Superseded:** 2025-11-18 - Continuation tokens removed for simpler approach

4. **[ADR-004: Cache Strategy MVP](adrs/ADR-004-cache-strategy-mvp.md)** *(Superseded by STORY-021)*
   - **Original:** In-memory cache with TTL
   - **Current:** SQLite database with background sync
   - **See:** [STORY-021: Local Data Store](../stories/done/story-021-local-data-store.md) for current implementation

5. **[ADR-005: Response Size Limits](adrs/ADR-005-response-size-limits.md)**
   - Soft limits with warnings
   - Default 100 items, max 1000 items per page
   - User can override with clear guidance

6. **[ADR-006: Service Layer Pattern](adrs/ADR-006-service-layer-pattern.md)**
   - Separate business logic from transport mechanisms
   - Framework-agnostic services (TestService, ProductService, MultiTestReportService)
   - Tools are thin wrappers that delegate to services
   - Services use repository pattern for data access (STORY-023c)
   - Enables future multi-transport architecture (REST, CLI, webhooks)
   - Improves testability (no MCP framework mocking required)

7. **[ADR-007: FastMCP Context Injection Pattern](adrs/ADR-007-fastmcp-context-injection.md)**
   - Use FastMCP lifespan handler for resource initialization
   - Store dependencies on app instance for access via Context
   - Tools receive `ctx: Context` parameter (injected by framework)
   - Replaces custom getter functions with framework convention
   - Prerequisite for future HTTP multi-tenancy (STORY-010)

8. **[ADR-015: Feature Staleness and Sync Strategy](adrs/ADR-015-feature-staleness-and-sync-strategy.md)** *(Partially superseded by ADR-017)*
   - TTL-based staleness refresh for features (1 hour default)
   - Background sync + on-demand refresh pattern
   - **Note:** Sync phases updated by ADR-017

9. **[ADR-016: Alembic Migration Strategy](adrs/ADR-016-alembic-migration-strategy.md)**
   - Single-path with frozen baseline DDL
   - pytest-alembic CI protection
   - Auto-discovery of ORM model changes

10. **[ADR-017: Background Sync Optimization - Pull Model](adrs/ADR-017-background-sync-optimization-pull-model.md)** **[NEW]**
    - Shift from push model (4-phase proactive refresh) to pull model (3-phase + on-demand)
    - Read-through caching with per-entity locks
    - Unified `CACHE_TTL_SECONDS` configuration
    - 95% reduction in API calls during background sync

**When to Create New ADRs:**
- Changing any of the above decisions
- Adding new major components (Redis, message queue, etc.)
- Significant architecture changes (multi-tenancy, write operations, etc.)

---

## References

- **Project Brief (ARCHIVED):** [docs/archive/planning/project-brief-mvp-v2.4.md](../archive/planning/project-brief-mvp-v2.4.md)
- **Epic:** [docs/epics/epic-001-testio-mcp-mvp.md](../epics/epic-001-testio-mcp-mvp.md)
- **Stories:** [docs/stories/](../stories/)
- **FastMCP Docs:** https://github.com/jlowin/fastmcp
- **TestIO API Docs:** (Internal - see project brief for verified endpoints)
- **MCP Specification:** https://spec.modelcontextprotocol.io/

---

## Document Status

**Version:** 3.0.0
**Status:** ✅ Production Ready
**Last Review:** 2025-12-03
**Next Review:** After multi-tenant features (STORY-010)

**Changelog:**
- **v3.1.0 (2025-12-21):** v0.4.0 updates - PQR refactor to multi-product, REST API additions
- **v3.0.0 (2025-12-03):** Major update - BMAD document-project workflow validation
  - ✅ Validated all sections against live codebase via automated scan
  - **MCP Layer:** 8 → 17 tools (categorized), added 2 prompts, 2 resources
  - **Service Layer:** 3 → 13 services with detailed categorization
  - **Data Layer:** 5 → 9 ORM models, added FTS5 full-text search
  - **Migrations:** 1 baseline → 18 Alembic migrations
  - Updated component architecture diagram with all current components
  - Added MCP prompts and resources documentation
  - Added FTS5 search capability documentation
  - Cross-referenced Epic 005 (features/users), Epic 007 (analytics), Epic 009 (sync), Epic 010 (search), Epic 014 (prompts)
- **v2.2.1 (2025-11-27):** Async Session Management (STORY-062)
  - Added "Async Session Management" section under Local Data Store Strategy
  - Documents per-operation session pattern for batch operations
  - Cross-references CLAUDE.md for detailed implementation guidance
- **v2.2.0 (2025-11-26):** Background Sync Optimization (ADR-017)
  - Updated sync strategy: 4-phase → 3-phase background sync
  - Added read-through caching pattern documentation
  - Updated TTL configuration: Unified `CACHE_TTL_SECONDS`
  - Added ADR-015, ADR-016, ADR-017 references
  - Added per-entity lock documentation
- **v2.1.1 (2025-11-20):** Content Consolidation
  - Consolidated duplicate content with cross-references to specialized guides
  - **Service Layer:** Reduced from 65 lines → 6 lines, link to SERVICE_LAYER_SUMMARY.md
  - **Testing Strategy:** Reduced from 102 lines → 21 lines, link to TESTING.md
  - **Performance:** Reduced from 22 lines → 6 lines, link to PERFORMANCE.md
  - Added cross-references: MCP.md, TECH-STACK.md, CUSTOMER_ID_STRATEGY.md, SECURITY.md
  - **Document size:** 1,123 lines → 998 lines (11% reduction, ~6,000 tokens saved)
  - Clear separation: Architectural overview (ARCHITECTURE.md) vs. implementation guides (sibling docs)
- **v2.1 (2025-11-20):** Pre-0.2.0 Release Validation
  - ✅ Validated all sections against live codebase
  - Corrected tool count (5 → 8 actual tools)
  - Updated repository pattern (2 repos: TestRepository, BugRepository)
  - Corrected database tables (5 tables: tests, products, bugs, sync_metadata, sync_events)
  - Ready for v0.2.0 release
- **v2.0 (2025-11-18):** Major update - SQLite-first architecture
  - Replaced InMemoryCache with PersistentCache (SQLite database)
  - Updated service layer: 5 services → 3 services (TestService, ProductService, MultiTestReportService)
  - Added repository pattern (TestRepository, BugRepository)
  - Added HTTP transport mode for multiple MCP clients (STORY-023a)
- **v1.1 (2025-11-04):** Service Layer Pattern Added
  - Added ADR-006: Service Layer Pattern
  - Pre-implementation refinement (ground zero)
- **v1.0 (2025-11-04):** Initial architecture document
  - Created after comprehensive story review
  - All ADRs finalized and approved
