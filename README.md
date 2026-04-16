# ga-mcp-full

GA4 MCP server exposing full Google Analytics 4 Admin API + Data API read/write access to MCP-compatible clients (Claude Code, Cursor, etc.) over stdio.

Thirty-plus tools cover property management, custom dimensions & metrics, audiences, key events, data streams, reporting (standard + realtime), Firebase/BigQuery/Google Ads link management, and measurement protocol secrets.

## Installation

### As a Python CLI

Requires Python 3.10+.

```bash
pip install -e .
# or, once published:
# pip install ga-mcp-full
```

This installs the `ga-mcp-full` executable. Verify with `ga-mcp-full --help`.

### As a Claude Code plugin

This repo ships a plugin manifest at `.claude-plugin/plugin.json` and an MCP server declaration at `.mcp.json`, so you can enable it in Claude Code without hand-editing any config.

1. Install the Python CLI first (`pip install -e .` — the plugin just wraps the CLI, it does not bundle Python).
2. Add this repo as a local plugin marketplace and install:
   ```
   /plugin marketplace add /absolute/path/to/ga-mcp-full
   /plugin install ga-mcp-full
   ```
3. On the next session start, the bundled `SessionStart` hook checks whether you are authenticated. If not, it prints a one-liner pointing you at `/ga-mcp-full:setup` or `/ga-mcp-full:auth-login`.

#### Bundled slash commands

| Command | What it does |
| --- | --- |
| `/ga-mcp-full:setup` | Guided first-run: create an OAuth client, install credentials, complete the browser login. |
| `/ga-mcp-full:auth-login` | Run the OAuth browser flow and cache tokens at `~/.config/ga-mcp/credentials.json`. |
| `/ga-mcp-full:auth-logout` | Remove cached OAuth credentials. |
| `/ga-mcp-full:auth-status` | Report current auth state and credential source. |

## Authentication

The server uses this resolution order (see `ga_mcp/auth.py`):

1. Cached OAuth tokens at `~/.config/ga-mcp/credentials.json` (refreshed automatically when expired).
2. Application Default Credentials (`gcloud auth application-default login`).
3. Fresh OAuth browser flow if `GA_MCP_CLIENT_ID` / `GA_MCP_CLIENT_SECRET` are set or `~/.config/ga-mcp/client_secrets.json` exists.

### First-time setup

1. In **Google Cloud Console → APIs & Services → Credentials**, create an **OAuth 2.0 Client ID** (Desktop app).
2. Ensure the **Google Analytics Admin API** and **Google Analytics Data API** are enabled for the project.
3. Either:
   - Download the client JSON and move it to `~/.config/ga-mcp/client_secrets.json` (mode `0600`), **or**
   - Set `GA_MCP_CLIENT_ID` and `GA_MCP_CLIENT_SECRET` in your shell profile.
4. Run `ga-mcp-full auth login` (or `/ga-mcp-full:auth-login` from Claude Code).
5. Approve the `analytics.edit` scope in the browser.

From that point on, the refresh token in `credentials.json` handles re-auth silently. You do not need the client ID/secret at runtime.

## Why not use the `/mcp` "Authenticate" button?

Claude Code's `/mcp` menu OAuth flow only applies to **HTTP-transport** MCP servers per the MCP 2025-06-18 authorization spec (stdio servers "SHOULD NOT" use it). `ga-mcp-full` is a stdio server, so auth is handled by the bundled slash commands and the `SessionStart` hook instead. An HTTP-mode transport that would participate in the `/mcp` OAuth flow is a possible future addition.

## Usage (standalone, without the plugin)

Add to your MCP client config (example for Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ga-mcp-full": {
      "command": "ga-mcp-full",
      "args": ["serve"]
    }
  }
}
```

## CLI

```
ga-mcp-full                 # Start the MCP server (stdio)
ga-mcp-full serve           # Same
ga-mcp-full auth login      # OAuth browser flow
ga-mcp-full auth logout     # Clear cached credentials
ga-mcp-full auth status     # Show current auth status
```

## Troubleshooting

- **`OAuth client credentials not found`** — Set `GA_MCP_CLIENT_ID` + `GA_MCP_CLIENT_SECRET` or place a `client_secrets.json` at `~/.config/ga-mcp/`.
- **Port 8085 in use during login** — The callback listener is hardcoded to `localhost:8085`. Free the port (`lsof -i :8085`) and retry.
- **Token refresh failed** — Run `ga-mcp-full auth logout` then `ga-mcp-full auth login`.

## License

MIT
