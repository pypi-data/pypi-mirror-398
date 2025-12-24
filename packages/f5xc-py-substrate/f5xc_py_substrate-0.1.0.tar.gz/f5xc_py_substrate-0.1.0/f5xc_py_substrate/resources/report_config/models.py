"""Pydantic models for report_config."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ReportConfigListItem(F5XCBaseModel):
    """List item for report_config resources."""


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


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


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


class ProtectedLBCount(F5XCBaseModel):
    """Protected LB Count."""

    protected_lb_count: Optional[str] = None
    total_lb_count: Optional[str] = None


class ReportDataATB(F5XCBaseModel):
    """ATB report data."""

    json_data: Optional[str] = None


class ReportHeader(F5XCBaseModel):
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


class ReportDataWAAP(F5XCBaseModel):
    """WAAP report data."""

    attack_impact: Optional[AttackImpact] = None
    attack_sources: Optional[AttackSources] = None
    lb_count: Optional[ProtectedLBCount] = None
    report_footer: Optional[Any] = None
    report_header: Optional[ReportHeader] = None
    security_events: Optional[SecurityEvents] = None
    threat_details: Optional[ThreatDetails] = None


class ReportDeliveryStatus(F5XCBaseModel):
    """report generation status"""

    delivered_time: Optional[str] = None
    eta: Optional[str] = None
    report_delivery_state: Optional[Literal['REPORT_DELIVERY_STATE_NONE', 'REPORT_DELIVERY_STATE_SUCCESS', 'REPORT_DELIVERY_STATE_ERROR', 'REPORT_DELIVERY_STATE_PARTIAL', 'REPORT_DELIVERY_STATE_PENDING', 'REPORT_DELIVERY_STATE_DOWNLOAD']] = None


class ReportGenerationStatus(F5XCBaseModel):
    """report generation status"""

    eta: Optional[str] = None
    report_status: Optional[Literal['NONE', 'SUCCESS', 'ERROR', 'PENDING', 'PAUSED', 'PARTIAL']] = None
    scheduled_time: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class ReportRecipients(F5XCBaseModel):
    """Report recipients"""

    user_groups: Optional[list[ObjectRefType]] = None


class ReportFreqDaily(F5XCBaseModel):
    """create report daily"""

    report_generation_time: Optional[str] = None


class ReportFreqMonthly(F5XCBaseModel):
    """create report monthly"""

    date: Optional[Literal['DATE_NONE', 'DATE_ONE', 'DATE_TWO', 'DATE_THREE', 'DATE_FOUR', 'DATE_FIVE', 'DATE_SIX', 'DATE_SEVEN', 'DATE_EIGHT', 'DATE_NINE', 'DATE_TEN', 'DATE_ELEVEN', 'DATE_TWELVE', 'DATE_THIRTEEN', 'DATE_FOURTEEN', 'DATE_FIFTEEN', 'DATE_SIXTEEN', 'DATE_SEVENTEEN', 'DATE_EIGHTEEN', 'DATE_NINETEEN', 'DATE_TWENTY', 'DATE_TWENTYONE', 'DATE_TWENTYTWO', 'DATE_TWENTYTHREE', 'DATE_TWENTYFOUR', 'DATE_TWENTYFIVE', 'DATE_TWENTYSIX', 'DATE_TWENTYSEVEN', 'DATE_TWENTYEIGHT', 'DATE_LAST']] = None
    report_generation_time: Optional[str] = None


class Namespaces(F5XCBaseModel):
    """namespaces"""

    namespaces: Optional[list[str]] = None


class ReportFreqWeekly(F5XCBaseModel):
    """create report weekly"""

    day: Optional[Literal['WEEKDAY_NONE', 'WEEKDAY_MONDAY', 'WEEKDAY_TUESDAY', 'WEEKDAY_WEDNESDAY', 'WEEKDAY_THURSDAY', 'WEEKDAY_FRIDAY', 'WEEKDAY_SATURDAY', 'WEEKDAY_SUNDAY']] = None
    report_generation_time: Optional[str] = None


class ReportTypeWaap(F5XCBaseModel):
    """Report Type Waap"""

    current_namespace: Optional[Any] = None
    daily: Optional[ReportFreqDaily] = None
    monthly: Optional[ReportFreqMonthly] = None
    namespaces: Optional[Namespaces] = None
    weekly: Optional[ReportFreqWeekly] = None


class CreateSpecType(F5XCBaseModel):
    """Report configuration is used to schedule report generation at a later..."""

    report_recipients: Optional[ReportRecipients] = None
    waap: Optional[ReportTypeWaap] = None


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class GetSpecType(F5XCBaseModel):
    """Get Report Configuration will read the configuration"""

    report_recipients: Optional[ReportRecipients] = None
    waap: Optional[ReportTypeWaap] = None


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


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class GetSpecType(F5XCBaseModel):
    """Get Report will read the report metadata."""

    atb: Optional[ReportDataATB] = None
    report_config: Optional[ObjectRefType] = None
    report_creator_method: Optional[Literal['REPORT_CREATE_METHOD_NONE', 'REPORT_CREATE_METHOD_PERIODIC', 'REPORT_CREATE_METHOD_USER_TRIGGERED']] = None
    report_delivery_status: Optional[ReportDeliveryStatus] = None
    report_frequency: Optional[str] = None
    report_generation_status: Optional[ReportGenerationStatus] = None
    report_id: Optional[str] = None
    report_status: Optional[Literal['NONE', 'SUCCESS', 'ERROR', 'PENDING', 'PAUSED', 'PARTIAL']] = None
    sent_time: Optional[str] = None
    waap: Optional[ReportDataWAAP] = None


class ObjectMetaType(F5XCBaseModel):
    """ObjectMetaType is metadata(common attributes) of an object that all..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    """Configuration specification for Report Configuration."""

    atb: Optional[ReportDataATB] = None
    report_config: Optional[ObjectRefType] = None
    report_creator_method: Optional[Literal['REPORT_CREATE_METHOD_NONE', 'REPORT_CREATE_METHOD_PERIODIC', 'REPORT_CREATE_METHOD_USER_TRIGGERED']] = None
    report_delivery_status: Optional[ReportDeliveryStatus] = None
    report_frequency: Optional[str] = None
    report_generation_status: Optional[ReportGenerationStatus] = None
    sent_time: Optional[str] = None
    waap: Optional[ReportDataWAAP] = None


class SpecType(F5XCBaseModel):
    """Shape of the report specification"""

    gc_spec: Optional[GlobalSpecType] = None


class SystemObjectMetaType(F5XCBaseModel):
    """SystemObjectMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_cookie: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    direct_ref_hash: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    namespace: Optional[list[ObjectRefType]] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    revision: Optional[str] = None
    sre_disable: Optional[bool] = None
    tenant: Optional[str] = None
    trace_info: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class Object(F5XCBaseModel):
    """Report object specification"""

    metadata: Optional[ObjectMetaType] = None
    spec: Optional[SpecType] = None
    system_metadata: Optional[SystemObjectMetaType] = None


class CustomAPIListResponseItem(F5XCBaseModel):
    """By default a summary of report is returned in 'List'. By setting..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[GetSpecType] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    object_: Optional[Object] = Field(default=None, alias="object")
    owner_view: Optional[ViewRefType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class GenerateReportRequest(F5XCBaseModel):
    """Generate report request"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class GenerateReportResponse(F5XCBaseModel):
    """Generate report response"""

    pass


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace Report Configuration.  Update the configuration by replacing the..."""

    report_recipients: Optional[ReportRecipients] = None
    waap: Optional[ReportTypeWaap] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class StatusMetaType(F5XCBaseModel):
    """StatusMetaType is metadata that all status must have."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_id: Optional[str] = None
    publish: Optional[Literal['STATUS_DO_NOT_PUBLISH', 'STATUS_PUBLISH']] = None
    status_id: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class StatusObject(F5XCBaseModel):
    """Status of the report status object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    report_delivery_status: Optional[ReportDeliveryStatus] = None
    report_generation_status: Optional[ReportGenerationStatus] = None
    reports: Optional[list[ObjectRefType]] = None
    sent_time: Optional[str] = None


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[CreateRequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[ReplaceRequest] = None
    spec: Optional[GetSpecType] = None
    status: Optional[list[StatusObject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class ListReportsHistoryResponseItem(F5XCBaseModel):
    metadata: Optional[ObjectMetaType] = None
    spec: Optional[SpecType] = None


class ListReportsHistoryResponse(F5XCBaseModel):
    """List of report objects for the given namespace and report configuration names"""

    items: Optional[list[CustomAPIListResponseItem]] = None
    reports: Optional[list[GlobalSpecType]] = None
    reports_list: Optional[list[ListReportsHistoryResponseItem]] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of report_config is returned in 'List'. By setting..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[GetSpecType] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[StatusObject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[ListResponseItem]] = None


class ReplaceResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = GetSpecType
Spec = GlobalSpecType
Spec = SpecType
Spec = ReplaceSpecType
