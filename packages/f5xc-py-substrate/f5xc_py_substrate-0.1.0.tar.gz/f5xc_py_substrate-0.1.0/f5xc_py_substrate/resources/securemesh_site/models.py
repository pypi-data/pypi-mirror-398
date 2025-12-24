"""Pydantic models for securemesh_site."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class SecuremeshSiteListItem(F5XCBaseModel):
    """List item for securemesh_site resources."""


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


class FleetBondDevicesListType(F5XCBaseModel):
    """List of bond devices for this fleet"""

    bond_devices: Optional[list[FleetBondDeviceType]] = None


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


class ActiveNetworkPoliciesType(F5XCBaseModel):
    """List of firewall policy views."""

    network_policies: Optional[list[ObjectRefType]] = None


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


class DHCPInterfaceIPType(F5XCBaseModel):
    """Specify static IPv4 addresses per node."""

    interface_ip_map: Optional[dict[str, Any]] = None


class DHCPPoolType(F5XCBaseModel):
    """DHCP pool is a range of IP addresses (start ip and end ip)."""

    end_ip: Optional[str] = None
    start_ip: Optional[str] = None


class DHCPNetworkType(F5XCBaseModel):
    """DHCP network configuration"""

    dgw_address: Optional[str] = None
    dns_address: Optional[str] = None
    first_address: Optional[Any] = None
    last_address: Optional[Any] = None
    network_prefix: Optional[str] = None
    pool_settings: Optional[Literal['INCLUDE_IP_ADDRESSES_FROM_DHCP_POOLS', 'EXCLUDE_IP_ADDRESSES_FROM_DHCP_POOLS']] = None
    pools: Optional[list[DHCPPoolType]] = None
    same_as_dgw: Optional[Any] = None


class DHCPServerParametersType(F5XCBaseModel):
    automatic_from_end: Optional[Any] = None
    automatic_from_start: Optional[Any] = None
    dhcp_networks: Optional[list[DHCPNetworkType]] = None
    fixed_ip_map: Optional[dict[str, Any]] = None
    interface_ip_map: Optional[DHCPInterfaceIPType] = None


class LinkQualityMonitorConfig(F5XCBaseModel):
    """Link Quality Monitoring configuration for a network interface."""

    pass


class DedicatedInterfaceType(F5XCBaseModel):
    """Dedicated Interface Configuration"""

    cluster: Optional[Any] = None
    device: Optional[str] = None
    is_primary: Optional[Any] = None
    monitor: Optional[Any] = None
    monitor_disabled: Optional[Any] = None
    mtu: Optional[int] = None
    node: Optional[str] = None
    not_primary: Optional[Any] = None
    priority: Optional[int] = None


class DedicatedManagementInterfaceType(F5XCBaseModel):
    """Dedicated Interface Configuration"""

    cluster: Optional[Any] = None
    device: Optional[str] = None
    mtu: Optional[int] = None
    node: Optional[str] = None


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


class EthernetInterfaceType(F5XCBaseModel):
    """Ethernet Interface Configuration"""

    cluster: Optional[Any] = None
    device: Optional[str] = None
    dhcp_client: Optional[Any] = None
    dhcp_server: Optional[DHCPServerParametersType] = None
    ipv6_auto_config: Optional[IPV6AutoConfigType] = None
    is_primary: Optional[Any] = None
    monitor: Optional[Any] = None
    monitor_disabled: Optional[Any] = None
    mtu: Optional[int] = None
    no_ipv6_address: Optional[Any] = None
    node: Optional[str] = None
    not_primary: Optional[Any] = None
    priority: Optional[int] = None
    site_local_inside_network: Optional[Any] = None
    site_local_network: Optional[Any] = None
    static_ip: Optional[StaticIPParametersType] = None
    static_ipv6_address: Optional[StaticIPParametersType] = None
    storage_network: Optional[Any] = None
    untagged: Optional[Any] = None
    vlan_id: Optional[int] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


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


class Coordinates(F5XCBaseModel):
    """Coordinates of the site which provides the site physical location"""

    latitude: Optional[float] = None
    longitude: Optional[float] = None


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


class Interface(F5XCBaseModel):
    """Interface definition"""

    dc_cluster_group_connectivity_interface_disabled: Optional[Any] = None
    dc_cluster_group_connectivity_interface_enabled: Optional[Any] = None
    dedicated_interface: Optional[DedicatedInterfaceType] = None
    dedicated_management_interface: Optional[DedicatedManagementInterfaceType] = None
    description: Optional[str] = None
    ethernet_interface: Optional[EthernetInterfaceType] = None
    labels: Optional[dict[str, Any]] = None


class InterfaceListType(F5XCBaseModel):
    """Configure network interfaces for this Secure Mesh site"""

    interfaces: Optional[list[Interface]] = None


class StaticRouteViewType(F5XCBaseModel):
    """Defines a static route, configuring a list of prefixes and a next-hop to..."""

    attrs: Optional[list[Literal['ROUTE_ATTR_NO_OP', 'ROUTE_ATTR_ADVERTISE', 'ROUTE_ATTR_INSTALL_HOST', 'ROUTE_ATTR_INSTALL_FORWARDING', 'ROUTE_ATTR_MERGE_ONLY']]] = None
    default_gateway: Optional[Any] = None
    ip_address: Optional[str] = None
    ip_prefixes: Optional[list[str]] = None
    node_interface: Optional[NodeInterfaceType] = None


class StaticRoutesListType(F5XCBaseModel):
    """List of static routes"""

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


class VnConfiguration(F5XCBaseModel):
    """Site local network configuration"""

    dc_cluster_group: Optional[ObjectRefType] = None
    labels: Optional[dict[str, Any]] = None
    nameserver: Optional[str] = None
    no_dc_cluster_group: Optional[Any] = None
    no_static_routes: Optional[Any] = None
    no_v6_static_routes: Optional[Any] = None
    static_routes: Optional[StaticRoutesListType] = None
    static_v6_routes: Optional[StaticV6RoutesListType] = None
    vip: Optional[str] = None


class SmsNetworkConfiguration(F5XCBaseModel):
    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    default_config: Optional[Any] = None
    default_interface_config: Optional[Any] = None
    default_sli_config: Optional[Any] = None
    forward_proxy_allow_all: Optional[Any] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    interface_list: Optional[InterfaceListType] = None
    no_forward_proxy: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    sli_config: Optional[VnConfiguration] = None
    slo_config: Optional[VnConfiguration] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None
    tunnel_dead_timeout: Optional[int] = None
    vip_vrrp_mode: Optional[Literal['VIP_VRRP_INVALID', 'VIP_VRRP_ENABLE', 'VIP_VRRP_DISABLE']] = None


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


class MasterNode(F5XCBaseModel):
    """Master Node is the configuration of the master node"""

    name: Optional[str] = None
    public_ip: Optional[str] = None


class OfflineSurvivabilityModeType(F5XCBaseModel):
    """Offline Survivability allows the Site to continue functioning normally..."""

    enable_offline_survivability_mode: Optional[Any] = None
    no_offline_survivability_mode: Optional[Any] = None


class OperatingSystemType(F5XCBaseModel):
    """Select the F5XC Operating System Version for the site. By default,..."""

    default_os_version: Optional[Any] = None
    operating_system_version: Optional[str] = None


class L3PerformanceEnhancementType(F5XCBaseModel):
    """x-required L3 enhanced performance mode options"""

    jumbo: Optional[Any] = None
    no_jumbo: Optional[Any] = None


class PerformanceEnhancementModeType(F5XCBaseModel):
    """x-required Optimize the site for L3 or L7 traffic processing. L7..."""

    perf_mode_l3_enhanced: Optional[L3PerformanceEnhancementType] = None
    perf_mode_l7_enhanced: Optional[Any] = None


class VolterraSoftwareType(F5XCBaseModel):
    """Select the F5XC Software Version for the site. By default, latest..."""

    default_sw_version: Optional[Any] = None
    volterra_software_version: Optional[str] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the Secure Mesh site specification"""

    address: Optional[str] = None
    blocked_services: Optional[BlockedServicesListType] = None
    bond_device_list: Optional[FleetBondDevicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_network_config: Optional[SmsNetworkConfiguration] = None
    default_blocked_services: Optional[Any] = None
    default_network_config: Optional[Any] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    master_node_configuration: Optional[list[MasterNode]] = None
    no_bond_devices: Optional[Any] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    os: Optional[OperatingSystemType] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    sw: Optional[VolterraSoftwareType] = None
    volterra_certified_hw: Optional[str] = None
    worker_nodes: Optional[list[str]] = None


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


class GetSpecType(F5XCBaseModel):
    """Shape of the Secure Mesh site specification"""

    address: Optional[str] = None
    blocked_services: Optional[BlockedServicesListType] = None
    bond_device_list: Optional[FleetBondDevicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_network_config: Optional[SmsNetworkConfiguration] = None
    default_blocked_services: Optional[Any] = None
    default_network_config: Optional[Any] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    master_node_configuration: Optional[list[MasterNode]] = None
    no_bond_devices: Optional[Any] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    operating_system_version: Optional[str] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    site_state: Optional[Literal['ONLINE', 'PROVISIONING', 'UPGRADING', 'STANDBY', 'FAILED', 'REREGISTRATION', 'WAITINGNODES', 'DECOMMISSIONING', 'WAITING_FOR_REGISTRATION', 'ORCHESTRATION_IN_PROGRESS', 'ORCHESTRATION_COMPLETE', 'ERROR_IN_ORCHESTRATION', 'DELETING_CLOUD_RESOURCES', 'DELETED_CLOUD_RESOURCES', 'ERROR_DELETING_CLOUD_RESOURCES', 'VALIDATION_IN_PROGRESS', 'VALIDATION_SUCCESS', 'VALIDATION_FAILED']] = None
    volterra_certified_hw: Optional[str] = None
    volterra_software_version: Optional[str] = None
    worker_nodes: Optional[list[str]] = None


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Shape of the Secure Mesh site specification"""

    address: Optional[str] = None
    blocked_services: Optional[BlockedServicesListType] = None
    bond_device_list: Optional[FleetBondDevicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_network_config: Optional[SmsNetworkConfiguration] = None
    default_blocked_services: Optional[Any] = None
    default_network_config: Optional[Any] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    master_node_configuration: Optional[list[MasterNode]] = None
    no_bond_devices: Optional[Any] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    os: Optional[OperatingSystemType] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    sw: Optional[VolterraSoftwareType] = None
    volterra_certified_hw: Optional[str] = None
    worker_nodes: Optional[list[str]] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


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


class ListResponseItem(F5XCBaseModel):
    """By default a summary of securemesh_site is returned in 'List'. By..."""

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


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
