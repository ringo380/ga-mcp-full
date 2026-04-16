"""Core reporting tool — run_report."""

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
    get_date_ranges_hints,
    get_dimension_filter_hints,
    get_metric_filter_hints,
    get_order_bys_hints,
)


def _run_report_description() -> str:
    return f"""
{run_report.__doc__}

## Hints for arguments

### Hints for `dimensions`
The `dimensions` list must consist of standard dimensions from
https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema#dimensions
or custom dimensions (use `get_custom_dimensions_and_metrics`).

### Hints for `metrics`
The `metrics` list must consist of standard metrics from
https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema#metrics
or custom metrics (use `get_custom_dimensions_and_metrics`).

### Hints for `date_ranges`:
{get_date_ranges_hints()}

### Hints for `dimension_filter`:
{get_dimension_filter_hints()}

### Hints for `metric_filter`:
{get_metric_filter_hints()}

### Hints for `order_bys`:
{get_order_bys_hints()}
"""


@handle_ga_errors
async def run_report(
    property_id: int | str,
    date_ranges: List[Dict[str, Any]],
    dimensions: List[str],
    metrics: List[str],
    dimension_filter: Dict[str, Any] = None,
    metric_filter: Dict[str, Any] = None,
    order_bys: List[Dict[str, Any]] = None,
    limit: int = None,
    offset: int = None,
    currency_code: str = None,
    return_property_quota: bool = False,
) -> Dict[str, Any]:
    """Runs a Google Analytics Data API report.

    Field names should be in snake_case (protobuf format).

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        date_ranges: List of date ranges, each with start_date and end_date.
        dimensions: List of dimension names.
        metrics: List of metric names.
        dimension_filter: Optional FilterExpression for dimensions.
        metric_filter: Optional FilterExpression for metrics.
        order_bys: Optional list of OrderBy objects.
        limit: Max rows to return (<=250,000).
        offset: Row offset for pagination.
        currency_code: ISO4217 currency code (e.g. "USD").
        return_property_quota: Whether to include quota info.
    """
    request = data_v1beta.RunReportRequest(
        property=construct_property_rn(property_id),
        dimensions=[data_v1beta.Dimension(name=d) for d in dimensions],
        metrics=[data_v1beta.Metric(name=m) for m in metrics],
        date_ranges=[data_v1beta.DateRange(dr) for dr in date_ranges],
        return_property_quota=return_property_quota,
    )
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
    if currency_code:
        request.currency_code = currency_code

    response = await create_data_client().run_report(request)
    return proto_to_dict(response)
