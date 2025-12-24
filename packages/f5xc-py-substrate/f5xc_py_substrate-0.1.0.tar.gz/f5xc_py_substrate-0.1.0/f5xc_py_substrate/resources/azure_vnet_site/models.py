"""Pydantic models for azure_vnet_site."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AzureVnetSiteListItem(F5XCBaseModel):
    """List item for azure_vnet_site resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class BlindfoldSecretInfoType(F5XCBaseModel):
    """BlindfoldSecretInfoType specifies information about the Secret managed..."""

    decryption_provider: Optional[str] = None
    location: Optional[str] = None
    store_provider: Optional[str] = None


class ClearSecretInfoType(F5XCBaseModel):
    """ClearSecretInfoType specifies information about the Secret that is not encrypted."""

    provider: Optional[str] = None
    url: Optional[str] = None


class SecretType(F5XCBaseModel):
    """SecretType is used in an object to indicate a sensitive/confidential field"""

    blindfold_secret_info: Optional[BlindfoldSecretInfoType] = None
    clear_secret_info: Optional[ClearSecretInfoType] = None


class ExpressRouteOtherSubscriptionConnection(F5XCBaseModel):
    """Express Route Circuit Config From Other Subscription"""

    authorized_key: Optional[SecretType] = None
    circuit_id: Optional[str] = None


class ExpressRouteConnectionType(F5XCBaseModel):
    """Express Route Connection Configuration"""

    circuit_id: Optional[str] = None
    metadata: Optional[MessageMetaType] = None
    other_subscription: Optional[ExpressRouteOtherSubscriptionConnection] = None
    weight: Optional[int] = None


class AzureSpecialSubnetType(F5XCBaseModel):
    """Parameters for Azure special subnet which name is reserved. (i.e..."""

    subnet_resource_grp: Optional[str] = None
    vnet_resource_group: Optional[Any] = None


class CloudSubnetParamType(F5XCBaseModel):
    """Parameters for creating a new cloud subnet"""

    ipv4: Optional[str] = None


class AzureSubnetChoiceWithAutoType(F5XCBaseModel):
    """Parameters for Azure subnet"""

    auto: Optional[Any] = None
    subnet: Optional[AzureSpecialSubnetType] = None
    subnet_param: Optional[CloudSubnetParamType] = None


class CloudLinkADNType(F5XCBaseModel):
    cloudlink_network_name: Optional[str] = None


class ExpressRouteConfigType(F5XCBaseModel):
    """Express Route Configuration"""

    advertise_to_route_server: Optional[Any] = None
    auto_asn: Optional[Any] = None
    connections: Optional[list[ExpressRouteConnectionType]] = None
    custom_asn: Optional[int] = None
    do_not_advertise_to_route_server: Optional[Any] = None
    gateway_subnet: Optional[AzureSubnetChoiceWithAutoType] = None
    route_server_subnet: Optional[AzureSubnetChoiceWithAutoType] = None
    site_registration_over_express_route: Optional[CloudLinkADNType] = None
    site_registration_over_internet: Optional[Any] = None
    sku_ergw1az: Optional[Any] = None
    sku_ergw2az: Optional[Any] = None
    sku_high_perf: Optional[Any] = None
    sku_standard: Optional[Any] = None


class AzureVnetType(F5XCBaseModel):
    """Resource group and name of existing Azure Vnet"""

    f5_orchestrated_routing: Optional[Any] = None
    manual_routing: Optional[Any] = None
    resource_group: Optional[str] = None
    vnet_name: Optional[str] = None


class VnetPeeringType(F5XCBaseModel):
    """VNet peering to azure VNet site"""

    auto: Optional[Any] = None
    labels: Optional[dict[str, Any]] = None
    manual: Optional[Any] = None
    vnet: Optional[AzureVnetType] = None


class AzureHubVnetType(F5XCBaseModel):
    """Hub VNet type"""

    express_route_disabled: Optional[Any] = None
    express_route_enabled: Optional[ExpressRouteConfigType] = None
    spoke_vnets: Optional[list[VnetPeeringType]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class ActiveEnhancedFirewallPoliciesType(F5XCBaseModel):
    """List of Enhanced Firewall Policies These policies use session-based..."""

    enhanced_firewall_policies: Optional[list[ObjectRefType]] = None


class ActiveForwardProxyPoliciesType(F5XCBaseModel):
    """Ordered List of Forward Proxy Policies active"""

    forward_proxy_policies: Optional[list[ObjectRefType]] = None


class ActiveNetworkPoliciesType(F5XCBaseModel):
    """List of firewall policy views."""

    network_policies: Optional[list[ObjectRefType]] = None


class GlobalConnectorType(F5XCBaseModel):
    """Global network reference for direct connection"""

    global_vn: Optional[ObjectRefType] = None


class GlobalNetworkConnectionType(F5XCBaseModel):
    """Global network connection"""

    sli_to_global_dr: Optional[GlobalConnectorType] = None
    slo_to_global_dr: Optional[GlobalConnectorType] = None


class GlobalNetworkConnectionListType(F5XCBaseModel):
    """List of global network connections"""

    global_network_connections: Optional[list[GlobalNetworkConnectionType]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class Ipv4AddressType(F5XCBaseModel):
    """IPv4 Address in dot-decimal notation"""

    addr: Optional[str] = None


class Ipv6AddressType(F5XCBaseModel):
    """IPv6 Address specified as hexadecimal numbers separated by ':'"""

    addr: Optional[str] = None


class IpAddressType(F5XCBaseModel):
    """IP Address used to specify an IPv4 or IPv6 address"""

    ipv4: Optional[Ipv4AddressType] = None
    ipv6: Optional[Ipv6AddressType] = None


class NextHopType(F5XCBaseModel):
    """Identifies the next-hop for a route"""

    interface: Optional[list[ObjectRefType]] = None
    nexthop_address: Optional[IpAddressType] = None
    type_: Optional[Literal['NEXT_HOP_DEFAULT_GATEWAY', 'NEXT_HOP_USE_CONFIGURED', 'NEXT_HOP_NETWORK_INTERFACE']] = Field(default=None, alias="type")


class Ipv4SubnetType(F5XCBaseModel):
    """IPv4 subnets specified as prefix and prefix-length. Prefix length must be <= 32"""

    plen: Optional[int] = None
    prefix: Optional[str] = None


class Ipv6SubnetType(F5XCBaseModel):
    """IPv6 subnets specified as prefix and prefix-length. prefix-legnth must be <= 128"""

    plen: Optional[int] = None
    prefix: Optional[str] = None


class IpSubnetType(F5XCBaseModel):
    """IP Address used to specify an IPv4 or IPv6 subnet addresses"""

    ipv4: Optional[Ipv4SubnetType] = None
    ipv6: Optional[Ipv6SubnetType] = None


class StaticRouteType(F5XCBaseModel):
    """Defines a static route, configuring a list of prefixes and a next-hop to..."""

    attrs: Optional[list[Literal['ROUTE_ATTR_NO_OP', 'ROUTE_ATTR_ADVERTISE', 'ROUTE_ATTR_INSTALL_HOST', 'ROUTE_ATTR_INSTALL_FORWARDING', 'ROUTE_ATTR_MERGE_ONLY']]] = None
    labels: Optional[dict[str, Any]] = None
    nexthop: Optional[NextHopType] = None
    subnets: Optional[list[IpSubnetType]] = None


class SiteStaticRoutesType(F5XCBaseModel):
    """Different ways to configure static routes"""

    custom_static_route: Optional[StaticRouteType] = None
    simple_static_route: Optional[str] = None


class SiteStaticRoutesListType(F5XCBaseModel):
    """List of static routes"""

    static_route_list: Optional[list[SiteStaticRoutesType]] = None


class AzureSubnetType(F5XCBaseModel):
    """Parameters for Azure subnet"""

    subnet_name: Optional[str] = None
    subnet_resource_grp: Optional[str] = None
    vnet_resource_group: Optional[Any] = None


class AzureSubnetChoiceType(F5XCBaseModel):
    """Parameters for Azure subnet"""

    subnet: Optional[AzureSubnetType] = None
    subnet_param: Optional[CloudSubnetParamType] = None


class AzureVnetTwoInterfaceNodeARType(F5XCBaseModel):
    """Parameters for creating two interface Node in one AZ"""

    fault_domain: Optional[int] = None
    inside_subnet: Optional[AzureSubnetChoiceType] = None
    node_number: Optional[int] = None
    outside_subnet: Optional[AzureSubnetChoiceType] = None
    update_domain: Optional[int] = None


class L3PerformanceEnhancementType(F5XCBaseModel):
    """x-required L3 enhanced performance mode options"""

    jumbo: Optional[Any] = None
    no_jumbo: Optional[Any] = None


class PerformanceEnhancementModeType(F5XCBaseModel):
    """x-required Optimize the site for L3 or L7 traffic processing. L7..."""

    perf_mode_l3_enhanced: Optional[L3PerformanceEnhancementType] = None
    perf_mode_l7_enhanced: Optional[Any] = None


class AzureVnetIngressEgressGwARReplaceType(F5XCBaseModel):
    """Two interface Azure ingress/egress site for Alternate Region"""

    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    dc_cluster_group_inside_vn: Optional[ObjectRefType] = None
    dc_cluster_group_outside_vn: Optional[ObjectRefType] = None
    forward_proxy_allow_all: Optional[Any] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    hub: Optional[AzureHubVnetType] = None
    inside_static_routes: Optional[SiteStaticRoutesListType] = None
    no_dc_cluster_group: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_inside_static_routes: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_outside_static_routes: Optional[Any] = None
    node: Optional[AzureVnetTwoInterfaceNodeARType] = None
    not_hub: Optional[Any] = None
    outside_static_routes: Optional[SiteStaticRoutesListType] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None


class AcceleratedNetworkingType(F5XCBaseModel):
    """x-required Accelerated Networking to reduce Latency, When Mode is..."""

    disable: Optional[Any] = None
    enable: Optional[Any] = None


class AzureVnetIngressEgressGwARType(F5XCBaseModel):
    """Two interface Azure ingress/egress site on Alternate Region with no..."""

    accelerated_networking: Optional[AcceleratedNetworkingType] = None
    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    azure_certified_hw: Optional[str] = None
    dc_cluster_group_inside_vn: Optional[ObjectRefType] = None
    dc_cluster_group_outside_vn: Optional[ObjectRefType] = None
    forward_proxy_allow_all: Optional[Any] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    hub: Optional[AzureHubVnetType] = None
    inside_static_routes: Optional[SiteStaticRoutesListType] = None
    no_dc_cluster_group: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_inside_static_routes: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_outside_static_routes: Optional[Any] = None
    node: Optional[AzureVnetTwoInterfaceNodeARType] = None
    not_hub: Optional[Any] = None
    outside_static_routes: Optional[SiteStaticRoutesListType] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None


class AzureVnetTwoInterfaceNodeType(F5XCBaseModel):
    """Parameters for creating two interface Node in one AZ"""

    azure_az: Optional[str] = None
    inside_subnet: Optional[AzureSubnetChoiceType] = None
    outside_subnet: Optional[AzureSubnetChoiceType] = None


class AzureVnetIngressEgressGwReplaceType(F5XCBaseModel):
    """Two interface Azure ingress/egress site"""

    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    az_nodes: Optional[list[AzureVnetTwoInterfaceNodeType]] = None
    dc_cluster_group_inside_vn: Optional[ObjectRefType] = None
    dc_cluster_group_outside_vn: Optional[ObjectRefType] = None
    forward_proxy_allow_all: Optional[Any] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    hub: Optional[AzureHubVnetType] = None
    inside_static_routes: Optional[SiteStaticRoutesListType] = None
    no_dc_cluster_group: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_inside_static_routes: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_outside_static_routes: Optional[Any] = None
    not_hub: Optional[Any] = None
    outside_static_routes: Optional[SiteStaticRoutesListType] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None


class AzureVnetIngressEgressGwType(F5XCBaseModel):
    """Two interface Azure ingress/egress site"""

    accelerated_networking: Optional[AcceleratedNetworkingType] = None
    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    az_nodes: Optional[list[AzureVnetTwoInterfaceNodeType]] = None
    azure_certified_hw: Optional[str] = None
    dc_cluster_group_inside_vn: Optional[ObjectRefType] = None
    dc_cluster_group_outside_vn: Optional[ObjectRefType] = None
    forward_proxy_allow_all: Optional[Any] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    hub: Optional[AzureHubVnetType] = None
    inside_static_routes: Optional[SiteStaticRoutesListType] = None
    no_dc_cluster_group: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_inside_static_routes: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_outside_static_routes: Optional[Any] = None
    not_hub: Optional[Any] = None
    outside_static_routes: Optional[SiteStaticRoutesListType] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None


class AzureVnetOneInterfaceNodeARType(F5XCBaseModel):
    """Parameters for creating Single interface Node for Alternate Region"""

    fault_domain: Optional[int] = None
    local_subnet: Optional[AzureSubnetChoiceType] = None
    node_number: Optional[int] = None
    update_domain: Optional[int] = None


class AzureVnetIngressGwARReplaceType(F5XCBaseModel):
    """Single interface Azure ingress site for Alternate Region"""

    node: Optional[AzureVnetOneInterfaceNodeARType] = None


class AzureVnetIngressGwARType(F5XCBaseModel):
    """Single interface Azure ingress site"""

    accelerated_networking: Optional[AcceleratedNetworkingType] = None
    azure_certified_hw: Optional[str] = None
    node: Optional[AzureVnetOneInterfaceNodeARType] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None


class AzureVnetOneInterfaceNodeType(F5XCBaseModel):
    """Parameters for creating Single interface Node in one AZ"""

    azure_az: Optional[str] = None
    local_subnet: Optional[AzureSubnetChoiceType] = None


class AzureVnetIngressGwReplaceType(F5XCBaseModel):
    """Single interface Azure ingress site"""

    az_nodes: Optional[list[AzureVnetOneInterfaceNodeType]] = None


class AzureVnetIngressGwType(F5XCBaseModel):
    """Single interface Azure ingress site on on Recommended Region"""

    accelerated_networking: Optional[AcceleratedNetworkingType] = None
    az_nodes: Optional[list[AzureVnetOneInterfaceNodeType]] = None
    azure_certified_hw: Optional[str] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None


class ExpressRouteInfo(F5XCBaseModel):
    """Express Route Info"""

    route_server_asn: Optional[int] = None
    route_server_ips: Optional[list[str]] = None


class NodeInstanceNameType(F5XCBaseModel):
    """Node Instance Name"""

    node_id: Optional[str] = None
    node_instance_name: Optional[str] = None


class VnetIpPrefixesType(F5XCBaseModel):
    """Azure VNet IP prefixes Info"""

    prefixes: Optional[list[str]] = None
    vnet: Optional[AzureVnetType] = None


class VNETInfoType(F5XCBaseModel):
    """Azure Vnet Info Type"""

    resource_id: Optional[str] = None
    vnet_name: Optional[str] = None


class InfoType(F5XCBaseModel):
    """Azure VNet Site information like"""

    express_route_info: Optional[ExpressRouteInfo] = None
    node_info: Optional[list[NodeInstanceNameType]] = None
    private_ips: Optional[list[str]] = None
    public_ips: Optional[list[str]] = None
    spoke_vnet_prefix_info: Optional[list[VnetIpPrefixesType]] = None
    vnet: Optional[VNETInfoType] = None


class AzureVnetVoltstackClusterARReplaceType(F5XCBaseModel):
    """App Stack cluster of single interface Azure nodes"""

    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    dc_cluster_group: Optional[ObjectRefType] = None
    forward_proxy_allow_all: Optional[Any] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    k8s_cluster: Optional[ObjectRefType] = None
    no_dc_cluster_group: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_k8s_cluster: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_outside_static_routes: Optional[Any] = None
    node: Optional[AzureVnetOneInterfaceNodeARType] = None
    outside_static_routes: Optional[SiteStaticRoutesListType] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None


class StorageClassType(F5XCBaseModel):
    """Configuration of custom storage class"""

    default_storage_class: Optional[bool] = None
    storage_class_name: Optional[str] = None


class StorageClassListType(F5XCBaseModel):
    """Add additional custom storage classes in kubernetes for this site"""

    storage_classes: Optional[list[StorageClassType]] = None


class AzureVnetVoltstackClusterARType(F5XCBaseModel):
    """App Stack Cluster of single interface Azure nodes"""

    accelerated_networking: Optional[AcceleratedNetworkingType] = None
    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    azure_certified_hw: Optional[str] = None
    dc_cluster_group: Optional[ObjectRefType] = None
    default_storage: Optional[Any] = None
    forward_proxy_allow_all: Optional[Any] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    k8s_cluster: Optional[ObjectRefType] = None
    no_dc_cluster_group: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_k8s_cluster: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_outside_static_routes: Optional[Any] = None
    node: Optional[AzureVnetOneInterfaceNodeARType] = None
    outside_static_routes: Optional[SiteStaticRoutesListType] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None
    storage_class_list: Optional[StorageClassListType] = None


class AzureVnetVoltstackClusterReplaceType(F5XCBaseModel):
    """App Stack cluster of single interface Azure nodes"""

    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    az_nodes: Optional[list[AzureVnetOneInterfaceNodeType]] = None
    dc_cluster_group: Optional[ObjectRefType] = None
    forward_proxy_allow_all: Optional[Any] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    k8s_cluster: Optional[ObjectRefType] = None
    no_dc_cluster_group: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_k8s_cluster: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_outside_static_routes: Optional[Any] = None
    outside_static_routes: Optional[SiteStaticRoutesListType] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None


class AzureVnetVoltstackClusterType(F5XCBaseModel):
    """App Stack Cluster of single interface Azure nodes"""

    accelerated_networking: Optional[AcceleratedNetworkingType] = None
    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    az_nodes: Optional[list[AzureVnetOneInterfaceNodeType]] = None
    azure_certified_hw: Optional[str] = None
    dc_cluster_group: Optional[ObjectRefType] = None
    default_storage: Optional[Any] = None
    forward_proxy_allow_all: Optional[Any] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    k8s_cluster: Optional[ObjectRefType] = None
    no_dc_cluster_group: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_k8s_cluster: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_outside_static_routes: Optional[Any] = None
    outside_static_routes: Optional[SiteStaticRoutesListType] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None
    storage_class_list: Optional[StorageClassListType] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class BlockedServices(F5XCBaseModel):
    """Disable a node local service on this site."""

    dns: Optional[Any] = None
    network_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None
    ssh: Optional[Any] = None
    web_user_interface: Optional[Any] = None


class BlockedServicesListType(F5XCBaseModel):
    """Disable node local services on this site. Note: The chosen services will..."""

    blocked_sevice: Optional[list[BlockedServices]] = None


class Coordinates(F5XCBaseModel):
    """Coordinates of the site which provides the site physical location"""

    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CustomDNS(F5XCBaseModel):
    """Custom DNS is the configured for specify CE site"""

    inside_nameserver: Optional[str] = None
    outside_nameserver: Optional[str] = None


class KubernetesUpgradeDrainConfig(F5XCBaseModel):
    """Specify batch upgrade settings for worker nodes within a site."""

    disable_vega_upgrade_mode: Optional[Any] = None
    drain_max_unavailable_node_count: Optional[int] = None
    drain_node_timeout: Optional[int] = None
    enable_vega_upgrade_mode: Optional[Any] = None


class KubernetesUpgradeDrain(F5XCBaseModel):
    """Specify how worker nodes within a site will be upgraded."""

    disable_upgrade_drain: Optional[Any] = None
    enable_upgrade_drain: Optional[KubernetesUpgradeDrainConfig] = None


class OfflineSurvivabilityModeType(F5XCBaseModel):
    """Offline Survivability allows the Site to continue functioning normally..."""

    enable_offline_survivability_mode: Optional[Any] = None
    no_offline_survivability_mode: Optional[Any] = None


class OperatingSystemType(F5XCBaseModel):
    """Select the F5XC Operating System Version for the site. By default,..."""

    default_os_version: Optional[Any] = None
    operating_system_version: Optional[str] = None


class VolterraSoftwareType(F5XCBaseModel):
    """Select the F5XC Software Version for the site. By default, latest..."""

    default_sw_version: Optional[Any] = None
    volterra_software_version: Optional[str] = None


class AzureVnetParamsType(F5XCBaseModel):
    """Parameters to create a new Azure Vnet"""

    autogenerate: Optional[Any] = None
    name: Optional[str] = None
    primary_ipv4: Optional[str] = None


class AzureVnetChoiceType(F5XCBaseModel):
    """This defines choice about Azure Vnet for a view"""

    existing_vnet: Optional[AzureVnetType] = None
    new_vnet: Optional[AzureVnetParamsType] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the Azure VNet site specification"""

    address: Optional[str] = None
    admin_password: Optional[SecretType] = None
    alternate_region: Optional[str] = None
    azure_cred: Optional[ObjectRefType] = None
    azure_region: Optional[str] = None
    block_all_services: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_dns: Optional[CustomDNS] = None
    default_blocked_services: Optional[Any] = None
    disk_size: Optional[int] = None
    ingress_egress_gw: Optional[AzureVnetIngressEgressGwType] = None
    ingress_egress_gw_ar: Optional[AzureVnetIngressEgressGwARType] = None
    ingress_gw: Optional[AzureVnetIngressGwType] = None
    ingress_gw_ar: Optional[AzureVnetIngressGwARType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    machine_type: Optional[str] = None
    no_worker_nodes: Optional[Any] = None
    nodes_per_az: Optional[int] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    os: Optional[OperatingSystemType] = None
    resource_group: Optional[str] = None
    ssh_key: Optional[str] = None
    sw: Optional[VolterraSoftwareType] = None
    tags: Optional[dict[str, Any]] = None
    total_nodes: Optional[int] = None
    vnet: Optional[AzureVnetChoiceType] = None
    voltstack_cluster: Optional[AzureVnetVoltstackClusterType] = None
    voltstack_cluster_ar: Optional[AzureVnetVoltstackClusterARType] = None


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class SiteError(F5XCBaseModel):
    """Site Error"""

    error_description: Optional[str] = None
    suggested_action: Optional[str] = None


class GetSpecType(F5XCBaseModel):
    """Shape of the Azure VNet site specification"""

    address: Optional[str] = None
    admin_password: Optional[SecretType] = None
    alternate_region: Optional[str] = None
    azure_cred: Optional[ObjectRefType] = None
    azure_region: Optional[str] = None
    block_all_services: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    cloud_site_info: Optional[InfoType] = None
    coordinates: Optional[Coordinates] = None
    custom_dns: Optional[CustomDNS] = None
    default_blocked_services: Optional[Any] = None
    disk_size: Optional[int] = None
    error_description: Optional[str] = None
    ingress_egress_gw: Optional[AzureVnetIngressEgressGwType] = None
    ingress_egress_gw_ar: Optional[AzureVnetIngressEgressGwARType] = None
    ingress_gw: Optional[AzureVnetIngressGwType] = None
    ingress_gw_ar: Optional[AzureVnetIngressGwARType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    machine_type: Optional[str] = None
    no_worker_nodes: Optional[Any] = None
    nodes_per_az: Optional[int] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    resource_group: Optional[str] = None
    site_errors: Optional[list[SiteError]] = None
    site_state: Optional[Literal['ONLINE', 'PROVISIONING', 'UPGRADING', 'STANDBY', 'FAILED', 'REREGISTRATION', 'WAITINGNODES', 'DECOMMISSIONING', 'WAITING_FOR_REGISTRATION', 'ORCHESTRATION_IN_PROGRESS', 'ORCHESTRATION_COMPLETE', 'ERROR_IN_ORCHESTRATION', 'DELETING_CLOUD_RESOURCES', 'DELETED_CLOUD_RESOURCES', 'ERROR_DELETING_CLOUD_RESOURCES', 'VALIDATION_IN_PROGRESS', 'VALIDATION_SUCCESS', 'VALIDATION_FAILED']] = None
    ssh_key: Optional[str] = None
    suggested_action: Optional[str] = None
    tags: Optional[dict[str, Any]] = None
    total_nodes: Optional[int] = None
    validation_state: Optional[Literal['VALIDATION_STATE_NONE', 'VALIDATION_IN_PROGRESS', 'VALIDATION_FAILED', 'VALIDATION_SUCCEEDED']] = None
    vnet: Optional[AzureVnetChoiceType] = None
    voltstack_cluster: Optional[AzureVnetVoltstackClusterType] = None
    voltstack_cluster_ar: Optional[AzureVnetVoltstackClusterARType] = None


class InitializerType(F5XCBaseModel):
    """Initializer is information about an initializer that has not yet completed."""

    name: Optional[str] = None


class StatusType(F5XCBaseModel):
    """Status is a return value for calls that don't return other objects."""

    code: Optional[int] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class InitializersType(F5XCBaseModel):
    """Initializers tracks the progress of initialization of a configuration object"""

    pending: Optional[list[InitializerType]] = None
    result: Optional[StatusType] = None


class ViewRefType(F5XCBaseModel):
    """ViewRefType represents a reference to a view"""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class SystemObjectGetMetaType(F5XCBaseModel):
    """SystemObjectGetMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Shape of the Azure VNet site replace specification"""

    address: Optional[str] = None
    alternate_region: Optional[str] = None
    azure_cred: Optional[ObjectRefType] = None
    azure_region: Optional[str] = None
    block_all_services: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_dns: Optional[CustomDNS] = None
    default_blocked_services: Optional[Any] = None
    disk_size: Optional[int] = None
    ingress_egress_gw: Optional[AzureVnetIngressEgressGwReplaceType] = None
    ingress_egress_gw_ar: Optional[AzureVnetIngressEgressGwARReplaceType] = None
    ingress_gw: Optional[AzureVnetIngressGwReplaceType] = None
    ingress_gw_ar: Optional[AzureVnetIngressGwARReplaceType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    machine_type: Optional[str] = None
    no_worker_nodes: Optional[Any] = None
    nodes_per_az: Optional[int] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    resource_group: Optional[str] = None
    ssh_key: Optional[str] = None
    total_nodes: Optional[int] = None
    vnet: Optional[AzureVnetChoiceType] = None
    voltstack_cluster: Optional[AzureVnetVoltstackClusterReplaceType] = None
    voltstack_cluster_ar: Optional[AzureVnetVoltstackClusterARReplaceType] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class ApplyStatus(F5XCBaseModel):
    apply_state: Optional[Literal['APPLIED', 'APPLY_ERRORED', 'APPLY_INIT_ERRORED', 'APPLYING', 'APPLY_PLANNING', 'APPLY_PLAN_ERRORED', 'APPLY_QUEUED']] = None
    container_version: Optional[str] = None
    destroy_state: Optional[Literal['DESTROYED', 'DESTROY_ERRORED', 'DESTROYING', 'DESTROY_QUEUED']] = None
    error_output: Optional[str] = None
    infra_state: Optional[Literal['PROVISIONED', 'TIMED_OUT', 'ERRORED', 'PROVISIONING']] = None
    modification_timestamp: Optional[str] = None
    suggested_action: Optional[str] = None
    tf_output: Optional[str] = None
    tf_stdout: Optional[str] = None


class PlanStatus(F5XCBaseModel):
    error_output: Optional[str] = None
    infra_state: Optional[Literal['PROVISIONED', 'TIMED_OUT', 'ERRORED', 'PROVISIONING']] = None
    modification_timestamp: Optional[str] = None
    plan_state: Optional[Literal['PLANNING', 'PLAN_ERRORED', 'NO_CHANGES', 'HAS_CHANGES', 'DISCARDED', 'PLAN_INIT_ERRORED', 'PLAN_QUEUED']] = None
    suggested_action: Optional[str] = None
    tf_plan_output: Optional[str] = None


class DeploymentStatusType(F5XCBaseModel):
    apply_status: Optional[ApplyStatus] = None
    expected_container_version: Optional[str] = None
    plan_status: Optional[PlanStatus] = None


class StatusMetaType(F5XCBaseModel):
    """StatusMetaType is metadata that all status must have."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_id: Optional[str] = None
    publish: Optional[Literal['STATUS_DO_NOT_PUBLISH', 'STATUS_PUBLISH']] = None
    status_id: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class AzureRouteTableWithStaticRoute(F5XCBaseModel):
    """Azure Route Table with Static Route"""

    route_table_id: Optional[str] = None
    static_routes: Optional[list[str]] = None


class AzureRouteTableWithStaticRouteListType(F5XCBaseModel):
    """List Azure Route Table with Static Route"""

    route_tables: Optional[list[AzureRouteTableWithStaticRoute]] = None


class SubnetStatusType(F5XCBaseModel):
    """Network Interface Status"""

    availability_zone: Optional[str] = None
    interface_type: Optional[str] = None
    network_interface_id: Optional[str] = None
    private_ipv4_address: Optional[str] = None
    status: Optional[str] = None
    subnet_id: Optional[str] = None


class AzureAttachmentsStatusType(F5XCBaseModel):
    """Azure Attachment Status Type"""

    deployment_status: Optional[str] = None
    hub_owner_subscriptionid: Optional[str] = None
    hub_vnet_name: Optional[str] = None
    hub_vnet_resource_group: Optional[str] = None
    installed_routes: Optional[AzureRouteTableWithStaticRouteListType] = None
    peering_state: Optional[str] = None
    peering_sync_level: Optional[str] = None
    provisioning_state: Optional[str] = None
    spoke_subscription_id: Optional[str] = None
    spoke_vnet_id: Optional[str] = None
    subnets: Optional[list[SubnetStatusType]] = None
    tags: Optional[dict[str, Any]] = None
    vnet_attachment_id: Optional[str] = None
    vnet_cidr: Optional[str] = None


class AzureAttachmentsListStatusType(F5XCBaseModel):
    """Azure VEspokeNT Attachment List Status Type"""

    attachment_status: Optional[list[AzureAttachmentsStatusType]] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    deployment: Optional[DeploymentStatusType] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    vnet_attachment: Optional[AzureAttachmentsListStatusType] = None


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[CreateRequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[ReplaceRequest] = None
    spec: Optional[GetSpecType] = None
    status: Optional[list[StatusObject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of azure_vnet_site is returned in 'List'. By..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[GetSpecType] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[StatusObject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[ListResponseItem]] = None


class ReplaceResponse(F5XCBaseModel):
    pass


class SetCloudSiteInfoRequest(F5XCBaseModel):
    """Request to configure Cloud Site Information"""

    azure_vnet_info: Optional[InfoType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class SetCloudSiteInfoResponse(F5XCBaseModel):
    """Response to configure configure Cloud Site Information"""

    pass


class PublishVIPParamsPerAz(F5XCBaseModel):
    """x-displayName: 'Publish VIP Params Per AZ' Per AZ parameters needed to..."""

    az_name: Optional[str] = None
    inside_vip: Optional[list[str]] = None
    inside_vip_cname: Optional[str] = None
    inside_vip_v6: Optional[list[str]] = None
    outside_vip: Optional[list[str]] = None
    outside_vip_cname: Optional[str] = None
    outside_vip_v6: Optional[list[str]] = None


class SetVIPInfoRequest(F5XCBaseModel):
    """Request to configure Azure VNet Site VIP information"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    vip_params_per_az: Optional[list[PublishVIPParamsPerAz]] = None


class SetVIPInfoResponse(F5XCBaseModel):
    pass


class ValidateConfigRequest(F5XCBaseModel):
    """Request to validate AWS VPC site configuration"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class ValidateConfigResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = AzureSpecialSubnetType
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
