"""Pydantic models for log."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AccessLogAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for access logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None


class AccessLogRequestV2(F5XCBaseModel):
    """Request to fetch access logs."""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None


class AuditLogAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for audit logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None


class AuditLogRequestV2(F5XCBaseModel):
    """Request to fetch audit logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None


class LabelFilter(F5XCBaseModel):
    """Label Filter is used to filter th that match the logs specified label..."""

    label: Optional[Literal['LABEL_NONE', 'LABEL_EXTERNAL_CONNECTOR_IP', 'LABEL_EXTERNAL_CONNECTOR_NODE']] = None
    op: Optional[Literal['EQ', 'NEQ']] = None
    value: Optional[str] = None


class ExternalConnectorRequest(F5XCBaseModel):
    """Request to get logs for a external connector"""

    end_time: Optional[str] = None
    external_connector: Optional[str] = None
    label_filter: Optional[list[LabelFilter]] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    site: Optional[str] = None
    start_time: Optional[str] = None


class FirewallLogAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for Firewall logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None


class FirewallLogRequest(F5XCBaseModel):
    """Request to fetch Firewall logs."""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None


class K8SAuditLogAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for K8s audit logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    site: Optional[str] = None
    start_time: Optional[str] = None


class K8SAuditLogRequest(F5XCBaseModel):
    """Request to fetch K8s audit logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    site: Optional[str] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None


class K8SEventsAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for K8s events in a Cluster"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    site: Optional[str] = None
    start_time: Optional[str] = None


class K8SEventsRequest(F5XCBaseModel):
    """Request to fetch physical K8s events"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    site: Optional[str] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None


class AggregationResponse(F5XCBaseModel):
    """Response message for AuditLogAggregationRequest/AccessLogAggregationRequest"""

    aggs: Optional[dict[str, Any]] = None
    total_hits: Optional[str] = None


class Response(F5XCBaseModel):
    """Response message for AuditLogRequest/AccessLogRequest/LogScrollRequest"""

    aggs: Optional[dict[str, Any]] = None
    logs: Optional[list[str]] = None
    scroll_id: Optional[str] = None
    total_hits: Optional[str] = None


class PlatformEventAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for platform events"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None


class PlatformEventRequest(F5XCBaseModel):
    """Request to fetch platform events"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    include_config_changes: Optional[bool] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None


class VK8SAuditLogAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for vK8s audit logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None


class VK8SAuditLogRequest(F5XCBaseModel):
    """Request to fetch Virtual K8s audit logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None


class VK8SEventsAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for vK8s events"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None


class VK8SEventsRequest(F5XCBaseModel):
    """Request to fetch Virtual K8s events"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None


# Convenience aliases
