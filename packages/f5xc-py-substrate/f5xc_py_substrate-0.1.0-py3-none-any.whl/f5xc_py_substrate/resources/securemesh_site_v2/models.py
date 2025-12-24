"""Pydantic models for securemesh_site_v2."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class SecuremeshSiteV2ListItem(F5XCBaseModel):
    """List item for securemesh_site_v2 resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class BlockedServices(F5XCBaseModel):
    """Disable a node local service on this site."""

    dns: Optional[Any] = None
    network_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None
    ssh: Optional[Any] = None
    web_user_interface: Optional[Any] = None


class BlockedServicesListType(F5XCBaseModel):
    """Disable node local services on this site. Note: The chosen services will..."""

    blocked_sevice: Optional[list[BlockedServices]] = None


class BondLacpType(F5XCBaseModel):
    """LACP parameters for the bond device"""

    rate: Optional[int] = None


class FleetBondDeviceType(F5XCBaseModel):
    """Bond devices configuration for fleet"""

    active_backup: Optional[Any] = None
    devices: Optional[list[str]] = None
    lacp: Optional[BondLacpType] = None
    link_polling_interval: Optional[int] = None
    link_up_delay: Optional[int] = None
    name: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


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


class DHCPIPV6PoolType(F5XCBaseModel):
    """DHCP IPV6 pool is a range of IP addresses (start ip and end ip)."""

    end_ip: Optional[str] = None
    start_ip: Optional[str] = None


class DHCPIPV6NetworkType(F5XCBaseModel):
    """DHCP IPV6 network type configuration"""

    network_prefix: Optional[str] = None
    pool_settings: Optional[Literal['INCLUDE_IP_ADDRESSES_FROM_DHCP_POOLS', 'EXCLUDE_IP_ADDRESSES_FROM_DHCP_POOLS']] = None
    pools: Optional[list[DHCPIPV6PoolType]] = None


class DHCPInterfaceIPV6Type(F5XCBaseModel):
    """Map of Interface IPV6 assignments per node"""

    interface_ip_map: Optional[dict[str, Any]] = None


class DHCPIPV6StatefulServer(F5XCBaseModel):
    automatic_from_end: Optional[Any] = None
    automatic_from_start: Optional[Any] = None
    dhcp_networks: Optional[list[DHCPIPV6NetworkType]] = None
    fixed_ip_map: Optional[dict[str, Any]] = None
    interface_ip_map: Optional[DHCPInterfaceIPV6Type] = None


class IPV6DnsList(F5XCBaseModel):
    dns_list: Optional[list[str]] = None


class IPV6LocalDnsAddress(F5XCBaseModel):
    configured_address: Optional[str] = None
    first_address: Optional[Any] = None
    last_address: Optional[Any] = None


class IPV6DnsConfig(F5XCBaseModel):
    configured_list: Optional[IPV6DnsList] = None
    local_dns: Optional[IPV6LocalDnsAddress] = None


class IPV6AutoConfigRouterType(F5XCBaseModel):
    dns_config: Optional[IPV6DnsConfig] = None
    network_prefix: Optional[str] = None
    stateful: Optional[DHCPIPV6StatefulServer] = None


class IPV6AutoConfigType(F5XCBaseModel):
    host: Optional[Any] = None
    router: Optional[IPV6AutoConfigRouterType] = None


class LinkQualityMonitorConfig(F5XCBaseModel):
    """Link Quality Monitoring configuration for a network interface."""

    pass


class StaticIpParametersClusterType(F5XCBaseModel):
    """Configure Static IP parameters  for cluster"""

    interface_ip_map: Optional[dict[str, Any]] = None


class StaticIpParametersNodeType(F5XCBaseModel):
    """Configure Static IP parameters for a node"""

    default_gw: Optional[str] = None
    ip_address: Optional[str] = None


class StaticIPParametersType(F5XCBaseModel):
    """Configure Static IP parameters"""

    cluster_static_ip: Optional[StaticIpParametersClusterType] = None
    node_static_ip: Optional[StaticIpParametersNodeType] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class BlindfoldSecretInfoType(F5XCBaseModel):
    """BlindfoldSecretInfoType specifies information about the Secret managed..."""

    decryption_provider: Optional[str] = None
    location: Optional[str] = None
    store_provider: Optional[str] = None


class ClearSecretInfoType(F5XCBaseModel):
    """ClearSecretInfoType specifies information about the Secret that is not encrypted."""

    provider: Optional[str] = None
    url: Optional[str] = None


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


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


class NodeInterfaceInfo(F5XCBaseModel):
    """On a multinode site, this list holds the nodes and corresponding tunnel..."""

    interface: Optional[list[ObjectRefType]] = None
    node: Optional[str] = None


class NodeInterfaceType(F5XCBaseModel):
    """On multinode site, this type holds the information about per node interfaces"""

    list_: Optional[list[NodeInterfaceInfo]] = Field(default=None, alias="list")


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
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


class SecretType(F5XCBaseModel):
    """SecretType is used in an object to indicate a sensitive/confidential field"""

    blindfold_secret_info: Optional[BlindfoldSecretInfoType] = None
    clear_secret_info: Optional[ClearSecretInfoType] = None


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


class ViewssecuremeshSiteV2ethernetinterfacetype(F5XCBaseModel):
    device: Optional[str] = None
    mac: Optional[str] = None


class NetworkSelectType(F5XCBaseModel):
    """x-required Select virtual network (VRF) for this interface. There are 2..."""

    site_local_inside_network: Optional[Any] = None
    site_local_network: Optional[Any] = None


class SecuremeshSiteV2vlaninterfacetype(F5XCBaseModel):
    device: Optional[str] = None
    vlan_id: Optional[int] = None


class SecuremeshSiteV2interface(F5XCBaseModel):
    """Interface definition"""

    bond_interface: Optional[FleetBondDeviceType] = None
    description: Optional[str] = None
    dhcp_client: Optional[Any] = None
    ethernet_interface: Optional[ViewssecuremeshSiteV2ethernetinterfacetype] = None
    ipv6_auto_config: Optional[IPV6AutoConfigType] = None
    labels: Optional[dict[str, Any]] = None
    monitor: Optional[Any] = None
    monitor_disabled: Optional[Any] = None
    mtu: Optional[int] = None
    name: Optional[str] = None
    network_option: Optional[NetworkSelectType] = None
    no_ipv4_address: Optional[Any] = None
    no_ipv6_address: Optional[Any] = None
    priority: Optional[int] = None
    site_to_site_connectivity_interface_disabled: Optional[Any] = None
    site_to_site_connectivity_interface_enabled: Optional[Any] = None
    static_ip: Optional[StaticIpParametersNodeType] = None
    static_ipv6_address: Optional[StaticIPParametersType] = None
    vlan_interface: Optional[SecuremeshSiteV2vlaninterfacetype] = None


class ViewssecuremeshSiteV2node(F5XCBaseModel):
    """Node definition"""

    hostname: Optional[str] = None
    interface_list: Optional[list[SecuremeshSiteV2interface]] = None
    public_ip: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class SecuremeshSiteV2nodelist(F5XCBaseModel):
    """This section will show nodes associated with this site. Note: For sites..."""

    node_list: Optional[list[ViewssecuremeshSiteV2node]] = None


class SecuremeshSiteV2awsprovidertype(F5XCBaseModel):
    """AWS Provider Type"""

    not_managed: Optional[SecuremeshSiteV2nodelist] = None


class SecuremeshSiteV2azureprovidertype(F5XCBaseModel):
    """Azure Provider Type"""

    not_managed: Optional[SecuremeshSiteV2nodelist] = None


class SecuremeshSiteV2baremetalprovidertype(F5XCBaseModel):
    """Baremetal Provider Type"""

    not_managed: Optional[SecuremeshSiteV2nodelist] = None


class AdminUserCredentialsType(F5XCBaseModel):
    """Setup user credentials to manage access to nodes belonging to the site...."""

    admin_password: Optional[SecretType] = None
    ssh_key: Optional[str] = None


class SecuremeshSiteV2customproxy(F5XCBaseModel):
    """Custom Enterprise Proxy"""

    disable_re_tunnel: Optional[Any] = None
    enable_re_tunnel: Optional[Any] = None
    password: Optional[SecretType] = None
    proxy_ip_address: Optional[str] = None
    proxy_port: Optional[int] = None
    username: Optional[str] = None


class SecuremeshSiteV2customproxybypasssettings(F5XCBaseModel):
    """List of domains to bypass the proxy"""

    proxy_bypass: Optional[list[str]] = None


class SecuremeshSiteV2customdnssettings(F5XCBaseModel):
    """DNS Servers"""

    dns_servers: Optional[list[str]] = None


class SecuremeshSiteV2customntpsettings(F5XCBaseModel):
    """NTP Servers"""

    ntp_servers: Optional[list[str]] = None


class SecuremeshSiteV2dnsntpserverconfig(F5XCBaseModel):
    """Specify DNS and NTP servers that will be used by the nodes in this..."""

    custom_dns: Optional[SecuremeshSiteV2customdnssettings] = None
    custom_ntp: Optional[SecuremeshSiteV2customntpsettings] = None
    f5_dns_default: Optional[Any] = None
    f5_ntp_default: Optional[Any] = None


class SecuremeshSiteV2equinixprovidertype(F5XCBaseModel):
    """Equinix Provider Type"""

    not_managed: Optional[SecuremeshSiteV2nodelist] = None


class SecuremeshSiteV2gcpprovidertype(F5XCBaseModel):
    """GCP Provider Type"""

    not_managed: Optional[SecuremeshSiteV2nodelist] = None


class SecuremeshSiteV2kvmprovidertype(F5XCBaseModel):
    """KVM Provider Type"""

    not_managed: Optional[SecuremeshSiteV2nodelist] = None


class SecuremeshSiteV2loadbalancingsettingstype(F5XCBaseModel):
    """This section contains settings on the site that relate to Load Balancing..."""

    vip_vrrp_mode: Optional[Literal['VIP_VRRP_INVALID', 'VIP_VRRP_ENABLE', 'VIP_VRRP_DISABLE']] = None


class StaticRouteViewType(F5XCBaseModel):
    """Defines a static route, configuring a list of prefixes and a next-hop to..."""

    attrs: Optional[list[Literal['ROUTE_ATTR_NO_OP', 'ROUTE_ATTR_ADVERTISE', 'ROUTE_ATTR_INSTALL_HOST', 'ROUTE_ATTR_INSTALL_FORWARDING', 'ROUTE_ATTR_MERGE_ONLY']]] = None
    default_gateway: Optional[Any] = None
    ip_address: Optional[str] = None
    ip_prefixes: Optional[list[str]] = None
    node_interface: Optional[NodeInterfaceType] = None


class SecuremeshSiteV2staticrouteslisttype(F5XCBaseModel):
    static_routes: Optional[list[StaticRouteViewType]] = None


class StaticV6RouteViewType(F5XCBaseModel):
    """Defines a static route of IPv6 prefixes, configuring a list of prefixes..."""

    attrs: Optional[list[Literal['ROUTE_ATTR_NO_OP', 'ROUTE_ATTR_ADVERTISE', 'ROUTE_ATTR_INSTALL_HOST', 'ROUTE_ATTR_INSTALL_FORWARDING', 'ROUTE_ATTR_MERGE_ONLY']]] = None
    default_gateway: Optional[Any] = None
    ip_address: Optional[str] = None
    ip_prefixes: Optional[list[str]] = None
    node_interface: Optional[NodeInterfaceType] = None


class StaticV6RoutesListType(F5XCBaseModel):
    """List of IPv6 static routes"""

    static_routes: Optional[list[StaticV6RouteViewType]] = None


class SecuremeshSiteV2virtualnetworkconfiguration(F5XCBaseModel):
    """Site local network configuration"""

    labels: Optional[dict[str, Any]] = None
    nameserver: Optional[str] = None
    no_static_routes: Optional[Any] = None
    no_v6_static_routes: Optional[Any] = None
    static_routes: Optional[SecuremeshSiteV2staticrouteslisttype] = None
    static_v6_routes: Optional[StaticV6RoutesListType] = None
    vip: Optional[str] = None


class SecuremeshSiteV2localvrfsettingtype(F5XCBaseModel):
    """There can be two local VRFs on each site. The Site Local Outside (SLO)..."""

    default_config: Optional[Any] = None
    default_sli_config: Optional[Any] = None
    sli_config: Optional[SecuremeshSiteV2virtualnetworkconfiguration] = None
    slo_config: Optional[SecuremeshSiteV2virtualnetworkconfiguration] = None


class SecuremeshSiteV2nutanixprovidertype(F5XCBaseModel):
    """Nutanix Provider Type"""

    not_managed: Optional[SecuremeshSiteV2nodelist] = None


class SecuremeshSiteV2ociprovidertype(F5XCBaseModel):
    """OCI Provider Type"""

    not_managed: Optional[SecuremeshSiteV2nodelist] = None


class OfflineSurvivabilityModeType(F5XCBaseModel):
    """Offline Survivability allows the Site to continue functioning normally..."""

    enable_offline_survivability_mode: Optional[Any] = None
    no_offline_survivability_mode: Optional[Any] = None


class SecuremeshSiteV2openstackprovidertype(F5XCBaseModel):
    """Openstack Provider Type"""

    not_managed: Optional[SecuremeshSiteV2nodelist] = None


class L3PerformanceEnhancementType(F5XCBaseModel):
    """x-required L3 enhanced performance mode options"""

    jumbo: Optional[Any] = None
    no_jumbo: Optional[Any] = None


class PerformanceEnhancementModeType(F5XCBaseModel):
    """x-required Optimize the site for L3 or L7 traffic processing. L7..."""

    perf_mode_l3_enhanced: Optional[L3PerformanceEnhancementType] = None
    perf_mode_l7_enhanced: Optional[Any] = None


class SpecificRE(F5XCBaseModel):
    """Select specific REs. This is useful when a site needs to..."""

    primary_re: Optional[str] = None


class RegionalEdgeSelection(F5XCBaseModel):
    """Selection criteria to connect the site with F5 Distributed Cloud..."""

    geo_proximity: Optional[Any] = None
    specific_re: Optional[SpecificRE] = None


class SecuremeshSiteV2sitemeshgrouptype(F5XCBaseModel):
    """Select how the site mesh group will be connected. By default, public IPs..."""

    no_site_mesh_group: Optional[Any] = None
    site_mesh_group: Optional[ObjectRefType] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None


class OperatingSystemType(F5XCBaseModel):
    """Select the F5XC Operating System Version for the site. By default,..."""

    default_os_version: Optional[Any] = None
    operating_system_version: Optional[str] = None


class VolterraSoftwareType(F5XCBaseModel):
    """Select the F5XC Software Version for the site. By default, latest..."""

    default_sw_version: Optional[Any] = None
    volterra_software_version: Optional[str] = None


class SecuremeshSiteV2softwaresettingstype(F5XCBaseModel):
    """Select OS and Software version for the site. All nodes in the site will..."""

    os: Optional[OperatingSystemType] = None
    sw: Optional[VolterraSoftwareType] = None


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


class SecuremeshSiteV2upgradesettingstype(F5XCBaseModel):
    """Specify how a site will be upgraded."""

    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None


class SecuremeshSiteV2vmwareprovidertype(F5XCBaseModel):
    """VMware Provider Type"""

    not_managed: Optional[SecuremeshSiteV2nodelist] = None


class ViewssecuremeshSiteV2createspectype(F5XCBaseModel):
    """Shape of the Secure Mesh site specification"""

    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    admin_user_credentials: Optional[AdminUserCredentialsType] = None
    aws: Optional[SecuremeshSiteV2awsprovidertype] = None
    azure: Optional[SecuremeshSiteV2azureprovidertype] = None
    baremetal: Optional[SecuremeshSiteV2baremetalprovidertype] = None
    block_all_services: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    custom_proxy: Optional[SecuremeshSiteV2customproxy] = None
    custom_proxy_bypass: Optional[SecuremeshSiteV2customproxybypasssettings] = None
    dc_cluster_group_sli: Optional[ObjectRefType] = None
    dc_cluster_group_slo: Optional[ObjectRefType] = None
    disable_ha: Optional[Any] = None
    disable_url_categorization: Optional[Any] = None
    dns_ntp_config: Optional[SecuremeshSiteV2dnsntpserverconfig] = None
    enable_ha: Optional[Any] = None
    enable_url_categorization: Optional[Any] = None
    equinix: Optional[SecuremeshSiteV2equinixprovidertype] = None
    f5_proxy: Optional[Any] = None
    gcp: Optional[SecuremeshSiteV2gcpprovidertype] = None
    kvm: Optional[SecuremeshSiteV2kvmprovidertype] = None
    load_balancing: Optional[SecuremeshSiteV2loadbalancingsettingstype] = None
    local_vrf: Optional[SecuremeshSiteV2localvrfsettingtype] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_proxy_bypass: Optional[Any] = None
    no_s2s_connectivity_sli: Optional[Any] = None
    no_s2s_connectivity_slo: Optional[Any] = None
    nutanix: Optional[SecuremeshSiteV2nutanixprovidertype] = None
    oci: Optional[SecuremeshSiteV2ociprovidertype] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    openstack: Optional[SecuremeshSiteV2openstackprovidertype] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    re_select: Optional[RegionalEdgeSelection] = None
    site_mesh_group_on_slo: Optional[SecuremeshSiteV2sitemeshgrouptype] = None
    software_settings: Optional[SecuremeshSiteV2softwaresettingstype] = None
    tunnel_dead_timeout: Optional[int] = None
    tunnel_type: Optional[Literal['SITE_TO_SITE_TUNNEL_IPSEC_OR_SSL', 'SITE_TO_SITE_TUNNEL_IPSEC', 'SITE_TO_SITE_TUNNEL_SSL']] = None
    upgrade_settings: Optional[SecuremeshSiteV2upgradesettingstype] = None
    vmware: Optional[SecuremeshSiteV2vmwareprovidertype] = None


class SecuremeshSiteV2createrequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[ViewssecuremeshSiteV2createspectype] = None


class SiteError(F5XCBaseModel):
    """Site Error"""

    error_description: Optional[str] = None
    suggested_action: Optional[str] = None


class ViewssecuremeshSiteV2getspectype(F5XCBaseModel):
    """Shape of the Secure Mesh site specification"""

    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    admin_user_credentials: Optional[AdminUserCredentialsType] = None
    aws: Optional[SecuremeshSiteV2awsprovidertype] = None
    azure: Optional[SecuremeshSiteV2azureprovidertype] = None
    baremetal: Optional[SecuremeshSiteV2baremetalprovidertype] = None
    block_all_services: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    custom_proxy: Optional[SecuremeshSiteV2customproxy] = None
    custom_proxy_bypass: Optional[SecuremeshSiteV2customproxybypasssettings] = None
    dc_cluster_group_sli: Optional[ObjectRefType] = None
    dc_cluster_group_slo: Optional[ObjectRefType] = None
    disable_ha: Optional[Any] = None
    disable_url_categorization: Optional[Any] = None
    dns_ntp_config: Optional[SecuremeshSiteV2dnsntpserverconfig] = None
    enable_ha: Optional[Any] = None
    enable_url_categorization: Optional[Any] = None
    equinix: Optional[SecuremeshSiteV2equinixprovidertype] = None
    f5_proxy: Optional[Any] = None
    gcp: Optional[SecuremeshSiteV2gcpprovidertype] = None
    kvm: Optional[SecuremeshSiteV2kvmprovidertype] = None
    load_balancing: Optional[SecuremeshSiteV2loadbalancingsettingstype] = None
    local_vrf: Optional[SecuremeshSiteV2localvrfsettingtype] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_proxy_bypass: Optional[Any] = None
    no_s2s_connectivity_sli: Optional[Any] = None
    no_s2s_connectivity_slo: Optional[Any] = None
    nutanix: Optional[SecuremeshSiteV2nutanixprovidertype] = None
    oci: Optional[SecuremeshSiteV2ociprovidertype] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    openstack: Optional[SecuremeshSiteV2openstackprovidertype] = None
    operating_system_version: Optional[str] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    re_select: Optional[RegionalEdgeSelection] = None
    site_errors: Optional[list[SiteError]] = None
    site_mesh_group_on_slo: Optional[SecuremeshSiteV2sitemeshgrouptype] = None
    site_state: Optional[Literal['ONLINE', 'PROVISIONING', 'UPGRADING', 'STANDBY', 'FAILED', 'REREGISTRATION', 'WAITINGNODES', 'DECOMMISSIONING', 'WAITING_FOR_REGISTRATION', 'ORCHESTRATION_IN_PROGRESS', 'ORCHESTRATION_COMPLETE', 'ERROR_IN_ORCHESTRATION', 'DELETING_CLOUD_RESOURCES', 'DELETED_CLOUD_RESOURCES', 'ERROR_DELETING_CLOUD_RESOURCES', 'VALIDATION_IN_PROGRESS', 'VALIDATION_SUCCESS', 'VALIDATION_FAILED']] = None
    software_settings: Optional[SecuremeshSiteV2softwaresettingstype] = None
    tunnel_dead_timeout: Optional[int] = None
    tunnel_type: Optional[Literal['SITE_TO_SITE_TUNNEL_IPSEC_OR_SSL', 'SITE_TO_SITE_TUNNEL_IPSEC', 'SITE_TO_SITE_TUNNEL_SSL']] = None
    upgrade_settings: Optional[SecuremeshSiteV2upgradesettingstype] = None
    vmware: Optional[SecuremeshSiteV2vmwareprovidertype] = None
    volterra_software_version: Optional[str] = None


class SecuremeshSiteV2createresponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[ViewssecuremeshSiteV2getspectype] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class SecuremeshSiteV2deleterequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ViewssecuremeshSiteV2replacespectype(F5XCBaseModel):
    """Shape of the Secure Mesh site specification"""

    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    admin_user_credentials: Optional[AdminUserCredentialsType] = None
    aws: Optional[SecuremeshSiteV2awsprovidertype] = None
    azure: Optional[SecuremeshSiteV2azureprovidertype] = None
    baremetal: Optional[SecuremeshSiteV2baremetalprovidertype] = None
    block_all_services: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    custom_proxy: Optional[SecuremeshSiteV2customproxy] = None
    custom_proxy_bypass: Optional[SecuremeshSiteV2customproxybypasssettings] = None
    dc_cluster_group_sli: Optional[ObjectRefType] = None
    dc_cluster_group_slo: Optional[ObjectRefType] = None
    disable_ha: Optional[Any] = None
    disable_url_categorization: Optional[Any] = None
    dns_ntp_config: Optional[SecuremeshSiteV2dnsntpserverconfig] = None
    enable_ha: Optional[Any] = None
    enable_url_categorization: Optional[Any] = None
    equinix: Optional[SecuremeshSiteV2equinixprovidertype] = None
    f5_proxy: Optional[Any] = None
    gcp: Optional[SecuremeshSiteV2gcpprovidertype] = None
    kvm: Optional[SecuremeshSiteV2kvmprovidertype] = None
    load_balancing: Optional[SecuremeshSiteV2loadbalancingsettingstype] = None
    local_vrf: Optional[SecuremeshSiteV2localvrfsettingtype] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    no_proxy_bypass: Optional[Any] = None
    no_s2s_connectivity_sli: Optional[Any] = None
    no_s2s_connectivity_slo: Optional[Any] = None
    nutanix: Optional[SecuremeshSiteV2nutanixprovidertype] = None
    oci: Optional[SecuremeshSiteV2ociprovidertype] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    openstack: Optional[SecuremeshSiteV2openstackprovidertype] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    re_select: Optional[RegionalEdgeSelection] = None
    site_mesh_group_on_slo: Optional[SecuremeshSiteV2sitemeshgrouptype] = None
    software_settings: Optional[SecuremeshSiteV2softwaresettingstype] = None
    tunnel_dead_timeout: Optional[int] = None
    tunnel_type: Optional[Literal['SITE_TO_SITE_TUNNEL_IPSEC_OR_SSL', 'SITE_TO_SITE_TUNNEL_IPSEC', 'SITE_TO_SITE_TUNNEL_SSL']] = None
    upgrade_settings: Optional[SecuremeshSiteV2upgradesettingstype] = None
    vmware: Optional[SecuremeshSiteV2vmwareprovidertype] = None


class SecuremeshSiteV2replacerequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ViewssecuremeshSiteV2replacespectype] = None


class SecuremeshSiteV2statusobject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


class SecuremeshSiteV2getresponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[SecuremeshSiteV2createrequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[SecuremeshSiteV2replacerequest] = None
    spec: Optional[ViewssecuremeshSiteV2getspectype] = None
    status: Optional[list[SecuremeshSiteV2statusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class SecuremeshSiteV2listresponseitem(F5XCBaseModel):
    """By default a summary of securemesh_site_v2 is returned in 'List'. By..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[ViewssecuremeshSiteV2getspectype] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[SecuremeshSiteV2statusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class SecuremeshSiteV2listresponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[SecuremeshSiteV2listresponseitem]] = None


class SecuremeshSiteV2replaceresponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = SpecificRE
