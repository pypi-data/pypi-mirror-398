# Epic-008: MCP Layer Optimization

## 1. Overview

**Goal:** Optimize the MCP tool layer for token efficiency, consistency, and usability while adding REST API parity for all tools.

**Motivation:**

- **Token Efficiency:** Current tool schemas consume ~12.8k tokens (Claude Code `/context`). Target: ~6.6k tokens (49% reduction).
- **Consistent Taxonomy:** Establish clear discover -> summarize -> analyze pattern across all tools.
- **Richer Metadata:** List tools should return counts and meaningful activity timestamps.
- **Standardized Patterns:** Consistent pagination, sorting, and filtering across all tools.
- **REST Parity:** Enable non-MCP clients (dashboards, curl, integrations) to access all functionality.

**Key Decisions (from planning session 2025-11-26):**

- **Tool Taxonomy:** Discover (`list_*`) + Summarize (`get_*_summary`) + Analyze (`query_metrics`, `get_product_quality_report`)
- **EBR Tool:** Keep for server-side batch efficiency, rename to `get_product_quality_report`
- **Computed Fields:** Use subqueries (not denormalized columns) for counts - always accurate with read-through cache
- **Schema Changes:** Add `product_type` column to products table (extract from JSON)
- **Sorting:** Add `sort_by`, `sort_order` to all `list_*` tools; add `limit` to `query_metrics`
- **Renaming Strategy:** Clean break (no aliases) to avoid context bloat

**External Input:**

- Architecture review by Codex CLI (hybrid tool strategy, composition patterns)
- Design review by Gemini CLI (atomic + composite tools, schema optimization)
- **Progressive Disclosure Research:** Verified alignment with "Discover → Summarize → Analyze" taxonomy (Nov 27)

## 2. Scope

### Tools to Modify

| Tool | Change |
|------|--------|
| `get_test_status` | Rename to `get_test_summary`, add quality metrics |
| `generate_ebr_report` | Rename to `get_product_quality_report` |
| `list_products` | Add pagination, sorting, computed counts (test_count, bug_count, feature_count) |
| `list_tests` | Add sorting |
| `list_features` | Add sorting, computed counts (test_count, bug_count), `has_user_stories` filter |
| `list_users` | Add sorting, fix `last_activity` (semantic timestamps) |
| `list_user_stories` | Remove (redundant with features) |
| `query_metrics` | Add `limit` parameter |
| `get_analytics_capabilities` | Move to disabled-by-default, create MCP prompt alternative |
| `health_check`, `get_database_stats`, `get_sync_history` | Consolidate into `get_server_diagnostics` |
| `get_problematic_tests` | Slim description |
| All tools | Slim descriptions, flatten schemas |

### New Tools

| Tool | Purpose |
|------|---------|
| `get_product_summary` | Product overview with test/bug/feature counts, recent activity |
| `get_feature_summary` | Feature details with test coverage, bug attribution |
| `get_user_summary` | User profile with activity metrics |
| `get_server_diagnostics` | Consolidated server health, database stats, and sync status |

### Schema Changes

| Table | Change |
|-------|--------|
| `products` | Add `product_type` column (extracted from JSON) |

### Computed Fields (via Subqueries)

| Entity | Computed Fields |
|--------|-----------------|
| Products | `test_count`, `bug_count`, `feature_count` |
| Features | `test_count`, `bug_count` |
| Users | `last_activity` (customer: last test created/submitted; tester: last bug reported) |

**Note:** Computed via subqueries, not denormalized columns. This ensures accuracy with read-through caching (ADR-017). Performance acceptable at current scale (tens of thousands of records).

### Tool Cache Strategy

**Principle:** Cache strategy determined by API capability - if single-entity endpoint exists, use API-first; otherwise rely on background sync.

| Tool | Data Source | Refresh Trigger | Response Metadata |
|------|-------------|-----------------|-------------------|
| **Discover** (`list_*`) | SQLite | Background sync | `data_as_of` (top-level) |
| `get_test_summary` | **API** | Always fresh (`GET /tests/{id}`) | Fresh data |
| `get_product_summary` | SQLite | Background sync | `data_as_of` (top-level) |
| `get_feature_summary` | SQLite | Background sync | `data_as_of` (top-level) |
| `get_user_summary` | SQLite | Background sync | `data_as_of` (top-level) |
| **Analyze** (`query_metrics`) | SQLite + API | On-demand (TTL check) | Warnings list |
| **Analyze** (`get_product_quality_report`) | SQLite + API | On-demand (TTL check) | Warnings list |

**Key Changes:**

- Remove `force_refresh_bugs` from EBR (Epic-009 STORY-067, same release as `sync_data`)
- Add top-level `data_as_of` timestamp to discover/summarize tools
- User-controlled refresh via new `sync_data` MCP tool (Epic-009)

**Dependency:** `force_refresh_bugs` removal requires `sync_data` tool (same Epic-009 release).

## 3. Tool Taxonomy (Target State)

```
DISCOVER (list_*)              SUMMARIZE (get_*_summary)        ANALYZE
--------------------           -------------------------        -------
list_products            <->   get_product_summary              query_metrics
list_tests               <->   get_test_summary                 get_product_quality_report
list_features            <->   get_feature_summary
list_users               <->   get_user_summary

OPERATIONAL
-----------
get_server_diagnostics (consolidated from health_check, get_database_stats, get_sync_history)
get_problematic_tests
get_analytics_capabilities (disabled by default)
```

## 4. Standardized Parameters

### Pagination (all `list_*` tools)

```python
page: int = 1                    # Page number (1-indexed)
per_page: int = 50               # Items per page (from settings)
offset: int = 0                  # Optional starting offset
```

### Sorting (all `list_*` tools)

```python
sort_by: str | None = None       # Field to sort by (entity-specific)
sort_order: "asc" | "desc" = "desc"
```

### Sort Fields by Entity

| Tool | Default `sort_by` | Available Fields | Filters |
|------|-------------------|------------------|---------|
| `list_products` | `title` | `title`, `product_type`, `last_synced` | `product_type` |
| `list_tests` | `end_at` | `start_at`, `end_at`, `status`, `title` | `status`, `testing_type` |
| `list_features` | `title` | `title`, `test_count`*, `bug_count`*, `last_synced` | `has_user_stories` |
| `list_users` | `username` | `username`, `user_type`, `last_activity`*, `first_seen` | `user_type` |

*\* = computed via subquery*

### Analytics Limit (query_metrics)

```python
limit: int | None = None         # Max rows to return (for "top N" queries)
```

## 5. Stories

### STORY-053: Tool Inventory Audit & Taxonomy Alignment

**User Story:**
As a developer maintaining the MCP server,
I want tools to follow a consistent naming taxonomy,
So that users can predict tool names and understand their purpose.

**Acceptance Criteria:**

1. [ ] Rename `get_test_status` -> `get_test_summary`
   - Update tool file name: `test_status_tool.py` -> `test_summary_tool.py`
   - Update function name and decorator
   - Update all imports and references
   - **Constraint:** Do NOT maintain backward compatibility (clean break)

2. [ ] Rename `generate_ebr_report` -> `get_product_quality_report`
   - Update tool file name: `generate_ebr_report_tool.py` -> `product_quality_report_tool.py`
   - Update function name and decorator
   - Update tool description (remove "EBR" jargon)
   - Update all imports and references
   - **Constraint:** Do NOT maintain backward compatibility

3. [ ] Remove `list_user_stories` tool (redundant)
   - Delete `src/testio_mcp/tools/list_user_stories_tool.py`
   - Remove any imports/references to `list_user_stories`
   - Update CLAUDE.md: remove from tool list, note user stories via `list_features`
   - Verify `list_features` returns embedded user stories (no functionality loss)

4. [ ] Move `get_analytics_capabilities` to disabled-by-default
   - Add to `TESTIO_DISABLED_TOOLS` default list in config
   - Document how to enable if needed
   - Create MCP prompt as alternative (STORY-059)

5. [ ] Update all tool descriptions for consistency
   - Follow pattern: "Verb + object + purpose"
   - Remove redundant examples from descriptions (move to prompts)

6. [ ] Update REST API routes to match new tool names
   - `/api/test/{id}/status` -> `/api/test/{id}/summary`
   - `/api/products/{id}/ebr` -> `/api/products/{id}/quality-report`

7. [ ] Update CLAUDE.md with new tool names

8. [ ] All tests pass after renaming

**Prerequisites:** None

---

### STORY-054: Schema Migration - Normalize Key Fields

**User Story:**
As a developer optimizing queries,
I want key fields extracted from JSON into proper columns,
So that filtering, sorting, and indexing is efficient.

**Acceptance Criteria:**

**Part A: Add product_type column (products table)**

1. [ ] Create Alembic migration to add `product_type` column
   - Column: `product_type VARCHAR(50)`
   - Nullable: YES (for existing rows before backfill)
   - Index: `ix_products_product_type`

2. [ ] Backfill existing rows from JSON
   ```sql
   UPDATE products SET product_type = json_extract(data, '$.type')
   WHERE json_valid(data);
   ```

3. [ ] Update `ProductRepository.upsert_product()` to extract and store `product_type`
   - Extract from API response: `product_data.get("type")`
   - Store in column during upsert

4. [ ] Update `Product` ORM model with `product_type` field

5. [ ] Update `list_products` tool to use column for filtering (instead of JSON)

**Part B: Add title and testing_type columns (tests table)**

6. [ ] Create Alembic migration to add columns:
   - `title VARCHAR(500)` - Test title for display/search/sorting
   - `testing_type VARCHAR(50)` - Test type (coverage, focused, rapid)
   - Index: `ix_tests_title` (for search)
   - Index: `ix_tests_testing_type` (for filtering)

7. [ ] Backfill existing rows from JSON
   ```sql
   UPDATE tests SET title = json_extract(data, '$.title')
   WHERE json_valid(data);
   UPDATE tests SET testing_type = json_extract(data, '$.testing_type')
   WHERE json_valid(data);
   ```

8. [ ] Update `TestRepository` to extract and store these fields during upsert
   - Extract: `test_data.get("title")`, `test_data.get("testing_type")`

9. [ ] Update `Test` ORM model with `title` and `testing_type` fields

10. [ ] Update `list_tests` tool:
    - Add `title` to available sort fields
    - Add `testing_type` filter parameter
    - Update sort fields: `start_at`, `end_at`, `status`, `title`

11. [ ] Consider adding `testing_type` as analytics dimension (future)

**Part C: Drop tests.created_at column (unused)**

12. [ ] Verify `created_at` is NULL in all rows (confirmed: 724 tests, 0 populated)
    - Data not provided by TestIO API

13. [ ] Create Alembic migration to drop `created_at` column from tests table
    - Use `batch_alter_table` for SQLite compatibility
    - Drop index `ix_tests_created_at` first

14. [ ] Remove `created_at` field from `Test` ORM model
    - File: `src/testio_mcp/models/orm/test.py`

15. [ ] Remove any code that writes to `created_at`
    - Search: `grep -r "created_at" src/testio_mcp/`
    - Update `TestRepository` if needed

**Part D: Validation**

16. [ ] Migration tested on fresh and existing databases

17. [ ] Type checking passes: `mypy src/testio_mcp/models/orm/ --strict`

18. [ ] All tests pass after schema changes

**Data Analysis (for reference):**

```
testing_type distribution:
- coverage: 340 tests (47%)
- focused:  203 tests (28%)
- rapid:    181 tests (25%)
```

**Prerequisites:** None

---

### STORY-055: Standardize Pagination & Sorting

**User Story:**
As an AI agent querying data,
I want consistent pagination and sorting across all list tools,
So that I can predictably navigate and order results.

**Progressive Disclosure Goal:**
- **Slim Response Models:** Return ONLY essential fields in list tools:
  - `list_products`: `id`, `title`, `product_type`, `counts`
  - `list_tests`: `id`, `title`, `status`, `testing_type`, `counts`
- **Rationale:** Force agents to use `get_*_summary` for details (Option B).

**Acceptance Criteria:**

1. [ ] Add `sort_by`, `sort_order` parameters to `list_products`
   - Available fields: `title`, `product_type`, `last_synced`
   - Default: `sort_by="title"`, `sort_order="asc"`

2. [ ] Add `sort_by`, `sort_order` parameters to `list_tests`
   - Available fields: `start_at`, `end_at`, `status`, `title`
   - Default: `sort_by="end_at"`, `sort_order="desc"` (shows recent/active tests first)
   - Note: `title` added in STORY-056; `created_at` removed (never populated by API)
   - Add `testing_type` filter parameter (coverage, focused, rapid)

3. [ ] Add `sort_by`, `sort_order` parameters to `list_features`
   - Available fields: `title`, `test_count`, `bug_count`, `last_synced`
   - Default: `sort_by="title"`, `sort_order="asc"`
   - `test_count`, `bug_count` computed via subquery when used for sorting

4. [ ] Add `sort_by`, `sort_order` parameters to `list_users`
   - Available fields: `username`, `user_type`, `last_activity`, `first_seen`
   - Default: `sort_by="username"`, `sort_order="asc"`
   - `last_activity` computed via subquery when used for sorting

5. [ ] Add pagination to `list_products`
   - Add `page`, `per_page`, `offset` parameters
   - Match pattern from other list tools

6. [ ] Add `limit` parameter to `query_metrics`
   - Optional parameter, default: None (unlimited up to 1000 row cap)
   - Enables "top N" queries elegantly
   - Example: `query_metrics(metrics=["bug_count"], dimensions=["feature"], limit=5)`

7. [ ] Repository layer: Implement sorting with computed subqueries
   - `FeatureRepository.query_features()` - Support `test_count`, `bug_count` sort
   - `UserRepository.query_users()` - Support `last_activity` sort
   - Only compute subquery when sorting by computed field (optimization)

8. [ ] Unit tests for sorting by all available fields

9. [ ] Integration tests for pagination + sorting combined

**Prerequisites:** STORY-054 (Schema Migration)

---

### STORY-056: Schema Token Optimization

**User Story:**
As an MCP server operator,
I want tool schemas to use fewer tokens,
So that more context is available for actual queries and responses.

**Acceptance Criteria:**

1. [x] Audit all tool schemas for token usage
   - Baseline measurement script: `scripts/measure_tool_tokens.py`
   - Claude Code `/context` baseline: `scripts/token_baseline_2025-11-26.txt`
   - **Baseline: ~12,840 tokens** (Claude Code `/context`)

2. [ ] Slim `generate_ebr_report` (now `get_product_quality_report`) schema
   - Remove verbose examples from Field definitions
   - Shorten descriptions (remove filler words)
   - Flatten nested output models where possible
   - Target: 1,700 → ~1,000 tokens (41% reduction)

3. [ ] Slim `query_metrics` schema
   - Shorten dimension/metric descriptions
   - Move detailed documentation to MCP prompt
   - Target: 2,100 → ~1,500 tokens (29% reduction)

4. [ ] Slim `list_tests` schema
   - Target: 1,100 → ~800 tokens (27% reduction)

5. [ ] Slim `get_analytics_capabilities` schema
   - Target: 1,100 → ~700 tokens (36% reduction)

6. [ ] Review and slim all other tool schemas
   - Apply consistent description style
   - Remove redundant `json_schema_extra` examples

7. [ ] Total token reduction measured and documented
   - Target: ~12,840 → ~6,600 total (49% reduction)

8. [ ] All tools still function correctly after slimming

9. [ ] LLM usability validated (tools still discoverable and understandable)

**Prerequisites:** STORY-053 (renames complete)

---

### STORY-057: Add Summary Tools

**User Story:**
As an AI agent exploring data,
I want summary tools for each entity type,
So that I can get comprehensive details about a single product, feature, or user.

**Cache Strategy Note:**

- `get_test_summary`: API-first (always fresh via `GET /tests/{id}`)
- `get_product_summary`, `get_feature_summary`, `get_user_summary`: SQLite only (no single-entity API endpoints)
- All include top-level `data_as_of` timestamp for staleness visibility

**Acceptance Criteria:**

1. [ ] Create `get_product_summary` tool
   - Input: `product_id: int`
   - Output:
     - Product metadata (id, title, type, description)
     - `test_count` (computed)
     - `bug_count` (computed)
     - `feature_count` (computed)
     - `last_synced` timestamp
     - **Excluded:** Recent activity (prevents context bloat)

2. [ ] Create `get_feature_summary` tool
   - Input: `feature_id: int`
   - Output:
     - Feature metadata (id, title, description, howtofind)
     - User stories (embedded)
     - `test_count` (computed via test_features)
     - `bug_count` (computed via bugs.test_feature_id)
     - Associated product info
     - **Excluded:** Recent bugs (prevents context bloat)

3. [ ] Create `get_user_summary` tool
   - Input: `user_id: int`
   - Output:
     - User metadata (id, username, type)
     - For customers:
       - `tests_created_count`
       - `tests_submitted_count`
       - `last_activity` (most recent test created/submitted)
     - For testers:
       - `bugs_reported_count`
       - `last_activity` (most recent bug reported)
     - **Excluded:** Recent activity (prevents context bloat)

4. [ ] Enhance `get_test_summary` (renamed from `get_test_status`)
   - Add quality metrics:
     - `bug_count`
     - `bugs_by_severity` (critical, high, medium, low)
     - `acceptance_rate` (if bugs exist)
   - Keep existing fields (test metadata, activity, assignments)
   - Add new rich text fields (from Story 054):
     - `goal`
     - `instructions`
     - `out_of_scope`
   - Add configuration flags:
     - `enable_low`, `enable_high`, `enable_critical`
     - `testing_type`

5. [ ] Service layer: Extend existing services (Domain-Driven Design)
   - `ProductService.get_product_summary()`
   - `FeatureService.get_feature_summary()`
   - `UserService.get_user_summary()`
   - `TestService.get_test_summary()` (extend existing)
   - **Decision:** Do NOT create a monolithic `SummaryService` to avoid high coupling.

6. [ ] Unit tests for all summary methods

7. [ ] Integration tests for summary tools

8. [ ] Schema tokens measured (target: ~500-600 tokens each)

**Prerequisites:** STORY-053 (taxonomy alignment)

---

### STORY-058: Enrich List Tools with Metadata

**User Story:**
I want list tools to return richer metadata,
So that I can understand data volume and activity without additional queries.

**Rationale:**
- `test_count`, `bug_count`, `feature_count` provide essential **Information Scent**.
- Agents need these metrics to decide which entities to explore further.

**Implementation Note (2025-11-28):**
Original STORY-055 implementation computed `test_count`/`bug_count` subqueries **only when sorting by those fields** (optimization to avoid cost when not needed). Commit `6802f09` changed this pattern to **always compute and return counts** for `list_features`, effectively completing AC #2a-2b early. This means STORY-058 should focus on remaining work only.

**Acceptance Criteria:**

1. [ ] Enrich `list_products` response
   - Add `test_count` per product (computed subquery)
   - Add `bug_count` per product (computed subquery)
   - Add `feature_count` per product (computed subquery)

2. [x] ~~Enrich `list_features` response~~ **COMPLETED EARLY (commit 6802f09)**
   - ~~Add `test_count` per feature (via test_features)~~ ✅ **DONE**
   - ~~Add `bug_count` per feature (via bugs.test_feature_id)~~ ✅ **DONE**
   - [ ] Add `has_user_stories` filter parameter (REMAINING WORK)
     - When true: only return features with user_story_count > 0
     - When false/None: return all features

3. [ ] Fix `list_users` timestamps
   - Replace `first_seen`/`last_seen` (cache-based) with meaningful fields:
   - For customer users:
     - `last_activity`: MAX(tests.end_at) WHERE created_by_user_id = user.id OR submitted_by_user_id = user.id
     - Note: Using `end_at` since `created_at` is dropped in STORY-055 (never populated by API)
   - For tester users:
     - `last_activity`: MAX(bugs.created_at) WHERE reported_by_user_id = user.id
   - Keep `first_seen` for reference but document it's cache-based

4. [ ] Repository layer: Implement computed fields
   - [ ] `ProductRepository.query_products()` - Add count subqueries
   - [x] ~~`FeatureRepository.query_features()` - Add count subqueries~~ ✅ **DONE (commit 6802f09)**
   - [ ] `UserRepository.query_users()` - Add last_activity subquery

5. [ ] Performance validation
   - Test with production-scale data (thousands of records)
   - Verify query time < 500ms for typical queries
   - Document performance characteristics

6. [ ] Unit tests for enriched responses

7. [ ] Update tool descriptions to document new fields

**Prerequisites:** STORY-055 (sorting infrastructure)

---

### STORY-059: MCP Prompts for Workflows

**User Story:**
As an AI agent using the MCP server,
I want MCP prompts that guide complex workflows,
So that I can perform multi-step operations without tool schema bloat.

**Acceptance Criteria:**

1. [ ] Create MCP prompt: `quality-report-guide`
   - Explains how to generate quality reports
   - Documents `get_product_quality_report` parameters
   - Provides example queries for common scenarios
   - Replaces verbose tool description

2. [ ] Create MCP prompt: `analytics-guide`
   - Documents all available dimensions and metrics
   - Mirrors `get_analytics_capabilities` output
   - Provides example queries (replaces examples in tool schema)
   - Explains filters, date ranges, sorting

3. [ ] Create MCP prompt: `data-exploration-guide`
   - Documents discover -> summarize -> analyze workflow
   - Shows how to navigate from list -> summary -> detail
   - Provides common exploration patterns

4. [ ] Prompts registered in server.py

5. [ ] Prompts accessible via MCP protocol

6. [ ] Documentation updated with prompt usage examples

**Prerequisites:** STORY-053 (taxonomy finalized)

---

### STORY-060: Consolidate Diagnostic Tools

**User Story:**
As an MCP server operator,
I want a single diagnostic tool instead of multiple fragmented tools,
So that I can check server health with one call and reduce tool schema overhead.

**Context:**
Current diagnostic tools consume ~2,625 tokens across 4 tools:

- `health_check`: 579 tokens
- `get_database_stats`: 635 tokens
- `get_sync_history`: 722 tokens
- `get_problematic_tests`: 689 tokens

Consolidating the first 3 into `get_server_diagnostics` saves ~1,200 tokens (46% reduction for diagnostic tools).

**Acceptance Criteria:**

1. [ ] Create `get_server_diagnostics` tool
   - Consolidates: `health_check`, `get_database_stats`, `get_sync_history`
   - Input parameters:
     - `include_sync_events: bool = False` - Include recent sync event history
     - `sync_event_limit: int = 5` - Max sync events (default: 5, max: 20)
   - Output structure:
     ```python
     class ServerDiagnostics(BaseModel):
         api: ApiStatus           # connected, latency_ms, product_count
         database: DatabaseStatus # size_mb, path, test_count, product_count, feature_count, bug_count
         sync: SyncStatus         # last_sync, last_sync_duration_seconds, success_rate_24h, circuit_breaker_active
         storage: StorageRange    # oldest_test_date, newest_test_date
         events: list[SyncEvent] | None  # Only if include_sync_events=True
     ```

2. [ ] Create supporting Pydantic models
   - `ApiStatus`: connected, latency_ms, product_count
   - `DatabaseStatus`: size_mb, path, test_count, product_count, feature_count, bug_count
   - `SyncStatus`: last_sync, last_sync_duration_seconds, success_rate_24h, syncs_completed_24h, syncs_failed_24h, circuit_breaker_active
   - `StorageRange`: oldest_test_date, newest_test_date
   - `SyncEvent`: started_at, completed_at, status, duration_seconds, tests_synced, error

3. [ ] Deprecate old tools
   - Add deprecation warning to `health_check` description
   - Add deprecation warning to `get_database_stats` description
   - Add deprecation warning to `get_sync_history` description
   - Log warning when deprecated tools are called
   - Plan removal in future epic

4. [ ] Keep `get_problematic_tests` separate
   - Niche use case (debugging failed syncs, filing support tickets)
   - Slim description to reduce tokens (~689 -> ~500 tokens)

5. [ ] Service layer: Create `DiagnosticsService`
   - `get_server_diagnostics()` - Orchestrates all diagnostic data
   - Reuses existing service methods where possible

6. [ ] Unit tests for `DiagnosticsService`

7. [ ] Integration tests for `get_server_diagnostics`

8. [ ] Token reduction measured
   - Target: ~2,625 -> ~1,400 tokens (~1,200 saved, 46% reduction)

**Token Budget:**

| Before | Tokens | After | Tokens |
|--------|--------|-------|--------|
| `health_check` | 579 | `get_server_diagnostics` | ~900 |
| `get_database_stats` | 635 | | |
| `get_sync_history` | 722 | | |
| `get_problematic_tests` | 689 | `get_problematic_tests` | ~500 |
| **Total** | **2,625** | **Total** | **~1,400** |

**Prerequisites:** None

---

### STORY-061: REST API Parity

**User Story:**
As a developer building integrations,
I want REST endpoints for all MCP tools,
So that I can access TestIO data from non-MCP clients.

**Acceptance Criteria:**

1. [ ] Define scope: active tools only
   - Exclude removed tools (`list_user_stories`)
   - Exclude disabled-by-default tools (`get_analytics_capabilities` unless enabled)
   - Parity applies to: discover (`list_*`), summarize (`get_*_summary`), analyze, operational

2. [ ] Audit existing REST endpoints vs active MCP tools
   - Document gaps (active tools without REST endpoints)

3. [ ] Add REST endpoints for summary tools
   - `GET /api/products/{id}/summary`
   - `GET /api/features/{id}/summary`
   - `GET /api/users/{id}/summary`
   - `GET /api/tests/{id}/summary`

4. [ ] Add REST endpoint for quality report
   - `GET /api/products/{id}/quality-report`
   - Query params match tool parameters

5. [ ] Add REST endpoints for analytics
   - `POST /api/analytics/query` (query_metrics)
   - `GET /api/analytics/capabilities`

6. [ ] Add REST endpoints for operational tools
   - `GET /api/diagnostics` (consolidated: health, database, sync status)
   - `GET /api/diagnostics?include_sync_events=true` (with sync history)
   - `GET /api/sync/problematic` (kept separate)

7. [ ] All REST endpoints follow consistent patterns
   - Response format matches MCP tool output
   - Error format matches MCP ToolError pattern

8. [ ] OpenAPI documentation generated
   - All endpoints documented
   - Request/response schemas included

9. [ ] Integration tests for all REST endpoints

**Prerequisites:** STORY-057 (summary tools exist), STORY-060 (diagnostic tools consolidated)

---

## 6. Success Criteria

**Token Efficiency:**

- Total tool schema tokens reduced from ~12.8k to ~6.6k (49% reduction)
- `generate_ebr_report` → `get_product_quality_report` < 1.0k tokens (from 1.7k)
- Diagnostic tools consolidated from 4 to 2 (< 500 total from 1.9k)

**Consistency:**

- All `list_*` tools support `sort_by`, `sort_order` parameters
- All `list_*` tools support `page`, `per_page`, `offset` parameters
- All entities have both `list_*` and `get_*_summary` tools
- Tool naming follows discover -> summarize -> analyze taxonomy

**Functionality:**

- `list_products` returns test_count, bug_count, feature_count per product
- `list_features` supports `has_user_stories` filter
- `list_users` returns meaningful `last_activity` timestamps
- `query_metrics` supports `limit` parameter for "top N" queries

**REST Parity:**

- 1:1 REST endpoints for all MCP tools
- OpenAPI documentation complete

## 7. Token Budget

**Baseline (2025-11-26):** ~12,840 tokens (Claude Code `/context` report)

| Tool | Baseline | Target | Savings |
|------|----------|--------|---------|
| `query_metrics` | 2,100 | 1,500 | 600 |
| `generate_ebr_report` | 1,700 | 1,000 | 700 |
| `list_tests` | 1,100 | 800 | 300 |
| `get_analytics_capabilities` | 1,100 | 700 | 400 |
| `list_users` | 956 | 600 | 356 |
| `list_user_stories` | 908 | 0 | 908 (remove) |
| `list_products` | 857 | 500 | 357 |
| `list_features` | 829 | 500 | 329 |
| `get_sync_history` | 722 | 0 | 722 (consolidate) |
| `get_problematic_tests` | 689 | 500 | 189 |
| `get_test_status` | 665 | 500 | 165 |
| `get_database_stats` | 635 | 0 | 635 (consolidate) |
| `health_check` | 579 | 0 | 579 (consolidate) |
| **Total** | **~12,840** | **~6,600** | **~6,240 (49%)** |

**Measurement:**
- Primary: Run `/context` in Claude Code and check MCP tool token counts
- Secondary: `uv run python scripts/measure_tool_tokens.py` (tiktoken baseline)
- See `scripts/token_baseline_2025-11-26.txt` for comparison notes

## 8. Dependencies

**Internal:**

- Epic 007 complete (analytics engine, read-through caching)
- ADR-017 (pull model architecture) - informs computed field strategy

**External:**

- None

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Computed subqueries slow at scale | Medium | Monitor query times; can migrate to PostgreSQL materialized views if needed |
| Breaking changes from renames | Medium | Consider backward-compatible aliases; document migration clearly |
| Schema slimming reduces LLM usability | Medium | Validate with LLM testing; move detail to MCP prompts |
| REST API scope creep | Low | Strict 1:1 parity only; no new functionality |

## 10. Future Enhancements (Post-Epic)

Deferred to future epics:

- PostgreSQL migration (if scale demands)
- Materialized views for computed counts
- GraphQL API (alternative to REST)
- WebSocket subscriptions for real-time updates

---

**Epic Status:** Ready for Implementation
**Dependencies:** Epic 007 (Generic Analytics Framework) complete ✅
**Target:** MCP tool token usage reduced 49% (12.8k→6.6k), consistent taxonomy, REST parity
