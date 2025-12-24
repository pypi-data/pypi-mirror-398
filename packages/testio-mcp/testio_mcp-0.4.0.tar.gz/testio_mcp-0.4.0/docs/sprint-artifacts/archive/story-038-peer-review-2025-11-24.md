# STORY-038 Peer Review Findings

**Date:** 2025-11-24
**Reviewer:** Codex (via Zen MCP clink)
**Status:** Needs Revision - Critical issues identified

---

## Executive Summary

Codex identified **7 critical issues** that would block STORY-038 implementation. The story structure and approach are sound, but several gaps exist between the story specification and current codebase reality.

**Overall Assessment:** Needs revision before implementation; issues are fixable but must be addressed to prevent blocking.

---

## Critical Issues

### ❌ Issue 1: Product ORM Missing `features_synced_at` Field

**Problem:**
Story AC1 only shows Alembic migration, but `Product` ORM model (`src/testio_mcp/models/orm/product.py`) doesn't have the `features_synced_at` field. Alembic auto-generate won't emit the column, and runtime staleness logic will crash with `AttributeError`.

**Current State:**
```python
class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    customer_id: int = Field(index=True)
    data: str = Field()
    last_synced: datetime | None = Field(default=None)
    # ❌ Missing: features_synced_at field
```

**Fix Required:**
- Add `features_synced_at: datetime | None = Field(default=None)` to Product ORM
- Update AC1 to show ORM model change FIRST
- Add separate AC2 for Alembic migration (auto-generated from ORM)

**Status:** ✅ **FIXED** - Updated AC1 to show ORM change, added AC2 for migration

---

### ❌ Issue 2: `ProductRepository.get_product()` Doesn't Exist

**Problem:**
Multiple ACs (AC3, AC5, AC6, AC7) reference `ProductRepository.get_product()`, but this method doesn't exist. Current repository only has `get_product_info()` which returns a dict, not an ORM instance.

**Current State:**
```python
# src/testio_mcp/repositories/product_repository.py
class ProductRepository:
    async def get_product_info(self, product_id: int) -> dict | None:
        """Returns dict, not ORM instance"""
        # ...

    # ❌ Missing: get_product(product_id) -> Product | None
```

**Fix Required:**
- Add `async def get_product(self, product_id: int) -> Product | None` method to `ProductRepository`
- Method should return ORM instance (not dict)
- Update all code snippets in ACs to use correct method

**Status:** 🔴 **PENDING** - Needs implementation

---

### ❌ Issue 3: SyncEvent Schema Doesn't Track Feature Counts

**Problem:**
AC4 shows `run_background_refresh()` returning `features_refreshed` count, but `SyncEvent` ORM model and `log_sync_event_complete()` only persist `tests_discovered` and `tests_refreshed`. Feature counts would be dropped.

**Current State:**
```python
# src/testio_mcp/models/orm/sync_event.py
class SyncEvent(SQLModel, table=True):
    tests_discovered: int | None = Field(default=None)
    tests_refreshed: int | None = Field(default=None)
    # ❌ Missing: features_refreshed field
```

**Fix Required:**
- Add `features_refreshed: int | None = Field(default=None)` to SyncEvent ORM
- Create Alembic migration for schema change
- Update `log_sync_event_complete()` to accept `features_refreshed` parameter
- Update all call sites to pass feature counts

**Status:** 🔴 **PENDING** - Needs design decision (extend SyncEvent vs separate table)

---

### ❌ Issue 4: Background Refresh API Mismatch

**Problem:**
AC4 shows `run_background_refresh()` as a single-run function returning a dict, but the real implementation is a **long-running loop** with `interval_seconds` parameter and no return value. Tests in AC10/AC11 that call it directly would hang.

**Current State:**
```python
# src/testio_mcp/database/cache.py
async def run_background_refresh(self, interval_seconds: int, since_filter: str | None = None) -> None:
    """Long-running loop - runs forever"""
    while True:
        await asyncio.sleep(interval_seconds)
        # ... refresh logic ...
        # ❌ Never returns!
```

**Fix Required:**
- Extract single-cycle logic into new helper: `async def _run_background_refresh_cycle() -> dict`
- Keep existing `run_background_refresh()` as long-running wrapper (calls `_run_background_refresh_cycle()` in loop)
- Update tests to call `_run_background_refresh_cycle()` (single execution)
- Update AC4 to show both methods

**Status:** 🔴 **PENDING** - Requires refactoring

---

### ❌ Issue 5: Incomplete Test Mocking

**Problem:**
AC9, AC10, AC11 test sketches instantiate `PersistentCache(...)` without required dependencies, don't mock repository calls or feature syncs (would hit DB/API), and reference the long-running refresh function. Tests would fail or hang.

**Issues:**
- `PersistentCache(...)` - what arguments?
- No mocking of `FeatureRepository.sync_features()` (would hit API)
- No mocking of `ProductRepository.get_product()` (would hit DB)
- No time freezing for deterministic staleness tests
- Product IDs inconsistent (uses 598 vs 21362/18559 from other stories)

**Fix Required:**
- Use proper pytest fixtures: `cache: PersistentCache` (injected)
- Mock `FeatureRepository.sync_features()` in unit tests
- Use `freezegun` or `unittest.mock` for time-based tests
- Standardize on product ID 21362 (Flourish) across Epic-005 tests
- Show complete test setup with all required mocks

**Status:** 🔴 **PENDING** - Tests need complete rewrite

---

### ❌ Issue 6: Manual/CLI Sync Not Wired

**Problem:**
Story only covers background sync and tool calls. Manual `testio-mcp sync` command would still skip features unless explicitly added. No AC mentions wiring features into initial/CLI sync paths.

**Missing Coverage:**
- `PersistentCache.initial_sync()` - should sync features?
- CLI `sync` command - should refresh features?
- Or is background sync the only way? (needs explicit decision)

**Fix Required:**
- Add AC for initial sync integration (or document why not needed)
- Add AC for CLI sync integration (or document why not needed)
- Clarify in story: "Features only sync via background task" (if true)

**Status:** 🔴 **PENDING** - Design decision needed

---

### ❌ Issue 7: Code Duplication - No Shared Staleness Helper

**Problem:**
Staleness check logic is duplicated across: `cache.refresh_features()`, `list_features` tool, `list_user_stories` tool, and both REST endpoints. ADR-015 mentions `_is_stale()` helper but no AC implements it.

**Duplicated Logic (5 places):**
```python
if product and product.features_synced_at:
    seconds_since_sync = (now - product.features_synced_at).total_seconds()
    if seconds_since_sync < settings.FEATURE_CACHE_TTL_SECONDS:
        # Fresh
    else:
        # Stale
```

**Fix Required:**
- Add AC for shared staleness helper method
- Extract `_is_features_stale(product: Product) -> bool` helper
- Update all code snippets to use helper
- Reduce duplication from 5 copies to 1 implementation

**Status:** 🔴 **PENDING** - Needs AC addition

---

## Minor Issues

### ⚠️ Issue 8: Status Label Inconsistency

**Problem:**
Front matter uses `status: pending`, but STORY-035A/036/037 use `status: todo` or `status: blocked`.

**Fix:** Change `status: pending` → `status: todo` for consistency.

**Status:** ✅ **FIXED**

---

## Recommended Action Plan

### Phase 1: ORM + Schema (2 hours)
1. ✅ Add `features_synced_at` to Product ORM (AC1)
2. Generate Alembic migration (AC2)
3. Add `features_refreshed` to SyncEvent ORM (new AC)
4. Generate Alembic migration for SyncEvent

### Phase 2: Repository Layer (1 hour)
5. Implement `ProductRepository.get_product()` method
6. Implement `ProductRepository.update_features_last_synced()` method
7. Implement shared staleness helper: `_is_features_stale()`

### Phase 3: Background Sync Refactor (1.5 hours)
8. Extract `_run_background_refresh_cycle()` single-execution helper
9. Update `run_background_refresh()` to call helper in loop
10. Add Phase 3 (features) to single-cycle helper

### Phase 4: Tool + API Integration (1 hour)
11. Update `list_features` tool with staleness check (use helper)
12. Update `list_user_stories` tool with staleness check (use helper)
13. Update REST endpoints with staleness check (use helper)

### Phase 5: Testing (2 hours)
14. Write unit tests with proper mocking (freeze time, mock repos)
15. Write integration tests (use single-cycle helper, not loop)
16. Standardize on product ID 21362 across all tests

### Phase 6: Manual Sync Decision (30 minutes)
17. Decide: Should initial_sync/CLI sync also refresh features?
18. Document decision in story
19. Implement if yes, skip if no (background-only)

**Total Estimated Effort:** 8 hours (up from original 3-4 hours)

---

## Codex's Final Notes

**Consistency vs STORY-037:**
- Structure and tone largely match 037 (front matter + Background + ACs) ✅
- Acceptance criteria are more prescriptive (inline code blocks) ✅
- Status label fixed (pending → todo) ✅

**Soundness:**
- Architectural approach is correct (staleness pattern, Phase 3 integration)
- References to ADR-013 and ADR-015 are appropriate
- Epic-005 integration is well thought out

**Completeness:**
- Missing critical pieces (ORM fields, repository methods, observability)
- Test coverage needs significant detail
- Manual sync path ambiguous

**Verdict:** Story is 70% ready. With fixes applied, implementation can proceed safely.

---

## Next Steps

1. **User Decision:** Should manual/CLI sync also refresh features? (Issue 6)
2. **User Decision:** Extend SyncEvent model or create separate feature_sync_events table? (Issue 3)
3. **Apply Fixes:** Update STORY-038 with all required ACs
4. **Re-Review:** Optional second Codex review after fixes

**Recommendation:** Address Issues 1-7 before starting implementation. Estimate revised to **8 hours** total.
