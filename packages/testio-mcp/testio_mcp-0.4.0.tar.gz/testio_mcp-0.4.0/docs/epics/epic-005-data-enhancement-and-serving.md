# Epic-005: Data Enhancement and Serving

## 1. Overview

**Goal:** Add Features and User Stories as first-class entities in the local database to enable advanced analytics and complete product catalog visibility.

**Motivation:**
- **Complete Catalog:** Current database only shows features that have been *tested*. We need the full catalog of what *could* be tested.
- **Advanced Analytics:** Enable queries like "Bug Density per Feature", "Untested Features", "Test Coverage by User Story".
- **Independent Lifecycle:** Features can be updated/renamed without re-syncing old tests.
- **Cleaner Code:** Replace JSON blob parsing with SQL queries.

## 2. Scope

Add three new first-class entities with repositories and sync:
- **Features:** Testable features of a product (from `/products/{id}/features` or `/products/{id}/sections/{sid}/features`)
- **User Stories:** User journeys and acceptance criteria (from `/products/{id}/user_stories`)
- **Users:** Tester metadata extracted from bug reports

**Deferred to Future Epic:**
- **TestFeature Junction Table:** Test-to-feature relationships will remain in JSON blobs (`test.features`) for now. Adding the junction table requires more nuanced handling and will be easier once base ORM architecture is established.

**Stories:** 5 total + 1 prerequisite sub-story
- **STORY-035C AC0:** Section Detection Helper (PREREQUISITE - must complete first)
- STORY-035A: Features Repository & Sync (depends on 035C AC0)
- STORY-035B: User Stories Repository & Sync (depends on 035A)
- STORY-035C: API Contract Testing & Monitoring (AC1-AC6)
- STORY-036: User Metadata Extraction
- STORY-037: Data Serving Layer (MCP Tools + REST API)

## 3. Prerequisites (CRITICAL - Epic 006 Must Complete First)

**Epic-005 CANNOT begin until Epic-006 (ORM Refactor) is complete and merged.**

### 3.1. Epic 006 Completion Gate

**✅ ALL PREREQUISITES SATISFIED (2025-11-23)**

**Required before ANY Epic-005 work:**

1. ✅ **Epic 006 fully merged to main**
   - All 8 stories (STORY-030 through STORY-034B) complete ✅
   - All tests passing (335 unit tests, 39 integration tests) ✅
   - Performance baseline met (see below) ✅

2. ✅ **Alembic baseline established**
   - Baseline Revision: **`0965ad59eafa`** (documented in Epic 006)
   - Run: `alembic current` → shows `0965ad59eafa (head)` ✅
   - Run: `alembic heads` → returns exactly ONE revision ✅

3. ✅ **All repositories using AsyncSession**
   - Run: `grep -r "aiosqlite.Connection" src/` → returns empty ✅
   - TestRepository, BugRepository, ProductRepository all use SQLModel ✅

4. ✅ **Performance baseline met (Measured 2025-11-23)**
   - `list_tests()` p95 = **1.93ms** < 20ms threshold ✅ (90% faster)
   - `list_products()` p95 = **2.69ms** < 15ms threshold ✅ (82% faster)
   - No N+1 query issues ✅
   - Benchmarks: `scripts/benchmark_list_products.py`, `scripts/benchmark_list_tests.py`

5. ✅ **Migration infrastructure working**
   - Server starts successfully with migrations applied ✅
   - `TESTIO_SKIP_MIGRATIONS` env flag implemented ✅
   - SQLite JSON1 extension verified ✅

**Epic 005 Status:** ✅ **COMPLETED**

### 3.2. Migration Chain Management

**Epic 005 migrations MUST chain from Epic 006 baseline:**

```bash
# Before generating ANY Epic 005 migration:
# 1. Verify single migration head
alembic heads  # Must return exactly one revision

# 2. Verify at head
alembic current  # Must be at head

# 3. If not, rebase branch and resolve conflicts
git rebase main
alembic upgrade head
```

**Epic 005 Alembic Migration Pattern:**
```python
# In migration file header
\"\"\"Add features and user_stories tables

Revision ID: <new_revision_id>
Revises: <epic_006_baseline_revision_id>  # ← CRITICAL: Reference Epic 006 baseline
Create Date: 2025-11-22
\"\"\"
```

### 3.3. Rollback Order

If Epic 005 needs to be rolled back:

```bash
# Snapshot database first
cp ~/.testio-mcp/cache.db ~/.testio-mcp/cache.db.backup

# Rollback Epic 005 completely
alembic downgrade <epic-006-baseline-revision-id>

# If needed, rollback Epic 006 too
alembic downgrade base  # Back to pre-ORM state
```

---

## 4. Strategy

**"Catalog-First" Approach:**
1. **Schema:** Define SQLModel classes for Features and User Stories ✅ (STORY-035A)
2. **Repositories:** Implement FeatureRepository and UserStoryRepository with section-aware sync ✅ (STORY-035A, ADR-013)
3. **Sync:** Add catalog sync to background refresh (Products → Features → User Stories → Tests) ⚠️ (STORY-038 - sync integration)
4. **Serve:** Expose new entities via MCP tools and REST API ✅ (STORY-037)

**Note (2025-11-24):** During STORY-037 implementation, discovered that sync orchestration (step 3) was not implemented. STORY-038 completes this integration using staleness pattern (1-hour TTL) for features.

**Key Technical Challenge:** Products can be organized with or without sections, requiring different API endpoints (see Design Doc Section 6).

---

## 5. Stories

### STORY-035C AC0: Section Detection Helper (OPTIONAL ENHANCEMENT)

**✅ STATUS: Research Validated - No Blocker (2025-11-23)**

**User Story:**
As a developer implementing section-aware repositories,
I want a shared section detection helper,
So that FeatureRepository and UserStoryRepository can reuse the same logic.

**Background - Research Validation (2025-11-23):**
- Research script logic VALIDATED as CORRECT: `len(sections) > 0 OR len(sections_with_default) > 1`
- Tested with real API:
  - Flourish (21362): `sections_with_default=[default-section]` (len=1) → non-section endpoint works ✅
  - Canva (18559): `sections=[...]` (len=2) → section endpoint required (422 without) ✅
- **Key Insight:** Default-section (single item) indicates legacy non-section product
- **Decision:** Repositories can implement logic directly OR use shared helper (optional)

**Acceptance Criteria:**

1. [ ] Shared helper created: `src/testio_mcp/utilities/section_detection.py`
2. [ ] `has_sections(product: dict) -> bool` implemented with research logic: `len(sections) > 0 OR len(sections_with_default) > 1`
3. [ ] `get_section_ids(product: dict) -> list[int]` implemented
4. [ ] Unit test file created: `tests/unit/test_section_detection.py`
5. [ ] Test cases: no sections, default-section, single real section, multi-section, malformed
6. [ ] All unit tests pass: `uv run pytest tests/unit/test_section_detection.py -v`
7. [ ] Type checking passes: `mypy src/testio_mcp/utilities/section_detection.py --strict`
8. [ ] Helper documented with docstrings and examples

**Estimated Effort:** 30 minutes

**Does NOT Block:** STORY-035A, STORY-035B (can proceed in parallel)

---

### STORY-035A: Features Repository & Sync

**Dependencies:** None (research validated, can proceed independently)

**User Story:**
As a developer analyzing feature coverage,
I want features stored as first-class entities in the database,
So that I can query "Which features have the most bugs?" without parsing JSON blobs.

**Acceptance Criteria:**

1. [ ] `Feature` SQLModel class created in `src/testio_mcp/models/orm/feature.py`
2. [ ] Model includes: `id`, `product_id`, `section_id`, `title`, `description`, `howtofind`, `raw_data`, `last_synced`
3. [ ] Relationships defined: `product`, `user_stories` (TestFeature junction deferred to future epic)
4. [ ] `FeatureRepository` created in `src/testio_mcp/repositories/feature_repository.py`
6. [ ] Repository inherits from `BaseRepository` (from Epic 006)
7. [ ] **CRITICAL:** Repository imports and uses `has_sections()` and `get_section_ids()` from STORY-035C AC0
8. [ ] `sync_features()` method implements section-aware sync:
   - Products WITHOUT sections: `GET /products/{id}/features`
   - Products WITH sections: `GET /products/{id}/sections/{sid}/features` (undocumented endpoint)
9. [ ] Concurrency control: Sync reuses existing client semaphore with per-product cap (2-3 concurrent section calls)
10. [ ] Defensive pattern: Use `client.get_with_retry()` for section calls (exponential backoff already implemented)
11. [ ] Alembic migration generated: `alembic revision --autogenerate -m "Add features table"`
12. [ ] Migration includes indexes: `idx_features_product_id`, `idx_features_section_id`
13. [ ] Unit tests pass: FeatureRepository CRUD operations (100% success rate)
14. [ ] Integration test: Sync features for non-section product (Product 21362: 28 features)
15. [ ] Integration test: Sync features for section product (Product 18559: 288+ features across sections)
16. [ ] **NEW:** Integration test: Sync features for single-section product (Product 24959: 8 features, section 25543)
17. [ ] Performance: Feature sync completes in < 30 seconds for product with 10 sections
16. [ ] Type checking passes: `mypy src/testio_mcp/repositories/feature_repository.py --strict`

**Tasks:**
- Define Feature SQLModel class (TestFeature junction deferred)
- Create FeatureRepository with section-aware sync logic and concurrency control
- Generate Alembic migration
- Write unit and integration tests
- Validate with real API (Products 21362, 18559, 24959)

**Estimated Effort:** 4 hours

---

### STORY-035B: User Stories Repository & Sync

**Dependencies:** STORY-035A (Feature repository), STORY-035C AC0 (section detection helper)

**User Story:**
As a developer analyzing test coverage,
I want user stories stored as first-class entities linked to features,
So that I can query "Which user stories are untested?" for sprint planning.

**Acceptance Criteria:**

1. [ ] `UserStory` SQLModel class created in `src/testio_mcp/models/orm/user_story.py`
2. [ ] Model includes: `id`, `product_id`, `section_id`, `feature_id`, `title`, `requirements`, `raw_data`, `last_synced`
3. [ ] Relationship defined: `feature` (back_populates with Feature.user_stories)
4. [ ] `UserStoryRepository` created in `src/testio_mcp/repositories/user_story_repository.py`
5. [ ] Repository inherits from `BaseRepository` (from Epic 006)
6. [ ] **CRITICAL:** Repository imports and uses `has_sections()` and `get_section_ids()` from STORY-035C AC0 (SAME helper as FeatureRepository)
7. [ ] `sync_user_stories()` method implements section-aware logic:
   - Products WITHOUT sections: `GET /products/{id}/user_stories`
   - Products WITH sections: `GET /products/{id}/user_stories?section_id={sid}` (required param)
8. [ ] **Data consistency validation (Codex recommendations):**
   - `user_story.product_id == feature.product_id` → FATAL (raise exception)
   - `user_story.section_id == feature.section_id` → WARNING (log and continue)
   - Missing `feature_id` → Store as NULL, flag row, emit warning
9. [ ] Concurrency control: Sync reuses existing client semaphore with per-product cap (2-3 concurrent section calls)
10. [ ] Defensive pattern: Use `client.get_with_retry()` for section calls (exponential backoff already implemented)
11. [ ] Alembic migration generated: `alembic revision --autogenerate -m "Add user_stories table"`
12. [ ] Migration includes indexes: `idx_user_stories_product_id`, `idx_user_stories_section_id`, `idx_user_stories_feature_id`
13. [ ] Unit tests pass: UserStoryRepository CRUD operations (100% success rate)
14. [ ] Integration test: Sync user stories for non-section product (Product 21362: 54 user stories)
15. [ ] Integration test: Sync user stories for section product (Product 18559: 1,709+ user stories)
16. [ ] **NEW:** Integration test: Sync user stories for single-section product (Product 24959: 9 user stories, section 25543)
17. [ ] Data consistency test: Validates product_id (FATAL) and section_id (WARNING) enforcement
18. [ ] Performance: User story sync completes in < 45 seconds for product with 10 sections
19. [ ] Type checking passes: `mypy src/testio_mcp/repositories/user_story_repository.py --strict`

**Tasks:**
- Define UserStory SQLModel class
- Create UserStoryRepository with section-aware sync and consistency validation
- Generate Alembic migration
- Write unit and integration tests with consistency checks
- Validate with real API (Products 21362, 18559, 24959)

**Estimated Effort:** 3-4 hours

**Prerequisites:** STORY-035A must be complete (UserStory references Feature)

---

### STORY-035C: API Contract Testing & Monitoring

**Dependencies:** STORY-035A and STORY-035B (validates their sync logic)

**Note:** AC0 (section detection helper) is the PREREQUISITE for the entire epic and must complete first.

**User Story:**
As a developer maintaining undocumented API integrations,
I want automated contract tests and health monitoring for features/user stories endpoints,
So that API changes don't silently break production sync.

**Acceptance Criteria:**

**AC0: Section Detection Helper (PREREQUISITE - See separate story above)**

**AC1-AC6: Contract Testing & Monitoring (After 035A/B complete)**

1. [ ] Contract test suite created in `tests/integration/test_api_contracts.py` with **14 tests** (9 original + 5 Codex enhancements)
2. [ ] Test: Non-section product features endpoint (`GET /products/{id}/features`) returns 200
3. [ ] Test: Section product features endpoint (`GET /products/{id}/sections/{sid}/features`) returns 200
4. [ ] Test: Section product features without section fails with 422 (validates endpoint requirement)
5. [ ] **NEW:** Test: Single-default-section product features (Product 24959, critical bug case)
6. [ ] **NEW:** Test: Schema field TYPE validation (not just presence - detects id becoming string)
7. [ ] **NEW:** Test: Pagination sentinel (warn if > 2000 items, detect pagination keys)
8. [ ] **NEW:** Test: 422→section fallback pattern (defensive probe)
9. [ ] **NEW:** Test: Minimal concurrency (2 sections in parallel)
10. [ ] Test: Non-section product user stories endpoint (`GET /products/{id}/user_stories`) returns 200
11. [ ] Test: Section product user stories with section_id param returns 200
12. [ ] Test: Section product user stories without section_id param fails with 500 (validates param requirement)
13. [ ] Test: Response schemas validated (features have `id`, `title`, `description`, `howtofind` with correct types)
14. [ ] Test: Response schemas validated (user_stories have `id`, `title`, `requirements`, `feature_id` with correct types)
15. [ ] CI workflow updated: Contract tests run on every PR and daily at 6 AM UTC
16. [ ] Sync event logging: Features sync logged to `sync_events` table with success/failure
17. [ ] Sync event logging: User stories sync logged to `sync_events` table with success/failure and validation_warnings
18. [ ] `get_sync_history` MCP tool shows features/user stories sync events
19. [ ] All contract tests pass (100% success rate)
20. [ ] Type checking passes: `mypy tests/integration/test_api_contracts.py --strict`

**Tasks:**
- Create contract test suite for features and user stories endpoints
- Add response schema validation
- Update CI workflow to run contract tests
- Add sync event logging to repositories
- Validate `get_sync_history` shows new sync events

**Estimated Effort:** 3 hours

**Prerequisites:** STORY-035A and STORY-035B must be complete (tests validate their sync logic)

**Note:** Complete BEFORE widespread feature sync rollout to production

---

### STORY-036: User Metadata Extraction

**User Story:**
As a CSM analyzing tester engagement,
I want user metadata (tester names, roles, activity) extracted from bug reports,
So that I can identify top contributors and engagement patterns.

**Acceptance Criteria:**

1. [ ] `User` SQLModel class created in `src/testio_mcp/models/orm/user.py`
2. [ ] Model includes: `id`, `username`, `email`, `role`, `raw_data`, `last_seen`
3. [ ] `UserRepository` created in `src/testio_mcp/repositories/user_repository.py`
4. [ ] Repository inherits from `BaseRepository` (from Epic 006)
5. [ ] Bug sync enhanced: Extract user data from `bug.reported_by` and store in `users` table
6. [ ] User deduplication: Upsert logic prevents duplicate user records
7. [ ] Relationship added: `Bug.reported_by_user` (foreign key to users table)
8. [ ] Alembic migration generated: `alembic revision --autogenerate -m "Add users table and bug.reported_by_user_id"`
9. [ ] Migration includes index: `idx_users_username`
10. [ ] Unit tests pass: UserRepository CRUD operations (100% success rate)
11. [ ] Integration test: Bug sync populates users table correctly
12. [ ] Integration test: User deduplication works (same user across multiple bugs)
13. [ ] Type checking passes: `mypy src/testio_mcp/repositories/user_repository.py --strict`

**Tasks:**
- Define User SQLModel class
- Create UserRepository with upsert logic
- Enhance BugRepository to extract and link user data
- Generate Alembic migration
- Write unit and integration tests

**Estimated Effort:** 3 hours

**Prerequisites:** Epic 006 complete (uses ORM patterns)

---

### STORY-037: Data Serving Layer (MCP Tools + REST API)

**User Story:**
As a user querying product data via AI or web apps,
I want MCP tools and REST endpoints to expose features, user stories, and user metadata,
So that I can analyze test coverage and tester engagement without direct database access.

**Acceptance Criteria:**

1. [ ] MCP tool created: `list_features(product_id, section_id=None, force_refresh_features=False)` - List features with optional section filter and cache bypass parameter
2. [ ] MCP tool created: `list_user_stories(product_id, feature_id=None, section_id=None, force_refresh_features=False)` - List user stories with filters and cache bypass parameter
3. [ ] MCP tool created: `list_users(role=None)` - List testers with optional role filter
4. [ ] REST endpoint created: `GET /api/products/{id}/features` - List features for product
5. [ ] REST endpoint created: `GET /api/products/{id}/user_stories` - List user stories for product
6. [ ] REST endpoint created: `GET /api/users` - List users
7. [ ] Service layer created: `FeatureService` with business logic (filtering, aggregation)
8. [ ] Service layer created: `UserStoryService` with business logic (feature grouping, filtering)
9. [ ] Service layer created: `UserService` with business logic (top contributors, activity metrics)
10. [ ] All MCP tools work correctly (end-to-end integration tests)
11. [ ] All REST endpoints work correctly (integration tests)
12. [ ] Swagger docs updated: `/docs` shows new endpoints with examples
13. [ ] Performance: `list_features` completes in < 50ms for product with 300 features
14. [ ] Performance: `list_user_stories` completes in < 100ms for product with 1,000 stories
15. [ ] Type checking passes: `mypy src/testio_mcp/tools/ src/testio_mcp/services/ --strict`

**Tasks:**
- Create FeatureService, UserStoryService, UserService
- Implement 3 new MCP tools (features, user stories, users)
- Implement 3 new REST endpoints (features, user stories, users)
- Write integration tests for all tools and endpoints
- Update Swagger documentation
- Validate performance targets

**Estimated Effort:** 4-5 hours

**Prerequisites:** STORY-035A, STORY-035B, STORY-036 must be complete (serves their data)

---

### STORY-038: Feature Sync Integration

**Status:** 🟡 **PENDING** (Added 2025-11-24 via Correct Course workflow)

**User Story:**
As a developer validating Epic-005 deliverables,
I want features automatically synced via background refresh and on-demand tool calls,
So that MCP tools return populated data and catalog visibility is achieved.

**Background:**
During STORY-037 implementation, discovered that Features and Users tables exist with functional repositories, but **sync orchestration was never implemented**. Features table remains empty because nothing populates it during background sync or CLI sync operations.

**Acceptance Criteria:**

1. [ ] Schema: `features_synced_at` column added to `products` table (nullable datetime)
2. [ ] Schema: Alembic migration generated and tested
3. [ ] Config: `FEATURE_CACHE_TTL_SECONDS` added to `config.py` (default: 3600 seconds)
4. [ ] Config: `FEATURE_CACHE_TTL_SECONDS` added to `.env.example` with documentation
5. [ ] Background sync: `PersistentCache.refresh_features()` method implemented
6. [ ] Background sync: Checks staleness (`products.features_synced_at` vs TTL)
7. [ ] Background sync: Integrated as Phase 3 in `run_background_refresh()`
8. [ ] Background sync: Skips refresh if features fresh (< TTL)
9. [ ] Background sync: Error handling (log errors, continue with next product)
10. [ ] Tool: `list_features` checks staleness before returning cached data
11. [ ] Tool: `force_refresh=True` parameter bypasses staleness check
12. [ ] Tool: Updates `products.features_synced_at` after refresh
13. [ ] ProductRepository: `update_features_last_synced()` helper method
14. [ ] Unit tests: Staleness logic (mock scenarios)
15. [ ] Integration tests: Background sync refreshes features
16. [ ] Integration tests: Tool staleness check behavior
17. [ ] Integration tests: Force refresh bypasses cache
18. [ ] Documentation: ADR-015 created (Feature Staleness Strategy)
19. [ ] Documentation: CLAUDE.md updated (sync flow diagram)
20. [ ] Documentation: README.md updated (configuration section)
21. [ ] Validation: Background sync logs show features being refreshed
22. [ ] Validation: `list_features` tool returns populated data

**Tasks:**
- Add `features_synced_at` column to products table
- Add `FEATURE_CACHE_TTL_SECONDS` configuration
- Implement `refresh_features()` with staleness check
- Integrate into background sync as Phase 3
- Update `list_features` tool with staleness check
- Add `update_features_last_synced()` to ProductRepository
- Write unit and integration tests
- Create ADR-015 documentation
- Update CLAUDE.md and README.md

**Estimated Effort:** 3-4 hours

**Prerequisites:** STORY-035A complete (FeatureRepository functional)

**Blocks:** Epic-005 validation (features table must be populated to test MCP tools)

---

## 6. Success Criteria (ALL must pass before Epic complete)

**Data Model:**
- Features, UserStories, Users tables exist in database
- Relationships working (Feature ↔ UserStory, Feature ↔ Product, UserStory ↔ Feature)
- All indexes created and used by queries
- Test-feature relationships remain in JSON blobs (deferred to future epic)

**Sync:**
- Features sync works for both section and non-section products
- User stories sync works for both product types
- User metadata extracted from bug reports
- All sync events logged to `sync_events` table
- Background sync includes catalog sync (Products → Features → User Stories → Tests)

**Data Quality:**
- Data consistency validation prevents mismatched product_id/section_id
- User deduplication prevents duplicate user records
- Concurrency control prevents API 500s during sectioned product sync

**API:**
- 3 new MCP tools working correctly (list_features, list_user_stories, list_users)
- 3 new REST endpoints working correctly
- Swagger docs updated
- All integration tests passing (100% success rate)

**Performance:**
- Feature sync: < 30 seconds for product with 10 sections
- User story sync: < 45 seconds for product with 10 sections
- `list_features`: < 50ms for 300 features
- `list_user_stories`: < 100ms for 1,000 stories

**Code Quality:**
- All tests pass (100% success rate)
- Test coverage maintained at >90%
- Type checking passes: `mypy src/ --strict`
- No regressions in existing functionality

**Migration Management:**
- All migrations chain from Epic 006 baseline
- `alembic heads` returns exactly one revision
- All migration `downgrade()` functions tested
- Rollback procedures documented and tested

---

## 7. Deferred Stories

### STORY-038: Advanced Analytics Tools (DEFERRED)

**Rationale:** Scope already considerable with 5 active stories. Foundation (Features, User Stories, Users) must be solid before adding analytics.

**Recommendation:** Create "Epic 007: Advanced Analytics" after Epic 005 deployment.

**Proposed Analytics:**
- Bug density per feature
- Test coverage heatmap
- Untested features report
- Tester engagement metrics
- Year-over-year trend analysis

**No Impact on EBR Tool:** Existing `generate_ebr_report` continues to work (no regression).

---

## 8. Rollback Strategy

**Per-Story Rollback:**
```bash
# Revert code changes
git revert <commit-hash>

# Rollback database migration
alembic downgrade -1

# Resync data
rm ~/.testio-mcp/cache.db
uv run python -m testio_mcp sync --verbose
```

**Full Epic Rollback:**
```bash
# Rollback all Epic 005 migrations
alembic downgrade <epic-006-baseline-revision-id>

# Revert all Epic 005 commits
git revert <epic-005-first-commit>..<epic-005-last-commit>

# Resync database
rm ~/.testio-mcp/cache.db
uv run python -m testio_mcp sync --verbose
```

---

## 9. Notes from Design

**API Research Completed:** 2025-11-22
**Research Script:** `scripts/research_features_api.py`

**Key Findings:**
- Features endpoint: `/products/{id}/sections/{sid}/features` is **undocumented** but required for section products
- User stories endpoint: Requires `section_id` query param for section products (500 error without it)
- Section detection: Use `has_sections()` helper (checks `sections` or `sections_with_default` length)
- No pagination observed for features/user stories endpoints

**Verified Products:**
- Product 21362 (Flourish): No sections, 28 features, 54 user stories ✅
- Product 18559 (Canva): Has sections, 288+ features, 1,709+ user stories ✅
- Product 24959 (remove.bg): Has sections, 8 features (section 25543), 9 user stories ✅

**Performance Considerations:**
- Non-section product: 2 API calls (features + user stories)
- Section product (10 sections): 20 API calls (10 features + 10 user stories)
- Use existing concurrency control (semaphore) to avoid overwhelming API
- Consider rate limiting or backpressure if sync takes >2 minutes

---

## 10. Migration Chain Reference

**Epic 006 Baseline Revision:** `0965ad59eafa` (Completed 2025-11-23)

**Epic 005 Migration Chain:**
```
Epic 006 Baseline: 0965ad59eafa
  ↓
STORY-035A: Add features table
  ↓
STORY-035B: Add user_stories table
  ↓
STORY-036: Add users table and bug.reported_by_user_id
```

**Verification Commands:**
```bash
# Show current migration
alembic current

# Show migration history
alembic history

# Verify single head
alembic heads  # Must return exactly one revision
```

---

**Epic Status:** ✅ COMPLETED
**Total Estimated Effort:** 17-21 hours (5 stories)
**Dependencies:** Epic 006 (ORM Refactor) ✅ Complete
