"""Custom dimensions and custom metrics CRUD tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from google.analytics import admin_v1beta
from google.protobuf import field_mask_pb2

from ga_mcp.tools.utils import (
    build_field_mask,
    construct_custom_dimension_rn,
    construct_custom_metric_rn,
    construct_property_rn,
    create_admin_client,
    handle_ga_errors,
    proto_to_dict,
)


# ---------------------------------------------------------------------------
# Custom Dimensions
# ---------------------------------------------------------------------------


@handle_ga_errors
async def list_custom_dimensions(property_id: int | str) -> List[Dict[str, Any]]:
    """Lists all custom dimensions for a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1beta.ListCustomDimensionsRequest(
        parent=construct_property_rn(property_id)
    )
    pager = await create_admin_client().list_custom_dimensions(request=request)
    return [proto_to_dict(d) async for d in pager]


@handle_ga_errors
async def create_custom_dimension(
    property_id: int | str,
    parameter_name: str,
    display_name: str,
    scope: str,
    description: str = "",
    disallow_ads_personalization: bool = False,
) -> Dict[str, Any]:
    """Creates a custom dimension on a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        parameter_name: The event parameter or user property name (immutable,
            max 40 chars, e.g. 'content_type').
        display_name: Display name in the GA4 UI (max 82 chars).
        scope: 'EVENT', 'USER', or 'ITEM' (immutable).
        description: Optional description (max 150 chars).
        disallow_ads_personalization: If true, this dimension is excluded from
            ads personalization.
    """
    dim = admin_v1beta.CustomDimension(
        parameter_name=parameter_name,
        display_name=display_name,
        scope=scope,
        description=description,
        disallow_ads_personalization=disallow_ads_personalization,
    )
    response = await create_admin_client().create_custom_dimension(
        parent=construct_property_rn(property_id),
        custom_dimension=dim,
    )
    return proto_to_dict(response)


@handle_ga_errors
async def update_custom_dimension(
    property_id: int | str,
    custom_dimension_id: str,
    display_name: str = None,
    description: str = None,
    disallow_ads_personalization: bool = None,
) -> Dict[str, Any]:
    """Updates a custom dimension. Only provided (non-None) fields are modified.

    Note: parameter_name and scope are immutable and cannot be changed.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        custom_dimension_id: The custom dimension resource ID (the numeric
            portion from the resource name, or the full resource name).
        display_name: New display name (max 82 chars).
        description: New description (max 150 chars).
        disallow_ads_personalization: New ads personalization setting.
    """
    fields = {
        "display_name": display_name,
        "description": description,
        "disallow_ads_personalization": disallow_ads_personalization,
    }
    mask_paths = build_field_mask(fields)
    if not mask_paths:
        raise ValueError("At least one field must be provided for update.")

    dim = admin_v1beta.CustomDimension(
        name=construct_custom_dimension_rn(property_id, custom_dimension_id),
    )
    for k, v in fields.items():
        if v is not None:
            setattr(dim, k, v)

    response = await create_admin_client().update_custom_dimension(
        custom_dimension=dim,
        update_mask=field_mask_pb2.FieldMask(paths=mask_paths),
    )
    return proto_to_dict(response)


@handle_ga_errors
async def archive_custom_dimension(
    property_id: int | str,
    custom_dimension_id: str,
) -> str:
    """Archives (soft-deletes) a custom dimension. Archived dimensions can still
    appear in reports for historical data but no new data is collected.

    WARNING: This cannot be undone. The parameter_name cannot be reused after
    archiving.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        custom_dimension_id: The custom dimension resource ID or full name.
    """
    request = admin_v1beta.ArchiveCustomDimensionRequest(
        name=construct_custom_dimension_rn(property_id, custom_dimension_id),
    )
    await create_admin_client().archive_custom_dimension(request=request)
    return f"Custom dimension {custom_dimension_id} archived successfully."


# ---------------------------------------------------------------------------
# Custom Metrics
# ---------------------------------------------------------------------------


@handle_ga_errors
async def list_custom_metrics(property_id: int | str) -> List[Dict[str, Any]]:
    """Lists all custom metrics for a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1beta.ListCustomMetricsRequest(
        parent=construct_property_rn(property_id)
    )
    pager = await create_admin_client().list_custom_metrics(request=request)
    return [proto_to_dict(m) async for m in pager]


@handle_ga_errors
async def create_custom_metric(
    property_id: int | str,
    parameter_name: str,
    display_name: str,
    measurement_unit: str,
    scope: str = "EVENT",
    description: str = "",
    restricted_metric_type: List[str] = None,
) -> Dict[str, Any]:
    """Creates a custom metric on a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        parameter_name: The event parameter name (immutable, max 40 chars).
        display_name: Display name in the GA4 UI (max 82 chars).
        measurement_unit: 'STANDARD', 'CURRENCY', 'FEET', 'METERS', 'KILOMETERS',
            'MILES', 'MILLISECONDS', 'SECONDS', 'MINUTES', 'HOURS'.
        scope: Currently only 'EVENT' is supported (immutable).
        description: Optional description.
        restricted_metric_type: Required for CURRENCY unit. List of restricted
            types, e.g. ['COST_DATA', 'REVENUE_DATA'].
    """
    metric = admin_v1beta.CustomMetric(
        parameter_name=parameter_name,
        display_name=display_name,
        measurement_unit=measurement_unit,
        scope=scope,
        description=description,
    )
    if restricted_metric_type:
        metric.restricted_metric_type = restricted_metric_type

    response = await create_admin_client().create_custom_metric(
        parent=construct_property_rn(property_id),
        custom_metric=metric,
    )
    return proto_to_dict(response)


@handle_ga_errors
async def update_custom_metric(
    property_id: int | str,
    custom_metric_id: str,
    display_name: str = None,
    measurement_unit: str = None,
    description: str = None,
    restricted_metric_type: List[str] = None,
) -> Dict[str, Any]:
    """Updates a custom metric. Only provided (non-None) fields are modified.

    Note: parameter_name and scope are immutable and cannot be changed.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        custom_metric_id: The custom metric resource ID or full resource name.
        display_name: New display name (max 82 chars).
        measurement_unit: New measurement unit.
        description: New description.
        restricted_metric_type: New restricted metric types.
    """
    fields = {
        "display_name": display_name,
        "measurement_unit": measurement_unit,
        "description": description,
    }
    mask_paths = build_field_mask(fields)
    if restricted_metric_type is not None:
        mask_paths.append("restricted_metric_type")
    if not mask_paths:
        raise ValueError("At least one field must be provided for update.")

    metric = admin_v1beta.CustomMetric(
        name=construct_custom_metric_rn(property_id, custom_metric_id),
    )
    for k, v in fields.items():
        if v is not None:
            setattr(metric, k, v)
    if restricted_metric_type is not None:
        metric.restricted_metric_type = restricted_metric_type

    response = await create_admin_client().update_custom_metric(
        custom_metric=metric,
        update_mask=field_mask_pb2.FieldMask(paths=mask_paths),
    )
    return proto_to_dict(response)


@handle_ga_errors
async def archive_custom_metric(
    property_id: int | str,
    custom_metric_id: str,
) -> str:
    """Archives (soft-deletes) a custom metric. Archived metrics still appear
    in reports for historical data but no new data is collected.

    WARNING: This cannot be undone. The parameter_name cannot be reused.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        custom_metric_id: The custom metric resource ID or full resource name.
    """
    request = admin_v1beta.ArchiveCustomMetricRequest(
        name=construct_custom_metric_rn(property_id, custom_metric_id),
    )
    await create_admin_client().archive_custom_metric(request=request)
    return f"Custom metric {custom_metric_id} archived successfully."
