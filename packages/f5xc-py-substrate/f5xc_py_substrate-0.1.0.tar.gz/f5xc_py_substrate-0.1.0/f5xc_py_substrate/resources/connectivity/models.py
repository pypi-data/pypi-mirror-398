"""Pydantic models for connectivity."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class Id(F5XCBaseModel):
    """Id uniquely identifies a node or an edge in the connectivity graph."""

    site: Optional[str] = None
    site_type: Optional[Literal['INVALID', 'REGIONAL_EDGE', 'CUSTOMER_EDGE', 'NGINX_ONE']] = None


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


class HealthscoreTypeData(F5XCBaseModel):
    """HealthScoreTypeData contains healthscore type and the corresponding value"""

    reason: Optional[str] = None
    type_: Optional[Literal['HEALTHSCORE_NONE', 'HEALTHSCORE_CONNECTIVITY', 'HEALTHSCORE_PERFORMANCE', 'HEALTHSCORE_SECURITY', 'HEALTHSCORE_RELIABILITY', 'HEALTHSCORE_OVERALL']] = Field(default=None, alias="type")
    value: Optional[list[MetricValue]] = None


class HealthscoreData(F5XCBaseModel):
    """Contains the list of healthscores requested by the user."""

    data: Optional[list[HealthscoreTypeData]] = None


class MetricFeatureData(F5XCBaseModel):
    """Contains metric values for timeseries features specified in the request."""

    anomaly: Optional[list[MetricValue]] = None
    confidence_lower_bound: Optional[list[MetricValue]] = None
    confidence_upper_bound: Optional[list[MetricValue]] = None
    healthscore: Optional[list[MetricValue]] = None
    raw: Optional[list[MetricValue]] = None
    trend: Optional[list[MetricValue]] = None


class EdgeMetricData(F5XCBaseModel):
    """EdgeMetricData contains the metric type and the corresponding metric value."""

    type_: Optional[Literal['EDGE_METRIC_TYPE_NONE', 'EDGE_REACHABILITY', 'EDGE_LATENCY', 'EDGE_IN_THROUGHPUT', 'EDGE_OUT_THROUGHPUT', 'EDGE_IN_DROP_RATE', 'EDGE_OUT_DROP_RATE', 'EDGE_CONNECTION_STATUS', 'EDGE_ARES_CONNECTION_STATUS', 'EDGE_DATA_PLANE_CONNECTION_STATUS', 'EDGE_CONTROL_PLANE_CONNECTION_STATUS']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None
    value: Optional[MetricFeatureData] = None


class EdgeData(F5XCBaseModel):
    """EdgeData wraps all the response data for an edge in the connectivity..."""

    dst_id: Optional[Id] = None
    healthscore: Optional[HealthscoreData] = None
    metric: Optional[list[EdgeMetricData]] = None
    src_id: Optional[Id] = None


class HealthscoreSelector(F5XCBaseModel):
    """Healthscore Selector is used to specify the healthscore types to be..."""

    types: Optional[list[Literal['HEALTHSCORE_NONE', 'HEALTHSCORE_CONNECTIVITY', 'HEALTHSCORE_PERFORMANCE', 'HEALTHSCORE_SECURITY', 'HEALTHSCORE_RELIABILITY', 'HEALTHSCORE_OVERALL']]] = None


class EdgeMetricSelector(F5XCBaseModel):
    """EdgeMetricSelector is used to select the metrics that should be returned..."""

    features: Optional[list[Literal['TIMESERIES_FEATURE_NONE', 'CONFIDENCE_INTERVAL', 'ANOMALY_DETECTION', 'TREND', 'HEALTHSCORE']]] = None
    types: Optional[list[Literal['EDGE_METRIC_TYPE_NONE', 'EDGE_REACHABILITY', 'EDGE_LATENCY', 'EDGE_IN_THROUGHPUT', 'EDGE_OUT_THROUGHPUT', 'EDGE_IN_DROP_RATE', 'EDGE_OUT_DROP_RATE', 'EDGE_CONNECTION_STATUS', 'EDGE_ARES_CONNECTION_STATUS', 'EDGE_DATA_PLANE_CONNECTION_STATUS', 'EDGE_CONTROL_PLANE_CONNECTION_STATUS']]] = None


class EdgeFieldSelector(F5XCBaseModel):
    """EdgeFieldSelector is used to specify the list of fields that should be..."""

    healthscore: Optional[HealthscoreSelector] = None
    metric: Optional[EdgeMetricSelector] = None


class EdgeRequest(F5XCBaseModel):
    """Request to get the time-series data for an edge in the connectivity..."""

    dst_id: Optional[Id] = None
    end_time: Optional[str] = None
    field_selector: Optional[EdgeFieldSelector] = None
    namespace: Optional[str] = None
    range: Optional[str] = None
    src_id: Optional[Id] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class EdgeResponse(F5XCBaseModel):
    """Response for graph/connectivity/edge API returns the time-series data..."""

    data: Optional[EdgeData] = None
    step: Optional[str] = None


class NodeMetricSelector(F5XCBaseModel):
    """NodeMetricSelector is used to select the metrics that should be returned..."""

    features: Optional[list[Literal['TIMESERIES_FEATURE_NONE', 'CONFIDENCE_INTERVAL', 'ANOMALY_DETECTION', 'TREND', 'HEALTHSCORE']]] = None
    instances: Optional[list[Literal['NODE_INSTANCE_METRIC_TYPE_NONE', 'NODE_INSTANCE_CPU_USAGE', 'NODE_INSTANCE_MEMORY_USAGE', 'NODE_INSTANCE_DISK_USAGE', 'NODE_INSTANCE_GPU_TEMPERATURE', 'NODE_INSTANCE_GPU_TX_THROUGHPUT', 'NODE_INSTANCE_GPU_RX_THROUGHPUT', 'NODE_INSTANCE_GPU_USAGE', 'NODE_INSTANCE_STATUS', 'NODE_INSTANCE_CPU_USAGE_EXTERNAL']]] = None
    interfaces: Optional[list[Literal['NODE_IF_METRIC_TYPE_NONE', 'NODE_IF_STATUS', 'NODE_IF_IN_THROUGHPUT', 'NODE_IF_OUT_THROUGHPUT', 'NODE_IF_IN_DROP_RATE', 'NODE_IF_OUT_DROP_RATE']]] = None
    types: Optional[list[Literal['NODE_METRIC_TYPE_NONE', 'NODE_IN_THROUGHPUT', 'NODE_OUT_THROUGHPUT', 'NODE_IN_DROP_RATE', 'NODE_OUT_DROP_RATE', 'NODE_DEPLOYMENT_COUNT', 'NODE_POD_COUNT', 'NODE_REACHABILITY', 'NODE_CONNECTION_STATUS', 'NODE_ARES_CONNECTION_STATUS', 'NODE_DATA_PLANE_CONNECTION_STATUS', 'NODE_CONTROL_PLANE_CONNECTION_STATUS', 'NODE_LOCAL_CONTROL_PLANE_CONNECTION_STATUS']]] = None


class NodeFieldSelector(F5XCBaseModel):
    """NodeFieldSelector is used to specify the list of fields that should be..."""

    healthscore: Optional[HealthscoreSelector] = None
    metric: Optional[NodeMetricSelector] = None


class FieldSelector(F5XCBaseModel):
    """FieldSelector is used to specify the list of fields to be returned in..."""

    edge: Optional[EdgeFieldSelector] = None
    node: Optional[NodeFieldSelector] = None


class LabelFilter(F5XCBaseModel):
    """Metrics used in the connectivity graph are tagged with labels listed in..."""

    label: Optional[Literal['LABEL_NONE', 'LABEL_SITE', 'LABEL_NETWORK_TYPE', 'LABEL_INTERFACE_TYPE', 'LABEL_CONNECTIVITY_TYPE']] = None
    op: Optional[Literal['NOP', 'EQ', 'NEQ']] = None
    value: Optional[str] = None


class NodeInstanceMetricData(F5XCBaseModel):
    """NodeInstanceMetricData contains the metric type and the corresponding..."""

    type_: Optional[Literal['NODE_INSTANCE_METRIC_TYPE_NONE', 'NODE_INSTANCE_CPU_USAGE', 'NODE_INSTANCE_MEMORY_USAGE', 'NODE_INSTANCE_DISK_USAGE', 'NODE_INSTANCE_GPU_TEMPERATURE', 'NODE_INSTANCE_GPU_TX_THROUGHPUT', 'NODE_INSTANCE_GPU_RX_THROUGHPUT', 'NODE_INSTANCE_GPU_USAGE', 'NODE_INSTANCE_STATUS', 'NODE_INSTANCE_CPU_USAGE_EXTERNAL']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None
    value: Optional[MetricFeatureData] = None


class NodeInstanceData(F5XCBaseModel):
    """NodeInstanceData is part of the connectivity graph response that..."""

    id_: Optional[str] = Field(default=None, alias="id")
    metric: Optional[list[NodeInstanceMetricData]] = None


class NodeInterfaceMetricData(F5XCBaseModel):
    """NodeInterfaceMetricData contains the metric type and the corresponding..."""

    type_: Optional[Literal['NODE_IF_METRIC_TYPE_NONE', 'NODE_IF_STATUS', 'NODE_IF_IN_THROUGHPUT', 'NODE_IF_OUT_THROUGHPUT', 'NODE_IF_IN_DROP_RATE', 'NODE_IF_OUT_DROP_RATE']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None
    value: Optional[MetricFeatureData] = None


class NodeInterfaceData(F5XCBaseModel):
    """NodeInterfaceData is part of the connectivity graph response that..."""

    id_: Optional[str] = Field(default=None, alias="id")
    metric: Optional[list[NodeInterfaceMetricData]] = None
    network_type: Optional[str] = None
    segment_name: Optional[str] = None


class NodeMetricData(F5XCBaseModel):
    """NodeMetricData contains metric type and the corresponding value for a node"""

    type_: Optional[Literal['NODE_METRIC_TYPE_NONE', 'NODE_IN_THROUGHPUT', 'NODE_OUT_THROUGHPUT', 'NODE_IN_DROP_RATE', 'NODE_OUT_DROP_RATE', 'NODE_DEPLOYMENT_COUNT', 'NODE_POD_COUNT', 'NODE_REACHABILITY', 'NODE_CONNECTION_STATUS', 'NODE_ARES_CONNECTION_STATUS', 'NODE_DATA_PLANE_CONNECTION_STATUS', 'NODE_CONTROL_PLANE_CONNECTION_STATUS', 'NODE_LOCAL_CONTROL_PLANE_CONNECTION_STATUS']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None
    value: Optional[MetricFeatureData] = None


class NodeData(F5XCBaseModel):
    """NodeData wraps all the response data for a node in the connectivity..."""

    healthscore: Optional[HealthscoreData] = None
    id_: Optional[Id] = Field(default=None, alias="id")
    instances: Optional[list[NodeInstanceData]] = None
    interfaces: Optional[list[NodeInterfaceData]] = None
    metric: Optional[list[NodeMetricData]] = None


class NodeRequest(F5XCBaseModel):
    """Request to get time-series data for a node in the connectivity graph...."""

    end_time: Optional[str] = None
    field_selector: Optional[NodeFieldSelector] = None
    id_: Optional[Id] = Field(default=None, alias="id")
    label_filter: Optional[list[LabelFilter]] = None
    namespace: Optional[str] = None
    range: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class NodeResponse(F5XCBaseModel):
    """Response for graph/connectivity/node API returns the time-series data..."""

    data: Optional[NodeData] = None
    step: Optional[str] = None


class Request(F5XCBaseModel):
    """graph/connectivity API is used to get the reachability, throughput and..."""

    end_time: Optional[str] = None
    field_selector: Optional[FieldSelector] = None
    group_by: Optional[list[Literal['NONE', 'SITE']]] = None
    label_filter: Optional[list[LabelFilter]] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None


class Response(F5XCBaseModel):
    """Response for graph/connectivity API contains list of nodes and edges...."""

    edges: Optional[list[EdgeData]] = None
    nodes: Optional[list[NodeData]] = None


# Convenience aliases
