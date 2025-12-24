"""Gia resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.gia.models import (
    AllocateIPRequest,
    AllocateIPResponse,
    DeallocateIPRequest,
    DeallocateIPResponse,
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


class GiaResource:
    """API methods for gia.

    
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.gia.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def allocate_ip(
        self,
        body: dict[str, Any] | None = None,
    ) -> AllocateIPResponse:
        """Allocate Ip for gia.

        AllocateIP will allocate an ip address for the tenant read from context
        """
        path = "/api/gia/gia/allocateip"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AllocateIPResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("gia", "allocate_ip", e, response) from e

    def deallocate_ip(
        self,
    ) -> DeallocateIPResponse:
        """Deallocate Ip for gia.

        DeallocateIP will de-allocate the specified ip address for tenant
        """
        path = "/api/gia/gia/deallocateip"


        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeallocateIPResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("gia", "deallocate_ip", e, response) from e

