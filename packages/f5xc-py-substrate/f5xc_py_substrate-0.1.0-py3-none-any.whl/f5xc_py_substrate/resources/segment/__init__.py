"""Segment resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.segment.models import *
    from f5xc_py_substrate.resources.segment.resource import SegmentResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SegmentResource":
        from f5xc_py_substrate.resources.segment.resource import SegmentResource
        return SegmentResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.segment.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.segment' has no attribute '{name}'")


__all__ = [
    "SegmentResource",
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
    "CreateSpecType",
    "MetricData",
    "EdgeData",
    "FieldSelector",
    "AttachmentType",
    "GetSpecType",
    "LabelFilter",
    "ReplaceSpecType",
    "CreateRequest",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceRequest",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "NodeData",
    "ReplaceResponse",
    "SegmentSegmentsRequest",
    "SegmentSegmentsResponse",
    "Spec",
]
