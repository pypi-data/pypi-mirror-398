---
story_id: STORY-023c
epic_id: EPIC-004
title: SQLite-First Foundation - Repository Layer
status: approved
created: 2025-01-17
estimate: 2 story points (2 days)
assignee: dev
dependencies: [STORY-023b]
priority: critical
---

## Story

**As a** developer building on the new architecture
**I want** a repository layer that queries SQLite directly
**So that** we eliminate in-memory cache complexity and have a single source of truth

## Problem Solved

**Current (Dual Data Sources):**
```
Tools → Service Layer → BaseService._get_cached_or_fetch()
                              ↓
                        ┌─────┴─────┐
                        ↓           ↓
                   InMemoryCache   TestIOClient
                   (TTL=300s)      (HTTP API)
                        ↓           ↓
                   RAM (stale?)   API (fresh)
```

**Issues:**
- ❌ Two data sources (cache + database)
- ❌ Cache invalidation complexity
- ❌ TTL management
- ❌ Stampede protection
- ❌ Complex testing (mock 2 things)

**After (SQLite-Always):**
```
Tools → Service Layer → Repository Layer
                              ↓
                         SQLiteDB
                         (WAL mode)
                              ↓
                         Disk (single source)
```

**Benefits:**
- ✅ One data source (SQLite)
- ✅ No cache invalidation
- ✅ No TTL management
- ✅ Simple testing (mock 1 thing)
- ✅ Faster list queries (~10ms)

## Acceptance Criteria

### AC1: Create Repository Layer

**Create `src/testio_mcp/repositories/`:**
- [ ] Create `__init__.py` with repository exports
- [ ] Create `base_repository.py` with shared DB connection logic
- [ ] Create `bug_repository.py` for bug operations

**BugRepository Methods:**
```python
class BugRepository(BaseRepository):
    """Repository for bug data access."""

    async def get_bugs(self, test_id: int) -> list[dict]:
        """Get all bugs for a test from SQLite."""

    async def get_bug_stats(self, test_id: int) -> dict:
        """Get bug statistics (counts by status)."""

    async def refresh_bugs(self, test_id: int) -> int:
        """Fetch fresh bugs from API, upsert to SQLite, return count."""
```

**Why BugRepository?**
- Bugs are NOT currently in PersistentCache (STORY-021)
- Tests and products already have repositories (TestRepository, ProductRepository)
- BugRepository completes the data access layer

### AC2: Update TestRepository

**Extend existing `TestRepository`:**
- [ ] Add `get_test_with_bugs(test_id: int)` - Join tests + bugs
- [ ] Add `refresh_test(test_id: int)` - Fetch fresh test data from API
- [ ] Document that background sync keeps data fresh

**Why extend TestRepository?**
- Tests are already in PersistentCache (STORY-021)
- Just adding methods for new access patterns (list vs get)

### AC3: Delete In-Memory Cache

**Remove cache layer:**
- [ ] Delete `src/testio_mcp/cache.py` (InMemoryCache class)
- [ ] Delete cache initialization in `server.py`
- [ ] Remove `CACHE_TTL_*` environment variables from `config.py`
- [ ] Update dependency injection (no more cache parameter)

**What gets deleted:**
- `InMemoryCache` class (~200 lines)
- `BaseService._get_cached_or_fetch()` method
- TTL constants and configuration
- Cache-related tests

### AC4: Update Services to Use Repositories

**Update TestService:**
- [ ] Inject `TestRepository` and `BugRepository` instead of cache
- [ ] Update `get_test_status()`:
  ```python
  async def get_test_status(self, test_id: int) -> dict:
      # Refresh data (always fresh)
      await self.test_repo.refresh_test(test_id)
      await self.bug_repo.refresh_bugs(test_id)

      # Query from SQLite
      test = await self.test_repo.get_test_with_bugs(test_id)
      return test
  ```
- [ ] Update `list_tests()` to query SQLite (no API call)

**Update ProductService:**
- [ ] Already uses TestRepository from STORY-021
- [ ] No changes needed (products come from background sync)

### AC5: Verify No Regressions

- [ ] Run full test suite: `uv run pytest`
- [ ] Verify all 160 tests pass
- [ ] Update tests to mock repositories (not cache)
- [ ] Verify performance:
  - `list_tests`: ~10ms (SQLite query)
  - `get_test_status`: ~70ms (2 API calls + SQLite)

## Tasks

### Task 1: Create Repository Layer (3 hours)

**Create BugRepository:**
- [ ] Create `src/testio_mcp/repositories/bug_repository.py`
- [ ] Implement `get_bugs()` - Query bugs from SQLite
- [ ] Implement `get_bug_stats()` - Aggregate bug counts
- [ ] Implement `refresh_bugs()` - Fetch from API, upsert to SQLite
- [ ] Add comprehensive type hints and docstrings

**Extend TestRepository:**
- [ ] Add `get_test_with_bugs()` method (LEFT JOIN tests + bugs)
- [ ] Add `refresh_test()` method (fetch from API, upsert to SQLite)
- [ ] Document background sync behavior

**Create BaseRepository:**
- [ ] Shared DB connection logic
- [ ] Common query patterns (get, list, upsert)
- [ ] Error handling for DB operations

### Task 2: Delete In-Memory Cache (1 hour)

- [ ] Delete `src/testio_mcp/cache.py`
- [ ] Remove cache from `server.py` initialization
- [ ] Remove `CACHE_TTL_*` from `config.py`
- [ ] Delete `BaseService._get_cached_or_fetch()`
- [ ] Update dependency injection throughout codebase

### Task 3: Update Services (2 hours)

**TestService refactoring:**
- [ ] Inject repositories instead of cache
- [ ] Update `get_test_status()` to refresh then query
- [ ] Update `list_tests()` to query SQLite directly
- [ ] Remove all cache-related code

**ProductService refactoring:**
- [ ] Verify it already uses TestRepository (STORY-021)
- [ ] No changes needed (products from background sync)

### Task 4: Update Tests (2 hours)

- [ ] Create `tests/repositories/test_bug_repository.py`
- [ ] Update service tests to mock repositories (not cache)
- [ ] Update integration tests (verify API refresh works)
- [ ] Run full test suite, fix any failures

### Task 5: Verify Performance (1 hour)

- [ ] Benchmark `list_tests` (target: ~10ms)
- [ ] Benchmark `get_test_status` (target: ~70ms)
- [ ] Verify no memory leaks
- [ ] Test background sync still works

## Testing

### Unit Tests for BugRepository
```python
# tests/repositories/test_bug_repository.py

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bugs_returns_from_sqlite():
    """Verify get_bugs queries SQLite directly."""
    repo = BugRepository(db_path=":memory:")
    # Seed bugs in test database
    # Query and verify results
    bugs = await repo.get_bugs(test_id=123)
    assert len(bugs) == 3
    assert bugs[0]["status"] == "accepted"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_bugs_upserts_to_sqlite():
    """Verify refresh_bugs fetches from API and updates SQLite."""
    mock_client = AsyncMock()
    mock_client.get.return_value = [{"id": 1, "status": "accepted"}]

    repo = BugRepository(db_path=":memory:", client=mock_client)
    count = await repo.refresh_bugs(test_id=123)

    assert count == 1
    bugs = await repo.get_bugs(test_id=123)
    assert bugs[0]["status"] == "accepted"
```

### Integration Tests
```python
# tests/integration/test_sqlite_first_integration.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_test_status_always_fresh():
    """Verify get_test_status refreshes from API before querying."""
    service = TestService(...)

    # First call
    result1 = await service.get_test_status(test_id=123)

    # API changes data
    # ...

    # Second call (should reflect fresh data)
    result2 = await service.get_test_status(test_id=123)
    assert result2["bugs"]["total"] != result1["bugs"]["total"]
```

## Implementation Notes

### Why Repository Pattern?

**Separation of Concerns:**
- **Repositories:** Data access logic (SQL queries, API fetching)
- **Services:** Business logic (orchestration, aggregation)
- **Tools:** MCP interface (parameter extraction, error handling)

**Testing Benefits:**
- Mock repositories in service tests
- Mock database in repository tests
- No more dual mocking (cache + client)

### Why Delete InMemoryCache?

**Complexity Removed:**
- No TTL management
- No cache invalidation
- No stampede protection
- No stale data issues

**SQLite is Fast Enough:**
- ~10ms for list queries at our scale
- WAL mode supports concurrent reads
- Background sync keeps data fresh

### Data Flow After This Story

**List Operations (Fast):**
```
Tool → Service → Repository → SQLite (~10ms)
```

**Get Operations (Fresh):**
```
Tool → Service → Repository.refresh() → API (fetch) → SQLite (upsert)
                → Repository.get() → SQLite (query)
```

**Background Sync (Transparent):**
```
Lifespan handler → PersistentCache.initial_sync() → SQLite
                → Background refresh (every 300s) → SQLite
```

### Migration Notes

**No User Impact:**
- Background sync populates SQLite on startup
- Tools continue working (same interface)
- Performance improves (8x faster lists)

**Developer Impact:**
- Services now inject repositories (not cache)
- Tests mock repositories (simpler)
- No more TTL configuration

## Success Metrics

- ✅ `BugRepository` created with full CRUD operations
- ✅ `TestRepository` extended with refresh methods
- ✅ In-memory cache deleted (~200 lines)
- ✅ Services refactored to use repositories
- ✅ All 160 tests pass
- ✅ `list_tests`: ~10ms (8x faster than before)
- ✅ `get_test_status`: Always fresh (no stale cache)

## References

- **EPIC-004:** Production-Ready Architecture Rewrite
- **STORY-021:** Local Data Store (PersistentCache + TestRepository)
- **Architecture Docs:**
  - `docs/architecture/wip/DATA-ACCESS-STRATEGY.md` - List vs Get patterns
  - `docs/architecture/wip/FINAL-ARCHITECTURE-PLAN.md` - Repository layer design
- **Existing Code:**
  - `src/testio_mcp/repositories/test_repository.py` - Example repository pattern
  - `src/testio_mcp/persistent_cache.py` - Background sync mechanism

---

**Deliverable:** Repository layer complete, in-memory cache deleted, services refactored, no regressions
