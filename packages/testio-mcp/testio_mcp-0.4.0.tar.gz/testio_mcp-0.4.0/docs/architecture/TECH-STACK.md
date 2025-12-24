# Technology Stack

**Version:** 1.2
**Last Updated:** 2025-12-03
**Status:** Active

---

## Table of Contents

1. [Core Stack](#core-stack)
2. [Development Tools](#development-tools)
3. [Testing Framework](#testing-framework)
4. [Security & Quality](#security--quality)
5. [Deployment & Infrastructure](#deployment--infrastructure)
6. [Technology Decisions](#technology-decisions)

---

## Core Stack

### Language & Runtime

- **Python 3.12+**
  - Rationale: Modern type hints, performance improvements, async/await maturity
  - Minimum version: 3.12 (required for improved error messages, typing features)

### MCP Framework

- **FastMCP**
  - Purpose: Model Context Protocol server framework
  - Why FastMCP: Lightweight, async-native, good type support
  - Protocol: JSON-RPC over stdio (MVP) / SSE (future)

### HTTP Client

- **httpx**
  - Purpose: Async HTTP client for TestIO API integration
  - Features: Connection pooling, timeout management, retry logic
  - Why not requests: Requires async support for concurrent API calls

### Configuration Management

- **Pydantic Settings**
  - Purpose: Type-safe configuration from environment variables
  - Features: Validation, type coercion, .env file support
  - Integration: Settings injected via dependency injection pattern

### Data Storage

- **SQLite** (via aiosqlite)
  - Purpose: Local persistent data store for tests, products, bugs
  - Features: ACID transactions, WAL mode for concurrent reads, schema versioning
  - Performance: ~10ms queries at our scale (700+ tests)
  - Database path: `~/.testio-mcp/cache.db` (configurable)
  - Why SQLite: Zero infrastructure cost, fast local queries, persistence across restarts

- **aiosqlite**
  - Purpose: Async SQLite adapter for Python
  - Features: Async context managers, connection pooling
  - Integration: Used by PersistentCache and repository layer

- **SQLModel + SQLAlchemy 2.0**
  - Purpose: ORM layer for type-safe database operations
  - Features: Pydantic integration, async support, declarative models
  - Integration: Repository pattern, Alembic migrations

- **Alembic**
  - Purpose: Database schema migration management
  - Strategy: Frozen baseline (ADR-016), single-path migrations
  - Testing: pytest-alembic for migration consistency checks

---

## Development Tools

### Package Management

- **uv** (recommended)
  - Purpose: Fast Python package installer and resolver
  - Usage: `uv run python`, `uv pip install`
  - Alternative: pip/pip-tools for environments without uv

### Code Quality

- **mypy**
  - Purpose: Static type checking
  - Mode: Strict (no type: ignore allowed without justification)
  - Configuration: Enforces type hints on all public functions

- **ruff**
  - Purpose: Fast linting and formatting
  - Replaces: black, isort, flake8, pylint
  - Features: Auto-fixing, import sorting, PEP 8 compliance

### Pre-commit Hooks

- **pre-commit**
  - Purpose: Automated code quality checks before commits
  - Hooks: ruff, mypy, detect-secrets, trailing-whitespace
  - Configuration: `.pre-commit-config.yaml`

---

## Testing Framework

### Test Runner

- **pytest**
  - Purpose: Unit, integration, and functional testing
  - Plugins: pytest-asyncio (async test support)
  - Coverage: pytest-cov for code coverage reports

### Async Testing

- **pytest-asyncio**
  - Purpose: Native async test support
  - Features: Automatic event loop management, async fixtures
  - Usage: `@pytest.mark.asyncio` decorator

### Mocking & Fixtures

- **unittest.mock** (stdlib)
  - Purpose: Mock external dependencies (API calls, caches)
  - Patterns: AsyncMock for async functions
  - Test isolation: Each test uses fresh mock instances

---

## Security & Quality

### Secret Detection

- **detect-secrets**
  - Purpose: Prevent committing API tokens, credentials
  - Integration: Pre-commit hook + CI/CD pipeline
  - Baseline: `.secrets.baseline` for allowed patterns

### Dependency Scanning

- **pip-audit** (planned)
  - Purpose: Scan for known vulnerabilities in dependencies
  - Frequency: Weekly automated scans + on dependency updates

### Environment Security

- **python-dotenv** (via Pydantic Settings)
  - Purpose: Load `.env` files with restrictive permissions
  - Security: `.env` excluded from git, file permissions enforced (600)

---

## Deployment & Infrastructure

### Current (MVP - Phase 1)

- **Transport:** stdio (single client) or HTTP (multiple clients)
  - stdio mode: Default, backward compatible, one MCP client
  - HTTP mode: Port 8080, multiple concurrent clients (Claude Code + Cursor + Inspector)
  - Benefits of HTTP: No database lock conflicts, single background sync, visible logs
- **Process Model:** Single process (HTTP mode) or per-client (stdio mode)
- **State:** SQLite database (`~/.testio-mcp/cache.db`) with persistence
  - Background sync: Every hour (configurable via TESTIO_REFRESH_INTERVAL_SECONDS)
  - Incremental sync: Only fetches new/changed data
  - WAL mode: Concurrent reads during background writes
- **Auth:** Single API token in `.env`

### Future (Multi-Tenant - Phase 3)

- **Transport:** Server-Sent Events (SSE) over HTTP
- **Infrastructure:** Supabase Edge Functions (planned)
  - Runtime: Deno with Python compatibility layer
  - Scaling: Auto-scaling based on request volume
  - Region: US-East-1 (TestIO API proximity)

- **State Management:**
  - Cache: Supabase (PostgreSQL + pgvector for semantic search)
  - Session: JWT tokens for user authentication
  - Secrets: Supabase Vault for encrypted token storage

---

## Technology Decisions

### Why FastMCP over alternatives?

- **vs. Custom JSON-RPC:** FastMCP handles protocol boilerplate
- **vs. REST API:** MCP provides structured tool/resource model
- **vs. GraphQL:** Simpler for read-heavy, AI-optimized responses

### Why httpx over requests?

- **Async-native:** Required for concurrent API calls without blocking
- **Connection pooling:** Reuse TCP connections for better performance
- **Modern API:** Better timeout/retry handling than aiohttp

### Why SQLite over Redis/PostgreSQL?

- **Zero infrastructure:** No external database server required
- **Persistence:** Data survives server restarts (unlike in-memory cache)
- **Performance:** ~10ms queries at our scale (700+ tests), WAL mode for concurrent reads
- **Simplicity:** Single file database, no connection strings, automatic backups
- **Multi-tenancy ready:** `customer_id` column for database-level isolation
- **Cost:** Zero infrastructure cost
- **Future migration:** Repository pattern abstracts data access, easy swap to PostgreSQL if needed

### Why Pydantic Settings over os.environ?

- **Type safety:** Automatic type coercion and validation
- **Documentation:** Settings class serves as config reference
- **Error handling:** Clear errors for missing/invalid config

### Why mypy strict mode?

- **Early error detection:** Catch type errors before runtime
- **Better IDE support:** Autocomplete, refactoring tools
- **Team alignment:** Forces explicit types, improves code readability

### Why ruff over black/flake8?

- **Performance:** 10-100x faster than black/flake8 combined
- **All-in-one:** Replaces 5+ tools with single binary
- **Auto-fixing:** Saves developer time on formatting issues

### Why HTTP transport mode in addition to stdio?

- **Multiple clients:** Run Claude Code + Cursor + MCP Inspector simultaneously
- **Database lock prevention:** Single server process = no SQLite lock conflicts
- **Efficient sync:** One background sync instead of multiple per client
- **Debugging:** Logs visible in terminal (not captured by stdio parent process)
- **Backward compatibility:** stdio mode still default, HTTP opt-in

### Why repository pattern?

- **Clean data access:** Separation between business logic (services) and data access (repositories)
- **Testability:** Mock repositories in tests without SQLite database setup
- **Multi-tenancy:** Database-level isolation via `customer_id` filtering in queries
- **Migration flexibility:** Easy swap from SQLite → PostgreSQL without changing services
- **Single responsibility:** Repositories handle SQL, services handle business logic

---

## Version History

- **v1.2 (2025-12-03):** Added SQLModel/SQLAlchemy 2.0 and Alembic to stack, corrected sync interval (1 hour)
- **v1.1 (2025-11-18):** Updated for SQLite-first architecture (STORY-021, STORY-023 refactoring)
  - Added SQLite and aiosqlite to core stack
  - Updated deployment: In-memory → SQLite persistence
  - Added HTTP transport mode (in addition to stdio)
  - Replaced "Why in-memory cache" → "Why SQLite over Redis/PostgreSQL"
  - Added "Why HTTP transport mode?" and "Why repository pattern?" sections
  - Updated state management: Background sync, WAL mode, incremental sync
- **v1.0 (2025-11-04):** Initial technology stack documentation
