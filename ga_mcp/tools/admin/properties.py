"""Property CRUD and data retention settings."""

from __future__ import annotations

from typing import Any, Dict, Optional

from google.analytics import admin_v1beta
from google.protobuf import field_mask_pb2

from ga_mcp.tools.utils import (
    build_field_mask,
    construct_property_rn,
    create_admin_client,
    handle_ga_errors,
    proto_to_dict,
)


@handle_ga_errors
async def create_property(
    parent: str,
    display_name: str,
    time_zone: str,
    currency_code: str = "USD",
    industry_category: str = None,
) -> Dict[str, Any]:
    """Creates a new GA4 property under the given account.

    WARNING: This creates a billable resource. Ensure you intend to create a
    new property.

    Args:
        parent: The account resource name, e.g. 'accounts/123456'.
        display_name: Human-readable name for the property (required).
        time_zone: Reporting time zone, e.g. 'America/New_York' (required).
        currency_code: ISO4217 currency code (default 'USD').
        industry_category: Optional industry, e.g. 'TECHNOLOGY'.
    """
    prop = admin_v1beta.Property(
        parent=parent,
        display_name=display_name,
        time_zone=time_zone,
        currency_code=currency_code,
    )
    if industry_category:
        prop.industry_category = industry_category

    response = await create_admin_client().create_property(property=prop)
    return proto_to_dict(response)


@handle_ga_errors
async def update_property(
    property_id: int | str,
    display_name: str = None,
    time_zone: str = None,
    currency_code: str = None,
    industry_category: str = None,
) -> Dict[str, Any]:
    """Updates a GA4 property. Only provided (non-None) fields are modified.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        display_name: New display name.
        time_zone: New reporting time zone.
        currency_code: New ISO4217 currency code.
        industry_category: New industry category.
    """
    fields = {
        "display_name": display_name,
        "time_zone": time_zone,
        "currency_code": currency_code,
        "industry_category": industry_category,
    }
    mask_paths = build_field_mask(fields)
    if not mask_paths:
        raise ValueError("At least one field must be provided for update.")

    prop = admin_v1beta.Property(name=construct_property_rn(property_id))
    for k, v in fields.items():
        if v is not None:
            setattr(prop, k, v)

    response = await create_admin_client().update_property(
        property=prop,
        update_mask=field_mask_pb2.FieldMask(paths=mask_paths),
    )
    return proto_to_dict(response)


@handle_ga_errors
async def delete_property(property_id: int | str) -> Dict[str, Any]:
    """Moves a GA4 property to the trash. It can be restored within 35 days;
    after that it is permanently deleted.

    WARNING: This is a destructive operation. All data streams, custom
    definitions, and configuration under this property will become inaccessible.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1beta.DeletePropertyRequest(
        name=construct_property_rn(property_id)
    )
    response = await create_admin_client().delete_property(request=request)
    return proto_to_dict(response)


@handle_ga_errors
async def update_data_retention_settings(
    property_id: int | str,
    event_data_retention: str = None,
    reset_user_data_on_new_activity: bool = None,
) -> Dict[str, Any]:
    """Updates data retention settings for a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        event_data_retention: Retention period, e.g. 'TWO_MONTHS', 'FOURTEEN_MONTHS',
            'TWENTY_SIX_MONTHS', 'THIRTY_EIGHT_MONTHS', 'FIFTY_MONTHS'.
        reset_user_data_on_new_activity: If true, resets user-level data retention
            on each new event from that user.
    """
    fields = {
        "event_data_retention": event_data_retention,
        "reset_user_data_on_new_activity": reset_user_data_on_new_activity,
    }
    mask_paths = build_field_mask(fields)
    if not mask_paths:
        raise ValueError("At least one field must be provided for update.")

    settings = admin_v1beta.DataRetentionSettings(
        name=f"{construct_property_rn(property_id)}/dataRetentionSettings"
    )
    if event_data_retention is not None:
        settings.event_data_retention = event_data_retention
    if reset_user_data_on_new_activity is not None:
        settings.reset_user_data_on_new_activity = reset_user_data_on_new_activity

    response = await create_admin_client().update_data_retention_settings(
        data_retention_settings=settings,
        update_mask=field_mask_pb2.FieldMask(paths=mask_paths),
    )
    return proto_to_dict(response)
