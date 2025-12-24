"""Subscription resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.subscription.models import (
    Empty,
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


class SubscriptionResource:
    """API methods for subscription.

    Use this API to subscribe to XC addon services served by akar
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.subscription.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def subscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> SubscribeResponse:
        """Subscribe for subscription.

        Subscribe to XC addon services
        """
        path = "/api/web/namespaces/system/addon/subscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("subscription", "subscribe", e, response) from e

    def unsubscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> UnsubscribeResponse:
        """Unsubscribe for subscription.

        Unsubscribe to  XC addon services
        """
        path = "/api/web/namespaces/system/addon/unsubscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UnsubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("subscription", "unsubscribe", e, response) from e

