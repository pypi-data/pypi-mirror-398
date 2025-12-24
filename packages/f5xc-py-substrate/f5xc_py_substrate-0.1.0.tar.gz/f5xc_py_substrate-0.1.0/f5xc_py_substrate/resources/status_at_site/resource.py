"""StatusAtSite resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.status_at_site.models import (
    ProtobufAny,
    ConditionType,
    ErrorType,
    StatusResponse,
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


class StatusAtSiteResource:
    """API methods for status_at_site.

    Any user configured object in F5XC Edge Cloud has a status object...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.status_at_site.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_status(
        self,
        namespace: str,
        kind: str,
        name: str,
        site: str | None = None,
        site_type: str | None = None,
    ) -> StatusResponse:
        """Get Status for status_at_site.

        Get status of an object in a given site.
        """
        path = "/api/data/namespaces/{namespace}/{kind}/{name}/status_at_site"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{kind}", kind)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if site is not None:
            params["site"] = site
        if site_type is not None:
            params["site_type"] = site_type

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("status_at_site", "get_status", e, response) from e

