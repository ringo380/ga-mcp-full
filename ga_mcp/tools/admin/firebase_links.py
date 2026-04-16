"""Firebase link create/delete tools."""

from __future__ import annotations

from typing import Any, Dict, List

from google.analytics import admin_v1beta

from ga_mcp.tools.utils import (
    construct_firebase_link_rn,
    construct_property_rn,
    create_admin_client,
    handle_ga_errors,
    proto_to_dict,
)


@handle_ga_errors
async def list_firebase_links(property_id: int | str) -> List[Dict[str, Any]]:
    """Lists all Firebase links for a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1beta.ListFirebaseLinksRequest(
        parent=construct_property_rn(property_id),
    )
    pager = await create_admin_client().list_firebase_links(request=request)
    return [proto_to_dict(link) async for link in pager]


@handle_ga_errors
async def create_firebase_link(
    property_id: int | str,
    project: str,
) -> Dict[str, Any]:
    """Creates a link between a GA4 property and a Firebase project.

    A property can have at most one Firebase link.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        project: The Firebase project resource name,
            e.g. 'projects/my-firebase-project'.
    """
    link = admin_v1beta.FirebaseLink(project=project)
    response = await create_admin_client().create_firebase_link(
        parent=construct_property_rn(property_id),
        firebase_link=link,
    )
    return proto_to_dict(response)


@handle_ga_errors
async def delete_firebase_link(
    property_id: int | str,
    link_id: str,
) -> str:
    """Deletes a Firebase link from a GA4 property.

    WARNING: This will break the connection between GA4 and the Firebase
    project. Audiences and other shared configurations may be affected.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        link_id: The Firebase link resource ID or full resource name.
    """
    request = admin_v1beta.DeleteFirebaseLinkRequest(
        name=construct_firebase_link_rn(property_id, link_id),
    )
    await create_admin_client().delete_firebase_link(request=request)
    return f"Firebase link {link_id} deleted successfully."
