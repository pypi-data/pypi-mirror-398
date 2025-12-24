"""WafSignaturesChangelog resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.waf_signatures_changelog.models import (
    ReleaseSignatures,
    ReleasedSignaturesRsp,
    StagedSignature,
    StagedSignaturesReq,
    StagedSignaturesRsp,
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


class WafSignaturesChangelogResource:
    """API methods for waf_signatures_changelog.

    WAF Signatures Changelog custom APIs
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.waf_signatures_changelog.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_active_staged_signatures(
        self,
        namespace: str,
        vh_name: str,
    ) -> ReleasedSignaturesRsp:
        """Get Active Staged Signatures for waf_signatures_changelog.

        API to get active Staged Signatures
        """
        path = "/api/config/namespaces/{namespace}/virtual_hosts/{vh_name}/active_staged_signatures"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{vh_name}", vh_name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReleasedSignaturesRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("waf_signatures_changelog", "get_active_staged_signatures", e, response) from e

    def get_released_signatures(
        self,
        namespace: str,
        vh_name: str,
    ) -> ReleasedSignaturesRsp:
        """Get Released Signatures for waf_signatures_changelog.

        API to get Released Signatures
        """
        path = "/api/config/namespaces/{namespace}/virtual_hosts/{vh_name}/released_signatures"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{vh_name}", vh_name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReleasedSignaturesRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("waf_signatures_changelog", "get_released_signatures", e, response) from e

    def get_staged_signatures(
        self,
        namespace: str,
        vh_name: str,
        body: dict[str, Any] | None = None,
    ) -> StagedSignaturesRsp:
        """Get Staged Signatures for waf_signatures_changelog.

        API to get Staged Signatures
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{vh_name}/staged_signatures"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{vh_name}", vh_name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StagedSignaturesRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("waf_signatures_changelog", "get_staged_signatures", e, response) from e

