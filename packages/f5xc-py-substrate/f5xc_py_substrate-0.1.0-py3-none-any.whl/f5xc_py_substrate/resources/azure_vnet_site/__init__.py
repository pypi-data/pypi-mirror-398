"""AzureVnetSite resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.azure_vnet_site.models import *
    from f5xc_py_substrate.resources.azure_vnet_site.resource import AzureVnetSiteResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AzureVnetSiteResource":
        from f5xc_py_substrate.resources.azure_vnet_site.resource import AzureVnetSiteResource
        return AzureVnetSiteResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.azure_vnet_site.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.azure_vnet_site' has no attribute '{name}'")


__all__ = [
    "AzureVnetSiteResource",
    "Empty",
    "MessageMetaType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "ExpressRouteOtherSubscriptionConnection",
    "ExpressRouteConnectionType",
    "AzureSpecialSubnetType",
    "CloudSubnetParamType",
    "AzureSubnetChoiceWithAutoType",
    "CloudLinkADNType",
    "ExpressRouteConfigType",
    "AzureVnetType",
    "VnetPeeringType",
    "AzureHubVnetType",
    "ObjectRefType",
    "ActiveEnhancedFirewallPoliciesType",
    "ActiveForwardProxyPoliciesType",
    "ActiveNetworkPoliciesType",
    "GlobalConnectorType",
    "GlobalNetworkConnectionType",
    "GlobalNetworkConnectionListType",
    "ObjectRefType",
    "Ipv4AddressType",
    "Ipv6AddressType",
    "IpAddressType",
    "NextHopType",
    "Ipv4SubnetType",
    "Ipv6SubnetType",
    "IpSubnetType",
    "StaticRouteType",
    "SiteStaticRoutesType",
    "SiteStaticRoutesListType",
    "AzureSubnetType",
    "AzureSubnetChoiceType",
    "AzureVnetTwoInterfaceNodeARType",
    "L3PerformanceEnhancementType",
    "PerformanceEnhancementModeType",
    "AzureVnetIngressEgressGwARReplaceType",
    "AcceleratedNetworkingType",
    "AzureVnetIngressEgressGwARType",
    "AzureVnetTwoInterfaceNodeType",
    "AzureVnetIngressEgressGwReplaceType",
    "AzureVnetIngressEgressGwType",
    "AzureVnetOneInterfaceNodeARType",
    "AzureVnetIngressGwARReplaceType",
    "AzureVnetIngressGwARType",
    "AzureVnetOneInterfaceNodeType",
    "AzureVnetIngressGwReplaceType",
    "AzureVnetIngressGwType",
    "ExpressRouteInfo",
    "NodeInstanceNameType",
    "VnetIpPrefixesType",
    "VNETInfoType",
    "InfoType",
    "AzureVnetVoltstackClusterARReplaceType",
    "StorageClassType",
    "StorageClassListType",
    "AzureVnetVoltstackClusterARType",
    "AzureVnetVoltstackClusterReplaceType",
    "AzureVnetVoltstackClusterType",
    "ObjectCreateMetaType",
    "BlockedServices",
    "BlockedServicesListType",
    "Coordinates",
    "CustomDNS",
    "KubernetesUpgradeDrainConfig",
    "KubernetesUpgradeDrain",
    "OfflineSurvivabilityModeType",
    "OperatingSystemType",
    "VolterraSoftwareType",
    "AzureVnetParamsType",
    "AzureVnetChoiceType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "SiteError",
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
    "ApplyStatus",
    "PlanStatus",
    "DeploymentStatusType",
    "StatusMetaType",
    "AzureRouteTableWithStaticRoute",
    "AzureRouteTableWithStaticRouteListType",
    "SubnetStatusType",
    "AzureAttachmentsStatusType",
    "AzureAttachmentsListStatusType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "SetCloudSiteInfoRequest",
    "SetCloudSiteInfoResponse",
    "PublishVIPParamsPerAz",
    "SetVIPInfoRequest",
    "SetVIPInfoResponse",
    "ValidateConfigRequest",
    "ValidateConfigResponse",
    "Spec",
]
