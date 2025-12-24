"""SyntheticMonitor resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.synthetic_monitor.models import *
    from f5xc_py_substrate.resources.synthetic_monitor.resource import SyntheticMonitorResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SyntheticMonitorResource":
        from f5xc_py_substrate.resources.synthetic_monitor.resource import SyntheticMonitorResource
        return SyntheticMonitorResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.synthetic_monitor.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.synthetic_monitor' has no attribute '{name}'")


__all__ = [
    "SyntheticMonitorResource",
    "ProtobufAny",
    "Empty",
    "CertItem",
    "CertificateReportDetailResponseEntry",
    "DNSMonitorEventDetail",
    "GetCertSummaryResponse",
    "GetCertificateReportDetailResponse",
    "GetDNSMonitorHealthRequest",
    "SourceHealthItem",
    "GetDNSMonitorHealthResponse",
    "GetDNSMonitorHealthResponseList",
    "GetDNSMonitorSummaryResponse",
    "HistoryItem",
    "GetGlobalHistoryResponse",
    "GetGlobalSummaryResponse",
    "RegionLatencyItem",
    "GetHTTPMonitorDetailResponse",
    "GetHTTPMonitorHealthRequest",
    "GetHTTPMonitorHealthResponse",
    "GetHTTPMonitorHealthResponseList",
    "GetHTTPMonitorSummaryResponse",
    "TagValuesItem",
    "MetricItem",
    "GetMetricQueryDataRequest",
    "RawData",
    "MetricQueryData",
    "GetMetricQueryDataResponse",
    "HTTPMonitorEventDetail",
    "MonitorEvents",
    "GetMonitorEventsResponse",
    "GetMonitorHistorySegment",
    "GetMonitorHistories",
    "GetMonitorHistoryResponse",
    "Record",
    "GetRecordTypeSummaryResponse",
    "MonitorRegionCoordinates",
    "MonitorsBySourceSummary",
    "GetSourceSummaryResponse",
    "GetTLSReportDetailResponse",
    "MonitorTLSReportSummaryProtocol",
    "GetTLSReportSummaryResponse",
    "TLSItem",
    "GetTLSSummaryResponse",
    "SuggestValuesRequest",
    "SuggestedItem",
    "SuggestValuesResponse",
    "Spec",
]
