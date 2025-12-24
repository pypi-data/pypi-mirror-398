"""Srv6NetworkSlice resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.srv6_network_slice.models import *
    from f5xc_py_substrate.resources.srv6_network_slice.resource import Srv6NetworkSliceResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "Srv6NetworkSliceResource":
        from f5xc_py_substrate.resources.srv6_network_slice.resource import Srv6NetworkSliceResource
        return Srv6NetworkSliceResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.srv6_network_slice.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.srv6_network_slice' has no attribute '{name}'")


__all__ = [
    "Srv6NetworkSliceResource",
    "ObjectRefType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "Schemasrv6NetworkSlicecreatespectype",
    "Schemasrv6NetworkSlicegetspectype",
    "Schemasrv6NetworkSlicereplacespectype",
    "Srv6NetworkSlicecreaterequest",
    "Srv6NetworkSlicecreateresponse",
    "Srv6NetworkSlicedeleterequest",
    "Srv6NetworkSlicereplacerequest",
    "Srv6NetworkSlicestatusobject",
    "Srv6NetworkSlicegetresponse",
    "Srv6NetworkSlicelistresponseitem",
    "Srv6NetworkSlicelistresponse",
    "Srv6NetworkSlicereplaceresponse",
    "Spec",
]
