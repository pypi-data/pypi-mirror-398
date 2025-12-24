"""V1HttpMonitor resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.v1_http_monitor.models import *
    from f5xc_py_substrate.resources.v1_http_monitor.resource import V1HttpMonitorResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "V1HttpMonitorResource":
        from f5xc_py_substrate.resources.v1_http_monitor.resource import V1HttpMonitorResource
        return V1HttpMonitorResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.v1_http_monitor.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.v1_http_monitor' has no attribute '{name}'")


__all__ = [
    "V1HttpMonitorResource",
    "Empty",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectMetaType",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "SystemObjectMetaType",
    "AWSRegions",
    "AWSRegionsExternal",
    "DynamicThreshold",
    "StaticMaxThreshold",
    "StaticMinThreshold",
    "HealthPolicy",
    "RegionalEdgeExternal",
    "RegionalEdgeRegions",
    "Source",
    "SourceExternal",
    "V1HttpMonitorrequestbody",
    "V1HttpMonitorhttpmonitorheader",
    "V1HttpMonitorcreatespectype",
    "V1HttpMonitorcreaterequest",
    "V1HttpMonitorgetspectype",
    "V1HttpMonitorcreateresponse",
    "V1HttpMonitordeleterequest",
    "V1HttpMonitorglobalspectype",
    "V1HttpMonitorspectype",
    "V1HttpMonitorobject",
    "V1HttpMonitorgetfilteredhttpmonitorlistresponse",
    "V1HttpMonitorreplacespectype",
    "V1HttpMonitorreplacerequest",
    "V1HttpMonitorstatusobject",
    "V1HttpMonitorgetresponse",
    "V1HttpMonitorlistresponseitem",
    "V1HttpMonitorlistresponse",
    "V1HttpMonitorreplaceresponse",
    "Spec",
]
