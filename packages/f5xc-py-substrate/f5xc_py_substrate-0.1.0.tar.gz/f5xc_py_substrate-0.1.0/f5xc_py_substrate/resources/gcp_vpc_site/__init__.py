"""GcpVpcSite resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.gcp_vpc_site.models import *
    from f5xc_py_substrate.resources.gcp_vpc_site.resource import GcpVpcSiteResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "GcpVpcSiteResource":
        from f5xc_py_substrate.resources.gcp_vpc_site.resource import GcpVpcSiteResource
        return GcpVpcSiteResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.gcp_vpc_site.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.gcp_vpc_site' has no attribute '{name}'")


__all__ = [
    "GcpVpcSiteResource",
    "Empty",
    "BlockedServices",
    "BlockedServicesListType",
    "ObjectCreateMetaType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "ObjectRefType",
    "Coordinates",
    "CustomDNS",
    "ActiveEnhancedFirewallPoliciesType",
    "ActiveForwardProxyPoliciesType",
    "ActiveNetworkPoliciesType",
    "GlobalConnectorType",
    "GlobalNetworkConnectionType",
    "GlobalNetworkConnectionListType",
    "GCPVPCNetworkType",
    "GCPVPCNetworkParamsType",
    "GCPVPCNetworkAutogenerateParamsType",
    "GCPVPCNetworkChoiceType",
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
    "GCPSubnetType",
    "GCPSubnetParamsType",
    "GCPVPCSubnetChoiceType",
    "L3PerformanceEnhancementType",
    "PerformanceEnhancementModeType",
    "GCPVPCIngressEgressGwType",
    "GCPVPCIngressGwType",
    "KubernetesUpgradeDrainConfig",
    "KubernetesUpgradeDrain",
    "OfflineSurvivabilityModeType",
    "OperatingSystemType",
    "PrivateConnectConfigType",
    "VolterraSoftwareType",
    "StorageClassType",
    "StorageClassListType",
    "GCPVPCVoltstackClusterType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "GCPVPCSiteInfoType",
    "SiteError",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "DeleteRequest",
    "GCPVPCIngressEgressGwReplaceType",
    "GCPVPCIngressGwReplaceType",
    "GCPVPCVoltstackClusterReplaceType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "ApplyStatus",
    "PlanStatus",
    "DeploymentStatusType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "SetCloudSiteInfoRequest",
    "SetCloudSiteInfoResponse",
    "ValidateConfigRequest",
    "ValidateConfigResponse",
    "Spec",
]
