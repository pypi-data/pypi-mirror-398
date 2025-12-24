"""AwsTgwSite resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.aws_tgw_site.models import *
    from f5xc_py_substrate.resources.aws_tgw_site.resource import AwsTgwSiteResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AwsTgwSiteResource":
        from f5xc_py_substrate.resources.aws_tgw_site.resource import AwsTgwSiteResource
        return AwsTgwSiteResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.aws_tgw_site.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.aws_tgw_site' has no attribute '{name}'")


__all__ = [
    "AwsTgwSiteResource",
    "AWSSubnetInfoType",
    "AWSSubnetIdsType",
    "AWSTGWInfoConfigType",
    "AWSTGWResourceShareType",
    "AWSTGWStatusType",
    "ObjectCreateMetaType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "ObjectRefType",
    "CloudSubnetParamType",
    "CloudSubnetType",
    "Empty",
    "AWSVPCTwoInterfaceNodeType",
    "SecurityGroupType",
    "ExistingTGWType",
    "TGWAssignedASNType",
    "TGWParamsType",
    "AWSVPCParamsType",
    "ServicesVPCType",
    "BlockedServices",
    "BlockedServicesListType",
    "Coordinates",
    "CustomDNS",
    "CloudLinkADNType",
    "VifRegionConfig",
    "HostedVIFConfigType",
    "DirectConnectConfigType",
    "KubernetesUpgradeDrainConfig",
    "KubernetesUpgradeDrain",
    "OfflineSurvivabilityModeType",
    "OperatingSystemType",
    "L3PerformanceEnhancementType",
    "PerformanceEnhancementModeType",
    "PrivateConnectConfigType",
    "VolterraSoftwareType",
    "ActiveServicePoliciesType",
    "ActiveEnhancedFirewallPoliciesType",
    "ActiveForwardProxyPoliciesType",
    "ActiveNetworkPoliciesType",
    "SecurityConfigType",
    "CustomPorts",
    "AllowedVIPPorts",
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
    "VnConfiguration",
    "VPCAttachmentType",
    "VPCAttachmentListType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "DirectConnectInfo",
    "SiteError",
    "PublishVIPParamsPerAz",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "DeleteRequest",
    "ObjectReplaceMetaType",
    "ServicesVPCReplaceType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "ApplyStatus",
    "PlanStatus",
    "DeploymentStatusType",
    "StatusMetaType",
    "AWSRouteTableType",
    "AWSRouteTableListType",
    "SubnetStatusType",
    "AWSAttachmentsStatusType",
    "AWSConnectPeerStatusType",
    "AWSConnectAttachmentStatusType",
    "AWSTGWResourceReference",
    "AWSTGWRouteTableStatusType",
    "AWSAttachmentsListStatusType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "SetTGWInfoRequest",
    "SetTGWInfoResponse",
    "SetVIPInfoRequest",
    "SetVIPInfoResponse",
    "SetVPCIpPrefixesRequest",
    "SetVPCIpPrefixesResponse",
    "SetVPNTunnelsRequest",
    "SetVPNTunnelsResponse",
    "ValidateConfigRequest",
    "ValidateConfigResponse",
    "Spec",
]
