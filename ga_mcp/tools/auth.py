"""Account-identity MCP tools: whoami + switch_account.

These tools let a user see which Google Account the server is authenticated as
and stage a switch to a different account — without leaving the Claude Code
MCP dialog. The actual browser re-auth still has to happen via the
``/ga-mcp-full:auth-login`` slash command because MCP stdio has no TTY and
``run_oauth_flow()`` would hang the tool call (see CLAUDE.md).
"""

from __future__ import annotations

from typing import Any, Dict

from ga_mcp.auth import (
    clear_cached_credentials_silent,
    get_authenticated_user_info,
)


async def whoami() -> Dict[str, Any]:
    """Report which Google Account ga-mcp-full is currently authenticated as.

    Returns the logged-in email (when available), the auth method (OAuth
    browser flow vs. Application Default Credentials), the granted scopes,
    and any hints if account identification is unavailable.

    Tokens granted before v0.4.0 only carry the analytics.edit scope, so
    `email` will be None with a hint to re-run /ga-mcp-full:auth-login.
    """
    return get_authenticated_user_info()


async def switch_account() -> Dict[str, Any]:
    """Clear cached OAuth credentials so the user can sign in as a different Google Account.

    Does NOT trigger a browser — the MCP stdio transport has no TTY. After this
    runs, the user must execute /ga-mcp-full:auth-login in Claude Code (or
    `ga-mcp-full auth login` in their shell) to complete the switch.

    Returns a dict with `previous_email` (the account that was logged in, if
    known), `cleared` (True when cached OAuth creds were removed), and
    `next_step` (the exact slash command to run).
    """
    previous = get_authenticated_user_info()
    cleared = clear_cached_credentials_silent()
    return {
        "previous_email": previous.get("email"),
        "previous_auth_method": previous.get("auth_method"),
        "cleared": cleared,
        "next_step": "/ga-mcp-full:auth-login",
        "note": (
            "Cached OAuth credentials have been cleared. Run "
            "/ga-mcp-full:auth-login in Claude Code to sign in as a different "
            "Google Account. ADC credentials (from `gcloud auth "
            "application-default login`) are managed by gcloud, not this "
            "server, and were left untouched."
        ),
    }
