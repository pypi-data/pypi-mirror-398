"""NginxServiceDiscovery resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.nginx_service_discovery.models import *
    from f5xc_py_substrate.resources.nginx_service_discovery.resource import NginxServiceDiscoveryResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NginxServiceDiscoveryResource":
        from f5xc_py_substrate.resources.nginx_service_discovery.resource import NginxServiceDiscoveryResource
        return NginxServiceDiscoveryResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.nginx_service_discovery.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.nginx_service_discovery' has no attribute '{name}'")


__all__ = [
    "NginxServiceDiscoveryResource",
    "ObjectRefType",
    "ConfigSyncGroup",
    "ObjectCreateMetaType",
    "NGINXInstance",
    "DiscoveryTarget",
    "ServerBlockFilter",
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
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
