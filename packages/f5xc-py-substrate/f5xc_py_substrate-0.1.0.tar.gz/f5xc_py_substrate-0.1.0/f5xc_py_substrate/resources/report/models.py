"""Pydantic models for report."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class AttachmentValue(F5XCBaseModel):
    """Attachment data contains contentId and the data."""

    content: Optional[str] = None
    content_id: Optional[str] = None
    content_type: Optional[str] = None
    file_name: Optional[str] = None


class TrendValue(F5XCBaseModel):
    """Trend value contains trend value, trend sentiment and trend calculation..."""

    description: Optional[str] = None
    previous_value: Optional[str] = None
    sentiment: Optional[Literal['TREND_SENTIMENT_NONE', 'TREND_SENTIMENT_POSITIVE', 'TREND_SENTIMENT_NEGATIVE']] = None
    value: Optional[str] = None


class WaapReportFieldData(F5XCBaseModel):
    """waap report field data"""

    current_value: Optional[float] = None
    current_value_header: Optional[str] = None
    current_value_sub_values: Optional[dict[str, Any]] = None
    current_value_type: Optional[Literal['TYPE_NONE', 'TYPE_RATE', 'TYPE_PERCENT', 'TYPE_THROUGHPUT', 'TYPE_NUMBER']] = None
    prev_value: Optional[float] = None
    prev_value_header: Optional[str] = None
    trend_value: Optional[TrendValue] = None


class WaapReportFieldDataList(F5XCBaseModel):
    """waap report field data list"""

    data: Optional[list[WaapReportFieldData]] = None


class AttackImpactData(F5XCBaseModel):
    """key value pair of attack impact data"""

    key: Optional[Literal['ATTACK_IMPACT_KEY_NONE', 'ATTACK_IMPACT_KEY_TOP_3_ATTACKED_PATHS', 'ATTACK_IMPACT_KEY_TOP_3_ATTACKED_DOMAINS']] = None
    value: Optional[WaapReportFieldDataList] = None


class AttackImpact(F5XCBaseModel):
    """attack impact"""

    data: Optional[list[AttackImpactData]] = None
    header: Optional[str] = None


class AttackSourcesData(F5XCBaseModel):
    """key value pair of attack sources data"""

    key: Optional[Literal['ATTACK_SOURCES_KEY_NONE', 'ATTACK_SOURCES_KEY_TOP_3_ASNS', 'ATTACK_SOURCES_KEY_TOP_3_COUNTRIES']] = None
    value: Optional[WaapReportFieldDataList] = None


class AttackSources(F5XCBaseModel):
    """attack sources"""

    data: Optional[list[AttackSourcesData]] = None
    header: Optional[str] = None


class DownloadReportResponse(F5XCBaseModel):
    """Download report response"""

    attachments: Optional[list[AttachmentValue]] = Field(default=None, alias="Attachments")
    css_data: Optional[str] = None
    html_data: Optional[str] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class DataATB(F5XCBaseModel):
    """ATB report data."""

    json_data: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class DeliveryStatus(F5XCBaseModel):
    """report generation status"""

    delivered_time: Optional[str] = None
    eta: Optional[str] = None
    report_delivery_state: Optional[Literal['REPORT_DELIVERY_STATE_NONE', 'REPORT_DELIVERY_STATE_SUCCESS', 'REPORT_DELIVERY_STATE_ERROR', 'REPORT_DELIVERY_STATE_PARTIAL', 'REPORT_DELIVERY_STATE_PENDING', 'REPORT_DELIVERY_STATE_DOWNLOAD']] = None


class GenerationStatus(F5XCBaseModel):
    """report generation status"""

    eta: Optional[str] = None
    report_status: Optional[Literal['NONE', 'SUCCESS', 'ERROR', 'PENDING', 'PAUSED', 'PARTIAL']] = None
    scheduled_time: Optional[str] = None


class ProtectedLBCount(F5XCBaseModel):
    """Protected LB Count."""

    protected_lb_count: Optional[str] = None
    total_lb_count: Optional[str] = None


class Header(F5XCBaseModel):
    """report header"""

    end_time: Optional[str] = None
    generation_time: Optional[str] = None
    namespace: Optional[str] = None
    report_frequency: Optional[Literal['REPORT_FREQUENCY_NONE', 'REPORT_FREQUENCY_DAILY', 'REPORT_FREQUENCY_WEEKLY', 'REPORT_FREQUENCY_MONTHLY']] = None
    report_sub_title: Optional[str] = None
    report_title: Optional[str] = None
    start_time: Optional[str] = None
    tenant_fqdn: Optional[str] = None


class SecurityEventsData(F5XCBaseModel):
    """Security events breakdown data"""

    key: Optional[Literal['SECURITY_EVENTS_KEY_NONE', 'SECURITY_EVENTS_KEY_TOTAL_SECURITY_EVENTS', 'SECURITY_EVENTS_KEY_WAF_SECURITY_EVENTS', 'SECURITY_EVENTS_KEY_BOT_DEFENSE_SECURITY_EVENTS', 'SECURITY_EVENTS_KEY_API_SECURITY_EVENTS', 'SECURITY_EVENTS_KEY_SERVICE_POLICY_SECURITY_EVENTS', 'SECURITY_EVENTS_KEY_WAF_SECURITY_EVENTS_ALLOWED', 'SECURITY_EVENTS_KEY_WAF_SECURITY_EVENTS_BLOCKED', 'SECURITY_EVENTS_KEY_BOT_DEFENSE_SECURITY_EVENTS_ALLOWED', 'SECURITY_EVENTS_KEY_BOT_DEFENSE_SECURITY_EVENTS_BLOCKED', 'SECURITY_EVENTS_KEY_API_SECURITY_EVENTS_ALLOWED', 'SECURITY_EVENTS_KEY_API_SECURITY_EVENTS_BLOCKED', 'SECURITY_EVENTS_KEY_SERVICE_POLICY_SECURITY_EVENTS_ALLOWED', 'SECURITY_EVENTS_KEY_SERVICE_POLICY_SECURITY_EVENTS_BLOCKED']] = None
    value: Optional[WaapReportFieldData] = None


class SecurityEvents(F5XCBaseModel):
    """Security events Breakdown"""

    data: Optional[list[SecurityEventsData]] = None
    header: Optional[str] = None


class ThreatDetailsData(F5XCBaseModel):
    """key value pair threat details data"""

    key: Optional[Literal['THREAT_DETAILS_KEY_NONE', 'THREAT_DETAILS_KEY_ALL_TRAFFIC_IS_FROM_BOTS', 'THREAT_DETAILS_KEY_ALL_TRAFFIC_FROM_MALICIOUS_BOTS', 'THREAT_DETAILS_KEY_THREAT_CAMPAIGNS', 'THREAT_DETAILS_KEY_IP_REPUTATION_ATTACK_MITIGATED', 'THREAT_DETAILS_KEY_LB_DDOS_ATTACK_ACTIVITY', 'THREAT_DETAILS_KEY_MALICIOUS_USERS_DETECTED', 'THREAT_DETAILS_KEY_API_ENDPOINTS', 'THREAT_DETAILS_KEY_API_ENDPOINTS_PII_DETECTED', 'THREAT_DETAILS_KEY_API_ENDPOINTS_PII_NOT_DETECTED', 'THREAT_DETAILS_KEY_THREAT_CAMPAIGNS_ALLOWED', 'THREAT_DETAILS_KEY_THREAT_CAMPAIGNS_BLOCKED', 'THREAT_DETAILS_KEY_IP_REPUTATION_ALLOWED', 'THREAT_DETAILS_KEY_IP_REPUTATION_BLOCKED']] = None
    value: Optional[WaapReportFieldData] = None


class ThreatDetails(F5XCBaseModel):
    """Threat details"""

    data: Optional[list[ThreatDetailsData]] = None
    header: Optional[str] = None


class DataWAAP(F5XCBaseModel):
    """WAAP report data."""

    attack_impact: Optional[AttackImpact] = None
    attack_sources: Optional[AttackSources] = None
    lb_count: Optional[ProtectedLBCount] = None
    report_footer: Optional[Any] = None
    report_header: Optional[Header] = None
    security_events: Optional[SecurityEvents] = None
    threat_details: Optional[ThreatDetails] = None


class GetSpecType(F5XCBaseModel):
    """Get Report will read the report metadata."""

    atb: Optional[DataATB] = None
    report_config: Optional[ObjectRefType] = None
    report_creator_method: Optional[Literal['REPORT_CREATE_METHOD_NONE', 'REPORT_CREATE_METHOD_PERIODIC', 'REPORT_CREATE_METHOD_USER_TRIGGERED']] = None
    report_delivery_status: Optional[DeliveryStatus] = None
    report_frequency: Optional[str] = None
    report_generation_status: Optional[GenerationStatus] = None
    report_id: Optional[str] = None
    report_status: Optional[Literal['NONE', 'SUCCESS', 'ERROR', 'PENDING', 'PAUSED', 'PARTIAL']] = None
    sent_time: Optional[str] = None
    waap: Optional[DataWAAP] = None


class InitializerType(F5XCBaseModel):
    """Initializer is information about an initializer that has not yet completed."""

    name: Optional[str] = None


class StatusType(F5XCBaseModel):
    """Status is a return value for calls that don't return other objects."""

    code: Optional[int] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class InitializersType(F5XCBaseModel):
    """Initializers tracks the progress of initialization of a configuration object"""

    pending: Optional[list[InitializerType]] = None
    result: Optional[StatusType] = None


class ViewRefType(F5XCBaseModel):
    """ViewRefType represents a reference to a view"""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class SystemObjectGetMetaType(F5XCBaseModel):
    """SystemObjectGetMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


# Convenience aliases
Spec = GetSpecType
