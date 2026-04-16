"""Read-only admin tools (ported from upstream analytics-mcp)."""

from __future__ import annotations

from typing import Any, Dict, List

from google.analytics import admin_v1alpha, admin_v1beta

from ga_mcp.tools.utils import (
    construct_property_rn,
    create_admin_client,
    create_admin_alpha_client,
    handle_ga_errors,
    proto_to_dict,
)


@handle_ga_errors
async def get_account_summaries() -> List[Dict[str, Any]]:
    """Retrieves all Google Analytics account summaries accessible to the
    authenticated user. Returns account names, IDs, and their properties."""
    pager = await create_admin_client().list_account_summaries()
    return [proto_to_dict(page) async for page in pager]


@handle_ga_errors
async def list_google_ads_links(property_id: int | str) -> List[Dict[str, Any]]:
    """Returns all Google Ads links for a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1beta.ListGoogleAdsLinksRequest(
        parent=construct_property_rn(property_id)
    )
    pager = await create_admin_client().list_google_ads_links(request=request)
    return [proto_to_dict(page) async for page in pager]


@handle_ga_errors
async def get_property_details(property_id: int | str) -> Dict[str, Any]:
    """Returns detailed information about a GA4 property including display name,
    time zone, currency, industry category, and service level.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1beta.GetPropertyRequest(
        name=construct_property_rn(property_id)
    )
    response = await create_admin_client().get_property(request=request)
    return proto_to_dict(response)


@handle_ga_errors
async def list_property_annotations(property_id: int | str) -> List[Dict[str, Any]]:
    """Returns annotations for a GA4 property. Annotations are notes on specific
    dates/periods (e.g. releases, campaign launches, traffic changes).

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1alpha.ListReportingDataAnnotationsRequest(
        parent=construct_property_rn(property_id)
    )
    pager = await create_admin_alpha_client().list_reporting_data_annotations(
        request=request
    )
    return [proto_to_dict(page) async for page in pager]
