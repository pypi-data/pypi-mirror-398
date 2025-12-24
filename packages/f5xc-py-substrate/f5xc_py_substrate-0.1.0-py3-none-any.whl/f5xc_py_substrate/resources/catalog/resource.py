"""Catalog resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.catalog.models import (
    CatalogListItem,
    ListRequest,
    ListResponse,
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


class CatalogResource:
    """API methods for catalog.

    Custom API of services catalog.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.catalog.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(
        self,
    ) -> list[CatalogListItem]:
        """List catalog resources in a namespace.

        Retrieves service catalog tailor for the currently logged-in user.

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/web/namespaces/system/catalogs"

        params: dict[str, Any] = {}

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

        items = response.get("items", [])
        errors = response.get("errors", [])

        if errors:
            raise F5XCPartialResultsError(items=items, errors=errors)

        try:
            return [CatalogListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("catalog", "list", e, response) from e

