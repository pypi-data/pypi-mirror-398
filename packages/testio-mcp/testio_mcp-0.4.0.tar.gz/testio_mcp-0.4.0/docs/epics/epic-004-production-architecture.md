---
epic_id: EPIC-004
title: Production-Ready Architecture Rewrite
status: completed
created: 2025-01-17
completed: 2025-01-20
priority: critical
estimate: 7 story points (2 weeks)
dependencies: [EPIC-002]
release_version: 0.2.0
---

## Epic Overview

**As a** development team
**We want** to refactor the architecture to SQLite-first, HTTP transport, and hybrid MCP+REST
**So that** we have a production-ready, scalable, maintainable system with no database conflicts

## Business Value

- **Performance:** 8x faster list queries (SQLite vs API)
- **Reliability:** Single server process eliminates database lock conflicts
- **Extensibility:** REST API enables web dashboards, integrations
- **Simplicity:** -1200 lines of code (-30%), single data source
- **Production Ready:** HTTP transport + Swagger docs

## Research Validation

All patterns validated through external research:
- ✅ FastMCP HTTP transport (native support)
- ✅ FastAPI Swagger (auto-generation)
- ✅ Hybrid MCP+REST deployment (documented pattern)
- ✅ SQLite-first performance (proven at scale)

**Research Documents:** `docs/architecture/wip/` (9 documents, ~4780 lines)

## The Four Pillars

### 1. SQLite-Always (Single Source of Truth)
- SQLite is the only data store
- No in-memory cache complexity
- Simpler testing, simpler architecture

### 2. List vs Get Pattern
- **Lists:** SQLite queries (~10ms, background-synced)
- **Get:** Refresh then query (always fresh)
- Smart balance of performance and freshness

### 3. HTTP Transport
- Single server process (no more spawning per client)
- Visible logs in terminal
- Multiple clients connect to one server

### 4. Hybrid MCP+REST
- `/mcp` - MCP protocol (Claude Code, Cursor)
- `/api/*` - REST endpoints (web apps)
- `/docs` - Automatic Swagger UI

## Technical Validation

**Codex Review:**
> "The rewrite direction—SQLite-first, HTTP transport, and clear service/formatter separation—is strong. This preserves validated business logic, keeps the codebase working through each step."

**Gemini Review:**
> "The 'Four Pillars' architecture is excellent. The move to a single SQLite source of truth and a centralized HTTP server is the correct path forward."

## Stories

1. **STORY-023a:** HTTP Transport (0.5 pts) - Single server process
2. **STORY-023b:** Extract Shared Utilities (1 pt) - Prerequisites for STORY-019
3. **STORY-023c:** SQLite-First Foundation (2 pts) - Repository layer + delete cache
4. **STORY-023d:** Service Refactoring + Delete Legacy (2 pts) - Clean service layer
5. **STORY-023e:** MultiTestReportService (1.5 pts) - STORY-019a implementation
6. **STORY-023f:** Hybrid MCP+REST (0.5 pts) - Production deployment

**Total:** 7.5 story points

## Success Metrics

### Performance
| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| list_tests | ~80ms | ~10ms | **8x faster** |
| get_test_status | ~100ms | ~70ms | 30% faster |
| Multi-client DB access | Fails | Works | ✅ Fixed |

### Code Metrics
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total LOC | 4122 | ~2900 | -1200 (-30%) |
| Services | 5 | 3 | -2 |
| Repositories | 1 | 4 | +3 |
| Data sources | 2 | 1 | -1 (SQLite only) |

### Architecture Quality
- ✅ Single data source (no cache layer)
- ✅ Shared utilities (no duplication)
- ✅ Repository pattern (clean separation)
- ✅ Production-ready (HTTP + Swagger)

## Implementation Timeline

**Week 1:** Foundation (HTTP + Utilities + SQLite-first)
- Day 1: HTTP Transport
- Day 2: Extract Utilities (date_filters, bug_classifiers)
- Days 3-4: SQLite-First Foundation (repositories)
- Day 5: Service Refactoring

**Week 2:** Modern Features (EBR + REST + Deploy)
- Day 1: Delete Legacy Services
- Days 2-3: MultiTestReportService (STORY-019a)
- Day 4: Hybrid MCP+REST API
- Day 5: Production deployment + testing

## Risks & Mitigation

### Critical Risk: STORY-019 Dependencies
**Risk:** ActivityService deletion blocks STORY-019a utility extraction
**Mitigation:** Extract utilities FIRST (Day 2), then delete services (Day 5-6)

### High Risk: Cache Deletion Before Proof
**Risk:** Performance regression without load testing
**Mitigation:** Build repositories first, prove SQLite-first works, then delete cache

### Medium Risk: Feature Vacuum
**Risk:** Losing functionality before replacement ready
**Mitigation:** Extract → Refactor → Build New → Delete Old (safe sequence)

## Dependencies

**Upstream:**
- EPIC-002 (Local Data Store) - Complete ✅
- STORY-021 (Incremental Sync) - Complete ✅

**Downstream:**
- STORY-010 (Multi-tenant) - Deferred
- Future EBR enhancements

## References

- **Architecture Docs:** `docs/architecture/wip/FINAL-ARCHITECTURE-PLAN.md`
- **Research:** `docs/architecture/wip/RESEARCH-SUMMARY.md`
- **Technical Reviews:** Codex + Gemini validation (2025-01-17)

---

**Epic Status:** ✅ COMPLETED
**Approval:** Technical validation complete (Codex, Gemini)
**Completed:** 2025-01-20
