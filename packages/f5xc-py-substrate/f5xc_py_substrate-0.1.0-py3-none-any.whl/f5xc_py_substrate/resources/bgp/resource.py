"""Bgp resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.bgp.models import (
    BGPPath,
    Ipv4AddressType,
    Ipv6AddressType,
    IpAddressType,
    PeerStatusType,
    VerBGPPeers,
    BGPPeersResponse,
    BGPRoute,
    BGPRouteTable,
    BGPRoutingInstanceTable,
    VerBGPRoutes,
    BGPRoutesResponse,
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


class BgpResource:
    """API methods for bgp.

    Proto definitions for BGP peer information. Peer status and routes...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.bgp.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def show_bgp_peers(
        self,
        namespace: str,
        site: str,
    ) -> BGPPeersResponse:
        """Show Bgp Peers for bgp.

        Show BGP Peer information
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/ver/bgp_peers"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return BGPPeersResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bgp", "show_bgp_peers", e, response) from e

    def show_bgp_routes(
        self,
        namespace: str,
        site: str,
    ) -> BGPRoutesResponse:
        """Show Bgp Routes for bgp.

        Show routes exported / imported via BGP
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/ver/bgp_routes"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return BGPRoutesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bgp", "show_bgp_routes", e, response) from e

