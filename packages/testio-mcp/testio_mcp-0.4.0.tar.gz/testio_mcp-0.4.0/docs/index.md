# TestIO MCP Server - Documentation Index

**Last Updated:** 2025-12-03
**Version:** 0.3.0+
**Purpose:** Master AI entry point for navigating TestIO MCP Server documentation

---

## Quick Start

**New to this project?** Start here:
1. **[Project Overview](#project-overview)** - What this project does
2. **[Architecture](#architecture)** - System design and components
3. **[Development](#development)** - How to contribute

---

## Project Overview

TestIO MCP Server is an **AI-first integration layer** providing Model Context Protocol (MCP) access to TestIO's Customer API. It enables non-developer stakeholders (CSMs, PMs, QA leads) to query test status, bug information, and activity metrics through AI tools like Claude and Cursor.

### Current Capabilities (v0.3.0+)

| Category | Count | Description |
|----------|-------|-------------|
| **MCP Tools** | 17 | Data discovery, summaries, analytics, sync, search |
| **MCP Prompts** | 2 | Interactive workflows (product quality, meeting prep) |
| **MCP Resources** | 2 | Knowledge playbook, programmatic access guide |
| **REST API** | 17 endpoints | Full parity with MCP tools + Swagger UI |
| **Services** | 13 | Core, Analytics, Infrastructure services |

### Key Features

- **SQLite-First Architecture** - Persistent cache with WAL mode, FTS5 full-text search
- **Intelligent Caching** - Read-through caching with immutable/mutable entity handling
- **3-Phase Sync** - Products → Features → Tests with incremental discovery
- **Hybrid Server** - MCP + REST API in single process
- **Production Ready** - Token sanitization, graceful degradation, comprehensive testing

---

## Architecture

### Core Architecture Documents

- **[ARCHITECTURE.md](./architecture/ARCHITECTURE.md)** - Complete system architecture (v3.0)
- **[MCP.md](./architecture/MCP.md)** - MCP implementation patterns (v2.0)
- **[REST_API.md](./architecture/REST_API.md)** - REST API reference (v1.0)
- **[SERVICE_LAYER_SUMMARY.md](./architecture/SERVICE_LAYER_SUMMARY.md)** - Service layer architecture (v2.0)
- **[TECH-STACK.md](./architecture/TECH-STACK.md)** - Technology decisions and rationales

### Specialized Guides

- **[ANALYTICS.md](./ANALYTICS.md)** - Analytics engine guide (query_metrics, dimensions, metrics)
- **[API_CAPABILITIES.md](./architecture/API_CAPABILITIES.md)** - TestIO API capabilities and endpoints
- **[AUTH_STRATEGY.md](./architecture/AUTH_STRATEGY.md)** - Authentication and authorization
- **[CODING-STANDARDS.md](./architecture/CODING-STANDARDS.md)** - Code quality standards
- **[CUSTOMER_ID_STRATEGY.md](./architecture/CUSTOMER_ID_STRATEGY.md)** - Customer isolation strategy
- **[PERFORMANCE.md](./architecture/PERFORMANCE.md)** - Performance optimization
- **[SECURITY.md](./architecture/SECURITY.md)** - Security considerations
- **[TESTING.md](./architecture/TESTING.md)** - Testing strategy and guidelines

### Architecture Decision Records (ADRs)

- **[INDEX.md](./architecture/adrs/INDEX.md)** - ADR index and navigation
- **ADR-001** through **ADR-017** - Technology and design decisions

---

## Current System State (Dec 2025)

### MCP Tools Catalog

#### Data Discovery & Listing
| Tool | Purpose | Epic |
|------|---------|------|
| `list_products` | Product listing with enriched counts | MVP |
| `list_tests` | Test listing with filtering/pagination | MVP |
| `list_features` | Feature listing with test/bug counts | Epic-005 |
| `list_users` | User (tester/customer) listing | Epic-005 |
| `list_bugs` | Bug listing scoped to tests | STORY-084 |

#### Single-Entity Summaries
| Tool | Purpose | Story |
|------|---------|-------|
| `get_test_summary` | Test status with bug breakdown | MVP |
| `get_product_summary` | Product metadata with counts | STORY-057 |
| `get_feature_summary` | Feature with user stories | STORY-057 |
| `get_user_summary` | User with activity counts | STORY-057 |
| `get_bug_summary` | Bug details with attribution | STORY-085 |

#### Analytics & Reporting
| Tool | Purpose | Epic |
|------|---------|------|
| `get_product_quality_report` | Multi-test EBR aggregation | Epic-003 |
| `query_metrics` | Dynamic pivot tables | Epic-007 |
| `get_analytics_capabilities` | Discover dimensions/metrics | Epic-007 |
| `search` | FTS5 full-text search | Epic-010 |

#### Server Management
| Tool | Purpose | Story |
|------|---------|-------|
| `sync_data` | Explicit data refresh | STORY-051 |
| `get_server_diagnostics` | Consolidated health check | STORY-060 |
| `get_problematic_tests` | Failed sync debugging | Epic-009 |

### MCP Prompts

| Prompt | Purpose | Story |
|--------|---------|-------|
| `analyze-product-quality` | Interactive 5-phase quality analysis | STORY-087 |
| `prep-meeting` | Narrative-first meeting preparation | STORY-099 |

### MCP Resources

| URI | Purpose | Story |
|-----|---------|-------|
| `testio://knowledge/playbook` | CSM heuristics and templates | STORY-066 |
| `testio://knowledge/programmatic-access` | REST API discovery guide | STORY-099 |

### Breaking Changes (v0.3.0+)

| Change | Migration |
|--------|-----------|
| `health_check` → `get_server_diagnostics` | Use consolidated tool |
| `get_database_stats` → `get_server_diagnostics` | Use consolidated tool |
| `list_user_stories` removed | Use `list_features` + `get_feature_summary` |
| Default status filter | Excludes initialized/cancelled (override with explicit statuses) |

---

## Service Layer (13 Services)

| Service | Purpose | Dependencies |
|---------|---------|--------------|
| BaseService | Minimal DI base | TestIOClient |
| ProductService | Product operations | Client, Repository |
| TestService | Test status + caching | 3 Repositories |
| BugService | Bug listing/details | 2 Repositories |
| FeatureService | Feature operations | 1 Repository |
| UserService | User operations | 1 Repository |
| SearchService | FTS5 search | 1 Repository |
| SyncService | Unified sync orchestration | Client, Cache, 3 Repo Factories |
| AnalyticsService | Dynamic metrics | Client, 4 Repositories |
| QueryBuilder | Dynamic SQL | - |
| DiagnosticsService | Server health | Client, Cache |
| MultiTestReportService | EBR aggregation | 3 Repositories |
| UserStoryService | User story extraction | 1 Repository |

---

## Data Layer

### ORM Models (SQLModel)

| Model | Table | Key Fields |
|-------|-------|------------|
| Product | products | id, title, product_type, last_synced |
| Test | tests | id, title, status, testing_type, start_at, end_at |
| Bug | bugs | id, title, severity, status, rejection_reason, reported_at |
| Feature | features | id, title, user_stories (JSON), section_ids |
| TestFeature | test_features | id, test_id, feature_id |
| User | users | id, username, user_type, first_seen, last_seen |
| TestPlatform | test_platforms | id, test_id, operating_system_name |
| SyncMetadata | sync_metadata | key, value |
| SyncEvent | sync_events | id, status, duration_seconds |

### Database Configuration

- **Engine:** SQLite + WAL mode
- **Migrations:** Alembic (18 versions, frozen baseline: `0965ad59eafa`)
- **Current Head:** `8699d94758fb` (Dec 3, 2025)
- **FTS5:** Full-text search across products, features, tests, bugs

---

## Integration Patterns

### Data Flow

```
Read Path:  Tool → Service → Repository → SQLite (with read-through cache)
Write Path: API → Repository → SQLite (3-phase sync)
```

### Concurrency Controls

| Control | Limit | Purpose |
|---------|-------|---------|
| HTTP Semaphore | 10 | API request throttling |
| DB Write Semaphore | 1 | SQLite write serialization |
| Per-Entity Locks | Unlimited | Prevent duplicate API calls |
| File Lock | 1 | Cross-process sync coordination |
| Asyncio Lock | 1 | In-process sync coordination |

### Caching Strategy

| Entity Type | Strategy | TTL |
|-------------|----------|-----|
| Immutable (archived/cancelled) | Always SQLite | N/A |
| Mutable (running/locked/etc.) | Check staleness | 3600s (1 hour) |
| Background Refresh | Force all | Every hour |

---

## Epics

### Completed Epics

- **[Epic-014: Interactive Prompts](./epics/epic-014-interactive-prompts.md)** - analyze-product-quality, prep-meeting
- **[Epic-010: Full-Text Search](./epics/epic-010-fts5-search.md)** - FTS5 search across entities
- **[Epic-009: Sync Consolidation](./epics/epic-009-sync-consolidation.md)** - SyncService, sync_data tool
- **[Epic-008: MCP Layer Optimization](./epics/epic-008-mcp-layer-optimization.md)** - Token efficiency, taxonomy
- **[Epic-007: Generic Analytics Framework](./epics/epic-007-generic-analytics-framework.md)** - query_metrics tool
- **[Epic-006: ORM Refactor](./epics/epic-006-orm-refactor.md)** - SQLModel + Alembic
- **[Epic-005: Data Enhancement](./epics/epic-005-data-enhancement-and-serving.md)** - Features, users, metadata
- **[Epic-004: Production Architecture](./epics/epic-004-production-architecture.md)** - Production readiness
- **[Epic-003: Executive Testing Reports](./epics/epic-003-automated-executive-testing-reports.md)** - EBR reporting
- **[Epic-002: Local Data Store](./epics/epic-002-local-data-store-foundation.md)** - SQLite foundation
- **[Epic-001: TestIO MCP MVP](./epics/epic-001-testio-mcp-mvp.md)** - Initial implementation

---

## CLI Reference

### Commands

```bash
testio-mcp serve [OPTIONS]       # Start MCP server
testio-mcp sync [OPTIONS]        # Sync local database
testio-mcp setup                 # Interactive configuration wizard
testio-mcp problematic list      # List failed syncs
testio-mcp problematic retry ID  # Retry failed product sync
```

### Transport Modes

| Mode | Use Case |
|------|----------|
| `--transport stdio` (default) | MCP clients (Claude Code, Cursor) |
| `--transport http --api-mode hybrid` | REST API + MCP + Swagger docs |

### Sync Modes

| Flag | Behavior |
|------|----------|
| (default) | Hybrid: discover new + update mutable |
| `--incremental-only` | Fast: new tests only |
| `--force` | Non-destructive: refresh all |
| `--nuke --yes` | Destructive: delete + resync |

---

## Stories

Stories are organized in `./stories/` directory with completed stories in `./stories/done/`.

### Recent Completed Stories

- **STORY-099** - prep-meeting prompt workflow
- **STORY-087** - analyze-product-quality interactive prompt
- **STORY-085** - get_bug_summary tool
- **STORY-084** - list_bugs tool
- **STORY-066** - CSM knowledge playbook resource
- **STORY-065** - FTS5 search infrastructure
- **STORY-062** - AsyncSession management refactor
- **STORY-060** - Consolidated diagnostics tool
- **STORY-057** - Entity summary tools
- **STORY-051** - sync_data MCP tool

---

## Quality Assurance

### Testing

- **[TESTING.md](./architecture/TESTING.md)** - Testing strategy
- **[E2E_TESTING_SCRIPT.md](./E2E_TESTING_SCRIPT.md)** - End-to-end procedures
- **[AGENT_USABILITY_TASKS.md](./AGENT_USABILITY_TASKS.md)** - AI agent usability tests
- **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** - Common issues and solutions

### Test Coverage

```bash
uv run pytest -m unit              # ~0.5s, no API needed
uv run pytest                      # ~31s, full suite
uv run pytest -m integration       # ~30s, requires API token
```

---

## Planning & Technical Debt

- **[TECH_DEBT.md](./TECH_DEBT.md)** - Technical debt status (2/14 complete)
- **[tech-debt-remediation-plan.md](./planning/tech-debt-remediation-plan.md)** - Master plan for all 14 items
- **[future-enhancements.md](./planning/future-enhancements.md)** - Planned future features
- **[showcase-strategy.md](./planning/showcase-strategy.md)** - Product showcase strategy
- **[AUTH_STRATEGY_FUTURE.md](./planning/AUTH_STRATEGY_FUTURE.md)** - Future authentication

---

## Resources

- **[business_context.md](./resources/business_context.md)** - Business context and domain
- **[csm-assistant-system-prompt.md](./resources/csm-assistant-system-prompt.md)** - CSM assistant prompt

---

## Document Organization

### By Purpose

| Directory | Content |
|-----------|---------|
| `./architecture/` | System design, patterns, ADRs |
| `./epics/` | High-level feature sets |
| `./stories/` | Detailed implementation tasks |
| `./planning/` | Future roadmap and strategy |
| `./designs/` | Technical design documents |
| `./resources/` | Reference materials |

### By Audience

| Audience | Start With |
|----------|------------|
| Developers | ARCHITECTURE.md → Epic files → Stories |
| AI Agents | This index → Navigate to sections |
| Product/PM | Epic files → Planning docs |
| QA/Testing | TESTING.md → E2E_TESTING_SCRIPT.md |

---

## Maintenance

**This index generated/updated by:** document-project workflow (BMAD)
**Scan Strategy:** Vertical slices → Diagonal integration patterns
**Last Scan:** 2025-12-03

### Documentation Gaps Identified

| File | Issue | Priority |
|------|-------|----------|
| ARCHITECTURE.md | v2.1.1 outdated (shows 8 tools, now 19) | High |
| SERVICE_LAYER_SUMMARY.md | Missing new services | Medium |
| MCP.md | Missing new tools, prompts, resources | High |

---

## Quick Links

- **Current Version:** 0.3.0+
- **Repository:** [testio-mcp](https://github.com/testio/testio-mcp)
- **System Overview:** [ARCHITECTURE.md](./architecture/ARCHITECTURE.md)
- **Code Standards:** [CODING-STANDARDS.md](./architecture/CODING-STANDARDS.md)
- **Testing Guide:** [TESTING.md](./architecture/TESTING.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Scan Report:** [project-scan-report.json](./project-scan-report.json)
