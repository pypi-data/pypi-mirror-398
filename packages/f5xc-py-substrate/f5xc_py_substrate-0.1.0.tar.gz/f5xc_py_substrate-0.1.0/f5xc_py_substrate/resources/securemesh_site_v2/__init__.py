"""SecuremeshSiteV2 resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.securemesh_site_v2.models import *
    from f5xc_py_substrate.resources.securemesh_site_v2.resource import SecuremeshSiteV2Resource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SecuremeshSiteV2Resource":
        from f5xc_py_substrate.resources.securemesh_site_v2.resource import SecuremeshSiteV2Resource
        return SecuremeshSiteV2Resource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.securemesh_site_v2.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.securemesh_site_v2' has no attribute '{name}'")


__all__ = [
    "SecuremeshSiteV2Resource",
    "Empty",
    "BlockedServices",
    "BlockedServicesListType",
    "BondLacpType",
    "FleetBondDeviceType",
    "ObjectRefType",
    "ObjectRefType",
    "ActiveEnhancedFirewallPoliciesType",
    "ActiveForwardProxyPoliciesType",
    "DHCPIPV6PoolType",
    "DHCPIPV6NetworkType",
    "DHCPInterfaceIPV6Type",
    "DHCPIPV6StatefulServer",
    "IPV6DnsList",
    "IPV6LocalDnsAddress",
    "IPV6DnsConfig",
    "IPV6AutoConfigRouterType",
    "IPV6AutoConfigType",
    "LinkQualityMonitorConfig",
    "StaticIpParametersClusterType",
    "StaticIpParametersNodeType",
    "StaticIPParametersType",
    "ProtobufAny",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
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
    "SecretType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "ViewssecuremeshSiteV2ethernetinterfacetype",
    "NetworkSelectType",
    "SecuremeshSiteV2vlaninterfacetype",
    "SecuremeshSiteV2interface",
    "ViewssecuremeshSiteV2node",
    "SecuremeshSiteV2nodelist",
    "SecuremeshSiteV2awsprovidertype",
    "SecuremeshSiteV2azureprovidertype",
    "SecuremeshSiteV2baremetalprovidertype",
    "AdminUserCredentialsType",
    "SecuremeshSiteV2customproxy",
    "SecuremeshSiteV2customproxybypasssettings",
    "SecuremeshSiteV2customdnssettings",
    "SecuremeshSiteV2customntpsettings",
    "SecuremeshSiteV2dnsntpserverconfig",
    "SecuremeshSiteV2equinixprovidertype",
    "SecuremeshSiteV2gcpprovidertype",
    "SecuremeshSiteV2kvmprovidertype",
    "SecuremeshSiteV2loadbalancingsettingstype",
    "StaticRouteViewType",
    "SecuremeshSiteV2staticrouteslisttype",
    "StaticV6RouteViewType",
    "StaticV6RoutesListType",
    "SecuremeshSiteV2virtualnetworkconfiguration",
    "SecuremeshSiteV2localvrfsettingtype",
    "SecuremeshSiteV2nutanixprovidertype",
    "SecuremeshSiteV2ociprovidertype",
    "OfflineSurvivabilityModeType",
    "SecuremeshSiteV2openstackprovidertype",
    "L3PerformanceEnhancementType",
    "PerformanceEnhancementModeType",
    "SpecificRE",
    "RegionalEdgeSelection",
    "SecuremeshSiteV2sitemeshgrouptype",
    "OperatingSystemType",
    "VolterraSoftwareType",
    "SecuremeshSiteV2softwaresettingstype",
    "KubernetesUpgradeDrainConfig",
    "KubernetesUpgradeDrain",
    "SecuremeshSiteV2upgradesettingstype",
    "SecuremeshSiteV2vmwareprovidertype",
    "ViewssecuremeshSiteV2createspectype",
    "SecuremeshSiteV2createrequest",
    "SiteError",
    "ViewssecuremeshSiteV2getspectype",
    "SecuremeshSiteV2createresponse",
    "SecuremeshSiteV2deleterequest",
    "ViewssecuremeshSiteV2replacespectype",
    "SecuremeshSiteV2replacerequest",
    "SecuremeshSiteV2statusobject",
    "SecuremeshSiteV2getresponse",
    "SecuremeshSiteV2listresponseitem",
    "SecuremeshSiteV2listresponse",
    "SecuremeshSiteV2replaceresponse",
    "Spec",
]
