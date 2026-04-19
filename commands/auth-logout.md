---
description: Clear cached Google Analytics OAuth credentials for the ga-mcp-full MCP server.
allowed-tools: ["Bash"]
---

# /ga-mcp-full:auth-logout

Remove cached GA4 OAuth credentials so the next request either falls back to Application Default Credentials or triggers a fresh browser login.

## Steps

1. Run:

   ```bash
   ga-mcp-full auth logout
   ```

2. Confirm to the user that `~/.config/ga-mcp/credentials.json` was removed (the CLI prints the path to stderr on success, or "No cached credentials found." if there was nothing to remove).

3. Let the user know they can re-authenticate anytime with `/ga-mcp-full:auth-login`.

4. Note: inside the Claude Code MCP dialog, the `switch_account` tool performs the same cache clear and returns the previously-logged-in email — handy when a user wants to switch Google Accounts without leaving the chat.
