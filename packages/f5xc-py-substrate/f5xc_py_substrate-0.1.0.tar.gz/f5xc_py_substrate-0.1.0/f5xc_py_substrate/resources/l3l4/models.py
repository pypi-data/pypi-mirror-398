"""Pydantic models for l3l4."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class L3l4ByApplicationRequest(F5XCBaseModel):
    """Used to display Application (aka protocol) by tenant"""

    end_time: Optional[str] = None
    namespace: Optional[str] = None
    network_id: Optional[str] = None
    start_time: Optional[str] = None
    traffic_unit: Optional[Literal['TrafficUnitUnknown', 'TrafficUnitBps', 'TrafficUnitPps']] = None


class L3l4L3L4GraphValue(F5XCBaseModel):
    """Each metric value consists of a timestamp and a value. Timestamp in the..."""

    timestamp: Optional[str] = None
    value: Optional[str] = None


class L3l4L3L4Metric(F5XCBaseModel):
    name: Optional[str] = None
    values: Optional[list[L3l4L3L4GraphValue]] = None


class L3l4ByApplicationResponse(F5XCBaseModel):
    """Response for Application Traffic"""

    in_: Optional[list[L3l4L3L4Metric]] = Field(default=None, alias="in")
    out: Optional[list[L3l4L3L4Metric]] = None


class L3l4ByMitigationRequest(F5XCBaseModel):
    """Used to display Zone by tenant"""

    end_time: Optional[str] = None
    mitigation_id: Optional[str] = None
    namespace: Optional[str] = None
    sort: Optional[Literal['MitigationSeriesSortUnknown', 'MitigationSeriesSortMax', 'MitigationSeriesSortAverage', 'MitigationSeriesSortPct95']] = None
    start_time: Optional[str] = None
    top_n: Optional[int] = None
    traffic_unit: Optional[Literal['TrafficUnitUnknown', 'TrafficUnitBps', 'TrafficUnitPps']] = None


class L3l4ByMitigationResponse(F5XCBaseModel):
    """Response for Mitigation Traffic"""

    rates: Optional[list[L3l4L3L4Metric]] = None


class L3l4ByNetworkRequest(F5XCBaseModel):
    """Used to display Network (aka protocol) by tenant"""

    end_time: Optional[str] = None
    namespace: Optional[str] = None
    network_id: Optional[str] = None
    start_time: Optional[str] = None
    traffic_unit: Optional[Literal['TrafficUnitUnknown', 'TrafficUnitBps', 'TrafficUnitPps']] = None


class L3l4ByNetworkResponse(F5XCBaseModel):
    """Response for Network Traffic"""

    in_: Optional[list[L3l4L3L4Metric]] = Field(default=None, alias="in")
    out: Optional[list[L3l4L3L4Metric]] = None


class L3l4ByZoneRequest(F5XCBaseModel):
    """Used to display Zone by tenant"""

    end_time: Optional[str] = None
    namespace: Optional[str] = None
    network_id: Optional[str] = None
    routed_traffic: Optional[Literal['RoutedTrafficUnknown', 'RoutedTrafficPreScrub', 'RoutedTrafficPostScrub']] = None
    start_time: Optional[str] = None
    traffic_unit: Optional[Literal['TrafficUnitUnknown', 'TrafficUnitBps', 'TrafficUnitPps']] = None


class L3l4ByZoneResponse(F5XCBaseModel):
    """Response for Zone Traffic"""

    in_: Optional[list[L3l4L3L4Metric]] = Field(default=None, alias="in")
    out: Optional[list[L3l4L3L4Metric]] = None


class L3l4EventCountRequest(F5XCBaseModel):
    """Used to display Event counts for a network"""

    end_time: Optional[str] = None
    namespace: Optional[str] = None
    network_id: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class L3l4EventDataPoint(F5XCBaseModel):
    bounded: Optional[str] = None
    ongoing: Optional[str] = None
    timestamp: Optional[str] = None


class L3l4EventCountResponse(F5XCBaseModel):
    """Response for Application Traffic"""

    events: Optional[list[L3l4EventDataPoint]] = None


class L3l4TopTalker(F5XCBaseModel):
    in_: Optional[str] = Field(default=None, alias="in")
    ip: Optional[str] = None
    out: Optional[str] = None


class L3l4TopTalkersRequest(F5XCBaseModel):
    """Used to display Top Talkers for a network"""

    end_time: Optional[str] = None
    namespace: Optional[str] = None
    network_id: Optional[str] = None
    start_time: Optional[str] = None
    traffic_type: Optional[Literal['TrafficTypeUnknown', 'TrafficTypeExternal', 'TrafficTypeInternal']] = None
    traffic_unit: Optional[Literal['TrafficUnitUnknown', 'TrafficUnitBps', 'TrafficUnitPps']] = None


class L3l4TopTalkersResponse(F5XCBaseModel):
    """Response for Top Talkers"""

    data: Optional[list[L3l4TopTalker]] = None
    traffic_unit: Optional[Literal['TrafficUnitUnknown', 'TrafficUnitBps', 'TrafficUnitPps']] = None


# Convenience aliases
