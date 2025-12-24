# ADR-012: MCP Resources Strategy - Defer to Post-MVP

**Status:** Accepted

**Date:** 2025-11-06

**Context:** MCP Resources implementation strategy and MVP scope

---

## Context

The Model Context Protocol (MCP) defines three core primitives for AI-LLM interaction:

| Primitive | Control | Purpose | Example |
|-----------|---------|---------|---------|
| **Tools** | Model-controlled | LLM automatically invokes when needed | `list_products()`, `get_test_status()` |
| **Resources** | Application-controlled | User/UI explicitly loads context | `product://123`, `file://path/to/doc` |
| **Prompts** | User-controlled | Explicit workflow templates | `/plan-vacation`, `/analyze-bugs` |

STORY-007 originally proposed implementing 3 MCP resources for TestIO MCP Server:
- `products://list` - Browse all available products
- `tests://active` - View currently active tests
- `bugs://recent?limit=50` - View recently submitted bugs

### Research Findings

Comprehensive research of MCP specification, FastMCP documentation, and real-world implementations revealed:

**1. Resources vs Tools - Philosophical Difference**

From [MCP Official Specification](https://modelcontextprotocol.io/specification/2025-03-26/server/resources):
> "Resources are designed to be **application-driven**, with host applications determining how to incorporate context based on their needs... applications could expose resources through UI elements for explicit selection, in a tree or list view."

From [Zuplo Blog](https://zuplo.com/blog/mcp-resources):
> "Choose Tools instead when you want the AI model to **automatically decide** when to access data or perform actions based on the conversation. If you want data to be **automatically available** to the model, use a Tool. If you want the **application or user to control** what context gets loaded, use a Resource."

**2. Real-World Usage Patterns**

From [Sean Goedecke's MCP Analysis](https://www.seangoedecke.com/model-context-protocol/):
> "None of the public MCP server codebases I read through expose prompts or resources, just tools. This might change if a popular MCP-compatible app appears that offers a good way to use prompts or resources."

**Key Insight:** Many production MCP servers implement ONLY tools, deferring resources until clear user demand emerges.

**3. Token Efficiency Considerations**

Research revealed token budgets differ by primitive type:

| Type | Typical Size | Max Size | Frequency | Rationale |
|------|-------------|----------|-----------|-----------|
| **Tool** | 500-2k tokens | 5k tokens | Many calls per conversation | Must be efficient |
| **Resource (catalog)** | 2k tokens | 10k tokens | Loaded once | Can be larger if paginated |
| **Resource (context)** | 5k-10k tokens | 50k tokens | Loaded once | Comprehensive by design |

**4. Use Cases Requiring Resources**

Resources add value when:
- ✅ UI has explicit "Load Context" buttons (e.g., "Load Product 25073 context")
- ✅ RAG scenarios (embed resource content for semantic search)
- ✅ File browser patterns (directory listings, documentation trees)
- ✅ User wants comprehensive context loaded once (vs. repeated tool calls)
- ❌ AI-driven queries (tools are better for this)

### Problem

**Current State:**
- TestIO MCP Server has well-designed tools that are model-controlled and token-efficient
- Tools provide excellent query capability: `list_products(search="studio")`, `get_test_status(109363)`
- No UI currently exists for resource selection (Claude Desktop, Cursor use tools primarily)

**Original STORY-007 Proposal:**
- Implement 3 resources alongside existing tools
- Resources would duplicate tool functionality (e.g., `products://list` vs `list_products()`)
- No clear differentiation between when to use tools vs resources
- Added complexity without clear MVP value

**Key Questions:**
1. Do resources provide value over existing tools for MVP use cases?
2. Should `list_products` tool be deprecated once resources exist?
3. How do users decide between `list_products(search="studio")` vs `products://list?limit=20`?

---

## Decision

**Defer MCP Resources implementation to post-MVP.**

**MVP Scope (STORY-007 Revised):**
- ✅ Implement PersistentCache (SQLite) with background sync (AC5) - Updated in v0.2.0
- ✅ Add cache monitoring tools (AC6)
- ✅ Integration testing for cache behavior (AC7)
- ❌ Remove resources implementation (AC1-AC4)

**Rationale:**

### 1. Tools Already Provide Excellent Query Capability

Current tools are perfectly aligned with MCP philosophy and user needs:

```python
# Model-controlled, token-efficient, query-specific
list_products(search="studio")  # Returns ~500 tokens (only matches)
get_test_status(test_id=109363)  # Returns ~2k tokens (specific test)
list_tests(product_id=25073, statuses=["running"])  # Filtered results
```

These tools:
- Are automatically invoked by AI when user asks questions
- Return filtered, targeted results (token-efficient)
- Support programmatic filtering (search, status, type)
- Cover all MVP query patterns identified in project brief

### 2. No UI for Resource Selection

Current MCP clients (Claude Desktop, Cursor) primarily use tools:
- No "Load Product Context" button exists
- No file browser UI for resource selection
- Resources would be awkward to invoke (must type URIs manually)

Resources shine when UI provides explicit selection mechanisms, which don't exist in MVP deployment.

### 3. Avoid Duplication and Confusion

Implementing both creates decision paralysis:

| Scenario | Tool Approach | Resource Approach | Which to use? |
|----------|--------------|-------------------|---------------|
| "Show me products with 'studio'" | `list_products(search="studio")` | `products://list` then filter? | ❓ Unclear |
| "Get test status" | `get_test_status(109363)` | `test://109363`? | ❓ Unclear |
| "Find active tests" | `list_tests(status="running")` | `tests://active`? | ❓ Unclear |

Without clear differentiation, users and AI will be confused about which primitive to use.

### 4. Follow Real-World Patterns

Many production MCP servers start with tools only, adding resources later based on user feedback:
- GitHub MCP server: Primarily tools
- Filesystem MCP server: Mix of tools + resources (file browsing use case is clear)
- Database MCP servers: Primarily tools

Resources are **optional** in MCP spec - defer until clear use case emerges.

### 5. YAGNI Principle

**You Aren't Gonna Need It** - Don't build speculative features:
- No user has requested resource-based context loading
- No evidence that tools are insufficient for MVP queries
- Can add resources post-MVP if user feedback indicates gaps

---

## Consequences

### Positive

1. **Simpler MVP Scope**
   - Reduces STORY-007 estimate from 5 hours to 3 hours
   - Focus on high-value caching infrastructure
   - Less code to maintain and test

2. **Clear Mental Model**
   - Tools are the only query mechanism (no confusion)
   - AI always knows to use tools for data access
   - Consistent interaction pattern for all queries

3. **Token Efficiency**
   - Tools remain optimized for repeated queries
   - No risk of accidentally loading large resource catalogs
   - Caching still provides performance benefits

4. **Easier Migration Path**
   - Can add resources later without breaking existing tools
   - User feedback will inform resource design (context loaders vs catalogs)
   - ADR documents rationale for future reference

5. **Alignment with Real-World Patterns**
   - Follows successful MCP server implementations
   - Validates MVP assumptions before committing to resources
   - Can observe tool usage patterns before designing resources

### Negative

1. **No "Load Context" Pattern**
   - Users cannot explicitly load comprehensive product/test context
   - AI must make multiple tool calls for related queries
   - No single "load everything about Product X" operation

2. **No Browsing UI**
   - Cannot present products/tests as selectable tree/list in UI
   - Must rely on search-based tool queries
   - No visual resource browser experience

3. **Potential Duplication Post-MVP**
   - If resources added later, might duplicate tool functionality
   - Need careful design to differentiate use cases
   - Risk of confusion between overlapping capabilities

### Neutral

1. **Deferred Decision**
   - Not a permanent "no" to resources, just "not now"
   - Can revisit based on user feedback and usage patterns
   - Maintains optionality for future architecture

---

## When to Reconsider (Migration Triggers)

Add MCP Resources when one or more of these conditions are met:

### 1. UI Integration with Resource Selection
- MCP client adds "Load Context" buttons
- File browser UI for product/test selection
- Tree view for hierarchical data browsing

**Example:** Claude Desktop adds sidebar with "Available Resources" that users can drag-and-drop into conversation.

### 2. RAG/Embedding Use Cases
- Need to embed comprehensive product documentation
- Semantic search across test history
- Vector database integration for context retrieval

**Example:** User wants to search "all bugs similar to this description" using embeddings.

### 3. "Load Everything" Request Pattern
- Users repeatedly ask for "tell me everything about Product X"
- AI makes 10+ tool calls to gather comprehensive context
- Performance suffers from repeated tool invocations

**Metric:** If >30% of conversations involve "comprehensive context" queries, resources make sense.

### 4. Multi-Turn Context Persistence
- Users want product context to persist across conversation
- Avoid re-querying same data in every follow-up question
- Context window optimization (load once, reference many times)

**Example:** "Now that you have Product 25073 context, analyze trends over 6 months..."

### 5. External User Feedback
- Users explicitly request "load context" capability
- Feature requests for resource-based workflows
- Pain points with current tool-only approach

**Trigger:** 3+ user requests for resource-like functionality.

---

## Future Resource Design Patterns

When resources ARE implemented, use one of these patterns:

### Pattern A: Context Loaders (MCP Purist)

Resources provide **comprehensive context** (large payloads okay):

```python
@mcp.resource("product://{product_id}")
async def load_product_context(product_id: int) -> dict:
    """Load COMPLETE product context for conversation.

    Returns: All metadata, tests, bugs, history (~10k tokens)
    Use when: User clicks "Load Product X" in UI
    """
    # Return EVERYTHING - size is okay for resources!
```

**Characteristics:**
- NO pagination (comprehensive by design)
- Loaded explicitly (user/UI selection)
- Large size acceptable (5k-50k tokens)
- Complements tools (different use case)

### Pattern B: Paginated Catalogs (FastMCP Pattern)

Resources provide **browsable listings** (paginated):

```python
@mcp.resource("products://list{?limit,offset}")
async def products_catalog(limit: int = 20, offset: int = 0) -> str:
    """Browse products (paginated).

    Default: 20 products (~2k tokens)
    Use when: User browses catalog in UI
    """
```

**Characteristics:**
- Paginated (default 20, max 100)
- Token-efficient defaults
- UI-friendly (searchable, filterable)
- Query parameters for control

**Important:** If implementing Pattern B, KEEP tools for AI-driven queries. Resources serve UI browsing, tools serve AI queries.

---

## Related Decisions

- **ADR-004:** Cache Strategy MVP - Caching remains valuable even without resources
- **ADR-006:** Service Layer Pattern - Services can support both tools and resources
- **ADR-011:** Extensibility Infrastructure - Easy to add resources later using same patterns
- **STORY-007:** (Revised) Now focuses solely on caching infrastructure

---

## References

### MCP Specification
- [MCP Resources Spec](https://modelcontextprotocol.io/specification/2025-03-26/server/resources)
- [MCP Server Concepts](https://modelcontextprotocol.io/docs/learn/server-concepts)

### FastMCP Documentation
- [FastMCP Resources & Templates](https://gofastmcp.com/servers/resources)
- [FastMCP Query Parameters](https://gofastmcp.com/servers/resources#query-parameters)

### Community Analysis
- [Sean Goedecke - MCP Explained Simply](https://www.seangoedecke.com/model-context-protocol/)
- [Zuplo - What are MCP Resources?](https://zuplo.com/blog/mcp-resources)
- [Daily Dose of DS - MCP Blueprint](https://www.dailydoseofds.com/model-context-protocol-crash-course-part-4/)

### Research
- [Sarah (PO) - STORY-007 Validation](../stories/story-007-resources-caching.md)
- Octocode MCP search results (2025-11-06)
- Brave Search: "model context protocol resources vs tools" (10 sources analyzed)

---

## Decision History

**2025-11-06:** Initial decision to defer resources to post-MVP
- **Context:** STORY-007 validation revealed unclear use case for resources in MVP
- **Research:** Comprehensive MCP spec review, FastMCP docs, real-world examples
- **Outcome:** Revised STORY-007 to focus on caching only (AC5-AC7)
- **Reviewers:** Sarah (PO), Ricardo Leon (Engineering)

---

## Open Questions

1. **Should we track tool usage metrics to inform future resource design?**
   - Current: No tracking of query patterns
   - Proposed: Log tool invocation frequency, query types, multi-tool patterns
   - Decision: Defer to STORY-008 (Error Handling & Monitoring)

2. **What threshold of "comprehensive context" queries justifies resources?**
   - Current: Undefined
   - Proposed: If >30% of conversations involve 5+ related tool calls
   - Decision: Monitor post-MVP, revisit in 30 days

3. **Should we create spike story to prototype resource UI patterns?**
   - Current: No resource UI exists
   - Proposed: Design mockups for "Load Context" buttons in Claude Desktop
   - Decision: Defer until user feedback indicates demand

---

## Appendix: Token Efficiency Analysis

### Comparison: Tool vs Resource Approaches

**Scenario:** User asks "Show me everything about Product 25073"

#### Tool Approach (Current):
```
1. get_product(25073)              → 500 tokens
2. list_tests(25073)               → 1,000 tokens
3. get_test_bugs(109363)           → 2,000 tokens
4. get_test_bugs(109364)           → 2,000 tokens
Total: 5,500 tokens across 4 tool calls
```

**Pros:** Incremental, AI decides what to fetch
**Cons:** Multiple API calls, AI reasoning overhead

#### Resource Approach (Hypothetical):
```
1. Load resource: product://25073  → 10,000 tokens
Total: 10,000 tokens in 1 resource load
```

**Pros:** Single operation, comprehensive context
**Cons:** May load unneeded data, no filtering

**Conclusion:** Tools more efficient for MVP query patterns (users rarely need "everything").
