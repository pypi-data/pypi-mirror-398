"""SecretManagement resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.secret_management.models import (
    MatcherType,
    LabelSelectorType,
    GlobalSpecType,
    PolicyInfoType,
    PolicyData,
    GetPolicyDocumentResponse,
    KeyData,
    GetPublicKeyResponse,
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


class SecretManagementResource:
    """API methods for secret_management.

    F5XC Secret Management service serves APIs for information required...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.secret_management.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_public_key(
        self,
        key_version: int | None = None,
    ) -> GetPublicKeyResponse:
        """Get Public Key for secret_management.

        GetPublicKey API returns public part of the volterra secret...
        """
        path = "/api/secret_management/get_public_key"

        params: dict[str, Any] = {}
        if key_version is not None:
            params["key_version"] = key_version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetPublicKeyResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("secret_management", "get_public_key", e, response) from e

    def get_policy_document(
        self,
        namespace: str,
        name: str,
    ) -> GetPolicyDocumentResponse:
        """Get Policy Document for secret_management.

        GetPolicyDocument API returns secret policy document for the given...
        """
        path = "/api/secret_management/namespaces/{namespace}/secret_policys/{name}/get_policy_document"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetPolicyDocumentResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("secret_management", "get_policy_document", e, response) from e

