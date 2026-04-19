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
   - `Account: <email>` — the Google Account currently logged in. May read `<unknown …>` for tokens issued before v0.4.0 that lack the openid/email scopes; tell the user to re-run `/ga-mcp-full:auth-login` to enable account identification.
   - `Auth method: OAuth (browser flow)` or `Application Default Credentials (gcloud)`
   - `Credentials file:` path (when OAuth cache is in use)
   - `Scopes:` space-separated list
   - `Token expired: true|false`
   - `Hint:` present only when account identification failed; includes the remediation.

3. If `Authenticated: no`, offer `/ga-mcp-full:auth-login` or `/ga-mcp-full:setup` as next steps depending on the error message.

4. If the user wants to see which account is logged in without leaving the MCP dialog, they can also invoke the `whoami` MCP tool; to switch accounts, invoke the `switch_account` MCP tool followed by `/ga-mcp-full:auth-login`.
