"""Tool registry and MCP server singleton.

Registers all tools (read + write) using the google-adk FunctionTool pattern
and exposes them via the low-level MCP Server's list_tools/call_tool handlers.
"""

from __future__ import annotations

import json

from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type
from mcp import types as mcp_types
from mcp.server.lowlevel import Server

# ---------------------------------------------------------------------------
# Read tools — reporting
# ---------------------------------------------------------------------------
from ga_mcp.tools.reporting.core import run_report, _run_report_description
from ga_mcp.tools.reporting.realtime import (
    run_realtime_report,
    _run_realtime_report_description,
)
from ga_mcp.tools.reporting.metadata import get_custom_dimensions_and_metrics

# ---------------------------------------------------------------------------
# Read tools — admin info
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.info import (
    get_account_summaries,
    get_property_details,
    list_google_ads_links,
    list_property_annotations,
)

# ---------------------------------------------------------------------------
# Read tools — new list endpoints
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.data_streams import list_data_streams
from ga_mcp.tools.admin.custom_definitions import (
    list_custom_dimensions,
    list_custom_metrics,
)
from ga_mcp.tools.admin.key_events import list_key_events
from ga_mcp.tools.admin.measurement_protocol import (
    list_measurement_protocol_secrets,
)
from ga_mcp.tools.admin.firebase_links import list_firebase_links
from ga_mcp.tools.admin.audiences import list_audiences
from ga_mcp.tools.admin.bigquery_links import list_bigquery_links

# ---------------------------------------------------------------------------
# Write tools — properties
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.properties import (
    create_property,
    update_property,
    delete_property,
    update_data_retention_settings,
)

# ---------------------------------------------------------------------------
# Write tools — data streams
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.data_streams import (
    create_data_stream,
    update_data_stream,
    delete_data_stream,
)

# ---------------------------------------------------------------------------
# Write tools — custom definitions
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.custom_definitions import (
    create_custom_dimension,
    update_custom_dimension,
    archive_custom_dimension,
    create_custom_metric,
    update_custom_metric,
    archive_custom_metric,
)

# ---------------------------------------------------------------------------
# Write tools — key events
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.key_events import (
    create_key_event,
    update_key_event,
    delete_key_event,
)

# ---------------------------------------------------------------------------
# Write tools — measurement protocol secrets
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.measurement_protocol import (
    create_measurement_protocol_secret,
    update_measurement_protocol_secret,
    delete_measurement_protocol_secret,
)

# ---------------------------------------------------------------------------
# Write tools — Google Ads links
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.google_ads_links import (
    create_google_ads_link,
    update_google_ads_link,
    delete_google_ads_link,
)

# ---------------------------------------------------------------------------
# Write tools — Firebase links
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.firebase_links import (
    create_firebase_link,
    delete_firebase_link,
)

# ---------------------------------------------------------------------------
# Write tools — audiences (v1alpha)
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.audiences import (
    create_audience,
    archive_audience,
)

# ---------------------------------------------------------------------------
# Write tools — BigQuery links (v1alpha)
# ---------------------------------------------------------------------------
from ga_mcp.tools.admin.bigquery_links import (
    create_bigquery_link,
    delete_bigquery_link,
)


# ---------------------------------------------------------------------------
# Build tool list using ADK FunctionTool wrappers
# ---------------------------------------------------------------------------

# Reporting tools with enhanced descriptions
_run_report_ft = FunctionTool(run_report)
_run_report_ft.description = _run_report_description()
_run_realtime_ft = FunctionTool(run_realtime_report)
_run_realtime_ft.description = _run_realtime_report_description()

tools = [
    # -- Reporting --
    _run_report_ft,
    _run_realtime_ft,
    FunctionTool(get_custom_dimensions_and_metrics),
    # -- Admin read --
    FunctionTool(get_account_summaries),
    FunctionTool(get_property_details),
    FunctionTool(list_google_ads_links),
    FunctionTool(list_property_annotations),
    # -- New read endpoints --
    FunctionTool(list_data_streams),
    FunctionTool(list_custom_dimensions),
    FunctionTool(list_custom_metrics),
    FunctionTool(list_key_events),
    FunctionTool(list_measurement_protocol_secrets),
    FunctionTool(list_firebase_links),
    FunctionTool(list_audiences),
    FunctionTool(list_bigquery_links),
    # -- Property write --
    FunctionTool(create_property),
    FunctionTool(update_property),
    FunctionTool(delete_property),
    FunctionTool(update_data_retention_settings),
    # -- Data stream write --
    FunctionTool(create_data_stream),
    FunctionTool(update_data_stream),
    FunctionTool(delete_data_stream),
    # -- Custom dimension write --
    FunctionTool(create_custom_dimension),
    FunctionTool(update_custom_dimension),
    FunctionTool(archive_custom_dimension),
    # -- Custom metric write --
    FunctionTool(create_custom_metric),
    FunctionTool(update_custom_metric),
    FunctionTool(archive_custom_metric),
    # -- Key event write --
    FunctionTool(create_key_event),
    FunctionTool(update_key_event),
    FunctionTool(delete_key_event),
    # -- Measurement Protocol secret write --
    FunctionTool(create_measurement_protocol_secret),
    FunctionTool(update_measurement_protocol_secret),
    FunctionTool(delete_measurement_protocol_secret),
    # -- Google Ads link write --
    FunctionTool(create_google_ads_link),
    FunctionTool(update_google_ads_link),
    FunctionTool(delete_google_ads_link),
    # -- Firebase link write --
    FunctionTool(create_firebase_link),
    FunctionTool(delete_firebase_link),
    # -- Audience write (v1alpha) --
    FunctionTool(create_audience),
    FunctionTool(archive_audience),
    # -- BigQuery link write (v1alpha) --
    FunctionTool(create_bigquery_link),
    FunctionTool(delete_bigquery_link),
]

tool_map = {t.name: t for t in tools}

# ---------------------------------------------------------------------------
# MCP Server instance
# ---------------------------------------------------------------------------

app = Server(name="GA4 Full Read/Write MCP Server")

# Convert ADK tools to MCP tool definitions
mcp_tools = [adk_to_mcp_tool_type(tool) for tool in tools]

# Fix empty schemas and spurious "type": "null" from ADK conversion bug
# (https://github.com/google/adk-python/issues/948)
for tool in mcp_tools:
    if tool.inputSchema == {}:
        tool.inputSchema = {"type": "object", "properties": {}}
    for prop in tool.inputSchema.get("properties", {}).values():
        if "anyOf" in prop and prop.get("type") == "null":
            del prop["type"]


@app.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
    return mcp_tools


@app.call_tool()
async def call_mcp_tool(name: str, arguments: dict) -> list[mcp_types.Content]:
    if name not in tool_map:
        error_text = json.dumps(
            {"error": f"Tool '{name}' not found. Use list_tools to see available tools."}
        )
        return [mcp_types.TextContent(type="text", text=error_text)]

    tool = tool_map[name]
    try:
        result = await tool.run_async(args=arguments, tool_context=None)
        response_text = json.dumps(result, indent=2)
        return [mcp_types.TextContent(type="text", text=response_text)]
    except Exception as e:
        error_text = json.dumps(
            {"error": f"Tool '{name}' failed: {str(e)}"}
        )
        return [mcp_types.TextContent(type="text", text=error_text)]
