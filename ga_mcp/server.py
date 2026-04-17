"""Entry point for the GA4 Full Read/Write MCP server."""

from __future__ import annotations

import asyncio
import sys
import traceback
from importlib import metadata

import ga_mcp.coordinator as coordinator
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio


def _package_version() -> str:
    try:
        return metadata.version("ga-mcp-full")
    except metadata.PackageNotFoundError:
        return "0.0.0+unknown"


async def run_server_async() -> None:
    """Runs the MCP server over standard I/O."""
    print(f"Starting MCP Stdio Server: {coordinator.app.name}", file=sys.stderr)
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await coordinator.app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=coordinator.app.name,
                server_version=_package_version(),
                capabilities=coordinator.app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def run_server() -> None:
    """Synchronous wrapper to run the async MCP server."""
    try:
        asyncio.run(run_server_async())
    except KeyboardInterrupt:
        print("\nMCP Server stopped by user.", file=sys.stderr)
    except Exception:
        print("MCP Server encountered an error:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    finally:
        print("MCP Server process exiting.", file=sys.stderr)


if __name__ == "__main__":
    run_server()
