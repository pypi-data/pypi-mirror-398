"""Pydantic models for synthetic_monitor."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class CertItem(F5XCBaseModel):
    """HTTP Monitor Certificate object"""

    certificate_expiry_time: Optional[str] = None
    monitor_name: Optional[str] = None


class CertificateReportDetailResponseEntry(F5XCBaseModel):
    """Entry in certificate report detail response"""

    cert_common_name: Optional[str] = None
    cert_issuer: Optional[str] = None
    certificate_expiry_time: Optional[str] = None
    monitor_labels: Optional[str] = None
    monitor_name: Optional[str] = None
    region: Optional[str] = None
    region_provider: Optional[str] = None


class DNSMonitorEventDetail(F5XCBaseModel):
    answer: Optional[str] = None
    compress: Optional[str] = None
    dns_lookup_ms: Optional[str] = None
    msg_hdr_authenticated_data: Optional[str] = None
    msg_hdr_authoritative: Optional[str] = None
    msg_hdr_checking_disabled: Optional[str] = None
    msg_hdr_id: Optional[str] = None
    msg_hdr_opcode: Optional[str] = None
    msg_hdr_rcode: Optional[str] = None
    msg_hdr_recursion_available: Optional[str] = None
    msg_hdr_response: Optional[str] = None
    msg_hdr_truncated: Optional[str] = None
    msg_hdr_zero: Optional[str] = None
    question: Optional[str] = None
    region: Optional[str] = None
    status_code: Optional[str] = None
    trailer: Optional[str] = None


class GetCertSummaryResponse(F5XCBaseModel):
    """Response of HTTP monitor certificate summary"""

    items: Optional[list[CertItem]] = None


class GetCertificateReportDetailResponse(F5XCBaseModel):
    """Response of certificate report detail"""

    entries: Optional[list[CertificateReportDetailResponseEntry]] = None


class GetDNSMonitorHealthRequest(F5XCBaseModel):
    """Request of DNS Monitor Health"""

    include_latency: Optional[bool] = None
    monitor_names: Optional[list[str]] = None
    namespace: Optional[str] = None


class SourceHealthItem(F5XCBaseModel):
    """Health status by region"""

    health: Optional[str] = None
    latency: Optional[str] = None
    provider: Optional[str] = None
    source: Optional[str] = None


class GetDNSMonitorHealthResponse(F5XCBaseModel):
    """Health status by region for specified monitor"""

    health: Optional[str] = None
    monitor_name: Optional[str] = None
    sources: Optional[list[SourceHealthItem]] = None


class GetDNSMonitorHealthResponseList(F5XCBaseModel):
    """List of health statuses by region for specified monitors"""

    items: Optional[list[GetDNSMonitorHealthResponse]] = None


class GetDNSMonitorSummaryResponse(F5XCBaseModel):
    """DNS monitor summary of latency and trend data"""

    avg_latency: Optional[str] = None
    health: Optional[str] = None
    last_critical_event_timestamp: Optional[str] = None
    latency: Optional[str] = None
    max_latency: Optional[str] = None
    trend: Optional[str] = None


class HistoryItem(F5XCBaseModel):
    """Object of timestamp and critical monitor count"""

    critical_monitors: Optional[int] = None
    timestamp: Optional[float] = None


class GetGlobalHistoryResponse(F5XCBaseModel):
    """Response for global history"""

    items: Optional[list[HistoryItem]] = None


class GetGlobalSummaryResponse(F5XCBaseModel):
    """Response of getting global monitor summary"""

    critical_monitor_count: Optional[int] = None
    healthy_monitor_count: Optional[int] = None
    number_of_monitors: Optional[int] = None


class RegionLatencyItem(F5XCBaseModel):
    """Latency, trend, and health data by region"""

    avg_latency: Optional[str] = None
    health: Optional[str] = None
    latency: Optional[str] = None
    max_latency: Optional[str] = None
    provider: Optional[str] = None
    region: Optional[str] = None
    trend: Optional[str] = None


class GetHTTPMonitorDetailResponse(F5XCBaseModel):
    """Monitor latency, trend, and health data by region"""

    items: Optional[list[RegionLatencyItem]] = None


class GetHTTPMonitorHealthRequest(F5XCBaseModel):
    """Request of HTTP Monitor Health"""

    include_latency: Optional[bool] = None
    monitor_names: Optional[list[str]] = None
    namespace: Optional[str] = None


class GetHTTPMonitorHealthResponse(F5XCBaseModel):
    """Health status by region for specified monitor"""

    health: Optional[str] = None
    monitor_name: Optional[str] = None
    sources: Optional[list[SourceHealthItem]] = None


class GetHTTPMonitorHealthResponseList(F5XCBaseModel):
    """List of health statuses by region for specified monitors"""

    items: Optional[list[GetHTTPMonitorHealthResponse]] = None


class GetHTTPMonitorSummaryResponse(F5XCBaseModel):
    """HTTP monitor summary of latency, trend, and TLS data"""

    avg_latency: Optional[str] = None
    cert_expiry_date: Optional[str] = None
    health: Optional[str] = None
    last_critical_event_timestamp: Optional[str] = None
    latency: Optional[str] = None
    max_latency: Optional[str] = None
    tls_score: Optional[str] = None
    trend: Optional[str] = None


class TagValuesItem(F5XCBaseModel):
    """Metric query metric tag values object"""

    key: Optional[str] = None
    values: Optional[list[str]] = None


class MetricItem(F5XCBaseModel):
    """Metric query metric object"""

    field: Optional[str] = None
    function: Optional[Literal['MEAN', 'MIN', 'MAX', 'SUM', 'DIFFERENCE']] = None
    measurement: Optional[str] = None
    tags: Optional[list[TagValuesItem]] = None


class GetMetricQueryDataRequest(F5XCBaseModel):
    """Request of metric query metric data"""

    end_time: Optional[str] = None
    metrics: Optional[list[MetricItem]] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None
    step_size: Optional[str] = None


class RawData(F5XCBaseModel):
    """Raw Data object"""

    timestamp: Optional[float] = None
    value: Optional[float] = None


class MetricQueryData(F5XCBaseModel):
    """Metric Query Data object"""

    message: Optional[str] = None
    raw: Optional[list[RawData]] = None


class GetMetricQueryDataResponse(F5XCBaseModel):
    """Metric query metric data"""

    data: Optional[list[MetricQueryData]] = None


class HTTPMonitorEventDetail(F5XCBaseModel):
    body: Optional[str] = None
    content_length: Optional[str] = None
    content_transfer_ms: Optional[str] = None
    dns_lookup_ms: Optional[str] = None
    header: Optional[str] = None
    proto: Optional[str] = None
    region: Optional[str] = None
    server_processing_ms: Optional[str] = None
    status_code: Optional[str] = None
    tcp_connection_ms: Optional[str] = None
    tls_cipher_suite: Optional[str] = None
    tls_did_resume: Optional[str] = None
    tls_handshake_complete: Optional[str] = None
    tls_handshake_ms: Optional[str] = None
    tls_negotiated_protocol: Optional[str] = None
    tls_server_name: Optional[str] = None
    tls_version: Optional[str] = None
    trailer: Optional[str] = None
    transfer_encoding: Optional[str] = None
    uncompressed: Optional[str] = None


class MonitorEvents(F5XCBaseModel):
    dns_detail: Optional[DNSMonitorEventDetail] = None
    event: Optional[str] = None
    event_time: Optional[str] = None
    historical_health: Optional[str] = None
    http_detail: Optional[HTTPMonitorEventDetail] = None
    monitor_type: Optional[str] = None
    provider: Optional[str] = None
    source: Optional[str] = None


class GetMonitorEventsResponse(F5XCBaseModel):
    """Monitor health events by region"""

    events: Optional[list[MonitorEvents]] = None


class GetMonitorHistorySegment(F5XCBaseModel):
    end_time: Optional[str] = None
    health: Optional[str] = None
    health_reason: Optional[str] = None
    start_time: Optional[str] = None


class GetMonitorHistories(F5XCBaseModel):
    """Monitor health history by region"""

    provider: Optional[str] = None
    segments: Optional[list[GetMonitorHistorySegment]] = None
    source: Optional[str] = None


class GetMonitorHistoryResponse(F5XCBaseModel):
    """Health history data for monitor by region"""

    histories: Optional[list[GetMonitorHistories]] = None


class Record(F5XCBaseModel):
    """DNS monitor record type object"""

    count: Optional[int] = None
    record_type: Optional[str] = None


class GetRecordTypeSummaryResponse(F5XCBaseModel):
    """Response for the summary of DNS monitor record type"""

    items: Optional[list[Record]] = None


class MonitorRegionCoordinates(F5XCBaseModel):
    """Region coordinates"""

    latitude: Optional[float] = None
    longitude: Optional[float] = None


class MonitorsBySourceSummary(F5XCBaseModel):
    coordinates: Optional[MonitorRegionCoordinates] = None
    critical_count: Optional[int] = None
    curr_latency: Optional[str] = None
    healthy_count: Optional[int] = None
    provider: Optional[str] = None
    region: Optional[str] = None


class GetSourceSummaryResponse(F5XCBaseModel):
    """Healthy and critical counts by monintor source region"""

    monitor_by_source: Optional[list[MonitorsBySourceSummary]] = None


class GetTLSReportDetailResponse(F5XCBaseModel):
    """HTML encoding of TLS report"""

    ssl_check_html_report: Optional[str] = None


class MonitorTLSReportSummaryProtocol(F5XCBaseModel):
    """Response of Monitor TLS Report Summary"""

    detail: Optional[str] = None
    protocol: Optional[str] = None


class GetTLSReportSummaryResponse(F5XCBaseModel):
    """Grade, score, and supported protocols from TLS scan of monitor endpoint"""

    grade: Optional[str] = None
    grade_reason: Optional[str] = None
    protocols: Optional[list[MonitorTLSReportSummaryProtocol]] = None
    score: Optional[str] = None


class TLSItem(F5XCBaseModel):
    """Object containing list and percent of monitors using specified TLS protocol"""

    monitor_list: Optional[list[str]] = None
    monitor_protocol: Optional[Literal['SSLv2', 'SSLv3', 'TLS1', 'TLS1_1', 'TLS1_2', 'TLS1_3', 'NPN', 'ALPN']] = None
    percentage: Optional[int] = None


class GetTLSSummaryResponse(F5XCBaseModel):
    """TLS summary of HTTPs monitors in namespace"""

    items: Optional[list[TLSItem]] = None


class SuggestValuesRequest(F5XCBaseModel):
    """Suggested values request"""

    field_path: Optional[str] = None
    match_value: Optional[str] = None
    namespace: Optional[str] = None
    request_body: Optional[ProtobufAny] = None


class SuggestedItem(F5XCBaseModel):
    """A tuple with a suggested value and it's description."""

    description: Optional[str] = None
    value: Optional[str] = None


class SuggestValuesResponse(F5XCBaseModel):
    """Response body of SuggestValues request"""

    items: Optional[list[SuggestedItem]] = None


# Convenience aliases
