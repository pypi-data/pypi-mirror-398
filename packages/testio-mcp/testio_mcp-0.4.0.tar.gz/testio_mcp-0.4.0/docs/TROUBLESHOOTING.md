# Troubleshooting Guide

**Quick solutions for common TestIO MCP Server issues**

---

## Quick Diagnosis

**Server won't connect?**
1. Test server standalone: `uv run python -m testio_mcp`
2. Check absolute path in client config (no relative paths like `~/`)
3. Restart client completely (not just reload)
4. Check logs (see below)

**Getting 401 Unauthorized?**
1. Verify token: `cat .env | grep TESTIO_CUSTOMER_API_TOKEN`
2. Test token manually:
   ```bash
   curl -H "Authorization: Token YOUR_TOKEN" https://api.test.io/customer/v2/products
   ```
3. Regenerate token from TestIO dashboard if invalid

---

## Common Issues

### 1. Authentication Errors (401 Unauthorized)

**Symptom:** API returns "401 Unauthorized" or "Invalid token"

**Cause:** Invalid or expired `TESTIO_CUSTOMER_API_TOKEN`

**Solution:**

**Step 1:** Check token is set in `.env`

```bash
cat .env | grep TESTIO_CUSTOMER_API_TOKEN
```

**Step 2:** Test token manually

```bash
# Replace YOUR_TOKEN with actual token
curl -H "Authorization: Token YOUR_TOKEN" \
  https://api.test.io/customer/v2/products
```

**Expected:** JSON response with products list

**If you see 401:** Token is invalid

**Step 3:** Regenerate token

1. Go to https://testcloud.test.io/account/api
2. Generate new Customer API token
3. Update `.env` file with new token
4. Restart MCP server

---

### 2. Server Won't Start (Disconnected Status)

**Symptom:** Client shows "MCP server disconnected" or "Server not found"

**Cause:** Incorrect path, missing dependencies, or configuration errors

**Solution:**

**Step 1:** Test server runs standalone

```bash
cd /path/to/customer-mcp
uv run python -m testio_mcp
```

**Expected output:**
```
INFO:testio_mcp.server:FastMCP server initialized successfully
INFO:testio_mcp.server:Registered 9 tools
INFO:testio_mcp.server:TestIO MCP Server ready
```

**If it fails:** Fix the error before configuring clients

**Step 2:** Verify path in client config

Get absolute path:
```bash
cd /path/to/customer-mcp
echo "$(pwd)/.venv/bin/python"
```

Update client config with this **exact absolute path** (no `~/` or relative paths)

**Step 3:** Restart client completely

- **Claude Desktop:** Fully quit (Cmd+Q / Ctrl+Q), then relaunch
- **Cursor:** Reload window (Cmd+R / Ctrl+R)
- **Other clients:** Check [MCP_SETUP.md](../MCP_SETUP.md)

**Step 4:** Check client logs

See [Debug Logging](#debug-mode) section below for log locations

---

### 3. Slow Responses (> 5 seconds)

**Symptom:** Queries take longer than 5 seconds to return results

**Causes:**
- Cache expired (first query after restart)
- Large date ranges in activity queries
- Multiple products in timeframe queries

**Solution:**

**Check cache statistics:**

```
Show me cache statistics
```

**Expected metrics:**
- Hit rate: 70-90% (good)
- Hit rate: <50% (cache not effective)

**If cache hit rate is low:**

1. **Wait for cache warm-up:** First few queries are slower
2. **Reduce query scope:**
   - Use smaller date ranges (max 3 months)
   - Query fewer products at once (max 3-5)
3. **Check cache configuration:** See [.env.example](../.env.example) for TTL settings

**Clear cache to force refresh:**

```
Clear the cache
```

---

### 4. No Data Returned

**Symptom:** Queries return empty results or "No tests found"

**Causes:**
- No tests match filter criteria
- Product has no tests
- Date range has no activity
- Test ID doesn't exist

**Solution:**

**Step 1:** Verify data exists with resources

```
List all TestIO products
```

**Expected:** Returns list of products (should be 225 in staging)

**Step 2:** Check for active tests

```
Show me all tests for product 25073
```

**If empty:** Product has no tests, try different product ID

**Step 3:** Verify test IDs

```
What's the status of test 109363?
```

**If "Test not found":** Test ID doesn't exist or was deleted

**Step 4:** Broaden filters

- Remove severity filters: Use `bug_type="all"` instead of `severity="critical"`
- Remove status filters: Use `status="all"` instead of `status="running"`
- Expand date ranges: Use full quarter instead of single week

---

## Debug Mode

Enable detailed logging to diagnose issues:

### Enable DEBUG Logging

**Option 1: Environment variable (recommended)**

```bash
# macOS/Linux
export LOG_LEVEL=DEBUG
uv run python -m testio_mcp

# Windows
set LOG_LEVEL=DEBUG
uv run python -m testio_mcp
```

**Option 2: Update `.env` file**

```bash
echo "LOG_LEVEL=DEBUG" >> .env
```

### Log Locations

**Claude Desktop:**

- **macOS:** `~/Library/Logs/Claude/mcp-server-testio.log`
- **Windows:** `%APPDATA%\Claude\logs\mcp-server-testio.log`

**View logs:**

```bash
# macOS/Linux - watch live
tail -f ~/Library/Logs/Claude/mcp-server-testio.log

# macOS/Linux - last 50 lines
tail -n 50 ~/Library/Logs/Claude/mcp-server-testio.log

# Windows (PowerShell)
Get-Content "$env:APPDATA\Claude\logs\mcp-server-testio.log" -Tail 50
```

**Cursor, Codex, Gemini:**

Check client documentation for log locations (usually in client output panel)

### What to Look For in Logs

**Connection errors:**
```
ERROR: Failed to connect to https://api.test.io
```
→ Check network/firewall

**Authentication errors:**
```
ERROR: 401 Unauthorized
```
→ Check API token in `.env`

**Tool errors:**
```
ERROR: Tool 'get_test_status' failed with ToolError
```
→ Check parameters match tool schema

---

## Platform-Specific Issues

### macOS

**Issue:** "Permission denied" when running Python

**Solution:**
```bash
chmod +x /path/to/.venv/bin/python
```

**Issue:** Relative path `~/` doesn't work in Claude Desktop config

**Solution:** Use absolute path: `/Users/your-username/...` (not `~/...`)

### Windows

**Issue:** JSON syntax error with backslashes

**Solution:** Use double backslashes `\\` or forward slashes `/`:
```json
"command": "C:/path/to/.venv/Scripts/python.exe"
```
**NOT:**
```json
"command": "C:\path\to\.venv\Scripts\python.exe"  ❌
```

**Issue:** `npx` or `uv` not found

**Solution:** Install globally or use absolute path to executable

---

## FAQ

**Q: Do I need to restart the MCP server when I change `.env`?**

A: Yes. The server loads environment variables at startup. Restart the server for changes to take effect.

**Q: Can I use staging and production API tokens at the same time?**

A: No. Only one token can be active per server instance. To use both, configure two separate MCP servers with different names (e.g., `testio-staging`, `testio-prod`).

**Q: How do I update to a newer version of the MCP server?**

A:
```bash
cd /path/to/customer-mcp
git pull
uv pip install -e ".[dev]"
# Restart client
```

**Q: Why is the cache hit rate low?**

A: Cache resets on server restart. First queries after restart will always be slow (cache miss). Hit rate should improve to 70-90% after warm-up.

**Q: Can I increase cache TTL to improve performance?**

A: Yes. Add to `.env`:
```bash
CACHE_TTL_PRODUCTS=7200   # 2 hours (default: 3600)
CACHE_TTL_TESTS=600       # 10 minutes (default: 300)
CACHE_TTL_BUGS=120        # 2 minutes (default: 60)
```

**Q: How do I know which tools are available?**

A: Use the health_check tool:
```
Check TestIO API health
```

Or see [README.md Features](../README.md#features--api-reference) for full tool list.

---

## Still Stuck?

If issues persist after trying the solutions above:

1. ✅ Enable DEBUG logging (see above)
2. ✅ Check server runs standalone: `uv run python -m testio_mcp`
3. ✅ Verify all prerequisites: Python 3.12+, uv installed, API token valid
4. ✅ Review [MCP_SETUP.md](../MCP_SETUP.md) for client-specific setup
5. ✅ Check [CLAUDE.md](../CLAUDE.md) for development workflows

**Report Issues:**

If you encounter a bug or need support:
- Include log output (with DEBUG enabled)
- Include your configuration (redact API tokens!)
- Describe steps to reproduce the issue

---

**Version:** 1.0 | **Updated:** 2025-11-06
