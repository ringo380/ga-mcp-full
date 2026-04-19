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
        AuthRequiredError,
        run_oauth_flow,
        clear_credentials,
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
        try:
            run_oauth_flow(client_id=client_id, client_secret=client_secret)
        except AuthRequiredError as exc:
            print(
                f"Error: {exc.reason}. Remediation: run {exc.remediation}",
                file=sys.stderr,
            )
            sys.exit(1)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args[0] == "logout":
        clear_credentials()

    elif args[0] == "status":
        from ga_mcp.auth import get_authenticated_user_info

        info = get_authenticated_user_info()
        if not info.get("authenticated"):
            print("Authenticated: no")
            if info.get("reason"):
                print(f"Reason: {info['reason']}")
            if info.get("remediation"):
                print(f"Run: {info['remediation']}")
            return

        print("Authenticated: yes")
        if info.get("email"):
            print(f"Account: {info['email']}")
        else:
            print("Account: <unknown — re-run `ga-mcp-full auth login` to enable>")
        method = info.get("auth_method", "oauth")
        if method == "oauth":
            print("Auth method: OAuth (browser flow)")
            if info.get("credentials_file"):
                print(f"Credentials file: {info['credentials_file']}")
        else:
            print("Auth method: Application Default Credentials (gcloud)")
        scopes = info.get("scopes") or []
        if scopes:
            print(f"Scopes: {' '.join(scopes)}")
        print(f"Token expired: {info.get('token_expired', False)}")
        if info.get("hint"):
            print(f"Hint: {info['hint']}")

    else:
        print(f"Unknown auth command: {args[0]}", file=sys.stderr)
        print("Usage: ga-mcp-full auth [login|logout|status]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
