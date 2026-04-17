# Security Policy

## Reporting a vulnerability

If you believe you have found a security vulnerability in `ga-mcp-full`, please report it privately — do not open a public GitHub issue.

Use either:

- **GitHub private vulnerability reporting** (preferred): open an advisory at https://github.com/ringo380/ga-mcp-full/security/advisories/new
- **Email**: ringo380@gmail.com — include "ga-mcp-full security" in the subject. If the report contains sensitive technical details, PGP is available on request.

You should receive an acknowledgement within **72 hours**. Fixes for confirmed vulnerabilities are committed privately and coordinated with disclosure; the typical window from confirmation to publicly published fix is 7–30 days depending on severity.

## In scope

- Authentication / credential handling in the `ga-mcp-full` codebase (OAuth flow, token cache, PKCE, credential resolution order)
- MCP tool surface — command injection, argument coercion, unexpected state mutation
- The bundled Claude Code plugin artifacts: hook scripts, slash commands, `.mcp.json`
- The release pipeline (GitHub Actions workflow) and the published PyPI artifact
- Anything in the supply chain specific to this project (pinned dependencies, install scripts)

## Out of scope

- Vulnerabilities in Google's APIs, Google's OAuth servers, or the Analytics platform itself — report those directly to Google
- Vulnerabilities in upstream dependencies (`mcp`, `google-analytics-admin`, `google-analytics-data`, `google-auth`, etc.) that are not unique to this project — report those upstream; we'll bump versions when fixes land
- Issues that require a user to explicitly execute untrusted code the project never ships (e.g., running a modified fork that removes PKCE)
- The "unverified app" warning on Google's consent screen — this is expected behavior during Google's brand verification window and does not indicate a vulnerability
- The fact that the bundled OAuth client ID + secret are recoverable from the published artifact — this is intentional, per Google's native-app OAuth guidance (see the comment in `ga_mcp/auth.py`)

## Hardening posture

- **OAuth flow**: PKCE (S256) on every authorization exchange, per [Google's installed-app guidance](https://developers.google.com/identity/protocols/oauth2/native-app).
- **Loopback redirect**: binds to `127.0.0.1` on an OS-assigned free port; no wildcard registration.
- **Token storage**: `~/.config/ga-mcp/credentials.json` with file mode `0600`; no transmission of tokens off the user's machine.
- **Refresh-token invalidation**: when a cached refresh token is rejected by Google, the stale file is `unlink()`ed and the user is told to re-authenticate.
- **No server-side component**: the project maintains no hosted infrastructure that receives user credentials or Analytics data.
- **Release pipeline**: PyPI publishing uses [OIDC trusted publishing](https://docs.pypi.org/trusted-publishers/) — no long-lived API tokens in CI; the release workflow is environment-gated.

## Privacy

See [PRIVACY.md](./PRIVACY.md) for the full data-handling policy.

## Credit

Researchers who report valid vulnerabilities in good faith will be credited in the advisory and the release notes for the fix, unless they prefer to remain anonymous.
