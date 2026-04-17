#!/bin/bash
# PreToolUse hook for ga-mcp-full plugin.
#
# Fires before any mcp__ga-mcp-full__* tool call. If the user has no cached
# OAuth tokens and no ADC, emits `additionalContext` that nudges Claude to
# tell the user to run /ga-mcp-full:auth-login before the tool call runs.
#
# Always exits 0 — NEVER uses `permissionDecision: "deny"`. A deny here would
# race against a successful auth-login that may have just completed in another
# pane. The MCP server itself raises an actionable error if auth is still
# missing at tool-call time, so this hook is belt-and-suspenders only.
#
# Output contract (Claude Code hooks spec): write JSON to stdout with a
# hookSpecificOutput.additionalContext string, which is injected into Claude's
# context before the tool executes.
#
# Intentionally NOT using `set -e` / `pipefail` — hook runner failures should
# not propagate. Only `set -u` with `${VAR:-}` defaults everywhere.

set -u

CREDENTIALS_FILE="${HOME}/.config/ga-mcp/credentials.json"
ADC_FILE="${HOME}/.config/gcloud/application_default_credentials.json"

# If either OAuth cache or ADC is present, stay silent. Tool will likely succeed.
if [[ -f "$CREDENTIALS_FILE" ]] || [[ -f "$ADC_FILE" ]]; then
  exit 0
fi

# No credentials anywhere — inject context so Claude tells the user upfront
# instead of waiting for the tool to fail and recovering from the error.
cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "The user has not authenticated ga-mcp-full yet (no cached OAuth token at ~/.config/ga-mcp/credentials.json and no Application Default Credentials). Before this tool can succeed, tell the user to run /ga-mcp-full:auth-login in this Claude Code session, then retry the tool call. Do not attempt workarounds or guess credentials."
  }
}
EOF

exit 0
