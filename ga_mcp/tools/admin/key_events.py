"""Key event (conversion) CRUD tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from google.analytics import admin_v1beta
from google.protobuf import field_mask_pb2

from ga_mcp.tools.utils import (
    build_field_mask,
    construct_key_event_rn,
    construct_property_rn,
    create_admin_client,
    handle_ga_errors,
    proto_to_dict,
)


@handle_ga_errors
async def list_key_events(property_id: int | str) -> List[Dict[str, Any]]:
    """Lists all key events (conversions) for a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1beta.ListKeyEventsRequest(
        parent=construct_property_rn(property_id)
    )
    pager = await create_admin_client().list_key_events(request=request)
    return [proto_to_dict(e) async for e in pager]


@handle_ga_errors
async def create_key_event(
    property_id: int | str,
    event_name: str,
    counting_method: str = "ONCE_PER_EVENT",
    default_value_numeric: float = None,
    default_value_currency_code: str = None,
) -> Dict[str, Any]:
    """Marks an event name as a key event (conversion) on a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        event_name: The event name to mark as a key event (immutable).
        counting_method: 'ONCE_PER_EVENT' or 'ONCE_PER_SESSION'.
        default_value_numeric: Optional default monetary value.
        default_value_currency_code: Optional ISO4217 currency for the default value.
    """
    key_event = admin_v1beta.KeyEvent(
        event_name=event_name,
        counting_method=counting_method,
    )
    if default_value_numeric is not None or default_value_currency_code is not None:
        dv = admin_v1beta.KeyEvent.DefaultValue()
        if default_value_numeric is not None:
            dv.numeric_value = default_value_numeric
        if default_value_currency_code is not None:
            dv.currency_code = default_value_currency_code
        key_event.default_value = dv

    response = await create_admin_client().create_key_event(
        parent=construct_property_rn(property_id),
        key_event=key_event,
    )
    return proto_to_dict(response)


@handle_ga_errors
async def update_key_event(
    property_id: int | str,
    key_event_id: str,
    counting_method: str = None,
    default_value_numeric: float = None,
    default_value_currency_code: str = None,
) -> Dict[str, Any]:
    """Updates a key event. Only provided (non-None) fields are modified.

    Note: event_name is immutable and cannot be changed.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        key_event_id: The key event resource ID or full resource name.
        counting_method: New counting method.
        default_value_numeric: New default monetary value.
        default_value_currency_code: New currency code for default value.
    """
    fields = {"counting_method": counting_method}
    mask_paths = build_field_mask(fields)

    if default_value_numeric is not None or default_value_currency_code is not None:
        mask_paths.append("default_value")

    if not mask_paths:
        raise ValueError("At least one field must be provided for update.")

    ke = admin_v1beta.KeyEvent(
        name=construct_key_event_rn(property_id, key_event_id),
    )
    if counting_method is not None:
        ke.counting_method = counting_method
    if default_value_numeric is not None or default_value_currency_code is not None:
        dv = admin_v1beta.KeyEvent.DefaultValue()
        if default_value_numeric is not None:
            dv.numeric_value = default_value_numeric
        if default_value_currency_code is not None:
            dv.currency_code = default_value_currency_code
        ke.default_value = dv

    response = await create_admin_client().update_key_event(
        key_event=ke,
        update_mask=field_mask_pb2.FieldMask(paths=mask_paths),
    )
    return proto_to_dict(response)


@handle_ga_errors
async def delete_key_event(
    property_id: int | str,
    key_event_id: str,
) -> str:
    """Deletes a key event (conversion) from a GA4 property.

    WARNING: This is irreversible. The event will no longer be tracked as a
    conversion, though historical data is retained.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        key_event_id: The key event resource ID or full resource name.
    """
    request = admin_v1beta.DeleteKeyEventRequest(
        name=construct_key_event_rn(property_id, key_event_id),
    )
    await create_admin_client().delete_key_event(request=request)
    return f"Key event {key_event_id} deleted successfully."
