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

# Silent success if the user already has cached OAuth tokens.
if [[ -f "$CREDENTIALS_FILE" ]]; then
  exit 0
fi

# If the ga-mcp-full CLI is not on PATH, the MCP server can't start.
# Surface the install hint — everything else depends on this.
if ! command -v ga-mcp-full >/dev/null 2>&1; then
  cat >&2 <<'EOF'
[ga-mcp-full] The `ga-mcp-full` CLI is not on PATH.
  Install:  pip install ga-mcp-full
  Then:     /ga-mcp-full:auth-login
EOF
  exit 0
fi

# CLI installed but no cached credentials. The bundled OAuth client handles
# the majority path, so a single slash command is the next step.
cat >&2 <<'EOF'
[ga-mcp-full] Not yet authenticated. Run: /ga-mcp-full:auth-login
EOF

exit 0
