# Epic Technical Specification: Sync Consolidation

Date: 2025-11-26
Author: leoric
Epic ID: 009
Status: Draft

---

## Overview

Epic-009 consolidates sync **orchestration** into a unified SyncService so that three entry points (background server sync, CLI manual sync, and a new MCP tool) share the same implementation. Currently, sync logic is duplicated between `cache.py` (background sync) and `cli/sync.py` (manual sync), with different code paths for similar operations. The new `sync_data` MCP tool requirement would create a third duplication point without this consolidation.

The key insight is that **orchestration** (phases, filtering, scoping) gets consolidated, while **repositories keep their encapsulated read-through caching**. After Epic-007's ADR-017, repositories already handle on-demand staleness checks - SyncService only handles bulk sync orchestration for discovery and refresh cycles.

## Objectives and Scope

### In Scope

- **SyncService class** with unified `execute_sync()` method
- **SyncPhase enum**: PRODUCTS, FEATURES, NEW_TESTS (current 3-phase model)
- **SyncScope dataclass**: product_ids, since_date, entity_filters
- **SyncOptions dataclass**: force_refresh, incremental_only, nuke
- **SyncResult dataclass**: stats, warnings, duration_seconds, phases_completed
- **Dual-layer locking**: File lock (cross-process) + asyncio lock (in-process)
- **Stale lock recovery**: PID tracking + 1-hour mtime timeout
- **Migration of cache.py sync methods** to SyncService
- **Migration of cli/sync.py** to delegate to SyncService
- **New `sync_data` MCP tool** with CLI parity (product_ids, since, force)
- **Remove `force_refresh_bugs`** from EBR tool (replaced by sync_data)
- **Persist `last_sync_completed`** timestamp to prevent immediate post-sync background refresh

### Out of Scope

- Repository changes (they keep `get_*_cached_or_refresh()` as-is)
- New sync phases (stays at 3-phase model from ADR-017)
- Background sync interval changes
- Multi-tenant sync (deferred to STORY-010)

## System Architecture Alignment

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SyncService                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ execute_sync(phases, scope, options) -> SyncResult        │  │
│  │                                                           │  │
│  │ - Phase orchestration (1→2→3 in order)                    │  │
│  │ - Dual-layer locking (file + asyncio)                     │  │
│  │ - Sync event logging                                      │  │
│  │ - Error aggregation and recovery                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        ^                    ^                    ^
   Background            CLI Sync            MCP Tool
   (server.py)          (cli/sync)         (sync_data)

Repositories (bug/test/feature) keep their own get_*_cached_or_refresh()
methods for on-demand read-through caching - they do NOT delegate to SyncService.
```

### Architecture Constraints

- **ADR-017 compliance**: 3-phase background sync (products → features → new tests)
- **ADR-006 compliance**: Service layer pattern - SyncService is framework-agnostic
- **ADR-007 compliance**: SyncService accessible via FastMCP Context injection
- **ADR-002 compliance**: Respects global concurrency semaphore during API calls

## Detailed Design

### Services and Modules

| Service/Module | Location | Responsibility |
|----------------|----------|----------------|
| `SyncService` | `src/testio_mcp/services/sync_service.py` | Unified sync orchestration |
| `SyncPhase` | `src/testio_mcp/services/sync_service.py` | Phase enumeration (PRODUCTS, FEATURES, NEW_TESTS) |
| `SyncScope` | `src/testio_mcp/services/sync_service.py` | Filtering: product_ids, since_date |
| `SyncOptions` | `src/testio_mcp/services/sync_service.py` | Modes: force, incremental_only, nuke |
| `SyncResult` | `src/testio_mcp/services/sync_service.py` | Return type with stats, duration, warnings |
| `sync_data` tool | `src/testio_mcp/tools/sync_data_tool.py` | MCP tool wrapper for SyncService |

### Data Models and Contracts

```python
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

class SyncPhase(str, Enum):
    """Sync phases from ADR-017 3-phase model."""
    PRODUCTS = "products"      # Phase 1: Refresh product metadata
    FEATURES = "features"      # Phase 2: Refresh features (TTL-gated)
    NEW_TESTS = "new_tests"    # Phase 3: Discover new tests (incremental)

@dataclass
class SyncScope:
    """Filtering parameters for sync scope."""
    product_ids: list[int] | None = None  # Limit to specific products
    since_date: datetime | None = None    # Date filter for test discovery
    entity_types: list[str] | None = None # Future: filter specific entities

@dataclass
class SyncOptions:
    """Sync mode configuration."""
    force_refresh: bool = False       # Re-sync all tests (non-destructive upsert)
    incremental_only: bool = False    # Fast mode: discover new only
    nuke: bool = False                # Destructive: delete DB + full resync

@dataclass
class SyncResult:
    """Unified sync result with stats and diagnostics."""
    phases_completed: list[SyncPhase] = field(default_factory=list)
    products_synced: int = 0
    features_refreshed: int = 0
    tests_discovered: int = 0
    tests_updated: int = 0
    duration_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
```

**Lock file schema** (`~/.testio-mcp/sync.lock`):
```
PID: 12345
STARTED: 2025-11-26T10:30:00Z
```

**Sync metadata table update** (existing `sync_metadata` table):
- Add `last_sync_completed: datetime` column for background sync coordination

### APIs and Interfaces

#### SyncService API

```python
class SyncService(BaseService):
    """Unified sync orchestration service (Epic-009)."""

    async def execute_sync(
        self,
        phases: list[SyncPhase] | None = None,  # Default: all 3 phases
        scope: SyncScope | None = None,
        options: SyncOptions | None = None,
    ) -> SyncResult:
        """Execute sync with specified phases, scope, and options.

        Args:
            phases: Which phases to run (default: all 3)
            scope: Filtering (products, dates)
            options: Mode flags (force, incremental, nuke)

        Returns:
            SyncResult with stats and diagnostics

        Raises:
            SyncLockError: Another sync in progress
            SyncTimeoutError: Lock acquisition timeout
        """

    def _acquire_file_lock(self, timeout: float = 30.0) -> FileLock:
        """Acquire cross-process file lock with stale recovery."""

    def _is_lock_stale(self, lock_path: Path) -> bool:
        """Check if lock is stale (PID dead or mtime > 1 hour)."""
```

#### sync_data MCP Tool

```python
@mcp.tool()
async def sync_data(
    ctx: Context,
    product_ids: list[int] | None = None,
    since: str | None = None,
    force: bool = False,
) -> dict:
    """Refresh local data from TestIO API.

    Args:
        product_ids: Limit sync to specific products (default: all)
        since: Date filter (ISO or relative like '30 days ago')
        force: Re-sync all tests, not just new ones

    Returns:
        {
            "products_synced": int,
            "features_refreshed": int,
            "tests_discovered": int,
            "duration_seconds": float,
            "warnings": list[str]
        }
    """
```

**Schema token target**: ~500 tokens (minimal description, essential params only)

### Workflows and Sequencing

#### Background Sync Flow (server.py → SyncService)

```
Server Startup
    │
    ├─→ Lifespan: Initialize SyncService
    │
    ├─→ Check should_run_initial_sync()
    │   │
    │   └─→ Read last_sync_completed from DB
    │       │
    │       ├─→ If stale (> interval): Run initial_sync()
    │       └─→ If fresh: Skip
    │
    └─→ Schedule background_refresh_task
        │
        └─→ Every 15 min:
            │
            ├─→ Check last_sync_completed (skip if recent manual/MCP sync)
            │
            ├─→ SyncService.execute_sync(
            │       phases=[PRODUCTS, FEATURES, NEW_TESTS],
            │       scope=SyncScope(since_date=env_filter)
            │   )
            │
            └─→ Update last_sync_completed in DB
```

#### CLI Sync Flow (cli/sync.py → SyncService)

```
testio-mcp sync --force --product-ids 598
    │
    ├─→ Parse CLI args → SyncScope + SyncOptions
    │
    ├─→ SyncService.execute_sync(
    │       phases=[PRODUCTS, FEATURES, NEW_TESTS],
    │       scope=SyncScope(product_ids=[598]),
    │       options=SyncOptions(force_refresh=True)
    │   )
    │
    ├─→ Acquire file lock (30s timeout)
    │   ├─→ Check stale lock recovery
    │   └─→ Write PID to lock file
    │
    ├─→ Execute phases sequentially
    │
    ├─→ Update last_sync_completed (resets background timer)
    │
    └─→ Release file lock
```

#### MCP sync_data Flow

```
AI: sync_data(product_ids=[598], since="30 days ago")
    │
    ├─→ Parse params → SyncScope + SyncOptions
    │
    ├─→ SyncService.execute_sync(
    │       phases=[PRODUCTS, FEATURES, NEW_TESTS],
    │       scope=SyncScope(product_ids=[598], since_date=parsed)
    │   )
    │
    ├─→ Uses asyncio lock (lightweight, in-process only)
    │
    ├─→ Execute phases
    │
    ├─→ Update last_sync_completed in DB
    │   └─→ Prevents immediate background sync
    │
    └─→ Return SyncResult as JSON
```

## Non-Functional Requirements

### Performance

| Metric | Target | Source |
|--------|--------|--------|
| Lock acquisition timeout | 30 seconds | STORY-048 AC4 |
| Default sync duration | < 5 minutes for 10 products | Current baseline |
| Incremental sync | < 30 seconds for 10 products | Current baseline |
| MCP tool response (in-process) | < 500ms for lock check | UX expectation |

**Constraint**: SyncService must not introduce latency regression vs current implementation.

### Security

- **File lock path**: `~/.testio-mcp/sync.lock` (user home directory, not world-readable)
- **PID exposure**: Lock file contains PID - acceptable for local deployment
- **No new credentials**: Uses existing `TESTIO_CUSTOMER_API_TOKEN`
- **Token sanitization**: Inherited from existing logging infrastructure (SEC-002)

### Reliability/Availability

- **Stale lock recovery**: If PID is dead OR mtime > 1 hour, reclaim lock
- **Graceful degradation**: If lock acquisition fails, return clear error message
- **Atomic updates**: Sync events logged atomically per phase
- **Partial failure handling**: Continue with next product if one fails

**Recovery scenarios**:
1. CLI crashes mid-sync → Lock file left behind → Next sync recovers via PID check
2. Server restart during background sync → Lock file stale → Background task recovers
3. Concurrent MCP calls → Asyncio lock serializes (no deadlock)

### Observability

**Logging**:
- Sync event logged to `sync_events` table (existing infrastructure)
- Duration always included in final log message
- Per-phase timing for debugging

**Metrics** (via get_sync_history tool):
- Success/failure counts
- Average duration
- Phase completion rates

**Log format example**:
```
INFO: Sync completed in 45.2s (3 phases: products=6, features=42, tests=15 new)
```

## Dependencies and Integrations

### Python Dependencies (from pyproject.toml)

| Package | Version | Purpose |
|---------|---------|---------|
| `filelock` | `>=3.13.0` | Cross-process file locking |
| `psutil` | `>=5.9.0` | PID validation for stale lock recovery |
| `fastmcp` | `>=2.12.0` | MCP tool registration |
| `sqlmodel` | `>=0.0.16` | ORM for sync_metadata updates |
| `aiosqlite` | `>=0.20.0` | Async SQLite access |

### Internal Dependencies

| Component | Used By | Integration |
|-----------|---------|-------------|
| `PersistentCache` | SyncService | Phase execution (sync_product_tests, refresh_features) |
| `ProductRepository` | SyncService | Product metadata upsert (Phase 1) |
| `FeatureRepository` | SyncService | Feature refresh (Phase 2) |
| `TestRepository` | SyncService | Test discovery (Phase 3) |
| `sync_events` table | SyncService | Event logging |
| `sync_metadata` table | SyncService | last_sync_completed timestamp |

### Migration Notes

**Database migration required**: Add `last_sync_completed` column to `sync_metadata` table (or create dedicated row in existing table).

## Acceptance Criteria (Authoritative)

### STORY-048: SyncService Foundation

1. **AC1**: `SyncService` class exists in `src/testio_mcp/services/sync_service.py`
2. **AC2**: `SyncPhase`, `SyncScope`, `SyncOptions`, `SyncResult` data models implemented
3. **AC3**: `execute_sync()` orchestrates phases in order: PRODUCTS → FEATURES → NEW_TESTS
4. **AC4**: File lock at `~/.testio-mcp/sync.lock` with 30s timeout
5. **AC5**: Stale lock recovery: check PID alive + mtime < 1 hour
6. **AC6**: Asyncio lock for in-process serialization (reuses PersistentCache pattern)
7. **AC7**: Sync event logged with duration on completion
8. **AC8**: Unit tests for SyncService (mock repositories)

### STORY-049: Background Sync Migration

1. **AC1**: `server.py` lifespan calls `SyncService.execute_sync()` instead of direct cache methods
2. **AC2**: `_run_background_refresh_cycle()` logic moved to SyncService
3. **AC3**: `TESTIO_REFRESH_INTERVAL_SECONDS` behavior unchanged
4. **AC4**: Old sync methods removed from `cache.py`
5. **AC5**: Integration tests pass with SyncService-based background sync

### STORY-050: CLI Sync Migration

1. **AC1**: `cli/sync.py` delegates to `SyncService.execute_sync()`
2. **AC2**: `--force` maps to `options.force_refresh=True`
3. **AC3**: `--incremental-only` maps to `phases=[NEW_TESTS]`
4. **AC4**: `--nuke` maps to `options.nuke=True`
5. **AC5**: `--product-ids` maps to `scope.product_ids`
6. **AC6**: `--since` maps to `scope.since_date`
7. **AC7**: Progress indicators and verbose output preserved
8. **AC8**: `--nuke` enhanced warning shows all entity counts

### STORY-051: sync_data MCP Tool

1. **AC1**: Tool exists in `src/testio_mcp/tools/sync_data_tool.py`
2. **AC2**: Parameters: `product_ids`, `since`, `force`
3. **AC3**: Calls `SyncService.execute_sync()` with mapped params
4. **AC4**: Updates `last_sync_completed` in DB on success
5. **AC5**: Background sync checks `last_sync_completed` before running
6. **AC6**: Returns: products_synced, features_refreshed, tests_discovered, duration_seconds, warnings
7. **AC7**: Schema under 500 tokens
8. **AC8**: Unit tests and integration tests

### STORY-052: Remove force_refresh_bugs from EBR

1. **AC1**: `force_refresh_bugs` parameter removed from `generate_ebr_report`
2. **AC2**: Tool description references `sync_data` for refresh control
3. **AC3**: CLAUDE.md updated with migration guidance
4. **AC4**: Unit tests updated

## Traceability Mapping

| AC | Spec Section | Component | Test Idea |
|----|--------------|-----------|-----------|
| STORY-048/AC1 | Services and Modules | SyncService | Import test |
| STORY-048/AC2 | Data Models | SyncPhase, SyncScope, SyncOptions, SyncResult | Model serialization test |
| STORY-048/AC3 | Workflows/Sequencing | SyncService.execute_sync() | Phase ordering test |
| STORY-048/AC4 | NFR/Reliability | _acquire_file_lock() | Lock timeout test |
| STORY-048/AC5 | NFR/Reliability | _is_lock_stale() | Stale PID recovery test |
| STORY-048/AC6 | Data Models | PersistentCache.get_refresh_lock() | Asyncio lock reuse test |
| STORY-048/AC7 | NFR/Observability | log_sync_event | Duration logging test |
| STORY-049/AC1 | Workflows/Sequencing | server.py lifespan | Integration test |
| STORY-049/AC2 | Services and Modules | SyncService._run_phase_*() | Phase migration test |
| STORY-050/AC1-7 | APIs/Interfaces | cli/sync.py | CLI mode mapping tests |
| STORY-051/AC1-8 | APIs/Interfaces | sync_data_tool.py | MCP tool tests |
| STORY-052/AC1-4 | APIs/Interfaces | generate_ebr_report | Parameter removal test |

## Risks, Assumptions, Open Questions

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking CLI behavior | High | Comprehensive integration tests (STORY-050 AC7) |
| Background sync regression | High | Feature flag for gradual rollout (if needed) |
| Scope creep into repositories | Medium | Strict boundary: repos unchanged (Epic scope) |
| File lock contention in multi-user env | Low | Clear error messages, manual retry guidance |

### Assumptions

1. **A1**: Single-tenant deployment (no concurrent customers sharing lock)
2. **A2**: Background sync interval (15 min) provides sufficient buffer for manual syncs
3. **A3**: `filelock` library works reliably on macOS, Linux, Windows
4. **A4**: PID validation via `psutil.pid_exists()` is sufficient for stale detection

### Open Questions

1. **Q1**: Should `sync_data` tool support `--nuke` mode?
   - **Recommendation**: No - too destructive for AI-initiated operations. CLI-only.

2. **Q2**: Should background sync skip if manual sync was very recent (e.g., < 5 min)?
   - **Answer**: Yes - persist `last_sync_completed` timestamp (STORY-051 AC4-5)

3. **Q3**: What if lock file is on NFS/network filesystem?
   - **Recommendation**: Document local filesystem requirement in CLAUDE.md

## Test Strategy Summary

### Test Levels

| Level | Focus | Framework | Coverage Target |
|-------|-------|-----------|-----------------|
| Unit | SyncService logic, data models | pytest | 90%+ |
| Integration | CLI → SyncService → DB | pytest + temp DB | 80%+ |
| E2E | MCP tool → SyncService → API | pytest-asyncio | Key flows |

### Key Test Scenarios

1. **Phase ordering**: Verify PRODUCTS → FEATURES → NEW_TESTS sequence
2. **Lock contention**: Two concurrent sync attempts (one should wait/fail)
3. **Stale lock recovery**: Kill process, verify lock reclaimed
4. **CLI mode mapping**: Each flag combo maps correctly to SyncService params
5. **Background sync coordination**: MCP sync resets timer, background skips
6. **Nuke confirmation**: Verify destructive operation warning shows all counts
7. **Partial failure**: One product fails, others continue

### Test Data Strategy

- **Unit tests**: Mocked repositories, synthetic data
- **Integration tests**: Real SQLite (temp file), mocked API
- **E2E tests**: Real API (staging), real SQLite

### Coverage Requirements

- `sync_service.py`: ≥90%
- `sync_data_tool.py`: ≥85%
- `cli/sync.py` (post-migration): ≥75%
