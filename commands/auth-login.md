---
description: Run the Google Analytics OAuth browser flow and cache credentials for the ga-mcp-full MCP server.
allowed-tools: ["Bash"]
---

# /ga-mcp-full:auth-login

Authenticate the ga-mcp-full MCP server against your Google Analytics account.

## What this does

Runs `ga-mcp-full auth login`, which:

1. Resolves your OAuth client ID and secret (from `GA_MCP_CLIENT_ID` / `GA_MCP_CLIENT_SECRET` env vars or `~/.config/ga-mcp/client_secrets.json`).
2. Opens your default browser to Google's consent screen with the `analytics.edit` scope.
3. Starts a local server on `localhost:8085` to catch the OAuth callback.
4. Exchanges the authorization code for access + refresh tokens.
5. Caches credentials at `~/.config/ga-mcp/credentials.json` (mode `0600`).

After this runs once, subsequent Claude Code sessions use the cached refresh token automatically — you do not need the client ID/secret at runtime.

## Steps

1. Run the login command with `Bash`:

   ```bash
   ga-mcp-full auth login
   ```

2. Report the result to the user. If the command fails with a `ValueError` about missing OAuth credentials, point them at `/ga-mcp-full:setup` so they can configure their OAuth client first.

3. If the browser does not open automatically, the command prints a URL to stderr — surface that URL to the user so they can open it manually.

## Notes

- The MCP server does NOT need to be restarted after login — the next tool call will load the new credentials from disk.
- If port 8085 is already in use, the flow will fail. Tell the user to free the port and retry.
