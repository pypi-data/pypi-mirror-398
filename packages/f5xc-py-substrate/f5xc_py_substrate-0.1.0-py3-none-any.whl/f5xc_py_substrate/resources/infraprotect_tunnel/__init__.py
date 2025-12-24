"""InfraprotectTunnel resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.infraprotect_tunnel.models import *
    from f5xc_py_substrate.resources.infraprotect_tunnel.resource import InfraprotectTunnelResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "InfraprotectTunnelResource":
        from f5xc_py_substrate.resources.infraprotect_tunnel.resource import InfraprotectTunnelResource
        return InfraprotectTunnelResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.infraprotect_tunnel.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.infraprotect_tunnel' has no attribute '{name}'")


__all__ = [
    "InfraprotectTunnelResource",
    "ObjectRefType",
    "Empty",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "BGPInformation",
    "Bandwidth",
    "ObjectCreateMetaType",
    "GreIpv4Tunnel",
    "GreIpv6Tunnel",
    "IpInIpTunnel",
    "Ipv6ToIpv6Tunnel",
    "TunnelLocation",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "L2DirectConnectTunnel",
    "L2EquinixTunnel",
    "L2MegaportTunnel",
    "L2PacketFabricTunnel",
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
    "UpdateTunnelStatusRequest",
    "UpdateTunnelStatusResponse",
    "Spec",
]
