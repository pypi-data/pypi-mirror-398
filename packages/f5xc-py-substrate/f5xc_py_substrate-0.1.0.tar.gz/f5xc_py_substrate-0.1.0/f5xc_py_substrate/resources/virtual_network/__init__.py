"""VirtualNetwork resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.virtual_network.models import *
    from f5xc_py_substrate.resources.virtual_network.resource import VirtualNetworkResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "VirtualNetworkResource":
        from f5xc_py_substrate.resources.virtual_network.resource import VirtualNetworkResource
        return VirtualNetworkResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.virtual_network.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.virtual_network' has no attribute '{name}'")


__all__ = [
    "VirtualNetworkResource",
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
    "NodeInterfaceInfo",
    "NodeInterfaceType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "StaticRouteViewType",
    "CreateSpecType",
    "CreateRequest",
    "StaticV6RouteViewType",
    "GetSpecType",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceSpecType",
    "ReplaceRequest",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "SIDCounterTypeData",
    "SIDCounterData",
    "SIDCounterRequest",
    "SIDCounterResponse",
    "Spec",
]
