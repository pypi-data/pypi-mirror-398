# MCP Client Setup

Connect AI clients to TestIO MCP Server.

**Prerequisites:**
1. **Configure server**: `uvx testio-mcp setup`
2. **Start server**: `uvx testio-mcp serve --transport http`
3. **Install npm** (for Claude Desktop): [Install via nvm](https://github.com/nvm-sh/nvm#installing-and-updating) or [direct download](https://nodejs.org/)

---

## HTTP Mode (Recommended)

Start server once, connect multiple clients:

```bash
uvx testio-mcp serve --transport http
```

### Claude Code (CLI)

```bash
claude mcp add --transport http testio-mcp http://127.0.0.1:8080/mcp
```

### Cursor

**Config:** `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project)

```json
{
  "mcpServers": {
    "testio-mcp": {
      "url": "http://127.0.0.1:8080/mcp"
    }
  }
}
```

Reload: `Cmd+Shift+P` → "Developer: Reload Window"

### Claude Desktop

**Config:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "testio-mcp": {
      "command": "npx",
      "args": ["mcp-remote", "http://127.0.0.1:8080/mcp"]
    }
  }
}
```

**Note:** Requires npm/Node.js. [Install via nvm](https://github.com/nvm-sh/nvm#installing-and-updating) if needed.

Restart: Fully quit (`Cmd+Q` / `Ctrl+Q`) and relaunch.

### Gemini Code (CLI)

```bash
gemini mcp add testio-mcp http://127.0.0.1:8080/mcp -t http
```

---

## stdio Mode (Single Client)

Each client spawns its own server process. **Not recommended** for multiple clients (causes database locks).

### Claude Code (CLI)

```bash
claude mcp add testio-mcp -- uvx testio-mcp
```

### Cursor

```json
{
  "mcpServers": {
    "testio-mcp": {
      "command": "uvx",
      "args": ["testio-mcp"]
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "testio-mcp": {
      "command": "uvx",
      "args": ["testio-mcp"]
    }
  }
}
```

### Gemini Code (CLI)

```bash
gemini mcp add testio-mcp uvx -- testio-mcp
```

---

## Verify Connection

Test with any of these queries:

```
What's the status of test 109363?
List all TestIO products
Check server diagnostics
```

Or via REST:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/api/products
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Connection refused" | Is server running? `curl http://127.0.0.1:8080/health` |
| "401 Unauthorized" | Reconfigure: `uvx testio-mcp setup` |
| Multiple clients conflict | Use HTTP mode, not stdio |
| Stale data | `uvx testio-mcp sync --force` |

**Logs:**
- Claude Desktop (macOS): `~/Library/Logs/Claude/mcp*.log`
- Server: Check terminal where `uvx testio-mcp serve` is running
