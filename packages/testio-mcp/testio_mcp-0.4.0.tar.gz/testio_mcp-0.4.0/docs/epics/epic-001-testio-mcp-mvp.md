---
epic_id: EPIC-001
title: TestIO MCP Server MVP
status: completed
created: 2025-11-04
completed: 2025-01-04
owner: Ricardo Leon
type: greenfield
tech_stack: [Python, FastMCP, Pydantic, httpx, pytest-asyncio]
release_version: 0.1.0, 0.1.1
---

# EPIC-001: TestIO MCP Server MVP

## Epic Goal

Build an MVP Model Context Protocol (MCP) server using **FastMCP** that provides AI-first access to TestIO's Customer API, enabling non-developer stakeholders (CSMs, PMs, QA leads) to query test status, bugs, and activity through AI tools like Claude and Cursor—eliminating traditional development bottlenecks and enabling rapid prototyping.

## Strategic Context

### Problem Being Solved
- **Development Capacity Bottleneck**: Limited dev resources create delays for customizations and enhancements
- **Non-Technical User Barrier**: CSMs and PMs cannot quickly prototype solutions or query test data
- **Integration Complexity**: TestIO's powerful APIs require traditional development for integration
- **Visibility Gap**: No real-time test cycle visibility without navigating the UI

### Desired Outcome
- Non-technical stakeholders can "vibe code" new functionality through AI tools (Claude, Cursor)
- Rapid creation of "throwaway prototypes" to validate ideas before committing dev resources
- AI-first integration layer making TestIO capabilities accessible to AI agents
- Real-time test cycle visibility without UI navigation
- **Strategic Goal**: Empower AI-enabled extensibility for TestIO as part of EPAM's AI-first initiative

## Technical Architecture

### Technology Stack

**Core Framework**: FastMCP (Python MCP server library)
- **Why FastMCP**: Pythonic decorator-based API, built-in Pydantic validation, async support, excellent error handling
- **Alternative Considered**: Official MCP Python SDK (more verbose, lower-level)

**Key Dependencies**:
- **FastMCP** - MCP server framework with decorator-based tools (`@mcp.tool`)
- **Pydantic v2** - Data validation and schema generation (JSON Schema for tools)
- **httpx** - Modern async HTTP client for TestIO Customer API calls
- **pytest-asyncio** - Async testing support

**Code Quality Tools** (ALL REQUIRED):
- **Ruff** - Fast Python linter and formatter (replaces black, isort, flake8)
- **mypy** - Static type checker with strict mode enabled
  - **Policy**: NEVER use `ignore_missing_imports` without exhausting alternatives first
  - Check for `py.typed` markers, `types-*` packages, or proper type stub installation
  - If override required, use specific module names (no wildcards), document reason
- **pre-commit** - Git hooks for automated code quality checks
  - Runs ruff format, ruff check, and mypy on every commit
  - Prevents committing non-compliant code
  - Ensures consistent quality across team members

**API Integration**:
- **TestIO Customer API v2**: `https://api.test.io/customer/v2`
- **Authentication**: Token-based (`Authorization: Token <token>`)
- **Environment**: Production Sandbox (verified 2025-11-04)
- **Verified Dataset**: 225 products, 89+ exploratory tests available

### Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│       AI Client (Claude Desktop, Cursor)        │
└────────────────┬────────────────────────────────┘
                 │ MCP Protocol (stdio/SSE)
┌────────────────▼────────────────────────────────┐
│            FastMCP Server                       │
│                                                 │
│  ┌──────────────────────────────────────────┐   │
│  │         @mcp.tool Decorators             │   │
│  │  - get_test_status                       │   │
│  │  - list_active_tests                     │   │
│  │  - get_test_bugs                         │   │
│  │  - generate_status_report                │   │
│  │  - get_test_activity_by_timeframe        │   │
│  └──────────────────────────────────────────┘   │
│                                                 │
│  ┌──────────────────────────────────────────┐   │
│  │      @mcp.resource Decorators            │   │
│  │  - products://list                       │   │
│  │  - tests://active                        │   │
│  │  - bugs://recent                         │   │
│  └──────────────────────────────────────────┘   │
│                                                 │
│  ┌──────────────────────────────────────────┐   │
│  │     TestIO API Client (httpx)            │   │
│  │  - Async request handling                │   │
│  │  - Token authentication                  │   │
│  │  - Timeout & retry logic                 │   │
│  │  - In-memory caching (TTL-based)         │   │
│  └──────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────┘
                     │ REST API (httpx)
         ┌───────────▼──────────┐
         │   TestIO Customer    │
         │      API v2          │
         │                      │
         │  - GET /products     │
         │  - GET /exploratory_ │
         │    tests             │
         │  - GET /bugs         │
         └──────────────────────┘
```

### FastMCP Implementation Pattern

```python
from fastmcp import FastMCP
from pydantic import BaseModel, Field
import httpx

mcp = FastMCP("TestIO MCP Server")

# Pydantic models for input validation + JSON Schema generation
class TestStatusInput(BaseModel):
    test_id: str = Field(description="Exploratory test ID")

# Decorator-based tool definition
@mcp.tool()
async def get_test_status(test_id: str) -> dict:
    """Get comprehensive status of a single exploratory test."""
    # Tool implementation with httpx async client
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/exploratory_tests/{test_id}",
            headers={"Authorization": f"Token {API_TOKEN}"},
            timeout=30.0
        )
        return response.json()
```

## MVP Scope

### 5 Core MCP Tools

1. **`get_test_status`** - Get comprehensive status of a single exploratory test
   - Input: `test_id` (string)
   - Output: Test config, bug summary, status, dates, review info

2. **`list_active_tests`** - List all active/running tests for a product
   - Input: `product_id` (string), `status` (enum: running|review_successful|all)
   - Output: Array of test summaries with high-level status

3. **`get_test_bugs`** - Get detailed bug information with advanced filtering
   - Input: `test_id`, `bug_type` (functional|visual|content|all), `severity` (low|high|critical|all), `status` (accepted|rejected|new|all)
   - Output: Array of bugs with full details (steps, attachments, devices)
   - **Critical Implementation Note**: `severity` field is overloaded (contains both bug type AND severity level)

4. **`generate_status_report`** - Generate executive summary for stakeholders
   - Input: `test_ids` (array), `format` (markdown|text|json)
   - Output: Formatted report with test overview table, bug metrics, critical issues

5. **`get_test_activity_by_timeframe`** - Query test activity across products by date range
   - Input: `product_ids` (array), `start_date`, `end_date`, `include_bugs` (boolean)
   - Output: Activity summary with testing type distribution, timeline data

### 3 Core MCP Resources

1. **`products://list`** - Browse available products (225 products verified)
2. **`tests://active`** - View all currently active tests
3. **`bugs://recent?limit=50`** - View recently submitted bugs

### Out of Scope (MVP)

- **Tester API integration** (requires tester-specific permissions, not suitable for CSM use case)
- Real-time tester session monitoring
- Test creation/modification (read-only for MVP)
- Bulk bug operations (accept/reject in batch)
- Real-time notifications/polling
- Advanced analytics/dashboards

## Core Use Cases

1. **"What's the status of test X?"**
   - Input: Test ID or product name
   - Output: Synthesized report with test config, bugs found (count by severity), status, review feedback, dates

2. **"Show me all active tests for Product Y"**
   - Input: Product name or ID
   - Output: List of running tests with high-level status, dates, bug counts

3. **"What bugs have been found in test X?"**
   - Input: Test ID
   - Output: Structured bug list with filtering by type/severity/status, full details (steps, attachments)

4. **"Generate a status report for stakeholder meeting"**
   - Input: Test ID(s) or product name
   - Output: Executive summary for email/Slack/presentations with key metrics, critical bugs, blockers

5. **"Show me testing activity across my products this quarter"**
   - Input: Product IDs and date range
   - Output: Activity analysis with product-wise breakdown, testing type distribution, trends

## Implementation Approach

### FastMCP Decorator Pattern
FastMCP uses Python decorators for clean, declarative tool definition:
- `@mcp.tool()` - Define tools with automatic Pydantic validation
- `@mcp.resource()` - Define resources with URI templates
- Type hints → JSON Schema generation (automatic)
- Async/await support built-in

### Pydantic for Validation
All tool inputs and outputs use Pydantic BaseModel:
- **Input validation**: Type safety, field constraints, error messages
- **JSON Schema generation**: Automatic from type hints for MCP protocol
- **Serialization**: Clean JSON output with `model_dump(by_alias=True)`

### httpx for API Calls
Modern async HTTP client for TestIO Customer API:
- **Async context manager**: `async with httpx.AsyncClient()` for connection pooling
- **Timeout configuration**: Per-request timeouts (default 30s)
- **Retry logic**: Exponential backoff for transient errors (3 attempts)
- **Error handling**: HTTP exceptions mapped to user-friendly MCP errors

### Caching Strategy (In-Memory with TTL)
Simple dictionary-based cache with expiration:
- **Products list**: 1 hour TTL (rarely changes)
- **Test lists**: 5 minutes TTL (moderate updates)
- **Bug data**: 1 minute TTL (changes frequently)
- **Cache key format**: `{endpoint}:{params_hash}`
- **Future**: Upgrade to Redis/file-based if performance requires

## Technical Implementation Details

### Bug Severity Field Handling (Critical)

**⚠️ OVERLOADED FIELD**: The TestIO API's `severity` field serves dual purposes:

**1. Bug Type Classification (non-functional bugs):**
- `severity = "visual"` → Visual/UI bugs (layout, alignment, UI problems)
- `severity = "content"` → Content bugs (text errors, typos)

**2. Severity Levels (functional bugs ONLY):**
- `severity = "critical"` → Critical severity functional bug
- `severity = "high"` → High severity functional bug
- `severity = "low"` → Low severity functional bug

**Implementation Logic (Story 4)**:
```python
def classify_bug(bug: dict) -> dict:
    """Classify bug type and severity from overloaded severity field."""
    severity_value = bug["severity"]

    if severity_value == "visual":
        return {"bug_type": "visual", "severity_level": None}
    elif severity_value == "content":
        return {"bug_type": "content", "severity_level": None}
    elif severity_value in ["low", "high", "critical"]:
        return {"bug_type": "functional", "severity_level": severity_value}
    else:
        # Unknown value - log and treat as functional
        return {"bug_type": "functional", "severity_level": "unknown"}
```

### Error Handling Patterns

**8 Failure Scenarios to Handle**:
1. **Authentication Errors** (401/403) → Clear message with `.env` guidance
2. **API Unavailability** (timeouts, 5xx) → Retry with exponential backoff
3. **Rate Limiting** (429) → Queue requests, inform user of delay
4. **Resource Not Found** (404) → Suggest using list tools to find valid IDs
5. **Invalid Parameters** → Pre-validate enums, show valid options in error
6. **Partial Data Availability** → Return partial data with warning
7. **Empty Results** (200 with empty array) → Suggest alternative queries
8. **Timeout** → Cancel request, suggest narrowing query

**Error Message Format**:
```
❌ {What failed}
ℹ️ {Why it failed}
💡 {Actionable next step}

Example:
❌ Test ID '12345' not found
ℹ️ This test may have been deleted or archived
💡 Use list_active_tests(product_id="...") to see available tests
```

### Testing Strategy

**pytest-asyncio for Async Testing**:
```python
import pytest
from fastmcp.client import Client

@pytest.fixture
async def mcp_client():
    async with Client(mcp) as client:
        yield client

@pytest.mark.parametrize("test_id,expected_status", [
    ("109363", "archived"),
    ("invalid", None),  # Should return error
])
async def test_get_test_status(mcp_client: Client, test_id: str, expected_status: str):
    result = await mcp_client.call_tool(
        name="get_test_status",
        arguments={"test_id": test_id}
    )
    # Assertions...
```

## Success Criteria

### MVP Launch Criteria
1. ✅ CSM can query test status via Claude without touching TestIO UI
2. ✅ All 5 core use cases work with real production data (225 products, 89+ tests)
3. ✅ Response times < 5 seconds for typical queries
4. ✅ Error messages are clear and actionable (8+ scenarios covered)
5. ✅ Documentation allows another CSM to install and use independently

### Quality Gates
- All 5 tools tested with real production data (Product 25073 - Affinity Studio verified)
- All 8 error scenarios handled gracefully with user-friendly messages
- Caching reduces redundant API calls (verified via logging)
- Integration verified with Claude Desktop and Cursor
- Test coverage > 80% for core tool logic

## Stories Breakdown

### Story 1: Project Setup & Authentication
**Goal**: Initialize FastMCP server with working Customer API authentication
**Estimate**: 4 hours
**File**: `docs/stories/story-001-project-setup.md`

### Story 2: Tool 1 - Get Test Status
**Goal**: Implement `get_test_status` tool with Pydantic validation
**Estimate**: 6 hours
**File**: `docs/stories/story-002-get-test-status.md`

### Story 3: Tool 2 - List Active Tests
**Goal**: Implement `list_active_tests` tool with filtering
**Estimate**: 5 hours
**File**: `docs/stories/story-003-list-active-tests.md`

### Story 4: Tool 3 - Get Test Bugs with Filtering
**Goal**: Implement `get_test_bugs` with overloaded severity field handling
**Estimate**: 8 hours
**File**: `docs/stories/story-004-get-test-bugs.md`

### Story 5: Tool 4 - Generate Status Report
**Goal**: Implement `generate_status_report` with multiple format support
**Estimate**: 6 hours
**File**: `docs/stories/story-005-generate-status-report.md`

### Story 6: Tool 5 - Test Activity by Timeframe
**Goal**: Implement `get_test_activity_by_timeframe` with date filtering
**Estimate**: 6 hours
**File**: `docs/stories/story-006-test-activity-timeframe.md`

### Story 7: MCP Resources & Caching
**Goal**: Implement 3 MCP resources and in-memory caching layer
**Estimate**: 5 hours
**File**: `docs/stories/story-007-resources-caching.md`

### Story 8: Error Handling & Polish
**Goal**: Comprehensive error handling for 8+ scenarios
**Estimate**: 6 hours
**File**: `docs/stories/story-008-error-handling.md`

### Story 9: Integration Testing & Documentation
**Goal**: End-to-end testing with AI clients and complete documentation
**Estimate**: 8 hours
**File**: `docs/stories/story-009-integration-docs.md`

**Total Estimate**: ~54 hours (≈ 7 working days for single developer)

## Dependencies

### External Services
- TestIO Customer API v2 (`https://api.test.io/customer/v2`)
- Customer API Token (production sandbox credentials)
- Claude Desktop or Cursor (for testing)

### Python Packages
```toml
[project]
dependencies = [
    "fastmcp>=2.12.0",  # Core MCP server framework
    "pydantic>=2.12.0",   # Data validation & schema generation
    "httpx>=0.28.0",     # Async HTTP client
]

[project.optional-dependencies]
dev = [
    "pytest>=8.4.0",
    "pytest-asyncio>=1.2.0",
    "pytest-cov>=7.0.0",
    "ruff>=0.8.4",         # Fast Python linter & formatter
    "mypy>=1.13.0",        # Static type checker
    "pre-commit>=4.0.0",   # Git pre-commit hooks (optional)
]
```

### Integration Points
- Claude Desktop MCP configuration (`claude_desktop_config.json`)
- Cursor MCP configuration (`.cursor/mcp.json`)
- TestIO Customer API endpoints (6 endpoints used)

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| API rate limits | High | Implement caching (1hr/5min/1min TTLs), throttling, graceful degradation |
| Authentication complexity | Medium | Clear `.env` template, validation on startup, helpful error messages |
| API schema changes | Medium | Version API clients, add schema validation, log unknown values |
| Overloaded severity field | High | Client-side filtering logic in Story 4, comprehensive testing |
| Incomplete status enums | Low | Accept any string value, log unknown for documentation |
| MCP protocol updates | Medium | Pin FastMCP version, monitor changelog, test before upgrading |

### Rollback Plan
- MCP server is additive (doesn't modify TestIO systems)
- Can be disabled by removing from AI client configuration
- No data persistence in MVP (stateless)
- No destructive operations (read-only)

## Definition of Done

**Epic is complete when:**
- [ ] All 9 stories completed with acceptance criteria met
- [ ] All 5 MCP tools working with real production data
- [ ] All 3 MCP resources accessible via `mcp://` protocol
- [ ] Caching layer operational with defined TTLs (1hr/5min/1min)
- [ ] Error handling covers 8+ failure scenarios with user-friendly messages
- [ ] Integration verified with Claude Desktop and Cursor
- [ ] Documentation complete (installation, usage, troubleshooting)
- [ ] Demo video created showing all 5 core use cases
- [ ] Another CSM can install and use independently (validation test)
- [ ] Response times < 5 seconds for typical queries
- [ ] Test coverage > 80% for core tool logic
- [ ] No regression in TestIO systems (read-only, non-invasive)

## Future Enhancements (Post-MVP)

**Phase 2 Potential Features:**
- Tester API integration (for tester-facing tools with tester authentication)
- Test creation via MCP (write operations for `POST /exploratory_tests`)
- Bulk bug operations (batch accept/reject/export)
- Issue tracker integration (Jira, Linear auto-creation from critical bugs)
- CI/CD integration (trigger tests from pipeline, post results back)
- AI-powered bug triage (auto-categorize, prioritize, deduplicate using LLM)
- Advanced reporting (custom templates, scheduled digests, PDF/CSV exports)
- Real-time notifications via Slack/Teams webhooks

## References

- **Project Brief (ARCHIVED)**: `docs/archive/planning/project-brief-mvp-v2.4.md` (v2.4, 2025-11-04 - Completed 2025-01-20)
- **FastMCP Documentation**: https://gofastmcp.com/
- **MCP Protocol Spec**: https://modelcontextprotocol.io/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **httpx Documentation**: https://www.python-httpx.org/
- **TestIO Customer API**: Blueprint (internal documentation)
- **Knowledge Base**: Archon MCP Server RAG (8 technical sources loaded)

---

**Epic Status:** ✅ COMPLETED - 2025-01-20
