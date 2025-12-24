"""Bfdp resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.bfdp.models import (
    EnableFeatureRequest,
    EnableFeatureResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
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


class BfdpResource:
    """API methods for bfdp.

    Custom handler in BFDP microservice will forward request(s) to Shape...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.bfdp.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def enable_feature(
        self,
        body: dict[str, Any] | None = None,
    ) -> EnableFeatureResponse:
        """Enable Feature for bfdp.

        Enable service by returning service account details
        """
        path = "/api/ai_data/bfdp/namespaces/system/bfdp/enable_feature"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EnableFeatureResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bfdp", "enable_feature", e, response) from e

    def refresh_token(
        self,
        body: dict[str, Any] | None = None,
    ) -> RefreshTokenResponse:
        """Refresh Token for bfdp.

        Enable service by returning service account details
        """
        path = "/api/ai_data/bfdp/namespaces/system/bfdp/refresh_token"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return RefreshTokenResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bfdp", "refresh_token", e, response) from e

