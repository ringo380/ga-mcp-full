---
description: Diagnose the ga-mcp-full MCP connection and walk through reconnect options when tools stop responding.
allowed-tools: ["Bash"]
---

# /ga-mcp-full:reconnect

Diagnose the ga-mcp-full MCP server and surface the exact reconnect path for the current failure mode. Use this when GA tool calls stop responding, return auth errors, or the `/plugin` detail view shows a red error line for `ga-mcp-full`.

## Why this command exists

Claude Code's `/plugin` and `/mcp` menus do not expose a plugin-extensible "reconnect" button for stdio MCP servers — that affordance is HTTP-transport-only per the MCP 2025-06-18 spec. So reconnects for this stdio server happen through one of three paths, and the right path depends on *which* failure you hit. This command runs the diagnostics needed to pick the right one.

## Steps

1. **Check CLI installation** — if this fails, no other reconnect path will help:

   ```bash
   command -v ga-mcp-full && ga-mcp-full --version
   ```

   If missing, point the user at `/ga-mcp-full:setup`.

2. **Check auth state**:

   ```bash
   ga-mcp-full auth status
   ```

   Relay the output verbatim.

3. **Check `.mcp.json` sanity** — stale `env` substitution entries are the most common load-time failure:

   ```bash
   cat .mcp.json 2>/dev/null || echo "(no project-scoped .mcp.json in cwd)"
   ```

   Flag any `${GA_MCP_CLIENT_*}` entries in the `env` block — those make Claude Code refuse to start the subprocess even though the bundled client would work without them.

4. **Pick the reconnect path based on findings**, and tell the user exactly what to do:

   | Symptom | Reconnect path |
   |---|---|
   | `auth status` reports `Authenticated: no` or `Token expired: true` | Run `/ga-mcp-full:auth-login`. No process restart needed — `auth.py` reloads credentials from disk on the next tool call. |
   | `auth status` reports stale account / `email: <unknown …>` | Run `/ga-mcp-full:auth-login` to upgrade the cached token to the v0.4.0 scope set (adds openid/email). |
   | `/plugin` detail view shows "Missing environment variables: GA_MCP_CLIENT_ID…" | `.mcp.json` declares required env vars it shouldn't. Fix by removing the `env` block (bundled client is the default). Then **restart Claude Code** — plugin config is only re-read on session start. |
   | MCP subprocess crashed mid-session / `claude mcp list` shows it as `✗ Failed to connect` | Open the `/mcp` dialog; stdio servers are restarted by toggling the server off and on there. If that fails, restart Claude Code. |
   | Everything looks healthy but tool calls still 401 | Run `/ga-mcp-full:auth-logout` then `/ga-mcp-full:auth-login` — clears the cached refresh token and forces a fresh consent. |

5. **Do not attempt to restart the stdio subprocess yourself** — there is no CLI or API for a plugin to force-restart its own MCP server from inside a Claude Code session. The restart paths above (in-session `/mcp` toggle, or Claude Code restart) are the only sanctioned options.

## Notes

- Most "reconnect" needs after a fresh `ga-mcp-full auth login` are actually zero-restart: `get_credentials()` re-reads `~/.config/ga-mcp/credentials.json` on each tool invocation, so the next call picks up new auth automatically.
- If the user is on a version older than v0.4.0, cached tokens lack the openid/email scopes and `whoami` will return `email: None`. This is a soft degradation, not a failure — no reconnect needed unless they want the email lookup working.
