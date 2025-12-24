# testio-mcp - Technical Specification: Full-Text Search

**Author:** leoric
**Date:** 2025-11-28
**Project Level:** Quick-Flow (Brownfield)
**Change Type:** New Feature
**Development Context:** Extending existing SQLite local cache with FTS5 search capabilities

---

## Context

### Available Documents

- **CLAUDE.md** - Project architecture, service layer patterns, SQLModel query patterns
- **README.md** - MCP tool reference, CLI commands
- **docs/architecture/ARCHITECTURE.md** - Data flow, component architecture
- **docs/architecture/adrs/** - ADR-011 (Service Layer), ADR-013 (User Story Embedding), ADR-016 (Alembic Migrations), ADR-017 (Sync Strategy)

### Project Stack

| Component | Version | Source |
|-----------|---------|--------|
| Python | 3.12+ | pyproject.toml |
| FastMCP | 2.12.0+ | pyproject.toml |
| SQLModel | 0.0.16 | pyproject.toml |
| SQLite | 3.45+ | System (macOS) |
| Alembic | 1.13.0+ | pyproject.toml |
| aiosqlite | 0.20.0+ | pyproject.toml |
| pytest | 8.4.0+ | pyproject.toml (dev) |

### Existing Codebase Structure

```
src/testio_mcp/
├── models/orm/           # SQLModel ORM models
│   ├── product.py        # Product model (title field)
│   ├── feature.py        # Feature model (title, description, howtofind, user_stories)
│   ├── test.py           # Test model (title, goal, instructions, out_of_scope)
│   └── bug.py            # Bug model (title only - raw_data has actual/expected)
├── repositories/         # Data access layer
│   ├── base_repository.py
│   ├── product_repository.py
│   ├── feature_repository.py
│   ├── test_repository.py
│   └── bug_repository.py
├── services/             # Business logic layer
│   ├── base_service.py
│   └── ...
├── tools/                # MCP tool wrappers
│   ├── list_*.py         # List tools
│   └── *_summary_tool.py # Summary tools
└── database/
    ├── engine.py         # SQLite async engine
    └── cache.py          # PersistentCache class
```

**Key Patterns:**
- Service layer pattern (ADR-011): Tools → Services → Repositories
- SQLModel with async sessions (STORY-062 patterns)
- Alembic migrations with frozen baseline (ADR-016)
- Per-operation session pattern for concurrent operations

---

## The Change

### Problem Statement

The MCP prompt `explore-testio-data` promises discovery capabilities, but no actual search exists. Users cannot find entities by semantic meaning—only by exact field filters (status, product_id, etc.).

**Current limitations:**
1. Cannot search "features related to video mode" unless feature is literally named "Video Mode"
2. No way to find bugs about "login issues" across all tests
3. Listing all entities and manually scanning is the only workaround
4. Context window limits make manual scanning unreliable for large datasets

**Real user scenario:**
> "What features relate to borders?"
> Today: List all features, hope context fits, manually scan
> After this: `search(query="borders", entities=["features"])` → ranked results

### Proposed Solution

Implement SQLite FTS5 (Full-Text Search version 5) with BM25 relevance ranking as a unified `search` MCP tool.

**Why FTS5:**
- Built into SQLite (no external dependencies)
- BM25 relevance ranking out of the box
- Supports phrase search, prefix matching, boolean operators
- Lightweight—virtual table adds minimal storage overhead

**Tool Design:**
```python
@mcp.tool()
async def search(
    query: str,
    entities: list[str] | None = None,     # Default: all
    product_ids: list[int] | None = None,  # Optional scope filter (one or more products)
    limit: int = 20,
    match_mode: str = "simple",           # "simple" (sanitized) or "raw" (FTS5 syntax)
) -> dict:
    """Search across TestIO entities using full-text search."""
```

### Scope

**In Scope:**

1. **Bug Field Denormalization (Story 1)**
   - Add `actual_result`, `expected_result` columns to bugs table
   - Migration to extract from raw_data JSON
   - Update BugRepository to populate on sync

2. **FTS5 Infrastructure (Story 2)**
   - Create FTS5 virtual table indexing: products, features, tests, bugs
   - Alembic migration for FTS5 table + triggers
   - Bugs indexed with all fields (title + actual_result + expected_result) from start
   - Rebuild triggers for INSERT/UPDATE/DELETE sync
   - SearchRepository for FTS queries

3. **Search MCP Tool (Story 3)**
   - Unified `search` tool with entity filtering
   - BM25 relevance ranking
   - Product scope filtering (optional)
   - Result grouping by entity type

**Out of Scope:**

- Fuzzy/typo tolerance (requires trigram extension or Levenshtein—future enhancement)
- Snippet highlighting (nice-to-have, not MVP)
- Cross-entity relationship search (e.g., "bugs in features about video")
- Real-time index updates during sync (triggers handle this)

---

## Implementation Details

### Source Tree Changes

| File | Action | Changes |
|------|--------|---------|
| `alembic/versions/xxxx_add_fts5_search_index.py` | CREATE | FTS5 virtual table + triggers migration |
| `alembic/versions/xxxx_add_bug_result_fields.py` | CREATE | Bug actual/expected_result columns migration |
| `src/testio_mcp/models/orm/bug.py` | MODIFY | Add actual_result, expected_result fields |
| `src/testio_mcp/repositories/search_repository.py` | CREATE | FTS5 query repository |
| `src/testio_mcp/repositories/bug_repository.py` | MODIFY | Extract actual/expected on sync |
| `src/testio_mcp/services/search_service.py` | CREATE | Search business logic |
| `src/testio_mcp/tools/search_tool.py` | CREATE | MCP search tool wrapper |
| `tests/unit/test_search_repository.py` | CREATE | Repository unit tests |
| `tests/unit/test_search_tool.py` | CREATE | Tool unit tests |
| `tests/integration/test_search_integration.py` | CREATE | Integration tests |

### Technical Approach

**FTS5 Virtual Table Design:**

```sql
-- Single unified FTS5 table for all entities
CREATE VIRTUAL TABLE search_index USING fts5(
    entity_type UNINDEXED,  -- Store but don't index (filtering only)
    entity_id UNINDEXED,    -- Store but don't index
    product_id UNINDEXED,   -- Store but don't index
    title,                  -- Indexed (weight 5.0)
    content,                -- Indexed (weight 1.0)
    tokenize='porter unicode61 remove_diacritics 2',  -- Stemming + accent insensitivity
    prefix='2 3'            -- Accelerate prefix queries (2-3 chars)
);
```

**Why single table vs per-entity tables:**
- Simpler unified search across all entities
- Single BM25 ranking across results
- Fewer triggers to maintain
- Entity filtering via WHERE clause

**Trigger Strategy:**

```sql
-- Example for features (similar for other entities)
CREATE TRIGGER features_ai AFTER INSERT ON features BEGIN
    INSERT INTO search_index(entity_type, entity_id, product_id, title, content)
    VALUES (
        'feature',
        NEW.id,
        NEW.product_id,
        NEW.title,
        NEW.title || ' ' || COALESCE(NEW.description, '') || ' ' ||
        COALESCE(NEW.howtofind, '') || ' ' || COALESCE(NEW.user_stories, '')
    );
END;

CREATE TRIGGER features_ad AFTER DELETE ON features BEGIN
    DELETE FROM search_index WHERE entity_type = 'feature' AND entity_id = OLD.id;
END;

CREATE TRIGGER features_au AFTER UPDATE ON features BEGIN
    UPDATE search_index
    SET
        product_id = NEW.product_id,
        title = NEW.title,
        content = NEW.title || ' ' || COALESCE(NEW.description, '') || ' ' ||
                  COALESCE(NEW.howtofind, '') || ' ' || COALESCE(NEW.user_stories, '')
    WHERE entity_type = 'feature' AND entity_id = OLD.id;
END;
```

**Content Concatenation per Entity:**

| Entity | Content Fields |
|--------|----------------|
| Products | `title` |
| Features | `title + description + howtofind + user_stories` |
| Tests | `title + goal + instructions + out_of_scope` |
| Bugs | `title + actual_result + expected_result` |

### Existing Patterns to Follow

**Repository Pattern (base_repository.py):**
```python
class SearchRepository(BaseRepository):
    """FTS5 search repository.

    Uses raw SQL for FTS5 queries (SQLModel doesn't support virtual tables).
    """

    async def search(
        self,
        query: str,
        entities: list[str] | None = None,
        product_ids: list[int] | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        ...
```

**Service Pattern (base_service.py):**
```python
class SearchService(BaseService):
    """Search business logic."""

    async def search(self, query: str, ...) -> dict:
        # Validate inputs
        # Call repository
        # Format results
        ...
```

**Tool Pattern (existing tools):**
```python
@mcp.tool()
async def search(query: str, ..., ctx: Context) -> dict:
    service = get_service(ctx, SearchService)
    try:
        return await service.search(query, ...)
    except InvalidSearchQueryError as e:
        raise ToolError(f"❌ Invalid search query\nℹ️ {e}\n💡 Try simpler terms") from None
```

### Integration Points

1. **Database Layer:**
   - FTS5 virtual table alongside existing ORM tables
   - Raw SQL queries (SQLModel doesn't support FTS5 virtual tables natively)
   - Triggers auto-sync on INSERT/UPDATE/DELETE

2. **Sync Service:**
   - No changes needed—triggers handle index updates automatically
   - Initial migration populates from existing data

3. **MCP Tools:**
   - New `search` tool registered via auto-discovery
   - Follows existing error handling patterns (ToolError with ❌ℹ️💡)

---

## Development Context

### Relevant Existing Code

- `src/testio_mcp/repositories/base_repository.py` - Repository base class pattern
- `src/testio_mcp/services/analytics_service.py:45-80` - Raw SQL query pattern for analytics
- `src/testio_mcp/database/engine.py` - Async engine configuration
- `alembic/versions/0965ad59eafa_baseline_existing_schema.py` - Migration pattern reference

### Dependencies

**Framework/Libraries:**
- SQLite FTS5 (built-in, requires SQLite 3.9.0+)
- aiosqlite 0.20.0 (async SQLite access)
- SQLModel 0.0.16 (ORM, but raw SQL for FTS5)
- Alembic 1.13.0 (migrations)

**Internal Modules:**
- `testio_mcp.database.cache.PersistentCache`
- `testio_mcp.repositories.base_repository.BaseRepository`
- `testio_mcp.services.base_service.BaseService`
- `testio_mcp.utilities.service_helpers.get_service`

### Configuration Changes

None required—FTS5 is built into SQLite.

### Existing Conventions

**Code Style:**
- Ruff formatting (line length 100)
- Type hints everywhere (mypy --strict)
- Docstrings for public methods

**Test Patterns:**
- `tests/unit/` - Mock dependencies, test in isolation
- `tests/integration/` - Real database, real API (where applicable)
- pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`
- Fixtures in `conftest.py`

**File Naming:**
- Repositories: `*_repository.py`
- Services: `*_service.py`
- Tools: `*_tool.py`

---

## Implementation Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Runtime |
| SQLite FTS5 | Built-in | Full-text search |
| aiosqlite | 0.20.0 | Async database access |
| SQLModel | 0.0.16 | ORM (regular tables) |
| Alembic | 1.13.0 | Migrations |
| pytest | 8.4.0 | Testing |
| pytest-asyncio | 0.24.0 | Async test support |

---

## Technical Details

### FTS5 Query Syntax

**Basic search:**
```sql
SELECT entity_type, entity_id, title, bm25(search_index) as score
FROM search_index
WHERE search_index MATCH 'video mode'
ORDER BY score
LIMIT 20;
```

**Phrase search:**
```sql
WHERE search_index MATCH '"video mode"'  -- Exact phrase
```

**Prefix search:**
```sql
WHERE search_index MATCH 'vid*'  -- Matches video, vidmode, etc.
```

**Boolean operators:**
```sql
WHERE search_index MATCH 'video AND mode'
WHERE search_index MATCH 'video OR audio'
WHERE search_index MATCH 'video NOT audio'
```

**Entity filtering:**
```sql
WHERE search_index MATCH 'video' AND entity_type = 'feature'
```

**Product scoping:**
```sql
WHERE search_index MATCH 'video' AND product_id = 598
```

### Ranking Strategy (BM25 + Boosting)

FTS5 includes BM25 relevance ranking via the `bm25()` function. To ensure high-quality results across heterogeneous data (short titles vs. long descriptions):

**1. Column Weighting:**
We will weight matches in the `title` column higher than matches in the `content` column.
- `title` weight: **5.0**
- `content` weight: **1.0**

**Query Syntax:**
```sql
SELECT ..., bm25(search_index, 5.0, 1.0) as score
FROM search_index ...
ORDER BY score
```

**2. Entity Boosting (Future):**
If specific entities (like Products) are consistently outranked by long documents (like Tests), we can apply a multiplier in the query:
```sql
-- Conceptual example
SELECT ..., bm25(...) * (CASE WHEN entity_type='product' THEN 2.0 ELSE 1.0 END) as score
```
*Note: We will start with Column Weighting only and add Entity Boosting only if user feedback indicates a need.*

### Error Handling

| Error Case | Handling |
|------------|----------|
| Invalid FTS5 syntax | Catch exception, return friendly error |
| Empty query | Validate upfront, return empty results |
| No results | Return empty list with metadata |
| Entity type not recognized | Validate against allowed list |

### Performance Considerations

- FTS5 index adds ~10-20% to database size
- Query performance: O(log n) for most queries
- Trigger overhead: negligible for single-record operations
- Bulk sync: triggers fire per-row (acceptable for our data volumes)

### Index Maintenance

FTS5 indexes can become fragmented over time, especially with frequent updates.

**Optimization Strategy:**
- Run `INSERT INTO search_index(search_index) VALUES('optimize')` periodically.
- Trigger this automatically after a full "nuke" sync or major background refresh.
- Expose as a hidden option in `get_server_diagnostics` or a dedicated maintenance method in `SearchService`.

### Bulk Sync Strategy

To avoid trigger overhead during initial migration or full re-syncs:
1. **Initial Migration:** Use `INSERT INTO search_index SELECT ...` for backfill. This is much faster than row-by-row triggers.
2. **Full Sync:** If doing a "nuke" sync, the `DELETE FROM features` will cascade to FTS5 via triggers. For re-insertion, the overhead is acceptable, but we should monitor it.

### PostgreSQL Migration Path

**Note:** SQLite FTS5 and PostgreSQL full-text search have incompatible APIs. If we migrate to PostgreSQL in the future:

| Component | SQLite FTS5 | PostgreSQL | Migration Impact |
|-----------|-------------|------------|------------------|
| Index | Virtual table | GIN index on tsvector | Rewrite migration |
| Query | `MATCH 'term'` | `@@ to_tsquery('term')` | Rewrite queries |
| Ranking | `bm25()` | `ts_rank()` | Different function |
| Phrase | `"exact phrase"` | `<->` operator | Different syntax |

**Mitigation (already in design):**
- All FTS5 SQL isolated in `SearchRepository`
- Services and tools use repository interface only
- Migration scope: rewrite SearchRepository internals (~100-200 lines) + new Alembic migration
- No changes to SearchService, search_tool, or tests (mocked at repository level)

### Design Principles (DRY/SOLID)

**Single Responsibility:**
- `SearchRepository`: FTS5 query execution only (database concern)
- `SearchService`: Validation, formatting, orchestration (business logic)
- `search_tool`: MCP protocol translation, error formatting (transport)

**Open/Closed (extensibility without modification):**
- New entity types: Add to `SEARCHABLE_ENTITIES` constant + trigger in migration
- New search features (fuzzy, highlighting): Extend SearchRepository, service unchanged

**Dependency Inversion:**
- SearchService depends on repository interface, not FTS5 implementation
- Enables PostgreSQL swap or mock injection for testing

**DRY - Centralized Constants:**
```python
# src/testio_mcp/schemas/constants.py
SEARCHABLE_ENTITIES = ("product", "feature", "test", "bug")

# Entity → indexed fields mapping (single source of truth)
SEARCH_CONTENT_FIELDS: dict[str, tuple[str, ...]] = {
    "product": ("title",),
    "feature": ("title", "description", "howtofind", "user_stories"),
    "test": ("title", "goal", "instructions", "out_of_scope"),
    "bug": ("title", "actual_result", "expected_result"),
}
```

**DRY - Query Builder Pattern:**
```python
class FTS5QueryBuilder:
    """Builds FTS5 queries from parameters. Single place for SQL generation."""

    def build_search_query(
        self,
        entities: list[str] | None,
        product_id: int | None,
        limit: int,
    ) -> tuple[str, list[Any]]:
        """Returns (sql, params) tuple."""
        ...
```

This keeps raw SQL in one place, making PostgreSQL migration a matter of swapping `FTS5QueryBuilder` for `PostgresQueryBuilder`.

---

## Development Setup

```bash
# Standard setup (already in CLAUDE.md)
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run migrations (after creating them)
uv run alembic upgrade head

# Verify FTS5 available
sqlite3 ~/.testio-mcp/cache.db "SELECT sqlite_version();"
# Should be 3.9.0+ for FTS5 support
```

---

## Implementation Guide

### Setup Steps

1. Create feature branch: `git checkout -b feat/fts5-search`
2. Verify SQLite version supports FTS5: `sqlite3 --version` (3.9.0+)
3. Review existing migrations in `alembic/versions/`

### Implementation Steps

**Story 1: Bug Field Denormalization**
1. Add actual_result, expected_result to Bug ORM model
2. Create Alembic migration for new columns + backfill from raw_data
3. Update BugRepository.sync_bugs() to extract fields on sync
4. Write migration and repository tests

**Story 2: FTS5 Infrastructure**
1. Create Alembic migration for FTS5 virtual table
2. Add triggers for products, features, tests, bugs (bugs include all 3 fields)
3. Populate index from existing data in migration
4. Create SearchRepository with basic query method
5. Write unit tests for repository

**Story 3: Search MCP Tool**
1. Create SearchService with query validation
2. Create search_tool.py with MCP registration
3. Handle entity filtering and product scoping
4. Format results with entity metadata
5. Write tool unit tests and integration tests

### Testing Strategy

**Unit Tests:**
- SearchRepository: Mock database, test query building
- SearchService: Mock repository, test business logic
- search_tool: Mock service, test error transformation

**Integration Tests:**
- Create test database with FTS5
- Insert test data via ORM
- Verify search returns correct results
- Test trigger updates on INSERT/UPDATE/DELETE

### Acceptance Criteria

1. **Bug Field Denormalization:**
   - [ ] actual_result, expected_result columns added to bugs table
   - [ ] BugRepository extracts fields from raw_data on sync
   - [ ] Existing bugs backfilled via migration

2. **FTS5 Infrastructure:**
   - [ ] FTS5 virtual table created via Alembic migration
   - [ ] Triggers sync data on INSERT/UPDATE/DELETE for all 4 entities
   - [ ] Bugs indexed with title + actual_result + expected_result
   - [ ] Existing data populated in migration upgrade
   - [ ] Migration is reversible (downgrade drops FTS5)

3. **Search MCP Tool:**
   - [ ] `search(query="borders")` returns ranked results
   - [ ] `search(query="borders", entities=["features"])` filters to features only
   - [ ] `search(query="borders", product_ids=[598, 601])` scopes to specific products
   - [ ] Empty query returns validation error
   - [ ] Invalid FTS5 syntax returns friendly error
   - [ ] Results include entity_type, entity_id, title, score

---

## Developer Resources

### File Paths Reference

**New Files:**
- `alembic/versions/xxxx_add_fts5_search_index.py`
- `alembic/versions/xxxx_add_bug_result_fields.py`
- `src/testio_mcp/repositories/search_repository.py`
- `src/testio_mcp/services/search_service.py`
- `src/testio_mcp/tools/search_tool.py`
- `tests/unit/test_search_repository.py`
- `tests/unit/test_search_tool.py`
- `tests/integration/test_search_integration.py`

**Modified Files:**
- `src/testio_mcp/models/orm/bug.py` - Add actual_result, expected_result
- `src/testio_mcp/repositories/bug_repository.py` - Extract fields on sync

### Key Code Locations

- Repository base pattern: `src/testio_mcp/repositories/base_repository.py:1-50`
- Service base pattern: `src/testio_mcp/services/base_service.py:1-80`
- Tool pattern: `src/testio_mcp/tools/list_features_tool.py:1-40`
- Raw SQL in async context: `src/testio_mcp/services/analytics_service.py:45-80`

### Testing Locations

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Fixtures: `tests/conftest.py`

### Documentation to Update

- `README.md` - Add search tool to MCP Tools section
- `CLAUDE.md` - Add search tool to Available MCP Tools list
- `CHANGELOG.md` - Document new feature

---

## UX/UI Considerations

No UI/UX impact - backend MCP tool only.

---

## Testing Approach

**Test Framework:** pytest 8.4.0 with pytest-asyncio 0.24.0

**Unit Tests (SearchRepository):**
```python
@pytest.mark.unit
async def test_search_returns_ranked_results():
    # Mock async session with raw SQL execution
    ...

@pytest.mark.unit
async def test_search_filters_by_entity_type():
    ...

@pytest.mark.unit
async def test_search_handles_invalid_fts5_syntax():
    ...
```

**Integration Tests:**
```python
@pytest.mark.integration
async def test_search_end_to_end(cache_with_test_data):
    # Insert test data via ORM
    # Call search tool
    # Verify results
    ...

@pytest.mark.integration
async def test_triggers_update_index_on_insert(cache):
    # Insert feature via ORM
    # Search for feature
    # Verify found
    ...
```

---

## Deployment Strategy

### Deployment Steps

1. Merge to main branch
2. CI runs migrations in test environment
3. Release via `uvx testio-mcp` (auto-runs migrations)
4. Users run `uvx testio-mcp sync` to populate index

### Rollback Plan

1. `uv run alembic downgrade -1` (or -2 for both migrations)
2. FTS5 table and triggers dropped
3. No data loss (source tables unchanged)

### Monitoring

- Check search query performance via `get_sync_history`
- Monitor database size growth
- Log slow FTS5 queries (>100ms)
