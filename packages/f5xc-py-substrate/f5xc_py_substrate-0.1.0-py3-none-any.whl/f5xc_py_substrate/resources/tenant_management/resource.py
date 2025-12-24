"""TenantManagement resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.tenant_management.models import (
    SubscribeRequest,
    SubscribeResponse,
    UnsubscribeRequest,
    UnsubscribeResponse,
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


class TenantManagementResource:
    """API methods for tenant_management.

    Public APIs for Tenant Management feature.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.tenant_management.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def delegated_access_subscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> SubscribeResponse:
        """Delegated Access Subscribe for tenant_management.

        Subscribe Delegated Access addon service feature. A support request...
        """
        path = "/api/web/namespaces/system/tenant_management/delegated_access/subscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant_management", "delegated_access_subscribe", e, response) from e

    def delegated_access_unsubscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> UnsubscribeResponse:
        """Delegated Access Unsubscribe for tenant_management.

        Unsubscribe Delegated Access addon service feature. A support...
        """
        path = "/api/web/namespaces/system/tenant_management/delegated_access/unsubscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UnsubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant_management", "delegated_access_unsubscribe", e, response) from e

