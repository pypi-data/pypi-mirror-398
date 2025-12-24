"""Tunnel resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.tunnel.models import *
    from f5xc_py_substrate.resources.tunnel.resource import TunnelResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "TunnelResource":
        from f5xc_py_substrate.resources.tunnel.resource import TunnelResource
        return TunnelResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.tunnel.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.tunnel' has no attribute '{name}'")


__all__ = [
    "TunnelResource",
    "Empty",
    "ObjectRefType",
    "ProtobufAny",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "Ipv4AddressType",
    "Ipv6AddressType",
    "IpAddressType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "SecretType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "VirtualNetworkSelectorType",
    "InterfaceType",
    "LocalIpAddressType",
    "LocalIpAddressSelector",
    "IpsecTunnelParams",
    "Params",
    "RemoteEndpointType",
    "RemoteIpAddressSelector",
    "CreateSpecType",
    "GetSpecType",
    "ReplaceSpecType",
    "FlapReason",
    "ConnectionStatus",
    "CreateRequest",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceRequest",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
