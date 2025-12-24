"""Pydantic models for waf."""

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
    """Metric data contains timestamp and the value."""

    timestamp: Optional[float] = None
    trend_value: Optional[TrendValue] = None
    value: Optional[str] = None


class RuleHitsId(F5XCBaseModel):
    """RuleHitsId uniquely identifies an entry in the response for rule_hits..."""

    app_type: Optional[str] = None
    bot_name: Optional[str] = None
    bot_type: Optional[str] = None
    instance: Optional[str] = None
    namespace: Optional[str] = None
    rule_id: Optional[str] = None
    rule_severity: Optional[str] = None
    rule_tag: Optional[str] = None
    service: Optional[str] = None
    site: Optional[str] = None
    virtual_host: Optional[str] = None
    waf_instance_id: Optional[str] = None


class RuleHitsCounter(F5XCBaseModel):
    """RuleHitsCounter contains the timeseries data of rule hits counter."""

    id_: Optional[RuleHitsId] = Field(default=None, alias="id")
    metric: Optional[list[MetricValue]] = None


class RuleHitsCountResponse(F5XCBaseModel):
    """Number of rule hits for each unique combination of group_by labels in..."""

    data: Optional[list[RuleHitsCounter]] = None
    step: Optional[str] = None


class SecurityEventsId(F5XCBaseModel):
    """SecurityEventsId uniquely identifies an entry in the response for..."""

    app_type: Optional[str] = None
    bot_name: Optional[str] = None
    bot_type: Optional[str] = None
    instance: Optional[str] = None
    namespace: Optional[str] = None
    service: Optional[str] = None
    site: Optional[str] = None
    virtual_host: Optional[str] = None
    waf_instance_id: Optional[str] = None
    waf_mode: Optional[str] = None


class SecurityEventsCounter(F5XCBaseModel):
    """SecurityEventsCounter contains the timeseries data of security events counter."""

    id_: Optional[SecurityEventsId] = Field(default=None, alias="id")
    metric: Optional[list[MetricValue]] = None


class SecurityEventsCountResponse(F5XCBaseModel):
    """Number of security events for each unique combination of group_by labels..."""

    data: Optional[list[SecurityEventsCounter]] = None
    step: Optional[str] = None


# Convenience aliases
