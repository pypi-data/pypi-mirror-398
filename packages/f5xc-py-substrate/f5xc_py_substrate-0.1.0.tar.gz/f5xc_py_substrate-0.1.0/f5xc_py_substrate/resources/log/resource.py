"""Log resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.log.models import (
    AccessLogAggregationRequest,
    AccessLogRequestV2,
    AuditLogAggregationRequest,
    AuditLogRequestV2,
    LabelFilter,
    ExternalConnectorRequest,
    FirewallLogAggregationRequest,
    FirewallLogRequest,
    K8SAuditLogAggregationRequest,
    K8SAuditLogRequest,
    K8SEventsAggregationRequest,
    K8SEventsRequest,
    AggregationResponse,
    Response,
    PlatformEventAggregationRequest,
    PlatformEventRequest,
    VK8SAuditLogAggregationRequest,
    VK8SAuditLogRequest,
    VK8SEventsAggregationRequest,
    VK8SEventsRequest,
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


class LogResource:
    """API methods for log.

    Two types of logs are supported, viz, access logs and audit logs.
 ...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.log.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def access_log_query_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Access Log Query V2 for log.

        Request to get access logs that matches the criteria in request for...
        """
        path = "/api/data/namespaces/{namespace}/access_logs"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "access_log_query_v2", e, response) from e

    def access_log_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AggregationResponse:
        """Access Log Aggregation Query for log.

        Request to get summary/analytics data for the access logs that...
        """
        path = "/api/data/namespaces/{namespace}/access_logs/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "access_log_aggregation_query", e, response) from e

    def access_log_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> Response:
        """Access Log Scroll Query for log.

        The response for access log query contain no more than 500 records....
        """
        path = "/api/data/namespaces/{namespace}/access_logs/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "access_log_scroll_query", e, response) from e

    def custom_access_log_scroll_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Custom Access Log Scroll Query for log.

        The response for access log query contain no more than 500 records....
        """
        path = "/api/data/namespaces/{namespace}/access_logs/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "custom_access_log_scroll_query", e, response) from e

    def audit_log_query_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Audit Log Query V2 for log.

        Request to get audit logs that matches the criteria in request for a...
        """
        path = "/api/data/namespaces/{namespace}/audit_logs"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "audit_log_query_v2", e, response) from e

    def audit_log_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AggregationResponse:
        """Audit Log Aggregation Query for log.

        Request to get summary/analytics data for the audit logs that...
        """
        path = "/api/data/namespaces/{namespace}/audit_logs/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "audit_log_aggregation_query", e, response) from e

    def audit_log_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> Response:
        """Audit Log Scroll Query for log.

        The response for audit log query contain no more than 500 messages....
        """
        path = "/api/data/namespaces/{namespace}/audit_logs/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "audit_log_scroll_query", e, response) from e

    def custom_audit_log_scroll_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Custom Audit Log Scroll Query for log.

        The response for audit log query contain no more than 500 messages....
        """
        path = "/api/data/namespaces/{namespace}/audit_logs/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "custom_audit_log_scroll_query", e, response) from e

    def firewall_log_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Firewall Log Query for log.

        Request to get access logs and network logs with policy hits. By...
        """
        path = "/api/data/namespaces/{namespace}/firewall_logs"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "firewall_log_query", e, response) from e

    def firewall_log_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AggregationResponse:
        """Firewall Log Aggregation Query for log.

        Request to get summary/analytics data for the firewall logs that...
        """
        path = "/api/data/namespaces/{namespace}/firewall_logs/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "firewall_log_aggregation_query", e, response) from e

    def firewall_log_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> Response:
        """Firewall Log Scroll Query for log.

        The response for firewall log query contain no more than 500...
        """
        path = "/api/data/namespaces/{namespace}/firewall_logs/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "firewall_log_scroll_query", e, response) from e

    def custom_firewall_log_scroll_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Custom Firewall Log Scroll Query for log.

        The response for firewall log query contain no more than 500...
        """
        path = "/api/data/namespaces/{namespace}/firewall_logs/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "custom_firewall_log_scroll_query", e, response) from e

    def k8_s_audit_log_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> Response:
        """K8 S Audit Log Scroll Query for log.

        The response for K8s audit log query contain no more than 500...
        """
        path = "/api/data/namespaces/{namespace}/k8s_audit_logs/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "k8_s_audit_log_scroll_query", e, response) from e

    def custom_k8_s_audit_log_scroll_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Custom K8 S Audit Log Scroll Query for log.

        The response for K8s audit log query contain no more than 500...
        """
        path = "/api/data/namespaces/{namespace}/k8s_audit_logs/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "custom_k8_s_audit_log_scroll_query", e, response) from e

    def k8_s_events_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> Response:
        """K8 S Events Scroll Query for log.

        The response for K8s events query contain no more than 500 events....
        """
        path = "/api/data/namespaces/{namespace}/k8s_events/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "k8_s_events_scroll_query", e, response) from e

    def custom_k8_s_events_scroll_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Custom K8 S Events Scroll Query for log.

        The response for K8s events query contain no more than 500 events....
        """
        path = "/api/data/namespaces/{namespace}/k8s_events/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "custom_k8_s_events_scroll_query", e, response) from e

    def platform_event_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Platform Event Query for log.

        Request to get platform event that matches the criteria in request...
        """
        path = "/api/data/namespaces/{namespace}/platform_events"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "platform_event_query", e, response) from e

    def platform_event_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AggregationResponse:
        """Platform Event Aggregation Query for log.

        Request to get summary/analytics data for the audit logs that...
        """
        path = "/api/data/namespaces/{namespace}/platform_events/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "platform_event_aggregation_query", e, response) from e

    def platform_event_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> Response:
        """Platform Event Scroll Query for log.

        The response for platform event query contain no more than 500...
        """
        path = "/api/data/namespaces/{namespace}/platform_events/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "platform_event_scroll_query", e, response) from e

    def custom_platform_event_scroll_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Custom Platform Event Scroll Query for log.

        The response for platform event query contain no more than 500...
        """
        path = "/api/data/namespaces/{namespace}/platform_events/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "custom_platform_event_scroll_query", e, response) from e

    def external_connector_log_query(
        self,
        namespace: str,
        site: str,
        external_connector: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """External Connector Log Query for log.

        Request to get external connector logs that matches the criteria in...
        """
        path = "/api/data/namespaces/{namespace}/site/{site}/external_connector/{external_connector}/logs"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{external_connector}", external_connector)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "external_connector_log_query", e, response) from e

    def k8_s_audit_log_query(
        self,
        namespace: str,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """K8 S Audit Log Query for log.

        Request to get Physical K8s audit logs that matches the criteria in...
        """
        path = "/api/data/namespaces/{namespace}/site/{site}/k8s_audit_logs"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "k8_s_audit_log_query", e, response) from e

    def k8_s_audit_log_aggregation_query(
        self,
        namespace: str,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> AggregationResponse:
        """K8 S Audit Log Aggregation Query for log.

        Request to get summary/analytics data for the K8s audit logs that...
        """
        path = "/api/data/namespaces/{namespace}/site/{site}/k8s_audit_logs/aggregation"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "k8_s_audit_log_aggregation_query", e, response) from e

    def k8_s_events_query(
        self,
        namespace: str,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """K8 S Events Query for log.

        Request to get physical K8s events that matches the criteria in...
        """
        path = "/api/data/namespaces/{namespace}/site/{site}/k8s_events"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "k8_s_events_query", e, response) from e

    def k8_s_events_aggregation_query(
        self,
        namespace: str,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> AggregationResponse:
        """K8 S Events Aggregation Query for log.

        Request to get summary/analytics data for the K8s events that...
        """
        path = "/api/data/namespaces/{namespace}/site/{site}/k8s_events/aggregation"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "k8_s_events_aggregation_query", e, response) from e

    def vk8_s_audit_log_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Vk8 S Audit Log Query for log.

        Request to get Virtual K8s audit logs that matches the criteria in...
        """
        path = "/api/data/namespaces/{namespace}/vk8s_audit_logs"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "vk8_s_audit_log_query", e, response) from e

    def vk8_s_audit_log_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AggregationResponse:
        """Vk8 S Audit Log Aggregation Query for log.

        Request to get summary/analytics data for the vK8s audit logs that...
        """
        path = "/api/data/namespaces/{namespace}/vk8s_audit_logs/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "vk8_s_audit_log_aggregation_query", e, response) from e

    def vk8_s_audit_log_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> Response:
        """Vk8 S Audit Log Scroll Query for log.

        The response for vK8s audit log query contain no more than 500...
        """
        path = "/api/data/namespaces/{namespace}/vk8s_audit_logs/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "vk8_s_audit_log_scroll_query", e, response) from e

    def custom_vk8_s_audit_log_scroll_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Custom Vk8 S Audit Log Scroll Query for log.

        The response for vK8s audit log query contain no more than 500...
        """
        path = "/api/data/namespaces/{namespace}/vk8s_audit_logs/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "custom_vk8_s_audit_log_scroll_query", e, response) from e

    def vk8_s_events_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Vk8 S Events Query for log.

        Request to get Virtual K8s events that matches the criteria in...
        """
        path = "/api/data/namespaces/{namespace}/vk8s_events"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "vk8_s_events_query", e, response) from e

    def vk8_s_events_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AggregationResponse:
        """Vk8 S Events Aggregation Query for log.

        Request to get summary/analytics data for the vK8s events that...
        """
        path = "/api/data/namespaces/{namespace}/vk8s_events/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "vk8_s_events_aggregation_query", e, response) from e

    def vk8_s_events_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> Response:
        """Vk8 S Events Scroll Query for log.

        The response for vK8s events query contain no more than 500 events....
        """
        path = "/api/data/namespaces/{namespace}/vk8s_events/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "vk8_s_events_scroll_query", e, response) from e

    def custom_vk8_s_events_scroll_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Custom Vk8 S Events Scroll Query for log.

        The response for vK8s events query contain no more than 500 events....
        """
        path = "/api/data/namespaces/{namespace}/vk8s_events/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("log", "custom_vk8_s_events_scroll_query", e, response) from e

