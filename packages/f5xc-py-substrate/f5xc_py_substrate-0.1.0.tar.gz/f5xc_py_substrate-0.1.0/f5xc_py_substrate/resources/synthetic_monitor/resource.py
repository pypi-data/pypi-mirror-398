"""SyntheticMonitor resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.synthetic_monitor.models import (
    ProtobufAny,
    Empty,
    CertItem,
    CertificateReportDetailResponseEntry,
    DNSMonitorEventDetail,
    GetCertSummaryResponse,
    GetCertificateReportDetailResponse,
    GetDNSMonitorHealthRequest,
    SourceHealthItem,
    GetDNSMonitorHealthResponse,
    GetDNSMonitorHealthResponseList,
    GetDNSMonitorSummaryResponse,
    HistoryItem,
    GetGlobalHistoryResponse,
    GetGlobalSummaryResponse,
    RegionLatencyItem,
    GetHTTPMonitorDetailResponse,
    GetHTTPMonitorHealthRequest,
    GetHTTPMonitorHealthResponse,
    GetHTTPMonitorHealthResponseList,
    GetHTTPMonitorSummaryResponse,
    TagValuesItem,
    MetricItem,
    GetMetricQueryDataRequest,
    RawData,
    MetricQueryData,
    GetMetricQueryDataResponse,
    HTTPMonitorEventDetail,
    MonitorEvents,
    GetMonitorEventsResponse,
    GetMonitorHistorySegment,
    GetMonitorHistories,
    GetMonitorHistoryResponse,
    Record,
    GetRecordTypeSummaryResponse,
    MonitorRegionCoordinates,
    MonitorsBySourceSummary,
    GetSourceSummaryResponse,
    GetTLSReportDetailResponse,
    MonitorTLSReportSummaryProtocol,
    GetTLSReportSummaryResponse,
    TLSItem,
    GetTLSSummaryResponse,
    SuggestValuesRequest,
    SuggestedItem,
    SuggestValuesResponse,
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


class SyntheticMonitorResource:
    """API methods for synthetic_monitor.

    Custom handler for DNS Monitor and HTTP Monitor
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.synthetic_monitor.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_certificate_report_detail(
        self,
        namespace: str,
    ) -> GetCertificateReportDetailResponse:
        """Get Certificate Report Detail for synthetic_monitor.

        Returns the certificate report detail
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/certificate-report-detail"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetCertificateReportDetailResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_certificate_report_detail", e, response) from e

    def get_cert_summary(
        self,
        namespace: str,
        period_in_days: int | None = None,
    ) -> GetCertSummaryResponse:
        """Get Cert Summary for synthetic_monitor.

        Returns list of TLS certificate expirations in specified time window...
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/certificate-summary"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if period_in_days is not None:
            params["period_in_days"] = period_in_days

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetCertSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_cert_summary", e, response) from e

    def get_dns_monitor_summary(
        self,
        namespace: str,
        start_time: str | None = None,
        end_time: str | None = None,
        monitor_name: str | None = None,
    ) -> GetDNSMonitorSummaryResponse:
        """Get Dns Monitor Summary for synthetic_monitor.

        Returns the DNS monitor health status, latency, and trend
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/dns-monitor-summary"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time
        if monitor_name is not None:
            params["monitor_name"] = monitor_name

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDNSMonitorSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_dns_monitor_summary", e, response) from e

    def get_dns_monitor_health(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetDNSMonitorHealthResponseList:
        """Get Dns Monitor Health for synthetic_monitor.

        Returns list of DNS monitors in namespace with corresponding region health(s)
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/dns-monitors-health"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDNSMonitorHealthResponseList(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_dns_monitor_health", e, response) from e

    def get_global_history(
        self,
        namespace: str,
        monitor_type: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        step_size: str | None = None,
    ) -> GetGlobalHistoryResponse:
        """Get Global History for synthetic_monitor.

        Returns a time series of critical monitor counts in namespace
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/global-history"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if monitor_type is not None:
            params["monitor_type"] = monitor_type
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time
        if step_size is not None:
            params["step_size"] = step_size

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetGlobalHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_global_history", e, response) from e

    def get_global_summary(
        self,
        namespace: str,
        monitor_type: str | None = None,
    ) -> GetGlobalSummaryResponse:
        """Get Global Summary for synthetic_monitor.

        Returns a healthy and critical count of all monitors in namespace,...
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/global-summary"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if monitor_type is not None:
            params["monitor_type"] = monitor_type

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetGlobalSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_global_summary", e, response) from e

    def get_health(
        self,
        namespace: str,
    ) -> Empty:
        """Get Health for synthetic_monitor.

        returns 200 Ok if the service is healthy
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/health"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_health", e, response) from e

    def get_http_monitor_detail(
        self,
        namespace: str,
        monitor_name: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> GetHTTPMonitorDetailResponse:
        """Get Http Monitor Detail for synthetic_monitor.

        Returns the monitor latency, trend, and health by region
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/http-monitor-detail"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if monitor_name is not None:
            params["monitor_name"] = monitor_name
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetHTTPMonitorDetailResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_http_monitor_detail", e, response) from e

    def get_http_monitor_summary(
        self,
        namespace: str,
        start_time: str | None = None,
        end_time: str | None = None,
        monitor_name: str | None = None,
    ) -> GetHTTPMonitorSummaryResponse:
        """Get Http Monitor Summary for synthetic_monitor.

        Returns the HTTP monitor health status, latency, and trend
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/http-monitor-summary"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time
        if monitor_name is not None:
            params["monitor_name"] = monitor_name

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetHTTPMonitorSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_http_monitor_summary", e, response) from e

    def get_http_monitor_health(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetHTTPMonitorHealthResponseList:
        """Get Http Monitor Health for synthetic_monitor.

        Returns list of HTTP monitors in namespace with corresponding region...
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/http-monitors-health"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetHTTPMonitorHealthResponseList(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_http_monitor_health", e, response) from e

    def get_metric_query_data(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetMetricQueryDataResponse:
        """Get Metric Query Data for synthetic_monitor.

        Returns time series data of monitor metric query by region
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/metric-query"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetMetricQueryDataResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_metric_query_data", e, response) from e

    def get_monitor_events(
        self,
        namespace: str,
        monitor_type: str | None = None,
        monitor_name: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> GetMonitorEventsResponse:
        """Get Monitor Events for synthetic_monitor.

        Returns the healthy and critical events for the specified monitor
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/monitor-events"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if monitor_type is not None:
            params["monitor_type"] = monitor_type
        if monitor_name is not None:
            params["monitor_name"] = monitor_name
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetMonitorEventsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_monitor_events", e, response) from e

    def get_monitor_history(
        self,
        namespace: str,
        monitor_type: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        step_size: str | None = None,
        monitor_name: str | None = None,
    ) -> GetMonitorHistoryResponse:
        """Get Monitor History for synthetic_monitor.

        Returns the healthy and critical statuses for the specified monitor
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/monitor-history"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if monitor_type is not None:
            params["monitor_type"] = monitor_type
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time
        if step_size is not None:
            params["step_size"] = step_size
        if monitor_name is not None:
            params["monitor_name"] = monitor_name

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetMonitorHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_monitor_history", e, response) from e

    def get_record_type_summary(
        self,
        namespace: str,
    ) -> GetRecordTypeSummaryResponse:
        """Get Record Type Summary for synthetic_monitor.

        Returns record type summary for DNS monitor including record type and count
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/record-type-summary"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetRecordTypeSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_record_type_summary", e, response) from e

    def get_source_summary(
        self,
        namespace: str,
        monitor_type: str | None = None,
        label_filter: str | None = None,
        monitor_name: str | None = None,
    ) -> GetSourceSummaryResponse:
        """Get Source Summary for synthetic_monitor.

        Returns the healthy and critical status count, latency, and...
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/source-summary"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if monitor_type is not None:
            params["monitor_type"] = monitor_type
        if label_filter is not None:
            params["label_filter"] = label_filter
        if monitor_name is not None:
            params["monitor_name"] = monitor_name

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSourceSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_source_summary", e, response) from e

    def suggest_values(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SuggestValuesResponse:
        """Suggest Values for synthetic_monitor.

        Returns suggested values for the specified field in the given...
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/suggest-values"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuggestValuesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "suggest_values", e, response) from e

    def get_tls_report_detail(
        self,
        namespace: str,
        monitor_name: str | None = None,
    ) -> GetTLSReportDetailResponse:
        """Get Tls Report Detail for synthetic_monitor.

        Returns the HTML encoding of the generated TLS report
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/tls-report-detail"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if monitor_name is not None:
            params["monitor_name"] = monitor_name

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTLSReportDetailResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_tls_report_detail", e, response) from e

    def get_tls_report_summary(
        self,
        namespace: str,
        monitor_name: str | None = None,
    ) -> GetTLSReportSummaryResponse:
        """Get Tls Report Summary for synthetic_monitor.

        Returns the TLS report summary including grade, score, and protocol names
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/tls-report-summary"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if monitor_name is not None:
            params["monitor_name"] = monitor_name

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTLSReportSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_tls_report_summary", e, response) from e

    def get_tls_summary(
        self,
        namespace: str,
    ) -> GetTLSSummaryResponse:
        """Get Tls Summary for synthetic_monitor.

        Returns TLS summary of all HTTPs monitors running in namespace
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/tls-summary"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTLSSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("synthetic_monitor", "get_tls_summary", e, response) from e

