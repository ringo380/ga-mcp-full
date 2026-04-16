---
description: Show the current Google Analytics auth status for the ga-mcp-full MCP server.
allowed-tools: ["Bash"]
---

# /ga-mcp-full:auth-status

Report whether ga-mcp-full can currently authenticate to Google Analytics, and which credential source it is using.

## Steps

1. Run:

   ```bash
   ga-mcp-full auth status
   ```

2. Relay the output verbatim to the user. The command prints:
   - `Authenticated: yes|no`
   - `Auth method: OAuth (browser flow)` or `Application Default Credentials (gcloud)`
   - `Credentials file:` path (when OAuth cache is in use)
   - `Scopes: analytics.edit`
   - `Token expired: true|false`

3. If `Authenticated: no`, offer `/ga-mcp-full:auth-login` or `/ga-mcp-full:setup` as next steps depending on the error message.
