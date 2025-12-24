# MCP Progressive Disclosure Research

**Research Date:** 2025-11-27
**Verification Status:** ✅ Cross-referenced against primary sources
**Context:** Preparing for Epic-008 (MCP Layer Optimization) and Epic-009 STORY-051 (sync_data tool)
**Objective:** Understand progressive disclosure patterns in MCP ecosystem and identify applicable strategies for testio-mcp

---

## Executive Summary

The MCP community has rapidly adopted **progressive disclosure patterns** following Anthropic's November 4, 2025 article ["Code Execution with MCP"](https://www.anthropic.com/engineering/code-execution-with-mcp). Multiple production implementations have achieved **85-99% token reductions** through various strategies.

**Key Insight:** Progressive disclosure is about **cognitive clarity**, not just token cost savings. Even with 2M token context windows, polluting context with 15k tokens of irrelevant tools degrades model performance.

**Critical Discovery:** `defer_loading` is a **client-side API configuration**, not a server-side code feature. MCP servers like testio-mcp don't need code changes - users configure defer_loading in their Claude API requests.

**⚠️ Client Support Uncertainty:** `defer_loading` is confirmed for Claude API but **not documented** for Claude Desktop or Claude Code. XC-MCP shows users configuring it in `claude_desktop_config.json`, but official Anthropic docs don't confirm this works. Proceed with caution.

**For testio-mcp (14 tools, ~12.8k tokens):**
- ✅ **Server-side control:** Focus on Epic-008 description slimming (benefits ALL clients, we control this)
- 🤔 **Hold defer_loading docs:** Wait for official Claude Desktop/Code support confirmation
- 🤔 **Evaluate later:** Progressive list disclosure (96% reduction for large result sets, 1-2 days effort)

---

## Timeline of Emergence

| Date | Event | Source |
|------|-------|--------|
| **Oct 2025** | MCP protocol released, static tool loading dominates | [MCP Specification](https://spec.modelcontextprotocol.io) |
| **Early Nov 2025** | Community complaints about token bloat (GitHub MCP = 50k+ tokens) | [GitHub MCP #275](https://github.com/github/github-mcp-server/issues/275) |
| **Nov 4, 2025** | Anthropic publishes "Code Execution with MCP" article proposing filesystem-based progressive disclosure (98.7% reduction: 150k → 2k tokens) | [Anthropic Blog](https://www.anthropic.com/engineering/code-execution-with-mcp) |
| **Nov 7, 2025** | XC-MCP v3.0.0 implements platform-native `defer_loading` for 29 tools (45k → 18.7k → ~0 tokens) | [XC-MCP GitHub](https://github.com/conorluddy/xc-mcp) |
| **Nov 20, 2025** | Anthropic launches "advanced-tool-use-2025-11-20" beta with Tool Search Tool and `defer_loading` API | [Claude Docs: Tool Search](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) |
| **Nov 25-27, 2025** | Production deployments: GitHub MCP dynamic toolsets, Speakeasy Gram (400 tools), widespread adoption | Community GitHub repos |

**Verdict:** Progressive disclosure transitioned from experimental to **standard best practice** within 3 weeks.

---

## Community Sentiment

### ✅ Positive Reactions

- **Token efficiency** is now a primary design constraint for MCP servers
- **Progressive disclosure** seen as essential for production deployments (>20 tools)
- **Multiple viable patterns** acknowledged (not one-size-fits-all)
- **Platform support** (`defer_loading`) praised for simplicity - **users configure, servers benefit automatically**
- **Skills pattern** valued for local customization and universal compatibility

### ⚠️ Concerns

- **Code execution pattern** lacks official implementation (Anthropic proposal only, no production examples)
- **Discovery UX** varies across clients (tool search not universally supported)
- **defer_loading** requires Claude API beta header or Desktop config (not all clients support)
- **Semantic search** requires embeddings infrastructure (may be overkill for small tool counts)
- **Dynamic toolsets** add complexity (meta-tools for discovery)

### 📈 Evolution Trajectory

1. **October 2025:** Static tools dominant, token bloat complaints emerge
2. **November 2025:** Progressive disclosure becomes standard practice
3. **Current trend:** Client-side defer_loading + server-side optimizations (minimal mode, progressive lists)
4. **Future:** Expect MCP spec updates formalizing progressive patterns

---

## 6 Production Patterns

### 1. Platform `defer_loading` (Client-Side Configuration) 🏆

**Status:** Production-ready (requires Claude API support)
**Example:** XC-MCP v3.0.0, any MCP server used with Claude's Tool Search
**Implementation:** ⚠️ **CLIENT-SIDE, NOT SERVER-SIDE**

**How Users Configure It:**

**Option A: Claude Desktop Config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "testio-mcp": {
      "command": "uvx",
      "args": ["testio-mcp"],
      "toolsets": [{
        "type": "mcp_toolset",
        "mcp_server_name": "testio-mcp",
        "default_config": {
          "defer_loading": true
        },
        "configs": {
          "list_products": {
            "defer_loading": false
          },
          "list_tests": {
            "defer_loading": false
          }
        }
      }]
    }
  }
}
```

**Option B: Claude API Request** (requires beta header):
```python
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-4-5-20250929",
    betas=["mcp-client-2025-11-20"],  # Enable MCP defer_loading support
    messages=[{"role": "user", "content": "List my tests"}],
    tools=[{
        "type": "mcp_toolset",
        "mcp_server_name": "testio-mcp",
        "default_config": {
            "defer_loading": True  # All tools deferred by default
        },
        "configs": {
            "list_products": {"defer_loading": False}  # This one loads immediately
        }
    }]
)
```

**How It Works:**
1. **Claude's Tool Search Tool** discovers deferred tools on-demand based on conversation context
2. User mentions "show me bugs" → Tool Search finds `get_test_bugs` → Full schema loaded → Tool called
3. Tools with `defer_loading: false` loaded immediately (keep 3-5 most-used tools for instant access)

**Token Reduction:**
- **85% reduction** per [Anthropic's internal testing](https://www.anthropic.com/engineering/advanced-tool-use)
- **Accuracy improvements:** Opus 4 (49% → 74%), Opus 4.5 (79.5% → 88.1%)

**Effort for testio-mcp:**
- **Server-side:** 0 minutes (no code changes needed!)
- **Documentation:** 30 minutes (add to MCP_SETUP.md with config examples)

**Compatibility:**
- ✅ **Claude API** (confirmed - requires beta header `"mcp-client-2025-11-20"`)
- ❓ **Claude Desktop** (XC-MCP docs show config example, but NOT in official Anthropic docs)
- ❓ **Claude Code** (no mention of defer_loading in [official docs](https://code.claude.com/docs/en/mcp))
- ❌ **Cursor, Zed, other clients** (load all tools, no defer_loading support)

**Best Practice:**
Keep 3-5 most-used tools always loaded (`defer_loading: false`), defer the rest:
```json
{
  "configs": {
    "list_products": {"defer_loading": false},
    "list_tests": {"defer_loading": false},
    "get_test_status": {"defer_loading": false}
    // Other 11 tools: defer_loading=true (default)
  }
}
```

**XC-MCP Evolution (Verified from [XC-MCP README](https://github.com/conorluddy/xc-mcp)):**
- v1.0: 45k tokens (29 tools with verbose descriptions)
- v2.0: 18.7k tokens (slimmed descriptions)
- v3.0: ~0 baseline tokens (users enable defer_loading in Claude config)

---

### 2. Dynamic Toolsets (Server-Side)

**Status:** Production-ready, client-agnostic
**Example:** [GitHub MCP server](https://github.com/github/github-mcp-server) with `--dynamic-toolsets` flag
**Implementation:** Server exposes meta-tools for discovery + enablement

```python
# Discovery tools (always loaded)
@mcp.tool()
async def list_available_toolsets() -> list[str]:
    """Return available toolset categories."""
    return ["repos", "issues", "pulls", "branches", "search"]

@mcp.tool()
async def enable_toolset(name: str) -> dict:
    """Enable a toolset, loading its tools into context."""
    # Dynamically register tools for this category
    register_tools_for_category(name)
    return {"enabled": name, "tool_count": len(tools)}

@mcp.tool()
async def get_toolset_tools(name: str) -> list[dict]:
    """List tools in a toolset without enabling it."""
    return [{"name": t.name, "description": t.description} for t in get_tools(name)]
```

**How It Works:**
- Tools grouped by domain (repos, issues, pulls, etc.)
- Agent discovers toolsets via `list_available_toolsets`
- Agent enables relevant toolsets on-demand via `enable_toolset`
- Only enabled toolset tools loaded into context

**Token Reduction:** 80-95% (depends on toolset usage patterns)

**Effort:** High (reorganize tool registration, implement discovery logic)

**Compatibility:** Universal (any MCP client)

**Tradeoffs:**
- ❌ Two-step workflow (discover → enable → use)
- ❌ Adds complexity (meta-tools for discovery)
- ✅ Client-agnostic (no platform dependencies)
- ✅ Clear mental model (explicit tool loading)

**Verified:** GitHub MCP has [dynamic toolsets feature](https://github.blog/changelog/2025-10-29-github-mcp-server-now-comes-with-server-instructions-better-tools-and-more/), enabled via `--dynamic-toolsets` flag or `GITHUB_DYNAMIC_TOOLSETS=1` env var. Tool count not publicly documented.

---

### 3. Progressive List Disclosure (Server-Side)

**Status:** Production-ready
**Example:** Speakeasy Gram, Cloudflare APIs, [XC-MCP](https://github.com/conorluddy/xc-mcp) (verified: simctl-list tool)
**Implementation:** Return summaries + cache IDs, retrieve full details on-demand

```python
@mcp.tool()
async def list_tests(product_id: int) -> dict:
    """List tests for a product (summary view)."""
    tests = await service.list_tests(product_id)

    # Store full results in cache
    cache_id = await cache.store_result_set(
        key=f"list_tests:{product_id}",
        data=tests,
        ttl_seconds=300  # 5 min
    )

    return {
        "summary": {
            "total": len(tests),
            "by_status": count_by_status(tests)
        },
        "quick_access": [
            {"id": t["id"], "title": t["title"], "status": t["status"]}
            for t in tests[:10]  # First 10 only
        ],
        "cache_id": cache_id  # ← Key for full retrieval
    }

@mcp.tool()
async def get_cached_results(cache_id: str, item_ids: list[int] | None = None) -> dict:
    """Retrieve full details from cached result set."""
    results = await cache.get_result_set(cache_id)
    if item_ids:
        results = [r for r in results if r["id"] in item_ids]
    return {"items": results}
```

**Agent Workflow:**
1. **Query:** `list_tests(product_id=25073)` → Returns 50 summaries (~600 tokens) + cache_id
2. **Scan:** Agent reviews summaries, identifies 2 tests of interest
3. **Details:** `get_cached_results(cache_id="abc123", item_ids=[12345, 67890])` → Returns 2 full objects (~1.2k tokens)

**Token Reduction:** 96% for large result sets (50 full objects: ~15k → ~1.8k total)

**Effort:** Medium (1-2 days: cache infrastructure + refactor list tools)

**Compatibility:** Universal (any MCP client)

**Tradeoffs:**
- ❌ Two-step workflow (list → retrieve details)
- ❌ Cache management complexity (TTL, eviction)
- ✅ Massive savings for large result sets
- ✅ Agent controls detail level
- ✅ Backwards compatible (small result sets return full objects)

**Verified:** XC-MCP README shows [progressive disclosure pattern](https://github.com/conorluddy/xc-mcp#token-optimization-architecture) with `simctl-list` returning summary + cacheId, `simctl-get-details` for full data (96% reduction: 57k → 2k tokens).

---

### 4. Semantic Tool Search (Server-Side)

**Status:** Production-ready (requires embeddings)
**Example:** Speakeasy Gram, ToolHive Optimizer
**Implementation:** Pre-generate embeddings, expose `find_tool` and `describe_tool`

```python
@mcp.tool()
async def find_tool(query: str, limit: int = 5) -> list[dict]:
    """Find tools using natural language query.

    Examples:
      - "show me test bugs" → Returns [get_test_bugs, list_bugs]
      - "product quality" → Returns [get_product_quality_report]
    """
    # Semantic search via embeddings
    tool_embeddings = await get_tool_embeddings()
    query_embedding = await embed(query)
    results = cosine_similarity_top_k(query_embedding, tool_embeddings, k=limit)

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "score": score
        }
        for tool, score in results
    ]

@mcp.tool()
async def describe_tool(tool_name: str) -> dict:
    """Get full schema for a specific tool."""
    tool = get_tool_by_name(tool_name)
    return {
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.input_schema,
        "output_schema": tool.output_schema
    }
```

**How It Works:**
- Pre-generate embeddings for all tool descriptions
- Agent uses `find_tool("natural language query")` to discover relevant tools
- Agent calls `describe_tool(name)` for full schema before using
- Tools not in context until explicitly described

**Token Reduction:** 99.7% baseline (400 tools: 405k → 1.3k tokens)

**Effort:** High (embeddings infrastructure, search implementation)

**Compatibility:** Universal (any MCP client)

**Tradeoffs:**
- ❌ Requires embeddings infrastructure (OpenAI API or local model)
- ❌ Three-step workflow (find → describe → execute)
- ✅ Flat scaling (works for 10 or 1000 tools)
- ✅ Natural language discovery
- ✅ Handles synonyms and fuzzy matching

**Not Verified:** No production examples found for testio-mcp scale. Referenced from [Speakeasy blog](https://www.speakeasy.com/blog/100x-token-reduction-dynamic-toolsets).

---

### 5. Skills Pattern (Client-Side, orthogonal to MCP)

**Status:** Production-ready (Anthropic), experimental (MCP wrapper)
**Example:** Anthropic Claude Skills, Open-ClaudeSkill MCP wrapper
**Implementation:** YAML frontmatter + markdown, loaded on-demand

**Skill File (`~/.claude/skills/testio-analyst/SKILL.md`):**
```markdown
---
name: testio-analyst
description: TestIO quality analysis workflows
provider: testio-mcp
tools: ["list_tests", "get_test_bugs", "generate_ebr_report"]
---

# TestIO Quality Analyst Skill

This skill provides workflows for analyzing test quality using TestIO data.

## Workflows

### Generate Quality Report
1. Call `list_tests(product_id)` to find active tests
2. For each test, call `get_test_bugs(test_id)` to fetch bugs
3. Aggregate bug metrics by severity
4. Call `generate_ebr_report(product_id)` for executive summary
```

**How It Works:**
- **Level 1 (always loaded):** Skill metadata in Claude sidebar (~100 tokens)
- **Level 2 (on-demand):** Full SKILL.md content loaded when user triggers skill (~5k tokens)
- **Level 3 (as needed):** MCP tools referenced in skill loaded

**Token Reduction:** High (single skill metadata + on-demand content)

**Effort:** Medium (write workflow documentation)

**Compatibility:** Native (Claude Desktop/Code only, NOT MCP standard)

**Tradeoffs:**
- ❌ Skills are "how to act", not "what to access" (different abstraction from MCP)
- ❌ Requires writing workflow documentation
- ✅ Perfect for domain-specific workflows
- ✅ Users can customize workflows locally

**Skills vs MCP:**
- **MCP:** "What can I access?" (data sources, APIs, external systems)
- **Skills:** "How should I act?" (workflows, domain expertise, organizational context)
- **Complementary:** Skills can use MCP tools; testio-mcp could have companion Skills

**Verified:** Anthropic feature documented at [Claude Skills](https://support.anthropic.com/en/articles/10442041-claude-skills-beta). Not a progressive disclosure mechanism - different abstraction layer.

---

### 6. Code Execution Pattern (Experimental)

**Status:** Conceptual (Anthropic proposal only, no official implementation)
**Example:** [Anthropic's "Code Execution with MCP" article](https://www.anthropic.com/engineering/code-execution-with-mcp)
**Implementation:** Generate filesystem structure representing API, agent explores via bash

**Generated Filesystem:**
```
/api/
  server.json       # Server metadata
  tools/
    list_tests/
      schema.json   # Input/output schema
      README.md     # Usage documentation
    get_test_bugs/
      schema.json
      README.md
```

**Agent Workflow:**
1. Agent executes `ls /api/tools` to discover available tools
2. Agent reads `/api/tools/list_tests/schema.json` for specific tool
3. Agent calls tool via special `execute_tool(name, params)` function
4. Results written to `/output/result.json` for agent to read

**How It Works:**
- MCP server generates filesystem structure representing its API
- Agent explores via bash commands (`ls`, `cat`, `grep`)
- Data filtering happens in execution environment (agent writes code)
- Only relevant data returned to model context

**Token Reduction:** **98.7% (verified: 150k → 2k tokens)** per [Anthropic article](https://www.anthropic.com/engineering/code-execution-with-mcp)

**Effort:** Very High (redesign MCP interaction model)

**Compatibility:** Unknown (requires client support for code execution)

**Tradeoffs:**
- ❌ No official implementation exists yet
- ❌ Requires paradigm shift (filesystem exploration vs direct tool calling)
- ❌ Complex for read-only tools (testio-mcp doesn't need execution environment)
- ✅ Ultimate token efficiency
- ✅ Agent filters data before returning to context

**Not Recommended for testio-mcp:** Our tools are read-only data access; code execution pattern designed for complex multi-step workflows with large intermediate results.

---

## Token Metrics Comparison

### Static Approach (Current State)

| Server | Tools | Baseline Tokens | Source |
|--------|-------|-----------------|--------|
| GitHub MCP | Unknown | ~50k+ (estimated) | [GitHub issue #275](https://github.com/github/github-mcp-server/issues/275) |
| testio-mcp | 14 | ~12.8k | Measured via Claude Code `/context` |
| XC-MCP v1.0 | 29 | 45k | [XC-MCP README](https://github.com/conorluddy/xc-mcp) |
| XC-MCP v2.0 | 28 | 18.7k | [XC-MCP README](https://github.com/conorluddy/xc-mcp) |

### Progressive Approaches

| Pattern | Baseline Tokens | On-Demand Tokens | Total (avg query) | Reduction | Source |
|---------|-----------------|------------------|-------------------|-----------|--------|
| `defer_loading` (client-side) | ~0 | ~800-1.1k per tool | ~2.4k-3.3k (3 tools) | **85%** | [Anthropic docs](https://www.anthropic.com/engineering/advanced-tool-use) |
| `--minimal` mode (server-side) | ~100-200 | ~500-700 per tool | ~1.6k-2.3k (3 tools) | **82-87%** | [XC-MCP --mini flag](https://github.com/conorluddy/xc-mcp) |
| Progressive lists (server-side) | ~100-200 | ~600 summary + ~1.2k details | ~1.9k-2k | **96%** | [XC-MCP simctl-list](https://github.com/conorluddy/xc-mcp) |
| Dynamic toolsets | ~500-1k | ~2-3k per toolset | ~2.5k-4k | 68-80% | [GitHub MCP](https://github.blog/changelog/2025-10-29-github-mcp-server-now-comes-with-server-instructions-better-tools-and-more/) |
| Code execution | ~2k | Data filtered in execution env | ~2k | **98.7%** | [Anthropic article](https://www.anthropic.com/engineering/code-execution-with-mcp) |

**Combined Impact (defer_loading + --minimal):**
- **User configures:** defer_loading in Claude Desktop config (~0 baseline)
- **We implement:** --minimal mode (~500-700 per tool on-demand)
- **Total:** ~1.5k-2.1k for typical 3-tool query (**84-88% reduction** from ~12.8k)

---

## Production Examples

### XC-MCP: Accessibility Workflow Server

**Repo:** [conorluddy/xc-mcp](https://github.com/conorluddy/xc-mcp)
**Stars:** 19
**Tools:** 29
**Domain:** Website accessibility analysis (3-4x cheaper than screenshots)

**Evolution (Verified from README):**
- **v1.0:** 45k tokens (29 tools with verbose descriptions)
- **v2.0:** 18.7k tokens (slimmed descriptions, moved examples to docs)
- **v3.0:** ~0 baseline tokens (users enable `defer_loading` in Claude config)

**Key Innovation:** `--mini` flag for ultra-slim descriptions (97% reduction to 540 tokens)

**Lesson Learned:** Platform support (`defer_loading`) eliminated need for manual optimization. v2.0 effort was wasted; could have jumped directly to v3.0 by documenting defer_loading for users.

**Quote from README:**
> "V3.0.0 adds platform-native `defer_loading` support — Claude's tool search automatically discovers tools on-demand, minimizing baseline context overhead while maintaining full 29-tool functionality."

---

### GitHub MCP: Dynamic Toolsets

**Repo:** [github/github-mcp-server](https://github.com/github/github-mcp-server)
**Stars:** 24,761
**Tools:** Unknown (not documented in README)
**Pattern:** Dynamic toolsets with `--dynamic-toolsets` flag

**Discovery Flow (from [GitHub Blog](https://github.blog/changelog/2025-10-29-github-mcp-server-now-comes-with-server-instructions-better-tools-and-more/)):**
1. Agent calls `list_available_toolsets()` → ["repos", "issues", "pulls", ...]
2. Agent calls `enable_toolset("issues")` → Loads issue-related tools
3. Agent uses `create_issue()`, `add_comment()`, etc.

**Configuration:**
- Binary: `--dynamic-toolsets` flag
- Docker: `GITHUB_DYNAMIC_TOOLSETS=1` env var

**Purpose:** Avoid model confusion from too many tools loaded simultaneously

**Lesson Learned:** Dynamic toolsets work well for large tool counts, but add complexity. Not appropriate for testio-mcp's 14 tools.

---

## Recommendations for testio-mcp

### ✅ Recommended: Continue Epic-008 Description Slimming

**What It Is:** Manually slim all tool Field descriptions as planned in STORY-056.

**Effort:** Already planned in Epic-008 (multiple stories)

**Impact:**
- ~46% reduction (12.8k → ~6.9k tokens) across all tools
- Benefits **ALL clients** (Claude Desktop, Code, Cursor, Zed, API, etc.)
- **We have full control** - no dependency on client features

**Why This First:**
- **Universal compatibility** - works everywhere
- **Already planned** - part of Epic-008 roadmap
- **Proven strategy** - XC-MCP did this before defer_loading (45k → 18.7k)
- **No risk** - we control the implementation

---

### ⏸️ Hold: Document `defer_loading` for Users

**What It Is:** Client-side configuration for progressive tool loading.

**Why Hold:**
- ✅ **Confirmed for Claude API** (requires beta header)
- ❓ **Unconfirmed for Claude Desktop** (XC-MCP shows config, but no official Anthropic docs)
- ❓ **Unconfirmed for Claude Code** (no mention in official docs)
- ❌ **Not supported** in Cursor, Zed, other MCP clients

**Decision:** **Wait for official Anthropic documentation** confirming Claude Desktop/Code support before publishing user-facing docs.

**When to Reconsider:**
- Anthropic publishes official Claude Desktop/Code `defer_loading` docs
- Community confirms it works reliably
- We can test it ourselves and verify behavior

**If we document anyway (risky):**
Add experimental warning: "⚠️ This feature is documented for Claude API but not officially confirmed for Claude Desktop. Use at your own risk."

---

### 🤔 Evaluate Later: `--minimal` Mode CLI Flag

**What It Is:** Server-side CLI flag that strips tool descriptions to 1-2 sentences.

**Effort:** 2-4 hours (add CLI flag + description helper)

**Impact:** 80-97% reduction when opted in (per XC-MCP --mini flag)

**Risk:** Low (opt-in, backwards compatible)

**Decision:** **Defer until after Epic-008 slimming**. May be redundant if manual slimming achieves similar results.

**When to Reconsider:**
- After Epic-008 completion, if users request more aggressive optimization
- If significant user base uses non-Claude clients (Cursor, Zed)
- If we want opt-in extreme minimalism (XC-MCP style: "See rtfm for details")

---

### ❌ Not Recommended (for now)

**Progressive List Disclosure:**
- Need usage data to justify two-step workflow complexity
- defer_loading may be sufficient for our 14-tool server
- Reconsider if result sets consistently >50 items

**Dynamic Toolsets:**
- Only 14 tools total, grouping overhead exceeds benefit
- Reconsider if tool count exceeds 30-40 tools

**Semantic Tool Search:**
- Embeddings infrastructure overkill for 14 tools
- Natural language discovery less critical at this scale
- Reconsider if tool count approaches 100+

**Code Execution:**
- No official implementation exists
- Our tools are read-only data access (don't need execution environment)
- Reconsider if MCP spec adds code execution support

---

## Integration with Epic-008

### STORY-056: Token Optimization

**Current Plan:** Manually slim all tool descriptions

**Status:** ✅ **Proceed as planned**

**Rationale:**
- Benefits **all clients** (Claude Desktop, Code, Cursor, Zed, API)
- No dependency on unconfirmed defer_loading support
- Proven strategy (XC-MCP: 45k → 18.7k before defer_loading)
- We have full control over implementation

**No changes needed** - Epic-008 plan remains valid.

---

### STORY-060: Consolidate Diagnostics

**Current Plan:** Merge `health_check`, `get_database_stats`, `get_sync_history` → `get_server_diagnostics`

**Status:** ✅ **Proceed as planned**

**Rationale:**
- Consolidation valuable regardless of defer_loading (simpler API)
- Reduces tool count (14 → 12 after consolidation)
- Benefits all users

**No changes needed** - Epic-008 plan remains valid.

---

### STORY-051: sync_data Tool (Epic-009)

**Current Plan:** Target ~550-600 tokens with structured Pydantic output

**Status:** ✅ **Proceed as planned**

**Rationale:**
- Keep structured schema (richness important for agent understanding)
- Token target achievable with manual slimming patterns from Epic-008
- No dependency on defer_loading

**No changes needed** - Epic-009 plan remains valid.

---

## Key Takeaways

### 1. defer_loading Client Support is Unclear

**Critical Discovery:** `defer_loading` is confirmed for **Claude API only**. Client support (Claude Desktop, Claude Code) is **not officially documented** by Anthropic.

**What We Know:**
- ✅ **Claude API:** Confirmed, requires beta header `"mcp-client-2025-11-20"`
- ❓ **Claude Desktop:** XC-MCP shows config example, but NOT in official Anthropic docs
- ❓ **Claude Code:** No mention in official docs
- ❌ **Other clients:** Cursor, Zed don't support it

**Our Decision:** Hold off on documenting defer_loading until official support is confirmed.

### 2. Cognitive Clarity > Token Cost

Progressive disclosure isn't just about saving tokens—it's about loading **only what Claude needs** for the task at hand. Even with 2M token windows, irrelevant context degrades performance.

### 3. Multiple Patterns, Choose Wisely

| Tool Count | Recommended Patterns |
|------------|---------------------|
| 1-20 | Manual description slimming (universal compatibility) |
| 20-50 | + Progressive lists for large result sets |
| 50-100 | + Dynamic toolsets or semantic search |
| 100+ | + Code execution pattern (when available) |

**testio-mcp (14 tools):** Continue with Epic-008 description slimming (46% reduction, all clients benefit).

### 4. Community Moved Fast

Progressive disclosure went from **experimental to standard practice** in 3 weeks (Nov 4-25, 2025). MCP ecosystem is evolving rapidly; expect spec formalization soon.

### 5. Skills vs MCP: Different Abstractions

- **MCP:** "What can I access?" (data sources, APIs)
- **Skills:** "How should I act?" (workflows, domain expertise)
- **Both valuable:** Consider companion testio-analyst Skill for workflows

---

## References

### Primary Sources (Verified)

1. **Anthropic: Code Execution with MCP** (Nov 4, 2025)
   https://www.anthropic.com/engineering/code-execution-with-mcp
   ✅ Verified: 98.7% reduction (150k → 2k), code execution proposal, progressive disclosure concept

2. **Anthropic: Advanced Tool Use** (Nov 20, 2025)
   https://www.anthropic.com/engineering/advanced-tool-use
   ✅ Verified: defer_loading feature, Tool Search Tool, 85% reduction, accuracy improvements

3. **Claude Docs: Tool Search Tool** (Nov 20, 2025)
   https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool
   ✅ Verified: defer_loading API configuration, client-side setup, beta header requirements

4. **XC-MCP: Accessibility Workflow Server** (Nov 7, 2025)
   https://github.com/conorluddy/xc-mcp
   ✅ Verified: 45k → 18.7k → ~0 evolution, defer_loading usage, --mini flag (97% reduction), progressive lists

5. **GitHub MCP: Dynamic Toolsets** (Nov 25, 2025)
   https://github.com/github/github-mcp-server
   ✅ Verified: dynamic toolsets feature, --dynamic-toolsets flag
   ⚠️ Tool count not verified (claimed 114, not documented in README)

### Community Discussions

6. **GitHub MCP: Dynamic Tool Selection Feedback**
   https://github.com/github/github-mcp-server/issues/275
   ✅ Verified: Community discussion on tool bloat, dynamic toolsets as solution

7. **GitHub Blog: MCP Server Updates** (Oct 29, 2025)
   https://github.blog/changelog/2025-10-29-github-mcp-server-now-comes-with-server-instructions-better-tools-and-more/
   ✅ Verified: Server instructions, tool improvements, dynamic toolsets

### Not Verified

- Speakeasy Gram (400 tools, semantic search benchmarks) - No direct access to verify
- ToolHive Optimizer - Mentioned in search results but details not independently verified
- Open-ClaudeSkill - GitHub repo exists but claims not independently verified

---

**Next Steps:**

1. ✅ **Continue Epic-008 as planned** (manual description slimming, consolidation)
2. ⏸️ **Hold defer_loading docs** until official Anthropic support confirmed
3. 🔍 **Monitor Anthropic releases** for Claude Desktop/Code defer_loading announcements
4. 📊 **Measure token savings** after Epic-008 completion
5. 🤔 **Evaluate --minimal mode** after seeing Epic-008 results and user feedback
