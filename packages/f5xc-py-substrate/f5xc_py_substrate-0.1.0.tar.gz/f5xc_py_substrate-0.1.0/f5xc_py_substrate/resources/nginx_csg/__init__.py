"""NginxCsg resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.nginx_csg.models import *
    from f5xc_py_substrate.resources.nginx_csg.resource import NginxCsgResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NginxCsgResource":
        from f5xc_py_substrate.resources.nginx_csg.resource import NginxCsgResource
        return NginxCsgResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.nginx_csg.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.nginx_csg' has no attribute '{name}'")


__all__ = [
    "NginxCsgResource",
    "Empty",
    "ObjectRefType",
    "ObjectGetMetaType",
    "APIDiscoverySpec",
    "WAFSpec",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "Spec",
]
