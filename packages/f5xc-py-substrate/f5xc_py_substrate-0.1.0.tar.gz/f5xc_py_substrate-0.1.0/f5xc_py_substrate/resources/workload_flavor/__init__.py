"""WorkloadFlavor resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.workload_flavor.models import *
    from f5xc_py_substrate.resources.workload_flavor.resource import WorkloadFlavorResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "WorkloadFlavorResource":
        from f5xc_py_substrate.resources.workload_flavor.resource import WorkloadFlavorResource
        return WorkloadFlavorResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.workload_flavor.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.workload_flavor' has no attribute '{name}'")


__all__ = [
    "WorkloadFlavorResource",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateSpecType",
    "CreateRequest",
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
    "Spec",
]
