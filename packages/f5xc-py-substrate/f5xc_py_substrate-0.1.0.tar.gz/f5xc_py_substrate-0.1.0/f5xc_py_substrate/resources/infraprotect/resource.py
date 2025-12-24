"""Infraprotect resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.infraprotect.models import (
    AccessFlag,
    AddAlertToEventRequest,
    AddAlertToEventResponse,
    Attachment,
    AddEventDetailRequest,
    EventDetail,
    AddEventDetailResponse,
    Event,
    Alert,
    AlertPort,
    AlertPrefix,
    Ipv4AddressType,
    Ipv6AddressType,
    IpAddressType,
    Empty,
    DeviceLocation,
    BGPPeerStatusItem,
    BGPPeerStatusRequest,
    BGPPeerStatusResponse,
    CustomerAccessResponse,
    DeleteEventDetailResponse,
    EditEventDetailRequest,
    EditEventDetailResponse,
    EditEventRequest,
    EditEventResponse,
    EventSummary,
    GetAlertResponse,
    GetEventResponse,
    GetMitigationResponse,
    GetReportResponse,
    ListAlertsRequest,
    ListAlertsResponse,
    ListEventAlertsResponse,
    ListEventAttachmentsResponse,
    ListEventDetailsResponse,
    MitigationAnnotation,
    ListEventMitigationsResponse,
    ListEventsRequest,
    ListEventsResponse,
    ListEventsSummaryResponse,
    ListMitigationAnnotationsResponse,
    MitigationIP,
    ListMitigationIPsResponse,
    ListMitigationsRequest,
    Mitigation,
    ListMitigationsResponse,
    PrefixListType,
    Network,
    ListNetworksResponse,
    ListReportsRequest,
    Report,
    ListReportsResponse,
    ProtobufAny,
    SuggestValuesReq,
    TrendValue,
    MetricValue,
    TransitUsageTypeData,
    TransitUsageData,
    TransitUsageRequest,
    TransitUsageResponse,
    ObjectRefType,
    SuggestedItem,
    SuggestValuesResp,
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


class InfraprotectResource:
    """API methods for infraprotect.

    APIs to get monitoring data for infraprotect.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.infraprotect.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def customer_access(
        self,
    ) -> CustomerAccessResponse:
        """Customer Access for infraprotect.

        RPC to get customer access and availability info.
        """
        path = "/api/infraprotect/namespaces/system/infraprotect/access"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CustomerAccessResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "customer_access", e, response) from e

    def get_alert(
        self,
        namespace: str,
        alert_id: str,
    ) -> GetAlertResponse:
        """Get Alert for infraprotect.

        RPC to get details of an alert.
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/alert/{alert_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{alert_id}", alert_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetAlertResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "get_alert", e, response) from e

    def add_alert_to_event(
        self,
        namespace: str,
        alert_id: str,
        body: dict[str, Any] | None = None,
    ) -> AddAlertToEventResponse:
        """Add Alert To Event for infraprotect.

        Allows customers to link alerts with events. This helps with...
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/alert/{alert_id}/to_event"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{alert_id}", alert_id)


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AddAlertToEventResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "add_alert_to_event", e, response) from e

    def list_alerts(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListAlertsResponse:
        """List Alerts for infraprotect.

        RPC to get a list of Alerts. Alerts are raised when an attack is...
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/alerts"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListAlertsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_alerts", e, response) from e

    def bgp_peer_status(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> BGPPeerStatusResponse:
        """Bgp Peer Status for infraprotect.

        API to get routed DDoS BGP peer status information.
        """
        path = "/api/data/namespaces/{namespace}/infraprotect/bgp_peer_status"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return BGPPeerStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "bgp_peer_status", e, response) from e

    def get_event(
        self,
        namespace: str,
        event_id: str,
    ) -> GetEventResponse:
        """Get Event for infraprotect.

        Returns details of an event. This allows customers to review any...
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/event/{event_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{event_id}", event_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetEventResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "get_event", e, response) from e

    def edit_event(
        self,
        namespace: str,
        event_id: str,
        body: dict[str, Any] | None = None,
    ) -> EditEventResponse:
        """Edit Event for infraprotect.

        Allows editing of an event, setting its end date and upload any...
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/event/{event_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{event_id}", event_id)


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EditEventResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "edit_event", e, response) from e

    def list_event_alerts(
        self,
        namespace: str,
        event_id: str,
    ) -> ListEventAlertsResponse:
        """List Event Alerts for infraprotect.

        Returns a list of alerts triggers while an event is active.
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/event/{event_id}/alerts"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{event_id}", event_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListEventAlertsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_event_alerts", e, response) from e

    def list_event_attachments(
        self,
        namespace: str,
        event_id: str,
    ) -> ListEventAttachmentsResponse:
        """List Event Attachments for infraprotect.

        Returns any attachments associated with an event. This could be Pcap...
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/event/{event_id}/attachments"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{event_id}", event_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListEventAttachmentsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_event_attachments", e, response) from e

    def edit_event_detail(
        self,
        namespace: str,
        event_id: str,
        event_detail_id: str,
        body: dict[str, Any] | None = None,
    ) -> EditEventDetailResponse:
        """Edit Event Detail for infraprotect.

        Allows editing of an event detail, setting its title, description and date
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/event/{event_id}/detail/{event_detail_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{event_id}", event_id)
        path = path.replace("{event_detail_id}", event_detail_id)


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EditEventDetailResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "edit_event_detail", e, response) from e

    def delete_event_detail(
        self,
        namespace: str,
        event_id: str,
        event_detail_id: str,
    ) -> DeleteEventDetailResponse:
        """Delete Event Detail for infraprotect.

        Delete a single event detail, including all dependant objects (e.g....
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/event/{event_id}/detail/{event_detail_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{event_id}", event_id)
        path = path.replace("{event_detail_id}", event_detail_id)


        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeleteEventDetailResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "delete_event_detail", e, response) from e

    def list_event_details(
        self,
        namespace: str,
        event_id: str,
    ) -> ListEventDetailsResponse:
        """List Event Details for infraprotect.

        Returns a list of event details. The list contains event details...
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/event/{event_id}/details"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{event_id}", event_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListEventDetailsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_event_details", e, response) from e

    def add_event_detail(
        self,
        namespace: str,
        event_id: str,
        body: dict[str, Any] | None = None,
    ) -> AddEventDetailResponse:
        """Add Event Detail for infraprotect.

        Adds a single event detail to an event.
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/event/{event_id}/details"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{event_id}", event_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AddEventDetailResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "add_event_detail", e, response) from e

    def list_event_mitigations(
        self,
        namespace: str,
        event_id: str,
    ) -> ListEventMitigationsResponse:
        """List Event Mitigations for infraprotect.

        Return mitigation annotations that occur while an event is active
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/event/{event_id}/mitigation_annotations"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{event_id}", event_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListEventMitigationsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_event_mitigations", e, response) from e

    def list_events(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListEventsResponse:
        """List Events for infraprotect.

        Returns a list of events. Events are created when a high priority...
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/events"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListEventsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_events", e, response) from e

    def list_events_summary(
        self,
        namespace: str,
        alert_id: str | None = None,
    ) -> ListEventsSummaryResponse:
        """List Events Summary for infraprotect.

        Return a list of available event (suitable for an alert)
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/events_summary"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if alert_id is not None:
            params["alert_id"] = alert_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListEventsSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_events_summary", e, response) from e

    def get_mitigation(
        self,
        namespace: str,
        mitigation_id: str,
    ) -> GetMitigationResponse:
        """Get Mitigation for infraprotect.

        Returns details of a single mitigation
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/mitigation/{mitigation_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{mitigation_id}", mitigation_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetMitigationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "get_mitigation", e, response) from e

    def list_mitigation_annotations(
        self,
        namespace: str,
        mitigation_id: str,
    ) -> ListMitigationAnnotationsResponse:
        """List Mitigation Annotations for infraprotect.

        Returns annotations of a single mitigation
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/mitigation/{mitigation_id}/annotations"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{mitigation_id}", mitigation_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListMitigationAnnotationsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_mitigation_annotations", e, response) from e

    def list_mitigation_i_ps(
        self,
        namespace: str,
        mitigation_id: str,
    ) -> ListMitigationIPsResponse:
        """List Mitigation I Ps for infraprotect.

        Returns list of IPs involved in a mitigation (and allows for...
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/mitigation/{mitigation_id}/ips"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{mitigation_id}", mitigation_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListMitigationIPsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_mitigation_i_ps", e, response) from e

    def list_mitigations(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListMitigationsResponse:
        """List Mitigations for infraprotect.

        Returns a list of mitigations
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/mitigations"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListMitigationsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_mitigations", e, response) from e

    def list_networks(
        self,
        namespace: str,
    ) -> ListNetworksResponse:
        """List Networks for infraprotect.

        Returns a list available reports to be downloaded. Reports summarise...
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/networks"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListNetworksResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_networks", e, response) from e

    def get_report(
        self,
        namespace: str,
        report_id: str,
    ) -> GetReportResponse:
        """Get Report for infraprotect.

        Returns details of a report, most importantly the PDF document itself.
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/report/{report_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{report_id}", report_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetReportResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "get_report", e, response) from e

    def list_reports(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListReportsResponse:
        """List Reports for infraprotect.

        Returns a list of available reports to be downloaded. Reports...
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect/reports"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListReportsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "list_reports", e, response) from e

    def transit_usage(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TransitUsageResponse:
        """Transit Usage for infraprotect.

        API to get transit usage data.
        """
        path = "/api/data/namespaces/{namespace}/infraprotect/transit_usage"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TransitUsageResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "transit_usage", e, response) from e

    def suggest_values(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SuggestValuesResp:
        """Suggest Values for infraprotect.

        SuggestValues returns suggested values for the specified field in...
        """
        path = "/api/infraprotect/namespaces/{namespace}/suggest-values"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuggestValuesResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect", "suggest_values", e, response) from e

