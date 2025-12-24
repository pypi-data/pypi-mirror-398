# How to Compare MCP Tool and REST API Schemas

This guide explains how to systematically compare MCP tool schemas with REST API OpenAPI schemas to verify parity between the two interfaces.

## Overview

The testio-mcp server exposes both:
- **MCP Tools** - For AI assistants like Claude and Cursor
- **REST API** - For HTTP clients and web applications

Both interfaces should provide identical functionality. This guide helps verify that parity is maintained.

---

## Prerequisites

1. **Running Server** - The testio-mcp server must be running in HTTP mode:
   ```bash
   uv run python -m testio_mcp serve --transport http --port 8080
   ```

2. **MCP Inspector** - Install the MCP Inspector CLI tool:
   ```bash
   npm install -g @modelcontextprotocol/inspector
   ```

3. **Python Environment** - The scripts use Python for JSON processing:
   ```bash
   uv venv && source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

---

## Quick Start - Automated Comparison

Run the automated comparison script:

```bash
./scripts/compare_mcp_rest_schemas.py
```

This will:
1. Fetch the OpenAPI schema from the running server
2. Extract MCP tool schemas using Inspector CLI
3. Compare all tool/endpoint pairs
4. Generate a detailed report

**Expected output:**
```
================================================================================
MCP TOOL vs REST API SCHEMA COMPARISON
================================================================================

Comparing: get_product_summary ↔️  /api/products/{product_id}/summary
✅ Complete parity - no issues found!

Comparing: list_tests ↔️  /api/products/{product_id}/tests
✅ Complete parity - no issues found!

...

FINAL SUMMARY
Total comparisons: 11
✅ Perfect parity: 9
⚠️  Issues found: 2
```

---

## Manual Comparison Process

If you need to compare schemas manually or debug issues, follow these steps:

### Step 1: Extract MCP Tool Schemas

Use the MCP Inspector CLI to list all tools with their schemas:

```bash
npx @modelcontextprotocol/inspector \
  --cli "uv" --cli "run" --cli "python" --cli "-m" --cli "testio_mcp" \
  --method tools/list > mcp_tools_schema.json
```

**What this does:**
- Connects to the MCP server using stdio transport
- Calls the `tools/list` method to get all registered tools
- Saves the output to `mcp_tools_schema.json`

**Output format:**
```json
{
  "tools": [
    {
      "name": "get_product_summary",
      "description": "...",
      "inputSchema": {
        "type": "object",
        "properties": {
          "product_id": {
            "type": "integer",
            "exclusiveMinimum": 0
          }
        },
        "required": ["product_id"]
      },
      "outputSchema": {...}
    },
    ...
  ]
}
```

### Step 2: Extract OpenAPI Schema

Fetch the REST API schema from the running server:

```bash
curl -s http://127.0.0.1:8080/openapi.json > openapi_schema.json
```

**What this does:**
- Fetches the auto-generated OpenAPI 3.1 schema from FastAPI
- Saves to `openapi_schema.json`

**Output format:**
```json
{
  "openapi": "3.1.0",
  "info": {...},
  "paths": {
    "/api/products/{product_id}/summary": {
      "get": {
        "summary": "Get Product Summary Rest",
        "parameters": [...],
        "responses": {...}
      }
    },
    ...
  },
  "components": {
    "schemas": {...}
  }
}
```

### Step 3: Compare Schemas

Use the comparison script to analyze differences:

```bash
python scripts/compare_mcp_rest_schemas.py \
  --mcp-schema mcp_tools_schema.json \
  --openapi-schema openapi_schema.json
```

Or manually inspect using Python:

```python
import json

# Load schemas
with open('mcp_tools_schema.json') as f:
    mcp_tools = {tool['name']: tool for tool in json.load(f)['tools']}

with open('openapi_schema.json') as f:
    openapi = json.load(f)

# Compare a specific endpoint
tool_name = 'list_products'
endpoint_path = '/api/products'

mcp_tool = mcp_tools[tool_name]
rest_endpoint = openapi['paths'][endpoint_path]['get']

# Compare parameters
mcp_params = set(mcp_tool['inputSchema']['properties'].keys())
rest_params = {p['name'] for p in rest_endpoint['parameters']}

print(f"MCP parameters: {mcp_params}")
print(f"REST parameters: {rest_params}")
print(f"Missing in REST: {mcp_params - rest_params}")
print(f"Missing in MCP: {rest_params - mcp_params}")
```

---

## What to Compare

### 1. Input Parameters

**Check:**
- Parameter names match
- Parameter types match (integer, string, boolean, etc.)
- Required vs optional matches
- Default values match
- Validation constraints match (min, max, patterns)

**Example Mismatch:**
```
MCP: offset (integer, default: 0, optional)
REST: [MISSING]
```

### 2. Output Schemas

**Check:**
- Response model names match
- Both use the same Pydantic model
- Field names and types match

**Example Match:**
```
MCP output: ProductSummaryOutput
REST output: ProductSummaryOutput (reference: #/components/schemas/ProductSummaryOutput)
✅ Both use same model
```

### 3. Descriptions

**Check:**
- Tool descriptions are clear and consistent
- Parameter descriptions explain purpose
- Not critical for parity, but important for UX

---

## Common Issues and Solutions

### Issue 1: Tool Not Appearing in MCP List

**Symptom:** Tool exists in code but not in `tools/list` output

**Possible Causes:**
1. Tool is disabled via `DISABLED_TOOLS` environment variable
2. Tool registration failed (check server logs)
3. Tool module not imported (check `@mcp.tool()` decorator)

**Solution:**
```bash
# Check disabled tools
echo $DISABLED_TOOLS

# Enable all tools temporarily
DISABLED_TOOLS="" uv run python -m testio_mcp serve --transport http --port 8080

# Check server logs for registration errors
tail -f ~/.testio-mcp/logs/server.log | grep -i "tool"
```

### Issue 2: Parameter Type Mismatch

**Symptom:** Parameter types differ between MCP and REST

**Example:**
```
MCP: page (integer)
REST: page (string)
```

**Solution:**
- Check FastAPI `Query()` parameter definition
- Ensure Pydantic validation matches MCP tool
- Look for type coercion issues

### Issue 3: Missing REST Endpoint Parameter

**Symptom:** MCP tool accepts parameter but REST endpoint doesn't

**Root Cause:** Parameter not added to FastAPI route handler

**Solution:**
1. Add parameter to REST endpoint function signature:
   ```python
   @api.get("/api/products")
   async def list_products_rest(
       ...,
       offset: int = Query(0, description="Starting offset", ge=0),
   ):
   ```

2. Pass parameter to service layer:
   ```python
   result = await service.list_products(
       ...,
       offset=offset,
   )
   ```

3. Update docstring

4. Restart server and verify

---

## Tool-to-Endpoint Mapping

| MCP Tool | REST Endpoint | HTTP Method |
|----------|---------------|-------------|
| `get_product_summary` | `/api/products/{product_id}/summary` | GET |
| `get_feature_summary` | `/api/features/{feature_id}/summary` | GET |
| `get_user_summary` | `/api/users/{user_id}/summary` | GET |
| `get_test_summary` | `/api/tests/{test_id}/summary` | GET |
| `list_products` | `/api/products` | GET |
| `list_features` | `/api/products/{product_id}/features` | GET |
| `list_tests` | `/api/products/{product_id}/tests` | GET |
| `query_metrics` | `/api/analytics/query` | POST |
| `get_analytics_capabilities` | `/api/analytics/capabilities` | GET |
| `get_server_diagnostics` | `/api/diagnostics` | GET |
| `get_problematic_tests` | `/api/sync/problematic` | GET |

---

## Comparison Script Reference

The automated comparison script (`scripts/compare_mcp_rest_schemas.py`) performs these checks:

1. **Parameter Comparison:**
   - Extracts MCP `inputSchema.properties`
   - Extracts REST `parameters` array
   - Compares parameter names, types, and required status
   - Reports missing or mismatched parameters

2. **Output Schema Comparison:**
   - Extracts MCP `outputSchema.title`
   - Extracts REST response `$ref` schema name
   - Verifies both use the same Pydantic model

3. **HTTP Method Detection:**
   - Checks for `get` vs `post` in OpenAPI paths
   - For POST, compares request body schema instead of query params

4. **Error Reporting:**
   - ✅ Green checkmarks for matches
   - ❌ Red X for missing parameters
   - ⚠️  Warning for type mismatches
   - Final summary with pass/fail count

---

## Testing After Changes

After fixing schema issues, verify with these steps:

### 1. Restart Server

```bash
# Kill existing server
pkill -f "testio_mcp"

# Start fresh
uv run python -m testio_mcp serve --transport http --port 8080
```

### 2. Re-run Comparison

```bash
./scripts/compare_mcp_rest_schemas.py
```

### 3. Test Specific Endpoint

```bash
# Test MCP tool (if you have MCP client connected)
# Example: via Claude Code

# Test REST endpoint
curl -s "http://127.0.0.1:8080/api/products?offset=5&per_page=2" | python -m json.tool
```

### 4. Verify OpenAPI Schema

```bash
# Check parameter appears in schema
curl -s http://127.0.0.1:8080/openapi.json | \
  python -c "import json, sys; schema = json.load(sys.stdin); print(json.dumps(schema['paths']['/api/products']['get']['parameters'], indent=2))"
```

---

## CI/CD Integration

To prevent schema drift in the future, add the comparison script to CI:

```yaml
# .github/workflows/schema-parity.yml
name: Schema Parity Check

on: [pull_request]

jobs:
  compare-schemas:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[dev]"
          npm install -g @modelcontextprotocol/inspector

      - name: Start server
        run: |
          uv run python -m testio_mcp serve --transport http --port 8080 &
          sleep 5
        env:
          TESTIO_CUSTOMER_API_TOKEN: ${{ secrets.TESTIO_API_TOKEN }}

      - name: Compare schemas
        run: ./scripts/compare_mcp_rest_schemas.py

      - name: Upload comparison report
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: schema-comparison-report
          path: schema_comparison_report.txt
```

---

## References

- **MCP Inspector Docs:** https://github.com/modelcontextprotocol/inspector
- **FastAPI OpenAPI:** https://fastapi.tiangolo.com/how-to/extending-openapi/
- **Pydantic Schemas:** https://docs.pydantic.dev/latest/concepts/json_schema/
- **Story 061:** REST API Parity implementation details

---

**Last Updated:** 2025-11-29
**Maintained By:** TestIO MCP Team
