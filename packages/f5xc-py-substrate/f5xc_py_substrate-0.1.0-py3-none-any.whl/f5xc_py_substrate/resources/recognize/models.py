"""Pydantic models for recognize."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ChannelMWItem(F5XCBaseModel):
    """Enjoy Login Item prevFailedLogin or total"""

    mobile: Optional[float] = None
    web: Optional[float] = None


class ChannelItem(F5XCBaseModel):
    """Channel Item that represent the data to chart"""

    obsolete2_date: Optional[int] = Field(default=None, alias="OBSOLETE2_date")
    obsolete_date: Optional[str] = Field(default=None, alias="OBSOLETE_date")
    date: Optional[float] = None
    first_time: Optional[ChannelMWItem] = Field(default=None, alias="firstTime")
    total: Optional[ChannelMWItem] = None


class ChannelData(F5XCBaseModel):
    """Channel Data that represent the data to chart"""

    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    items: Optional[list[ChannelItem]] = None
    total_items: Optional[int] = Field(default=None, alias="totalItems")


class ChannelRequest(F5XCBaseModel):
    """Since and to times to generate the Channel Request"""

    end_time: Optional[str] = Field(default=None, alias="endTime")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    start_time: Optional[str] = Field(default=None, alias="startTime")


class ChannelResponse(F5XCBaseModel):
    """The data of Chanel Response Chart"""

    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    data: Optional[ChannelData] = None
    id_: Optional[str] = Field(default=None, alias="id")


class ConversionItem(F5XCBaseModel):
    """Conversion Item that represent the data to chart"""

    obsolete2_date: Optional[int] = Field(default=None, alias="OBSOLETE2_date")
    obsolete_date: Optional[str] = Field(default=None, alias="OBSOLETE_date")
    count: Optional[float] = None
    date: Optional[float] = None


class ConversionData(F5XCBaseModel):
    """Conversion Data that represent all the data to fill the chart"""

    avg_daily_conversion: Optional[float] = Field(default=None, alias="avgDailyConversion")
    avg_monthly_conversion: Optional[float] = Field(default=None, alias="avgMonthlyConversion")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    items: Optional[list[ConversionItem]] = None
    kind: Optional[str] = None
    projection_annual_conversion: Optional[float] = Field(default=None, alias="projectionAnnualConversion")
    projection_start_time: Optional[float] = Field(default=None, alias="projectionStartTime")
    total_items: Optional[int] = Field(default=None, alias="totalItems")
    year_to_date_conversion: Optional[float] = Field(default=None, alias="yearToDateConversion")


class ConversionRequest(F5XCBaseModel):
    """Since and to times to generate the Conversion request"""

    agent: Optional[str] = None
    end_time: Optional[str] = Field(default=None, alias="endTime")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    start_time: Optional[str] = Field(default=None, alias="startTime")
    tenant: Optional[str] = None


class ConversionResponse(F5XCBaseModel):
    """The data of Conversion Response Chart"""

    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    data: Optional[ConversionData] = None
    id_: Optional[str] = Field(default=None, alias="id")


class EnjoyLoginItem(F5XCBaseModel):
    """Enjoy Login Item prevFailedLogin or total"""

    converted: Optional[float] = None
    not_converted: Optional[float] = Field(default=None, alias="notConverted")


class EnjoyItem(F5XCBaseModel):
    """Enjoy Item that represent the data to chart"""

    obsolete2_date: Optional[int] = Field(default=None, alias="OBSOLETE2_date")
    obsolete_date: Optional[str] = Field(default=None, alias="OBSOLETE_date")
    date: Optional[float] = None
    prev_failed_login: Optional[EnjoyLoginItem] = Field(default=None, alias="prevFailedLogin")
    total: Optional[EnjoyLoginItem] = None


class EnjoyData(F5XCBaseModel):
    """Enjoy Data that represent the data to chart"""

    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    items: Optional[list[EnjoyItem]] = None
    total_items: Optional[int] = Field(default=None, alias="totalItems")


class EnjoyRequest(F5XCBaseModel):
    """Since and to times to generate the Enjoy Request"""

    end_time: Optional[str] = Field(default=None, alias="endTime")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    start_time: Optional[str] = Field(default=None, alias="startTime")


class EnjoyResponse(F5XCBaseModel):
    """The data of Enjoy Response Chart"""

    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    data: Optional[EnjoyData] = None
    id_: Optional[str] = Field(default=None, alias="id")


class FrictionAggregationItem(F5XCBaseModel):
    """Friction Aggregation Spareable Item data to fill the chart"""

    final_success: Optional[float] = Field(default=None, alias="finalSuccess")
    first_success: Optional[float] = Field(default=None, alias="firstSuccess")
    no_success: Optional[float] = Field(default=None, alias="noSuccess")
    upper_bound: Optional[float] = Field(default=None, alias="upperBound")


class FrictionAggregationData(F5XCBaseModel):
    """Friction Aggregation Data that represent the data to chart"""

    final_success_total: Optional[float] = Field(default=None, alias="finalSuccessTotal")
    first_success_total: Optional[float] = Field(default=None, alias="firstSuccessTotal")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    no_success_total: Optional[float] = Field(default=None, alias="noSuccessTotal")
    spareables: Optional[list[FrictionAggregationItem]] = None
    total_items: Optional[float] = Field(default=None, alias="totalItems")


class FrictionAggregationRequest(F5XCBaseModel):
    """Since and to times to generate the Friction Aggregation Request"""

    end_time: Optional[str] = Field(default=None, alias="endTime")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    start_time: Optional[str] = Field(default=None, alias="startTime")


class FrictionAggregationResponse(F5XCBaseModel):
    """The data of Friction Aggregation Response Chart"""

    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    data: Optional[FrictionAggregationData] = None
    id_: Optional[str] = Field(default=None, alias="id")


class FrictionHistogramItem(F5XCBaseModel):
    """Friction Histogram Spareable Item data to fill the chart"""

    obsolete2_date: Optional[int] = Field(default=None, alias="OBSOLETE2_date")
    obsolete_date: Optional[str] = Field(default=None, alias="OBSOLETE_date")
    date: Optional[float] = None
    direct_reset_pw: Optional[float] = Field(default=None, alias="directResetPw")
    final_success: Optional[float] = Field(default=None, alias="finalSuccess")
    first_success: Optional[float] = Field(default=None, alias="firstSuccess")
    login_fail_reset_pw: Optional[float] = Field(default=None, alias="loginFailResetPw")
    no_success: Optional[float] = Field(default=None, alias="noSuccess")
    non_recog_user: Optional[float] = Field(default=None, alias="nonRecogUser")
    recog_user: Optional[float] = Field(default=None, alias="recogUser")


class FrictionHistogramData(F5XCBaseModel):
    """Friction Histogram Data that represent the data to chart"""

    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    items: Optional[list[FrictionHistogramItem]] = None
    total_items: Optional[float] = Field(default=None, alias="totalItems")


class FrictionHistogramRequest(F5XCBaseModel):
    """Since and to times to generate the Friction Histogram Request"""

    end_time: Optional[str] = Field(default=None, alias="endTime")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    start_time: Optional[str] = Field(default=None, alias="startTime")


class FrictionHistogramResponse(F5XCBaseModel):
    """The data of Friction Histogram Response"""

    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    data: Optional[FrictionHistogramData] = None
    id_: Optional[str] = Field(default=None, alias="id")


class GetStatusProvisionResponse(F5XCBaseModel):
    """Provision struct response GetStatusProvisionResponse"""

    code: Optional[float] = None
    status: Optional[str] = None


class GetStatusResponse(F5XCBaseModel):
    """Any payload to be return by Get Provision API"""

    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    bid: Optional[str] = None
    data: Optional[GetStatusProvisionResponse] = None
    id_: Optional[str] = Field(default=None, alias="id")
    src: Optional[str] = None
    tag: Optional[str] = None


class HealthResponse(F5XCBaseModel):
    """HealthResponse"""

    message: Optional[str] = None


class LiftControlItem(F5XCBaseModel):
    """Lift Control Item absolute or relative"""

    control: Optional[float] = None
    extended: Optional[float] = None


class LiftItem(F5XCBaseModel):
    """Lift Item that represent the data to chart"""

    obsolete2_date: Optional[int] = Field(default=None, alias="OBSOLETE2_date")
    obsolete_date: Optional[str] = Field(default=None, alias="OBSOLETE_date")
    absolute: Optional[LiftControlItem] = None
    date: Optional[float] = None
    relative: Optional[LiftControlItem] = None


class LiftData(F5XCBaseModel):
    """Lift Data that represent the data to chart"""

    avg_absolute_lift: Optional[float] = Field(default=None, alias="avgAbsoluteLift")
    avg_relative_lift: Optional[float] = Field(default=None, alias="avgRelativeLift")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    items: Optional[list[LiftItem]] = None
    total_items: Optional[int] = Field(default=None, alias="totalItems")


class LiftRequest(F5XCBaseModel):
    """Since and to times to generate the Lift Request"""

    end_time: Optional[str] = Field(default=None, alias="endTime")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    start_time: Optional[str] = Field(default=None, alias="startTime")


class LiftResponse(F5XCBaseModel):
    """The data of Lift Response Chart"""

    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    data: Optional[LiftData] = None
    id_: Optional[str] = Field(default=None, alias="id")


class RescueItem(F5XCBaseModel):
    """Conversion Item that represent the data to chart"""

    obsolete2_upper_bound: Optional[int] = Field(default=None, alias="OBSOLETE2_upperBound")
    obsolote_upper_bound: Optional[str] = Field(default=None, alias="OBSOLOTE_upperBound")
    upper_bound: Optional[float] = Field(default=None, alias="upperBound")
    value: Optional[float] = None


class RescueData(F5XCBaseModel):
    """Rescue Data that represent all the data to fill the chart"""

    obsolete2_end_time: Optional[int] = Field(default=None, alias="OBSOLETE2_endTime")
    obsolete2_start_time: Optional[int] = Field(default=None, alias="OBSOLETE2_startTime")
    obsolete_end_time: Optional[str] = Field(default=None, alias="OBSOLETE_endTime")
    obsolete_start_time: Optional[str] = Field(default=None, alias="OBSOLETE_startTime")
    abandon_login_count: Optional[float] = Field(default=None, alias="abandonLoginCount")
    end_time: Optional[float] = Field(default=None, alias="endTime")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    items: Optional[list[RescueItem]] = None
    kind: Optional[str] = None
    no_benefit: Optional[float] = Field(default=None, alias="noBenefit")
    start_time: Optional[float] = Field(default=None, alias="startTime")
    total_items: Optional[int] = Field(default=None, alias="totalItems")


class RescueRequest(F5XCBaseModel):
    """Since and to times to generate the Rescue Request"""

    end_time: Optional[str] = Field(default=None, alias="endTime")
    item_unit: Optional[str] = Field(default=None, alias="itemUnit")
    start_time: Optional[str] = Field(default=None, alias="startTime")


class RescueResponse(F5XCBaseModel):
    """The data of Rescue Response Chart"""

    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    data: Optional[RescueData] = None
    id_: Optional[str] = Field(default=None, alias="id")


class StateData(F5XCBaseModel):
    """The data of State Data"""

    obsolete2_js_detected_time: Optional[str] = Field(default=None, alias="OBSOLETE2_jsDetectedTime")
    obsolete2_recommendation_consumption_time: Optional[str] = Field(default=None, alias="OBSOLETE2_recommendationConsumptionTime")
    obsolete_js_detected_time: Optional[str] = Field(default=None, alias="OBSOLETE_jsDetectedTime")
    obsolete_recommendation_consumption_time: Optional[str] = Field(default=None, alias="OBSOLETE_recommendationConsumptionTime")
    code: Optional[int] = None
    dashboard_state: Optional[str] = Field(default=None, alias="dashboardState")
    js_detected_time: Optional[float] = Field(default=None, alias="jsDetectedTime")
    recommendation_consumption_time: Optional[float] = Field(default=None, alias="recommendationConsumptionTime")


class StateResponse(F5XCBaseModel):
    """The data of State Response"""

    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    data: Optional[StateData] = None
    id_: Optional[str] = Field(default=None, alias="id")


class SubscribeRequest(F5XCBaseModel):
    """Any payload to be passed on the Subscribe API"""

    pass


class SubscribeResponse(F5XCBaseModel):
    """Any payload to be returned by Subscribe API"""

    pass


class TopReasonCodesData(F5XCBaseModel):
    """Top Reason Codes Data that represent all the data to fill the chart"""

    loe: Optional[float] = Field(default=None, alias="LOE")
    lsbh: Optional[float] = Field(default=None, alias="LSBH")
    mud: Optional[float] = Field(default=None, alias="MUD")
    sh: Optional[float] = Field(default=None, alias="SH")
    prev_total: Optional[float] = Field(default=None, alias="prevTotal")


class TopReasonCodesRequest(F5XCBaseModel):
    """Top Reason Codes Request"""

    end_time: Optional[str] = Field(default=None, alias="endTime")
    start_time: Optional[str] = Field(default=None, alias="startTime")


class TopReasonCodesResponse(F5XCBaseModel):
    """The data of Top Reason Codes Response"""

    api_version: Optional[str] = Field(default=None, alias="apiVersion")
    data: Optional[TopReasonCodesData] = None
    id_: Optional[str] = Field(default=None, alias="id")


class UnsubscribeRequest(F5XCBaseModel):
    """Any payload to be passed on the Unsubscribe API"""

    pass


class UnsubscribeResponse(F5XCBaseModel):
    """Any payload to be returned by Unsubscribe API"""

    pass


class ValidateSrcTagInjectionRequest(F5XCBaseModel):
    """Request to verify shape recognize src tag injection"""

    src: Optional[str] = None
    url: Optional[str] = None


class ValidateSrcTagInjectionResponse(F5XCBaseModel):
    """Response to indicate whether customer webpage has custom script tag to..."""

    is_injected: Optional[bool] = Field(default=None, alias="isInjected")
    message: Optional[str] = None


# Convenience aliases
