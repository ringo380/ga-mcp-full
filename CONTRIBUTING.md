# Contributing to ga-mcp-full

Thanks for considering a contribution. This project is small and intentionally scoped — PRs that keep it that way are easiest to land.

## Quick start

```bash
git clone https://github.com/ringo380/ga-mcp-full.git
cd ga-mcp-full
python -m venv .venv && source .venv/bin/activate
pip install -e .
ga-mcp-full --help
```

To iterate against a real GA4 property:

```bash
ga-mcp-full auth login         # opens the browser; caches tokens in ~/.config/ga-mcp/credentials.json
ga-mcp-full auth status        # confirms auth
ga-mcp-full serve              # starts the stdio MCP server on stdin/stdout
```

If you're working on the Claude Code plugin integration, load the local checkout directly instead of the marketplace copy:

```bash
claude --plugin-dir /path/to/ga-mcp-full
```

Then `/reload-plugins` inside Claude Code picks up changes to `commands/`, `hooks/`, and `.mcp.json` without restarting the session.

## What kinds of changes are in scope

**Welcome:**

- New tools that wrap additional GA4 Admin API / Data API endpoints (follow the existing module pattern in `ga_mcp/tools/admin/` and `ga_mcp/tools/reporting/`)
- Bug fixes, auth-flow hardening, refresh-failure edge cases
- Documentation improvements (README, PRIVACY.md, SECURITY.md, command docs, troubleshooting entries)
- Tests — there's currently no test coverage; any pytest-based starting point is appreciated
- Improvements to the Claude Code plugin surface (hooks, slash commands, SessionStart behavior)

**Not in scope without discussion:**

- Adding non-Google-Analytics integrations
- Switching OAuth libraries or the token storage location
- Changing the stdio transport contract (the project does not currently ship an HTTP mode)
- Adding telemetry, analytics, or phone-home behavior of any kind

If in doubt, open a discussion-type issue first with the `proposal` label.

## PR conventions

- Branch off `main`; target `main` for the PR.
- Keep PRs focused — one logical change per PR. "Drive-by" reformatting or unrelated fixes in the same PR will be asked to split.
- Commit messages follow roughly: `<type>: <short subject>` where `type` is one of `feat`, `fix`, `docs`, `chore`, `ci`, `refactor`, `test`. Bodies welcome when the why is non-obvious.
- Don't include AI-attribution lines (e.g., `Co-Authored-By: Claude`) in commits or PR descriptions.
- For user-facing changes, update the README / relevant command doc in the same PR.
- For changes that require a new release, bump both `pyproject.toml:version` and `.claude-plugin/plugin.json:version` to the same value — the release workflow will refuse to publish on mismatch.

## Running the plugin validator

If you touch `.claude-plugin/plugin.json`, `.mcp.json`, `commands/`, or `hooks/`, run Claude Code's plugin validator to catch schema regressions before opening the PR. From Claude Code with this repo open:

```
Use the plugin-dev:plugin-validator subagent to validate the plugin structure.
```

## Releases

Releases are cut from tags matching `v*.*.*`. The release workflow at `.github/workflows/release.yml` handles:

1. Building sdist + wheel
2. Asserting the git tag version matches `pyproject.toml`
3. Publishing to PyPI via OIDC trusted publishing

Tagging is currently maintainer-only. If your PR introduces a user-visible change, note in the PR whether you think it warrants a patch / minor / major bump, and a maintainer will cut the release after merging.

## Security disclosures

Do **not** file security vulnerabilities as public issues. See [SECURITY.md](./SECURITY.md) for the private reporting channel.

## Questions

Open an issue with the `question` label, or email ringo380@gmail.com.
