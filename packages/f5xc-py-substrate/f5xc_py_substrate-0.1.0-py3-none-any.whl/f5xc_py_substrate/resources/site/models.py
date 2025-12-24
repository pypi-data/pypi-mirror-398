"""Pydantic models for site."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


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


class EdgeFieldData(F5XCBaseModel):
    """EdgeFieldData wraps all the metric and the healthscore data for an edge."""

    healthscore: Optional[HealthscoreData] = None
    metric: Optional[EdgeMetricData] = None


class Id(F5XCBaseModel):
    """Id uniquely identifies a node or an edge in the site graph."""

    site: Optional[str] = None


class EdgeData(F5XCBaseModel):
    """EdgeData wraps all the response data for an edge in the site graph response."""

    data: Optional[EdgeFieldData] = None
    dst_id: Optional[Id] = None
    src_id: Optional[Id] = None


class EdgeFieldSelector(F5XCBaseModel):
    """EdgeFieldSelector is used to specify the list of fields that should be..."""

    healthscore: Optional[HealthscoreSelector] = None
    metric: Optional[EdgeMetricSelector] = None


class EdgeRequest(F5XCBaseModel):
    """Request to get the time-series data for an edge in the site graph. While..."""

    dst_id: Optional[Id] = None
    end_time: Optional[str] = None
    field_selector: Optional[EdgeFieldSelector] = None
    namespace: Optional[str] = None
    range: Optional[str] = None
    src_id: Optional[Id] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class EdgeResponse(F5XCBaseModel):
    """Response for graph/site/edge API returns the time-series data for the..."""

    data: Optional[EdgeFieldData] = None
    step: Optional[str] = None


class NodeFieldSelector(F5XCBaseModel):
    """NodeFieldSelector is used to specify the list of fields that should be..."""

    healthscore: Optional[HealthscoreSelector] = None
    metric: Optional[NodeMetricSelector] = None


class FieldSelector(F5XCBaseModel):
    """FieldSelector is used to specify the list of fields to be returned in..."""

    edge: Optional[EdgeFieldSelector] = None
    node: Optional[NodeFieldSelector] = None


class NodeFieldData(F5XCBaseModel):
    """NodeFieldData wraps all the metric and the healthscore data for a node."""

    healthscore: Optional[HealthscoreData] = None
    metric: Optional[NodeMetricData] = None


class NodeData(F5XCBaseModel):
    """NodeData wraps all the response data for a node in the site graph response."""

    data: Optional[NodeFieldData] = None
    id_: Optional[Id] = Field(default=None, alias="id")


class GraphData(F5XCBaseModel):
    """GraphData wraps the response for the site graph request that contains..."""

    edges: Optional[list[EdgeData]] = None
    nodes: Optional[list[NodeData]] = None


class LabelFilter(F5XCBaseModel):
    """Metrics used to render the site graph are tagged with labels listed in..."""

    label: Optional[Literal['LABEL_NONE', 'LABEL_SITE']] = None
    op: Optional[Literal['NOP', 'EQ', 'NEQ']] = None
    value: Optional[str] = None


class NodeRequest(F5XCBaseModel):
    """Request to get time-series data for a node in the site graph. While..."""

    end_time: Optional[str] = None
    field_selector: Optional[NodeFieldSelector] = None
    id_: Optional[Id] = Field(default=None, alias="id")
    namespace: Optional[str] = None
    range: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class NodeResponse(F5XCBaseModel):
    """Response for graph/site/node request returns the time-series data for..."""

    data: Optional[NodeFieldData] = None
    step: Optional[str] = None


class Request(F5XCBaseModel):
    """graph/site API is used to get intra-site and inter-site graph for..."""

    end_time: Optional[str] = None
    field_selector: Optional[FieldSelector] = None
    group_by: Optional[list[Literal['NONE', 'SITE']]] = None
    label_filter: Optional[list[LabelFilter]] = None
    namespace: Optional[str] = None
    range: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class Response(F5XCBaseModel):
    """Response for graph/site API contains list of nodes and edges. Each node..."""

    data: Optional[GraphData] = None
    step: Optional[str] = None


# Convenience aliases
