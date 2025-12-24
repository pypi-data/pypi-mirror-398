# Authentication Strategy - Current MVP Implementation

**Date:** 2025-11-20 (Updated from multi-phase planning)
**Status:** ✅ Current Implementation (MVP - Phase 1)
**Related:** ADR-006 (Service Layer), SERVICE_LAYER_SUMMARY.md, ARCHITECTURE.md v2.0

---

## Executive Summary

This document describes the **current authentication implementation** for the TestIO MCP Server MVP. The system uses single-tenant, server-side token authentication with stdio transport.

**Current Model:** Single TestIO API token in `.env`, no user authentication, local process only.

**Future Planning:** See [AUTH_STRATEGY_FUTURE.md](../planning/AUTH_STRATEGY_FUTURE.md) for multi-tenant architecture planning.

---

## Current State (MVP - Phase 1)

### Authentication Model

**Transport:** stdio (default) or HTTP (localhost:8080)
**User Auth:** None (local process only)
**API Auth:** Single server-side TestIO API token in `.env`
**Tenant Model:** Single tenant (one TestIO customer account)

### Architecture

```
MCP Client (Claude/Cursor) → stdio or HTTP → MCP Server
  ↓
Server Context (lifespan)
  ├─ TestIOClient (single token from .env)
  └─ PersistentCache (SQLite database, single customer_id)
  ↓
Tools → Services → TestIO API
```

---

## Security Posture (SQLite-First Architecture)

### Server Initialization

```python
# server.py - Lifespan handler
@asynccontextmanager
async def lifespan(server: FastMCP):
    """Manage client and cache lifecycle."""

    # Initialize API client with server token
    async with TestIOClient(
        base_url=settings.TESTIO_CUSTOMER_API_BASE_URL,
        api_token=settings.TESTIO_CUSTOMER_API_TOKEN,  # From .env
        max_concurrent_requests=settings.MAX_CONCURRENT_API_REQUESTS,
    ) as client:
        # Initialize PersistentCache (SQLite database)
        cache = PersistentCache(
            db_path=settings.TESTIO_DB_PATH,
            customer_id=settings.TESTIO_CUSTOMER_ID,
            customer_name=settings.TESTIO_CUSTOMER_NAME,
        )
        await cache.initialize()

        # Create repositories
        test_repo = TestRepository(cache)
        bug_repo = BugRepository(cache)
        product_repo = ProductRepository(cache)

        # Inject into server context
        server.context["testio_client"] = client  # Shared singleton
        server.context["cache"] = cache  # PersistentCache (SQLite)
        server.context["test_repository"] = test_repo
        server.context["bug_repository"] = bug_repo
        server.context["product_repository"] = product_repo

        # Server runs here
        yield

        # Cleanup (cache closed, client closed by __aexit__)
```

### Configuration

```bash
# .env file (required)
TESTIO_CUSTOMER_API_TOKEN=your-token-here
TESTIO_CUSTOMER_API_BASE_URL=https://api.test.io/customer/v2
TESTIO_CUSTOMER_NAME=YourCompanyName

# Local Data Store (SQLite)
TESTIO_DB_PATH=~/.testio-mcp/cache.db
TESTIO_CUSTOMER_ID=1  # Default: 1 (single-tenant)

# Optional: Product filtering
TESTIO_PRODUCT_IDS=598,1024  # Comma-separated product IDs to sync
```

---

## Security Measures (MVP)

### 1. Token Storage

**Current Implementation:**
- ✅ Token stored in `.env` file with restrictive permissions (600)
- ✅ Token not logged in telemetry or crash dumps
- ✅ Token sanitization in httpx event hooks (SEC-002)

**Setup:**
```bash
# Create .env file
touch .env
chmod 600 .env

# Add token
echo "TESTIO_CUSTOMER_API_TOKEN=your-token-here" >> .env
```

### 2. Transport Security

**Current Implementation:**
- ✅ stdio transport (default, no network exposure)
- ✅ HTTP transport (optional, localhost only by default)
- ✅ Local process communication (no remote access)

**Rationale:** stdio transport eliminates network attack surface. HTTP mode available for multi-client scenarios (localhost:8080).

### 3. Token Sanitization

**Implementation:**
```python
# client.py - Token sanitization in logs
class TestIOClient:
    def __init__(self, base_url: str, api_token: str, ...):
        self._api_token = api_token  # Private attribute

        # Setup httpx client with sanitized logging
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Token {api_token}"},
            event_hooks={
                "request": [self._sanitize_request_log],
                "response": [self._sanitize_response_log],
            }
        )

    async def _sanitize_request_log(self, request):
        """Remove token from request logs."""
        # Token never appears in logs
        pass
```

### 4. Runtime Guards (Planned)

**Future Enhancement:**
```python
# src/testio_mcp/security/runtime_guards.py

import sys
import os

def validate_runtime_environment():
    """Security checks before server starts."""

    # 1. Check stdout is not redirected to unknown pipe
    if not sys.stdout.isatty():
        # Allow known supervisors (systemd, docker logs)
        if not os.getenv("ALLOW_REDIRECTED_OUTPUT"):
            raise RuntimeError(
                "Security: stdout redirected to unknown pipe. "
                "Set ALLOW_REDIRECTED_OUTPUT=1 to override."
            )

    # 2. Check .env permissions
    env_file = ".env"
    if os.path.exists(env_file):
        stat_info = os.stat(env_file)
        if stat_info.st_mode & 0o077:  # World or group readable
            raise RuntimeError(
                f"Security: {env_file} has insecure permissions. "
                "Run: chmod 600 .env"
            )

    return True

# server.py
if __name__ == "__main__":
    validate_runtime_environment()
    # Start server...
```

---

## Incident Response Plan

### Token Compromise Suspected

**Immediate Actions:**
1. **Stop server** - Kill MCP server process immediately
2. **Revoke token** - Log into TestIO portal, revoke compromised token
3. **Generate new token** - Create new API token in TestIO portal
4. **Update .env** - Replace old token with new token
5. **Clear cache** - Delete SQLite database (`rm ~/.testio-mcp/cache.db`)
6. **Restart server** - Start MCP server with new token
7. **Notify TestIO** - Contact TestIO support if compromise confirmed

**Post-Incident:**
1. Review logs for unauthorized access
2. Audit file permissions (`.env` should be 600)
3. Check for unexpected processes accessing `.env`
4. Document incident timeline and root cause

---

## Tool Layer Integration

### Service Creation Pattern

```python
# tools/get_test_status_tool.py
from fastmcp import Context
from testio_mcp.utilities import get_service

@mcp.tool()
async def get_test_status(test_id: int, ctx: Context) -> dict:
    """Get comprehensive status of a single exploratory test."""

    # Extract dependencies from context (injected by lifespan)
    service = get_service(ctx, TestService)

    # Service receives client + repositories via dependency injection
    # No authentication logic in tools - handled at server level
    return await service.get_test_status(test_id)
```

**Key Points:**
- ✅ Tools don't handle authentication (server-level concern)
- ✅ Services receive pre-authenticated client via DI
- ✅ No token passing between layers (singleton client)

---

## Database Multi-Tenancy (Future-Ready)

### Current Implementation

**Single Tenant:**
```python
# All queries use single customer_id from config
cache = PersistentCache(customer_id=1)  # From TESTIO_CUSTOMER_ID
test_repo = TestRepository(cache)

# Queries don't filter by customer_id (single tenant)
SELECT * FROM tests WHERE id = ?;
```

**Schema (Multi-Tenant Ready):**
```sql
CREATE TABLE tests (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,  -- Multi-tenant field (exists but not used in MVP)
    product_id INTEGER NOT NULL,
    title TEXT,
    status TEXT,
    -- ... other fields
);
```

**Future Migration:**
```python
# Phase 3: Per-user customer_id from auth
user = auth_service.validate_token(jwt)
cache = cache_factory.get_cache(customer_id=user.tenant_id)
test_repo = TestRepository(cache)

# Queries filter by customer_id automatically
SELECT * FROM tests WHERE customer_id = ? AND id = ?;
```

**Benefits:**
- ✅ Schema already supports multi-tenancy (`customer_id` column exists)
- ✅ No migration needed for database structure
- ✅ Only need to add `customer_id` filter to queries

---

## Security Checklist

### MVP (Phase 1) - Current Status

- [x] `.env` file with restrictive permissions (600)
- [x] Token not logged in telemetry or crash dumps
- [x] Token sanitization in httpx event hooks (SEC-002)
- [x] No network exposure (stdio only)
- [ ] Runtime guard (stdout redirect check) - Planned
- [ ] Incident response plan documented - ✅ Documented above

### Deployment Checklist

Before deploying MCP server:
- [ ] Verify `.env` permissions: `chmod 600 .env`
- [ ] Verify token is valid (test with `uvx testio-mcp sync --status`)
- [ ] Verify SQLite database path is writable
- [ ] Verify no other processes can access `.env`
- [ ] Document token rotation schedule (manual for MVP)

---

## Future Planning

For multi-tenant authentication planning (Phases 2-4), see:
- **[AUTH_STRATEGY_FUTURE.md](../planning/AUTH_STRATEGY_FUTURE.md)** - Multi-tenant architecture planning
- **[STORY-010](../stories/story-010-multi-tenant-architecture.md)** - Multi-tenant implementation story (not yet prioritized)

**Future Phases:**
- **Phase 2:** Multi-user (same tenant) - Add user auth, RBAC, audit logging
- **Phase 3:** Multi-tenant - Per-user tokens, encrypted storage, client factory

**Service Layer Impact:** ✅ **No changes required** - Services remain auth-agnostic, only tool layer changes.

---

## References

- **ADR-006:** [Service Layer Pattern](adrs/ADR-006-service-layer-pattern.md) - Business logic separation
- **SEC-002:** [Token Sanitization](SECURITY.md#token-management) - Security implementation
- **ARCHITECTURE.md:** [Local Data Store Strategy](ARCHITECTURE.md#local-data-store-strategy)
- **Future Planning:** [AUTH_STRATEGY_FUTURE.md](../planning/AUTH_STRATEGY_FUTURE.md)

---

**Document Status:** ✅ Current Implementation (MVP)
**Last Updated:** 2025-12-03
**Author:** Winston (Architect)
**Changes:** Updated for HTTP transport support (v1.1)
