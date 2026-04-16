"""Audience CRUD tools (v1alpha API)."""

from __future__ import annotations

from typing import Any, Dict, List

from google.analytics import admin_v1alpha

from ga_mcp.tools.utils import (
    construct_audience_rn,
    construct_property_rn,
    create_admin_alpha_client,
    handle_ga_errors,
    proto_to_dict,
)


@handle_ga_errors
async def list_audiences(property_id: int | str) -> List[Dict[str, Any]]:
    """Lists all audiences for a GA4 property.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
    """
    request = admin_v1alpha.ListAudiencesRequest(
        parent=construct_property_rn(property_id),
    )
    pager = await create_admin_alpha_client().list_audiences(request=request)
    return [proto_to_dict(a) async for a in pager]


@handle_ga_errors
async def create_audience(
    property_id: int | str,
    display_name: str,
    description: str,
    membership_duration_days: int,
    filter_clauses: List[Dict[str, Any]],
    event_trigger: Dict[str, Any] = None,
    exclusion_duration_mode: str = None,
) -> Dict[str, Any]:
    """Creates a new audience on a GA4 property.

    Audiences define segments of users based on filter criteria. The complex
    filter_clauses structure is accepted as a list of dicts matching the
    AudienceFilterClause protobuf schema.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        display_name: Human-readable name for the audience.
        description: Description of what this audience represents.
        membership_duration_days: How long a user stays in the audience after
            qualifying (1-540 days).
        filter_clauses: List of AudienceFilterClause dicts. Each must have a
            'clause_type' ('INCLUDE' or 'EXCLUDE') and either
            'simple_filter' or 'sequence_filter'. See GA4 Admin API docs for
            the full schema.
        event_trigger: Optional AudienceEventTrigger dict with 'event_name'
            and 'log_condition'.
        exclusion_duration_mode: 'EXCLUDE_TEMPORARILY' or 'EXCLUDE_PERMANENTLY'.
    """
    audience = admin_v1alpha.Audience(
        display_name=display_name,
        description=description,
        membership_duration_days=membership_duration_days,
        filter_clauses=[
            admin_v1alpha.AudienceFilterClause(fc) for fc in filter_clauses
        ],
    )
    if event_trigger:
        audience.event_trigger = admin_v1alpha.AudienceEventTrigger(event_trigger)
    if exclusion_duration_mode:
        audience.exclusion_duration_mode = exclusion_duration_mode

    response = await create_admin_alpha_client().create_audience(
        parent=construct_property_rn(property_id),
        audience=audience,
    )
    return proto_to_dict(response)


@handle_ga_errors
async def archive_audience(
    property_id: int | str,
    audience_id: str,
) -> str:
    """Archives an audience. Archived audiences are no longer populated with
    new users but can still be used in reports for historical data.

    WARNING: This cannot be undone.

    Args:
        property_id: The GA4 property ID (number or 'properties/<number>').
        audience_id: The audience resource ID or full resource name.
    """
    request = admin_v1alpha.ArchiveAudienceRequest(
        name=construct_audience_rn(property_id, audience_id),
    )
    await create_admin_alpha_client().archive_audience(request=request)
    return f"Audience {audience_id} archived successfully."
