"""Common utilities for the GA4 MCP server.

Provides auth (analytics.edit scope), API clients, proto helpers, resource
name constructors, and an error-handling decorator.
"""

from __future__ import annotations

import functools
import json
from importlib import metadata
from typing import Any, Callable, Dict

import proto
from google.analytics import admin_v1alpha, admin_v1beta, data_v1beta
from google.api_core import exceptions as api_exceptions
from google.api_core.gapic_v1.client_info import ClientInfo

from ga_mcp.auth import (
    AuthRequiredError,
    clear_cached_credentials_silent,
    get_credentials,
)


def _get_package_version() -> str:
    try:
        return metadata.version("ga-mcp-full")
    except Exception:
        return "unknown"


_CLIENT_INFO = ClientInfo(user_agent=f"ga-mcp-full/{_get_package_version()}")


def _credentials_or_actionable_error():
    """Wrap get_credentials(), translating AuthRequiredError into a single
    imperative ValueError that the MCP tool layer surfaces verbatim."""
    try:
        return get_credentials()
    except AuthRequiredError as exc:
        raise ValueError(
            f"GA auth required: run {exc.remediation} in Claude Code, then retry."
        ) from exc


# ---------------------------------------------------------------------------
# API client factories
# ---------------------------------------------------------------------------

def create_admin_client() -> admin_v1beta.AnalyticsAdminServiceAsyncClient:
    return admin_v1beta.AnalyticsAdminServiceAsyncClient(
        client_info=_CLIENT_INFO, credentials=_credentials_or_actionable_error()
    )


def create_admin_alpha_client() -> admin_v1alpha.AnalyticsAdminServiceAsyncClient:
    return admin_v1alpha.AnalyticsAdminServiceAsyncClient(
        client_info=_CLIENT_INFO, credentials=_credentials_or_actionable_error()
    )


def create_data_client() -> data_v1beta.BetaAnalyticsDataAsyncClient:
    return data_v1beta.BetaAnalyticsDataAsyncClient(
        client_info=_CLIENT_INFO, credentials=_credentials_or_actionable_error()
    )


# ---------------------------------------------------------------------------
# Resource name helpers
# ---------------------------------------------------------------------------

def construct_property_rn(property_value: int | str) -> str:
    """Return ``properties/{id}`` from a numeric ID or resource name."""
    property_num = None
    if isinstance(property_value, int):
        property_num = property_value
    elif isinstance(property_value, str):
        property_value = property_value.strip()
        if property_value.isdigit():
            property_num = int(property_value)
        elif property_value.startswith("properties/"):
            numeric_part = property_value.split("/")[-1]
            if numeric_part.isdigit():
                property_num = int(numeric_part)
    if property_num is None:
        raise ValueError(
            f"Invalid property ID: {property_value!r}. "
            "Accepted formats: a number, or 'properties/<number>'."
        )
    return f"properties/{property_num}"


def construct_data_stream_rn(property_id: int | str, stream_id: int | str) -> str:
    """Return ``properties/{id}/dataStreams/{id}``."""
    parent = construct_property_rn(property_id)
    if isinstance(stream_id, str) and "/" in stream_id:
        return stream_id  # already a full resource name
    return f"{parent}/dataStreams/{stream_id}"


def construct_custom_dimension_rn(property_id: int | str, dim_name: str) -> str:
    """Return ``properties/{id}/customDimensions/{name}``."""
    parent = construct_property_rn(property_id)
    if dim_name.startswith("properties/"):
        return dim_name
    return f"{parent}/customDimensions/{dim_name}"


def construct_custom_metric_rn(property_id: int | str, metric_name: str) -> str:
    """Return ``properties/{id}/customMetrics/{name}``."""
    parent = construct_property_rn(property_id)
    if metric_name.startswith("properties/"):
        return metric_name
    return f"{parent}/customMetrics/{metric_name}"


def construct_key_event_rn(property_id: int | str, key_event_id: str) -> str:
    """Return ``properties/{id}/keyEvents/{id}``."""
    parent = construct_property_rn(property_id)
    if key_event_id.startswith("properties/"):
        return key_event_id
    return f"{parent}/keyEvents/{key_event_id}"


def construct_mp_secret_rn(
    property_id: int | str, stream_id: int | str, secret_id: str
) -> str:
    """Return ``properties/{id}/dataStreams/{id}/measurementProtocolSecrets/{id}``."""
    stream_rn = construct_data_stream_rn(property_id, stream_id)
    if secret_id.startswith("properties/"):
        return secret_id
    return f"{stream_rn}/measurementProtocolSecrets/{secret_id}"


def construct_google_ads_link_rn(property_id: int | str, link_id: str) -> str:
    parent = construct_property_rn(property_id)
    if link_id.startswith("properties/"):
        return link_id
    return f"{parent}/googleAdsLinks/{link_id}"


def construct_firebase_link_rn(property_id: int | str, link_id: str) -> str:
    parent = construct_property_rn(property_id)
    if link_id.startswith("properties/"):
        return link_id
    return f"{parent}/firebaseLinks/{link_id}"


def construct_audience_rn(property_id: int | str, audience_id: str) -> str:
    parent = construct_property_rn(property_id)
    if audience_id.startswith("properties/"):
        return audience_id
    return f"{parent}/audiences/{audience_id}"


def construct_bigquery_link_rn(property_id: int | str, link_id: str) -> str:
    parent = construct_property_rn(property_id)
    if link_id.startswith("properties/"):
        return link_id
    return f"{parent}/bigQueryLinks/{link_id}"


# ---------------------------------------------------------------------------
# Proto <-> dict/json helpers
# ---------------------------------------------------------------------------

def proto_to_dict(obj: proto.Message) -> Dict[str, Any]:
    return type(obj).to_dict(
        obj, use_integers_for_enums=False, preserving_proto_field_name=True
    )


def proto_to_json(obj: proto.Message) -> str:
    return type(obj).to_json(obj, indent=None, preserving_proto_field_name=True)


# ---------------------------------------------------------------------------
# Error-handling decorator
# ---------------------------------------------------------------------------

def handle_ga_errors(func: Callable) -> Callable:
    """Decorator that translates common GA API errors into readable messages.

    Catches ``Unauthenticated``, ``NotFound``, ``PermissionDenied``,
    ``InvalidArgument``, and ``FailedPrecondition`` and re-raises as
    ``ValueError`` with a clear message so the LLM receives actionable feedback.
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except api_exceptions.Unauthenticated as exc:
            # 401 from GA. The cached OAuth token was revoked, the scope grant
            # doesn't include analytics.edit, or ADC was used with insufficient
            # scopes. Clear our OAuth cache so the next /ga-mcp-full:auth-login
            # starts clean; ADC is not managed by this package so leave it.
            clear_cached_credentials_silent()
            raise ValueError(
                "GA auth required: the credentials were rejected by Google "
                "(token revoked, insufficient scope, or never granted "
                "analytics.edit). Run /ga-mcp-full:auth-login in Claude Code, "
                "then retry."
            ) from exc
        except api_exceptions.NotFound as exc:
            raise ValueError(
                f"Resource not found: {exc.message}. "
                "Check that the property/resource ID is correct and that you have access."
            ) from exc
        except api_exceptions.PermissionDenied as exc:
            raise ValueError(
                f"Permission denied: {exc.message}. "
                "Ensure the authenticated account has Editor or Admin role on this property."
            ) from exc
        except api_exceptions.InvalidArgument as exc:
            raise ValueError(
                f"Invalid argument: {exc.message}"
            ) from exc
        except api_exceptions.FailedPrecondition as exc:
            raise ValueError(
                f"Failed precondition: {exc.message}"
            ) from exc

    return wrapper


# ---------------------------------------------------------------------------
# FieldMask builder
# ---------------------------------------------------------------------------

def build_field_mask(provided_fields: Dict[str, Any]) -> list[str]:
    """Return a list of field paths for non-None values in *provided_fields*.

    Used by update tools to auto-build a ``FieldMask`` from the kwargs the
    caller actually supplied.
    """
    return [k for k, v in provided_fields.items() if v is not None]
