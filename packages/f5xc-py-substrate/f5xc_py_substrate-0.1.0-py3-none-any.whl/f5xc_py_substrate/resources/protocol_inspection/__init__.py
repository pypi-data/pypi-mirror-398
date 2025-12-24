"""ProtocolInspection resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.protocol_inspection.models import *
    from f5xc_py_substrate.resources.protocol_inspection.resource import ProtocolInspectionResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ProtocolInspectionResource":
        from f5xc_py_substrate.resources.protocol_inspection.resource import ProtocolInspectionResource
        return ProtocolInspectionResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.protocol_inspection.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.protocol_inspection' has no attribute '{name}'")


__all__ = [
    "ProtocolInspectionResource",
    "Empty",
    "ObjectRefType",
    "ProtobufAny",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "EnableDisableComplianceChecks",
    "EnableDisableSignatures",
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
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "Status",
    "StatusObject",
    "GetResponse",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
