#!/bin/bash
# SessionStart hook for ga-mcp-full plugin.
#
# Non-blocking, read-only check: emits a friendly hint to stderr if the user
# has not yet authenticated. Never fails the session start. Never opens a
# browser on its own — that would be surprising behavior during session boot.
#
# Intentionally does NOT use `set -e` / `pipefail` — an unexpected non-zero
# from any internal command must never propagate to the hook runner. All
# exit paths are explicit `exit 0`. Only `set -u` is kept, and every env-var
# reference uses `${VAR:-}` defaults so -u cannot trip on an unset variable.

set -u

CREDENTIALS_FILE="${HOME}/.config/ga-mcp/credentials.json"
CLIENT_SECRETS_FILE="${HOME}/.config/ga-mcp/client_secrets.json"

# Silent success if the user already has cached OAuth tokens.
if [[ -f "$CREDENTIALS_FILE" ]]; then
  exit 0
fi

# Check if the ga-mcp-full CLI is even installed — if not, the MCP server
# won't start anyway, so surface a more useful install hint.
if ! command -v ga-mcp-full >/dev/null 2>&1; then
  cat >&2 <<'EOF'
[ga-mcp-full] The `ga-mcp-full` CLI is not on PATH.
  Install it with:  pip install -e /path/to/ga-mcp-full
  Then run:         /ga-mcp-full:setup
EOF
  exit 0
fi

# CLI installed but no cached credentials yet — nudge the user toward setup.
if [[ -n "${GA_MCP_CLIENT_ID:-}" && -n "${GA_MCP_CLIENT_SECRET:-}" ]]; then
  cat >&2 <<'EOF'
[ga-mcp-full] OAuth client is configured but you have not logged in yet.
  Run:  /ga-mcp-full:auth-login
EOF
elif [[ -f "$CLIENT_SECRETS_FILE" ]]; then
  cat >&2 <<EOF
[ga-mcp-full] client_secrets.json found at $CLIENT_SECRETS_FILE but no cached tokens.
  Run:  /ga-mcp-full:auth-login
EOF
else
  cat >&2 <<'EOF'
[ga-mcp-full] Not yet configured. To finish setup:
  1. Create an OAuth 2.0 Desktop client in Google Cloud Console
     (APIs & Services > Credentials > Create OAuth client ID > Desktop)
  2. Run:  /ga-mcp-full:setup
EOF
fi

exit 0
