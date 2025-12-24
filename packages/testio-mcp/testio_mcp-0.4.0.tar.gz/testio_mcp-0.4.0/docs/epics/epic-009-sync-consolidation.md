# Epic-009: Sync Consolidation

## 1. Overview

**Goal:** Consolidate sync **orchestration** into a unified SyncService so that MCP tool can have CLI-like functionality (`--since`, `--product-ids`, `--force`).

**Motivation:**

- **2 Entry Points Today:** Background (cache.py), CLI (cli/sync.py)
- **New Requirement:** MCP `sync_data` tool needs same filtering as CLI
- **Without consolidation:** Would duplicate filtering/scoping logic in 3 places

**What Gets Consolidated:** Sync orchestration (phases, filtering, scoping)
**What Stays Unchanged:** Repository read-through caching (`get_*_cached_or_refresh()`)

**Key Principle:** Repositories encapsulate caching - callers don't think about it. SyncService only handles bulk sync orchestration (discovery, refresh cycles).

## 2. Current Architecture (After STORY-046)

| Component | Location | What It Does |
|-----------|----------|--------------|
| Background Sync | `cache.py:2525` | 3-phase: products -> features -> new tests |
| CLI Sync | `cli/sync.py` | Manual sync with modes (force, incremental, nuke) |
| Bug Read-Through | `bug_repository.py` | On-demand bug refresh if stale |
| Test Read-Through | `test_repository.py` | On-demand test refresh if stale |
| Feature Read-Through | `feature_repository.py` | On-demand feature refresh if stale |

**Current 3-Phase Model (cache.py:2525-2670):**

- Phase 1: Refresh product metadata (always)
- Phase 2: Refresh features (TTL-gated staleness check)
- Phase 3: Discover new tests (incremental sync)
- Phase 4: REMOVED - bugs/test metadata on-demand via repositories

**Consolidation Opportunity:**

- Background sync and CLI sync have different code paths for same operations
- CLI has additional modes (force, nuke) not available in background
- No MCP tool for user-triggered sync

## 3. Target Architecture

```
+-------------------------------------------------------------+
|                      SyncService                            |
|  +-----------------------------------------------------+   |
|  | execute_sync(phases, scope, options) -> SyncResult   |   |
|  +-----------------------------------------------------+   |
+-------------------------------------------------------------+
        ^              ^              ^
   Background     CLI Sync      MCP Tool
   (server.py)   (cli/sync)   (sync_data)

Repositories (bug/test/feature) keep their own get_*_cached_or_refresh()
methods for on-demand read-through caching - they do NOT delegate to SyncService.
```

## 4. Scope

### New Components

| Component | Purpose |
|-----------|---------|
| `SyncService` | Unified sync orchestration |
| `sync_data` MCP tool | User-controlled refresh via AI |
| `SyncPhase` enum | PRODUCTS, FEATURES, NEW_TESTS (current 3-phase model) |
| `SyncScope` | Product IDs, date filters, entity filters |
| `SyncResult` | Unified result with stats, warnings, timing |

### Refactored Components

| Component | Change |
|-----------|--------|
| `server.py` | Delegate to SyncService |
| `cli/sync.py` | Delegate to SyncService |
| `cache.py` | Remove sync methods (moved to SyncService) |

**Note:** Repositories keep their `get_*_cached_or_refresh()` methods unchanged. Read-through caching is already properly encapsulated there.

## 5. Stories

### STORY-048: SyncService Foundation

**User Story:**
As a developer maintaining the sync infrastructure,
I want a unified SyncService that handles all sync orchestration,
So that background, CLI, and MCP sync share the same implementation.

**Acceptance Criteria:**

1. [ ] Create `src/testio_mcp/services/sync_service.py`

2. [ ] Implement data models:
   - `SyncPhase` enum: PRODUCTS, FEATURES, NEW_TESTS
   - `SyncScope`: product_ids, since_date, entity_types
   - `SyncOptions`: force_refresh, incremental_only, nuke
   - `SyncResult`: stats, warnings, `duration_seconds` (always populated), phases_completed

3. [ ] Implement `execute_sync()` with phase orchestration
   - Accepts phases, scope, and options
   - Executes phases in order: PRODUCTS -> FEATURES -> NEW_TESTS
   - Returns unified SyncResult

4. [ ] Dual-layer locking strategy
   - **File lock (cross-process):** For "heavy" sync operations (background, CLI)
     - Path: `~/.testio-mcp/sync.lock`
     - Ensures only one process performs full sync at a time
   - **Asyncio lock (in-process):** For "light" entity refreshes (on-demand from MCP tools)
     - Reuses existing `PersistentCache.get_refresh_lock()` pattern
     - Prevents thundering herd within same process
   - **Deadlock prevention:** Never acquire file lock while holding asyncio lock
   - Second invocation: wait with timeout (30s) or fail fast with clear message

5. [ ] Stale lock recovery mechanism
   - Store PID in lock file content
   - On lock acquisition attempt, check if PID is still running
   - Also check file mtime: if > 1 hour old, treat as stale (handles zombie PIDs)
   - If stale, reclaim lock and log warning
   - Tests for crash recovery scenario

6. [ ] Move sync event logging to SyncService
   - Reuse existing sync_events table
   - Log start, progress, completion, errors
   - Final log message always includes total duration (e.g., "Sync completed in 45.2s")

7. [ ] Unit tests for SyncService

**Prerequisites:** STORY-062 (Async Session Management Refactor)

**Design Notes:**
- Follow the per-operation session pattern documented in STORY-062
- Reference CLAUDE.md for async session management best practices
- SyncService batch operations must create isolated sessions per concurrent task
- See Architecture document for session lifecycle rules

---

### STORY-049: Background Sync Migration

**User Story:**
As a developer maintaining the background sync,
I want it to delegate to SyncService,
So that background sync uses the same implementation as CLI and MCP.

**Acceptance Criteria:**

1. [ ] Refactor `server.py` lifespan to use SyncService
   - Replace direct cache.py calls with SyncService.execute_sync()
   - Pass appropriate scope and options

2. [ ] Move `_run_background_refresh_cycle()` logic from `cache.py` to SyncService
   - Preserve current 3-phase model: products -> features -> new tests
   - Maintain staleness checks for features

3. [ ] Preserve `TESTIO_REFRESH_INTERVAL_SECONDS` behavior
   - Background sync timer unchanged
   - SyncService execution respects interval

4. [ ] Remove migrated sync methods from `cache.py`
   - Clean up dead code
   - Keep non-sync cache methods

5. [ ] Integration tests for background sync via SyncService

**Prerequisites:** STORY-048

---

### STORY-050: CLI Sync Migration

**User Story:**
As a developer maintaining the CLI,
I want it to delegate to SyncService,
So that CLI sync modes map cleanly to SyncService options.

**Acceptance Criteria:**

1. [ ] Refactor `cli/sync.py` to delegate to SyncService

2. [ ] Map CLI modes to SyncService options:
   - Default -> phases=[PRODUCTS, FEATURES, NEW_TESTS]
   - `--force` -> force_refresh=True (re-sync all tests)
   - `--incremental-only` -> phases=[NEW_TESTS] only
   - `--nuke` -> nuke=True (delete DB + full resync)

3. [ ] Map CLI filters to SyncScope:
   - `--product-ids` -> scope.product_ids
   - `--since` -> scope.since_date

4. [ ] File locking via SyncService (unified with background/MCP)
   - CLI delegates lock acquisition to SyncService
   - SyncService handles both file lock (cross-process) and asyncio lock (in-process)
   - CLI invokes SyncService synchronously (asyncio.run)
   - Stale lock recovery inherited from SyncService (STORY-048)

5. [ ] Preserve CLI output formatting
   - Progress indicators
   - Verbose mode
   - Summary stats

6. [ ] Enhance --nuke warning to show all entities
   - Display counts for: products, tests, bugs, features, users
   - Example: "Current data: 6 products, 724 tests, 8,056 bugs, 298 features, 45 users"
   - Makes destructive operation impact more visible

7. [ ] CLI integration tests with all mode combinations

**Prerequisites:** STORY-048

---

### STORY-051: sync_data MCP Tool

**User Story:**
As an AI agent using the MCP server,
I want a `sync_data` tool that refreshes data on demand,
So that I can ensure data freshness before generating reports.

**Acceptance Criteria:**

1. [ ] Create `src/testio_mcp/tools/sync_data_tool.py`

2. [ ] Parameters (CLI parity):
   - `product_ids: list[int] | None` - Scope to specific products
   - `since: str | None` - Date filter for test discovery
   - `force: bool = False` - Re-sync all tests

3. [ ] Invoke SyncService.execute_sync() with mapped parameters

4. [ ] Reset background sync timer via persisted timestamp
   - Store `last_sync_completed` in SQLite (`sync_metadata` table or `sync_events`)
   - After successful sync completes, update timestamp in DB
   - Background task checks: `if now - last_sync_completed < interval: skip`
   - Timestamp only updated on success (failures don't reset timer)
   - Prevents immediate background sync after manual sync
   - Survives server restarts (persisted, not in-memory)

5. [ ] Return sync stats:
   - `products_synced`
   - `features_refreshed`
   - `tests_discovered`
   - `duration_seconds`
   - `warnings` (if any)

6. [ ] Slim schema design (target: ~500 tokens)

7. [ ] Unit tests for tool

8. [ ] Integration tests with real sync

**Prerequisites:** STORY-048

---

### STORY-052: Remove force_refresh_bugs from EBR

**User Story:**
As an MCP server operator,
I want the `force_refresh_bugs` parameter removed from EBR,
So that users use `sync_data` for explicit refresh control.

**Context:**
With `sync_data` available, the `force_refresh_bugs` parameter on `generate_ebr_report` (now `get_product_quality_report`) is redundant. Users who want fresh data should call `sync_data` first.

**Acceptance Criteria:**

1. [ ] Remove `force_refresh_bugs` parameter from `generate_ebr_report`
   - Remove from tool signature
   - Remove from schema
   - Remove from service layer

2. [ ] Update tool description
   - Reference `sync_data` for refresh control
   - Document that tool uses cached data

3. [ ] Slim schema (additional token savings beyond STORY-056)
   - Remove parameter documentation
   - Simplify description

4. [ ] Update CLAUDE.md with migration guidance

5. [ ] Unit tests updated

**Prerequisites:** STORY-051 (sync_data must exist first)

---

## 6. Success Criteria

**Consolidation:**

- Single SyncService used by 3 entry points (background, CLI, MCP)
- No duplicated sync orchestration logic
- Dual-layer locking: asyncio (in-process) + file lock (CLI cross-process)
- Repositories unchanged (keep encapsulated read-through caching)

**Functionality:**

- All existing CLI modes still work
- Background sync unchanged (3-phase, ADR-017)
- New `sync_data` MCP tool available
- `generate_ebr_report` no longer has `force_refresh_bugs`

**Performance:**

- No regression in sync speed
- Reduced code complexity

## 7. Dependencies

**Internal:**

- Epic-007 complete (analytics engine) ✅
- **STORY-062 complete (async session management refactor)** - Required before STORY-048
  - Establishes per-operation session pattern for batch operations
  - Documents session management patterns in CLAUDE.md and Architecture
  - Fixes existing session issues in FeatureRepository, BugRepository
- Epic-008 in progress (can run in parallel for non-cache stories)

**External:**

- None

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking CLI behavior | High | Comprehensive integration tests |
| Background sync regression | High | Feature flag for gradual rollout |
| Scope creep into repositories | Medium | Strict boundary: repos unchanged |

---

**Epic Status:** Ready for Implementation
**Dependencies:** Epic-007 (Generic Analytics Framework) ✅ Complete
**Target:** Unified sync architecture, new sync_data MCP tool
