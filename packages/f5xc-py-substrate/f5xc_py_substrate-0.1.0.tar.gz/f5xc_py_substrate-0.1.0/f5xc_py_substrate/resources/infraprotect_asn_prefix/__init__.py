"""InfraprotectAsnPrefix resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.infraprotect_asn_prefix.models import *
    from f5xc_py_substrate.resources.infraprotect_asn_prefix.resource import InfraprotectAsnPrefixResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "InfraprotectAsnPrefixResource":
        from f5xc_py_substrate.resources.infraprotect_asn_prefix.resource import InfraprotectAsnPrefixResource
        return InfraprotectAsnPrefixResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.infraprotect_asn_prefix.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.infraprotect_asn_prefix' has no attribute '{name}'")


__all__ = [
    "InfraprotectAsnPrefixResource",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "Empty",
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
    "UpdateASNPrefixIRROverrideRequest",
    "UpdateASNPrefixIRROverrideResponse",
    "UpdateASNPrefixReviewStatusRequest",
    "UpdateASNPrefixReviewStatusResponse",
    "Spec",
]
