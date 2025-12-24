"""NginxInstance resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.nginx_instance.models import *
    from f5xc_py_substrate.resources.nginx_instance.resource import NginxInstanceResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NginxInstanceResource":
        from f5xc_py_substrate.resources.nginx_instance.resource import NginxInstanceResource
        return NginxInstanceResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.nginx_instance.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.nginx_instance' has no attribute '{name}'")


__all__ = [
    "NginxInstanceResource",
    "Empty",
    "ObjectRefType",
    "APIDiscoverySpec",
    "ObjectGetMetaType",
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
