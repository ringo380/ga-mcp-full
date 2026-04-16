"""Google Ads link CRUD tools."""

from __future__ import annotations

from typing import Any, Dict, List

from google.analytics import admin_v1beta
from google.protobuf import field_mask_pb2

from ga_mcp.tools.utils import (
    build_field_mask,
    construct_google_ads_link_rn,
    construct_property_rn,
    create_admin_client,
    handle_ga_errors,
    proto_to_dict,
)


@handle_ga_errors
async def create_google_ads_link(
    property_id: int | str,
    customer_id: str,
    ads_personalization_enabled: bool = True,
) -> Dict[str, Any]:
    """Creates a link between a GA4 property and a Google Ads account.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        customer_id: The Google Ads customer ID (e.g. '1234567890', no dashes).
        ads_personalization_enabled: Enable ads personalization (default True).
    """
    link = admin_v1beta.GoogleAdsLink(
        customer_id=customer_id,
        ads_personalization_enabled=ads_personalization_enabled,
    )
    response = await create_admin_client().create_google_ads_link(
        parent=construct_property_rn(property_id),
        google_ads_link=link,
    )
    return proto_to_dict(response)


@handle_ga_errors
async def update_google_ads_link(
    property_id: int | str,
    link_id: str,
    ads_personalization_enabled: bool = None,
) -> Dict[str, Any]:
    """Updates a Google Ads link. Only provided (non-None) fields are modified.

    Note: customer_id is immutable and cannot be changed.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        link_id: The Google Ads link resource ID or full resource name.
        ads_personalization_enabled: New ads personalization setting.
    """
    fields = {"ads_personalization_enabled": ads_personalization_enabled}
    mask_paths = build_field_mask(fields)
    if not mask_paths:
        raise ValueError("At least one field must be provided for update.")

    link = admin_v1beta.GoogleAdsLink(
        name=construct_google_ads_link_rn(property_id, link_id),
    )
    if ads_personalization_enabled is not None:
        link.ads_personalization_enabled = ads_personalization_enabled

    response = await create_admin_client().update_google_ads_link(
        google_ads_link=link,
        update_mask=field_mask_pb2.FieldMask(paths=mask_paths),
    )
    return proto_to_dict(response)


@handle_ga_errors
async def delete_google_ads_link(
    property_id: int | str,
    link_id: str,
) -> str:
    """Deletes a Google Ads link from a GA4 property.

    WARNING: This will stop data sharing between the GA4 property and the
    linked Google Ads account.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        link_id: The Google Ads link resource ID or full resource name.
    """
    request = admin_v1beta.DeleteGoogleAdsLinkRequest(
        name=construct_google_ads_link_rn(property_id, link_id),
    )
    await create_admin_client().delete_google_ads_link(request=request)
    return f"Google Ads link {link_id} deleted successfully."
