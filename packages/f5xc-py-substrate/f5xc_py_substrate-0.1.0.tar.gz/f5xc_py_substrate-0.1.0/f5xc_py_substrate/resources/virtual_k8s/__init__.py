"""VirtualK8s resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.virtual_k8s.models import *
    from f5xc_py_substrate.resources.virtual_k8s.resource import VirtualK8sResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "VirtualK8sResource":
        from f5xc_py_substrate.resources.virtual_k8s.resource import VirtualK8sResource
        return VirtualK8sResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.virtual_k8s.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.virtual_k8s' has no attribute '{name}'")


__all__ = [
    "VirtualK8sResource",
    "Empty",
    "ObjectRefType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "TrendValue",
    "MetricValue",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "ObjectRefType",
    "VirtualK8screatespectype",
    "VirtualK8screaterequest",
    "VirtualK8sgetspectype",
    "VirtualK8screateresponse",
    "VirtualK8sdeleterequest",
    "VirtualK8sreplacespectype",
    "VirtualK8sreplacerequest",
    "VirtualK8sstatusobject",
    "VirtualK8sgetresponse",
    "VirtualK8slistresponseitem",
    "VirtualK8slistresponse",
    "VirtualK8spvcmetrictypedata",
    "VirtualK8spvcmetricdata",
    "VirtualK8spvcmetricsrequest",
    "VirtualK8spvcmetricsresponse",
    "VirtualK8sreplaceresponse",
    "Spec",
]
