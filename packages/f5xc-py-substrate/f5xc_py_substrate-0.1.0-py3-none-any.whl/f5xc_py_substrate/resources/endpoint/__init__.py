"""Endpoint resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.endpoint.models import *
    from f5xc_py_substrate.resources.endpoint.resource import EndpointResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "EndpointResource":
        from f5xc_py_substrate.resources.endpoint.resource import EndpointResource
        return EndpointResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.endpoint.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.endpoint' has no attribute '{name}'")


__all__ = [
    "EndpointResource",
    "ConsulInfo",
    "ObjectCreateMetaType",
    "DnsNameAdvancedType",
    "LabelSelectorType",
    "ServiceInfoType",
    "Empty",
    "PrefixStringListType",
    "SnatPoolConfiguration",
    "ObjectRefType",
    "SiteRefType",
    "NetworkRefType",
    "VSiteRefType",
    "NetworkSiteRefSelector",
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
    "DNSInfo",
    "DeleteRequest",
    "K8SInfo",
    "DiscoveredInfoType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "Ipv6AddressType",
    "Ipv4AddressType",
    "IpAddressType",
    "ObjectRefType",
    "HealthCheckInfoType",
    "VerStatusType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
