"""BigQuery link CRUD tools (v1alpha API)."""

from __future__ import annotations

from typing import Any, Dict, List

from google.analytics import admin_v1alpha

from ga_mcp.tools.utils import (
    construct_bigquery_link_rn,
    construct_property_rn,
    create_admin_alpha_client,
    handle_ga_errors,
    proto_to_dict,
)


@handle_ga_errors
async def list_bigquery_links(property_id: int | str) -> List[Dict[str, Any]]:
    """Lists all BigQuery links for a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1alpha.ListBigQueryLinksRequest(
        parent=construct_property_rn(property_id),
    )
    pager = await create_admin_alpha_client().list_big_query_links(request=request)
    return [proto_to_dict(link) async for link in pager]


@handle_ga_errors
async def create_bigquery_link(
    property_id: int | str,
    project: str,
    daily_export_enabled: bool = True,
    streaming_export_enabled: bool = False,
    fresh_daily_export_enabled: bool = False,
    include_advertising_id: bool = False,
    export_streams: List[str] = None,
) -> Dict[str, Any]:
    """Creates a link between a GA4 property and a BigQuery project for data export.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        project: The BigQuery project ID (e.g. 'my-gcp-project').
        daily_export_enabled: Enable daily export (default True).
        streaming_export_enabled: Enable streaming export (default False).
        fresh_daily_export_enabled: Enable fresh daily export (default False).
        include_advertising_id: Include advertising ID in export (default False).
        export_streams: Optional list of data stream resource names to export.
            If empty, all streams are exported.
    """
    link = admin_v1alpha.BigQueryLink(
        project=project,
        daily_export_enabled=daily_export_enabled,
        streaming_export_enabled=streaming_export_enabled,
        fresh_daily_export_enabled=fresh_daily_export_enabled,
        include_advertising_id=include_advertising_id,
    )
    if export_streams:
        link.export_streams = export_streams

    response = await create_admin_alpha_client().create_big_query_link(
        parent=construct_property_rn(property_id),
        bigquery_link=link,
    )
    return proto_to_dict(response)


@handle_ga_errors
async def delete_bigquery_link(
    property_id: int | str,
    link_id: str,
) -> str:
    """Deletes a BigQuery link from a GA4 property.

    WARNING: This will stop data export to BigQuery. Existing exported data
    in BigQuery is not affected.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        link_id: The BigQuery link resource ID or full resource name.
    """
    request = admin_v1alpha.DeleteBigQueryLinkRequest(
        name=construct_bigquery_link_rn(property_id, link_id),
    )
    await create_admin_alpha_client().delete_big_query_link(request=request)
    return f"BigQuery link {link_id} deleted successfully."
