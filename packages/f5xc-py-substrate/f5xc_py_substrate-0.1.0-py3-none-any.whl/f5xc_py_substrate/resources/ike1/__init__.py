"""Ike1 resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.ike1.models import *
    from f5xc_py_substrate.resources.ike1.resource import Ike1Resource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "Ike1Resource":
        from f5xc_py_substrate.resources.ike1.resource import Ike1Resource
        return Ike1Resource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.ike1.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.ike1' has no attribute '{name}'")


__all__ = [
    "Ike1Resource",
    "ObjectCreateMetaType",
    "IkePhase1Profileinputhours",
    "IkePhase1Profileinputminutes",
    "Empty",
    "IkePhase1Profileinputdays",
    "Schemaike1CreateSpecType",
    "Ike1CreateRequest",
    "ObjectGetMetaType",
    "Schemaike1GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "Ike1CreateResponse",
    "Ike1DeleteRequest",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "Schemaike1ReplaceSpecType",
    "Ike1ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "Ike1StatusObject",
    "Ike1GetResponse",
    "ProtobufAny",
    "ErrorType",
    "Ike1ListResponseItem",
    "Ike1ListResponse",
    "Ike1ReplaceResponse",
    "Spec",
]
