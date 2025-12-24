---
story_id: STORY-025b
epic_id: EPIC-002
title: HTTP Download Service with MCP Resources for EBR Reports
status: approved
created: 2025-01-19
estimate: 2-3 days
assignee: dev
dependencies: [STORY-025, STORY-023f]
priority: high
parent_design: ChatGPT 5.1 PRD - Production-Grade Artifact Service
---

## Status
Approved - Ready for Implementation (after STORY-023f)

## Story
**As a** CSM, QA Lead, or automated agent
**I want** to download large EBR reports via HTTP with secure, time-limited URLs
**So that** I can retrieve reports without filesystem access, share them securely, and support both human and programmatic access patterns

## Background

STORY-025 provides basic file export to `~/.testio-mcp/reports/` with filesystem paths in responses. This works for local development but has limitations:

**Security Concerns:**
- ❌ Exposes filesystem paths in API responses
- ❌ No access control (anyone with path can read file)
- ❌ No expiration (files persist indefinitely)
- ❌ Unsuitable for multi-user or shared environments

**Scale Concerns:**
- ❌ No cleanup mechanism (disk usage grows unbounded)
- ❌ No usage tracking (can't see who downloads what)
- ❌ No MCP resource support (not leveraging MCP capabilities)

**Solution: Production-Grade Artifact Service**

Based on ChatGPT 5.1 PRD recommendations, implement:
- ✅ Capability URLs with cryptographic tokens (W3C best practice)
- ✅ Short-lived access (15-30 min TTL, OAuth-style)
- ✅ SQLite-based artifact tracking (durable metadata)
- ✅ HTTP download endpoint (no filesystem exposure)
- ✅ MCP resource registry (future-proof for resource-aware clients)
- ✅ Background cleanup (TTL-based garbage collection)

## Problem Solved

**Current (STORY-025):**
```
generate_ebr_report(output_file="report.json")
→ Response: {
    "file_path": "~/.testio-mcp/reports/report.json",
    "summary": {...}
  }
→ User must access filesystem directly
→ No expiration, no access control
→ Works only for local development
```

**After (STORY-025b):**
```
generate_ebr_report(output_mode="file")
→ Response: {
    "mode": "file",
    "summary": {...},
    "download": {
      "url": "http://127.0.0.1:8080/download/abc123xyz",
      "expires_in_seconds": 1800
    },
    "resource": {
      "uri": "report://ebr/rep_456",
      "expires_at": "2025-01-19T14:30:00Z"
    }
  }
→ User clicks HTTP link OR agent fetches MCP resource
→ Token expires after 30 min
→ Works for local AND multi-user deployments
```

## Acceptance Criteria

### AC1: SQLite Artifact Tracking Schema

**Add to `src/testio_mcp/schema.py`:**

**Schema Definition (add to `initialize_schema()`):**

```python
# Table 1: Report artifacts (durable metadata)
await db.execute(
    """
    CREATE TABLE IF NOT EXISTS report_artifacts (
        id TEXT PRIMARY KEY,             -- UUID
        customer_id INTEGER NOT NULL,    -- Multi-tenant isolation
        product_id INTEGER NOT NULL,
        parameters_json TEXT NOT NULL,   -- Reproducibility (date filters, statuses)
        file_path TEXT NOT NULL,         -- Local filesystem path
        format TEXT NOT NULL,             -- "json" (MVP), "csv" (future)
        size_bytes INTEGER NOT NULL,
        created_at TEXT NOT NULL,         -- ISO8601 UTC (YYYY-MM-DDTHH:MM:SSZ)
        expires_at TEXT NOT NULL,         -- ISO8601 UTC
        status TEXT NOT NULL              -- "ready", "deleted", "error"
    )
    """
)

# Table 2: Download tokens (capability URLs)
await db.execute(
    """
    CREATE TABLE IF NOT EXISTS download_tokens (
        token TEXT PRIMARY KEY,           -- Cryptographic random (256 bits)
        customer_id INTEGER NOT NULL,     -- Multi-tenant isolation
        report_id TEXT NOT NULL,
        created_at TEXT NOT NULL,          -- ISO8601 UTC
        expires_at TEXT NOT NULL,          -- ISO8601 UTC
        one_time_use INTEGER DEFAULT 0,   -- Boolean (0=reusable, 1=single-use)
        usage_count INTEGER DEFAULT 0,
        last_accessed_at TEXT,            -- NULL until first access
        FOREIGN KEY (report_id) REFERENCES report_artifacts(id) ON DELETE CASCADE
    )
    """
)

# Table 3: MCP resources (optional, for resource-aware clients)
await db.execute(
    """
    CREATE TABLE IF NOT EXISTS mcp_resources (
        uri TEXT PRIMARY KEY,             -- "report://ebr/{report_id}"
        customer_id INTEGER NOT NULL,     -- Multi-tenant isolation
        report_id TEXT NOT NULL,
        mime TEXT NOT NULL,               -- "application/json"
        size_bytes INTEGER NOT NULL,
        created_at TEXT NOT NULL,          -- ISO8601 UTC
        expires_at TEXT NOT NULL,          -- ISO8601 UTC
        FOREIGN KEY (report_id) REFERENCES report_artifacts(id) ON DELETE CASCADE
    )
    """
)

# Indexes for performance (composite indexes for customer_id + other fields)
await db.execute(
    "CREATE INDEX IF NOT EXISTS idx_artifacts_customer_product "
    "ON report_artifacts (customer_id, product_id)"
)
await db.execute(
    "CREATE INDEX IF NOT EXISTS idx_artifacts_customer_expires "
    "ON report_artifacts (customer_id, expires_at)"
)
await db.execute(
    "CREATE INDEX IF NOT EXISTS idx_tokens_customer_expires "
    "ON download_tokens (customer_id, expires_at)"
)
await db.execute(
    "CREATE INDEX IF NOT EXISTS idx_tokens_report "
    "ON download_tokens (report_id)"
)
await db.execute(
    "CREATE INDEX IF NOT EXISTS idx_resources_customer_report "
    "ON mcp_resources (customer_id, report_id)"
)
```

**Migration Function (add to `schema.py`):**

```python
async def migrate_to_v5(db: "aiosqlite.Connection") -> None:
    """Add artifact tracking tables for download service.

    Migration: Add report_artifacts, download_tokens, and mcp_resources tables
    for STORY-025b (HTTP Download Service).

    Args:
        db: Active aiosqlite connection
    """
    current_version = await get_schema_version(db)
    if current_version >= 5:
        return  # Already migrated

    logger.info("Migrating schema from v4 to v5: Adding artifact tracking tables")

    # Create all three tables (already in initialize_schema for new DBs)
    # Just update version for existing databases
    await set_schema_version(db, 5)
    logger.info("Migrated to schema version 5: Added artifact tracking tables")
```

**Implementation:**
- [ ] Add table creation to `initialize_schema()` in `src/testio_mcp/schema.py`
- [ ] Add `migrate_to_v5()` function to `src/testio_mcp/schema.py`
- [ ] Update `CURRENT_SCHEMA_VERSION = 4` → `5`
- [ ] Add migration call in cache initialization (after `migrate_to_v4()`)
- [ ] All timestamps stored as UTC ISO8601 strings (`YYYY-MM-DDTHH:MM:SSZ`)
- [ ] Test migration on existing databases

### AC2: Artifact Repository

**Create `src/testio_mcp/repositories/artifact_repository.py`:**

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets
import uuid

@dataclass
class ReportArtifact:
    """Report artifact metadata."""
    id: str
    product_id: int
    parameters_json: str
    file_path: str
    format: str
    size_bytes: int
    created_at: datetime
    expires_at: datetime
    status: str

@dataclass
class DownloadToken:
    """Download token for capability URLs."""
    token: str
    report_id: str
    created_at: datetime
    expires_at: datetime
    one_time_use: bool
    usage_count: int
    last_accessed_at: datetime | None

@dataclass
class MCPResource:
    """MCP resource handle."""
    uri: str
    report_id: str
    mime: str
    size_bytes: int
    created_at: datetime
    expires_at: datetime

class ArtifactRepository:
    """Repository for artifact storage and retrieval.

    Multi-tenant aware: all operations scoped by customer_id.
    Uses aiosqlite for async database operations.
    """

    def __init__(self, db: "aiosqlite.Connection", customer_id: int):
        """Initialize repository.

        Args:
            db: Async SQLite connection
            customer_id: Customer ID for multi-tenant isolation
        """
        self.db = db
        self.customer_id = customer_id

    async def create_artifact(
        self,
        product_id: int,
        parameters: dict,
        file_path: str,
        format: str,
        size_bytes: int,
        ttl_seconds: int = 1800,  # 30 min default
    ) -> ReportArtifact:
        """Create artifact record with UUID.

        Args:
            product_id: Product ID
            parameters: Request parameters for reproducibility
            file_path: Absolute path to artifact file
            format: File format ("json", "csv")
            size_bytes: File size in bytes
            ttl_seconds: Time-to-live in seconds

        Returns:
            Created ReportArtifact
        """
        artifact_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        await self.db.execute(
            """
            INSERT INTO report_artifacts (
                id, customer_id, product_id, parameters_json,
                file_path, format, size_bytes,
                created_at, expires_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ready')
            """,
            (
                artifact_id,
                self.customer_id,
                product_id,
                json.dumps(parameters),
                file_path,
                format,
                size_bytes,
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        await self.db.commit()

        return ReportArtifact(
            id=artifact_id,
            product_id=product_id,
            parameters_json=json.dumps(parameters),
            file_path=file_path,
            format=format,
            size_bytes=size_bytes,
            created_at=now,
            expires_at=expires_at,
            status="ready",
        )

    async def create_download_token(
        self,
        report_id: str,
        ttl_seconds: int = 1800,
        one_time_use: bool = False,
    ) -> DownloadToken:
        """Generate cryptographic token (256-bit entropy).

        Args:
            report_id: Artifact ID
            ttl_seconds: Token validity period
            one_time_use: Delete token after first use

        Returns:
            Created DownloadToken

        Security:
            Uses secrets.token_urlsafe(32) for 256 bits of entropy.
            Tokens are opaque and cannot be guessed or enumerated.
        """
        token = secrets.token_urlsafe(32)  # 256 bits
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        await self.db.execute(
            """
            INSERT INTO download_tokens (
                token, customer_id, report_id,
                created_at, expires_at,
                one_time_use, usage_count, last_accessed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, NULL)
            """,
            (
                token,
                self.customer_id,
                report_id,
                now.isoformat(),
                expires_at.isoformat(),
                1 if one_time_use else 0,
            ),
        )
        await self.db.commit()

        return DownloadToken(
            token=token,
            report_id=report_id,
            created_at=now,
            expires_at=expires_at,
            one_time_use=one_time_use,
            usage_count=0,
            last_accessed_at=None,
        )

    async def validate_token(self, token: str) -> ReportArtifact | None:
        """Validate token and return artifact if valid.

        Args:
            token: Download token to validate

        Returns:
            ReportArtifact if valid, None if expired/not found

        Side effects:
            - Increments usage_count
            - Deletes token if one_time_use
            - Updates last_accessed_at
        """
        now = datetime.now(timezone.utc)

        # Fetch token with customer_id check
        cursor = await self.db.execute(
            """
            SELECT report_id, expires_at, one_time_use, customer_id
            FROM download_tokens
            WHERE token = ? AND customer_id = ?
            """,
            (token, self.customer_id),
        )
        row = await cursor.fetchone()
        await cursor.close()

        if not row:
            return None  # Token not found or wrong customer

        report_id, expires_at_str, one_time_use, _ = row
        expires_at = datetime.fromisoformat(expires_at_str)

        if now > expires_at:
            return None  # Token expired

        # Update usage tracking
        if one_time_use:
            # Delete token (one-time use)
            await self.db.execute(
                "DELETE FROM download_tokens WHERE token = ?",
                (token,),
            )
        else:
            # Increment usage count
            await self.db.execute(
                """
                UPDATE download_tokens
                SET usage_count = usage_count + 1,
                    last_accessed_at = ?
                WHERE token = ?
                """,
                (now.isoformat(), token),
            )
        await self.db.commit()

        # Fetch artifact
        cursor = await self.db.execute(
            """
            SELECT id, product_id, parameters_json, file_path, format,
                   size_bytes, created_at, expires_at, status
            FROM report_artifacts
            WHERE id = ? AND customer_id = ?
            """,
            (report_id, self.customer_id),
        )
        row = await cursor.fetchone()
        await cursor.close()

        if not row:
            return None  # Artifact deleted

        return ReportArtifact(
            id=row[0],
            product_id=row[1],
            parameters_json=row[2],
            file_path=row[3],
            format=row[4],
            size_bytes=row[5],
            created_at=datetime.fromisoformat(row[6]),
            expires_at=datetime.fromisoformat(row[7]),
            status=row[8],
        )

    async def create_mcp_resource(
        self,
        report_id: str,
        mime: str,
        size_bytes: int,
        ttl_seconds: int = 1800,
    ) -> MCPResource:
        """Register MCP resource URI.

        Args:
            report_id: Artifact ID
            mime: MIME type ("application/json")
            size_bytes: File size in bytes
            ttl_seconds: Resource validity period

        Returns:
            Created MCPResource
        """
        uri = f"report://ebr/{report_id}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        await self.db.execute(
            """
            INSERT INTO mcp_resources (
                uri, customer_id, report_id,
                mime, size_bytes,
                created_at, expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uri,
                self.customer_id,
                report_id,
                mime,
                size_bytes,
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        await self.db.commit()

        return MCPResource(
            uri=uri,
            report_id=report_id,
            mime=mime,
            size_bytes=size_bytes,
            created_at=now,
            expires_at=expires_at,
        )

    async def cleanup_expired(self) -> dict[str, int]:
        """Delete expired artifacts, tokens, and resources.

        Scoped to current customer_id only.

        Returns:
            Dictionary with counts: {
                "artifacts": int,
                "tokens": int,
                "resources": int
            }
        """
        now = datetime.now(timezone.utc).isoformat()

        # Delete expired tokens (CASCADE handles constraints)
        cursor = await self.db.execute(
            """
            DELETE FROM download_tokens
            WHERE customer_id = ? AND expires_at < ?
            """,
            (self.customer_id, now),
        )
        tokens_deleted = cursor.rowcount

        # Delete expired resources (CASCADE handles constraints)
        cursor = await self.db.execute(
            """
            DELETE FROM mcp_resources
            WHERE customer_id = ? AND expires_at < ?
            """,
            (self.customer_id, now),
        )
        resources_deleted = cursor.rowcount

        # Get expired artifacts (to delete files)
        cursor = await self.db.execute(
            """
            SELECT id, file_path FROM report_artifacts
            WHERE customer_id = ? AND expires_at < ?
            """,
            (self.customer_id, now),
        )
        expired_artifacts = await cursor.fetchall()
        await cursor.close()

        # Delete artifact files from disk
        for artifact_id, file_path in expired_artifacts:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete artifact file {file_path}: {e}")

        # Delete artifact records
        cursor = await self.db.execute(
            """
            DELETE FROM report_artifacts
            WHERE customer_id = ? AND expires_at < ?
            """,
            (self.customer_id, now),
        )
        artifacts_deleted = cursor.rowcount

        await self.db.commit()

        return {
            "artifacts": artifacts_deleted,
            "tokens": tokens_deleted,
            "resources": resources_deleted,
        }
```

**Key Points:**
- [ ] Use `secrets.token_urlsafe(32)` for 256-bit entropy (best practice)
- [ ] Store all timestamps as ISO8601 UTC strings
- [ ] CASCADE deletes (delete tokens when artifact deleted)
- [ ] Atomic operations (use transactions)
- [ ] Type hints for all methods

### AC3: Update `generate_ebr_report` Tool

**Modify `src/testio_mcp/tools/generate_ebr_report_tool.py`:**

```python
@mcp.tool()
async def generate_ebr_report(
    product_id: int,
    ctx: Context,
    start_date: str | None = None,
    end_date: str | None = None,
    statuses: str | list[TestStatus] | None = None,
    force_refresh_bugs: bool = False,
    output_mode: Literal["inline", "file"] = "inline",  # NEW
    inline_test_limit: int = 0,  # NEW: Cap by_test items when output_mode="file"
) -> dict[str, Any]:
    """Generate Executive Bug Report.

    Args:
        output_mode: "inline" (full JSON) or "file" (download URL + summary)
        inline_test_limit: Max by_test items in response when output_mode="file"
                          (0 = empty, >0 = truncated preview)

    Returns:
        When output_mode="inline":
            Full report (summary, by_test, cache_stats)

        When output_mode="file":
            {
                "mode": "file",
                "summary": EBRSummary (full),
                "by_test": list (truncated to inline_test_limit),
                "cache_stats": CacheStats (full),
                "download": {
                    "url": str,
                    "format": "json",
                    "expires_in_seconds": int
                },
                "resource": {  # Optional, if MCP resources enabled
                    "uri": str,
                    "mime": str,
                    "size_bytes": int,
                    "expires_at": str
                }
            }
    """
```

**Implementation:**
- [ ] Add `output_mode` parameter (default "inline" for backward compat)
- [ ] Add `inline_test_limit` parameter (default 0)
- [ ] Update tool docstring with output mode examples
- [ ] Delegate to service layer

### AC4: Update `MultiTestReportService`

**Modify `src/testio_mcp/services/multi_test_report_service.py`:**

```python
class MultiTestReportService(BaseService):
    def __init__(
        self,
        client: TestIOClient,
        test_repo: TestRepository,
        bug_repo: BugRepository,
        artifact_repo: ArtifactRepository,  # NEW
    ):
        super().__init__(client=client, cache=None)  # type: ignore[arg-type]
        self.test_repo = test_repo
        self.bug_repo = bug_repo
        self.artifact_repo = artifact_repo  # NEW

    async def generate_ebr_report(
        self,
        product_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
        statuses: list[str] | None = None,
        force_refresh_bugs: bool = False,
        output_mode: Literal["inline", "file"] = "inline",  # NEW
        inline_test_limit: int = 0,  # NEW
        artifact_ttl_seconds: int = 1800,  # NEW: Configurable TTL
    ) -> dict[str, Any]:
        """Generate EBR with optional artifact creation."""

        # 1. Generate full report (same as before)
        full_report = await self._generate_full_report(...)

        # 2. If inline mode, return full report (unchanged)
        if output_mode == "inline":
            return full_report

        # 3. File mode: Create artifact and return download info

        # 3a. Write file to disk
        artifact_id = str(uuid.uuid4())
        file_path = Path("~/.testio-mcp/artifacts") / f"{artifact_id}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)

        size_bytes = file_path.stat().st_size

        # 3b. Create artifact record
        artifact = await self.artifact_repo.create_artifact(
            product_id=product_id,
            parameters={"start_date": start_date, "end_date": end_date, "statuses": statuses},
            file_path=str(file_path),
            format="json",
            size_bytes=size_bytes,
            ttl_seconds=artifact_ttl_seconds,
        )

        # 3c. Generate download token
        token = await self.artifact_repo.create_download_token(
            report_id=artifact.id,
            ttl_seconds=artifact_ttl_seconds,
            one_time_use=False,  # Reusable by default
        )

        # 3d. Register MCP resource (if enabled)
        mcp_resource = None
        if os.getenv("TESTIO_MCP_ENABLE_RESOURCES", "false").lower() == "true":
            mcp_resource = await self.artifact_repo.create_mcp_resource(
                report_id=artifact.id,
                mime="application/json",
                size_bytes=size_bytes,
                ttl_seconds=artifact_ttl_seconds,
            )

        # 3e. Build file mode response
        return {
            "mode": "file",
            "summary": full_report["summary"],
            "by_test": full_report["by_test"][:inline_test_limit],  # Truncate
            "cache_stats": full_report["cache_stats"],
            "download": {
                "url": f"http://127.0.0.1:8080/download/{token.token}",
                "format": "json",
                "expires_in_seconds": artifact_ttl_seconds,
            },
            "resource": {
                "uri": mcp_resource.uri,
                "mime": mcp_resource.mime,
                "size_bytes": mcp_resource.size_bytes,
                "expires_at": mcp_resource.expires_at.isoformat(),
            } if mcp_resource else None,
        }
```

**Key Points:**
- [ ] Inject `ArtifactRepository` in constructor
- [ ] Write files to `~/.testio-mcp/artifacts/{uuid}.json` (not `reports/`)
- [ ] Store parameters for reproducibility
- [ ] Truncate `by_test` to `inline_test_limit` in response
- [ ] Make MCP resource optional (feature flag)

### AC5: Add `/download/{token}` Endpoint

**Update `src/testio_mcp/api.py`:**

```python
from fastapi import Path
from fastapi.responses import FileResponse, JSONResponse
from testio_mcp.repositories.artifact_repository import ArtifactRepository

@api.get("/download/{token}")
async def download_artifact(
    request: Request,
    token: str = Path(..., description="Download token"),
) -> FileResponse:
    """Download artifact via short-lived capability URL.

    Security:
    - Tokens are cryptographic random (256 bits)
    - Tokens expire after TTL (default 30 min)
    - Optional one-time use
    - No semantic data in URLs

    Returns:
        FileResponse with Content-Disposition: attachment

    Raises:
        404: Token not found or expired
        410: Token expired (gone)
    """
    # Get server context
    server_ctx = get_server_context_from_request(request)
    cache = server_ctx["cache"]

    # Create artifact repository
    artifact_repo = ArtifactRepository(db=cache.db)

    # Validate token and get artifact
    artifact = await artifact_repo.validate_token(token)

    if artifact is None:
        return JSONResponse(
            status_code=410,  # Gone
            content={
                "error": "token_expired",
                "message": "Download token has expired or was already used",
            },
        )

    # Check file exists
    file_path = Path(artifact.file_path)
    if not file_path.exists():
        return JSONResponse(
            status_code=404,
            content={
                "error": "file_not_found",
                "message": "Artifact file no longer exists",
            },
        )

    # Stream file (don't load into RAM)
    return FileResponse(
        path=file_path,
        media_type="application/json",
        filename=file_path.name,
        headers={
            "Content-Disposition": f'attachment; filename="{file_path.name}"',
            "Cache-Control": "no-store, no-cache, must-revalidate",
        },
    )
```

**Security Notes:**
- [ ] Use `FileResponse` for streaming (not loading full file)
- [ ] Return 410 (Gone) for expired tokens (semantic HTTP status)
- [ ] Set `Cache-Control: no-store` (prevent caching)
- [ ] No error details in production (generic messages)
- [ ] Log token usage for audit trail

### AC6: Add MCP Resource Support (Optional)

**Update `src/testio_mcp/server.py`:**

```python
@mcp.resource("report://ebr/{report_id}")
async def get_ebr_resource(uri: str, ctx: Context) -> dict[str, Any]:
    """Fetch EBR report via MCP resource URI.

    MCP resources provide read-only access to artifacts with metadata.
    This enables resource-aware clients to discover and fetch reports.

    Args:
        uri: Resource URI (e.g., "report://ebr/550e8400-...")

    Returns:
        {
            "contents": [{
                "uri": str,
                "mimeType": "application/json",
                "text": str  # Full report JSON
            }],
            "metadata": {
                "size_bytes": int,
                "created_at": str,
                "expires_at": str
            }
        }

    Raises:
        ResourceNotFoundException: If report_id not found or expired
    """
    # Parse report_id from URI
    report_id = uri.split("/")[-1]

    # Get server context
    server_ctx = cast(ServerContext, ctx.request_context.lifespan_context)
    cache = server_ctx["cache"]

    # Create artifact repository
    artifact_repo = ArtifactRepository(db=cache.db)

    # Get MCP resource
    resource = await artifact_repo.get_mcp_resource(uri)

    if resource is None:
        raise ResourceNotFoundException(f"Resource not found or expired: {uri}")

    # Get artifact
    artifact = await artifact_repo.get_artifact(resource.report_id)

    # Read file
    file_path = Path(artifact.file_path)
    with open(file_path, "r") as f:
        content = f.read()

    # Return MCP resource format
    return {
        "contents": [{
            "uri": uri,
            "mimeType": resource.mime,
            "text": content,
        }],
        "metadata": {
            "size_bytes": resource.size_bytes,
            "created_at": resource.created_at.isoformat(),
            "expires_at": resource.expires_at.isoformat(),
        },
    }
```

**Feature Flag:**
- [ ] Environment variable: `TESTIO_MCP_ENABLE_RESOURCES=true`
- [ ] Default: `false` (wait for client support)
- [ ] Only register resource handler if enabled

### AC7: Background Cleanup Task

**Add to `src/testio_mcp/server.py` lifespan:**

```python
@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[ServerContext]:
    """Server lifespan with artifact cleanup."""

    # ... existing setup ...

    async def cleanup_expired_artifacts() -> None:
        """Background task to delete expired artifacts."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every 1 hour

                artifact_repo = ArtifactRepository(db=cache.db)
                counts = await artifact_repo.cleanup_expired()

                logger.info(
                    "Artifact cleanup complete",
                    extra={
                        "artifacts_deleted": counts["artifacts"],
                        "tokens_deleted": counts["tokens"],
                        "resources_deleted": counts["resources"],
                    },
                )
            except Exception as e:
                logger.error(f"Artifact cleanup failed: {e}")

    # Start cleanup task
    cleanup_task = asyncio.create_task(cleanup_expired_artifacts())

    try:
        yield server_ctx
    finally:
        cleanup_task.cancel()
        # ... existing cleanup ...
```

**Configuration:**
- [ ] Configurable interval: `TESTIO_ARTIFACT_CLEANUP_INTERVAL_SECONDS=3600`
- [ ] Configurable default TTL: `TESTIO_ARTIFACT_DEFAULT_TTL_SECONDS=1800`
- [ ] Log cleanup statistics

### AC8: Update DI Helper

**Update `src/testio_mcp/utilities/service_helpers.py`:**

```python
def _build_service(service_class: type[ServiceT], server_ctx: ServerContext) -> ServiceT:
    """Shared service construction logic (DRY principle)."""
    client = server_ctx["testio_client"]
    cache = server_ctx["cache"]

    if service_class.__name__ == "MultiTestReportService":
        test_repo = cache.repo
        bug_repo = BugRepository(
            db=cache.db,
            client=client,
            customer_id=cache.customer_id
        )
        artifact_repo = ArtifactRepository(
            db=cache.db,
            customer_id=cache.customer_id  # Multi-tenant isolation
        )
        return service_class(
            client=client,
            test_repo=test_repo,
            bug_repo=bug_repo,
            artifact_repo=artifact_repo,
        )

    # ... rest unchanged ...
```

**Key Change:**
- [ ] Inject `customer_id` into `ArtifactRepository` for multi-tenant isolation
- [ ] Mirrors pattern used in `BugRepository` and `TestRepository`

### AC9: Error Handling

**Add exception handling in `api.py`:**

```python
class TokenExpiredError(Exception):
    """Download token has expired."""
    def __init__(self, token_prefix: str):
        """Initialize with truncated token for logging safety.

        Args:
            token_prefix: First 8 chars of token (for debugging)
        """
        self.token_prefix = token_prefix
        super().__init__(f"Token expired: {token_prefix}...")

class ArtifactNotFoundError(Exception):
    """Artifact file not found on disk."""
    def __init__(self, artifact_id: str):
        self.artifact_id = artifact_id
        super().__init__(f"Artifact not found: {artifact_id}")

@api.exception_handler(TokenExpiredError)
async def handle_token_expired(_: Request, exc: TokenExpiredError) -> JSONResponse:
    """Handle expired/invalid tokens.

    Security: Generic error message prevents token enumeration.
    Only logs truncated token prefix (first 8 chars).
    """
    return JSONResponse(
        status_code=410,  # Gone
        content={
            "error": "token_invalid_or_expired",
            "message": "Download link is no longer valid",
            "suggestion": "Generate a new report to get a fresh download link",
        },
    )

@api.exception_handler(ArtifactNotFoundError)
async def handle_artifact_not_found(_: Request, exc: ArtifactNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": "artifact_not_found",
            "message": "Artifact file no longer exists",
            "suggestion": "The file may have been cleaned up. Generate a new report.",
        },
    )
```

**Security Notes:**
- [ ] NEVER log full tokens (capability URL best practice)
- [ ] Log only truncated token (first 8 chars) for debugging
- [ ] Use generic error messages to prevent token enumeration
- [ ] Treat "unknown token" same as "expired" (avoid info disclosure)

### AC10: Unit Tests

**File: `tests/unit/test_repositories_artifact.py`**
- [ ] Test artifact creation with UUID generation
- [ ] Test token generation with 256-bit entropy
- [ ] Test token validation (valid, expired, not found)
- [ ] Test one-time use tokens (delete after use)
- [ ] Test usage count increment
- [ ] Test MCP resource registration
- [ ] Test cleanup_expired (deletes artifacts + files)
- [ ] Test CASCADE deletes (tokens deleted when artifact deleted)

**File: `tests/unit/test_tools_generate_ebr_report_output_mode.py`**
- [ ] Test `output_mode="inline"` (unchanged behavior)
- [ ] Test `output_mode="file"` (artifact creation)
- [ ] Test `inline_test_limit` truncation
- [ ] Test download URL format
- [ ] Test resource URI format (if enabled)
- [ ] Test backward compatibility (default "inline")

**File: `tests/unit/test_api_download_endpoint.py`**
- [ ] Test valid token download
- [ ] Test expired token (410 Gone)
- [ ] Test not found token (404)
- [ ] Test one-time use token (second access fails)
- [ ] Test file streaming (not full load)
- [ ] Test Content-Disposition header

### AC11: Integration Tests

**File: `tests/integration/test_artifact_service_integration.py`**
- [ ] Test full flow: generate → create artifact → download
- [ ] Test token expiry (fast-forward time)
- [ ] Test cleanup background task
- [ ] Test MCP resource access (if enabled)
- [ ] Test with large EBR (Canva Monoproduct, 216 tests)
- [ ] Test concurrent downloads (same token)

### AC12: Documentation

**Update `CLAUDE.md`:**
- [ ] Document `output_mode` parameter
- [ ] Document download URL usage
- [ ] Document MCP resource support (feature flag)
- [ ] Document artifact cleanup configuration
- [ ] Document security considerations (token expiry, one-time use)

**Update `README.md`:**
- [ ] Add download service architecture diagram
- [ ] Add usage examples (inline vs file mode)
- [ ] Add security best practices section
- [ ] Add troubleshooting (expired tokens, missing artifacts)

## Tasks

### Task 1: Database Schema (2 hours)
- [ ] Create migration script for 3 new tables
- [ ] Add indexes for performance
- [ ] Update schema version tracking
- [ ] Test migration on existing databases

### Task 2: Artifact Repository (3 hours)
- [ ] Implement `ArtifactRepository` class
- [ ] Implement artifact CRUD operations
- [ ] Implement token generation (256-bit entropy)
- [ ] Implement token validation with expiry
- [ ] Implement MCP resource registration
- [ ] Implement cleanup_expired method

### Task 3: Update Service Layer (2 hours)
- [ ] Add `output_mode` parameter to `generate_ebr_report`
- [ ] Implement file mode logic (artifact creation)
- [ ] Implement token generation
- [ ] Implement MCP resource registration (optional)
- [ ] Update DI helper to inject `ArtifactRepository`

### Task 4: Download Endpoint (2 hours)
- [ ] Add `/download/{token}` route to FastAPI
- [ ] Implement token validation
- [ ] Implement file streaming
- [ ] Add error handling (410, 404)
- [ ] Add security headers (Cache-Control)

### Task 5: MCP Resource Support (2 hours)
- [ ] Add `@mcp.resource` handler (if feature enabled)
- [ ] Implement resource URI parsing
- [ ] Implement resource metadata response
- [ ] Add feature flag check

### Task 6: Background Cleanup (1 hour)
- [ ] Add cleanup task to lifespan
- [ ] Implement periodic execution (1 hour interval)
- [ ] Add logging for cleanup statistics
- [ ] Add configuration (interval, TTL)

### Task 7: Testing (4 hours)
- [ ] Write unit tests (artifact repository)
- [ ] Write unit tests (service layer)
- [ ] Write unit tests (download endpoint)
- [ ] Write integration tests (full flow)
- [ ] Test with large EBR reports
- [ ] Achieve >85% coverage

### Task 8: Documentation (2 hours)
- [ ] Update CLAUDE.md
- [ ] Update README.md
- [ ] Add architecture diagram
- [ ] Add usage examples
- [ ] Add troubleshooting guide

## Configuration

**Environment Variables:**

```bash
# Artifact Storage
TESTIO_ARTIFACT_DIR=~/.testio-mcp/artifacts  # Artifact file storage
TESTIO_ARTIFACT_DEFAULT_TTL_SECONDS=1800     # 30 min default
TESTIO_ARTIFACT_CLEANUP_INTERVAL_SECONDS=3600 # 1 hour cleanup

# MCP Resources (optional)
TESTIO_MCP_ENABLE_RESOURCES=false  # Enable MCP resource registry

# Download Service
TESTIO_DOWNLOAD_ONE_TIME_USE=false  # Default: reusable tokens
```

## Security Considerations

### Capability URL Best Practices (W3C, AWS)
- ✅ **High entropy:** 256-bit tokens (not guessable)
- ✅ **Short-lived:** 15-30 min TTL (OAuth-style)
- ✅ **Opaque:** No semantic data in URLs
- ✅ **Limited scope:** One token = one artifact
- ✅ **Optional one-time use:** Delete token after first download

### MCP Security Best Practices
- ✅ **Read-only resources:** No mutations via resource API
- ✅ **Minimal data exposure:** No PII in URIs
- ✅ **Clear boundaries:** Resources separate from tools
- ✅ **Expiration:** Resources expire with artifacts

### Defense in Depth
- ✅ **Bind to 127.0.0.1:** Local-only for MVP
- ✅ **No caching:** `Cache-Control: no-store`
- ✅ **Audit trail:** Log all token usage
- ✅ **Cleanup:** Automatic deletion of expired artifacts

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ MCP Tool: generate_ebr_report(output_mode="file")          │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ MultiTestReportService                                      │
│ ├─ Generate full EBR                                        │
│ ├─ Write to ~/.testio-mcp/artifacts/{uuid}.json            │
│ ├─ Create artifact record (SQLite)                         │
│ ├─ Generate download token (256-bit random)                │
│ └─ Register MCP resource (if enabled)                      │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│ Response                                                     │
│ {                                                            │
│   "download": {                                              │
│     "url": "http://127.0.0.1:8080/download/abc123xyz",      │
│     "expires_in_seconds": 1800                               │
│   },                                                         │
│   "resource": {                                              │
│     "uri": "report://ebr/rep_456",                          │
│     "expires_at": "2025-01-19T14:30:00Z"                    │
│   }                                                          │
│ }                                                            │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌──────────────────┐          ┌──────────────────┐
│ HTTP Download    │          │ MCP Resource     │
│ GET /download/{} │          │ report://ebr/{}  │
│ ↓                │          │ ↓                │
│ Validate token   │          │ Validate URI     │
│ Stream file      │          │ Read file        │
│ Increment usage  │          │ Return metadata  │
└──────────────────┘          └──────────────────┘
```

## Success Metrics

- ✅ SQLite schema with 3 tables (artifacts, tokens, resources)
- ✅ Artifact repository with CRUD operations
- ✅ Download endpoint with token validation
- ✅ MCP resource support (feature-flagged)
- ✅ Background cleanup task
- ✅ 256-bit token generation
- ✅ File streaming (not full load)
- ✅ Unit tests >85% coverage
- ✅ Integration tests with real artifacts
- ✅ Documentation updated

## References

- **ChatGPT 5.1 PRD:** Production-Grade Artifact Service
- **W3C Capability URLs:** https://www.w3.org/TR/capability-urls/
- **AWS Pre-signed URLs:** https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html
- **OAuth Token Lifetimes:** https://datatracker.ietf.org/doc/html/rfc6749#section-4.2.2
- **MCP Security:** https://modelcontextprotocol.io/docs/concepts/security
- **MCP Resources:** https://modelcontextprotocol.io/docs/concepts/resources

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-19 | 1.0 | Story created based on ChatGPT PRD and user requirements | Sarah (PO) |
| 2025-01-19 | 1.1 | Critical fixes based on Codex peer review | Sarah (PO) |

**v1.1 Changes (Codex Peer Review):**
- **CRITICAL:** Added `customer_id` to all 3 tables for multi-tenant isolation
- **CRITICAL:** Changed migration strategy from SQL files to Python-based (align with `schema.py`)
- **CRITICAL:** Changed `ArtifactRepository` from `sqlite3.Connection` to `aiosqlite.Connection`
- **SECURITY:** Fixed token logging - only log truncated prefix (first 8 chars), never full tokens
- **SECURITY:** Generic error messages for token validation (prevent enumeration)
- **CONSISTENCY:** Composite indexes on `(customer_id, ...)` for performance
- **CONSISTENCY:** All timestamps stored as UTC ISO8601 strings (YYYY-MM-DDTHH:MM:SSZ)
- **CONSISTENCY:** Inject `customer_id` into `ArtifactRepository` constructor (mirrors TestRepository/BugRepository pattern)
- **TODO:** Add `Path.expanduser()` for artifact directory configuration
- **TODO:** Drive MIME type and filename from `format`/`mime` columns (not hard-coded)
- **TODO:** Wire cleanup task into existing `background_tasks` list in lifespan
- **TODO:** Clarify MCP resource registration with feature flag (imperative vs decorator)

## Dev Agent Record

**Implementation Notes:**
- Use `Settings.TESTIO_ARTIFACT_DIR` with `.expanduser()` for path resolution
- Drive `media_type` and `filename` from artifact's `format` and `mime` fields (future CSV support)
- Add cleanup task to existing `background_tasks` list (don't create separate shutdown path)
- For MCP resource registration, if `TESTIO_MCP_ENABLE_RESOURCES=false`, raise `ResourceNotFound` immediately in handler
- Consider hashing tokens in DB for additional security (defer to follow-up story)
- One-time use tokens: Implement basic support but note concurrency edge cases in docs

## QA Results
*This section will be populated after QA review*
