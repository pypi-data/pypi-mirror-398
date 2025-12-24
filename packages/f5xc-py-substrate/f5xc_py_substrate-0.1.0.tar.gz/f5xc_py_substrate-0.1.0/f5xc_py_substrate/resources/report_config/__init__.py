"""ReportConfig resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.report_config.models import *
    from f5xc_py_substrate.resources.report_config.resource import ReportConfigResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ReportConfigResource":
        from f5xc_py_substrate.resources.report_config.resource import ReportConfigResource
        return ReportConfigResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.report_config.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.report_config' has no attribute '{name}'")


__all__ = [
    "ReportConfigResource",
    "Empty",
    "ObjectRefType",
    "ProtobufAny",
    "TrendValue",
    "WaapReportFieldData",
    "WaapReportFieldDataList",
    "AttackImpactData",
    "AttackImpact",
    "AttackSourcesData",
    "AttackSources",
    "ProtectedLBCount",
    "ReportDataATB",
    "ReportHeader",
    "SecurityEventsData",
    "SecurityEvents",
    "ThreatDetailsData",
    "ThreatDetails",
    "ReportDataWAAP",
    "ReportDeliveryStatus",
    "ReportGenerationStatus",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "ReportRecipients",
    "ReportFreqDaily",
    "ReportFreqMonthly",
    "Namespaces",
    "ReportFreqWeekly",
    "ReportTypeWaap",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "GetSpecType",
    "ObjectMetaType",
    "GlobalSpecType",
    "SpecType",
    "SystemObjectMetaType",
    "Object",
    "CustomAPIListResponseItem",
    "DeleteRequest",
    "GenerateReportRequest",
    "GenerateReportResponse",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ListReportsHistoryResponseItem",
    "ListReportsHistoryResponse",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
