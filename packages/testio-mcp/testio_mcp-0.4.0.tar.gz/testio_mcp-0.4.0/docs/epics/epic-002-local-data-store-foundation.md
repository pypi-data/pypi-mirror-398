# Epic 002: Local Data Store Foundation - Brownfield Enhancement

## Epic Goal

Build a persistent SQLite-based data store with incremental sync that enables instant queries (<50ms) and eliminates complex API pagination logic, providing the foundation for advanced multi-test analytics and reporting features.

## Epic Description

### Existing System Context

**Current functionality:**
- In-memory cache (`InMemoryCache`) with TTL-based expiration (1h products, 5min tests, 1min bugs)
- API-based pagination that fetches data on every request (5-10s per query)
- Tools query API directly through services, no persistent storage
- Cache stampede protection and concurrency controls via semaphore

**Technology stack:**
- Python async (`asyncio`, `aiosqlite`)
- FastMCP for MCP server framework
- TestIO Customer API for data source
- ADR-006 service layer pattern

**Integration points:**
- All services (`ProductService`, `TestService`, `ActivityService`) depend on cache
- Cache injected via `BaseService` dependency injection
- Tools use `get_service()` helper to access services with cache

### Enhancement Details

**What's being added/changed:**

This epic replaces the in-memory cache with a persistent SQLite database that:
1. **Survives restarts** - Data persists across MCP server restarts
2. **Incremental sync** - Fetches only new tests since last sync using chronological ordering
3. **Instant queries** - SQL-based filtering/pagination (~10ms vs 5-10s API calls)
4. **Multi-customer ready** - Schema includes `customer_id` for future multi-customer support (STORY-010)

**Major architectural change:**
- `InMemoryCache` → `PersistentCache` (SQLite-only, no two-tier complexity)
- All services updated to use new cache interface
- Database location: `~/.testio-mcp/cache.db` (configurable via `TESTIO_DB_PATH`)

**How it integrates:**

1. **Cache layer** - `PersistentCache` implements same interface as `InMemoryCache` but with SQLite backend
2. **Service layer** - Services call `cache.sync_product_tests()` then `cache.query_tests()` instead of direct API calls
3. **Background sync** - Optional 5-minute refresh keeps active test data current
4. **Database tools** - Existing cache tools transformed to database management (stats, clear, force sync)

**Success criteria:**

- Query performance <50ms after initial sync (1000x faster than API)
- Incremental sync stops at first known test ID (self-correcting algorithm)
- Database survives server restarts with data intact
- Coverage >85% across new persistent cache components
- Rollback available via feature flag (`TESTIO_ENABLE_LOCAL_STORE=false`)

## Stories

### 1. STORY-021: Local Data Store with Incremental Sync (6-8 hours)
**Description:** Create SQLite database with `tests` and `products` tables, implement incremental sync algorithm that stops at first known test ID, build query interface with customer_id isolation, add database management tools.

**Key deliverables:**
- SQLite schema with multi-customer support (`customer_id` columns)
- `PersistentCache` class replacing `InMemoryCache`
- Incremental sync: `sync_product_tests(product_id)`
- Query interface: `query_tests()` with status/date/pagination filters
- Database tools: `get_database_stats()`, `clear_cache()`, `force_sync_product()`
- Comprehensive tests (unit + integration, >85% coverage)

**Critical patterns:**
- Chronological ordering enables self-correcting sync (fetch newest → stop at first known ID)
- SQLite-only (no in-memory layer) - 10ms queries are instant at our scale
- Customer isolation via `customer_id` in all queries (multi-tenant prep for STORY-010)

### 2. STORY-020: Add Robust Pagination to list_tests Tool (2-3 hours)
**Description:** Simplify list_tests pagination using local store SQL queries instead of complex parallel-fetch logic. Add `page` and `per_page` parameters to tool, update `ProductService.list_tests()` to query from SQLite.

**Key deliverables:**
- Tool signature updated: `list_tests(product_id, page=1, per_page=100, statuses=None, ...)`
- Service simplified: `sync_product_tests()` → `query_tests()` (no complex pagination)
- Response includes pagination metadata: `{page, per_page, has_more}`
- Tests updated for new pagination pattern

**Dependencies:**
- **CRITICAL:** Must be implemented AFTER STORY-021 (relies on `PersistentCache.query_tests()`)
- Estimate reduced from 6-8h to 2-3h (60% reduction) due to SQL simplification

## Compatibility Requirements

### Backward Compatibility

- ✅ Existing tool APIs remain unchanged (list_tests signature extended, not changed)
- ✅ Service layer interface compatible (services still call cache methods)
- ⚠️ **Breaking change:** `InMemoryCache` → `PersistentCache` (different implementation, same interface pattern)
- ✅ Database schema multi-tenant ready (no migration needed for STORY-010)

### Configuration Changes

**Centralized Storage Directory:**
- All persistent data stored in `~/.testio-mcp/` directory
- Database: `~/.testio-mcp/cache.db` (default)
- Future: `.env` and `customers.yaml` can also reside here (optional)
- **Rationale:** Cross-platform, hidden, centralized for easy backup/migration

**New environment variables:**
```bash
TESTIO_CUSTOMER_ID=25073                    # Required: TestIO/Cirro customer ID
TESTIO_CUSTOMER_NAME="Customer A"              # Optional: Human-friendly name (default: "default")
TESTIO_DB_PATH=~/.testio-mcp/cache.db      # Optional: SQLite path (default shown)
TESTIO_REFRESH_INTERVAL_SECONDS=300        # Optional: Background sync (0=disabled)
TESTIO_ENABLE_LOCAL_STORE=true             # Optional: Feature flag for rollout
```

**Notes:**
- `TESTIO_CUSTOMER_ID` is the TestIO/Cirro system's customer ID (obtained from TestIO admin tools, NOT auto-generated). This is NOT the same as product ID.
- `~/.testio-mcp/` directory auto-created if missing

### Performance Impact

**Before (In-Memory Cache):**
- Query with filter: 5 API pages × 2s = 10s
- Cold start: Same as warm (no persistence)

**After (SQLite Store):**
- Cold start: 2-5s (initial sync, one-time)
- Warm queries: 10-50ms (1000x faster)
- Background sync keeps data fresh

### Integration Points

**Tool patterns:**
- `get_service()` helper unchanged
- `ToolError` exception pattern unchanged
- Auto-discovery via `@mcp.tool()` decorator unchanged

**Cache migration:**
- All services updated from `InMemoryCache` → `PersistentCache`
- Cache interface similar (inject via constructor, call async methods)
- Key change: No TTL management needed (incremental sync handles freshness)

**API contract stability:**
- Relies on TestIO API chronological ordering (newest first)
- Relies on stable test ID uniqueness
- Relies on pagination consistency (100 tests per page)

## Risk Mitigation

### Primary Risk: Incremental Sync Algorithm Correctness

**Risk:** Self-correcting sync might miss tests or create duplicates if API ordering changes or test IDs are not monotonic.

**Mitigation:**
- Comprehensive unit tests with mock API responses (simulate gaps, reordering)
- Integration tests with real API to validate chronological ordering assumption
- Safety limit: Stop after 50 pages (5000 tests) with warning log
- Sync metadata tracking (`last_synced` timestamp per product)

**Rollback Plan:**
- Feature flag: `TESTIO_ENABLE_LOCAL_STORE=false` to revert to `InMemoryCache`
- Database deletion: Remove `~/.testio-mcp/cache.db` and restart server
- No user impact (project has no production users yet)

### Secondary Risk: SQLite Performance at Scale

**Risk:** Query performance degrades with large datasets (>10k tests per product).

**Mitigation:**
- Indexes on `customer_id`, `product_id`, `status`, `created_at` for fast filtering
- VACUUM on startup to compact database
- Load testing with large products (>5000 tests)
- Fallback to in-memory cache via feature flag if performance issues

### Tertiary Risk: Cache Migration Impact

**Risk:** Switching from `InMemoryCache` to `PersistentCache` breaks existing services.

**Mitigation:**
- Service layer abstraction isolates cache implementation from consumers
- Both caches follow same async method pattern
- Comprehensive service tests with mocked cache
- Gradual rollout: Week 1 opt-in → Week 2 opt-out → Week 3 always-on

## Definition of Done

- [x] STORY-021: PersistentCache implemented with SQLite backend
  - [x] Schema created with customer_id isolation
  - [x] Incremental sync algorithm working (stops at first known ID)
  - [x] Query interface with filters (status, date, pagination)
  - [x] Database tools (stats, clear, force sync)
  - [x] Tests passing (>85% coverage)

- [x] STORY-020: list_tests pagination simplified
  - [x] Tool signature updated (page, per_page parameters)
  - [x] Service uses SQLite queries (not complex parallel-fetch)
  - [x] Pagination metadata in response
  - [x] Tests updated for new pattern

- [x] All existing functionality verified through testing
  - [x] Service unit tests pass with PersistentCache
  - [x] Integration tests pass with real API
  - [x] No regression in existing tools/services

- [x] Integration points working correctly
  - [x] All services use PersistentCache successfully
  - [x] Background sync runs without blocking server startup
  - [x] Database tools accessible via MCP

- [x] Documentation updated appropriately
  - [x] README.md mentions local store feature
  - [x] Environment variables documented
  - [x] Migration guide (InMemoryCache → PersistentCache)

- [x] Performance targets met
  - [x] Query performance <50ms (measured via integration tests)
  - [x] Initial sync <5s for products with <1000 tests
  - [x] Incremental sync <2s for typical updates

- [x] Rollback plan validated
  - [x] Feature flag works (can disable local store)
  - [x] Database deletion safe (server recreates on next run)
  - [x] No data loss risk (API is source of truth)

---

**Epic Status:** ✅ COMPLETED - 2025-01-20
**Release Version:** 0.2.0
**Stories Completed:** 9/9 (100%)

## Validation Notes

**No production users:** Risk is minimal as project has no users yet. This epic enables powerful CSM use cases and sets groundwork for future features (multi-test analytics, EBR reports).

**Key validation:** Incremental sync correctness is the primary risk area. Ensure comprehensive testing of sync algorithm edge cases (gaps in data, reordered tests, safety limits).

---

**Epic Created:** 2025-01-07
**Author:** Sarah (Product Owner)
**Parent Design:** docs/architecture/STORY-019-021-ARCHITECTURE-REVIEW.md
**Related Epic:** Epic 003 (Automated Executive Testing Reports) depends on this foundation
