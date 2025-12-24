"""XcSaas resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.xc_saas.models import (
    GetRegistrationDetailsResponse,
    SendEmailResponse,
    SendSignupEmailRequest,
    XCSaaSSignupRequest,
    XCSaaSSignupResponse,
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


class XcSaasResource:
    """API methods for xc_saas.

    
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.xc_saas.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def signup_xc_saa_s(
        self,
        body: dict[str, Any] | None = None,
    ) -> XCSaaSSignupResponse:
        """Signup Xc Saa S for xc_saas.

        Use this API to signup registered Azure Service Bus (ASB)...
        """
        path = "/no_auth/namespaces/system/f5xc-saas/signup"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return XCSaaSSignupResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("xc_saas", "signup_xc_saa_s", e, response) from e

    def get_registration_details(
        self,
        token: str | None = None,
    ) -> GetRegistrationDetailsResponse:
        """Get Registration Details for xc_saas.

        Use this API to to get registration details (currently limited to...
        """
        path = "/no_auth/namespaces/system/f5xc-saas/signup/registration_details"

        params: dict[str, Any] = {}
        if token is not None:
            params["token"] = token

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetRegistrationDetailsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("xc_saas", "get_registration_details", e, response) from e

    def send_signup_email(
        self,
        body: dict[str, Any] | None = None,
    ) -> SendEmailResponse:
        """Send Signup Email for xc_saas.

        Use this API to send a tenant provisioning signup email when the...
        """
        path = "/no_auth/namespaces/system/f5xc-saas/signup/send_email"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SendEmailResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("xc_saas", "send_signup_email", e, response) from e

