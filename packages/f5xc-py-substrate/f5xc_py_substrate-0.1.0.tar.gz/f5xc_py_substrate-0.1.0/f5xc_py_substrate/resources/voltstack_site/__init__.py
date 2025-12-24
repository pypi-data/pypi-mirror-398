"""VoltstackSite resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.voltstack_site.models import *
    from f5xc_py_substrate.resources.voltstack_site.resource import VoltstackSiteResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "VoltstackSiteResource":
        from f5xc_py_substrate.resources.voltstack_site.resource import VoltstackSiteResource
        return VoltstackSiteResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.voltstack_site.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.voltstack_site' has no attribute '{name}'")


__all__ = [
    "VoltstackSiteResource",
    "BFD",
    "Empty",
    "Nodes",
    "ObjectRefType",
    "BgpRoutePolicy",
    "BgpRoutePolicies",
    "FamilyInet",
    "ObjectRefType",
    "InterfaceList",
    "PeerExternal",
    "MessageMetaType",
    "Peer",
    "BGPConfiguration",
    "BlockedServices",
    "BlockedServicesListType",
    "BondLacpType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "DeviceNetappBackendOntapSanChapType",
    "FlashArrayEndpoint",
    "FlashArrayType",
    "FlashBladeEndpoint",
    "FlashBladeType",
    "FleetBondDeviceType",
    "FleetBondDevicesListType",
    "StorageClassCustomType",
    "StorageClassHpeStorageType",
    "StorageClassNetappTridentType",
    "StorageClassPureServiceOrchestratorType",
    "FleetStorageClassType",
    "FleetStorageClassListType",
    "StorageDeviceHpeStorageType",
    "PrefixStringListType",
    "OntapVolumeDefaults",
    "OntapVirtualStoragePoolType",
    "StorageDeviceNetappBackendOntapNasType",
    "StorageDeviceNetappBackendOntapSanType",
    "StorageDeviceNetappTridentType",
    "PsoArrayConfiguration",
    "StorageDevicePureStorageServiceOrchestratorType",
    "FleetStorageDeviceType",
    "FleetStorageDeviceListType",
    "LocalControlPlaneType",
    "SriovInterface",
    "SriovInterfacesListType",
    "VGPUConfiguration",
    "VMConfiguration",
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
    "TunnelInterfaceType",
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
    "GlobalConnectorType",
    "GlobalNetworkConnectionType",
    "GlobalNetworkConnectionListType",
    "Coordinates",
    "CustomDNS",
    "KubernetesUpgradeDrainConfig",
    "KubernetesUpgradeDrain",
    "MasterNode",
    "OfflineSurvivabilityModeType",
    "OperatingSystemType",
    "VolterraSoftwareType",
    "Interface",
    "InterfaceListType",
    "StaticRouteViewType",
    "StaticRoutesListType",
    "StaticV6RouteViewType",
    "StaticV6RoutesListType",
    "SliVnConfiguration",
    "VnConfiguration",
    "VssNetworkConfiguration",
    "StorageInterfaceType",
    "StorageInterfaceListType",
    "VssStorageConfiguration",
    "CreateSpecType",
    "GetSpecType",
    "ReplaceSpecType",
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
