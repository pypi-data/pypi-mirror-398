"""VirtualAppliance resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.virtual_appliance.models import (
    GetImageRequest,
    GetImageResponse,
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


class VirtualApplianceResource:
    """API methods for virtual_appliance.

    Upgrade status custom APIs
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.virtual_appliance.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_image(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetImageResponse:
        """Get Image for virtual_appliance.

        API to get os IMAGE based on the software version
        """
        path = "/api/maurice/software_os_version"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetImageResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_appliance", "get_image", e, response) from e

