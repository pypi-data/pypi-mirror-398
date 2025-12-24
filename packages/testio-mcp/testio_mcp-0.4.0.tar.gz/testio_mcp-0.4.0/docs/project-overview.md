# TestIO MCP Server - Project Overview

**Version:** 0.2.0
**Last Updated:** 2025-11-21
**Status:** ✅ Production Ready

---

## Executive Summary

The **TestIO MCP Server** is an AI-first integration layer that provides Model Context Protocol (MCP) access to TestIO's Customer API. It enables non-developer stakeholders (CSMs, PMs, QA leads) to query test status, bug information, and activity metrics through AI tools like Claude and Cursor.

**Key Value Proposition:**
- Query test data conversationally through AI assistants
- Generate executive bug reports without manual data extraction
- Monitor testing activity and data freshness
- Access TestIO data from multiple AI clients simultaneously

---

## Project Purpose

### Problem Statement

TestIO customers need quick access to test status, bug metrics, and activity data, but:
- Customer API requires technical knowledge (HTTP, JSON, authentication)
- Manual data extraction is time-consuming and error-prone
- Non-technical stakeholders (CSMs, PMs) lack direct access to insights

### Solution

An MCP server that:
1. **Wraps TestIO Customer API** with AI-friendly tools
2. **Caches data locally** (SQLite) for fast queries (~10ms)
3. **Provides structured responses** optimized for AI consumption
4. **Supports multiple clients** (Claude, Cursor, web apps) simultaneously

---

## Technology Stack

### Core Technologies

- **Language:** Python 3.12+
- **MCP Framework:** FastMCP (Model Context Protocol server framework)
- **Web Framework:** FastAPI (hybrid MCP + REST server)
- **HTTP Client:** httpx (async HTTP with connection pooling)
- **Database:** SQLite with WAL mode (concurrent reads)
- **Configuration:** Pydantic Settings (type-safe configuration)
- **Testing:** pytest, pytest-asyncio (448+ tests, >90% coverage)
- **Code Quality:** mypy (strict), ruff (linting), pre-commit hooks

### Architecture Pattern

**Hybrid Server Architecture:**
- **MCP Protocol:** JSON-RPC over stdio or HTTP
- **REST API:** HTTP/JSON for web apps, curl, Postman
- **Shared Resources:** Single lifespan manager, shared database, shared API client
- **Service Layer:** Framework-agnostic business logic (reusable across MCP and REST)

---

## System Architecture

### High-Level Components

```
AI Clients (Claude, Cursor) + Web Apps
         ↓
Hybrid Server (FastAPI + FastMCP)
    ├── MCP Tools (8 tools)
    ├── REST API (8 endpoints)
    └── Service Layer (3 services)
         ├── TestIOClient (HTTP wrapper)
         └── PersistentCache (SQLite database)
              ↓
         TestIO Customer API
```

### Data Flow

**SQLite-First Architecture:**
1. Query local SQLite database (fast, ~10ms)
2. If not found, fallback to API (rare)
3. Store in database for future queries
4. Background sync keeps data fresh (every 5 minutes)

**Benefits:**
- Fast queries (no network latency)
- Persistent data (survives restarts)
- Reduced API load (fewer requests)
- Offline capability (cached data available)

---

## Key Features

### MCP Tools (8 Tools)

1. **health_check** - API authentication verification
2. **get_test_status** - Test details with bug summary
3. **list_products** - Product listing with filtering
4. **list_tests** - Test listing with pagination
5. **generate_ebr_report** - Evidence-based reporting (with file export)
6. **get_database_stats** - Database size and sync status
7. **get_problematic_tests** - Failed sync tracking (500 errors)
8. **get_sync_history** - Sync event history and statistics

### REST API (8 Endpoints)

- `GET /health` - Health check with database stats
- `GET /api/tests/{id}` - Get test status
- `GET /api/products` - List products
- `GET /api/products/{id}/tests` - List tests for product
- `POST /api/reports/ebr` - Generate EBR report
- `GET /api/database/stats` - Database statistics
- `GET /api/sync/history` - Sync event history
- `GET /api/sync/problematic` - Problematic tests

### Local Data Store (SQLite)

**5 Tables:**
- `products` - All products accessible to customer
- `tests` - Exploratory tests for each product
- `bugs` - Bugs associated with tests
- `sync_metadata` - Track last sync timestamp per product
- `sync_events` - Sync operation history and statistics

**Sync Strategy:**
- **Initial sync:** On server startup (non-blocking)
- **Background sync:** Every 5 minutes (configurable)
- **Incremental sync:** Fetch only new/changed data
- **Manual sync:** Via CLI: `testio-mcp sync`

---

## Current Development Status

### Completed Epics

- ✅ **Epic-001:** TestIO MCP MVP (8 MCP tools, basic functionality)
- ✅ **Epic-002:** Local Data Store Foundation (SQLite database, repositories)
- ✅ **Epic-003:** Automated Executive Testing Reports (EBR reporting with file export)
- ✅ **Epic-004:** Production Architecture (hybrid server, REST API, deployment)

### Active Epics

- 🔄 **Epic-006:** ORM Refactor (SQLModel + Alembic migration)
  - **Status:** Implementation-ready (7 stories, all vertically sliced)
  - **Goal:** Transition from raw SQL to SQLModel ORM with Alembic migrations
  - **Stories:** 030-034B (Infrastructure → Models → Repositories → Services → Migration)
  - **Estimated Effort:** 18-22 hours

### Planned Epics

- 📋 **Epic-005:** Data Enhancement and Serving (Features, user stories, metadata)
  - **Status:** Blocked by Epic-006 completion
  - **Goal:** Add Features and User Stories as first-class entities
  - **Stories:** 035A-037 (5 active stories, STORY-038 deferred)
  - **Estimated Effort:** 17-21 hours

---

## Deployment Architecture

### stdio Mode (Single Client)

**Use Case:** One MCP client (Claude Code OR Cursor, not both)

```
Claude Desktop / Cursor
         ↓ (stdio)
TestIO MCP Server (Python process)
         ↓ (HTTPS)
    TestIO API
```

**Characteristics:**
- Single-user, single-client deployment
- No network exposure (stdio = inter-process communication)
- Configuration via `.env` file
- SQLite database: `~/.testio-mcp/cache.db`

### HTTP Mode (Multiple Clients) - RECOMMENDED

**Use Case:** Multiple MCP clients (Claude + Cursor + Inspector)

```
Claude Code + Cursor + Inspector
         ↓ (HTTP)
TestIO MCP Server (localhost:8080)
         ↓ (HTTPS)
    TestIO API
```

**Characteristics:**
- Multi-client deployment (all clients share same server)
- HTTP on localhost only (127.0.0.1:8080)
- No database lock conflicts (single process)
- No redundant API calls (single background sync)
- Logs visible in terminal

**Start server:**
```bash
uv run python -m testio_mcp serve --transport http --port 8080
```

---

## Quality Metrics

### Test Coverage

- **Total Tests:** 448+ tests
- **Coverage:** >90%
- **Test Types:**
  - Unit tests (repositories, services, client)
  - Integration tests (MCP tools, REST endpoints)
  - End-to-end tests (full request flow)

### Performance Targets

- **Response Time:** 99% of queries < 5 seconds (P99 latency)
- **Local Queries:** ~10ms (SQLite-first architecture)
- **Error Rate:** Monitored via `get_sync_history` tool

### Code Quality

- **Type Checking:** mypy --strict (100% coverage)
- **Linting:** ruff (zero violations)
- **Pre-commit Hooks:** Automated quality checks
- **Code Review:** Required for all changes

---

## Security Considerations

### Authentication

- **Method:** Token-based (`Authorization: Token <token>`)
- **Storage:** Environment variable (`TESTIO_CUSTOMER_API_TOKEN`)
- **Rotation:** Manual (no automated rotation in MVP)

### Input Validation

- All tool inputs validated via Pydantic
- Type checking enforced (str, int, enum)
- Range validation (page_size: 1-1000)

### Output Sanitization

- MCP protocol handles JSON encoding (prevents injection)
- AI clients (Claude) sanitize for display
- No direct HTML rendering in MVP

---

## Documentation Structure

### Architecture Documentation

- **[ARCHITECTURE.md](./architecture/ARCHITECTURE.md)** - Complete system architecture
- **[TECH-STACK.md](./architecture/TECH-STACK.md)** - Technology decisions
- **[MCP.md](./architecture/MCP.md)** - MCP tool design patterns
- **[SERVICE_LAYER_SUMMARY.md](./architecture/SERVICE_LAYER_SUMMARY.md)** - Service layer architecture

### Specialized Guides

- **[PERFORMANCE.md](./architecture/PERFORMANCE.md)** - Performance optimization
- **[SECURITY.md](./architecture/SECURITY.md)** - Security best practices
- **[TESTING.md](./architecture/TESTING.md)** - Testing strategy
- **[CODING-STANDARDS.md](./architecture/CODING-STANDARDS.md)** - Code quality standards

### Architecture Decision Records (ADRs)

11 ADRs documenting key architectural decisions:
- ADR-001: API Client Dependency Injection
- ADR-002: Concurrency Limits
- ADR-003: Pagination Strategy
- ADR-004: Cache Strategy (MVP)
- ADR-006: Service Layer Pattern
- ADR-007: FastMCP Context Injection
- ... and more

---

## Getting Started

### For Developers

1. **Read:** [ARCHITECTURE.md](./architecture/ARCHITECTURE.md) - Understand system design
2. **Review:** [Epic-006](./epics/epic-006-orm-refactor.md) - Current work scope
3. **Check:** [CODING-STANDARDS.md](./architecture/CODING-STANDARDS.md) - Code quality requirements
4. **Test:** [TESTING.md](./architecture/TESTING.md) - Testing strategy

### For AI Agents

1. **Start:** [index.md](./index.md) - Master documentation index
2. **Navigate:** Use index to find relevant sections
3. **Read:** Specific architecture docs as needed
4. **Reference:** ADRs for architectural decisions

### For Product/PM

1. **Review:** Epic files for feature sets and status
2. **Check:** Planning docs for future roadmap
3. **Validate:** Validation reports for epic readiness

---

## Project Statistics

- **Lines of Code:** ~15,000+ (Python)
- **Test Files:** 50+ test files
- **Documentation Files:** 95+ markdown files
- **Architecture Decisions:** 11 ADRs
- **Epics Completed:** 4
- **Epics In Progress:** 1 (Epic-006)
- **Epics Planned:** 1 (Epic-005)

---

## Contact and Resources

### Repository

- **GitHub:** (Add repository URL)
- **Documentation:** `docs/` directory
- **Issues:** GitHub Issues

### Key Stakeholders

- **Development Team:** (Add team contacts)
- **Product Owner:** (Add PO contact)
- **Customer Success:** (Add CSM contacts)

---

## Quick Links

- **Current Work:** [Epic-006: ORM Refactor](./epics/epic-006-orm-refactor.md)
- **System Overview:** [ARCHITECTURE.md](./architecture/ARCHITECTURE.md)
- **Code Standards:** [CODING-STANDARDS.md](./architecture/CODING-STANDARDS.md)
- **Testing Guide:** [TESTING.md](./architecture/TESTING.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

**Last Updated:** 2025-11-21
**Generated By:** document-project workflow (Quick scan)
**Maintained By:** Development Team
