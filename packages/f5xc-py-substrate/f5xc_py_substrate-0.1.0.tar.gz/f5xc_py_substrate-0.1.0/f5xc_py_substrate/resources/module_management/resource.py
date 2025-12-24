"""ModuleManagement resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.module_management.models import (
    Response,
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


class ModuleManagementResource:
    """API methods for module_management.

    Package for managing a module.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.module_management.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_module_management_settings(
        self,
        namespace: str,
    ) -> Response:
        """Get Module Management Settings for module_management.

        Receive the module settings.
        """
        path = "/api/config/namespaces/{namespace}/module_management/settings"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("module_management", "get_module_management_settings", e, response) from e

