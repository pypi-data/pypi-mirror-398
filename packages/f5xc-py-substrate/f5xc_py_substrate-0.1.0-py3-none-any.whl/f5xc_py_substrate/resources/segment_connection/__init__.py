"""SegmentConnection resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.segment_connection.models import *
    from f5xc_py_substrate.resources.segment_connection.resource import SegmentConnectionResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SegmentConnectionResource":
        from f5xc_py_substrate.resources.segment_connection.resource import SegmentConnectionResource
        return SegmentConnectionResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.segment_connection.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.segment_connection' has no attribute '{name}'")


__all__ = [
    "SegmentConnectionResource",
    "Empty",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectGetMetaType",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "SegmentConnectionType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "GetSpecType",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
