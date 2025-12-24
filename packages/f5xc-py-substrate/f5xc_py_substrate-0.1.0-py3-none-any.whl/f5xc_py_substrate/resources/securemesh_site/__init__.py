"""SecuremeshSite resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.securemesh_site.models import *
    from f5xc_py_substrate.resources.securemesh_site.resource import SecuremeshSiteResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SecuremeshSiteResource":
        from f5xc_py_substrate.resources.securemesh_site.resource import SecuremeshSiteResource
        return SecuremeshSiteResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.securemesh_site.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.securemesh_site' has no attribute '{name}'")


__all__ = [
    "SecuremeshSiteResource",
    "Empty",
    "BlockedServices",
    "BlockedServicesListType",
    "BondLacpType",
    "FleetBondDeviceType",
    "FleetBondDevicesListType",
    "ObjectRefType",
    "ObjectRefType",
    "ActiveEnhancedFirewallPoliciesType",
    "ActiveForwardProxyPoliciesType",
    "ActiveNetworkPoliciesType",
    "DHCPIPV6PoolType",
    "DHCPIPV6NetworkType",
    "DHCPInterfaceIPV6Type",
    "DHCPIPV6StatefulServer",
    "DHCPInterfaceIPType",
    "DHCPPoolType",
    "DHCPNetworkType",
    "DHCPServerParametersType",
    "LinkQualityMonitorConfig",
    "DedicatedInterfaceType",
    "DedicatedManagementInterfaceType",
    "IPV6DnsList",
    "IPV6LocalDnsAddress",
    "IPV6DnsConfig",
    "IPV6AutoConfigRouterType",
    "IPV6AutoConfigType",
    "StaticIpParametersClusterType",
    "StaticIpParametersNodeType",
    "StaticIPParametersType",
    "EthernetInterfaceType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "NodeInterfaceInfo",
    "NodeInterfaceType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "Coordinates",
    "GlobalConnectorType",
    "GlobalNetworkConnectionType",
    "GlobalNetworkConnectionListType",
    "Interface",
    "InterfaceListType",
    "StaticRouteViewType",
    "StaticRoutesListType",
    "StaticV6RouteViewType",
    "StaticV6RoutesListType",
    "VnConfiguration",
    "SmsNetworkConfiguration",
    "KubernetesUpgradeDrainConfig",
    "KubernetesUpgradeDrain",
    "MasterNode",
    "OfflineSurvivabilityModeType",
    "OperatingSystemType",
    "L3PerformanceEnhancementType",
    "PerformanceEnhancementModeType",
    "VolterraSoftwareType",
    "CreateSpecType",
    "CreateRequest",
    "GetSpecType",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceSpecType",
    "ReplaceRequest",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
