"""PublicIp resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.public_ip.models import *
    from f5xc_py_substrate.resources.public_ip.resource import PublicIpResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "PublicIpResource":
        from f5xc_py_substrate.resources.public_ip.resource import PublicIpResource
        return PublicIpResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.public_ip.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.public_ip' has no attribute '{name}'")


__all__ = [
    "PublicIpResource",
    "ProtobufAny",
    "ObjectRefType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "GetSpecType",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "GetResponse",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
