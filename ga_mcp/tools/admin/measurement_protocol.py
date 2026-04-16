"""Measurement Protocol secrets CRUD tools."""

from __future__ import annotations

from typing import Any, Dict, List

from google.analytics import admin_v1beta
from google.protobuf import field_mask_pb2

from ga_mcp.tools.utils import (
    build_field_mask,
    construct_data_stream_rn,
    construct_mp_secret_rn,
    create_admin_client,
    handle_ga_errors,
    proto_to_dict,
)


@handle_ga_errors
async def list_measurement_protocol_secrets(
    property_id: int | str,
    stream_id: int | str,
) -> List[Dict[str, Any]]:
    """Lists all Measurement Protocol secrets for a data stream.

    The secret_value is returned for each secret.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        stream_id: The data stream ID.
    """
    request = admin_v1beta.ListMeasurementProtocolSecretsRequest(
        parent=construct_data_stream_rn(property_id, stream_id),
    )
    pager = await create_admin_client().list_measurement_protocol_secrets(
        request=request
    )
    return [proto_to_dict(s) async for s in pager]


@handle_ga_errors
async def create_measurement_protocol_secret(
    property_id: int | str,
    stream_id: int | str,
    display_name: str,
) -> Dict[str, Any]:
    """Creates a new Measurement Protocol secret for a data stream.

    The secret_value is auto-generated and returned in the response.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        stream_id: The data stream ID.
        display_name: Human-readable name (max 100 chars).
    """
    secret = admin_v1beta.MeasurementProtocolSecret(
        display_name=display_name,
    )
    response = await create_admin_client().create_measurement_protocol_secret(
        parent=construct_data_stream_rn(property_id, stream_id),
        measurement_protocol_secret=secret,
    )
    return proto_to_dict(response)


@handle_ga_errors
async def update_measurement_protocol_secret(
    property_id: int | str,
    stream_id: int | str,
    secret_id: str,
    display_name: str,
) -> Dict[str, Any]:
    """Updates a Measurement Protocol secret's display name.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        stream_id: The data stream ID.
        secret_id: The secret resource ID or full resource name.
        display_name: New display name (max 100 chars).
    """
    secret = admin_v1beta.MeasurementProtocolSecret(
        name=construct_mp_secret_rn(property_id, stream_id, secret_id),
        display_name=display_name,
    )
    response = await create_admin_client().update_measurement_protocol_secret(
        measurement_protocol_secret=secret,
        update_mask=field_mask_pb2.FieldMask(paths=["display_name"]),
    )
    return proto_to_dict(response)


@handle_ga_errors
async def delete_measurement_protocol_secret(
    property_id: int | str,
    stream_id: int | str,
    secret_id: str,
) -> str:
    """Deletes a Measurement Protocol secret.

    WARNING: This is irreversible. Any systems using this secret will
    immediately lose the ability to send data via the Measurement Protocol.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        stream_id: The data stream ID.
        secret_id: The secret resource ID or full resource name.
    """
    request = admin_v1beta.DeleteMeasurementProtocolSecretRequest(
        name=construct_mp_secret_rn(property_id, stream_id, secret_id),
    )
    await create_admin_client().delete_measurement_protocol_secret(request=request)
    return f"Measurement Protocol secret {secret_id} deleted successfully."
