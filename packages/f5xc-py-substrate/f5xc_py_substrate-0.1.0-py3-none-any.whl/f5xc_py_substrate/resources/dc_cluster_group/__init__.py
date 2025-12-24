"""DcClusterGroup resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.dc_cluster_group.models import *
    from f5xc_py_substrate.resources.dc_cluster_group.resource import DcClusterGroupResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "DcClusterGroupResource":
        from f5xc_py_substrate.resources.dc_cluster_group.resource import DcClusterGroupResource
        return DcClusterGroupResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.dc_cluster_group.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.dc_cluster_group' has no attribute '{name}'")


__all__ = [
    "DcClusterGroupResource",
    "ObjectCreateMetaType",
    "Empty",
    "DCClusterGroupMeshType",
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
    "DeleteRequest",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "SiteInfo",
    "Status",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "TrendValue",
    "MetricValue",
    "MetricTypeData",
    "MetricData",
    "MetricsRequest",
    "MetricsResponse",
    "ReplaceResponse",
    "Spec",
]
