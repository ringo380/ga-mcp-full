---
description: First-run setup for the ga-mcp-full MCP server — install the CLI if needed, then complete the browser login.
allowed-tools: ["Bash"]
---

# /ga-mcp-full:setup

Walk the user from "plugin enabled" to "running GA4 queries from Claude Code" in the smallest possible number of steps.

## Happy path

1. **Verify the CLI is installed**:

   ```bash
   command -v ga-mcp-full >/dev/null 2>&1 && echo OK || echo MISSING
   ```

   If the output is `MISSING`, tell the user to run:

   ```bash
   pip install ga-mcp-full
   ```

   (Or for a local dev checkout: `pip install -e /path/to/ga-mcp-full`.) Do not pip-install on their behalf without asking.

2. **Check existing auth state** (skip login if already set up):

   ```bash
   ga-mcp-full auth status || true
   ```

   If the first line is `Authenticated: yes`, say so and stop — they're done. Point them at `/ga-mcp-full:auth-status` for details.

3. **Run the browser login**:

   ```bash
   ga-mcp-full auth login
   ```

   This opens Google's consent screen, binds a local callback on `127.0.0.1` on a random free port, completes the PKCE-protected OAuth exchange, and caches a refresh token at `~/.config/ga-mcp/credentials.json` (mode `0600`).

4. **Confirm**: run `ga-mcp-full auth status` once more. On `Authenticated: yes`, tell the user they can now ask Claude for things like "list my GA4 properties" and the MCP server will handle it. No Claude Code restart needed — the next tool call loads the new credentials from disk.

## Troubleshooting

- **"GA auth required: run /ga-mcp-full:auth-login ..."** appearing in a tool response — the user's cached refresh token was rejected or never existed. Run `/ga-mcp-full:auth-login`.
- **Browser did not open** — the CLI prints the auth URL to stderr; paste that URL into any browser to continue.

## Power users: use your own OAuth client

The server ships with a public Desktop OAuth client so most users never need to visit the Google Cloud Console. If you want to use your own client (e.g., for quota isolation, custom consent screen, or a different GCP project):

1. Create an OAuth 2.0 **Desktop** client at https://console.cloud.google.com/apis/credentials in a project where the Google Analytics Admin API and Google Analytics Data API are enabled.
2. Override the bundled defaults using either:
   - Env vars in your shell profile:
     ```bash
     export GA_MCP_CLIENT_ID="<your-client-id>"
     export GA_MCP_CLIENT_SECRET="<your-client-secret>"
     ```
   - Or drop the downloaded JSON at `~/.config/ga-mcp/client_secrets.json` (mode `0600`).
3. Then run `ga-mcp-full auth login` as usual.

## Already using `gcloud`?

If you have run `gcloud auth application-default login --scopes=https://www.googleapis.com/auth/analytics.edit`, the server auto-detects ADC and skips OAuth. No further setup needed.
