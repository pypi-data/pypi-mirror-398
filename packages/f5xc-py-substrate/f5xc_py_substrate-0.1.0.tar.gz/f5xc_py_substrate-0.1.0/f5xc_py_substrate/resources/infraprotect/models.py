"""Pydantic models for infraprotect."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AccessFlag(F5XCBaseModel):
    """Single access flag instance"""

    data_expected_ts: Optional[str] = None
    data_present: Optional[bool] = None
    enabled: Optional[bool] = None


class AddAlertToEventRequest(F5XCBaseModel):
    """Request to add an alert to event (link them together)"""

    alert_id: Optional[str] = None
    event_id: Optional[str] = None
    namespace: Optional[str] = None


class AddAlertToEventResponse(F5XCBaseModel):
    """Response to adding an alert to event"""

    pass


class Attachment(F5XCBaseModel):
    """Event attachment record (pcap, or any arbitrary file)"""

    attachment_id: Optional[str] = None
    attachment_type: Optional[Literal['ATTACHMENT_TYPE_UNKNOWN', 'ATTACHMENT_TYPE_PCAP', 'ATTACHMENT_TYPE_BINARY', 'ATTACHMENT_TYPE_INVALID_PCAP', 'ATTACHMENT_TYPE_OTHER']] = None
    end_time: Optional[str] = None
    gos_name: Optional[str] = None
    gos_version: Optional[str] = None
    name: Optional[str] = None
    size_bytes: Optional[str] = None
    start_time: Optional[str] = None


class AddEventDetailRequest(F5XCBaseModel):
    """Request to add a single event detail to an event"""

    attachments: Optional[list[Attachment]] = None
    description: Optional[str] = None
    event_id: Optional[str] = None
    namespace: Optional[str] = None
    time: Optional[str] = None
    title: Optional[str] = None


class EventDetail(F5XCBaseModel):
    """Event detail represents a single occurrence of event detail, that tracks..."""

    attachments: Optional[list[Attachment]] = None
    creator: Optional[str] = None
    description: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    time: Optional[str] = None
    title: Optional[str] = None


class AddEventDetailResponse(F5XCBaseModel):
    """Event detail as stored in the backend"""

    detail: Optional[EventDetail] = None


class Event(F5XCBaseModel):
    """Event (an attack record) that holds info an attack and its mitigation(s)"""

    attachments: Optional[list[Attachment]] = None
    creator: Optional[str] = None
    description: Optional[str] = None
    end_time: Optional[str] = None
    has_attachment: Optional[bool] = None
    has_details: Optional[bool] = None
    id_: Optional[str] = Field(default=None, alias="id")
    ip: Optional[str] = None
    mitigation_id: Optional[str] = None
    name: Optional[str] = None
    network_id: Optional[str] = None
    start_time: Optional[str] = None


class Alert(F5XCBaseModel):
    """Detail of an alert."""

    arbor_id: Optional[str] = None
    bandwidth: Optional[str] = None
    creator: Optional[str] = None
    end_time: Optional[str] = None
    events: Optional[list[Event]] = None
    id_: Optional[str] = Field(default=None, alias="id")
    ip: Optional[str] = None
    network_id: Optional[str] = None
    source_type: Optional[Literal['ALERT_SOURCE_TYPE_UNKNOWN', 'ALERT_SOURCE_TYPE_MITIGATED', 'ALERT_SOURCE_TYPE_AUTOMITIGATED']] = None
    start_time: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class AlertPort(F5XCBaseModel):
    """Single occurrence of a port in an alert"""

    bytes: Optional[str] = None
    destination: Optional[bool] = None
    name: Optional[str] = None
    number: Optional[int] = None
    packets: Optional[str] = None
    protocol: Optional[str] = None


class AlertPrefix(F5XCBaseModel):
    """Single occurrence of a prefix in an alert"""

    cidr: Optional[str] = None
    destination: Optional[bool] = None
    num_bytes: Optional[str] = None
    num_packets: Optional[str] = None


class Ipv4AddressType(F5XCBaseModel):
    """IPv4 Address in dot-decimal notation"""

    addr: Optional[str] = None


class Ipv6AddressType(F5XCBaseModel):
    """IPv6 Address specified as hexadecimal numbers separated by ':'"""

    addr: Optional[str] = None


class IpAddressType(F5XCBaseModel):
    """IP Address used to specify an IPv4 or IPv6 address"""

    ipv4: Optional[Ipv4AddressType] = None
    ipv6: Optional[Ipv6AddressType] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class DeviceLocation(F5XCBaseModel):
    """Location of a network device (aka router) where DDoS transit tunnels are..."""

    name: Optional[str] = None
    zone1: Optional[Any] = None
    zone2: Optional[Any] = None


class BGPPeerStatusItem(F5XCBaseModel):
    """Routed DDoS BGP peer status data specific to a given router/peer combination"""

    asn: Optional[int] = None
    bgp_peer_address: Optional[IpAddressType] = None
    device_location: Optional[DeviceLocation] = None
    last_established: Optional[str] = None
    session_state: Optional[Literal['Idle', 'Connect', 'Active', 'OpenSent', 'OpenConfirm', 'Established']] = None


class BGPPeerStatusRequest(F5XCBaseModel):
    """Request to get routed DDoS BGP peer status information"""

    namespace: Optional[str] = None
    time: Optional[str] = None


class BGPPeerStatusResponse(F5XCBaseModel):
    """Routed DDoS BGP peer status response data"""

    items: Optional[list[BGPPeerStatusItem]] = None


class CustomerAccessResponse(F5XCBaseModel):
    """Infraprotect and L3/L4 ddos accessibility and availability flags response."""

    l3l4: Optional[AccessFlag] = None


class DeleteEventDetailResponse(F5XCBaseModel):
    """Event detail deletion response message."""

    pass


class EditEventDetailRequest(F5XCBaseModel):
    """Request to update a single event detail"""

    attachments: Optional[list[Attachment]] = None
    description: Optional[str] = None
    event_detail_id: Optional[str] = None
    event_id: Optional[str] = None
    namespace: Optional[str] = None
    time: Optional[str] = None
    title: Optional[str] = None


class EditEventDetailResponse(F5XCBaseModel):
    """Event detail as stored in the backend"""

    detail: Optional[EventDetail] = None


class EditEventRequest(F5XCBaseModel):
    """Request to get a single event"""

    description: Optional[str] = None
    end_time: Optional[str] = None
    event_attachments: Optional[list[Attachment]] = None
    event_id: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class EditEventResponse(F5XCBaseModel):
    """Updated event as a response to an event editing"""

    event: Optional[Event] = None


class EventSummary(F5XCBaseModel):
    """Simplified view of an event"""

    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None


class GetAlertResponse(F5XCBaseModel):
    """Response to the single alert request"""

    ports: Optional[list[AlertPort]] = None
    prefixes: Optional[list[AlertPrefix]] = None


class GetEventResponse(F5XCBaseModel):
    """Response to get a single event"""

    event: Optional[Event] = None


class GetMitigationResponse(F5XCBaseModel):
    """Details of a mitigation"""

    details: Optional[str] = None
    prefixes: Optional[list[str]] = None


class GetReportResponse(F5XCBaseModel):
    """Single report document content"""

    attachment: Optional[Attachment] = None


class ListAlertsRequest(F5XCBaseModel):
    """Request to get customer alerts with optional filtering"""

    end_time: Optional[str] = None
    event_id: Optional[str] = None
    namespace: Optional[str] = None
    network_id: Optional[str] = None
    start_time: Optional[str] = None


class ListAlertsResponse(F5XCBaseModel):
    """Response to the alerts request"""

    alerts: Optional[list[Alert]] = None


class ListEventAlertsResponse(F5XCBaseModel):
    """Response, list of alerts associated with an event"""

    alerts: Optional[list[Alert]] = None


class ListEventAttachmentsResponse(F5XCBaseModel):
    """Response, list of attachments associated with an event"""

    attachments: Optional[list[Attachment]] = None


class ListEventDetailsResponse(F5XCBaseModel):
    """All details of the event"""

    details: Optional[list[EventDetail]] = None


class MitigationAnnotation(F5XCBaseModel):
    """Mitigation annotation"""

    annotation: Optional[str] = None
    creator: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    time: Optional[str] = None


class ListEventMitigationsResponse(F5XCBaseModel):
    """Response, list of mitigations associated with an event"""

    mitigations: Optional[list[MitigationAnnotation]] = None


class ListEventsRequest(F5XCBaseModel):
    """Request to get a list of events"""

    end_time: Optional[str] = None
    mitigation_id: Optional[str] = None
    namespace: Optional[str] = None
    network_id: Optional[str] = None
    start_time: Optional[str] = None


class ListEventsResponse(F5XCBaseModel):
    """Response to get a list of events"""

    events: Optional[list[Event]] = None


class ListEventsSummaryResponse(F5XCBaseModel):
    """Response to the simplified events view request"""

    events: Optional[list[EventSummary]] = None


class ListMitigationAnnotationsResponse(F5XCBaseModel):
    """List of mitigation annotations (i.e. mitigation notes sorted chronologically)"""

    annotations: Optional[list[MitigationAnnotation]] = None


class MitigationIP(F5XCBaseModel):
    """A single mitigation IP record including log record count"""

    ip: Optional[str] = None
    log_count: Optional[str] = None


class ListMitigationIPsResponse(F5XCBaseModel):
    """List of mitigation Ips"""

    ips: Optional[list[MitigationIP]] = None


class ListMitigationsRequest(F5XCBaseModel):
    """Request to get a list of mitigations"""

    end_time: Optional[str] = None
    event_id: Optional[str] = None
    namespace: Optional[str] = None
    network_id: Optional[str] = None
    start_time: Optional[str] = None


class Mitigation(F5XCBaseModel):
    """Mitigation details"""

    arbor_id: Optional[str] = None
    creator: Optional[str] = None
    end_time: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    is_ongoing: Optional[bool] = None
    name: Optional[str] = None
    network_id: Optional[str] = None
    network_name: Optional[str] = None
    offramp: Optional[str] = None
    start_time: Optional[str] = None


class ListMitigationsResponse(F5XCBaseModel):
    """Response giving a list of mitigations"""

    mitigations: Optional[list[Mitigation]] = None


class PrefixListType(F5XCBaseModel):
    """List of IP Address prefixes. Prefix must contain both prefix and..."""

    prefix: Optional[list[str]] = None


class Network(F5XCBaseModel):
    """A single customer network record."""

    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None
    prefixes: Optional[PrefixListType] = None
    primary: Optional[bool] = None


class ListNetworksResponse(F5XCBaseModel):
    """Response containing all networks available to the customer"""

    networks: Optional[list[Network]] = None


class ListReportsRequest(F5XCBaseModel):
    """Request to get a list of available reports"""

    end_time: Optional[str] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None


class Report(F5XCBaseModel):
    """A single DDoS report record."""

    created_at: Optional[str] = None
    gos_name: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None
    scheduled: Optional[bool] = None
    scheduled_name: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")
    version: Optional[str] = None


class ListReportsResponse(F5XCBaseModel):
    """List of available reports"""

    reports: Optional[list[Report]] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class SuggestValuesReq(F5XCBaseModel):
    """Request body of SuggestValues request"""

    field_path: Optional[str] = None
    match_value: Optional[str] = None
    namespace: Optional[str] = None
    request_body: Optional[ProtobufAny] = None


class TrendValue(F5XCBaseModel):
    """Trend value contains trend value, trend sentiment and trend calculation..."""

    description: Optional[str] = None
    previous_value: Optional[str] = None
    sentiment: Optional[Literal['TREND_SENTIMENT_NONE', 'TREND_SENTIMENT_POSITIVE', 'TREND_SENTIMENT_NEGATIVE']] = None
    value: Optional[str] = None


class MetricValue(F5XCBaseModel):
    """Metric data contains timestamp and the value."""

    timestamp: Optional[float] = None
    trend_value: Optional[TrendValue] = None
    value: Optional[str] = None


class TransitUsageTypeData(F5XCBaseModel):
    """Transit Usage Type Data contains key/value pair that uniquely identifies..."""

    key: Optional[dict[str, Any]] = None
    value: Optional[list[MetricValue]] = None


class TransitUsageData(F5XCBaseModel):
    """Transit Usage data contains the transit usage type and the corresponding..."""

    data: Optional[list[TransitUsageTypeData]] = None
    type_: Optional[Literal['IN_THROUGHPUT_BYTES', 'IN_THROUGHPUT_PACKETS', 'OUT_THROUGHPUT_BYTES', 'OUT_THROUGHPUT_PACKETS']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None


class TransitUsageRequest(F5XCBaseModel):
    """Request to get transit usage data"""

    end_time: Optional[str] = None
    field_selector: Optional[list[Literal['IN_THROUGHPUT_BYTES', 'IN_THROUGHPUT_PACKETS', 'OUT_THROUGHPUT_BYTES', 'OUT_THROUGHPUT_PACKETS']]] = None
    filter: Optional[str] = None
    group_by: Optional[list[Literal['POP', 'DEVICE', 'INTERFACE', 'CIRCUIT_ID']]] = None
    namespace: Optional[str] = None
    range: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class TransitUsageResponse(F5XCBaseModel):
    """Transit usage response data"""

    data: Optional[list[TransitUsageData]] = None
    step: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class SuggestedItem(F5XCBaseModel):
    """A tuple with a suggested value and it's description."""

    description: Optional[str] = None
    ref_value: Optional[ObjectRefType] = None
    str_value: Optional[str] = None
    value: Optional[str] = None


class SuggestValuesResp(F5XCBaseModel):
    """Response body of SuggestValues request"""

    items: Optional[list[SuggestedItem]] = None


# Convenience aliases
