"""AwsAccount resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.aws_account.models import (
    AccountMeta,
    ContactMeta,
    CompanyMeta,
    CRMInfo,
    UserMeta,
    AWSAccountSignupRequest,
    AWSAccountSignupResponse,
    RegistrationRequest,
    RegistrationResponse,
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


class AwsAccountResource:
    """API methods for aws_account.

    APIs to manage AWS Account resources.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.aws_account.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def register_new_aws_account(
        self,
        body: dict[str, Any] | None = None,
    ) -> RegistrationResponse:
        """Register New Aws Account for aws_account.

        Use this API to register F5XC AWS marketplace product for F5XC service.
        """
        path = "/no_auth/namespaces/system/aws/f5xc-saas/register"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return RegistrationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("aws_account", "register_new_aws_account", e, response) from e

    def signup_aws_account(
        self,
        body: dict[str, Any] | None = None,
    ) -> AWSAccountSignupResponse:
        """Signup Aws Account for aws_account.

        Use this API to signup AWS account for F5XC service.
        """
        path = "/no_auth/namespaces/system/aws/f5xc-saas/signup"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AWSAccountSignupResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("aws_account", "signup_aws_account", e, response) from e

