"""AwsVpcSite resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.aws_vpc_site.models import *
    from f5xc_py_substrate.resources.aws_vpc_site.resource import AwsVpcSiteResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AwsVpcSiteResource":
        from f5xc_py_substrate.resources.aws_vpc_site.resource import AwsVpcSiteResource
        return AwsVpcSiteResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.aws_vpc_site.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.aws_vpc_site' has no attribute '{name}'")


__all__ = [
    "AwsVpcSiteResource",
    "ObjectRefType",
    "ActiveEnhancedFirewallPoliciesType",
    "ActiveForwardProxyPoliciesType",
    "ActiveNetworkPoliciesType",
    "CustomPorts",
    "Empty",
    "AllowedVIPPorts",
    "CloudSubnetParamType",
    "CloudSubnetType",
    "AWSVPCTwoInterfaceNodeType",
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
    "L3PerformanceEnhancementType",
    "PerformanceEnhancementModeType",
    "AWSVPCIngressEgressGwReplaceType",
    "AWSVPCIngressEgressGwType",
    "AWSVPCOneInterfaceNodeType",
    "AWSVPCIngressGwReplaceType",
    "AWSVPCIngressGwType",
    "AWSSubnetInfoType",
    "AWSSubnetIdsType",
    "AWSVPCSiteInfoType",
    "AWSVPCVoltstackClusterReplaceType",
    "StorageClassType",
    "StorageClassListType",
    "AWSVPCVoltstackClusterType",
    "ObjectCreateMetaType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "BlockedServices",
    "BlockedServicesListType",
    "Coordinates",
    "CustomDNS",
    "SecurityGroupType",
    "CloudLinkADNType",
    "VifRegionConfig",
    "HostedVIFConfigType",
    "DirectConnectConfigType",
    "AWSNATGatewaychoiceType",
    "AWSVirtualPrivateGatewaychoiceType",
    "KubernetesUpgradeDrainConfig",
    "KubernetesUpgradeDrain",
    "OfflineSurvivabilityModeType",
    "OperatingSystemType",
    "PrivateConnectConfigType",
    "VolterraSoftwareType",
    "AWSVPCParamsType",
    "AWSVPCchoiceType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "DirectConnectInfo",
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
    "SetVPCK8SHostnamesRequest",
    "SetVPCK8SHostnamesResponse",
    "ValidateConfigRequest",
    "ValidateConfigResponse",
    "Spec",
]
