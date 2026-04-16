# Privacy Policy — ga-mcp-full

**Last updated:** 2026-04-16
**Project:** [ga-mcp-full](https://github.com/ringo380/ga-mcp-full)
**Contact:** ringo380@gmail.com — or open a GitHub issue at https://github.com/ringo380/ga-mcp-full/issues

## What ga-mcp-full is

`ga-mcp-full` is an open-source [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that exposes Google Analytics 4 Admin API and Data API endpoints as tools for AI assistants such as Claude Code. It runs entirely on the end user's own machine (stdio transport). There is no hosted backend operated by the project maintainers.

## What data is accessed

When you authenticate, ga-mcp-full is granted the `https://www.googleapis.com/auth/analytics.edit` OAuth scope. This allows the tool to:

- Read property-, data-stream-, and account-level configuration of your GA4 properties.
- Read report data, realtime data, and metadata from your GA4 properties.
- Create, update, and delete property-level resources you explicitly request: custom dimensions, custom metrics, key events, audiences, data streams, Firebase/BigQuery/Google Ads links, and measurement protocol secrets.

All access is on-demand and initiated by the user of the AI assistant. The tool does not perform background access.

## Where data is stored

- **OAuth credentials** (access + refresh tokens) are cached locally at `~/.config/ga-mcp/credentials.json` on the end user's own machine, with file permissions `0600` (user-read/write only). They are never transmitted to the project maintainers or any third party.
- **Google Analytics data** (reports, configuration) retrieved through the tool is passed directly from Google's API to the local MCP client and then to the AI assistant you are using. `ga-mcp-full` itself does not log, retain, or redistribute this data.
- **No server-side storage.** The project maintainers do not operate any hosted service that receives your data or credentials. The shared OAuth client ID + secret bundled with the tool exist only to identify the software to Google's OAuth servers; they do not route traffic through any third-party server.

## What is transmitted

- **To Google:** OAuth authorization requests and GA4 Admin/Data API requests, originating from your local machine, using the credentials you granted at consent time.
- **To your AI assistant:** tool results (API responses) returned through the MCP stdio transport on your local machine.
- **To the project maintainers:** nothing. There is no telemetry, analytics, crash reporting, or usage tracking built into the tool.

## Third-party services

- **Google** handles your OAuth consent, token issuance, and GA4 API requests. Google's privacy policy governs their processing of this data: https://policies.google.com/privacy
- **Your AI assistant vendor** (e.g., Anthropic for Claude Code) handles the AI-assistant side. Their privacy policy governs tool-result handling.

`ga-mcp-full` itself is an intermediary that runs on your machine and does not introduce additional data-collection relationships.

## Why the `analytics.edit` scope

The tool exposes ~30 GA4 Admin and Data API operations, including administrative ones (create/update custom dimensions, audiences, key events, and so on). Google's OAuth scope model does not offer a finer-grained "write-certain-things-only" alternative below `analytics.edit`, so the broader scope is requested to make the full tool set available. Users who only need read access may prefer to set up their own OAuth client with the `analytics.readonly` scope via the environment-variable override documented in the project README.

## Credential revocation

To revoke ga-mcp-full's access at any time:

1. Run `/ga-mcp-full:auth-logout` in Claude Code (or `ga-mcp-full auth logout` at the shell) to delete the local token cache.
2. Visit https://myaccount.google.com/permissions and remove "ga-mcp-full" from the list of apps with access to your account.

Either step alone is sufficient to end future access; both are recommended for defense in depth.

## Changes to this policy

Changes are made by commit to the `PRIVACY.md` file in this repository. The "Last updated" date at the top reflects the most recent substantive change. Significant changes affecting scope, data handling, or third parties will additionally be called out in release notes for the release that introduces them.

## Questions

Email **ringo380@gmail.com** or open an issue at https://github.com/ringo380/ga-mcp-full/issues.
