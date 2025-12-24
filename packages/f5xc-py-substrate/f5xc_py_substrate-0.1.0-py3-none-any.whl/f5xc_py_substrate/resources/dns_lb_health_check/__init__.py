"""DnsLbHealthCheck resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.dns_lb_health_check.models import *
    from f5xc_py_substrate.resources.dns_lb_health_check.resource import DnsLbHealthCheckResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "DnsLbHealthCheckResource":
        from f5xc_py_substrate.resources.dns_lb_health_check.resource import DnsLbHealthCheckResource
        return DnsLbHealthCheckResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.dns_lb_health_check.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.dns_lb_health_check' has no attribute '{name}'")


__all__ = [
    "DnsLbHealthCheckResource",
    "ObjectCreateMetaType",
    "HttpHealthCheck",
    "Empty",
    "TcpHealthCheck",
    "TcpHexHealthCheck",
    "UdpHealthCheck",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "ObjectRefType",
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
    "Spec",
]
