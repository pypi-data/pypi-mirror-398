# Epic-007: Generic Analytics Framework (Metric Cube)

## 1. Overview

**Goal:** Implement a flexible, registry-driven analytics engine (the "Metric Cube") that enables dynamic querying of testing metrics without creating a new tool for every analytical question.

**Motivation:**
* **Eliminate Tool Explosion:** Instead of creating `analyze_feature_coverage`, `analyze_bug_density`, `analyze_tester_perf`, etc., we build ONE powerful query engine.
* **Enable Dynamic Exploration:** LLM can construct queries on-the-fly by combining dimensions (feature, tester, month) with metrics (bug_count, test_count, bugs_per_test).
* **Future-Proof:** New questions are answered by combining existing dimensions/metrics differently, not by writing new tools.
* **Direct Attribution:** Leverage API's direct Bug → TestFeature link (discovered in planning) for accurate bug attribution without fractional logic.

**Key Innovation:** The TestIO API provides direct `test_feature` object in bug JSON, enabling precise Bug → TestFeature → Feature attribution via foreign keys.

**Performance Guardrails (V1):**
* **Max Dimensions:** 2 (designed to extend to 3 in V2)
* **Max Rows:** 1000 (hard limit)
* **Timeout:** Inherits HTTP_TIMEOUT_SECONDS=90.0 from existing HTTP client config

## 2. Scope

Introduce the `test_features` table and build a generic analytics service that constructs dynamic SQL based on requested dimensions and metrics.

**Entities:**
* `TestFeature` (NEW) - Contextual snapshot of a feature in a specific test cycle (includes customer_id for security)
* `Bug.test_feature_id` (NEW FK) - Direct link to the feature being tested when bug was found

**Components:**
* `AnalyticsService` - Registry-driven SQL builder
* `query_metrics` tool - Dynamic analytics queries
* `get_analytics_capabilities` tool - Discovery of available dimensions/metrics
* Backfill script - Populate historical data

**Stories:** 8 total
- STORY-041: TestFeature Schema & Migration
- STORY-042: Historical Data Backfill
- STORY-043: Analytics Service (The Engine)
- STORY-044B: Analytics Staleness Warnings (Repository Pattern) ← REVISED
- STORY-044C: Referential Integrity Pattern (Repository Layer) ← REVISED
- STORY-044: Query Metrics Tool
- STORY-045: Customer Engagement Analytics
- STORY-046: Background Sync Optimization ← NEW

**Architecture Refinement (2025-11-25):**
During planning, a critical design flaw was discovered: the original STORY-044B/044C design created circular dependencies (AnalyticsService → TestService → FeatureService). The architecture was refined to use **repository-level integrity checks** instead:
- ✅ **No circular dependencies:** Services remain acyclic
- ✅ **Reuses existing patterns:** `BugRepository.get_bugs_cached_or_refresh()` already implements intelligent staleness
- ✅ **New pattern added:** `FeatureRepository.get_features_cached_or_refresh()` mirrors BugRepository for consistency
- ✅ **Dual integrity approach:** Read-time (analytics) + write-time (sync) both handled at repository layer
- ✅ **Simplified background sync:** 3 phases instead of 4 (removes proactive bug refresh)
- ✅ **Peer-reviewed:** Approved by architecture (Codex) and story design (Gemini) experts

**Architecture Documentation:**
- **[Repository Audit](../sprint-artifacts/epic-007-repository-audit.md)** - Comprehensive analysis of current vs. needed repository capabilities, implementation patterns, and testing strategy
- **[Sprint Change Proposal](../sprint-change-proposal-2025-11-25.md)** - Original architecture issue discovery and resolution

## 3. Context Documents

This epic is based on comprehensive planning documents in `docs/planning/`:
- [Integration Summary](../planning/epic-007-integration-summary.md) - Code touchpoints and migration checklist
- [Analytics Inventory](../planning/epic-007-analytics-inventory.md) - Entity analysis and use cases
- [Schema Proposal](../planning/epic-007-schema-proposal.md) - TestFeature table design and API discovery
- [Generic Analytics Strategy](../planning/epic-007-generic-analytics-strategy.md) - Implementation plan
- [Cube Prototype](../planning/epic-007-cube-prototype.md) - Technical implementation details

## 4. Stories

### STORY-041: TestFeature Schema & Migration

**User Story:**
As a developer building analytics features,
I want the `test_features` table and `Bug.test_feature_id` foreign key in the database,
So that I can query which features were tested and link bugs directly to the features being tested.

**Acceptance Criteria:**

**Given** the database schema needs to support feature-level analytics
**When** I run the migration
**Then** the following schema changes are applied:

1. [ ] `test_features` table created with columns:
   - `id` (INTEGER PRIMARY KEY) - TestFeature ID from API
   - `customer_id` (INTEGER, INDEXED) - Customer ID for security filtering
   - `test_id` (INTEGER, FK to tests.id, INDEXED)
   - `feature_id` (INTEGER, FK to features.id, INDEXED)
   - `title` (TEXT) - Snapshot of feature title
   - `description` (TEXT, NULLABLE) - Snapshot of feature description
   - `howtofind` (TEXT, NULLABLE) - Testing instructions snapshot
   - `user_stories` (TEXT, DEFAULT '[]') - JSON array of user story strings
   - `enable_default` (BOOLEAN, DEFAULT FALSE)
   - `enable_content` (BOOLEAN, DEFAULT FALSE)
   - `enable_visual` (BOOLEAN, DEFAULT FALSE)

2. [ ] `bugs` table altered to add:
   - `test_feature_id` (INTEGER, NULLABLE, FK to test_features.id, INDEXED)

3. [ ] Indices created:
   - `ix_test_features_customer_id` on `test_features.customer_id` (security filtering)
   - `ix_test_features_test_id` on `test_features.test_id`
   - `ix_test_features_feature_id` on `test_features.feature_id`
   - `ix_bugs_test_feature_id` on `bugs.test_feature_id`
   - `ix_tests_end_at` on `tests.end_at` (date range filtering)
   - `ix_tests_created_at` on `tests.created_at` (time bucketing queries)

4. [ ] ORM models updated:
   - `TestFeature` SQLModel class created in `src/testio_mcp/models/orm/test_feature.py`
   - `Bug` model updated with `test_feature_id` field
   - Relationships added: `Test.test_features`, `Feature.test_features`, `Bug.test_feature`

5. [ ] Migration uses `batch_alter_table` for SQLite compatibility

6. [ ] `TestRepository.insert_test()` updated to call `_upsert_test_feature()`
   - Location: `src/testio_mcp/repositories/test_repository.py:111-195`
   - After line 136, add test_features extraction and upsert

7. [ ] `TestRepository._upsert_test_feature()` method implemented
   - Extracts `test_data.get("features", [])`
   - For each feature_data, upserts TestFeature record
   - Handles both insert and update cases

8. [ ] `BugRepository.refresh_bugs()` updated to extract `test_feature_id`
   - Location: `src/testio_mcp/repositories/bug_repository.py:414-486`
   - After line 453, extract `bug.get("test_feature", {}).get("id")`
   - Include in Bug model instantiation (line 468-481)

9. [ ] `BugRepository.refresh_bugs_batch()` updated similarly

10. [ ] Type checking passes: `mypy src/testio_mcp/models/orm/ --strict`

11. [ ] Unit tests added:
    - `tests/unit/test_test_repository.py` - Test `_upsert_test_feature()`
    - `tests/unit/test_bug_repository.py` - Test `test_feature_id` extraction

12. [ ] Migration tested: `alembic upgrade head` works on clean database

**Prerequisites:** Epic 006 (ORM Refactor) must be complete

**Technical Notes:**
- See [Integration Summary](../planning/epic-007-integration-summary.md) for exact code touchpoints
- Migration chains from Epic 006 baseline revision `0965ad59eafa`
- Direct attribution eliminates need for fractional bug attribution logic
- `user_stories` stored as JSON string for simplicity (ADR-013 pattern)

**Estimated Effort:** 4-5 hours

---

### STORY-042: Historical Data Backfill

**User Story:**
As a developer preparing to launch analytics features,
I want all existing tests and bugs backfilled with TestFeature data,
So that analytics queries return complete historical data from day one.

**Acceptance Criteria:**

**Given** the `test_features` table and `Bug.test_feature_id` column exist
**When** I run the backfill script
**Then** historical data is populated:

1. [ ] Backfill script created: `tools/backfill_test_features.py`

2. [ ] Script processes tests in batches (500 per batch) to manage memory

3. [ ] For each test:
   - Parse `data["features"]` JSON array
   - Insert/update `test_features` records
   - Handle missing/malformed data gracefully

4. [ ] For each bug:
   - Parse `raw_data["test_feature"]["id"]` from JSON
   - Update `Bug.test_feature_id` field
   - Handle bugs without test_feature data (leave NULL)

5. [ ] Progress bar displays:
   - Current batch number
   - Total tests/bugs processed
   - ETA to completion
   - Success/error counts

6. [ ] Data validation:
   - >95% of tests have test_features populated
   - >95% of bugs have test_feature_id populated
   - Log mismatches for investigation

7. [ ] Script supports `--dry-run` mode:
   - Shows what would be changed
   - No database modifications
   - Reports validation statistics

8. [ ] Script is idempotent:
   - Safe to re-run multiple times
   - Uses upsert logic (INSERT OR REPLACE)
   - No duplicate records created

9. [ ] Error handling:
   - Logs errors to `backfill_errors.log`
   - Continues processing on individual record errors
   - Returns non-zero exit code if >5% failure rate

10. [ ] Documentation added to script docstring:
    - Usage examples
    - Expected runtime (~2-5 minutes for typical dataset)
    - Validation criteria

**Prerequisites:** STORY-041 must be complete (schema and ORM models exist)

**Technical Notes:**
- Use `AsyncSession` for database operations
- Batch commits every 500 records for performance
- Validation query: `SELECT COUNT(*) FROM test_features` vs `SELECT COUNT(*) FROM tests`
- Bug attribution query: `SELECT COUNT(test_feature_id) FROM bugs WHERE test_feature_id IS NOT NULL`

**Estimated Effort:** 3-4 hours

---

### STORY-043: Analytics Service (The Engine)

**User Story:**
As a developer building analytics tools,
I want an AnalyticsService that constructs dynamic SQL from dimension/metric requests,
So that I can answer analytical questions without writing custom SQL for each query.

**Acceptance Criteria:**

**Given** the `test_features` table is populated
**When** I request metrics with dimensions
**Then** the AnalyticsService generates optimized SQL:

1. [ ] `AnalyticsService` class created in `src/testio_mcp/services/analytics_service.py`

2. [ ] Service constructor: `__init__(self, session: AsyncSession, customer_id: int)`
   - Read-only service (no repositories needed)
   - Uses session for direct SQL queries

3. [ ] Dimension registry implemented with definitions:
   - `feature` - Group by Feature ID/Title (via test_features → features)
   - `product` - Group by Product (via features → products)
   - `tester` - Group by User (via bugs → users, type=tester)
   - `customer` - Group by User (via tests → users, type=customer)
   - `severity` - Group by Bug Severity
   - `status` - Group by Bug/Test Status
   - `month` - Time bucket by Month (from created_at)
   - `week` - Time bucket by Week (from created_at)

4. [ ] Metric registry implemented with definitions:
   - `test_count` - COUNT(DISTINCT test_id)
   - `bug_count` - COUNT(DISTINCT bug_id)
   - `bug_severity_score` - SUM(CASE severity WHEN 'critical' THEN 5 ...)
   - `features_tested` - COUNT(DISTINCT feature_id)
   - `active_testers` - COUNT(DISTINCT reported_by_user_id)
   - `bugs_per_test` - bug_count / NULLIF(test_count, 0)

5. [ ] `QueryBuilder` class implements:
   - `add_dimension(dimension_key)` - Adds GROUP BY clause
   - `add_metric(metric_key)` - Adds SELECT aggregation
   - `add_filter(dimension, value)` - Adds WHERE clause
   - `add_date_range(start, end)` - Filters on Test.end_at
   - `build()` - Returns SQLAlchemy select statement

6. [ ] Direct attribution via Bug.test_feature_id:
   - Bug metrics join via `bugs.test_feature_id = test_features.id`
   - No fractional attribution logic needed
   - Single join path: test_features → bugs

7. [ ] Performance guardrails:
   - Max 2 dimensions (V1 limit, designed to extend to 3 in V2)
   - Max 1000 rows returned
   - 10-second query timeout
   - Raises `ValueError` if limits exceeded

8. [ ] `query_metrics()` method signature:
   ```python
   async def query_metrics(
       self,
       metrics: list[str],
       dimensions: list[str],
       filters: dict[str, Any] = {},
       start_date: str | None = None,
       end_date: str | None = None,
       sort_by: str | None = None,
       sort_order: str = "desc"
   ) -> dict
   ```

9. [ ] Returns rich response:
   - `data`: List of result rows with IDs and display names
   - `metadata`: query_time_ms, total_rows, dimensions_used, metrics_used
   - `query_explanation`: Human-readable summary
   - `warnings`: List of caveats (e.g., "Results limited to 1000 rows")

10. [ ] Unit tests cover:
    - Single dimension + single metric
    - Multiple dimensions (2)
    - Multiple metrics
    - Dimension filters
    - Date range filtering
    - Sort control
    - Error cases (too many dimensions, invalid keys)
    - Direct attribution queries (bug_count by feature)

11. [ ] Type checking passes: `mypy src/testio_mcp/services/analytics_service.py --strict`

**Prerequisites:** STORY-042 must be complete (historical data populated)

**Technical Notes:**
- Use SQLAlchemy Core for dynamic SQL construction
- Registry pattern prevents SQL injection (validated keys only)
- See [Cube Prototype](../planning/epic-007-cube-prototype.md) for SQL generation examples
- Date filtering uses `parse_flexible_date()` utility (supports ISO and natural language)

**Estimated Effort:** 5-6 hours

---

### STORY-044B: Analytics Staleness Warnings (Repository Pattern)

**User Story:**
As a data consumer using the Analytics Service,
I want to be warned when bug OR feature data is stale and see it refreshed automatically,
So that I can trust analytics accuracy while knowing data is improving in the background.

**Acceptance Criteria:**

**Given** the AnalyticsService needs to ensure data freshness for multiple entities
**When** staleness integration is implemented
**Then** analytics queries leverage repository patterns for BOTH bugs AND features:

1. [ ] Implement `FeatureRepository.get_features_cached_or_refresh(product_ids, force_refresh=False)`
   - Mirrors `BugRepository.get_bugs_cached_or_refresh()` pattern
   - Returns `tuple[dict[int, list[dict]], dict[str, Any]]` (features_by_product + cache_stats)
   - Decision logic: Check `products.features_synced_at`, refresh if stale (> `FEATURE_CACHE_TTL_SECONDS`)

2. [ ] Database migration: Add `features_synced_at` column to `products` table
   - Type: TIMESTAMP, Nullable: YES
   - Updated by: `FeatureRepository.get_features_cached_or_refresh()` after sync
   - Used by: Staleness check in same method

3. [ ] AnalyticsService constructor: `__init__(self, session: AsyncSession, customer_id: int, client: TestIOClient)`
   - NO service dependencies (eliminates circular dependency risk)
   - Creates repository instances internally (composition)

4. [ ] Pre-query identifies `test_id`s and `product_id`s in scope (lightweight queries)
   - Performance target: <10ms for typical queries

5. [ ] Uses `BugRepository.get_bugs_cached_or_refresh()` for bug staleness (existing pattern)

6. [ ] Uses `FeatureRepository.get_features_cached_or_refresh()` for feature staleness (new pattern)

7. [ ] Adds warnings if cache_hit_rate < 50% for EITHER bugs OR features
   - Bug warning: "Warning: X tests had stale bug data and were refreshed."
   - Feature warning: "Warning: Y products had stale feature data and were refreshed."

8. [ ] Performance SLA: <25% overhead for pre-query + staleness checks

9. [ ] Error handling for failed refresh (graceful degradation)
   - Return stale data with warning if API fails
   - Emit metrics: `analytics.bug_refresh_failures`, `analytics.feature_refresh_failures`

**Prerequisites:** STORY-043 must be complete (AnalyticsService implemented)

**Technical Notes:**
- **REVISED ARCHITECTURE:** Repository-level staleness for BOTH bugs AND features
- **Key Addition:** `FeatureRepository.get_features_cached_or_refresh()` (mirrors BugRepository pattern)
- No service dependencies (eliminates circular dependency)
- Read-time integrity: Ensures all entities fresh before analytics queries
- See [Repository Audit](../sprint-artifacts/epic-007-repository-audit.md) for implementation details

**Estimated Effort:** 5-6 hours (increased to include FeatureRepository.get_features_cached_or_refresh() implementation)

---

### STORY-044C: Referential Integrity Pattern (Repository Layer)

**User Story:**
As the sync system AND analytics service,
I want repositories to ensure all foreign key references are valid during BOTH writes (sync) AND reads (analytics),
So that queries never encounter missing referenced entities (data integrity guaranteed at all times).

**Acceptance Criteria:**

**NOTE:** This story focuses on **WRITE-TIME integrity** (sync operations). **READ-TIME integrity** (analytics) is handled by STORY-044B's `FeatureRepository.get_features_cached_or_refresh()`.

**Given** sync fetches tests, bugs, features independently
**When** write-time referential integrity checks are implemented at repository layer
**Then** all foreign keys resolve locally during writes:

1. [ ] `TestRepository._upsert_test_feature()` checks for missing features (write-time)
   - Before upserting test_feature, check if `feature_id` exists locally
   - If missing, call `_fetch_and_store_features_for_product(product_id)`
   - Only proceed with upsert after feature exists (FK constraint satisfied)

2. [ ] `TestRepository._fetch_and_store_features_for_product()` implements per-key locks
   - Maintains `_feature_fetch_locks: dict[int, asyncio.Lock]` for product IDs
   - Acquires lock before fetching to prevent thundering herd
   - Double-checks feature existence after acquiring lock
   - Creates FeatureRepository instance (composition, not DI) and calls `sync_features(product_id)`
   - Releases lock when done

3. [ ] `BugRepository.upsert_bug()` checks for missing users (write-time)
   - Before upserting bug, check if `reported_by_user_id` exists locally
   - If missing, fetch user via `GET /users/{id}` and store via UserRepository
   - Uses same per-key lock pattern (keyed by `user_id`)

4. [ ] Logging/metrics emitted when integrity fills occur
   - Log level: WARNING (indicates data sync gap)
   - Message: "Referential integrity fill: {entity_type} {id} missing, fetching from API"
   - Metric: `repository.integrity_fills` (counter, tagged by entity type and operation)

5. [ ] Error handling for failed integrity fill
   - Log ERROR if feature fetch fails
   - SKIP the upsert (don't create dangling FK)
   - Emit metric: `repository.integrity_fill_failures`
   - Re-raise exception so caller can handle test-level failures
   - Don't crash entire sync operation

6. [ ] Pattern applied to all sync paths
   - Background sync Phase 3 (discover new tests)
   - Manual test refresh (on-demand)
   - Initial sync (first run)
   - All use same `_upsert_test_feature()` method

7. [ ] Triggering scenarios documented
   - **Scenario A:** Background sync discovers new test → integrity check RUNS
   - **Scenario B:** Manual test refresh → integrity check RUNS
   - **Scenario C:** Initial sync → integrity check RUNS (safety net)
   - **Scenario D:** Analytics query → write-time check DOES NOT RUN (different code path, read-time handled by STORY-044B)

**Prerequisites:** None (enhances existing sync layer)

**Technical Notes:**
- **REVISED ARCHITECTURE:** Write-time integrity in repository layer, not service layer
- Read-time integrity handled separately by STORY-044B (FeatureRepository.get_features_cached_or_refresh())
- **Composition over DI:** Repositories create other repositories internally as needed
- **Per-key locks:** Prevent thundering herd when multiple queries miss same feature
- **Double-check pattern:** After acquiring lock, verify feature still missing before fetching
- Eliminates need for service-level dependencies (no circular dependency)
- Establishes referential integrity pattern for all future entities
- See [Repository Audit](../sprint-artifacts/epic-007-repository-audit.md) for detailed implementation patterns

**Estimated Effort:** 5-6 hours (includes per-key lock implementation, error handling, and triggering scenario documentation)

---

### STORY-044: Query Metrics Tool

**User Story:**
As an AI agent analyzing testing data,
I want a `query_metrics` tool with rich usability features,
So that I can dynamically explore metrics and answer analytical questions.

**Acceptance Criteria:**

**Given** the AnalyticsService is implemented
**When** I call the query_metrics tool
**Then** I get a rich, usable response:

1. [ ] `query_metrics` tool created in `src/testio_mcp/tools/query_metrics_tool.py`

2. [ ] Tool schema includes:
   - `dimensions`: list[str] - How to slice data (required)
   - `metrics`: list[str] - What to measure (required)
   - `filters`: dict[str, Any] - Dimension value filters (optional)
   - `start_date`: str | None - Start date for Test.end_at filter (optional)
   - `end_date`: str | None - End date for Test.end_at filter (optional)
   - `sort_by`: str | None - Metric/dimension to sort by (optional)
   - `sort_order`: str - 'asc' or 'desc' (default: 'desc')

3. [ ] Tool description includes:
   - Mental model explanation (Pivot Table analogy)
   - Common query patterns with examples
   - Instruction to use `get_analytics_capabilities()` first

4. [ ] Rich entity context in results:
   - Both IDs and display names (e.g., `feature_id` + `feature_title`)
   - Example: `{"feature_id": 42, "feature": "Login", "bug_count": 15}`

5. [ ] Natural language explanation:
   - Human-readable query summary in response
   - Example: "Showing bug count grouped by feature, sorted by bug_count descending"

6. [ ] Date range filtering:
   - Uses `parse_flexible_date()` for flexible date parsing
   - Filters on `Test.end_at` column
   - Supports ISO dates and natural language ("3 months ago", "last quarter")

7. [ ] Dimension filters:
   - `filters` dict for dimension values
   - Example: `{"severity": "critical", "status": "accepted"}`
   - All filters AND-combined

8. [ ] Sort control:
   - `sort_by` parameter (metric or dimension name)
   - `sort_order` parameter ('asc' or 'desc')
   - Defaults to first metric, descending

9. [ ] Response metadata includes:
   - `query_time_ms` - Execution time
   - `total_rows` - Result count
   - `dimensions_used` - List of dimensions
   - `metrics_used` - List of metrics

10. [ ] Warnings for edge cases:
    - "Results limited to 1000 rows"
    - "Date range spans >1 year, consider narrowing"
    - "No data found for specified filters"

11. [ ] `get_analytics_capabilities` tool created in `src/testio_mcp/tools/get_analytics_capabilities_tool.py`

12. [ ] Capabilities tool returns:
    - `dimensions`: List with key, description, example
    - `metrics`: List with key, description, formula
    - `filters`: List of valid filter keys
    - `limits`: Max dimensions, max rows, timeout

13. [ ] AnalyticsService added to `service_helpers.py`:
    - Pattern follows FeatureService (lines 201-213)
    - Read-only service (no repositories)
    - Injects AsyncSession and customer_id

14. [ ] Tools registered in `server.py`

15. [ ] Integration tests added: `tests/integration/test_epic_007_e2e.py`
    - Sync test → Verify test_features populated
    - Sync bugs → Verify Bug.test_feature_id populated
    - Query metrics → Verify direct attribution works
    - Test all usability features (date range, filters, sort)

16. [ ] Type checking passes: `mypy src/testio_mcp/tools/ --strict`

**Prerequisites:** STORY-043 must be complete (AnalyticsService implemented)

**Technical Notes:**
- See [Integration Summary](../planning/epic-007-integration-summary.md) for service_helpers.py pattern
- See [Cube Prototype](../planning/epic-007-cube-prototype.md) for tool interface design
- Performance guardrails enforced: max 2 dimensions, 1000 rows, 10s timeout
- Deferred to post-epic: raw data export, pagination, suggested follow-up queries

**Estimated Effort:** 4-5 hours

---

### STORY-045: Customer Engagement Analytics

**User Story:**
As a product manager analyzing customer engagement,
I want to query tests created and submitted by customer users,
So that I can identify top customer users and engagement patterns.

**Acceptance Criteria:**

**Given** the AnalyticsService registry is extensible
**When** I add customer engagement dimensions and metrics
**Then** I can query customer activity:

1. [ ] `customer` dimension added to registry:
   - Groups by User (type=customer)
   - Joins: tests → users (created_by_user_id)
   - Returns: user_id, username

2. [ ] `tests_created` metric added to registry:
   - Formula: COUNT(DISTINCT tests.id WHERE tests.created_by_user_id IS NOT NULL)
   - Measures: Tests created by customers

3. [ ] `tests_submitted` metric added to registry:
   - Formula: COUNT(DISTINCT tests.id WHERE tests.status IN ('submitted', 'completed'))
   - Measures: Tests submitted for review

4. [ ] Unit tests added for customer metrics:
   - Query by customer dimension
   - tests_created metric calculation
   - tests_submitted metric calculation
   - Combined query: tests_created + tests_submitted by customer

5. [ ] Integration test validates:
   - Create test data with customer users
   - Query metrics by customer dimension
   - Verify correct counts

6. [ ] Documentation updated:
   - Add customer engagement examples to tool description
   - Update get_analytics_capabilities output

**Prerequisites:** STORY-044 must be complete (query_metrics tool implemented)

**Technical Notes:**
- Extends existing registry pattern
- No new tables or migrations needed
- Uses existing User.user_type field for filtering
- Example query: `query_metrics(metrics=["tests_created", "tests_submitted"], dimensions=["customer"])`

**Estimated Effort:** 2-3 hours

---

### STORY-046: Background Sync Optimization

**User Story:**
As a system operator,
I want background sync to focus on discovering new data rather than proactively refreshing existing data,
So that API quota is used efficiently and sync cycles complete faster.

**Acceptance Criteria:**

**Given** background sync currently has 4 phases
**When** optimization is implemented
**Then** background sync is simplified to 3 phases:

1. [ ] Remove Phase 4 (mutable test + bug refresh) from `_run_background_refresh_cycle()`
   - Delete code that refreshes mutable tests based on staleness
   - Delete code that refreshes bugs for mutable tests
   - Bug staleness now handled on-demand via `BugRepository.get_bugs_cached_or_refresh()`

2. [ ] Keep Phase 2 (feature refresh with staleness check)
   - Features can have cosmetic changes (name, description updates)
   - Proactive refresh ensures analytics show current feature names
   - TTL-gated refresh (only if stale per `FEATURE_CACHE_TTL_SECONDS`)

3. [ ] Update background sync logging
   - Log message: "Background sync: 3 phases (products, features, new tests)"
   - Remove references to "Phase 4: Refresh mutable tests"

4. [ ] Update `should_run_initial_sync()` staleness check
   - Remove check for oldest mutable test sync
   - Check only: oldest product sync + oldest feature sync
   - Simplifies staleness logic

5. [ ] Add metrics for API call savings
   - Metric: `background_sync.api_calls_saved` (counter)
   - Track: Number of bug refresh calls that would have been made in old Phase 4
   - Baseline: ~500-700 calls per cycle (for reference)

6. [ ] Integration test: Verify on-demand bug refresh during analytics
   - Setup: Background sync completes (no bug refresh)
   - Action: Run analytics query on tests with stale bugs
   - Verify: `BugRepository.get_bugs_cached_or_refresh()` refreshes stale bugs
   - Verify: Analytics query includes staleness warning

7. [ ] Performance test: Verify background sync completes faster
   - Measure: Background sync cycle time before/after
   - Target: <60 seconds (vs ~5-10 minutes previously)
   - Verify: API call count reduced by 50-70%

**Prerequisites:**
- STORY-044B complete (analytics uses repository staleness pattern)
- STORY-044C complete (repository integrity checks handle missing references)

**Technical Notes:**
- **Rationale:** Bug data refreshed on-demand when queried (better UX, fewer wasted calls)
- **Feature refresh kept:** User preference to keep proactive feature refresh for cosmetic updates
- **Background sync phases:**
  - Phase 1: Refresh product metadata (always)
  - Phase 2: Refresh features (TTL-gated, kept per user preference)
  - Phase 3: Discover new tests (with automatic integrity checks from STORY-044C)
- **Benefits:**
  - 10x faster background sync (5-10 min → 30-60 sec)
  - 50-70% fewer API calls (~1000 → ~300-500 per cycle)
  - Better UX (on-demand refresh only for queried data)
  - Lower network load and API quota usage

**Estimated Effort:** 2-3 hours

---

## 5. Success Criteria

**Data Integrity:**
* `test_features` table populated with >95% match to test JSON data
* `Bug.test_feature_id` populated for >95% of bugs
* Direct Bug → TestFeature → Feature attribution working

**Flexibility:**
* Can answer "Which feature has the most critical bugs?" using query_metrics
* Can answer "Who tested Feature X last month?" using query_metrics
* Can answer "What's the bug density trend by month?" using query_metrics
* Single tool (`query_metrics`) replaces need for multiple specialized tools

**Performance:**
* Queries return in <5s for typical datasets (analytical queries on indexed cached data)
* Date range queries use `ix_tests_end_at` index efficiently
* Time bucketing queries use `ix_tests_created_at` index efficiently
* No N+1 query issues in multi-dimension queries
* Query timeout: Inherits HTTP_TIMEOUT_SECONDS=90.0 (sufficient for large data fetches via API)

**Safety:**
* No SQL injection vulnerabilities (validated registry only)
* Query limits enforced (max 2 dimensions, 1000 rows, 10s timeout)
* Clear error messages for invalid requests

**Usability:**
* Rich entity context (IDs + display names)
* Natural language explanations
* Flexible date parsing
* Discovery via get_analytics_capabilities

## 6. Integration Points

See [Integration Summary](../planning/epic-007-integration-summary.md) for detailed code touchpoints:

**TestRepository.insert_test()** - Add TestFeature upsert (line 136)
**BugRepository.refresh_bugs()** - Add test_feature_id extraction (line 453)
**service_helpers.py** - Add AnalyticsService DI (pattern at line 201-213)

## 7. Testing Strategy

**Unit Tests:**
- `tests/unit/test_test_repository.py` - TestFeature upsert logic
- `tests/unit/test_bug_repository.py` - test_feature_id extraction
- `tests/unit/test_analytics_service.py` - Query builder, registry, metrics
- `tests/unit/test_query_metrics_tool.py` - Tool input validation, error handling

**Integration Tests:**
- `tests/integration/test_epic_007_e2e.py` - Full sync → query flow
- Test data setup with known features, tests, bugs
- Verify direct attribution works end-to-end
- Test all usability features (date range, filters, sort)

**Performance Tests:**
- Benchmark queries with 1000+ tests
- Verify index usage with EXPLAIN QUERY PLAN
- Validate <2s response time for typical queries

## 8. Rollback Strategy

**Per-Story Rollback:**
```bash
# Revert code changes
git revert <commit-hash>

# Rollback migration (if needed)
alembic downgrade -1

# Resync data (if needed)
rm ~/.testio-mcp/cache.db
uv run python -m testio_mcp sync --verbose
```

**Full Epic Rollback:**
```bash
# Rollback all Epic 007 migrations
alembic downgrade <epic-006-head-revision>

# Revert all Epic 007 commits
git revert <story-041-commit>..<story-045-commit>
```

## 9. Future Enhancements (Post-Epic)

Deferred to future epics:
* Raw data export to .json file
* Pagination for large result sets
* Suggested follow-up queries
* 3-dimension queries (currently limited to 2)
* Cached query results (5-minute TTL)
* Visual chart generation

---

**Epic Status:** Complete ✅ (All stories implemented: 041, 042, 043, 044B, 045, 046, 047)
**Dependencies:** Epic 006 (ORM Refactor) ✅ Complete
**Architecture:** ADR-017 (Background Sync Pull Model) accepted and implemented
