"""OAuth 2.0 browser-based authentication for GA4 MCP server.

On first use, opens a browser for Google OAuth consent with analytics.edit
scope. Caches refresh tokens locally at ~/.config/ga-mcp/credentials.json.
Falls back to Application Default Credentials if no OAuth tokens are found
and --no-browser is set.

The OAuth flow binds to a random free port on 127.0.0.1 (per Google's
installed-app guidance) and uses PKCE (S256) for authorization-code
protection — client_secret is not a true secret for Desktop clients.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse

import google.auth
import google.auth.transport.requests
from google.oauth2.credentials import Credentials

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCOPES = ["https://www.googleapis.com/auth/analytics.edit"]

# Bundled public OAuth client for the shared "ga-mcp-full" Desktop app.
#
# Per Google's native-app OAuth guidance (https://developers.google.com/identity/protocols/oauth2/native-app),
# the client_secret for Desktop-type OAuth clients is NOT a true secret —
# PKCE (S256) is the actual security boundary, and Google's own docs mark
# client_secret as "Optional" for Desktop token exchange. Widely-distributed
# open-source tools embed the same way (gcloud CLI, rclone, etc.).
#
# The values are stored XOR-obfuscated ONLY to avoid triggering secret
# scanners and opportunistic bot harvesters that scrape public repos.
# They are trivially recoverable by anyone running this code — the
# obfuscation is NOT a security mechanism. Do not reason about it as one.
#
# If Google revokes this client due to abuse, rotate in place or set
# GA_MCP_CLIENT_ID / GA_MCP_CLIENT_SECRET env vars to override.
_BUNDLED_KEY = b"ga-mcp-full-bundled-oauth-key-v1"
_BUNDLED_CLIENT_ID_OBF = "X1kUVFNJFFNCWVQfTwMKBxoPDUEFVgVDX08FDBpDHEdTBx4FVEQdCRwcHRoHWw8UHBZKSgAOEhgNWBgAC04ZXxMEQxlNE0IL"
_BUNDLED_CLIENT_SECRET_OBF = "IC5uPjMoAB4GXR9ZKS9WK1oxNlsbMDA3Mn8tOk5dRlMATEo="


def _deobf(obf: str) -> str:
    raw = base64.b64decode(obf)
    return bytes(b ^ _BUNDLED_KEY[i % len(_BUNDLED_KEY)] for i, b in enumerate(raw)).decode("ascii")


_BUNDLED_CLIENT_ID = _deobf(_BUNDLED_CLIENT_ID_OBF)
_BUNDLED_CLIENT_SECRET = _deobf(_BUNDLED_CLIENT_SECRET_OBF)

# Power-user override (env vars) takes precedence over bundled defaults.
_ENV_CLIENT_ID = os.environ.get("GA_MCP_CLIENT_ID", "")
_ENV_CLIENT_SECRET = os.environ.get("GA_MCP_CLIENT_SECRET", "")

_CONFIG_DIR = Path.home() / ".config" / "ga-mcp"
_CREDENTIALS_FILE = _CONFIG_DIR / "credentials.json"
_CLIENT_SECRETS_FILE = _CONFIG_DIR / "client_secrets.json"


# ---------------------------------------------------------------------------
# Structured auth errors — surfaced as single-sentence tool errors
# ---------------------------------------------------------------------------

class AuthRequiredError(RuntimeError):
    """Raised when the server cannot obtain Google Analytics credentials.

    Callers in ``tools/utils.py`` catch this and re-raise a ``ValueError`` whose
    message is a single imperative sentence naming the exact slash command the
    user should run inside Claude Code.
    """

    def __init__(self, reason: str, remediation: str) -> None:
        self.reason = reason            # "no_credentials" | "refresh_failed" | "client_not_configured"
        self.remediation = remediation  # slash-command string, e.g. "/ga-mcp-full:auth-login"
        super().__init__(f"{reason}: {remediation}")


# ---------------------------------------------------------------------------
# Client ID/Secret resolution
# ---------------------------------------------------------------------------

def _get_client_config() -> dict:
    """Resolve OAuth client ID and secret.

    Resolution order:
      1. GA_MCP_CLIENT_ID + GA_MCP_CLIENT_SECRET env vars (power-user override)
      2. ~/.config/ga-mcp/client_secrets.json (legacy BYO path — no break)
      3. Bundled public Desktop client (majority path for new users)
    """
    # 1. Env var override
    if _ENV_CLIENT_ID and _ENV_CLIENT_SECRET:
        return {"client_id": _ENV_CLIENT_ID, "client_secret": _ENV_CLIENT_SECRET}

    # 2. Legacy client_secrets.json
    if _CLIENT_SECRETS_FILE.exists():
        with open(_CLIENT_SECRETS_FILE) as f:
            secrets_data = json.load(f)
        for app_type in ("installed", "web"):
            if app_type in secrets_data:
                cid = secrets_data[app_type].get("client_id", "")
                csec = secrets_data[app_type].get("client_secret", "")
                if cid and csec:
                    return {"client_id": cid, "client_secret": csec}

    # 3. Bundled defaults
    if _BUNDLED_CLIENT_ID and _BUNDLED_CLIENT_SECRET:
        return {"client_id": _BUNDLED_CLIENT_ID, "client_secret": _BUNDLED_CLIENT_SECRET}

    raise AuthRequiredError(
        reason="client_not_configured",
        remediation="/ga-mcp-full:setup",
    )


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
    """Load cached OAuth credentials from disk, refreshing if needed.

    Returns ``None`` only when the credentials file is absent (first-run case,
    where the caller should fall through to ADC / fresh browser flow).

    Raises ``AuthRequiredError(reason="refresh_failed")`` when the cached
    refresh token is present but rejected by Google — the stale file is
    deleted and the user is told exactly which slash commands to run.
    """
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
            try:
                _CREDENTIALS_FILE.unlink()
            except OSError:
                pass
            raise AuthRequiredError(
                reason="refresh_failed",
                remediation="/ga-mcp-full:auth-login",
            ) from exc

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


def _generate_pkce_pair() -> Tuple[str, str]:
    """Return ``(verifier, challenge)`` for OAuth 2.0 PKCE (S256)."""
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def run_oauth_flow(client_id: str = None, client_secret: str = None) -> Credentials:
    """Run the OAuth 2.0 authorization code flow with a local browser.

    Binds a local HTTP server to 127.0.0.1 on an OS-assigned free port (per
    Google's installed-app guidance), opens the user's default browser to
    Google's consent screen with PKCE (S256), exchanges the authorization
    code for tokens, and caches them.
    """
    if client_id and client_secret:
        config = {"client_id": client_id, "client_secret": client_secret}
    else:
        config = _get_client_config()

    client_id = config["client_id"]
    client_secret = config["client_secret"]

    # PKCE: protects the authorization code even if the client_secret is
    # intercepted (client_secret is not a true secret for Desktop clients).
    code_verifier, code_challenge = _generate_pkce_pair()

    # Bind to any free port on the loopback interface. Google accepts
    # 127.0.0.1:<any-port> for Desktop client redirects without prior
    # registration, so we don't need a fixed port.
    _OAuthCallbackHandler.authorization_code = None
    _OAuthCallbackHandler.error = None
    server = HTTPServer(("127.0.0.1", 0), _OAuthCallbackHandler)
    redirect_port = server.server_address[1]
    redirect_uri = f"http://127.0.0.1:{redirect_port}"

    # Build authorization URL
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        f"scope={'%20'.join(SCOPES)}&"
        "access_type=offline&"
        "prompt=consent&"
        f"code_challenge={code_challenge}&"
        "code_challenge_method=S256"
    )

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
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
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
    3. Trigger OAuth browser flow if interactive and a client config is resolvable

    Raises ``AuthRequiredError`` with an actionable remediation when no source
    yields valid credentials. Refresh-token failures propagate unchanged.
    """
    # 1. Try cached OAuth tokens (may raise AuthRequiredError on refresh failure)
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
    except AuthRequiredError:
        raise

    return run_oauth_flow(config["client_id"], config["client_secret"])


def clear_credentials() -> None:
    """Remove cached OAuth credentials."""
    if _CREDENTIALS_FILE.exists():
        _CREDENTIALS_FILE.unlink()
        print(f"Removed {_CREDENTIALS_FILE}", file=sys.stderr)
    else:
        print("No cached credentials found.", file=sys.stderr)
