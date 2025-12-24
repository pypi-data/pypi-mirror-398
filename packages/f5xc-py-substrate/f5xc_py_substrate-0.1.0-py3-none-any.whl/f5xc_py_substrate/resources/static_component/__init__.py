"""StaticComponent resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.static_component.models import *
    from f5xc_py_substrate.resources.static_component.resource import StaticComponentResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "StaticComponentResource":
        from f5xc_py_substrate.resources.static_component.resource import StaticComponentResource
        return StaticComponentResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.static_component.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.static_component' has no attribute '{name}'")


__all__ = [
    "StaticComponentResource",
    "ProtobufAny",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectGetMetaType",
    "ObjectRefType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "GetSpecType",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "Spec",
]
