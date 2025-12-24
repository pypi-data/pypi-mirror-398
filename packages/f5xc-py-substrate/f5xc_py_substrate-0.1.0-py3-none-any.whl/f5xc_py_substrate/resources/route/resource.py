"""Route resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.route.models import (
    Ipv4AddressType,
    Ipv6AddressType,
    IpAddressType,
    DcgHop,
    DropNH,
    GREHop,
    GREType,
    IPSecType,
    IpSecHop,
    SslHop,
    IntermediateHop,
    IPinIPType,
    IPinUDPType,
    LocalNH,
    MPLSType,
    Info,
    Empty,
    PrefixListType,
    Request,
    RouteRoutes,
    Response,
    SSLType,
    SubnetNH,
    TunnelNH,
    SimplifiedNexthopType,
    SimplifiedEcmpNH,
    SimplifiedRouteInfo,
    SimplifiedRouteRequest,
    SimplifiedRoutes,
    SimplifiedRouteResponse,
)


# Exclusion group mappings for get() method
_EXCLUDE_GROUPS: dict[str, set[str]] = {
    "forms": {"create_form", "replace_form"},
    "references": {"referring_objects", "deleted_referred_objects", "disabled_referred_objects"},
    "system_metadata": {"system_metadata"},
}


def _resolve_exclude_groups(groups: list[str]) -> set[str]:
    """Resolve exclusion group names to field names."""
    fields: set[str] = set()
    for group in groups:
        if group in _EXCLUDE_GROUPS:
            fields.update(_EXCLUDE_GROUPS[group])
        else:
            # Allow direct field names for flexibility
            fields.add(group)
    return fields


class RouteResource:
    """API methods for route.

    Proto definitions for VER routes
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.route.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def show_routes(
        self,
        namespace: str,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Show Routes for route.

        Show VER routes matching the request
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/ver/routes"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("route", "show_routes", e, response) from e

    def show_simplified_routes(
        self,
        namespace: str,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> SimplifiedRouteResponse:
        """Show Simplified Routes for route.

        Show user-friendly VER routes matching the request
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/ver/simplified_routes"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SimplifiedRouteResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("route", "show_simplified_routes", e, response) from e

