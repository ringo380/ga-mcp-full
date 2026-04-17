# ga-mcp-full

[![PyPI version](https://img.shields.io/pypi/v/ga-mcp-full.svg)](https://pypi.org/project/ga-mcp-full/)
[![Python versions](https://img.shields.io/pypi/pyversions/ga-mcp-full.svg)](https://pypi.org/project/ga-mcp-full/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Release to PyPI](https://github.com/ringo380/ga-mcp-full/actions/workflows/release.yml/badge.svg)](https://github.com/ringo380/ga-mcp-full/actions/workflows/release.yml)

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
- Google Analytics 4 property you have **Editor** or **Administrator** access to (the scope requested is `analytics.edit`)

That's it — no Google Cloud Console visit needed for the default install. A public Desktop OAuth client is bundled with the package.

## Authentication

The server resolves credentials in this order (see `ga_mcp/auth.py`):

1. **Cached OAuth tokens** at `~/.config/ga-mcp/credentials.json`. Refresh tokens renew expired access tokens silently.
2. **Application Default Credentials** — from `gcloud auth application-default login`.
3. **Fresh OAuth browser flow** — using `GA_MCP_CLIENT_ID` + `GA_MCP_CLIENT_SECRET` env vars, `~/.config/ga-mcp/client_secrets.json`, or the bundled public Desktop client (in that order).

### First-time setup (majority path)

1. Install: `pip install ga-mcp-full` (or `pip install -e .` for a dev checkout).
2. Run `/ga-mcp-full:auth-login` in Claude Code (or `ga-mcp-full auth login` at the shell).
3. Approve the `analytics.edit` scope when the browser opens.
4. The refresh token lands in `~/.config/ga-mcp/credentials.json` (mode `0600`).

The OAuth flow uses PKCE (S256) and binds the loopback redirect to a random free port on `127.0.0.1`, per Google's installed-app OAuth guidance. No prior Google Cloud Console client configuration is required.

#### You'll see an "unverified app" warning — this is expected for now

The bundled OAuth client is a real production app owned by this project, but Google's brand verification for sensitive scopes (like `analytics.edit`) takes several business days the first time. Until verification clears, the consent screen displays:

> Google hasn't verified this app
> The app is requesting access to sensitive info in your Google Account…

To proceed: click **Advanced** → **Go to ga-mcp-full (unsafe)**. The warning is Google's default posture for unverified apps — it doesn't indicate anything is actually wrong with the tool. Review the [privacy policy](./PRIVACY.md) if you want to know exactly what data is accessed (it's all local, per-user, per the scope you approved). The warning will disappear once Google's review completes.

Users who want to avoid the warning entirely can use their own OAuth client — see **Power users** below.

### Power users: use your own OAuth client

If you want quota isolation, a custom consent screen, or to avoid the verification-window warning:

1. Create an **OAuth 2.0 Client ID** of type **Desktop app** at **Google Cloud Console → APIs & Services → Credentials** in a project where the Google Analytics Admin API and Data API are enabled.
2. Override the bundled defaults via either:
   - Env vars in your shell profile: `GA_MCP_CLIENT_ID=...` and `GA_MCP_CLIENT_SECRET=...`
   - Or drop the downloaded JSON at `~/.config/ga-mcp/client_secrets.json` (mode `0600`).
3. Run `ga-mcp-full auth login` as usual — the env vars / legacy JSON take precedence over the bundled client.

### Already using `gcloud`?

If you have `gcloud auth application-default login --scopes=https://www.googleapis.com/auth/analytics.edit` configured, the server auto-detects ADC and skips OAuth entirely. No further setup needed.

### Why not the `/mcp` Authenticate button?

Claude Code's `/mcp` menu OAuth flow only applies to **HTTP-transport** MCP servers per the MCP 2025-06-18 authorization spec (stdio servers "SHOULD NOT" use it). `ga-mcp-full` is stdio, so auth is handled out-of-band via the bundled slash commands and the SessionStart hook. An HTTP transport mode that participates in the `/mcp` OAuth flow is a possible future addition.

## Bundled Claude Code components

### Slash commands

| Command | Purpose |
| --- | --- |
| `/ga-mcp-full:setup` | Guided first-run — install the CLI (if needed) and run the browser login |
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
| "Google hasn't verified this app" on the consent screen | Expected during brand verification. Click **Advanced** → **Go to ga-mcp-full**. Or set up your own OAuth client (see README "Power users") |
| `GA auth required: run /ga-mcp-full:auth-login in Claude Code, then retry.` | The cached refresh token is missing or revoked. Rerun the slash command — it's the entire fix |
| OAuth browser window shows "access_denied" during login | Your Google account doesn't have Editor/Admin on any GA4 property. Grant access in **GA4 → Admin → Account/Property Access Management** |
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

MIT — see [LICENSE](./LICENSE).
