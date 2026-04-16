"""Realtime reporting tool."""

from __future__ import annotations

from typing import Any, Dict, List

from google.analytics import data_v1beta

from ga_mcp.tools.utils import (
    construct_property_rn,
    create_data_client,
    handle_ga_errors,
    proto_to_dict,
)
from ga_mcp.tools.reporting.metadata import (
    get_dimension_filter_hints,
    get_metric_filter_hints,
    get_order_bys_hints,
)


def _run_realtime_report_description() -> str:
    return f"""
{run_realtime_report.__doc__}

## Hints for arguments

### Hints for `dimensions`
Use realtime dimensions from
https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-api-schema#dimensions

### Hints for `metrics`
Use realtime metrics from
https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-api-schema#metrics

### Hints for `dimension_filter`:
{get_dimension_filter_hints()}

### Hints for `metric_filter`:
{get_metric_filter_hints()}

### Hints for `order_bys`:
{get_order_bys_hints()}
"""


@handle_ga_errors
async def run_realtime_report(
    property_id: int | str,
    dimensions: List[str] = None,
    metrics: List[str] = None,
    dimension_filter: Dict[str, Any] = None,
    metric_filter: Dict[str, Any] = None,
    order_bys: List[Dict[str, Any]] = None,
    limit: int = None,
    offset: int = None,
    return_property_quota: bool = False,
) -> Dict[str, Any]:
    """Runs a Google Analytics realtime report showing live data for a property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        dimensions: Optional list of realtime dimension names.
        metrics: Optional list of realtime metric names.
        dimension_filter: Optional FilterExpression for dimensions.
        metric_filter: Optional FilterExpression for metrics.
        order_bys: Optional list of OrderBy objects.
        limit: Max rows to return.
        offset: Row offset for pagination.
        return_property_quota: Whether to include quota info.
    """
    request = data_v1beta.RunRealtimeReportRequest(
        property=construct_property_rn(property_id),
        return_property_quota=return_property_quota,
    )
    if dimensions:
        request.dimensions = [data_v1beta.Dimension(name=d) for d in dimensions]
    if metrics:
        request.metrics = [data_v1beta.Metric(name=m) for m in metrics]
    if dimension_filter:
        request.dimension_filter = data_v1beta.FilterExpression(dimension_filter)
    if metric_filter:
        request.metric_filter = data_v1beta.FilterExpression(metric_filter)
    if order_bys:
        request.order_bys = [data_v1beta.OrderBy(ob) for ob in order_bys]
    if limit:
        request.limit = limit
    if offset:
        request.offset = offset

    response = await create_data_client().run_realtime_report(request)
    return proto_to_dict(response)
