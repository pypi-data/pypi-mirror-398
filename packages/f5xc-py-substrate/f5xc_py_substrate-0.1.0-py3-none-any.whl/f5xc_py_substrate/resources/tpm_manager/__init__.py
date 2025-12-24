"""TpmManager resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.tpm_manager.models import *
    from f5xc_py_substrate.resources.tpm_manager.resource import TpmManagerResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "TpmManagerResource":
        from f5xc_py_substrate.resources.tpm_manager.resource import TpmManagerResource
        return TpmManagerResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.tpm_manager.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.tpm_manager' has no attribute '{name}'")


__all__ = [
    "TpmManagerResource",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectRefType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateSpecType",
    "CreateRequest",
    "GetSpecType",
    "CreateResponse",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "Spec",
]
