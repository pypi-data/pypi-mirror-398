"""Ike2 resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.ike2.models import *
    from f5xc_py_substrate.resources.ike2.resource import Ike2Resource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "Ike2Resource":
        from f5xc_py_substrate.resources.ike2.resource import Ike2Resource
        return Ike2Resource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.ike2.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.ike2' has no attribute '{name}'")


__all__ = [
    "Ike2Resource",
    "ObjectCreateMetaType",
    "Ike2DHGroups",
    "Empty",
    "IkePhase1Profileinputhours",
    "IkePhase1Profileinputminutes",
    "Schemaike2CreateSpecType",
    "Ike2CreateRequest",
    "ObjectGetMetaType",
    "Schemaike2GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "Ike2CreateResponse",
    "Ike2DeleteRequest",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "Schemaike2ReplaceSpecType",
    "Ike2ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "Ike2StatusObject",
    "Ike2GetResponse",
    "ProtobufAny",
    "ErrorType",
    "Ike2ListResponseItem",
    "Ike2ListResponse",
    "Ike2ReplaceResponse",
    "Spec",
]
