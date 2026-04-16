"""OAuth 2.0 browser-based authentication for GA4 MCP server.

On first use, opens a browser for Google OAuth consent with analytics.edit
scope. Caches refresh tokens locally at ~/.config/ga-mcp/credentials.json.
Falls back to Application Default Credentials if no OAuth tokens are found
and --no-browser is set.
"""

from __future__ import annotations

import json
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Optional
from urllib.parse import parse_qs, urlparse

import google.auth
import google.auth.transport.requests
from google.oauth2.credentials import Credentials

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCOPES = ["https://www.googleapis.com/auth/analytics.edit"]

# Default OAuth client — users can override via env vars
_DEFAULT_CLIENT_ID = os.environ.get("GA_MCP_CLIENT_ID", "")
_DEFAULT_CLIENT_SECRET = os.environ.get("GA_MCP_CLIENT_SECRET", "")

_CONFIG_DIR = Path.home() / ".config" / "ga-mcp"
_CREDENTIALS_FILE = _CONFIG_DIR / "credentials.json"
_CLIENT_SECRETS_FILE = _CONFIG_DIR / "client_secrets.json"

_REDIRECT_PORT = 8085
_REDIRECT_URI = f"http://localhost:{_REDIRECT_PORT}"


# ---------------------------------------------------------------------------
# Client ID/Secret resolution
# ---------------------------------------------------------------------------

def _get_client_config() -> dict:
    """Resolve OAuth client ID and secret from env vars or client_secrets.json."""
    client_id = _DEFAULT_CLIENT_ID
    client_secret = _DEFAULT_CLIENT_SECRET

    # Try client_secrets.json file if env vars not set
    if not client_id and _CLIENT_SECRETS_FILE.exists():
        with open(_CLIENT_SECRETS_FILE) as f:
            secrets = json.load(f)
        # Support both "installed" and "web" application types
        for app_type in ("installed", "web"):
            if app_type in secrets:
                client_id = secrets[app_type].get("client_id", "")
                client_secret = secrets[app_type].get("client_secret", "")
                break

    if not client_id or not client_secret:
        raise ValueError(
            "OAuth client credentials not found. Set up authentication with one of:\n"
            "  1. Set GA_MCP_CLIENT_ID and GA_MCP_CLIENT_SECRET env vars\n"
            "  2. Place a client_secrets.json file at:\n"
            f"     {_CLIENT_SECRETS_FILE}\n"
            "     (Download from Google Cloud Console > APIs & Services > Credentials)\n"
            "  3. Run: ga-mcp-full auth --client-id=YOUR_ID --client-secret=YOUR_SECRET"
        )

    return {"client_id": client_id, "client_secret": client_secret}


# ---------------------------------------------------------------------------
# Token persistence
# ---------------------------------------------------------------------------

def _save_credentials(creds: Credentials) -> None:
    """Save OAuth credentials to disk."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or SCOPES),
    }
    with open(_CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(_CREDENTIALS_FILE, 0o600)
    print(f"Credentials saved to {_CREDENTIALS_FILE}", file=sys.stderr)


def _load_credentials() -> Optional[Credentials]:
    """Load cached OAuth credentials from disk, refreshing if needed."""
    if not _CREDENTIALS_FILE.exists():
        return None

    with open(_CREDENTIALS_FILE) as f:
        data = json.load(f)

    creds = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes", SCOPES),
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(google.auth.transport.requests.Request())
            _save_credentials(creds)
        except Exception as exc:
            print(f"Token refresh failed: {exc}", file=sys.stderr)
            return None

    return creds


# ---------------------------------------------------------------------------
# OAuth browser flow
# ---------------------------------------------------------------------------

class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth authorization code."""

    authorization_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            _OAuthCallbackHandler.authorization_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>Authentication successful!</h2>"
                b"<p>You can close this tab and return to your terminal.</p>"
                b"</body></html>"
            )
        elif "error" in params:
            _OAuthCallbackHandler.error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<html><body><h2>Authentication failed</h2>"
                f"<p>Error: {params['error'][0]}</p></body></html>".encode()
            )
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        # Suppress HTTP request logging
        pass


def run_oauth_flow(client_id: str = None, client_secret: str = None) -> Credentials:
    """Run the OAuth 2.0 authorization code flow with a local browser.

    Opens the user's default browser to Google's consent screen, starts a
    local HTTP server to receive the callback, exchanges the auth code for
    tokens, and caches them.
    """
    if client_id and client_secret:
        config = {"client_id": client_id, "client_secret": client_secret}
    else:
        config = _get_client_config()

    client_id = config["client_id"]
    client_secret = config["client_secret"]

    # Build authorization URL
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={_REDIRECT_URI}&"
        "response_type=code&"
        f"scope={'%20'.join(SCOPES)}&"
        "access_type=offline&"
        "prompt=consent"
    )

    # Start local server to catch callback
    _OAuthCallbackHandler.authorization_code = None
    _OAuthCallbackHandler.error = None
    server = HTTPServer(("localhost", _REDIRECT_PORT), _OAuthCallbackHandler)

    print(f"\nOpening browser for Google Analytics authentication...", file=sys.stderr)
    print(f"If the browser doesn't open, visit:\n  {auth_url}\n", file=sys.stderr)
    webbrowser.open(auth_url)

    # Wait for the callback (single request)
    server.handle_request()
    server.server_close()

    if _OAuthCallbackHandler.error:
        raise ValueError(f"OAuth failed: {_OAuthCallbackHandler.error}")
    if not _OAuthCallbackHandler.authorization_code:
        raise ValueError("No authorization code received.")

    # Exchange auth code for tokens
    import httpx

    token_response = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": _OAuthCallbackHandler.authorization_code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": _REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    token_response.raise_for_status()
    token_data = token_response.json()

    if "error" in token_data:
        raise ValueError(f"Token exchange failed: {token_data['error']}")

    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )

    _save_credentials(creds)
    print("Authentication successful!", file=sys.stderr)
    return creds


# ---------------------------------------------------------------------------
# Public API: get credentials (used by utils.py)
# ---------------------------------------------------------------------------

def get_credentials() -> google.auth.credentials.Credentials:
    """Get valid Google credentials for the Analytics API.

    Resolution order:
    1. Cached OAuth tokens from ~/.config/ga-mcp/credentials.json
    2. Application Default Credentials (gcloud ADC)
    3. Trigger OAuth browser flow if interactive
    """
    # 1. Try cached OAuth tokens
    creds = _load_credentials()
    if creds and creds.valid:
        return creds

    # 2. Try ADC
    try:
        adc_creds, _ = google.auth.default(scopes=SCOPES)
        return adc_creds
    except google.auth.exceptions.DefaultCredentialsError:
        pass

    # 3. If we have client config, trigger the browser flow
    try:
        config = _get_client_config()
        return run_oauth_flow(config["client_id"], config["client_secret"])
    except ValueError:
        pass

    raise ValueError(
        "No valid credentials found. Authenticate with one of:\n"
        "  1. ga-mcp-full auth   (OAuth browser flow)\n"
        "  2. gcloud auth application-default login "
        "--scopes=https://www.googleapis.com/auth/analytics.edit\n"
        "  3. Set GA_MCP_CLIENT_ID + GA_MCP_CLIENT_SECRET env vars"
    )


def clear_credentials() -> None:
    """Remove cached OAuth credentials."""
    if _CREDENTIALS_FILE.exists():
        _CREDENTIALS_FILE.unlink()
        print(f"Removed {_CREDENTIALS_FILE}", file=sys.stderr)
    else:
        print("No cached credentials found.", file=sys.stderr)
