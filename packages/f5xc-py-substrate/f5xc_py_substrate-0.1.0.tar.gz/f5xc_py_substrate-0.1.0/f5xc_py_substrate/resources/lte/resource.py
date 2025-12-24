"""Lte resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.lte.models import (
    Signal,
    Sim,
    Lte,
    Config,
    DisconnectRequest,
    DisconnectResponse,
    GetConfigResponse,
    InfoResponse,
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


class LteResource:
    """API methods for lte.

    Proto definitions for runtime LTE configuration on sites.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.lte.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_config(
        self,
        namespace: str,
        site: str,
        node: str,
    ) -> GetConfigResponse:
        """Get Config for lte.

        Get LTE configuration from the node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/lte/{node}/config"
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
            raise F5XCValidationError("lte", "get_config", e, response) from e

    def update_config(
        self,
        namespace: str,
        site: str,
        node: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateConfigResponse:
        """Update Config for lte.

        Update LTE configuration on the node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/lte/{node}/config"
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
            raise F5XCValidationError("lte", "update_config", e, response) from e

    def disconnect(
        self,
        namespace: str,
        site: str,
        node: str,
        body: dict[str, Any] | None = None,
    ) -> DisconnectResponse:
        """Disconnect for lte.

        Disconnect the node from LTE network
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/lte/{node}/disconnect"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DisconnectResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("lte", "disconnect", e, response) from e

    def show_info(
        self,
        namespace: str,
        site: str,
        node: str,
    ) -> InfoResponse:
        """Show Info for lte.

        Get LTE runtime information
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/lte/{node}/info"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return InfoResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("lte", "show_info", e, response) from e

