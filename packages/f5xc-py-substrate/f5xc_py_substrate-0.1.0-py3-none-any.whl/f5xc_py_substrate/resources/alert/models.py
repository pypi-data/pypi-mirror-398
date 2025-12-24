"""Pydantic models for alert."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AlertAlertsHistoryAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for alerts."""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    filter: Optional[str] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None


class AlertAlertsHistoryAggregationResponse(F5XCBaseModel):
    """Response message for AlertsHistoryAggregationRequest"""

    aggs: Optional[dict[str, Any]] = None
    total_hits: Optional[str] = None


class AlertAlertsHistoryResponse(F5XCBaseModel):
    """Response message for AlertsHistoryRequest/AlertsHistoryScrollRequest"""

    alerts: Optional[list[str]] = None
    scroll_id: Optional[str] = None
    total_hits: Optional[str] = None


class AlertAlertsHistoryScrollRequest(F5XCBaseModel):
    """Scroll request is used to fetch large number of alert messages in..."""

    namespace: Optional[str] = None
    scroll_id: Optional[str] = None


class Response(F5XCBaseModel):
    """Returns list of alerts that matches the selection criteria in the..."""

    data: Optional[str] = None


# Convenience aliases
