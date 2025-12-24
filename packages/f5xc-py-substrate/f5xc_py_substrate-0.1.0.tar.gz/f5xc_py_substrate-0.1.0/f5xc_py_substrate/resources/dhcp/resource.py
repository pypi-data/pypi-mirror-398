"""Dhcp resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.dhcp.models import (
    KeyValuePair,
    LeaseInfo,
    SubnetInfo,
    Leases,
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


class DhcpResource:
    """API methods for dhcp.

    Proto definitions for DHCP lease display. All leases provided...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.dhcp.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def show_dhcp_leases(
        self,
        namespace: str,
        site: str,
    ) -> Leases:
        """Show Dhcp Leases for dhcp.

        Get DHCP lease information
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/ver/dhcp_leases"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Leases(**response)
        except ValidationError as e:
            raise F5XCValidationError("dhcp", "show_dhcp_leases", e, response) from e

