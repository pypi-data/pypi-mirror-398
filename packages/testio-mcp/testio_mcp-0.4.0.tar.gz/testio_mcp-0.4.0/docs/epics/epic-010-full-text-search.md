# testio-mcp - Epic 010: Full-Text Search

**Date:** 2025-11-28
**Project Level:** Quick-Flow (Brownfield)

---

## Epic 010: Full-Text Search

**Slug:** fts-search

### Goal

Enable intuitive discovery of TestIO entities (products, features, tests, bugs) through a unified full-text search MCP tool powered by SQLite FTS5 with BM25 relevance ranking.

**Note:** This epic uses lexical full-text search (SQLite FTS5 + BM25), not vector/embedding-based search. "Semantic" here means users do not need exact string matches (thanks to tokenization, prefix search, and relevance ranking), not that we are doing semantic embeddings.

### Scope

- Bug field denormalization (actual_result, expected_result) to enable rich bug search
- FTS5 virtual table with automatic trigger-based sync
- Unified `search` MCP tool with entity filtering and product scoping

### Success Criteria

- Users can search "borders" and find features/bugs/tests about borders
- Results ranked by relevance (BM25)
- Search scoped to specific entities or products
- Index auto-updates via triggers (no code changes to SyncService)

### Dependencies

- Epic 009 complete (SyncService foundation)
- Epic 008 STORY-054 complete (field denormalization patterns)

---

## Story Map - Epic 010

```
STORY-063: Bug Field Denormalization
    └── Add actual_result, expected_result columns
    └── Backfill from raw_data
    └── Update BugRepository sync
           │
           ▼
STORY-064: FTS5 Infrastructure
    └── FTS5 virtual table migration
    └── Triggers for all 4 entities
    └── SearchRepository
           │
           ▼
STORY-065: Search MCP Tool
    └── SearchService
    └── search_tool.py
    └── Entity/product filtering
```

---

## Stories - Epic 010

### Story 10.1: Bug Field Denormalization

As a developer,
I want bug actual_result and expected_result fields denormalized to columns,
So that they can be indexed for full-text search.

**Acceptance Criteria:**

**Given** the bugs table exists with raw_data JSON
**When** the migration runs
**Then** nullable TEXT columns actual_result and expected_result are added to the bugs table (no default values)

**And** existing rows are backfilled from raw_data using the same JSON path and transformation rules defined in STORY-054 (missing keys or empty values result in NULL after trimming whitespace)

**And** BugRepository extracts these fields on sync for newly created and updated bugs so that the denormalized columns stay in sync with raw_data

**And** Alembic migrations and pytest-alembic checks pass (no drift between ORM model and DDL; baseline migration remains unchanged)

**Prerequisites:** None

**Technical Notes:** Follow STORY-054 pattern for field denormalization + backfill migration (single-path Alembic migration, idempotent backfill for existing databases, no edits to baseline migration); update Bug ORM model to include the new columns and expose them for use in Story 10.2 FTS indexing

**Estimated Effort:** 2 points

---

### Story 10.2: FTS5 Infrastructure

As a developer,
I want an FTS5 virtual table indexing all searchable entities,
So that search queries can be executed with BM25 ranking.

**Acceptance Criteria:**

**Given** products, features, tests, and bugs tables exist
**When** the FTS5 migration runs
**Then** search_index virtual table is created with triggers for INSERT/UPDATE/DELETE on all four base tables

**And** each index row stores entity_type, entity_id, and product_id so that queries can filter by entity type and product scope without additional joins

**And** existing data is populated in the migration so that search returns results for already-synced entities

**Prerequisites:** STORY-063 complete (bug fields available)

**Technical Notes:**

- Single unified FTS5 virtual table search_index with:
  - entity_type TEXT UNINDEXED (one of "product", "feature", "test", "bug")
  - entity_id INTEGER UNINDEXED
  - product_id INTEGER UNINDEXED
  - title TEXT (short, high-signal fields)
  - content TEXT (longer descriptive fields)
- Entity-to-column mapping (source → FTS columns), for example:
  - Product: name → title; description/notes → content
  - Feature: name → title; description/acceptance criteria → content
  - Test: title → title; description/steps → content
  - Bug: title → title; actual_result + "\n" + expected_result + other relevant text → content
- Triggers:
  - AFTER INSERT/UPDATE/DELETE triggers on products, features, tests, and bugs keep search_index in sync using `UPDATE search_index ... WHERE entity_type = ? AND entity_id = ?` for updates (do NOT use DELETE+INSERT) to preserve rowid stability and avoid index fragmentation
  - Triggers ensure exactly one search_index row per (entity_type, entity_id)
- Query behavior:
  - Prefix indexing enabled (e.g., `prefix='2 3'` on title and content) so partial tokens like "bord" can still match "borders"
  - Column weighting via BM25 so that title is weighted higher than content (Title=5.0, Content=1.0)
  - SearchRepository (backed by an FTS5QueryBuilder) can execute FTS5 queries with BM25 ranking
  - Alembic migration is reversible (downgrade drops search_index and associated triggers)

**Estimated Effort:** 3 points

---

### Story 10.3: Search MCP Tool + REST Endpoint

As an MCP user (CSM, PM, QA lead) or REST client,
I want a unified search tool that finds entities by semantic meaning,
So that I can discover features, bugs, and tests without knowing exact names.

**Acceptance Criteria:**

**Given** the FTS5 index exists
**When** I call `search(query="borders")` via MCP or `GET /search?query=borders` via REST
**Then** I receive relevance-ranked results (BM25) from all entity types

**And** I can filter by entities=["features"] (MCP) or entities=feature,bug (REST)

**And** I can filter by product_ids=[598, 601] (MCP) or product_ids=598,601 (REST) to scope search to specific products

**And** Both transports return identical JSON response format for the same inputs (modulo transport-specific envelope fields)

**And** queries shorter than the configured minimum length (e.g., 2–3 characters) return a friendly validation error instead of hitting FTS

**Prerequisites:** STORY-064 complete (FTS5 infrastructure)

**Technical Notes:** SearchService + search_tool.py + REST endpoint; shared Search API contract (see below); `match_mode` ("simple"/"raw"); FTS5 `optimize` maintenance routine; friendly error messages (ToolError pattern with ❌ℹ️💡 for MCP; HTTP 4xx for REST)

**Estimated Effort:** 3 points

---

## Search API Contract (MCP + REST)

The MCP tool and REST endpoint share a single canonical API contract. REST mirrors MCP parameters as query string arguments and returns the same JSON body structure.

### Parameters

**MCP Tool: `search`**

- `query: str` (required)
  - User search text; trimmed; must meet a configurable minimum length (e.g., 2–3 characters)
- `entities: list[str] | None` (optional)
  - Allowed values: `"product"`, `"feature"`, `"test"`, `"bug"`
  - Default: all entity types
- `product_ids: list[int] | None` (optional)
  - Default: all products
- `limit: int` (optional)
  - Default: 20; maximum enforced (e.g., 100) to prevent unbounded result sets
- `match_mode: Literal["simple", "raw"]` (optional)
  - Default: `"simple"`

**REST Endpoint: `GET /search`**

- Mirrors the MCP parameters using query string arguments:
  - `query` (string, required)
  - `entities` (comma-separated list, e.g., `entities=feature,bug`)
  - `product_ids` (comma-separated list of integers, e.g., `product_ids=598,601`)
  - `limit` (integer)
  - `match_mode` (`simple` or `raw`)

### Match Modes

- `match_mode="simple"`:
  - Treats the query primarily as plain text, with escaping/sanitization applied before passing to FTS5
  - Can apply sensible defaults like lowercasing and optional suffix wildcarding (e.g., `"borders"` → `"borders*"`), subject to tuning during implementation
  - Supports common FTS patterns (phrases, simple prefix search) while minimizing the chance of syntax errors from unescaped characters
- `match_mode="raw"`:
  - Passes the query string directly into the FTS5 MATCH clause for power users and internal use
  - Caller is responsible for providing valid FTS syntax; invalid syntax is caught and translated into a friendly error (no raw SQL error leaks)

### Response Shape

Both MCP and REST return the same JSON body structure:

```json
{
  "query": "borders",
  "total": 15,
  "match_mode": "simple",
  "entities": ["feature", "bug"],
  "product_ids": [598],
  "limit": 20,
  "results": [
    {
      "entity_type": "bug",
      "entity_id": 123,
      "product_id": 598,
      "title": "Border disappears on hover",
      "score": 0.87,
      "rank": 1
    }
  ]
}
```

- `score` is a relevance score derived from BM25 (higher is better)
- `rank` is the 1-based position of the result in the sorted list
- Future extensions (e.g., `snippet`/`highlight`) can be added as additional fields on each result without breaking backward compatibility

### Error Handling & Edge Cases

- Invalid `entities` or `match_mode` values:
  - MCP: raise ToolError with ❌ℹ️💡 format
  - REST: return HTTP 400 with a JSON error body that mirrors the ToolError messaging
- Query shorter than the minimum length:
  - MCP/REST: return a validation error explaining the minimum required length
- Invalid FTS5 syntax (especially in `match_mode="raw"` queries):
  - MCP/REST: catch database errors and translate them into friendly validation errors (no raw SQL error messages returned to users)
- FTS infrastructure unavailable (e.g., migrations not run, search_index missing):
  - MCP/REST: return a deterministic error indicating that full-text search is not available until the database is migrated, rather than a low-level SQL error

### Testing Expectations

- Unit tests for SearchService / SearchRepository:
  - Query building (MATCH clauses, filters for entities and product_ids)
  - Ordering and limit handling with BM25-based ranking
- Tool tests for search_tool.py:
  - Parameter validation and wiring to SearchService
  - Error transformations to ToolError (❌ℹ️💡)
- REST endpoint tests:
  - Parameter parsing and mapping to SearchService
  - Response shape parity with MCP for identical inputs

At least one integration test should verify that for the same query/filters, MCP and REST return identical result payloads (ignoring transport-specific wrappers).

---

## Implementation Timeline - Epic 010

**Total Story Points:** 8

**Story Sequence:**
1. STORY-063: Bug Field Denormalization
2. STORY-064: FTS5 Infrastructure
3. STORY-065: Search MCP Tool

---
