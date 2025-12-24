"""Pydantic models for data_delivery."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class DataPoint(F5XCBaseModel):
    """Message object representing data point"""

    timestamp: Optional[str] = None
    value: Optional[float] = None


class DataSet(F5XCBaseModel):
    """Represents the dataset details"""

    description: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None
    status: Optional[str] = None


class EventsReason(F5XCBaseModel):
    """Message object representing events reason"""

    category: Optional[str] = None
    events_count: Optional[int] = Field(default=None, alias="eventsCount")
    events_percentage: Optional[float] = Field(default=None, alias="eventsPercentage")
    reason: Optional[str] = None


class Feature(F5XCBaseModel):
    """Definition of feature which is unit of dataset"""

    data_format: Optional[str] = None
    description: Optional[str] = None
    feature_name: Optional[str] = None
    is_new_field: Optional[bool] = None
    notes: Optional[str] = None
    required: Optional[bool] = None


class FlowLabel(F5XCBaseModel):
    """message representing flow label information"""

    flow_label: Optional[str] = Field(default=None, alias="flowLabel")
    platform: Optional[str] = None


class GetDataDictionaryResponse(F5XCBaseModel):
    """dataset feature fetched  by data dictionary API"""

    feature_list: Optional[list[Feature]] = None


class GetDataSetsResponse(F5XCBaseModel):
    """x-example: 'DI Advanced' List of Data Sets eligible for the tenant"""

    data_sets: Optional[list[str]] = Field(default=None, alias="dataSets")


class Series(F5XCBaseModel):
    """Message object representing series"""

    data: Optional[list[DataPoint]] = None
    name: Optional[str] = None


class LineChartData(F5XCBaseModel):
    """Message object representing line chart data"""

    granularity: Optional[str] = None
    series: Optional[list[Series]] = None


class ListDataSetsResponse(F5XCBaseModel):
    """Response of list datasets by tenant"""

    dataset_list: Optional[list[DataSet]] = None


class ListFlowLabelsResponse(F5XCBaseModel):
    """Response object to list flow labels"""

    flow_labels: Optional[list[FlowLabel]] = Field(default=None, alias="flowLabels")


class LoadExecutiveSummaryRequest(F5XCBaseModel):
    """Request object to get executive summary of DI premium customer"""

    anomalous_score_percentile: Optional[float] = Field(default=None, alias="anomalousScorePercentile")
    flow_labels: Optional[list[FlowLabel]] = Field(default=None, alias="flowLabels")
    granularity: Optional[str] = None
    namespace: Optional[str] = None
    platform: Optional[str] = None
    time_range: Optional[str] = Field(default=None, alias="timeRange")
    timestamp: Optional[str] = None


class SummaryPanel(F5XCBaseModel):
    """Message object representing summary panel"""

    anomalous_devices: Optional[int] = Field(default=None, alias="anomalousDevices")
    anomalous_devices_percentage: Optional[float] = Field(default=None, alias="anomalousDevicesPercentage")
    anomalous_max_score: Optional[float] = Field(default=None, alias="anomalousMaxScore")
    anomalous_min_score: Optional[float] = Field(default=None, alias="anomalousMinScore")
    anomalous_percentage: Optional[float] = Field(default=None, alias="anomalousPercentage")
    anomalous_transactions: Optional[int] = Field(default=None, alias="anomalousTransactions")
    bot_percentage: Optional[float] = Field(default=None, alias="botPercentage")
    bot_transactions: Optional[int] = Field(default=None, alias="botTransactions")
    total_evaluated_devices: Optional[int] = Field(default=None, alias="totalEvaluatedDevices")
    total_evaluated_transactions: Optional[int] = Field(default=None, alias="totalEvaluatedTransactions")


class LoadExecutiveSummaryResponse(F5XCBaseModel):
    """Response object to get executive summary of DI premium customer"""

    events_reasons: Optional[list[EventsReason]] = Field(default=None, alias="eventsReasons")
    line_chart_data: Optional[LineChartData] = Field(default=None, alias="lineChartData")
    summary: Optional[SummaryPanel] = None


class TestReceiverRequest(F5XCBaseModel):
    """Request to test receiver & destination sink"""

    id_: Optional[str] = Field(default=None, alias="id")
    namespace: Optional[str] = None


class TestReceiverResponse(F5XCBaseModel):
    """Response for the Receiver test request; empty because the only returned..."""

    message: Optional[str] = None
    status: Optional[Literal['SUCCESS', 'FAILED']] = None


class UpdateReceiverStatusRequest(F5XCBaseModel):
    """Request to update"""

    id_: Optional[str] = Field(default=None, alias="id")
    namespace: Optional[str] = None
    type_: Optional[Literal['DISABLE', 'ENABLE']] = Field(default=None, alias="type")


class UpdateReceiverStatusResponse(F5XCBaseModel):
    """Payload about status of receiver status result"""

    id_: Optional[str] = Field(default=None, alias="id")
    receiver_name: Optional[str] = None
    status: Optional[str] = None


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
    title: Optional[str] = None
    value: Optional[str] = None


class SuggestValuesResp(F5XCBaseModel):
    """Response body of SuggestValues request"""

    items: Optional[list[SuggestedItem]] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


# Convenience aliases
