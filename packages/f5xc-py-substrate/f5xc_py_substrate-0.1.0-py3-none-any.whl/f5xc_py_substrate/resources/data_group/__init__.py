"""DataGroup resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.data_group.models import *
    from f5xc_py_substrate.resources.data_group.resource import DataGroupResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "DataGroupResource":
        from f5xc_py_substrate.resources.data_group.resource import DataGroupResource
        return DataGroupResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.data_group.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.data_group' has no attribute '{name}'")


__all__ = [
    "DataGroupResource",
    "AddressRecords",
    "IntegerRecords",
    "StringRecords",
    "CreateSpecType",
    "GetSpecType",
    "ReplaceSpecType",
    "ObjectCreateMetaType",
    "CreateRequest",
    "ObjectGetMetaType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "DeleteRequest",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ReplaceRequest",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
