# TestIO MCP Server

Query TestIO test data through AI tools - no UI required.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.12+-green.svg)](https://github.com/jlowin/fastmcp)

---

## Quick Start

**Get started in 3 steps:**

### 1. Setup (One-time configuration)
```bash
uvx testio-mcp setup
```
Creates `~/.testio-mcp.env` with your API credentials and preferences.

Reference docs are copied to `~/.testio-mcp/` including `.env.example` for all available options.

### 2. Sync Data
```bash
uvx testio-mcp sync
```
Loads your products, features, and tests into local cache (~30s-2min).

### 3. Start Server
```bash
uvx testio-mcp serve --transport http
```
Runs at http://127.0.0.1:8080 (keep terminal open).

**Next:** Configure your AI client → [MCP_SETUP.md](MCP_SETUP.md)

**Optional:** Open http://127.0.0.1:8080/docs for interactive API explorer.

---

## Access Methods

| Method | Endpoint | Best For |
|--------|----------|----------|
| **MCP** | `http://127.0.0.1:8080/mcp` | Claude, Cursor, AI assistants |
| **REST** | `http://127.0.0.1:8080/api/*` | Scripts, dashboards, integrations |
| **Swagger** | `http://127.0.0.1:8080/docs` | API exploration, testing |

### Example: Same Query, Two Ways

```bash
# Via AI (MCP)
"What's the status of test 109363?"

# Via REST
curl http://127.0.0.1:8080/api/tests/109363/summary
```

---

## Tools (17)

### Data Discovery
| Tool | Example Query |
|------|---------------|
| `list_products` | "Show all mobile apps" |
| `list_tests` | "List running tests for product 598" |
| `list_features` | "What features does product 598 have?" |
| `list_users` | "Who are our testers?" |
| `list_bugs` | "Show critical bugs for test 109363" |

### Entity Summaries
| Tool | Example Query |
|------|---------------|
| `get_test_summary` | "Status of test 109363" |
| `get_product_summary` | "Overview of product 598" |
| `get_feature_summary` | "Details on feature 1234" |
| `get_user_summary` | "Show tester 5678's activity" |
| `get_bug_summary` | "Details on bug 91011" |

### Analytics & Reports
| Tool | Example Query |
|------|---------------|
| `generate_quality_report` | "Quality report for products 598, 599" |
| `query_metrics` | "Bug counts by severity for product 598" |
| `get_analytics_capabilities` | "What metrics can I query?" |

See [ANALYTICS.md](docs/ANALYTICS.md) for the full analytics guide with query patterns and examples.

### Search & Sync
| Tool | Example Query |
|------|---------------|
| `search` | "Find bugs mentioning login" |
| `sync_data` | "Refresh data for product 598" |

### Diagnostics
| Tool | Example Query |
|------|---------------|
| `get_server_diagnostics` | "Check server health" |
| `get_problematic_tests` | "Which tests failed to sync?" |

---

## Prompts (2)

Interactive workflows for common tasks:

| Prompt | Use Case |
|--------|----------|
| `analyze-product-quality` | Deep-dive quality analysis with artifacts |
| `prep-meeting` | Generate meeting materials from analysis |

---

## Resources (2)

Knowledge bases accessible via `testio://` URIs:

| Resource | Content |
|----------|---------|
| `testio://knowledge/playbook` | CSM heuristics and templates |
| `testio://knowledge/programmatic-access` | REST API discovery guide |

---

## CLI Reference

```bash
# Configuration
uvx testio-mcp setup              # Interactive setup
uvx testio-mcp --version          # Show version

# Server
uvx testio-mcp serve --transport http              # HTTP mode (multi-client)
uvx testio-mcp serve --transport http --port 9000  # Custom port
uvx testio-mcp                                     # stdio mode (single client)

# Sync
uvx testio-mcp sync --status      # Check sync status
uvx testio-mcp sync               # Manual sync
uvx testio-mcp sync --force       # Full refresh
```

---

## Data Flow

```
┌─────────────────────────────────────────┐
│  AI Client (Claude, Cursor)             │
│  or REST Client (curl, scripts)         │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  TestIO MCP Server                      │
│  localhost:8080                         │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Local SQLite Cache                     │
│  ~/.testio-mcp/cache.db                 │
│  (queries: ~10ms, auto-sync: 1h)        │
└─────────────┬───────────────────────────┘
              ↓ (read-through cache + sync)
┌─────────────────────────────────────────┐
│  TestIO Customer API                    │
│  https://api.test.io/customer/v2        │
└─────────────────────────────────────────┘
```

**Caching:** Background sync refreshes products, features, and discovers new tests every hour. Bug and test metadata use read-through caching—refreshed on-demand when queried if stale (>1 hour). Immutable tests (`archived`/`cancelled`) always serve from cache. See [CLAUDE.md](CLAUDE.md) for details on test mutability and caching logic.

---

## Configuration

Created by `uvx testio-mcp setup` at `~/.testio-mcp.env`:

| Variable | Description |
|----------|-------------|
| `TESTIO_CUSTOMER_API_TOKEN` | Your API token |
| `TESTIO_CUSTOMER_NAME` | Your subdomain |
| `TESTIO_CUSTOMER_ID` | Customer ID (default: 1) |
| `TESTIO_PRODUCT_IDS` | Filter to specific products |
| `TESTIO_HTTP_PORT` | Server port (default: 8080) |

Full options: see `.env.example` (repo root or `~/.testio-mcp/.env.example` for uvx users).

---

## Client Setup

See [MCP_SETUP.md](MCP_SETUP.md) for connecting:
- Claude Desktop
- Claude Code (CLI)
- Cursor
- Gemini Code

---

## Troubleshooting

```bash
# Server won't start?
curl http://127.0.0.1:8080/health

# Data seems stale?
uvx testio-mcp sync --status
uvx testio-mcp sync --force

# Token issues?
uvx testio-mcp setup  # Reconfigure
```

---

## Documentation

- [MCP_SETUP.md](MCP_SETUP.md) - Client configuration
- [ANALYTICS.md](docs/ANALYTICS.md) - Analytics engine guide
- [CLAUDE.md](CLAUDE.md) - Development guide
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [docs/architecture/](docs/architecture/) - Technical architecture

---

## License

Proprietary - See [LICENSE](LICENSE) for terms.
