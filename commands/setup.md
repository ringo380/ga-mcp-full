---
description: Guided first-run setup for the ga-mcp-full MCP server — register a Google OAuth client, wire up credentials, and complete the browser login.
allowed-tools: ["Bash", "Read", "Write"]
---

# /ga-mcp-full:setup

Walk the user through end-to-end setup for the ga-mcp-full MCP server so they can go from "plugin enabled" to "running GA4 queries from Claude Code" in one session.

## Pre-flight checks (run these first, in order)

1. Verify the CLI is installed:
   ```bash
   command -v ga-mcp-full && ga-mcp-full --help || echo "MISSING"
   ```
   If missing, instruct the user to `pip install -e <path-to-ga-mcp-full>` (editable install) or `pip install ga-mcp-full` if it has been published. Do NOT try to pip install on their behalf — ask first.

2. Check for existing credentials:
   ```bash
   ga-mcp-full auth status || true
   ```
   If the status says `Authenticated: yes`, tell the user they are already set up and suggest `/ga-mcp-full:auth-status` for details. Stop here.

## OAuth client setup

Guide the user to create an OAuth 2.0 Desktop client in Google Cloud Console:

1. Explain they need to visit **https://console.cloud.google.com/apis/credentials** (in a project where the Google Analytics Admin API and Google Analytics Data API are enabled).
2. Steps:
   - Click **Create credentials → OAuth client ID**
   - Application type: **Desktop app**
   - Name: anything (e.g., "ga-mcp-full local")
   - Click **Create**, then download the JSON or copy the client ID + secret
3. Enable the required APIs if they have not been enabled:
   - Google Analytics Admin API
   - Google Analytics Data API

## Installing credentials

Ask the user which setup style they prefer:

- **(A) Drop the downloaded JSON** at `~/.config/ga-mcp/client_secrets.json` (simplest, no env vars).
- **(B) Set env vars** `GA_MCP_CLIENT_ID` and `GA_MCP_CLIENT_SECRET` in their shell profile.

For option (A), once the user has the downloaded JSON path, help them move it:
```bash
mkdir -p ~/.config/ga-mcp
mv "<downloaded-path>" ~/.config/ga-mcp/client_secrets.json
chmod 600 ~/.config/ga-mcp/client_secrets.json
```

For option (B), show them what to add to their `~/.zshrc` or `~/.bashrc`:
```bash
export GA_MCP_CLIENT_ID="<their-client-id>"
export GA_MCP_CLIENT_SECRET="<their-client-secret>"
```
Remind them to start a new shell (or source the profile) before running the login step, since Claude Code's MCP subprocess inherits the shell environment.

## Complete the browser login

Once credentials are in place, run:
```bash
ga-mcp-full auth login
```

This opens the browser, the user approves `analytics.edit` scope, and the refresh token is cached at `~/.config/ga-mcp/credentials.json`.

## Confirm success

Run `ga-mcp-full auth status` one more time and report the result. If `Authenticated: yes`, point out they can now ask Claude for things like "list my GA4 properties" and the MCP server will handle it.

## Troubleshooting

- **"OAuth client credentials not found"** — their env vars / client_secrets.json is not where the CLI is looking. Re-verify the path or re-open their shell.
- **Port 8085 already in use** — another process is using the callback port. `lsof -i :8085` to find it, kill it, retry.
- **Browser did not open** — the CLI prints the auth URL to stderr; paste that into any browser manually.
