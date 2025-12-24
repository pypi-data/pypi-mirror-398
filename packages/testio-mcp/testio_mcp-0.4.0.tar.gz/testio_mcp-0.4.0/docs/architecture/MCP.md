# MCP Server Architecture

**Version:** 2.0.0
**Last Updated:** 2025-12-03
**Purpose:** Implementation patterns for MCP tools, prompts, resources, and output schemas

**Audience:** Developers implementing or reviewing MCP artifacts

**Status:** Active

---

## Table of Contents

1. [Overview](#overview)
2. [Schema Architecture](#schema-architecture)
3. [Tool Parameter Guidelines](#tool-parameter-guidelines)
4. [Output Models](#output-models)
5. [Prompt Implementation Patterns](#prompt-implementation-patterns)
6. [Resource Implementation Patterns](#resource-implementation-patterns)
7. [REST API Integration](#rest-api-integration)
8. [References](#references)

---

## Overview

This codebase implements a Model Context Protocol (MCP) server using FastMCP, with Pydantic models for type safety and future REST API integration.

### Key Principles

1. **Nested Pydantic Models** - Use strongly-typed BaseModel classes for type safety
2. **Schema Inlining** - Post-process schemas to resolve `$ref` for MCP client compatibility
3. **Parameter-First Design** - LLMs parse parameter schemas more reliably than tool descriptions
4. **REST-Ready** - All models ready for FastAPI `response_model` integration

### Architecture Pattern

```python
# MCP Tool (returns dict, uses inlined schema)
@mcp.tool(output_schema=inline_schema_refs(MyOutputModel.model_json_schema()))
async def my_tool(...) -> dict[str, Any]:
    service = get_service(ctx, MyService)
    result = await service.my_method(...)
    validated = MyOutputModel(**result)  # Runtime validation
    return validated.model_dump(by_alias=True, exclude_none=True)

# Future REST Endpoint (returns Pydantic model)
@api.get("/api/my-resource", response_model=MyOutputModel)
async def my_endpoint(...) -> MyOutputModel:
    service = get_service(request.state, MyService)
    result = await service.my_method(...)
    return MyOutputModel(**result)  # FastAPI auto-serializes
```

---

## Schema Architecture

### Nested Models + Schema Inlining

**Problem:** Some MCP clients (Gemini CLI 0.16.0) fail to resolve JSON Schema `$ref` references.

**Solution:** Use nested Pydantic models in code, post-process schemas for MCP registration.

#### Benefits

| Aspect | Nested Models | Flattened (dict[str, Any]) |
|--------|---------------|----------------------------|
| **Type Safety** | ✅ Full (mypy checks) | ❌ None |
| **IDE Support** | ✅ Autocomplete, navigation | ❌ No hints |
| **FastAPI Docs** | ✅ Excellent (nested schemas) | ❌ Generic "object" |
| **Maintainability** | ✅ Clear domain structure | ❌ Unclear relationships |
| **MCP Compatibility** | ✅ (with inlining) | ✅ |

#### Implementation

**Step 1: Define nested models**

```python
from pydantic import BaseModel, Field

class StorageInfo(BaseModel):
    """Database storage metadata."""
    oldest_test_date: str | None = Field(default=None)
    newest_test_date: str | None = Field(default=None)

class DatabaseStatsOutput(BaseModel):
    """Database statistics and sync status."""
    database_size_mb: float
    storage_info: StorageInfo  # Nested model
```

**Step 2: Apply schema inlining in tool decorator**

```python
from testio_mcp.schema_utils import inline_schema_refs

@mcp.tool(output_schema=inline_schema_refs(DatabaseStatsOutput.model_json_schema()))
async def get_database_stats(...) -> dict[str, Any]:
    result = DatabaseStatsOutput(
        database_size_mb=25.5,
        storage_info=StorageInfo(
            oldest_test_date="2024-01-01",
            newest_test_date="2024-12-31",
        ),
    )
    return result.model_dump(by_alias=True, exclude_none=True)
```

**Step 3: Verify no `$ref` in output**

```python
# Original schema (has $ref)
original = DatabaseStatsOutput.model_json_schema()
# {"$defs": {"StorageInfo": {...}}, "properties": {"storage_info": {"$ref": "#/$defs/StorageInfo"}}}

# Inlined schema (no $ref)
inlined = inline_schema_refs(original)
# {"properties": {"storage_info": {"type": "object", "properties": {...}}}}
```

#### Schema Inlining Utility

**Location:** `src/testio_mcp/schema_utils.py`

```python
def inline_schema_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Recursively inline all $ref definitions from $defs.

    Resolves JSON schema $ref references by replacing them with
    their actual definitions. Works around bugs in MCP clients
    (Gemini CLI 0.16.0) that fail to resolve references.

    Features:
    - Recursively resolves nested $ref references
    - Preserves additional fields alongside $ref (e.g., description)
    - Does not mutate original schema
    - Handles refs in arrays, nested objects, and complex structures
    """
```

**Test Coverage:** 8 comprehensive test cases in `tests/unit/test_schema_utils.py`

---

## Tool Parameter Guidelines

### Core Principles

#### 1. Parameter Descriptions > Tool Descriptions

**Research Finding:**
> "The LLM uses function/tool names, descriptions, and parameter schemas to decide which tool to call based on the conversation and its instructions." - Google Agent Development Kit

**Implication:**
- LLMs parse **parameter schemas** more reliably than long tool descriptions
- Tool descriptions should be **concise** (100-200 chars, 1-3 sentences)
- Technical details belong in **parameter descriptions**, not tool descriptions

#### 2. Schema-First Design

**MCP Specification (2025-06-18):**
- Tool `description` is "like a hint to the model" - keep it brief
- `inputSchema` defines parameters using JSON Schema
- Enums use `enum` array with **values** (not names)

**FastMCP Auto-Generation:**
- Schemas generated from Python type hints + `Field()` metadata
- `Enum` classes → `$defs` section with descriptions (inlined for MCP)
- `Literal` types → inline `enum` arrays
- Validation constraints (`ge`, `le`) → JSON Schema constraints

#### 3. Validation Over Documentation

**Anti-Pattern:**
```python
# ❌ Documenting constraints in description only
page_size: int = Field(description="Number of items (1-1000)")
```

**Best Practice:**
```python
# ✅ Enforcing constraints in schema
page_size: int = Field(
    ge=1,
    le=1000,
    description="Number of items per page"
)
```

### Tool Description Guidelines

**Length Target:** 100-200 characters (1-3 sentences)

**Template:**
```python
"""[Action] [object] with [key capability]. [Optional: when to use]."""
```

**Examples:**

```python
# ✅ Good: Concise, focuses on what and when
"""Verify TestIO API authentication and connectivity. Returns product count as health indicator."""

# ✅ Good: Clear action, key capabilities
"""Get bug details with filtering by type, severity, and status. Supports pagination for tests with many bugs."""

# ❌ Too verbose: 4948 chars with Args/Returns/Raises
"""Get detailed bug information for a test with advanced filtering and pagination.

IMPORTANT: Bugs are classified by type (functional/visual/content/custom) based on
the API's severity field...

Args:
    test_id: Exploratory test ID (e.g., "109363")
    ... [87 more lines]
"""
```

### Parameter Description Guidelines

**Length Target:** 50-150 characters (1-2 sentences)

**Pattern:**
```python
parameter: Type = Field(
    description=(
        "[What it does]. "
        "[Optional: Performance/constraint note]. "
        "[Optional: Usage guidance]."
    ),
    json_schema_extra={"examples": ["value1", "value2"]},
)
```

**Examples:**

```python
# ✅ Good: Semantic meaning + performance hint
page_size: int = Field(
    ge=1,
    le=1000,
    description=(
        "Bugs per page. Use 100-500 for optimal performance. "
        "Values >500 may cause 2-5s latency for tests with 1000+ bugs."
    ),
)

# ✅ Good: Relationships + when to use
bug_type: BugType = Field(
    default=BugType.ALL,
    description=(
        "Bug classification filter. 'functional' bugs support severity filtering. "
        "'visual', 'content', 'custom' bugs ignore severity."
    ),
    json_schema_extra={"examples": ["functional", "custom"]},
)

# ✅ Good: Format guidance + discovery hint
product_id: int = Field(
    gt=0,
    description="Product identifier from TestIO (e.g., 25073). Use list_products to discover IDs.",
)
```

### Enum Usage Patterns

**Decision Tree:**
```
Is the enum used in multiple tools OR semantically meaningful?
├─ YES → Use Enum class
│   Examples: BugType, BugSeverity, TestStatus
│   Benefits: Reusability, semantic meaning, centralized docs
│
└─ NO → Use Literal
    Examples: Date formats, units, simple flags
    Benefits: Simpler, less code, single-use clarity
```

**Enum Class Pattern:**

```python
from enum import Enum

class TestStatus(str, Enum):
    """Test lifecycle status.

    - running: Test currently active, bugs being reported
    - locked: Test finalized, no new bugs accepted
    - archived: Test completed and archived
    """
    RUNNING = "running"
    LOCKED = "locked"
    ARCHIVED = "archived"

# Usage
statuses: list[TestStatus] | None = Field(
    default=None,
    description=(
        "Filter tests by lifecycle status. Omit to return all. "
        "Common: ['running'] for active, ['archived', 'locked'] for completed."
    ),
)
```

**Literal Pattern:**

```python
from typing import Literal

date_format: Literal["YYYY-MM-DD", "MM/DD/YYYY"] = Field(
    default="YYYY-MM-DD",
    description="Date format for output. ISO 8601 (YYYY-MM-DD) recommended.",
)
```

### Validation Constraints

**Numeric:**
```python
page_size: int = Field(ge=1, le=1000, description="Items per page")
product_id: int = Field(gt=0, description="Product identifier (positive)")
temperature: float = Field(ge=-273.15, le=100.0, description="Temperature (°C)")
```

**String:**
```python
test_id: str = Field(
    min_length=1,
    max_length=20,
    description="Test identifier from TestIO API"
)
```

### Performance Hints

**When to add:**
1. Parameter affects query latency (>500ms variance)
2. Parameter triggers expensive operations
3. Parameter has optimal value ranges

**Patterns:**

```python
# Latency warning
include_bug_counts: bool = Field(
    default=False,
    description=(
        "Include bug count summaries for each test. "
        "Adds 1-2s latency for products with 50+ tests."
    ),
)

# Optimal range
page_size: int = Field(
    ge=1, le=1000,
    description=(
        "Bugs per page. Use 100-500 for optimal performance. "
        "Values >500 may cause 2-5s latency."
    ),
)

# Client-side vs server-side
statuses: list[TestStatus] | None = Field(
    default=None,
    description=(
        "Filter tests by status. Applied client-side after API fetch. "
        "Doesn't reduce payload size, but reduces returned results."
    ),
)
```

---

## Output Models

All MCP tools use Pydantic models with **nested BaseModel classes** for type safety and FastAPI integration.

### Core Tool Output Models

#### 1. Test Status Tool

**Location:** `src/testio_mcp/tools/test_status_tool.py`

```python
class ProductInfo(BaseModel):
    """Product information embedded in test data."""
    id: int = Field(description="Product ID (integer from API)")
    name: str = Field(description="Product name")

class FeatureInfo(BaseModel):
    """Feature information embedded in test data."""
    id: int = Field(description="Feature ID (integer from API)")
    name: str = Field(description="Feature name")

class TestDetails(BaseModel):
    """Detailed information about an exploratory test."""
    id: int
    title: str
    goal: str | None = None
    testing_type: str
    status: str
    product: ProductInfo  # Nested model
    feature: FeatureInfo | None = None  # Nested model

class BugSummary(BaseModel):
    """Bug summary statistics for a test."""
    total_count: int = Field(ge=0)
    by_severity: dict[str, int]
    by_status: dict[str, int]
    recent_bugs: list[dict[str, Any]] = Field(max_length=3)

class TestStatusOutput(BaseModel):
    """Complete test status with configuration and bug summary."""
    test: TestDetails  # Nested model
    bugs: BugSummary   # Nested model
```

**MCP Tool:**
```python
@mcp.tool(output_schema=inline_schema_refs(TestStatusOutput.model_json_schema()))
async def get_test_status(test_id: int, ctx: Context) -> dict[str, Any]:
    service = get_service(ctx, TestService)
    result = await service.get_test_status(test_id)
    validated = TestStatusOutput(**result)
    return validated.model_dump(by_alias=True, exclude_none=True)
```

#### 2. List Tests Tool

**Location:** `src/testio_mcp/tools/list_tests_tool.py`

```python
class TestSummary(BaseModel):
    """Summary information for a single test."""
    test_id: int
    title: str
    status: str
    testing_type: str
    duration: int | None = None

class ProductInfoSummary(BaseModel):
    """Product information summary."""
    id: int
    name: str
    type: str

class ListTestsOutput(BaseModel):
    """Complete output for list_tests tool."""
    product: ProductInfoSummary  # Nested model
    statuses_filter: list[str]
    total_tests: int = Field(ge=0)
    tests: list[TestSummary]  # List of nested models
```

#### 3. List Products Tool

**Location:** `src/testio_mcp/tools/list_products_tool.py`

```python
class ProductSummary(BaseModel):
    """Summary information for a product."""
    product_id: int = Field(description="Product ID", alias="id")
    name: str
    type: str
    description: str | None = None

class ListProductsOutput(BaseModel):
    """Output model for list_products tool."""
    total_count: int = Field(ge=0)
    filters_applied: dict[str, str | list[str] | None]
    products: list[ProductSummary]  # List of nested models
```

### Database Monitoring Tool Output Models

#### 4. Database Stats Tool

**Location:** `src/testio_mcp/tools/cache_tools.py`

```python
class StorageInfo(BaseModel):
    """Database storage metadata."""
    oldest_test_date: str | None = Field(default=None)
    newest_test_date: str | None = Field(default=None)

class DatabaseStatsOutput(BaseModel):
    """Database statistics and sync status."""
    database_size_mb: float
    database_path: str
    total_tests: int = Field(ge=0)
    total_products: int = Field(ge=0)
    products_synced: list[dict[str, Any]]
    storage_info: StorageInfo  # Nested model
```

#### 5. Sync History Tool

**Location:** `src/testio_mcp/tools/cache_tools.py`

```python
class SyncSummary(BaseModel):
    """Aggregate statistics for sync events."""
    total_events: int = Field(ge=0)
    completed: int = Field(ge=0)
    failed: int = Field(ge=0)
    success_rate: float = Field(ge=0, le=100)
    avg_duration_seconds: float = Field(ge=0)

class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status for restart loop protection."""
    recent_failures_5min: int = Field(ge=0)
    is_active: bool
    message: str

class SyncHistoryOutput(BaseModel):
    """Sync event history with statistics."""
    events: list[dict[str, Any]]
    summary: SyncSummary  # Nested model
    circuit_breaker: CircuitBreakerStatus  # Nested model
```

#### 6. Problematic Tests Tool

**Location:** `src/testio_mcp/tools/cache_tools.py`

```python
class ProblematicTestsOutput(BaseModel):
    """Problematic tests (failed to sync) output."""
    count: int = Field(ge=0)
    tests: list[dict[str, Any]]
    message: str
```

---

## Prompt Implementation Patterns

MCP prompts are user-invoked workflow templates that expand into structured instructions for AI agents.

### Core Pattern

```python
from pathlib import Path
from testio_mcp.server import mcp

TEMPLATE_PATH = Path(__file__).parent / "my_workflow.md"

@mcp.prompt(name="my-workflow")
def my_workflow(
    required_param: str,
    optional_param: str = "default",
) -> str:
    """Brief description of what the workflow does.

    Args:
        required_param: Description of required parameter
        optional_param: Description with default behavior

    Returns:
        Formatted prompt template for AI agent execution.
    """
    template = TEMPLATE_PATH.read_text()
    return template.format(
        required_param=required_param,
        optional_param=optional_param,
    )
```

### Key Principles

1. **Template-driven** - Prompt logic lives in markdown files, not Python code
2. **Parameter injection** - Use `.format()` to inject values into template
3. **Kebab-case naming** - Prompts use `@mcp.prompt(name="verb-noun")` convention
4. **Auto-registration** - Import in `prompts/__init__.py` to register with server

### File Structure

```
src/testio_mcp/prompts/
├── __init__.py                    # Imports all prompts for registration
├── analyze_product_quality.py     # Python wrapper
├── analyze_product_quality.md     # Markdown template
├── prep_meeting.py
└── prep_meeting.md
```

### Template Design

Templates should include:
- **Phase structure** - Break workflow into numbered phases
- **Decision points** - When to pause for user input
- **Tool invocations** - Which MCP tools to call and when
- **Output format** - Expected deliverables

**Example template structure:**
```markdown
# {workflow_name} Workflow

## Phase 1: Discovery
<action>Call list_products to find {product_identifier}</action>
<checkpoint>Confirm product selection with user</checkpoint>

## Phase 2: Analysis
<action>Call get_product_quality_report with period={period}</action>

## Phase 3: Synthesis
<deliverable>Generate summary based on focus_area={focus_area}</deliverable>
```

### Registration

```python
# prompts/__init__.py
from testio_mcp.prompts import (
    analyze_product_quality,  # noqa: F401 - registers prompt
    prep_meeting,             # noqa: F401
)
```

```python
# server.py
from testio_mcp import prompts  # noqa: F401 - triggers registration
```

---

## Resource Implementation Patterns

MCP resources provide static knowledge bases accessible to AI clients via URI.

### Core Pattern

```python
from pathlib import Path
from fastmcp import FastMCP

def register_resources(mcp: FastMCP) -> None:
    """Register MCP resources."""

    @mcp.resource("testio://knowledge/my-resource")
    def get_my_resource() -> str:
        """Brief description of what this resource provides."""
        resource_path = Path(__file__).parent / "my_resource.md"
        return resource_path.read_text(encoding="utf-8")
```

### Key Principles

1. **URI scheme** - Use `{domain}://knowledge/{resource-name}` pattern
2. **Static content** - Resources serve markdown files, not dynamic data
3. **Read-only** - Resources are fetched, not modified
4. **Centralized registration** - All resources registered in `resources/__init__.py`

### File Structure

```
src/testio_mcp/resources/
├── __init__.py              # register_resources() function
├── playbook.md              # CSM heuristics and templates
└── programmatic_access.md   # REST API discovery guide
```

### URI Design

```
testio://knowledge/playbook             # Domain expertise
testio://knowledge/programmatic-access  # Technical guide
testio://schema/analytics               # Schema documentation (future)
```

### When to Use Resources vs Prompts

| Aspect | Resources | Prompts |
|--------|-----------|---------|
| **Content type** | Static knowledge | Dynamic workflow |
| **Invocation** | AI fetches when needed | User explicitly invokes |
| **Parameters** | None | User-provided values |
| **Use case** | Reference material | Multi-step operations |

### Registration

```python
# resources/__init__.py
def register_resources(mcp: FastMCP) -> None:
    @mcp.resource("testio://knowledge/playbook")
    def get_playbook() -> str:
        ...

    @mcp.resource("testio://knowledge/programmatic-access")
    def get_programmatic_access() -> str:
        ...
```

```python
# server.py
from testio_mcp.resources import register_resources
register_resources(mcp)
```

---

## REST API Integration

All Pydantic output models are ready for FastAPI `response_model` integration.

### FastAPI Pattern

```python
from fastapi import FastAPI, Request
from testio_mcp.tools.test_status_tool import TestStatusOutput

api = FastAPI()

@api.get("/api/tests/{test_id}", response_model=TestStatusOutput)
async def get_test_status_rest(test_id: int, request: Request) -> TestStatusOutput:
    """Get test status via REST API (same logic as MCP tool)."""
    service = get_service(request.state, TestService)
    result = await service.get_test_status(test_id)
    return TestStatusOutput(**result)  # FastAPI auto-serializes to JSON
```

### Swagger Auto-Generation

With nested Pydantic models, FastAPI automatically generates:

1. **OpenAPI Schema** (`/openapi.json`):
   - All endpoints documented
   - Request parameters with types and constraints
   - Response schemas with nested structures
   - Field descriptions from `Field(description=...)`

2. **Interactive Swagger UI** (`/docs`):
   - Try It Out functionality
   - See example requests/responses
   - Test endpoints in browser

3. **ReDoc Alternative** (`/redoc`):
   - Beautiful, clean API documentation
   - Searchable, navigable nested schemas

**Key Benefit:** Nested models generate **rich, hierarchical schemas** in Swagger docs. Flattened `dict[str, Any]` would show as generic "object" types with no structure.

### REST Endpoint Examples

```python
# List products
@api.get("/api/products", response_model=ListProductsOutput)
async def list_products_rest(
    search: str | None = None,
    product_type: list[ProductType] | None = None,
    request: Request,
) -> ListProductsOutput: ...

# List tests
@api.get("/api/tests", response_model=ListTestsOutput)
async def list_tests_rest(
    product_id: int,
    statuses: list[TestStatus] | None = None,
    request: Request,
) -> ListTestsOutput: ...

# Database stats
@api.get("/api/database/stats", response_model=DatabaseStatsOutput)
async def get_database_stats_rest(request: Request) -> DatabaseStatsOutput: ...

# Sync history
@api.get("/api/database/sync-history", response_model=SyncHistoryOutput)
async def get_sync_history_rest(
    limit: int = 10,
    request: Request,
) -> SyncHistoryOutput: ...
```

---

## References

### MCP Specification
- **Official Spec:** https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- Tool `description`: "Human-readable description... like a 'hint' to the model"
- `inputSchema`: JSON Schema object defining expected parameters

### FastMCP Documentation
- **Tools Guide:** https://gofastmcp.com/servers/tools
- "Clients send enum values (`\"red\"`), not names (`\"RED\"`)"
- "Use `Annotated` with descriptions to help LLMs understand parameter purposes"

### FastAPI Documentation
- **Response Models:** https://fastapi.tiangolo.com/tutorial/response-model/
- **OpenAPI Schema:** https://fastapi.tiangolo.com/tutorial/schema-extra-example/
- **FastMCP Integration:** https://gofastmcp.com/integrations/fastapi.md

### Internal Documentation
- **ADR-006:** Service Layer Pattern
- **ADR-007:** FastMCP Context Injection Pattern
- **ADR-011:** Extensibility Infrastructure Patterns
- **CLAUDE.md:** Tool implementation patterns and coding standards

### Implementation Stories
- **STORY-018:** Schema-driven tool optimization (parameter guidelines)
- **STORY-023f:** Hybrid MCP+REST API with Swagger (future work)

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-12-03 | 2.0 | Added Prompt and Resource implementation patterns (BMAD document-project) | Claude Code |
| 2025-11-18 | 1.0 | Consolidated TOOL_PARAMETER_GUIDELINES.md + OUTPUT_MODELS.md, added schema inlining | Claude Code |
| 2025-11-06 | 0.2 | Added output models documentation | Mary (Analyst) + Claude |
| 2025-11-06 | 0.1 | Initial tool parameter guidelines from STORY-018 | Mary (Analyst) + Claude |
