"""NetworkInterface resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.network_interface.models import *
    from f5xc_py_substrate.resources.network_interface.resource import NetworkInterfaceResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NetworkInterfaceResource":
        from f5xc_py_substrate.resources.network_interface.resource import NetworkInterfaceResource
        return NetworkInterfaceResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.network_interface.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.network_interface' has no attribute '{name}'")


__all__ = [
    "NetworkInterfaceResource",
    "Empty",
    "ObjectRefType",
    "ObjectCreateMetaType",
    "LinkQualityMonitorConfig",
    "DedicatedInterfaceType",
    "DedicatedManagementInterfaceType",
    "DHCPPoolType",
    "DHCPNetworkType",
    "DHCPInterfaceIPType",
    "DHCPServerParametersType",
    "IPV6DnsList",
    "IPV6LocalDnsAddress",
    "IPV6DnsConfig",
    "DHCPIPV6PoolType",
    "DHCPIPV6NetworkType",
    "DHCPInterfaceIPV6Type",
    "DHCPIPV6StatefulServer",
    "IPV6AutoConfigRouterType",
    "IPV6AutoConfigType",
    "StaticIpParametersClusterType",
    "StaticIpParametersNodeType",
    "StaticIPParametersType",
    "EthernetInterfaceType",
    "Layer2SriovInterfaceType",
    "Layer2VlanInterfaceType",
    "Layer2SloVlanInterfaceType",
    "Layer2InterfaceType",
    "ObjectRefType",
    "TunnelInterfaceType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "Ipv4AddressType",
    "DNS",
    "DFGW",
    "Ipv4SubnetType",
    "Tunnel",
    "LegacyInterfaceType",
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
    "Status",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
