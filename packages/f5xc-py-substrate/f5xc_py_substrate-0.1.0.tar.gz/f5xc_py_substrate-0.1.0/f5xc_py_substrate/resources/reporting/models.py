"""Pydantic models for reporting."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ReportFreqDaily(F5XCBaseModel):
    """create report daily"""

    report_generation_time: Optional[str] = None


class ReportFreqMonthly(F5XCBaseModel):
    """create report monthly"""

    date: Optional[Literal['DATE_NONE', 'DATE_ONE', 'DATE_TWO', 'DATE_THREE', 'DATE_FOUR', 'DATE_FIVE', 'DATE_SIX', 'DATE_SEVEN', 'DATE_EIGHT', 'DATE_NINE', 'DATE_TEN', 'DATE_ELEVEN', 'DATE_TWELVE', 'DATE_THIRTEEN', 'DATE_FOURTEEN', 'DATE_FIFTEEN', 'DATE_SIXTEEN', 'DATE_SEVENTEEN', 'DATE_EIGHTEEN', 'DATE_NINETEEN', 'DATE_TWENTY', 'DATE_TWENTYONE', 'DATE_TWENTYTWO', 'DATE_TWENTYTHREE', 'DATE_TWENTYFOUR', 'DATE_TWENTYFIVE', 'DATE_TWENTYSIX', 'DATE_TWENTYSEVEN', 'DATE_TWENTYEIGHT', 'DATE_LAST']] = None
    report_generation_time: Optional[str] = None


class ReportFreqWeekly(F5XCBaseModel):
    """create report weekly"""

    day: Optional[Literal['WEEKDAY_NONE', 'WEEKDAY_MONDAY', 'WEEKDAY_TUESDAY', 'WEEKDAY_WEDNESDAY', 'WEEKDAY_THURSDAY', 'WEEKDAY_FRIDAY', 'WEEKDAY_SATURDAY', 'WEEKDAY_SUNDAY']] = None
    report_generation_time: Optional[str] = None


class ATBRequest(F5XCBaseModel):
    """Request for ATB"""

    daily: Optional[ReportFreqDaily] = None
    enable: Optional[bool] = None
    monthly: Optional[ReportFreqMonthly] = None
    namespace: Optional[str] = None
    resource_id: Optional[str] = None
    virtual_host: Optional[str] = None
    weekly: Optional[ReportFreqWeekly] = None


class ATBResponse(F5XCBaseModel):
    """Response for ATB"""

    enable: Optional[bool] = None


class ActionData(F5XCBaseModel):
    action_taken: Optional[str] = None
    count: Optional[str] = None


class ActionTakenData(F5XCBaseModel):
    action_taken: Optional[str] = None
    current_total: Optional[str] = None
    previous_total: Optional[str] = None
    sentiment: Optional[str] = None
    trend: Optional[float] = None


class TimeSeriesDataV2(F5XCBaseModel):
    """Time Series Data"""

    count: Optional[str] = None
    percentage: Optional[float] = None
    timestamp: Optional[float] = None


class AttackIntentData(F5XCBaseModel):
    """Attack Intent Data"""

    count: Optional[str] = None
    name: Optional[str] = None
    percentage: Optional[float] = None
    time_series: Optional[list[TimeSeriesDataV2]] = None


class AttackIntentTimeSeriesResponse(F5XCBaseModel):
    """The Response of Attack Intent Time Series API"""

    attack_intent_data: Optional[list[AttackIntentData]] = None


class AttackedBFPData(F5XCBaseModel):
    """Attacked BFP Data"""

    count: Optional[str] = None
    name: Optional[str] = None
    percentage: Optional[float] = None


class AttackedEndpointData(F5XCBaseModel):
    """Attacked application endpoint data"""

    app_name: Optional[str] = None
    hostname: Optional[str] = None
    human_request_count: Optional[str] = None
    malicious_bot_request_count: Optional[str] = None
    malicious_bot_request_percentage: Optional[float] = None
    method: Optional[str] = None
    total_percentage: Optional[float] = None
    uri: Optional[str] = None


class DistributionData(F5XCBaseModel):
    """Distribution Data"""

    count: Optional[str] = None
    name: Optional[str] = None
    percentage: Optional[float] = None


class AttackedEndpointDataV2(F5XCBaseModel):
    """Attacked application endpoint data V2"""

    endpoint_traffic_details: Optional[list[DistributionData]] = None
    malicious_bot_request_count: Optional[str] = None
    malicious_bot_request_percentage: Optional[float] = None
    total_count: Optional[str] = None
    uri: Optional[str] = None


class AttackedEndpointDataV4(F5XCBaseModel):
    """Attacked application endpoint data V4"""

    category: Optional[str] = None
    endpoint_traffic_details: Optional[list[DistributionData]] = None
    flow_label: Optional[str] = None
    malicious_bot_request_count: Optional[str] = None
    malicious_bot_request_percentage: Optional[float] = None
    total_count: Optional[str] = None
    uri: Optional[str] = None


class AutomatedTrafficActionsResponse(F5XCBaseModel):
    """Automated Bot Taffic in Actions Response"""

    actions: Optional[list[ActionData]] = None
    current_total: Optional[str] = None
    previous_total: Optional[str] = None
    sentiment: Optional[str] = None
    trend: Optional[float] = None


class AutomationTypeData(F5XCBaseModel):
    """Malicious bot automation type"""

    automation_type: Optional[str] = None
    previous_reqeust_count: Optional[str] = None
    request_count: Optional[str] = None
    request_percentage: Optional[float] = None
    request_sentiment: Optional[str] = None
    trend: Optional[float] = None


class CategoriesData(F5XCBaseModel):
    """Flow label categories data. Includes total number of requests and..."""

    category: Optional[str] = None
    percentage: Optional[float] = None
    requests: Optional[str] = None


class CategoryTimeSeriesData(F5XCBaseModel):
    count: Optional[str] = None
    name: Optional[str] = None
    time_series: Optional[list[TimeSeriesDataV2]] = None


class CategoriesTimeSeriesResponse(F5XCBaseModel):
    """The Response contains the time series data list for each endpoint category"""

    category_time_series_data: Optional[list[CategoryTimeSeriesData]] = None


class ConsumptionData(F5XCBaseModel):
    all: Optional[str] = None
    day: Optional[str] = None
    month: Optional[str] = None
    telemetry_client: Optional[str] = None


class ConsumptionSummaryResponse(F5XCBaseModel):
    """Response for Consumption Summary"""

    sums: Optional[list[ConsumptionData]] = None


class TimeSeriesGraphData(F5XCBaseModel):
    """The data for Timeseries Graph"""

    name: Optional[str] = None
    time_series_data: Optional[list[TimeSeriesDataV2]] = None


class CredentialStuffingAttackResponse(F5XCBaseModel):
    """Response for Credential Stuffing Attack"""

    bad_bot_login: Optional[str] = None
    bad_bot_login_percentage: Optional[float] = None
    create_date: Optional[float] = None
    mitigated_percentage: Optional[float] = None
    time_series: Optional[list[TimeSeriesGraphData]] = None
    trend: Optional[float] = None


class EndpointCategoryData(F5XCBaseModel):
    """Response that contains Endpoint Category Data"""

    action_distribution: Optional[list[DistributionData]] = None
    category_label: Optional[str] = None
    endpoint_count: Optional[str] = None
    event_count: Optional[str] = None
    event_percentage: Optional[float] = None
    traffic_channel: Optional[list[DistributionData]] = None
    traffic_distribution: Optional[list[DistributionData]] = None


class EndpointCategoryResponse(F5XCBaseModel):
    """Response that contains Endpoint Data"""

    endpoint_categories: Optional[list[EndpointCategoryData]] = None
    endpoint_count: Optional[str] = None
    event_count: Optional[str] = None


class EndpointLabelsData(F5XCBaseModel):
    """Endpoint Labels Data"""

    endpoint_label: Optional[str] = Field(default=None, alias="endpointLabel")
    requests: Optional[str] = None


class EndpointListData(F5XCBaseModel):
    """Response that contains All Protected Endpoints Data"""

    application: Optional[str] = None
    category: Optional[str] = None
    count: Optional[str] = None
    count_percentage: Optional[float] = None
    domain: Optional[str] = None
    endpoint: Optional[str] = None
    label: Optional[str] = None


class EndpointListResponse(F5XCBaseModel):
    """Response that contains Endpoint Data"""

    endpoints: Optional[list[EndpointListData]] = None


class EndpointSummaryResponse(F5XCBaseModel):
    """Response that contains Endpoint Summary"""

    total_applications: Optional[str] = None
    total_distinct_endpoints: Optional[str] = None


class EndpointSummaryResponseV2(F5XCBaseModel):
    """Response that contains Endpoint Summary with Unevaluated Transactions"""

    total_applications: Optional[str] = None
    total_distinct_endpoints: Optional[str] = None
    total_unevaluated_transactions: Optional[str] = None


class ForensicAggregateType(F5XCBaseModel):
    """Forensic AggregateType fields"""

    count: Optional[str] = None
    percent: Optional[float] = None
    value: Optional[str] = None


class ForensicErrorType(F5XCBaseModel):
    """Forensic ErrorType"""

    code: Optional[str] = None
    message: Optional[str] = None


class ForensicSuggestType(F5XCBaseModel):
    """Forensic SuggestType fields"""

    value: Optional[str] = None


class ForensicData(F5XCBaseModel):
    """Forensic Data"""

    aggregate: Optional[list[ForensicAggregateType]] = None
    errors: Optional[ForensicErrorType] = None
    key: Optional[Literal['TIMESTAMP', 'USERNAME', 'CLIENT_TOKEN', 'IP_ADDRESS', 'ASN', 'AS_ORGANIZATION', 'COUNTRY', 'METHOD', 'HOST', 'PATH', 'URL', 'REFERER', 'TRAFFIC_CHANNEL', 'IS_ATTACK', 'BOT_REASON', 'TRAFFIC_TYPE', 'THREAT_TYPE', 'SDK_VERSION', 'ACTION_TAKEN', 'COOKIE_AGE', 'BOT_COOKIE', 'USER_AGENT', 'USER_AGENT_OS_FAMILY', 'USER_AGENT_FAMILY', 'BROWSER_FINGERPRINT', 'USER_FINGERPRINT', 'HEADER_FINGERPRINT', 'DEVICE_ID', 'FLOW', 'AGENT', 'APPLICATION_NAME', 'PROTECTED_APPLICATION', 'RESPONSE_CODE', 'SERVER_RESPONSE_CODE', 'TRANSACTION_RESULT', 'MOBILE_TRANSACTION_INSIGHT', 'WEB_TRANSACTION_INSIGHT', 'TRIGGERED_RULE']] = None
    mode: Optional[Literal['AGGREGATE', 'SUGGEST']] = None
    suggest: Optional[list[ForensicSuggestType]] = None


class ForensicSortOption(F5XCBaseModel):
    """Query Result Forensic Sort Option"""

    key: Optional[str] = None
    order: Optional[Literal['DESCENDING', 'ASCENDING']] = None


class ForensicField(F5XCBaseModel):
    """Forensic query field"""

    key: Optional[Literal['TIMESTAMP', 'USERNAME', 'CLIENT_TOKEN', 'IP_ADDRESS', 'ASN', 'AS_ORGANIZATION', 'COUNTRY', 'METHOD', 'HOST', 'PATH', 'URL', 'REFERER', 'TRAFFIC_CHANNEL', 'IS_ATTACK', 'BOT_REASON', 'TRAFFIC_TYPE', 'THREAT_TYPE', 'SDK_VERSION', 'ACTION_TAKEN', 'COOKIE_AGE', 'BOT_COOKIE', 'USER_AGENT', 'USER_AGENT_OS_FAMILY', 'USER_AGENT_FAMILY', 'BROWSER_FINGERPRINT', 'USER_FINGERPRINT', 'HEADER_FINGERPRINT', 'DEVICE_ID', 'FLOW', 'AGENT', 'APPLICATION_NAME', 'PROTECTED_APPLICATION', 'RESPONSE_CODE', 'SERVER_RESPONSE_CODE', 'TRANSACTION_RESULT', 'MOBILE_TRANSACTION_INSIGHT', 'WEB_TRANSACTION_INSIGHT', 'TRIGGERED_RULE']] = None
    limit: Optional[int] = None
    mode: Optional[Literal['AGGREGATE', 'SUGGEST']] = None
    sort: Optional[ForensicSortOption] = None


class GlobalFilter(F5XCBaseModel):
    """Query Global Filter"""

    key: Optional[Literal['TIMESTAMP', 'USERNAME', 'CLIENT_TOKEN', 'IP_ADDRESS', 'ASN', 'AS_ORGANIZATION', 'COUNTRY', 'METHOD', 'HOST', 'PATH', 'URL', 'REFERER', 'TRAFFIC_CHANNEL', 'IS_ATTACK', 'BOT_REASON', 'TRAFFIC_TYPE', 'THREAT_TYPE', 'SDK_VERSION', 'ACTION_TAKEN', 'COOKIE_AGE', 'BOT_COOKIE', 'USER_AGENT', 'USER_AGENT_OS_FAMILY', 'USER_AGENT_FAMILY', 'BROWSER_FINGERPRINT', 'USER_FINGERPRINT', 'HEADER_FINGERPRINT', 'DEVICE_ID', 'FLOW', 'AGENT', 'APPLICATION_NAME', 'PROTECTED_APPLICATION', 'RESPONSE_CODE', 'SERVER_RESPONSE_CODE', 'TRANSACTION_RESULT', 'MOBILE_TRANSACTION_INSIGHT', 'WEB_TRANSACTION_INSIGHT', 'TRIGGERED_RULE']] = None
    op: Optional[Literal['IN', 'NOT_IN', 'MATCHES_REGEX', 'DOES_NOT_MATCH_REGEX', 'INCLUDES', 'DOES_NOT_INCLUDE', 'STARTS_WITH', 'ENDS_WITH']] = None
    values: Optional[list[str]] = None


class GlobalFilters(F5XCBaseModel):
    """Query Global Filters"""

    global_filters: Optional[list[GlobalFilter]] = None
    region_filter: Optional[Literal['US', 'EU', 'ASIA', 'CA']] = None


class ForensicFieldsRequest(F5XCBaseModel):
    """Request for Shape Bot Defense Forensic Fields"""

    end_time: Optional[str] = None
    fields: Optional[list[ForensicField]] = None
    filters: Optional[GlobalFilters] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None


class ForensicFieldsResponse(F5XCBaseModel):
    """Response for Shape Bot Defense Forensic Fields"""

    fields: Optional[list[ForensicData]] = None


class HumanBrowserData(F5XCBaseModel):
    """Human Browser Data"""

    browser: Optional[str] = None
    count: Optional[str] = None


class HumanDeviceData(F5XCBaseModel):
    """Human Device Data"""

    count: Optional[str] = None
    device: Optional[str] = None


class HumanGeolocationData(F5XCBaseModel):
    """Human Geolocation Data"""

    count: Optional[str] = None
    count_percentage: Optional[float] = None
    flag_string: Optional[str] = None
    geolocation: Optional[str] = None


class HumanPlatformData(F5XCBaseModel):
    """Human Platform Data"""

    count: Optional[str] = None
    platform: Optional[str] = None


class InsightBadBotReductionResponse(F5XCBaseModel):
    """Insight Bad Bot Reduction Response"""

    create_date: Optional[float] = None
    reduction: Optional[float] = None
    time_series_data: Optional[list[TimeSeriesDataV2]] = None


class InsightPersonalStatsResponse(F5XCBaseModel):
    """Insight Personal Stats Response"""

    bots: Optional[str] = None
    human: Optional[str] = None


class InsightUnaddressedAutomationsResponse(F5XCBaseModel):
    """Insight Unaddressed Automations Response"""

    bad_bots: Optional[float] = None
    create_date: Optional[float] = None
    flagged_endpoints: Optional[str] = None
    unaddressed: Optional[float] = None


class MaliciousBotASOrgData(F5XCBaseModel):
    """Malicious Bot ASOrg Data"""

    as_org: Optional[str] = None
    country: Optional[str] = None
    distinct_ip_count: Optional[str] = None
    human_request_count: Optional[str] = None
    malicious_bot_request_count: Optional[str] = None
    malicious_bot_request_percentage: Optional[float] = None
    total_percentage: Optional[float] = None


class MaliciousBotASOrgDataV3(F5XCBaseModel):
    """Malicious Bot ASOrg Data with action distribution"""

    actions: Optional[list[ActionData]] = None
    as_org: Optional[str] = None
    country: Optional[str] = None
    distinct_ip_count: Optional[str] = None
    malicious_bot_request_count: Optional[str] = None
    malicious_bot_request_percentage: Optional[float] = None
    total_percentage: Optional[float] = None


class MaliciousBotAppData(F5XCBaseModel):
    """Malicious Bot per App Data"""

    app_sentiment: Optional[str] = None
    application: Optional[str] = None
    malicious_bot_request_count: Optional[str] = None
    malicious_bot_request_percentage: Optional[float] = None
    malicious_bot_request_trend: Optional[float] = None


class MaliciousBotAttackIntentASOrgData(F5XCBaseModel):
    as_org: Optional[str] = None
    bad_bot_count: Optional[str] = None
    bad_bot_percentage: Optional[float] = None
    traffic_distribution: Optional[list[DistributionData]] = None


class MaliciousBotAttackIntentIPData(F5XCBaseModel):
    as_org: Optional[str] = None
    bad_bot_count: Optional[str] = None
    bad_bot_percentage: Optional[float] = None
    country: Optional[str] = None
    ip: Optional[str] = None
    traffic_distribution: Optional[list[DistributionData]] = None


class MaliciousBotAttackIntentUAData(F5XCBaseModel):
    bad_bot_count: Optional[str] = None
    bad_bot_percentage: Optional[float] = None
    browser: Optional[str] = None
    traffic_distribution: Optional[list[DistributionData]] = None
    ua: Optional[str] = None


class MaliciousBotIPData(F5XCBaseModel):
    """Malicious Bot IP Data"""

    as_org: Optional[str] = None
    country: Optional[str] = None
    human_request_count: Optional[str] = None
    ip: Optional[str] = None
    malicious_bot_request_count: Optional[str] = None
    malicious_bot_request_percentage: Optional[float] = None
    total_percentage: Optional[float] = None


class MaliciousBotIPDataV3(F5XCBaseModel):
    """Malicious Bot IP Data with action distribution"""

    actions: Optional[list[ActionData]] = None
    as_org: Optional[str] = None
    country: Optional[str] = None
    ip: Optional[str] = None
    malicious_bot_request_count: Optional[str] = None
    malicious_bot_request_percentage: Optional[float] = None
    total_percentage: Optional[float] = None


class MaliciousBotUAData(F5XCBaseModel):
    """Malicious bot user agent data"""

    browser: Optional[str] = None
    human_request_count: Optional[str] = None
    malicious_bot_request_count: Optional[str] = None
    malicious_bot_request_percentage: Optional[float] = None
    total_percentage: Optional[float] = None
    ua: Optional[str] = None


class MaliciousBotUADataV4(F5XCBaseModel):
    """Malicious bot user agent data with action distribution"""

    actions: Optional[list[ActionData]] = None
    browser: Optional[str] = None
    malicious_bot_request_count: Optional[str] = None
    malicious_bot_request_percentage: Optional[float] = None
    total_percentage: Optional[float] = None
    ua: Optional[str] = None


class MaliciousReportAPPTimeSeries(F5XCBaseModel):
    """Malicious Report APP Time Series"""

    count: Optional[str] = None
    percentage: Optional[float] = None
    timestamp: Optional[float] = None
    total_count: Optional[str] = None


class MaliciousReportAPPData(F5XCBaseModel):
    """Malicious Report APP Data"""

    count: Optional[str] = None
    name: Optional[str] = None
    percentage: Optional[float] = None
    time_series: Optional[list[MaliciousReportAPPTimeSeries]] = None
    timestamp: Optional[float] = None
    total: Optional[str] = None


class MaliciousReportAPPTimeSeriesResponse(F5XCBaseModel):
    """Malicious Report APP Time Series Response"""

    app_data: Optional[list[MaliciousReportAPPData]] = None


class MaliciousReportEndpointData(F5XCBaseModel):
    """Malicious Report Endpoint Data"""

    base_path: Optional[str] = None
    collapsed_url: Optional[str] = None
    leaves_count: Optional[str] = None
    level: Optional[str] = None
    method: Optional[str] = None
    name: Optional[str] = None
    parent: Optional[str] = None
    percentage: Optional[float] = None
    request_percentage: Optional[float] = None


class MaliciousReportEndpointsResponse(F5XCBaseModel):
    """Malicious Report Endpoints Response"""

    endpoint_data: Optional[list[MaliciousReportEndpointData]] = None


class MaliciousReportTransactionsData(F5XCBaseModel):
    """Malicious Report Transactions Data"""

    asn: Optional[str] = Field(default=None, alias="ASN")
    bfp: Optional[str] = Field(default=None, alias="BFP")
    hfp: Optional[str] = Field(default=None, alias="HFP")
    ip: Optional[str] = Field(default=None, alias="IP")
    ufp: Optional[str] = Field(default=None, alias="UFP")
    attack_intent_distribution: Optional[list[DistributionData]] = None
    count: Optional[str] = None
    name: Optional[str] = None
    reason_code_distribution: Optional[list[DistributionData]] = None
    user_agent: Optional[str] = None


class MaliciousReportTransactionsResponse(F5XCBaseModel):
    """Malicious Report Transactions Response"""

    malicious_bot: Optional[list[MaliciousReportTransactionsData]] = None


class MaliciousTrafficOverviewActionsResponse(F5XCBaseModel):
    """Malicious Bot Taffic Overview in Actions Response"""

    flagged_count: Optional[str] = None
    flagged_percentage: Optional[float] = None
    flagged_previous: Optional[str] = None
    flagged_sentiment: Optional[str] = None
    flagged_trend: Optional[float] = None
    mitigated_count: Optional[str] = None
    mitigated_percentage: Optional[float] = None
    mitigated_previous: Optional[str] = None
    mitigated_sentiment: Optional[str] = None
    mitigated_trend: Optional[float] = None
    total: Optional[str] = None
    unknown_count: Optional[str] = None
    unknown_percentage: Optional[float] = None


class MaliciousTrafficOverviewActionsV2Response(F5XCBaseModel):
    """Malicious Bot Taffic in Actions Response V2"""

    actions: Optional[list[ActionTakenData]] = None


class MaliciousTrafficOverviewMetricsResponse(F5XCBaseModel):
    """Malicious Traffic Overview Metrics Response"""

    asn: Optional[str] = Field(default=None, alias="ASN")
    bfp: Optional[str] = Field(default=None, alias="BFP")
    hfp: Optional[str] = Field(default=None, alias="HFP")
    ip: Optional[str] = Field(default=None, alias="IP")
    ufp: Optional[str] = Field(default=None, alias="UFP")
    user_agent: Optional[str] = None


class MaliciousTrafficTimeseriesActions(F5XCBaseModel):
    """Shape Bot Defense malicious traffic overview timeseries in actions value"""

    flagged_count: Optional[str] = None
    flagged_percentage: Optional[float] = None
    mitigated_count: Optional[str] = None
    mitigated_percentage: Optional[float] = None
    timestamp: Optional[float] = None
    unknown_count: Optional[str] = None
    unknown_percentage: Optional[float] = None


class MaliciousTrafficTimeseriesActionsResponse(F5XCBaseModel):
    """Response that contains Shape Bot Defense traffic overview timeseries in..."""

    values: Optional[list[MaliciousTrafficTimeseriesActions]] = None


class MaliciousTrafficTimeseriesActionsV2(F5XCBaseModel):
    """Shape Bot Defense malicious traffic overview timeseries in actions value"""

    name: Optional[str] = None
    time_series: Optional[list[TimeSeriesDataV2]] = None


class MaliciousTrafficTimeseriesActionsResponseV2(F5XCBaseModel):
    """Response that contains Shape Bot Defense traffic overview timeseries in..."""

    values: Optional[list[MaliciousTrafficTimeseriesActionsV2]] = None


class MonthlyUsageSummaryData(F5XCBaseModel):
    all: Optional[str] = None
    js: Optional[str] = None
    mobile_config: Optional[str] = None
    month: Optional[str] = None


class Pagination(F5XCBaseModel):
    """Pagination with number and size"""

    page_number: Optional[int] = None
    page_size: Optional[int] = None


class PeerGroupData(F5XCBaseModel):
    name: Optional[str] = None
    peer_count: Optional[str] = None
    peer_percentage: Optional[float] = None
    self_count: Optional[str] = None
    self_percentage: Optional[float] = None


class PeerGroupResponse(F5XCBaseModel):
    """The Response contains the total and detail of the Peer Group data"""

    details: Optional[list[PeerGroupData]] = None


class PeerGroupTrafficOverviewResponse(F5XCBaseModel):
    """The Response contains the total and detail of the Peer Group data"""

    details: Optional[list[PeerGroupData]] = None
    peer_percentage: Optional[float] = None
    peer_total: Optional[str] = None
    self_percentage: Optional[float] = None
    self_total: Optional[str] = None


class PeerStatusRequest(F5XCBaseModel):
    pass


class PeerStatusResponse(F5XCBaseModel):
    """The Response for checking if the tenant has peers or not"""

    has_peers: Optional[bool] = None


class ReportEndpointDataV2(F5XCBaseModel):
    """Report Endpoint Data V2"""

    automated_events: Optional[str] = None
    automated_percentage: Optional[float] = None
    base_path: Optional[str] = None
    collapsed_url: Optional[str] = None
    events: Optional[str] = None
    flagged_events: Optional[str] = None
    flagged_percentage: Optional[float] = None
    human_events: Optional[str] = None
    human_percentage: Optional[float] = None
    method: Optional[str] = None
    mitigated_events: Optional[str] = None
    mitigated_percentage: Optional[float] = None
    request_percentage: Optional[float] = None
    undefined_events: Optional[str] = None
    undefined_percentage: Optional[float] = None


class ReportEndpointsResponse(F5XCBaseModel):
    """Report Endpoints Response"""

    endpoint_data: Optional[list[ReportEndpointDataV2]] = None


class SortOption(F5XCBaseModel):
    """Query Result Sort Option"""

    key: Optional[Literal['TIMESTAMP', 'USERNAME', 'CLIENT_TOKEN', 'IP_ADDRESS', 'ASN', 'AS_ORGANIZATION', 'COUNTRY', 'METHOD', 'HOST', 'PATH', 'URL', 'REFERER', 'TRAFFIC_CHANNEL', 'IS_ATTACK', 'BOT_REASON', 'TRAFFIC_TYPE', 'THREAT_TYPE', 'SDK_VERSION', 'ACTION_TAKEN', 'COOKIE_AGE', 'BOT_COOKIE', 'USER_AGENT', 'USER_AGENT_OS_FAMILY', 'USER_AGENT_FAMILY', 'BROWSER_FINGERPRINT', 'USER_FINGERPRINT', 'HEADER_FINGERPRINT', 'DEVICE_ID', 'FLOW', 'AGENT', 'APPLICATION_NAME', 'PROTECTED_APPLICATION', 'RESPONSE_CODE', 'SERVER_RESPONSE_CODE', 'TRANSACTION_RESULT', 'MOBILE_TRANSACTION_INSIGHT', 'WEB_TRANSACTION_INSIGHT', 'TRIGGERED_RULE']] = None
    order: Optional[Literal['DESCENDING', 'ASCENDING']] = None


class TimeSeriesMinimalData(F5XCBaseModel):
    """Requests over time"""

    count: Optional[str] = None
    timestamp: Optional[float] = None


class TimeSeriesGraphMinimalData(F5XCBaseModel):
    """Response that contains timeseries against each traffic or any other type"""

    name: Optional[str] = None
    time_series: Optional[list[TimeSeriesMinimalData]] = None


class TopAttackIntentData(F5XCBaseModel):
    """Top Attack Intent Data"""

    color_alert: Optional[bool] = None
    events: Optional[str] = None
    link: Optional[str] = None
    percentage: Optional[float] = None
    sentiment: Optional[str] = None
    trend: Optional[float] = None
    type_: Optional[str] = Field(default=None, alias="type")


class TopAttackIntentResponse(F5XCBaseModel):
    """The Response of Top Attack Intent  API"""

    attack_intents: Optional[list[TopAttackIntentData]] = None
    total: Optional[str] = None


class TopAttackedBFPResponse(F5XCBaseModel):
    """Top Attacked BFP Response"""

    attacked_bfp: Optional[list[AttackedBFPData]] = None


class TopAttackedEndpointsResponse(F5XCBaseModel):
    """Response for top attacked application endpoints"""

    attacked_endpoints: Optional[list[AttackedEndpointData]] = None


class TopAttackedEndpointsResponseV2(F5XCBaseModel):
    """Response for top attacked application endpoints"""

    attacked_endpoints: Optional[list[AttackedEndpointDataV2]] = None


class TopAttackedEndpointsResponseV4(F5XCBaseModel):
    """Response for top attacked application endpoints"""

    attacked_endpoints: Optional[list[AttackedEndpointDataV4]] = None


class TopAutomationTypesResponse(F5XCBaseModel):
    """Response for top malicious bot automation types"""

    automation_types: Optional[list[AutomationTypeData]] = None


class TopCategoriesResponse(F5XCBaseModel):
    """Response for top flow label categories"""

    categories: Optional[list[CategoriesData]] = None
    total_requests: Optional[str] = None


class TopEndpointLabelsResponse(F5XCBaseModel):
    """Response for Top Endpoint Labels"""

    endpoint_labels: Optional[list[EndpointLabelsData]] = None
    total_requests: Optional[str] = None


class TopGoodBotsData(F5XCBaseModel):
    """Good bots data"""

    name: Optional[str] = None
    traffic_usage_count: Optional[str] = None
    traffic_usage_percentage: Optional[float] = None
    type_: Optional[str] = Field(default=None, alias="type")


class TopGoodBotsResponse(F5XCBaseModel):
    """Response for top good bots"""

    good_bots: Optional[list[TopGoodBotsData]] = None


class TopGoodBotsResponseV2(F5XCBaseModel):
    good_bots: Optional[list[TopGoodBotsData]] = None
    top_good_bots_percentage: Optional[float] = None
    total_good_bots: Optional[str] = None


class TopHumanBrowserResponse(F5XCBaseModel):
    """Top Human Browser Response"""

    human_browser_data: Optional[list[HumanBrowserData]] = None


class TopHumanDeviceResponse(F5XCBaseModel):
    """Top Human Device Response"""

    human_device_data: Optional[list[HumanDeviceData]] = None


class TopHumanGeolocationResponse(F5XCBaseModel):
    """Top Human Geolocation Response"""

    human_geolocation_data: Optional[list[HumanGeolocationData]] = None


class TopHumanPlatformResponse(F5XCBaseModel):
    """Top Human Platform Response"""

    human_platform_data: Optional[list[HumanPlatformData]] = None


class TopLatencyOverviewAppsData(F5XCBaseModel):
    """Top Latency Applications"""

    application: Optional[str] = None
    counts: Optional[str] = None
    latency: Optional[str] = None
    sentiment: Optional[str] = None
    status: Optional[str] = None
    trend: Optional[float] = None


class TopLatencyOverviewAppsResponse(F5XCBaseModel):
    """Bot API Latency Across Top Protected Apps Overview Apps Response"""

    applications: Optional[list[TopLatencyOverviewAppsData]] = None


class TopLatencyOverviewResponse(F5XCBaseModel):
    """Bot API Latency Across Top Protected Apps Overview Response"""

    average_latency: Optional[str] = None
    critical: Optional[str] = None
    high: Optional[str] = None
    low: Optional[str] = None
    previous_latency: Optional[str] = None
    sentiment: Optional[str] = None
    trend: Optional[float] = None


class TopMaliciousBotsAttackIntentByASOrgResponse(F5XCBaseModel):
    """Response for top bad bot events by ASN of Attack Intent Types"""

    bad_bot_asn_data: Optional[list[MaliciousBotAttackIntentASOrgData]] = None


class TopMaliciousBotsAttackIntentByIPResponse(F5XCBaseModel):
    """Response for top bad bot events by source IPs of Attack Intent Types"""

    bad_bot_ip_data: Optional[list[MaliciousBotAttackIntentIPData]] = None


class TopMaliciousBotsAttackIntentByUAResponse(F5XCBaseModel):
    """Response for top bad bot events by User Agent of Attack Intent Types"""

    bad_bot_ua_data: Optional[list[MaliciousBotAttackIntentUAData]] = None


class TopMaliciousBotsByASOrgResponse(F5XCBaseModel):
    """Response for top malicious bots by AS Organizations"""

    malicious_bots: Optional[list[MaliciousBotASOrgData]] = None


class TopMaliciousBotsByASOrgResponseV3(F5XCBaseModel):
    """Response for top malicious bots by AS Organizations with action distribution"""

    malicious_bots: Optional[list[MaliciousBotASOrgDataV3]] = None


class TopMaliciousBotsByAppResponse(F5XCBaseModel):
    """Response for top malicious bots by applications"""

    application_data: Optional[list[MaliciousBotAppData]] = None
    total_applications: Optional[str] = None


class TopMaliciousBotsByIPResponse(F5XCBaseModel):
    """Response for top malicious bots by source IPs"""

    malicious_bots: Optional[list[MaliciousBotIPData]] = None


class TopMaliciousBotsByIPResponseV3(F5XCBaseModel):
    """Response for top malicious bots by source IPs with action distribution"""

    malicious_bots: Optional[list[MaliciousBotIPDataV3]] = None


class TopMaliciousBotsByUAResponse(F5XCBaseModel):
    """Response for top malicious bots by user agent string"""

    malicious_bots: Optional[list[MaliciousBotUAData]] = None


class TopMaliciousBotsByUAResponseV4(F5XCBaseModel):
    """Response for top malicious bots by user agent string  with action distribution"""

    malicious_bots: Optional[list[MaliciousBotUADataV4]] = None


class TopTransactionsByAppData(F5XCBaseModel):
    """Top Transactions per Application Data"""

    all_traffic_request_count: Optional[str] = None
    all_traffic_request_percentage: Optional[float] = None
    all_traffic_request_trend: Optional[float] = None
    app_sentiment: Optional[str] = None
    application: Optional[str] = None


class TopTransactionsByAppResponse(F5XCBaseModel):
    """Response for top transactions by applications"""

    application_data: Optional[list[TopTransactionsByAppData]] = None
    total_applications: Optional[str] = None


class TotalAutomationResponse(F5XCBaseModel):
    """Response for Total Automation Insight Event"""

    automated: Optional[str] = None
    automated_percentage: Optional[float] = None
    create_date: Optional[float] = None
    endpoint: Optional[str] = None
    endpoint_label: Optional[str] = None
    good_bot: Optional[str] = None
    good_bot_percentage: Optional[float] = None
    human: Optional[str] = None
    human_percentage: Optional[float] = None
    malicious_bot: Optional[str] = None
    malicious_bot_percentage: Optional[float] = None
    mobile: Optional[str] = None
    mobile_percentage: Optional[float] = None
    others: Optional[str] = None
    others_percentage: Optional[float] = None
    traffic_channel: Optional[str] = None
    web: Optional[str] = None
    web_percentage: Optional[float] = None


class TrafficOverviewData(F5XCBaseModel):
    """Data for different traffic type"""

    previous_reqeust_count: Optional[str] = None
    request_count: Optional[str] = None
    request_sentiment: Optional[str] = None
    traffic_type: Optional[str] = None
    trend: Optional[float] = None


class Transaction(F5XCBaseModel):
    """Traffic transaction"""

    action_taken: Optional[str] = None
    app_type: Optional[str] = None
    as_org: Optional[str] = None
    asn: Optional[int] = None
    attack_intent: Optional[str] = None
    automation_type: Optional[str] = None
    country: Optional[str] = None
    hostname: Optional[str] = None
    inference: Optional[str] = None
    inference_sub_type: Optional[str] = None
    ip: Optional[str] = None
    method: Optional[str] = None
    referer: Optional[str] = None
    timestamp: Optional[str] = None
    ua: Optional[str] = None
    uri: Optional[str] = None


class TrafficOverviewExpandedResponse(F5XCBaseModel):
    """Response for Shape Bot Defense expanded traffic overview"""

    total_transactions: Optional[str] = None
    transactions: Optional[list[Transaction]] = None


class TrafficOverviewExpandedV5Request(F5XCBaseModel):
    """Request for Shape Bot Defense expanded traffic overview V5"""

    end_time: Optional[str] = None
    filters: Optional[GlobalFilters] = None
    namespace: Optional[str] = None
    pagination: Optional[Pagination] = None
    sort: Optional[SortOption] = None
    start_time: Optional[str] = None


class TransactionField(F5XCBaseModel):
    """Traffic transaction fields"""

    group: Optional[str] = None
    name: Optional[str] = None
    value: Optional[str] = None


class TransactionRecord(F5XCBaseModel):
    """Traffic transaction"""

    fields: Optional[list[TransactionField]] = None


class TrafficOverviewExpandedV5Response(F5XCBaseModel):
    """Response for Shape Bot Defense expanded traffic overview V5"""

    total_transactions: Optional[str] = None
    transactions: Optional[list[TransactionRecord]] = None


class TrafficOverviewResponse(F5XCBaseModel):
    """Response that contains Shape Bot Defense traffic overview"""

    human: Optional[str] = None
    malicious_bot: Optional[str] = None
    total: Optional[str] = None


class TrafficOverviewTimeseriesValue(F5XCBaseModel):
    """Shape Bot Defense traffic overview timeseries value"""

    human: Optional[str] = None
    malicious_bot: Optional[str] = None
    timestamp: Optional[float] = None


class TrafficOverviewTimeseriesResponse(F5XCBaseModel):
    """Response that contains Shape Bot Defense traffic overview timeseries"""

    values: Optional[list[TrafficOverviewTimeseriesValue]] = None


class TrafficOverviewTimeseriesV2Value(F5XCBaseModel):
    """Shape Bot Defense traffic overview timeseries V2 value"""

    good_bot: Optional[str] = None
    human: Optional[str] = None
    malicious_bot: Optional[str] = None
    others: Optional[str] = None
    timestamp: Optional[float] = None


class TrafficOverviewTimeseriesV2Response(F5XCBaseModel):
    """Response that contains Shape Bot Defense traffic overview timeseries"""

    values: Optional[list[TrafficOverviewTimeseriesV2Value]] = None


class TrafficOverviewTimeseriesV3Response(F5XCBaseModel):
    """Response that contains Shape Bot Defense traffic type timeseries"""

    traffic_type_data: Optional[list[TimeSeriesGraphMinimalData]] = None


class TrafficOverviewV2Request(F5XCBaseModel):
    """Request for Shape Bot Defense traffic overview with global filters"""

    category: Optional[str] = None
    end_time: Optional[str] = None
    filters: Optional[GlobalFilters] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None
    use_raw_data: Optional[bool] = None


class TrafficOverviewV2Response(F5XCBaseModel):
    """Response that contains Shape Bot Defense traffic overview"""

    bot_trend: Optional[float] = None
    good_bot: Optional[str] = None
    good_bot_percentage: Optional[float] = None
    good_bot_previous: Optional[str] = None
    good_bot_sentiment: Optional[str] = None
    good_bot_trend: Optional[float] = None
    human: Optional[str] = None
    human_percentage: Optional[float] = None
    human_previous: Optional[str] = None
    human_sentiment: Optional[str] = None
    human_trend: Optional[float] = None
    malicious_bot: Optional[str] = None
    malicious_bot_percentage: Optional[float] = None
    malicious_bot_previous: Optional[str] = None
    malicious_bot_sentiment: Optional[str] = None
    others: Optional[str] = None
    others_percentage: Optional[float] = None
    others_previous: Optional[str] = None
    others_trend: Optional[float] = None
    total: Optional[str] = None
    total_previous: Optional[str] = None
    total_sentiment: Optional[str] = None
    total_trend: Optional[float] = None


class TrafficOverviewV3Response(F5XCBaseModel):
    """Response that contains Shape Bot Defense traffic overview"""

    traffic_type_data: Optional[list[TrafficOverviewData]] = None


class TransactionUsageSummaryResponse(F5XCBaseModel):
    """Response for Transaction Usage Summary"""

    records: Optional[list[MonthlyUsageSummaryData]] = None


# Convenience aliases
