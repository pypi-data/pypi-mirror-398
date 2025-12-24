"""V1DnsMonitor resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.v1_dns_monitor.models import *
    from f5xc_py_substrate.resources.v1_dns_monitor.resource import V1DnsMonitorResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "V1DnsMonitorResource":
        from f5xc_py_substrate.resources.v1_dns_monitor.resource import V1DnsMonitorResource
        return V1DnsMonitorResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.v1_dns_monitor.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.v1_dns_monitor' has no attribute '{name}'")


__all__ = [
    "V1DnsMonitorResource",
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
    "V1DnsMonitornameserver",
    "V1DnsMonitorcreatespectype",
    "V1DnsMonitorcreaterequest",
    "V1DnsMonitorgetspectype",
    "V1DnsMonitorcreateresponse",
    "V1DnsMonitordeleterequest",
    "V1DnsMonitorglobalspectype",
    "V1DnsMonitorspectype",
    "V1DnsMonitorobject",
    "V1DnsMonitorgetfiltereddnsmonitorlistresponse",
    "V1DnsMonitorreplacespectype",
    "V1DnsMonitorreplacerequest",
    "V1DnsMonitorstatusobject",
    "V1DnsMonitorgetresponse",
    "V1DnsMonitorlistresponseitem",
    "V1DnsMonitorlistresponse",
    "V1DnsMonitorreplaceresponse",
    "Spec",
]
