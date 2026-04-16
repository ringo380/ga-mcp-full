"""Data stream CRUD tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from google.analytics import admin_v1beta
from google.protobuf import field_mask_pb2

from ga_mcp.tools.utils import (
    build_field_mask,
    construct_data_stream_rn,
    construct_property_rn,
    create_admin_client,
    handle_ga_errors,
    proto_to_dict,
)


@handle_ga_errors
async def list_data_streams(property_id: int | str) -> List[Dict[str, Any]]:
    """Lists all data streams for a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1beta.ListDataStreamsRequest(
        parent=construct_property_rn(property_id)
    )
    pager = await create_admin_client().list_data_streams(request=request)
    return [proto_to_dict(page) async for page in pager]


@handle_ga_errors
async def create_data_stream(
    property_id: int | str,
    type: str,
    display_name: str,
    default_uri: str = None,
    package_name: str = None,
    bundle_id: str = None,
) -> Dict[str, Any]:
    """Creates a new data stream on a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        type: Stream type: 'WEB_DATA_STREAM', 'ANDROID_APP_DATA_STREAM', or
            'IOS_APP_DATA_STREAM'. Immutable after creation.
        display_name: Human-readable name for the stream.
        default_uri: Default URI for web streams (e.g. 'https://example.com').
        package_name: Android package name (required for Android streams).
        bundle_id: iOS bundle ID (required for iOS streams).
    """
    stream = admin_v1beta.DataStream(
        type_=type,
        display_name=display_name,
    )
    if default_uri:
        stream.web_stream_data = admin_v1beta.DataStream.WebStreamData(
            default_uri=default_uri
        )
    if package_name:
        stream.android_app_stream_data = admin_v1beta.DataStream.AndroidAppStreamData(
            package_name=package_name
        )
    if bundle_id:
        stream.ios_app_stream_data = admin_v1beta.DataStream.IosAppStreamData(
            bundle_id=bundle_id
        )

    response = await create_admin_client().create_data_stream(
        parent=construct_property_rn(property_id),
        data_stream=stream,
    )
    return proto_to_dict(response)


@handle_ga_errors
async def update_data_stream(
    property_id: int | str,
    stream_id: int | str,
    display_name: str = None,
    default_uri: str = None,
) -> Dict[str, Any]:
    """Updates a data stream. Only provided (non-None) fields are modified.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        stream_id: The data stream ID.
        display_name: New display name.
        default_uri: New default URI (web streams only).
    """
    fields = {"display_name": display_name}
    mask_paths = build_field_mask(fields)
    if default_uri is not None:
        mask_paths.append("web_stream_data.default_uri")
    if not mask_paths:
        raise ValueError("At least one field must be provided for update.")

    stream = admin_v1beta.DataStream(
        name=construct_data_stream_rn(property_id, stream_id),
    )
    if display_name is not None:
        stream.display_name = display_name
    if default_uri is not None:
        stream.web_stream_data = admin_v1beta.DataStream.WebStreamData(
            default_uri=default_uri
        )

    response = await create_admin_client().update_data_stream(
        data_stream=stream,
        update_mask=field_mask_pb2.FieldMask(paths=mask_paths),
    )
    return proto_to_dict(response)


@handle_ga_errors
async def delete_data_stream(
    property_id: int | str,
    stream_id: int | str,
) -> str:
    """Deletes a data stream from a GA4 property.

    WARNING: This is irreversible. The data stream and its measurement ID will
    be permanently removed. Any tags using this stream's measurement ID will
    stop collecting data.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        stream_id: The data stream ID.
    """
    request = admin_v1beta.DeleteDataStreamRequest(
        name=construct_data_stream_rn(property_id, stream_id)
    )
    await create_admin_client().delete_data_stream(request=request)
    return f"Data stream {stream_id} deleted successfully."
