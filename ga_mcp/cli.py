"""CLI entry point for ga-mcp-full.

Usage:
    ga-mcp-full              Start the MCP server (stdio)
    ga-mcp-full auth         Authenticate via OAuth browser flow
    ga-mcp-full auth logout  Clear cached credentials
    ga-mcp-full auth status  Show current auth status
"""

from __future__ import annotations

import sys


def main() -> None:
    args = sys.argv[1:]

    if not args or args == ["serve"]:
        # Default: start the MCP server
        from ga_mcp.server import run_server
        run_server()

    elif args[0] == "auth":
        _handle_auth(args[1:])

    elif args[0] in ("--help", "-h"):
        print(__doc__.strip())

    else:
        print(f"Unknown command: {args[0]}", file=sys.stderr)
        print("Usage: ga-mcp-full [auth|serve|--help]", file=sys.stderr)
        sys.exit(1)


def _handle_auth(args: list[str]) -> None:
    from ga_mcp.auth import (
        run_oauth_flow,
        clear_credentials,
        get_credentials,
        _CREDENTIALS_FILE,
    )

    if not args or args[0] == "login":
        # Parse optional --client-id and --client-secret
        client_id = None
        client_secret = None
        for arg in args:
            if arg.startswith("--client-id="):
                client_id = arg.split("=", 1)[1]
            elif arg.startswith("--client-secret="):
                client_secret = arg.split("=", 1)[1]
        run_oauth_flow(client_id=client_id, client_secret=client_secret)

    elif args[0] == "logout":
        clear_credentials()

    elif args[0] == "status":
        try:
            has_oauth = _CREDENTIALS_FILE.exists()
            creds = get_credentials()
            print("Authenticated: yes")
            if has_oauth:
                print("Auth method: OAuth (browser flow)")
                print(f"Credentials file: {_CREDENTIALS_FILE}")
            else:
                print("Auth method: Application Default Credentials (gcloud)")
            print("Scopes: analytics.edit")
            if hasattr(creds, "expired"):
                print(f"Token expired: {creds.expired}")
        except ValueError as e:
            print("Authenticated: no")
            print(f"Error: {e}")

    else:
        print(f"Unknown auth command: {args[0]}", file=sys.stderr)
        print("Usage: ga-mcp-full auth [login|logout|status]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
