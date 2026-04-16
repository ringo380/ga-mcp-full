# ga-mcp-full

A [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes the **full** Google Analytics 4 surface — both the Admin API (property & configuration management) and the Data API (reporting) — to MCP-compatible clients such as [Claude Code](https://claude.com/product/claude-code), [Claude Desktop](https://claude.ai/download), Cursor, Zed, and anything else that speaks stdio MCP.

Thirty-plus tools cover:

- **Property management** — create, list, update, delete, archive, retention settings
- **Custom dimensions & metrics** — create, list, update, archive
- **Audiences** — create, list, archive
- **Key events** — CRUD
- **Data streams** — CRUD
- **Linked accounts** — Firebase, BigQuery, Google Ads
- **Measurement Protocol secrets** — CRUD
- **Reporting** — standard reports, realtime reports, metadata discovery

## Install

The preferred install is via the **Robworks Claude Code Plugins** marketplace:

```bash
pip install ga-mcp-full  # once published to PyPI; for now use: pip install -e /path/to/ga-mcp-full
claude plugin marketplace add ringo380/robworks-claude-code-plugins
claude plugin install ga-mcp-full@robworks-claude-code-plugins
```

Why a two-step install: the plugin just wraps the Python CLI — it does not bundle the Python interpreter. You install the CLI once (`pip`), then the plugin registers the MCP server, slash commands, and SessionStart hook with Claude Code.

### Alternative: direct from the plugin repo

If you prefer to install the plugin directly from this repo without going through the Robworks marketplace:

```bash
pip install -e /path/to/ga-mcp-full
claude plugin marketplace add ringo380/ga-mcp-full   # uses the plugin repo as its own marketplace (once marketplace.json is added here)
claude plugin install ga-mcp-full
```

> Note: this repo currently only ships a `plugin.json`, not a `marketplace.json`. Use the Robworks marketplace above as the install path.

### Alternative: standalone MCP (no Claude Code plugin)

```bash
pip install -e /path/to/ga-mcp-full
```

Then add to your MCP client config. Example for Claude Desktop (`claude_desktop_config.json`):

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

For Cursor, Zed, or other clients, consult their MCP integration docs — the server command and arg pair is always `ga-mcp-full serve`.

## Requirements

- Python 3.10 or newer
- Google Cloud project with:
  - Google Analytics Admin API enabled
  - Google Analytics Data API enabled
- OAuth 2.0 Desktop client ID (Google Cloud Console → APIs & Services → Credentials)
- Google Analytics 4 property you have **Editor** or **Administrator** access to (the scope requested is `analytics.edit`)

## Authentication

The server resolves credentials in this order (see `ga_mcp/auth.py`):

1. **Cached OAuth tokens** at `~/.config/ga-mcp/credentials.json`. Refresh tokens renew expired access tokens silently.
2. **Application Default Credentials** — from `gcloud auth application-default login`.
3. **Fresh OAuth browser flow** — triggered if `GA_MCP_CLIENT_ID` + `GA_MCP_CLIENT_SECRET` env vars are set, or `~/.config/ga-mcp/client_secrets.json` exists.

### First-time setup

1. Open **Google Cloud Console → APIs & Services → Credentials** and create an **OAuth 2.0 Client ID** of type **Desktop app**.
2. Ensure **Google Analytics Admin API** and **Google Analytics Data API** are enabled on the project.
3. Either:
   - Download the client JSON and save it to `~/.config/ga-mcp/client_secrets.json` with mode `0600`, **or**
   - Export `GA_MCP_CLIENT_ID` and `GA_MCP_CLIENT_SECRET` in your shell profile (`~/.zshrc`, `~/.bashrc`, etc.)
4. Run `ga-mcp-full auth login` (or `/ga-mcp-full:auth-login` from Claude Code).
5. Approve the `analytics.edit` scope when the browser opens.
6. The refresh token lands in `~/.config/ga-mcp/credentials.json`. From here on, the client ID/secret are no longer required at runtime.

### Why not the `/mcp` Authenticate button?

Claude Code's `/mcp` menu OAuth flow only applies to **HTTP-transport** MCP servers per the MCP 2025-06-18 authorization spec (stdio servers "SHOULD NOT" use it). `ga-mcp-full` is stdio, so auth is handled out-of-band via the bundled slash commands and the SessionStart hook. An HTTP transport mode that participates in the `/mcp` OAuth flow is a possible future addition.

## Bundled Claude Code components

### Slash commands

| Command | Purpose |
| --- | --- |
| `/ga-mcp-full:setup` | Guided first-run — create an OAuth client, install credentials, complete the browser login |
| `/ga-mcp-full:auth-login` | Run the OAuth browser flow and cache tokens |
| `/ga-mcp-full:auth-logout` | Remove cached OAuth credentials |
| `/ga-mcp-full:auth-status` | Show current auth state and credential source |

### SessionStart hook

`hooks/scripts/ensure-auth.sh` runs at the start of every Claude Code session (`startup|resume|clear|compact`). It is non-blocking and only writes to stderr — if authentication is missing, it prints a one-line hint pointing at `/ga-mcp-full:setup`; it never exits non-zero and never blocks the session.

### MCP tools

After plugin install the server registers as `plugin:ga-mcp-full:ga-mcp-full` and tools surface as `mcp__ga-mcp-full__*`. Browse them with `/mcp` inside Claude Code.

## CLI reference

```bash
ga-mcp-full                 # Start the MCP server over stdio
ga-mcp-full serve           # Same as above (explicit)
ga-mcp-full auth login      # OAuth browser flow; caches refresh token
ga-mcp-full auth logout     # Clear cached credentials
ga-mcp-full auth status     # Show current auth state and credential source
ga-mcp-full --help          # Full help
```

## Development

```bash
git clone https://github.com/ringo380/ga-mcp-full.git
cd ga-mcp-full
python -m venv .venv && source .venv/bin/activate
pip install -e .
ga-mcp-full auth status
```

Project layout:

```
ga_mcp/
├── server.py          # MCP server entrypoint
├── cli.py             # CLI dispatcher
├── auth.py            # OAuth + credential resolution
└── tools/
    ├── admin/         # 11 modules — property, custom dimensions/metrics, audiences, etc.
    ├── reporting/     # 3 modules — core, realtime, metadata
    └── utils.py
```

Public Claude Code artifacts: `.claude-plugin/plugin.json`, `.mcp.json`, `commands/`, `hooks/`.

Issues and PRs welcome at https://github.com/ringo380/ga-mcp-full/issues.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `OAuth client credentials not found` | Set `GA_MCP_CLIENT_ID` + `GA_MCP_CLIENT_SECRET`, or drop `client_secrets.json` at `~/.config/ga-mcp/` (mode `0600`) |
| Port 8085 in use during login | Callback listener is hardcoded to `localhost:8085`. `lsof -i :8085` → `kill <pid>`, retry |
| Token refresh failed | `ga-mcp-full auth logout && ga-mcp-full auth login` |
| `/mcp` shows the server but no tools | Confirm `ga-mcp-full auth status` reports authenticated; tools are gated behind a working Analytics API client |
| Claude Code doesn't see the plugin | `claude plugin list` — confirm `ga-mcp-full@robworks-claude-code-plugins` is installed and enabled. Restart the session if you just enabled it |
| "insufficientPermissions" errors on Admin API writes | Verify your Google account has Editor/Admin role on the target GA4 property |

## Related

- [Robworks Claude Code Plugins marketplace](https://github.com/ringo380/robworks-claude-code-plugins) — catalogs this plugin alongside future plugins from `@ringo380`
- [Claude Code plugin docs](https://code.claude.com/docs/en/plugins)
- [MCP specification](https://modelcontextprotocol.io/)
- [Google Analytics Admin API](https://developers.google.com/analytics/devguides/config/admin/v1)
- [Google Analytics Data API](https://developers.google.com/analytics/devguides/reporting/data/v1)

## License

MIT — see [LICENSE](./LICENSE) (once added).
