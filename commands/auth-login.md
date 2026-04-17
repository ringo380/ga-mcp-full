---
description: Run the Google Analytics OAuth browser flow and cache credentials for the ga-mcp-full MCP server.
allowed-tools: ["Bash"]
---

# /ga-mcp-full:auth-login

Authenticate the ga-mcp-full MCP server against your Google Analytics account.

## What this does

Runs `ga-mcp-full auth login`, which:

1. Resolves the OAuth client (env var override → `~/.config/ga-mcp/client_secrets.json` → bundled public Desktop client).
2. Opens your default browser to Google's consent screen with the `analytics.edit` scope.
3. Starts a local HTTP server on `127.0.0.1` bound to a random free port (no pre-registration needed — Google's installed-app OAuth accepts any loopback port).
4. Completes a PKCE-protected (S256) authorization code exchange.
5. Caches credentials at `~/.config/ga-mcp/credentials.json` (mode `0600`).

Subsequent Claude Code sessions reuse the cached refresh token automatically — you never need the client ID/secret at runtime after this step.

## Steps

1. Run the login command with `Bash`:

   ```bash
   ga-mcp-full auth login
   ```

2. Report the result to the user. If the command exits non-zero with `client_not_configured`, point them at `/ga-mcp-full:setup` so they can install the CLI or provide a custom OAuth client.

3. If the browser does not open automatically, the command prints the auth URL to stderr — surface that URL to the user so they can open it manually.

## Notes

- The MCP server does NOT need to be restarted after login — the next tool call will load the new credentials from disk.
- If a cached refresh token has been revoked, tool calls surface `"GA auth required: run /ga-mcp-full:auth-login ..."` — rerun this command to re-authenticate.
