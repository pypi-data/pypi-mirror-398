"""UserToken resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.user_token.models import (
    GetUserTokenResponse,
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


class UserTokenResource:
    """API methods for user_token.

    Use this API to get one time user token to connect to Web App...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.user_token.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_user_token(
        self,
    ) -> GetUserTokenResponse:
        """Get User Token for user_token.

        Get one time token to connect Web App Scanning Service
        """
        path = "/api/config/namespaces/system/was/user_token"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetUserTokenResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("user_token", "get_user_token", e, response) from e

