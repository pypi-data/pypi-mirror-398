"""Pydantic models for service."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class APIEPDynExample(F5XCBaseModel):
    """List of Examples of expanded URL components for API endpoints that are..."""

    component_examples: Optional[list[str]] = None
    component_identifier: Optional[str] = None


class AuthenticationTypeLocPair(F5XCBaseModel):
    """API Endpoint's Authentication Type and Location."""

    auth_type: Optional[str] = None
    location: Optional[Literal['AUTH_LOCATION_HEADER', 'AUTH_LOCATION_QUERY', 'AUTH_LOCATION_BODY', 'AUTH_LOCATION_COOKIE']] = None
    type_: Optional[Literal['AUTH_TYPE_BASIC', 'AUTH_TYPE_BEARER', 'AUTH_TYPE_JWT', 'AUTH_TYPE_API_KEY', 'AUTH_TYPE_OAUTH2', 'AUTH_TYPE_OPENID', 'AUTH_TYPE_HTTP', 'AUTH_TYPE_OAUTH1', 'AUTH_TYPE_DIGEST', 'AUTH_TYPE_NEGOTIATE']] = Field(default=None, alias="type")


class PDFSpec(F5XCBaseModel):
    """Probability Density point in (PDF(x)) of the metric. x is the value of..."""

    probability: Optional[float] = None
    x: Optional[float] = None


class PDFStat(F5XCBaseModel):
    """Probability Density Function statistics of the metric. pdf_mean is the..."""

    pdf_95: Optional[float] = None
    pdf_mean: Optional[float] = None


class APIEPPDFInfo(F5XCBaseModel):
    """Metrics supported currently are request_size response_size..."""

    creation_timestamp: Optional[str] = None
    error_rate: Optional[list[PDFSpec]] = None
    error_rate_stat: Optional[PDFStat] = None
    latency_no_data: Optional[list[PDFSpec]] = None
    latency_no_data_stat: Optional[PDFStat] = None
    latency_with_data: Optional[list[PDFSpec]] = None
    latency_with_data_stat: Optional[PDFStat] = None
    request_rate: Optional[list[PDFSpec]] = None
    request_rate_stat: Optional[PDFStat] = None
    request_size: Optional[list[PDFSpec]] = None
    request_size_stat: Optional[PDFStat] = None
    response_size: Optional[list[PDFSpec]] = None
    response_size_stat: Optional[PDFStat] = None
    response_throughput: Optional[list[PDFSpec]] = None
    response_throughput_stat: Optional[PDFStat] = None


class RiskScore(F5XCBaseModel):
    """Risk score of the vulnerabilities found for this API Endpoint."""

    score: Optional[float] = None
    severity: Optional[Literal['APIEP_SEC_RISK_NONE', 'APIEP_SEC_RISK_LOW', 'APIEP_SEC_RISK_MED', 'APIEP_SEC_RISK_HIGH', 'APIEP_SEC_RISK_CRITICAL']] = None


class APIEPInfo(F5XCBaseModel):
    """Information about automatically identified API endpoint Each identified..."""

    access_discovery_time: Optional[str] = None
    api_groups: Optional[list[str]] = None
    api_type: Optional[Literal['API_TYPE_UNKNOWN', 'API_TYPE_GRAPHQL', 'API_TYPE_REST', 'API_TYPE_GRPC']] = None
    attributes: Optional[list[str]] = None
    authentication_state: Optional[Literal['AUTH_STATE_UNKNOWN', 'AUTH_STATE_AUTHENTICATED', 'AUTH_STATE_UNAUTHENTICATED']] = None
    authentication_types: Optional[list[AuthenticationTypeLocPair]] = None
    avg_latency: Optional[float] = None
    base_path: Optional[str] = None
    category: Optional[list[Literal['APIEP_CATEGORY_DISCOVERED', 'APIEP_CATEGORY_SWAGGER', 'APIEP_CATEGORY_INVENTORY', 'APIEP_CATEGORY_SHADOW', 'APIEP_CATEGORY_DEPRECATED', 'APIEP_CATEGORY_NON_API']]] = None
    collapsed_url: Optional[str] = None
    compliances: Optional[list[str]] = None
    domains: Optional[list[str]] = None
    dyn_examples: Optional[list[APIEPDynExample]] = None
    engines: Optional[list[str]] = None
    err_rsp_count: Optional[str] = None
    has_learnt_schema: Optional[bool] = None
    last_tested: Optional[str] = None
    max_latency: Optional[float] = None
    method: Optional[str] = None
    pdf_info: Optional[APIEPPDFInfo] = None
    pii_level: Optional[Literal['APIEP_PII_NOT_DETECTED', 'APIEP_PII_DETECTED']] = None
    req_rate: Optional[float] = None
    request_percentage: Optional[float] = None
    requests_count: Optional[int] = None
    risk_score: Optional[RiskScore] = None
    schema_status: Optional[str] = None
    sec_events_count: Optional[int] = None
    security_risk: Optional[Literal['APIEP_SEC_RISK_NONE', 'APIEP_SEC_RISK_LOW', 'APIEP_SEC_RISK_MED', 'APIEP_SEC_RISK_HIGH', 'APIEP_SEC_RISK_CRITICAL']] = None
    sensitive_data: Optional[list[Literal['SENSITIVE_DATA_TYPE_CCN', 'SENSITIVE_DATA_TYPE_SSN', 'SENSITIVE_DATA_TYPE_IP', 'SENSITIVE_DATA_TYPE_EMAIL', 'SENSITIVE_DATA_TYPE_PHONE', 'SENSITIVE_DATA_TYPE_CREDENTIALS', 'SENSITIVE_DATA_TYPE_APP_INFO_LEAKAGE', 'SENSITIVE_DATA_TYPE_MASKED_PII', 'SENSITIVE_DATA_TYPE_LOCATION']]] = None
    sensitive_data_location: Optional[list[str]] = None
    sensitive_data_types: Optional[list[str]] = None


class TrendValue(F5XCBaseModel):
    """Trend value contains trend value, trend sentiment and trend calculation..."""

    description: Optional[str] = None
    previous_value: Optional[str] = None
    sentiment: Optional[Literal['TREND_SENTIMENT_NONE', 'TREND_SENTIMENT_POSITIVE', 'TREND_SENTIMENT_NEGATIVE']] = None
    value: Optional[str] = None


class MetricValue(F5XCBaseModel):
    """Each metric value consists of a timestamp and a value. Timestamp in the..."""

    timestamp: Optional[float] = None
    trend_value: Optional[TrendValue] = None
    value: Optional[str] = None


class MetricFeatureData(F5XCBaseModel):
    """Contains metric values for timeseries features specified in the request."""

    anomaly: Optional[list[MetricValue]] = None
    confidence_lower_bound: Optional[list[MetricValue]] = None
    confidence_upper_bound: Optional[list[MetricValue]] = None
    healthscore: Optional[list[MetricValue]] = None
    raw: Optional[list[MetricValue]] = None
    trend: Optional[list[MetricValue]] = None


class MetricData(F5XCBaseModel):
    """MetricData contains the metric type and the corresponding metric value(s)"""

    type_: Optional[Literal['METRIC_TYPE_NONE', 'REQUEST_RATE', 'ERROR_RATE', 'RESPONSE_LATENCY', 'REQUEST_THROUGHPUT', 'RESPONSE_THROUGHPUT', 'ERROR_RATE_3XX', 'ERROR_RATE_4XX', 'ERROR_RATE_5XX', 'RESPONSE_LATENCY_PERCENTILE_50', 'RESPONSE_LATENCY_PERCENTILE_90', 'RESPONSE_LATENCY_PERCENTILE_99', 'RESPONSE_DATA_TRANSFER_DURATION', 'CLIENT_RTT', 'SERVER_RTT', 'SERVER_DATA_TRANSFER_TIME', 'APP_LATENCY', 'REQUEST_TO_ORIGIN_RATE', 'HTTP_REQUEST_RATE', 'HTTP_ERROR_RATE', 'HTTP_ERROR_RATE_4XX', 'HTTP_ERROR_RATE_5XX', 'HTTP_RESPONSE_LATENCY', 'HTTP_RESPONSE_LATENCY_PERCENTILE_50', 'HTTP_RESPONSE_LATENCY_PERCENTILE_90', 'HTTP_RESPONSE_LATENCY_PERCENTILE_99', 'HTTP_SERVER_DATA_TRANSFER_TIME', 'HTTP_APP_LATENCY', 'TCP_CONNECTION_RATE', 'TCP_ERROR_RATE', 'TCP_ERROR_RATE_CLIENT', 'TCP_ERROR_RATE_UPSTREAM', 'TCP_CONNECTION_DURATION']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None
    value: Optional[MetricFeatureData] = None


class EdgeMetricData(F5XCBaseModel):
    """EdgeMetricData contains requested metric data for an edge"""

    data: Optional[list[MetricData]] = None


class EdgeMetricSelector(F5XCBaseModel):
    """EdgeMetricSelector is used to select the metrics that should be returned..."""

    features: Optional[list[Literal['TIMESERIES_FEATURE_NONE', 'CONFIDENCE_INTERVAL', 'ANOMALY_DETECTION', 'TREND', 'HEALTHSCORE']]] = None
    types: Optional[list[Literal['METRIC_TYPE_NONE', 'REQUEST_RATE', 'ERROR_RATE', 'RESPONSE_LATENCY', 'REQUEST_THROUGHPUT', 'RESPONSE_THROUGHPUT', 'ERROR_RATE_3XX', 'ERROR_RATE_4XX', 'ERROR_RATE_5XX', 'RESPONSE_LATENCY_PERCENTILE_50', 'RESPONSE_LATENCY_PERCENTILE_90', 'RESPONSE_LATENCY_PERCENTILE_99', 'RESPONSE_DATA_TRANSFER_DURATION', 'CLIENT_RTT', 'SERVER_RTT', 'SERVER_DATA_TRANSFER_TIME', 'APP_LATENCY', 'REQUEST_TO_ORIGIN_RATE', 'HTTP_REQUEST_RATE', 'HTTP_ERROR_RATE', 'HTTP_ERROR_RATE_4XX', 'HTTP_ERROR_RATE_5XX', 'HTTP_RESPONSE_LATENCY', 'HTTP_RESPONSE_LATENCY_PERCENTILE_50', 'HTTP_RESPONSE_LATENCY_PERCENTILE_90', 'HTTP_RESPONSE_LATENCY_PERCENTILE_99', 'HTTP_SERVER_DATA_TRANSFER_TIME', 'HTTP_APP_LATENCY', 'TCP_CONNECTION_RATE', 'TCP_ERROR_RATE', 'TCP_ERROR_RATE_CLIENT', 'TCP_ERROR_RATE_UPSTREAM', 'TCP_CONNECTION_DURATION']]] = None


class HealthscoreTypeData(F5XCBaseModel):
    """HealthScoreTypeData contains healthscore type and the corresponding value"""

    reason: Optional[str] = None
    type_: Optional[Literal['HEALTHSCORE_NONE', 'HEALTHSCORE_CONNECTIVITY', 'HEALTHSCORE_PERFORMANCE', 'HEALTHSCORE_SECURITY', 'HEALTHSCORE_RELIABILITY', 'HEALTHSCORE_OVERALL']] = Field(default=None, alias="type")
    value: Optional[list[MetricValue]] = None


class HealthscoreData(F5XCBaseModel):
    """Contains the list of healthscores requested by the user."""

    data: Optional[list[HealthscoreTypeData]] = None


class HealthscoreSelector(F5XCBaseModel):
    """Healthscore Selector is used to specify the healthscore types to be..."""

    types: Optional[list[Literal['HEALTHSCORE_NONE', 'HEALTHSCORE_CONNECTIVITY', 'HEALTHSCORE_PERFORMANCE', 'HEALTHSCORE_SECURITY', 'HEALTHSCORE_RELIABILITY', 'HEALTHSCORE_OVERALL']]] = None


class NodeMetricData(F5XCBaseModel):
    """NodeMetricData contains the upstream and downstream metrics for a node."""

    downstream: Optional[list[MetricData]] = None
    upstream: Optional[list[MetricData]] = None


class NodeMetricSelector(F5XCBaseModel):
    """NodeMetricSelector is used to select the metrics that should be returned..."""

    downstream: Optional[list[Literal['METRIC_TYPE_NONE', 'REQUEST_RATE', 'ERROR_RATE', 'RESPONSE_LATENCY', 'REQUEST_THROUGHPUT', 'RESPONSE_THROUGHPUT', 'ERROR_RATE_3XX', 'ERROR_RATE_4XX', 'ERROR_RATE_5XX', 'RESPONSE_LATENCY_PERCENTILE_50', 'RESPONSE_LATENCY_PERCENTILE_90', 'RESPONSE_LATENCY_PERCENTILE_99', 'RESPONSE_DATA_TRANSFER_DURATION', 'CLIENT_RTT', 'SERVER_RTT', 'SERVER_DATA_TRANSFER_TIME', 'APP_LATENCY', 'REQUEST_TO_ORIGIN_RATE', 'HTTP_REQUEST_RATE', 'HTTP_ERROR_RATE', 'HTTP_ERROR_RATE_4XX', 'HTTP_ERROR_RATE_5XX', 'HTTP_RESPONSE_LATENCY', 'HTTP_RESPONSE_LATENCY_PERCENTILE_50', 'HTTP_RESPONSE_LATENCY_PERCENTILE_90', 'HTTP_RESPONSE_LATENCY_PERCENTILE_99', 'HTTP_SERVER_DATA_TRANSFER_TIME', 'HTTP_APP_LATENCY', 'TCP_CONNECTION_RATE', 'TCP_ERROR_RATE', 'TCP_ERROR_RATE_CLIENT', 'TCP_ERROR_RATE_UPSTREAM', 'TCP_CONNECTION_DURATION']]] = None
    features: Optional[list[Literal['TIMESERIES_FEATURE_NONE', 'CONFIDENCE_INTERVAL', 'ANOMALY_DETECTION', 'TREND', 'HEALTHSCORE']]] = None
    upstream: Optional[list[Literal['METRIC_TYPE_NONE', 'REQUEST_RATE', 'ERROR_RATE', 'RESPONSE_LATENCY', 'REQUEST_THROUGHPUT', 'RESPONSE_THROUGHPUT', 'ERROR_RATE_3XX', 'ERROR_RATE_4XX', 'ERROR_RATE_5XX', 'RESPONSE_LATENCY_PERCENTILE_50', 'RESPONSE_LATENCY_PERCENTILE_90', 'RESPONSE_LATENCY_PERCENTILE_99', 'RESPONSE_DATA_TRANSFER_DURATION', 'CLIENT_RTT', 'SERVER_RTT', 'SERVER_DATA_TRANSFER_TIME', 'APP_LATENCY', 'REQUEST_TO_ORIGIN_RATE', 'HTTP_REQUEST_RATE', 'HTTP_ERROR_RATE', 'HTTP_ERROR_RATE_4XX', 'HTTP_ERROR_RATE_5XX', 'HTTP_RESPONSE_LATENCY', 'HTTP_RESPONSE_LATENCY_PERCENTILE_50', 'HTTP_RESPONSE_LATENCY_PERCENTILE_90', 'HTTP_RESPONSE_LATENCY_PERCENTILE_99', 'HTTP_SERVER_DATA_TRANSFER_TIME', 'HTTP_APP_LATENCY', 'TCP_CONNECTION_RATE', 'TCP_ERROR_RATE', 'TCP_ERROR_RATE_CLIENT', 'TCP_ERROR_RATE_UPSTREAM', 'TCP_CONNECTION_DURATION']]] = None


class InstanceId(F5XCBaseModel):
    """Instance Id uniquely identifies a service instance."""

    app_type: Optional[str] = None
    instance: Optional[str] = None
    namespace: Optional[str] = None
    service: Optional[str] = None
    site: Optional[str] = None
    virtual_host: Optional[str] = None


class InstanceRequestId(F5XCBaseModel):
    """Instance request ID to fetch metric from a specific service instance."""

    app_type: Optional[str] = None
    instance: Optional[str] = None
    service: Optional[str] = None
    site: Optional[str] = None
    virtual_host: Optional[str] = None


class AppTypeInfo(F5XCBaseModel):
    """List of application types for a namespace"""

    app_types: Optional[list[str]] = None
    namespace: Optional[str] = None


class AppTypeListResponse(F5XCBaseModel):
    """Response for graph/service/app_types API that returns the list of..."""

    data: Optional[list[AppTypeInfo]] = None


class Id(F5XCBaseModel):
    """Id uniquely identifies a node or an edge in the service graph."""

    app_type: Optional[str] = None
    cacheability: Optional[str] = None
    namespace: Optional[str] = None
    service: Optional[str] = None
    site: Optional[str] = None
    vhost: Optional[str] = None
    vip: Optional[str] = None
    virtual_host_type: Optional[str] = None


class CdnMetricData(F5XCBaseModel):
    """CdnMetricData contains the metric type and the corresponding metric value(s)"""

    type_: Optional[Literal['METRIC_TYPE_NONE', 'REQUEST_RATE', 'ERROR_RATE', 'RESPONSE_LATENCY', 'REQUEST_THROUGHPUT', 'RESPONSE_THROUGHPUT', 'ERROR_RATE_3XX', 'ERROR_RATE_4XX', 'ERROR_RATE_5XX', 'RESPONSE_LATENCY_PERCENTILE_50', 'RESPONSE_LATENCY_PERCENTILE_90', 'RESPONSE_LATENCY_PERCENTILE_99', 'RESPONSE_DATA_TRANSFER_DURATION', 'CLIENT_RTT', 'SERVER_RTT', 'SERVER_DATA_TRANSFER_TIME', 'APP_LATENCY', 'REQUEST_TO_ORIGIN_RATE', 'HTTP_REQUEST_RATE', 'HTTP_ERROR_RATE', 'HTTP_ERROR_RATE_4XX', 'HTTP_ERROR_RATE_5XX', 'HTTP_RESPONSE_LATENCY', 'HTTP_RESPONSE_LATENCY_PERCENTILE_50', 'HTTP_RESPONSE_LATENCY_PERCENTILE_90', 'HTTP_RESPONSE_LATENCY_PERCENTILE_99', 'HTTP_SERVER_DATA_TRANSFER_TIME', 'HTTP_APP_LATENCY', 'TCP_CONNECTION_RATE', 'TCP_ERROR_RATE', 'TCP_ERROR_RATE_CLIENT', 'TCP_ERROR_RATE_UPSTREAM', 'TCP_CONNECTION_DURATION']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None
    value: Optional[list[MetricValue]] = None


class CacheableData(F5XCBaseModel):
    """Cacheable Content Data wraps all the response data for a load balancer"""

    id_: Optional[Id] = Field(default=None, alias="id")
    metric: Optional[list[CdnMetricData]] = None


class EdgeAPIEPData(F5XCBaseModel):
    """Details about the discovered API Endpoints between services. Each..."""

    api_ep: Optional[APIEPInfo] = None
    pdf_info: Optional[APIEPPDFInfo] = None


class EdgeAPIEPSelector(F5XCBaseModel):
    """Selector for API Endpoints"""

    pass


class EdgeFieldData(F5XCBaseModel):
    """EdgeFieldData wraps all the metric and the healthscore data for an edge."""

    api_endpoints: Optional[list[EdgeAPIEPData]] = None
    healthscore: Optional[HealthscoreData] = None
    metric: Optional[EdgeMetricData] = None


class EdgeData(F5XCBaseModel):
    """EdgeData wraps all the response data for an edge in the site graph response."""

    data: Optional[EdgeFieldData] = None
    dst_id: Optional[Id] = None
    src_id: Optional[Id] = None


class EdgeFieldSelector(F5XCBaseModel):
    """EdgeFieldSelector is used to specify the list of fields that should be..."""

    api_endpoint: Optional[Any] = None
    healthscore: Optional[HealthscoreSelector] = None
    metric: Optional[EdgeMetricSelector] = None


class RequestId(F5XCBaseModel):
    """Service request ID to fetch metric for a specific service."""

    app_type: Optional[str] = None
    service: Optional[str] = None
    site: Optional[str] = None
    vip: Optional[str] = None
    virtual_host: Optional[str] = None


class EdgeRequest(F5XCBaseModel):
    """While graph/service API is used to get the service mesh for an app_type,..."""

    dst_id: Optional[RequestId] = None
    end_time: Optional[str] = None
    field_selector: Optional[EdgeFieldSelector] = None
    namespace: Optional[str] = None
    range: Optional[str] = None
    src_id: Optional[RequestId] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class EdgeResponse(F5XCBaseModel):
    """Response for graph/service/edge API returns the time-series data for the..."""

    data: Optional[EdgeFieldData] = None
    step: Optional[str] = None


class NodeFieldData(F5XCBaseModel):
    """NodeFieldData wraps all the metric and the healthscore data for a node."""

    healthscore: Optional[HealthscoreData] = None
    metric: Optional[NodeMetricData] = None


class NodeData(F5XCBaseModel):
    """NodeData wraps all the response data for a node in the site graph response."""

    data: Optional[NodeFieldData] = None
    id_: Optional[Id] = Field(default=None, alias="id")


class GraphData(F5XCBaseModel):
    """GraphData wraps the response for the service graph request that contains..."""

    edges: Optional[list[EdgeData]] = None
    nodes: Optional[list[NodeData]] = None


class InstanceData(F5XCBaseModel):
    """InstanceData wraps all the response data for an instance in the graph response"""

    data: Optional[NodeFieldData] = None
    id_: Optional[InstanceId] = Field(default=None, alias="id")


class NodeFieldSelector(F5XCBaseModel):
    """NodeFieldSelector is used to specify the list of fields that should be..."""

    healthscore: Optional[HealthscoreSelector] = None
    metric: Optional[NodeMetricSelector] = None


class InstanceRequest(F5XCBaseModel):
    """Request to get the time-series data for an instance in the service node."""

    end_time: Optional[str] = None
    field_selector: Optional[NodeFieldSelector] = None
    id_: Optional[InstanceRequestId] = Field(default=None, alias="id")
    namespace: Optional[str] = None
    range: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class InstanceResponse(F5XCBaseModel):
    """Response for graph/service/node/instance API that returns the..."""

    data: Optional[NodeFieldData] = None
    step: Optional[str] = None


class InstancesData(F5XCBaseModel):
    """List of service instances that matched the request"""

    instances: Optional[list[InstanceData]] = None


class LabelFilter(F5XCBaseModel):
    """Metrics used to render the service graph are tagged with labels listed..."""

    label: Optional[Literal['LABEL_NONE', 'LABEL_SITE', 'LABEL_APP_TYPE', 'LABEL_SERVICE', 'LABEL_VHOST_TYPE', 'LABEL_VHOST', 'LABEL_VIP', 'LABEL_VHOST_CACHE']] = None
    op: Optional[Literal['NOP', 'EQ', 'NEQ']] = None
    value: Optional[str] = None


class InstancesRequest(F5XCBaseModel):
    """Request to get instances data for a node in the service graph."""

    end_time: Optional[str] = None
    field_selector: Optional[NodeFieldSelector] = None
    group_by: Optional[list[Literal['NONE', 'NAMESPACE', 'SITE', 'APP_TYPE', 'SERVICE', 'INSTANCE', 'VIRTUAL_HOST']]] = None
    label_filter: Optional[list[LabelFilter]] = None
    namespace: Optional[str] = None
    range: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class InstancesResponse(F5XCBaseModel):
    """Response for graph/service/node/instances API that returns the instances..."""

    data: Optional[InstancesData] = None
    step: Optional[str] = None


class LBCacheContentRequest(F5XCBaseModel):
    """graph/cacheable_content API is used to get data for CDN services."""

    end_time: Optional[str] = None
    field_selector: Optional[list[Literal['METRIC_TYPE_NONE', 'REQUEST_RATE', 'ERROR_RATE', 'RESPONSE_LATENCY', 'REQUEST_THROUGHPUT', 'RESPONSE_THROUGHPUT', 'ERROR_RATE_3XX', 'ERROR_RATE_4XX', 'ERROR_RATE_5XX', 'RESPONSE_LATENCY_PERCENTILE_50', 'RESPONSE_LATENCY_PERCENTILE_90', 'RESPONSE_LATENCY_PERCENTILE_99', 'RESPONSE_DATA_TRANSFER_DURATION', 'CLIENT_RTT', 'SERVER_RTT', 'SERVER_DATA_TRANSFER_TIME', 'APP_LATENCY', 'REQUEST_TO_ORIGIN_RATE', 'HTTP_REQUEST_RATE', 'HTTP_ERROR_RATE', 'HTTP_ERROR_RATE_4XX', 'HTTP_ERROR_RATE_5XX', 'HTTP_RESPONSE_LATENCY', 'HTTP_RESPONSE_LATENCY_PERCENTILE_50', 'HTTP_RESPONSE_LATENCY_PERCENTILE_90', 'HTTP_RESPONSE_LATENCY_PERCENTILE_99', 'HTTP_SERVER_DATA_TRANSFER_TIME', 'HTTP_APP_LATENCY', 'TCP_CONNECTION_RATE', 'TCP_ERROR_RATE', 'TCP_ERROR_RATE_CLIENT', 'TCP_ERROR_RATE_UPSTREAM', 'TCP_CONNECTION_DURATION']]] = None
    group_by: Optional[list[Literal['NONE', 'NAMESPACE', 'SITE', 'APP_TYPE', 'SERVICE', 'VHOST', 'VIRTUAL_HOST_TYPE', 'VIP', 'CACHEABILITY']]] = None
    label_filter: Optional[list[LabelFilter]] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class LBCacheContentResponse(F5XCBaseModel):
    """Response for graph/cacheable_content request contains a list of nodes"""

    nodes: Optional[list[CacheableData]] = None
    step: Optional[str] = None


class NodeRequest(F5XCBaseModel):
    """Request to get time-series data for a node in the service graph. While..."""

    end_time: Optional[str] = None
    field_selector: Optional[NodeFieldSelector] = None
    id_: Optional[RequestId] = Field(default=None, alias="id")
    namespace: Optional[str] = None
    range: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class NodeResponse(F5XCBaseModel):
    """Response for graph/service/node request returns the time-series data for..."""

    data: Optional[NodeFieldData] = None
    step: Optional[str] = None


class Response(F5XCBaseModel):
    """Response for graph/service request contains a list of nodes and edges...."""

    data: Optional[GraphData] = None
    step: Optional[str] = None


# Convenience aliases
Spec = PDFSpec
