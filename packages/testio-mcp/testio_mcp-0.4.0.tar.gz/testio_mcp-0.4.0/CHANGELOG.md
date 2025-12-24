# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

*No unreleased changes.*

## [0.4.0] - 2025-12-21

### Major Release: Multi-Product Analytics & Frontend Integration

This release adds multi-product portfolio analysis, centralized health thresholds, visualization hints for frontend rendering, and new REST API endpoints. 24 commits with significant breaking changes.

### Breaking Changes

#### Product Quality Report Refactor
- **`get_product_quality_report` → `generate_quality_report`**
  - New name reflects multi-product support
  - **Parameter changes:**
    - `product_id: int` → `product_ids: list[int] | int` (accepts single or multiple)
    - New: `test_ids: list[int] | None` for filtering to specific tests
    - Removed: `tests_limit` parameter (replaced by `test_ids` for explicit filtering)
  - **Response changes:**
    - New fields: `product_ids`, `products`, `test_ids`, `by_product` (multi-product breakdown)
    - Removed fields: `test_sample`, `cache_stats` (token efficiency for MCP)
    - Renamed: `test_sample` → `test_data` (REST API only, via `include_test_data`)
  - **Validation:** Empty `test_ids=[]` now raises error (use `None` for all tests)

- **REST API endpoint change:**
  - `GET /api/products/{product_id}/quality-report` → `GET /api/quality-report?product_ids=...`
  - New query parameters: `product_ids` (required), `test_ids` (optional)

- **New exception:** `TestProductMismatchError` - raised when test_ids don't belong to product_ids

- **Mutual exclusivity validation** - `test_ids` cannot be combined with date or status filters
  - `test_ids` means "report on exactly these tests" - additional filters would be confusing
  - Raises `ValidationError` with clear message when attempting to combine

#### Analytics Time Dimension Sorting
- **Time dimensions now sort ascending by default** (chronological order)
  - Before: `query_metrics(dimensions=["month"])` returned newest first
  - After: Returns oldest first (chronological)
  - Override with explicit `sort_order="desc"` if needed

### Added

#### REST API Endpoints (3 new)
- **`GET /api/bugs`** - List bugs with filtering (test_ids, status, severity, pagination)
- **`GET /api/bugs/{id}/summary`** - Detailed bug information with related entities
- **`GET /api/thresholds`** - Playbook health indicator threshold configuration

#### Centralized Playbook Thresholds
- **Health indicator thresholds** - Centralized configuration for rejection rate, auto-acceptance rate, and review rate thresholds
  - 6 new environment variables: `PLAYBOOK_REJECTION_WARNING`, `PLAYBOOK_REJECTION_CRITICAL`, `PLAYBOOK_AUTO_ACCEPTANCE_WARNING`, `PLAYBOOK_AUTO_ACCEPTANCE_CRITICAL`, `PLAYBOOK_REVIEW_WARNING`, `PLAYBOOK_REVIEW_CRITICAL`
  - Default values match CSM Playbook: rejection (20%/35%), auto-acceptance (20%/40%), review (80%/60%)
  - Values are 0.0-1.0 (e.g., 0.20 = 20%)

- **API response enhancements** - `generate_quality_report` now includes:
  - `health_indicators` - Computed health status for each metric ("healthy", "warning", "critical", "unknown")
  - `thresholds` - Current threshold configuration for transparency (enables frontend to explain status)

- **Threshold validation** - `MetricThreshold` model validates threshold ordering at startup
  - For direction="above": warning must be < critical
  - For direction="below": warning must be > critical
  - Misconfigured thresholds raise clear `ValidationError` on server startup

#### Analytics Enhancements
- **`visualization_hint`** - New field in `query_metrics` response with chart rendering recommendations
  - Includes: `chart_type`, `x_axis`, `y_axis`, `series_by`, `confidence`, `rationale`, `alternatives`
  - Supports: line, multi_line, pie, horizontal_bar, stacked_bar, grouped_bar, table
  - Dual-axis support for mixed count/rate metrics
- **`tests_limit`** - New parameter to scope metrics to most recent N tests
- **`testing_type`** - Now included in test data exports (rapid, focused, coverage, usability)

#### Flexible Input Parsing
- **`product_ids` and `test_ids`** now accept multiple formats:
  - Integer: `598`
  - List: `[598, 599]`
  - Comma-separated string: `"598,599"`
  - JSON array string: `"[598, 599]"`

#### MCP Progress Notifications
- **Long-running operations** now emit progress updates for better UX in AI clients

### Changed

#### Schema Additions (Non-Breaking)
- **`QualityReportSummary`** - New `health_indicators` field (dict with status per metric)
- **`GenerateQualityReportOutput`** - New `thresholds` field (threshold configuration)
- **`QueryResponse`** - New `visualization_hint` field (chart recommendations)
- **Note:** These are additive changes. Existing clients ignoring unknown fields will continue to work.

### Fixed

- **Boundary condition in health status** - Values exactly at threshold boundaries now correctly classified
  - Before: `rejection_rate=0.20` returned "healthy" (used `>` comparison)
  - After: `rejection_rate=0.20` returns "warning" (uses `>=` comparison)
  - Matches playbook documentation: "20-35% = warning" means 20% IS warning

- **Status filter collision in analytics** - Using `status` as a dimension no longer incorrectly filters bugs
  - Root cause: Default test status filter was being applied to Bug.status column
  - Now correctly scopes status filter to Test.status only

- **Empty status handling** - Empty strings in comma-separated status lists now filtered
  - Before: `statuses=",running,,"` would pass empty strings to SQL queries
  - After: Filters to `["running"]` before processing
  - Empty result (e.g., `",,"`) now raises validation error

- **Test ordering in quality reports** - Test IDs now consistently sorted by `end_at` descending (most recent first)

- **N+1 query optimization** - Multi-product breakdown now uses grouped aggregate queries
  - Before: 3×N queries for N products (one per product for test aggregates, test IDs, bug aggregates)
  - After: 6 queries total regardless of product count
  - New repository methods: `get_test_aggregates_grouped_by_product()`, `get_bug_aggregates_grouped_by_product()`

- **Dead code cleanup** - Removed unused Enum check in status parsing (TestStatus is a Literal, not Enum)

### Security

- **Dependency updates** - `urllib3` upgraded to 2.6.0 for CVE fixes
- **Dependency updates** - `filelock` and `fastmcp` upgraded for security vulnerabilities

## [0.3.0] - 2025-12-04

### Major Release: Productivity Workflows & Advanced Analytics

This release adds interactive analysis workflows, full-text search, enhanced analytics, and significant reliability improvements. 127 commits across 14+ epics.

### Breaking Changes

#### Tool Consolidation
- **`health_check` and `get_database_stats` → `get_server_diagnostics`**
  - Single unified diagnostic endpoint for API, database, and sync status
  - Migration: Replace `health_check` calls with `get_server_diagnostics`

- **`list_user_stories` → REMOVED**
  - Migration: Use `list_features` + `get_feature_summary` instead
  - User stories are now embedded in feature summaries

#### Analytics Behavior
- **`query_metrics` now excludes initialized/cancelled tests by default**
  - Matches `get_product_quality_report` default behavior
  - Override: Use `filters={'status': [...]}` to include all statuses

#### Configuration Defaults
- **`TESTIO_REFRESH_INTERVAL_SECONDS`**: 900 (15 min) → 3600 (1 hour)
  - No action needed; better default for most users

### Added

#### MCP Tools (5 new)
- **`get_product_summary`** - Product metadata with test/feature counts
- **`get_feature_summary`** - Feature details with embedded user stories
- **`get_user_summary`** - User metadata with activity counts
- **`get_bug_summary`** - Comprehensive bug details with reproduction steps
- **`search`** - Full-text search (FTS5) across products, features, tests, bugs
  - BM25 relevance ranking
  - Prefix matching (`login*`)
  - Date and product filtering

#### MCP Prompts (2 new)
- **`analyze-product-quality`** - Interactive 5-phase quality analysis workflow
  - Evidence-first methodology with bug citations
  - Portfolio mode for cross-product analysis
  - Generates exportable analysis artifacts
- **`prep-meeting`** - Narrative-first meeting preparation
  - Generates fetch scripts, slide data, conversation guides

#### MCP Resources (2 new)
- **`testio://knowledge/playbook`** - Expert CSM heuristics and templates
- **`testio://knowledge/programmatic-access`** - REST API discovery guide

#### Analytics Enhancements
- New dimensions: `platform`, `test_environment`, `known_bug`
- New metric: `bugs_per_test` (auto-includes `test_count`)
- Severity breakdown metrics (critical, high, medium, low counts)
- Rate metrics: `auto_acceptance_rate`, `active_acceptance_rate`, `overall_acceptance_rate`

#### Setup Command Enhancements
- Generates additional config vars with defaults:
  - `TESTIO_DB_PATH`, `TESTIO_REFRESH_INTERVAL_SECONDS`, `CACHE_TTL_SECONDS`
  - `LOG_FILE`, `TESTIO_SYNC_SINCE` (commented)
- Copies README.md and MCP_SETUP.md to `~/.testio-mcp/` for easy access

#### Data Model
- **Test environment tracking** - New `test_environment` field (Android, iOS, Web)
- **Known bug tracking** - New `known_bugs_count` field

### Fixed

#### Critical Production Fixes
- **AsyncSession resource leaks** (TD-001) - Fixed concurrency issues with shared sessions
- **ORM/Row confusion** - Fixed SQLAlchemy Row vs ORM model errors
- **Zero-bug test validation** - Fixed "required property" errors for tests with no bugs
- **Search bug indexing** - Restored full-text search for bugs

#### Other Fixes
- Date parsing for natural language inputs ("3 months ago")
- Query metrics cardinality bugs with many-to-many dimensions
- WebSocket protocol deprecation warnings

### Changed

#### Documentation Overhaul
- **README.md** - Streamlined, action-oriented with tool examples
- **MCP_SETUP.md** - Client-config only, removed duplicated setup content
- Docs bundled in wheel for uvx users

#### Performance & Reliability
- Read-through caching with per-entity locks
- Three-phase sync: products → features → tests
- Configurable cache TTL (default: 1 hour)
- Service layer boilerplate elimination (TD-002)

### Removed
- `list_user_stories` tool (use `list_features` + `get_feature_summary`)
- `health_check` tool (use `get_server_diagnostics`)
- `get_database_stats` tool (use `get_server_diagnostics`)

---

## [0.2.1] - 2025-11-20

### Fixed

#### Schema Validation Fixes
- **EBR report schema validation** - Fixed Pydantic v2 schema definition for optional rate fields
  - Added `default=None` to 10 rate fields in `TestBugMetrics` and `EBRSummary` models
  - Fields affected: active_acceptance_rate, auto_acceptance_rate, overall_acceptance_rate, rejection_rate, review_rate
  - **Impact:** `generate_ebr_report` now works correctly for tests with 0 bugs
  - **Error fixed:** "Output validation error: 'active_acceptance_rate' is a required property"
  - **Root cause:** In Pydantic v2, `field: Type | None` without `default=None` creates a required (but nullable) field

- **Date parsing for natural language inputs** - Fixed broken date parsing for relative date terms
  - Replaced `python-dateutil` with `dateparser` library (was installed but unused)
  - Added normalization: "last X {days,weeks,months,years}" → "X {days,weeks,months,years} ago"
  - Simplified parsing pipeline from 249→148 lines
  - Added `freezegun>=1.5.0` for deterministic time-based testing
  - **Impact:** CLI `--since "3 months ago"` and MCP date filters now work correctly
  - **Error fixed:** "3 months ago" was incorrectly parsed as November 3rd instead of 3 months before current date

### Added

#### Interactive Setup Command (STORY-027)
- **`testio-mcp setup` command** - Guided CLI workflow for creating `~/.testio-mcp.env` configuration
- **Customer name validation** - Enforces DNS subdomain rules (alphanumeric + hyphens only)
- **API token prompt** - Masked input with preview format (`{first_4}●●●●{last_4} ({length} chars)`)
- **Customer ID prompt** - Clear instructions for both TestIO employees and customers (default: 1)
- **Log format selection** - Choose between text (human-readable, colorized) or JSON (machine-parseable) logging
- **Log level selection** - Configure verbosity: INFO (normal), DEBUG (detailed), or WARNING (minimal)
- **Product filtering** - Optional comma-separated product IDs to limit sync scope and reduce sync time
- **API connectivity validation** - Tests token with retry/force-save/cancel options (SEC-002 compliant via TestIOClient)
- **Confirmation summary** - Table display showing all settings with Save/Edit/Cancel options
- **File overwrite handling** - Automatic backup creation before overwriting
- **Secure file permissions** - Sets 0o600 (user read/write only)
- **Success message** - Clear next steps and auto-loading info
- **No --env-file flag needed** - Configuration auto-loads from `~/.testio-mcp.env`

### Changed
- **BREAKING:** `TESTIO_CUSTOMER_ID` now defaults to `1` and is optional for single-tenant deployments
  - **Migration:** Remove `TESTIO_CUSTOMER_ID` from your `.env` file (default value is sufficient)
  - **Rationale:** Customers don't know their TestIO internal customer ID, and it's not exposed via API
  - **Impact:** Existing databases continue to work (customer_id column remains unchanged)
  - **Multi-tenant:** Explicit customer IDs still required for multi-tenant deployments (STORY-010)

---

## [0.2.0] - 2025-11-20

### Major Release: Architectural Improvements

This release includes significant architectural changes from 0.1.x, adding persistent storage, multi-client support, and REST API access.

### Added

#### Local Data Store (STORY-021)
- **SQLite-based persistent cache** with incremental sync
- **Background sync** on server startup (non-blocking)
- **Query interface** for fast local queries (~10ms vs ~500ms API calls)
- **Incremental sync** - Only fetches new/changed tests (stops at first known test + 2 safety pages)
- **Background refresh** - Configurable periodic refresh of mutable tests (default: 300s)
- **Database management tools**:
  - `get_database_stats` - Monitor size, sync status, storage info
  - `clear_cache` - Force fresh sync
  - `get_problematic_tests` - View tests that failed to sync
  - `force_sync_product` - Force fresh sync of specific product
- **CLI sync command** with progress reporting and date filtering:
  - `testio-mcp sync --status` - Show database status
  - `testio-mcp sync --since yesterday` - Incremental sync with date filtering
  - `testio-mcp sync --force` - Non-destructive full refresh
  - `testio-mcp sync --refresh` - Hybrid mode (discover new + update mutable)
  - `testio-mcp sync --nuke` - Destructive rebuild (requires confirmation)
- **Problematic tests management** (STORY-021e):
  - Track failed sync events with unique event IDs
  - Manual test ID mapping to failed events
  - Retry mechanism for individual test fetches
  - File-based locking for safe concurrent operations

#### HTTP Transport (STORY-023a)
- **HTTP transport mode** for multiple concurrent clients
- Single server process serves all clients (no database lock conflicts!)
- Visible logs in terminal (not hidden by stdio)
- Single background sync process (efficient, no redundant API calls)
- Configuration: `testio-mcp serve --transport http --port 8080`
- Clients connect via URL: `http://127.0.0.1:8080/mcp`

#### Hybrid MCP + REST API (STORY-023f)
- **FastAPI wrapper** serving both MCP and REST protocols
- **REST endpoints** at `/api/*` (tests, products, reports)
- **Interactive Swagger docs** at `/docs` (auto-generated)
- **Health endpoint** at `/health` (monitoring)
- **`--api-mode` flag** - Choose mcp, rest, or hybrid mode
- **Shared lifespan** - Single resource set (no duplication)

#### Transformers Layer (Anti-Corruption Layer)
- **ACL pattern** - Decouples service layer from API contracts
- **Semantic field mapping** - Transforms generic 'id' to 'test_id', 'product_id'
- **Type-safe transformations** - DTO validation before transformation
- Located in `src/testio_mcp/transformers/`

#### New MCP Tools
- `list_products` - List all products with optional search and type filtering
- `get_test_activity_by_timeframe` - Analyze activity across products by date range
- `generate_ebr_report` - Executive Bug Report with file export support (STORY-025)
- `generate_status_report` - Executive summaries in markdown/text/json
- Database management tools (see above)

#### CLI Enhancements
- **Subcommand architecture**: `serve`, `sync`, `problematic`
- **Transport selection**: `--transport stdio|http` (default: stdio)
- **HTTP server options**: `--host`, `--port`
- **Sync options**: `--since`, `--product-ids`, `--force`, `--refresh`, `--nuke`, `--dry-run`
- **Version pinning support**: `uvx testio-mcp@0.2.0`

#### Developer Experience
- **uvx installation** - No repository cloning needed, install directly from PyPI
- **Service layer refactoring** - BaseService class reduces boilerplate by ~40%
- **get_service() helper** - 1-line dependency injection with type safety
- **FastMCP ToolError pattern** - Consistent error handling across all tools
- **Auto-discovery** - Tools automatically registered via pkgutil

### Changed

#### ⚠️ BREAKING CHANGE: `list_tests` Default Behavior (Story 011)

**What changed:**
- The `list_tests` tool default behavior has changed from returning only "running" tests to returning ALL tests regardless of status
- `statuses=None` (default) now returns all tests (no filtering)
- `statuses=[]` (empty list) also returns all tests (consistent with None)
- The `statuses` parameter now supports all 6 valid test statuses from the TestIO Customer API

**Valid statuses:**
- `running` - Test currently active
- `locked` - Test locked/finalized (finished)
- `archived` - Test archived (finished)
- `customer_finalized` - Customer marked as final (finished)
- `initialized` - Test created but not started (pending)
- `cancelled` - Test cancelled



### Added
- Runtime validation for status values in `list_tests` tool (raises `ValueError` with descriptive message for invalid statuses)
- `VALID_STATUSES` constant in `ProductService` for centralized status validation
- Support for `customer_finalized` and `initialized` status values
- Clear output contract: `statuses_filter` field in response shows effective filter applied

- **Development Status**: Alpha → Beta (pyproject.toml)
- **Python 3.13 support** added to classifiers
- **Documentation overhaul**: README, MCP_SETUP, CLAUDE.md updated with uvx patterns

### Removed
- Invalid/legacy status value `review_successful` (this is a separate field in the API, not a test status)

### Fixed
- Cache key generation now handles `statuses=None` correctly (uses "all" sentinel instead of causing TypeError)
- Service layer now consistently handles `None` and empty list for statuses parameter
- Database lock conflicts eliminated via HTTP transport mode
- Timezone normalization - All timestamps stored in UTC (STORY-021c)


---

## [0.1.1] - 2025-01-04

### Added
- Initial MCP server implementation
- `health_check` tool
- `get_test_status` tool
- `list_products` tool
- `list_tests` tool
- `get_test_bugs` tool
- Service layer pattern (ADR-006)

### Fixed
- Various bug fixes and improvements

---

## [0.1.0] - 2025-01-03

### Added
- Initial project setup
- Basic TestIO API client
- In-memory caching
- Configuration management

[Unreleased]: https://github.com/testio/testio-mcp/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/testio/testio-mcp/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/testio/testio-mcp/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/testio/testio-mcp/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/testio/testio-mcp/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/testio/testio-mcp/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/testio/testio-mcp/releases/tag/v0.1.0
