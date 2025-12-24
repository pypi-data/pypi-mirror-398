"""Usb resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.usb.models import (
    UsbListItem,
    USBDevice,
    Rule,
    AddRulesRequest,
    AddRulesResponse,
    Config,
    DeleteRulesRequest,
    DeleteRulesResponse,
    GetConfigResponse,
    ListResponse,
    ListRulesResponse,
    UpdateConfigRequest,
    UpdateConfigResponse,
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


class UsbResource:
    """API methods for usb.

    Proto definitions for runtime USB info on sites.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.usb.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_config(
        self,
        namespace: str,
        site: str,
        node: str,
    ) -> GetConfigResponse:
        """Get Config for usb.

        Get USB configuration from the node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/usb/{node}/config"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetConfigResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("usb", "get_config", e, response) from e

    def update_config(
        self,
        namespace: str,
        site: str,
        node: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateConfigResponse:
        """Update Config for usb.

        Update USB configuration on the node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/usb/{node}/config"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateConfigResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("usb", "update_config", e, response) from e

    def list(
        self,
        namespace: str,
        site: str,
        node: str,
    ) -> list[UsbListItem]:
        """List usb resources in a namespace.

        List connected USB devices

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/usb/{node}/list"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)

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
            return [UsbListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("usb", "list", e, response) from e

    def list_rules(
        self,
        namespace: str,
        site: str,
        node: str,
    ) -> ListRulesResponse:
        """List Rules for usb.

        List USB Enablement Rules
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/usb/{node}/rules"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListRulesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("usb", "list_rules", e, response) from e

    def add_rules(
        self,
        namespace: str,
        site: str,
        node: str,
        body: dict[str, Any] | None = None,
    ) -> AddRulesResponse:
        """Add Rules for usb.

        Add USB Enablement Rules
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/usb/{node}/rules/add"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AddRulesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("usb", "add_rules", e, response) from e

    def delete_rules(
        self,
        namespace: str,
        site: str,
        node: str,
        body: dict[str, Any] | None = None,
    ) -> DeleteRulesResponse:
        """Delete Rules for usb.

        Delete USB Enablement Rules
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/usb/{node}/rules/delete"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeleteRulesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("usb", "delete_rules", e, response) from e

