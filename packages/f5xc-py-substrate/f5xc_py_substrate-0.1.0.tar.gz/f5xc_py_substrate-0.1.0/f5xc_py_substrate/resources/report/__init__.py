"""Report resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.report.models import *
    from f5xc_py_substrate.resources.report.resource import ReportResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ReportResource":
        from f5xc_py_substrate.resources.report.resource import ReportResource
        return ReportResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.report.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.report' has no attribute '{name}'")


__all__ = [
    "ReportResource",
    "Empty",
    "ObjectRefType",
    "AttachmentValue",
    "TrendValue",
    "WaapReportFieldData",
    "WaapReportFieldDataList",
    "AttackImpactData",
    "AttackImpact",
    "AttackSourcesData",
    "AttackSources",
    "DownloadReportResponse",
    "ObjectGetMetaType",
    "DataATB",
    "ObjectRefType",
    "DeliveryStatus",
    "GenerationStatus",
    "ProtectedLBCount",
    "Header",
    "SecurityEventsData",
    "SecurityEvents",
    "ThreatDetailsData",
    "ThreatDetails",
    "DataWAAP",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "GetResponse",
    "Spec",
]
