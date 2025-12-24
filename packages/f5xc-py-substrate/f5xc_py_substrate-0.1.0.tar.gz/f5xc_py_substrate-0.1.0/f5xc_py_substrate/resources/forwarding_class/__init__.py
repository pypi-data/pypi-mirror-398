"""ForwardingClass resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.forwarding_class.models import *
    from f5xc_py_substrate.resources.forwarding_class.resource import ForwardingClassResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ForwardingClassResource":
        from f5xc_py_substrate.resources.forwarding_class.resource import ForwardingClassResource
        return ForwardingClassResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.forwarding_class.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.forwarding_class' has no attribute '{name}'")


__all__ = [
    "ForwardingClassResource",
    "ObjectCreateMetaType",
    "DSCPMarkingType",
    "Empty",
    "ObjectRefType",
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
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
