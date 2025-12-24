"""Pydantic models for flow."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AnomalyData(F5XCBaseModel):
    """Anomaly Data contains key/value pairs that uniquely identifies the..."""

    anomalous_data_transferred: Optional[str] = None
    anomaly_duration_seconds: Optional[str] = None
    anomaly_level: Optional[Literal['LOW_ANOMALY_LEVEL', 'MEDIUM_ANOMALY_LEVEL', 'HIGH_ANOMALY_LEVEL']] = None
    anomaly_score: Optional[float] = None
    anomaly_start_time: Optional[str] = None
    flow_count: Optional[str] = None
    labels: Optional[dict[str, Any]] = None
    scan_time: Optional[str] = None
    total_data_transferred: Optional[str] = None


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


class FieldData(F5XCBaseModel):
    """Field Data contains key/value pairs that uniquely identifies the..."""

    labels: Optional[dict[str, Any]] = None
    value: Optional[list[MetricValue]] = None


class AnomalyData(F5XCBaseModel):
    anomaly_data: Optional[list[AnomalyData]] = None
    type_: Optional[Literal['BYTES', 'PACKETS', 'DROPPED_PACKETS', 'TX_BYTES', 'TX_PACKETS', 'TX_DROPPED_PACKETS', 'FLOW_COUNT']] = Field(default=None, alias="type")


class Data(F5XCBaseModel):
    """FlowData wraps all the response data"""

    data: Optional[list[FieldData]] = None
    type_: Optional[Literal['BYTES', 'PACKETS', 'DROPPED_PACKETS', 'TX_BYTES', 'TX_PACKETS', 'TX_DROPPED_PACKETS', 'FLOW_COUNT']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None


class SortBy(F5XCBaseModel):
    """Sorting for data by given fields"""

    sort_direction: Optional[Literal['SORT_DIRECTION_DESC', 'SORT_DIRECTION_ASC']] = None
    sort_label: Optional[Literal['SORT_LABEL_NONE', 'SORT_LABEL_BYTES', 'SORT_LABEL_FLOW_COUNT', 'SORT_LABEL_ANOMALY_LEVEL', 'SORT_LABEL_ANOMALY_DURATION']] = None


class SubscribeRequest(F5XCBaseModel):
    """Request to subscribe to Flow Collection"""

    service_type: Optional[Literal['FLOW_COLLECTION', 'FLOW_ANOMALY_DETECTION', 'FLOW_COLLECTION_AND_ANOMALY_DETECTION']] = None


class SubscribeResponse(F5XCBaseModel):
    """Response of subscribe to Flow Collection"""

    flow_anomaly_detection_last_enabled_time: Optional[str] = None
    last_enabled_time: Optional[str] = None


class SubscriptionStatusResponse(F5XCBaseModel):
    """Response of subscription status for Flow Collection"""

    flow_anomaly_detection_last_enabled_time: Optional[str] = None
    flow_anomaly_detection_result: Optional[Literal['AS_NONE', 'AS_PENDING', 'AS_SUBSCRIBED', 'AS_ERROR']] = None
    last_enabled_time: Optional[str] = None
    result: Optional[Literal['AS_NONE', 'AS_PENDING', 'AS_SUBSCRIBED', 'AS_ERROR']] = None


class TopFlowAnomaliesRequest(F5XCBaseModel):
    end_time: Optional[str] = None
    field_selector: Optional[list[Literal['BYTES', 'PACKETS', 'DROPPED_PACKETS', 'TX_BYTES', 'TX_PACKETS', 'TX_DROPPED_PACKETS', 'FLOW_COUNT']]] = None
    filter: Optional[str] = None
    group_by: Optional[list[Literal['SITE', 'SRC_IP', 'SRC_PORT', 'DST_IP', 'DST_PORT', 'PROTOCOL', 'APP_NAME', 'NFV_SERVICE', 'NFV_SERVICE_INSTANCE', 'NFV_SERVICE_INSTANCE_HOSTNAME', 'SRC_SITE', 'DST_SITE', 'SRC_PROVIDER_TYPE', 'DST_PROVIDER_TYPE', 'SRC_SUBNET', 'DST_SUBNET', 'SRC_NETWORK', 'DST_NETWORK', 'CLOUD_CONNECT', 'ANOMALY_LEVEL']]] = None
    limit: Optional[int] = None
    sort_by: Optional[list[SortBy]] = None
    start_time: Optional[str] = None


class TopFlowAnomaliesResponse(F5XCBaseModel):
    flow_anomaly_data: Optional[list[AnomalyData]] = Field(default=None, alias="flowAnomalyData")


class TopTalkersResponse(F5XCBaseModel):
    data: Optional[list[Data]] = None


class UnsubscribeRequest(F5XCBaseModel):
    """Request to unsubscribe to Flow Collection"""

    service_type: Optional[Literal['FLOW_COLLECTION', 'FLOW_ANOMALY_DETECTION', 'FLOW_COLLECTION_AND_ANOMALY_DETECTION']] = None


class UnsubscribeResponse(F5XCBaseModel):
    """Response of unsubscribe to Flow Collection"""

    pass


# Convenience aliases
