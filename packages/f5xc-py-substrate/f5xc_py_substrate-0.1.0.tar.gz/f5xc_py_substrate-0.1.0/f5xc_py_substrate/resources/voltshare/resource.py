"""Voltshare resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.voltshare.models import (
    VoltShareAccessId,
    VoltShareMetricValue,
    VoltShareAccessCounter,
    VoltShareMetricLabelFilter,
    AuditLogAggregationRequest,
    AuditLogAggregationResponse,
    AuditLogRequest,
    AuditLogResponse,
    AuditLogScrollRequest,
    UserRecordType,
    PolicyType,
    PolicyInformationType,
    DecryptSecretRequest,
    DecryptSecretResponse,
    ProcessPolicyRequest,
    ProcessPolicyResponse,
    VoltShareAccessCountRequest,
    VoltShareAccessCountResponse,
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


class VoltshareResource:
    """API methods for voltshare.

    F5XC VoltShare service serves APIs for users to securing the secrets...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.voltshare.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def volt_share_access_count_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> VoltShareAccessCountResponse:
        """Volt Share Access Count Query for voltshare.

        Request to get number of VoltShare API calls aggregated across...
        """
        path = "/api/secret_management/namespaces/{namespace}/voltshare/access_count"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return VoltShareAccessCountResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("voltshare", "volt_share_access_count_query", e, response) from e

    def audit_log_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AuditLogResponse:
        """Audit Log Query for voltshare.

        Request to get voltshare audit logs that matches the criteria in...
        """
        path = "/api/secret_management/namespaces/{namespace}/voltshare/audit_logs"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AuditLogResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("voltshare", "audit_log_query", e, response) from e

    def audit_log_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AuditLogAggregationResponse:
        """Audit Log Aggregation Query for voltshare.

        Request to get summary/analytics data for the audit logs that...
        """
        path = "/api/secret_management/namespaces/{namespace}/voltshare/audit_logs/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AuditLogAggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("voltshare", "audit_log_aggregation_query", e, response) from e

    def audit_log_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> AuditLogResponse:
        """Audit Log Scroll Query for voltshare.

        The response for audit log query contain no more than 500 messages....
        """
        path = "/api/secret_management/namespaces/{namespace}/voltshare/audit_logs/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AuditLogResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("voltshare", "audit_log_scroll_query", e, response) from e

    def audit_log_scroll_query_2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AuditLogResponse:
        """Audit Log Scroll Query 2 for voltshare.

        The response for audit log query contain no more than 500 messages....
        """
        path = "/api/secret_management/namespaces/{namespace}/voltshare/audit_logs/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AuditLogResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("voltshare", "audit_log_scroll_query_2", e, response) from e

    def decrypt_secret(
        self,
        body: dict[str, Any] | None = None,
    ) -> DecryptSecretResponse:
        """Decrypt Secret for voltshare.

        DecryptSecret API takes blinded encrypted secret and policy and...
        """
        path = "/api/secret_management/namespaces/system/voltshare/decrypt_secret"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DecryptSecretResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("voltshare", "decrypt_secret", e, response) from e

    def process_policy_information(
        self,
        body: dict[str, Any] | None = None,
    ) -> ProcessPolicyResponse:
        """Process Policy Information for voltshare.

        ProcessPolicyInformation API takes policy and secret name as input...
        """
        path = "/api/secret_management/namespaces/system/voltshare/process_policy_information"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ProcessPolicyResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("voltshare", "process_policy_information", e, response) from e

