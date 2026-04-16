"""Metadata and hints for the reporting tools."""

from __future__ import annotations

from typing import Any, Dict, List

from google.analytics import admin_v1beta

from ga_mcp.tools.utils import (
    construct_property_rn,
    create_admin_client,
    handle_ga_errors,
    proto_to_dict,
)


def get_date_ranges_hints() -> str:
    return """
Each date range must have a `start_date` and `end_date`.
Dates can be absolute (YYYY-MM-DD) or relative: "today", "yesterday",
"NdaysAgo" (e.g. "30daysAgo").
Example: [{"start_date": "30daysAgo", "end_date": "yesterday"}]
"""


def get_dimension_filter_hints() -> str:
    return """
Dimension filters use a FilterExpression with `filter`, `and_group`,
`or_group`, or `not_expression`.
Example string filter:
  {"filter": {"field_name": "country", "string_filter": {"match_type": "EXACT", "value": "US"}}}
Example in-list filter:
  {"filter": {"field_name": "eventName", "in_list_filter": {"values": ["page_view", "scroll"]}}}
"""


def get_metric_filter_hints() -> str:
    return """
Metric filters use the same FilterExpression structure but with numeric_filter
or between_filter.
Example:
  {"filter": {"field_name": "sessions", "numeric_filter": {"operation": "GREATER_THAN", "value": {"int64_value": 100}}}}
"""


def get_order_bys_hints() -> str:
    return """
Order by dimension:
  {"dimension": {"dimension_name": "date"}, "desc": false}
Order by metric:
  {"metric": {"metric_name": "sessions"}, "desc": true}
"""


@handle_ga_errors
async def get_custom_dimensions_and_metrics(
    property_id: int | str,
) -> Dict[str, List[Dict[str, Any]]]:
    """Returns all custom dimensions and custom metrics for a GA4 property.
    Use these names in run_report dimensions/metrics lists.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    client = create_admin_client()
    prop_rn = construct_property_rn(property_id)

    dim_pager = await client.list_custom_dimensions(
        admin_v1beta.ListCustomDimensionsRequest(parent=prop_rn)
    )
    dims = [proto_to_dict(d) async for d in dim_pager]

    met_pager = await client.list_custom_metrics(
        admin_v1beta.ListCustomMetricsRequest(parent=prop_rn)
    )
    mets = [proto_to_dict(m) async for m in met_pager]

    return {"custom_dimensions": dims, "custom_metrics": mets}
