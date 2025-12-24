"""TpmProvision resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.tpm_provision.models import (
    DeviceInfo,
    PreauthRequest,
    PreauthResponse,
    ProvisionRequest,
    ProvisionResponse,
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


class TpmProvisionResource:
    """API methods for tpm_provision.

    TPM Provisioning APIs used to generate F5XC certificates
to program...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.tpm_provision.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def preauth(
        self,
        body: dict[str, Any] | None = None,
    ) -> PreauthResponse:
        """Preauth for tpm_provision.

        Pre-flight auth checks before calling the Provision API
        """
        path = "/api/tpm/tpm/preauth"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PreauthResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tpm_provision", "preauth", e, response) from e

    def provision(
        self,
        body: dict[str, Any] | None = None,
    ) -> ProvisionResponse:
        """Provision for tpm_provision.

        
        """
        path = "/api/tpm/tpm/provision"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ProvisionResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tpm_provision", "provision", e, response) from e

