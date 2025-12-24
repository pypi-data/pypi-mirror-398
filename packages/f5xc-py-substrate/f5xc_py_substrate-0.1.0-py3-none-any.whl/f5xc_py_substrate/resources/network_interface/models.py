"""Pydantic models for network_interface."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class NetworkInterfaceListItem(F5XCBaseModel):
    """List item for network_interface resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


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


class DHCPInterfaceIPType(F5XCBaseModel):
    """Specify static IPv4 addresses per node."""

    interface_ip_map: Optional[dict[str, Any]] = None


class DHCPServerParametersType(F5XCBaseModel):
    automatic_from_end: Optional[Any] = None
    automatic_from_start: Optional[Any] = None
    dhcp_networks: Optional[list[DHCPNetworkType]] = None
    fixed_ip_map: Optional[dict[str, Any]] = None
    interface_ip_map: Optional[DHCPInterfaceIPType] = None


class IPV6DnsList(F5XCBaseModel):
    dns_list: Optional[list[str]] = None


class IPV6LocalDnsAddress(F5XCBaseModel):
    configured_address: Optional[str] = None
    first_address: Optional[Any] = None
    last_address: Optional[Any] = None


class IPV6DnsConfig(F5XCBaseModel):
    configured_list: Optional[IPV6DnsList] = None
    local_dns: Optional[IPV6LocalDnsAddress] = None


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


class Layer2SriovInterfaceType(F5XCBaseModel):
    """Layer2 SR-IOV Interface Configuration"""

    device: Optional[str] = None
    untagged: Optional[Any] = None
    vlan_id: Optional[int] = None


class Layer2VlanInterfaceType(F5XCBaseModel):
    """Layer2 VLAN Interface Configuration"""

    device: Optional[str] = None
    vlan_id: Optional[int] = None


class Layer2SloVlanInterfaceType(F5XCBaseModel):
    """Layer2 Site Local Outside VLAN Interface Configuration"""

    vlan_id: Optional[int] = None


class Layer2InterfaceType(F5XCBaseModel):
    """Layer2 Interface Configuration"""

    l2sriov_interface: Optional[Layer2SriovInterfaceType] = None
    l2vlan_interface: Optional[Layer2VlanInterfaceType] = None
    l2vlan_slo_interface: Optional[Layer2SloVlanInterfaceType] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class TunnelInterfaceType(F5XCBaseModel):
    """Tunnel Interface Configuration"""

    mtu: Optional[int] = None
    node: Optional[str] = None
    priority: Optional[int] = None
    site_local_inside_network: Optional[Any] = None
    site_local_network: Optional[Any] = None
    static_ip: Optional[StaticIPParametersType] = None
    tunnel: Optional[ObjectRefType] = None


class CreateSpecType(F5XCBaseModel):
    """Network interface represents configuration of a network device. It is..."""

    dedicated_interface: Optional[DedicatedInterfaceType] = None
    dedicated_management_interface: Optional[DedicatedManagementInterfaceType] = None
    ethernet_interface: Optional[EthernetInterfaceType] = None
    layer2_interface: Optional[Layer2InterfaceType] = None
    tunnel_interface: Optional[TunnelInterfaceType] = None


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


class Ipv4AddressType(F5XCBaseModel):
    """IPv4 Address in dot-decimal notation"""

    addr: Optional[str] = None


class DNS(F5XCBaseModel):
    """Controls how the DNS Server of the Network interface is derived"""

    dns_mode: Optional[Literal['NETWORK_INTERFACE_DNS_DISABLE', 'NETWORK_INTERFACE_DNS_AUTO_ALLOCATE', 'NETWORK_INTERFACE_DNS_USE_CONFIGURED']] = None
    dns_server: Optional[list[Ipv4AddressType]] = None


class DFGW(F5XCBaseModel):
    """Controls how the Default Gateway of the Network interface is derived"""

    default_gateway_address: Optional[Ipv4AddressType] = None
    default_gateway_mode: Optional[Literal['NETWORK_INTERFACE_GATEWAY_DISABLE', 'NETWORK_INTERFACE_GATEWAY_AUTO_ALLOCATE', 'NETWORK_INTERFACE_GATEWAY_USE_CONFIGURED']] = None


class Ipv4SubnetType(F5XCBaseModel):
    """IPv4 subnets specified as prefix and prefix-length. Prefix length must be <= 32"""

    plen: Optional[int] = None
    prefix: Optional[str] = None


class Tunnel(F5XCBaseModel):
    """Tunnel attached to this interface, enables encapsulation on interface"""

    tunnel: Optional[list[ObjectRefType]] = None


class LegacyInterfaceType(F5XCBaseModel):
    """Legacy Interface Configuration"""

    dhcp_server: Optional[Literal['NETWORK_INTERFACE_DHCP_SERVER_DISABLE', 'NETWORK_INTERFACE_DHCP_SERVER_ENABLE', 'NETWORK_INTERFACE_ENHANCED_DHCP_SERVER_ENABLE']] = Field(default=None, alias="DHCP_server")
    dns_server: Optional[DNS] = Field(default=None, alias="DNS_server")
    address_allocator: Optional[list[ObjectRefType]] = None
    default_gateway: Optional[DFGW] = None
    device_name: Optional[str] = None
    dhcp_address: Optional[Literal['NETWORK_INTERFACE_DHCP_DISABLE', 'NETWORK_INTERFACE_DHCP_ENABLE']] = None
    monitor: Optional[Any] = None
    monitor_disabled: Optional[Any] = None
    mtu: Optional[int] = None
    priority: Optional[int] = None
    static_addresses: Optional[list[Ipv4SubnetType]] = None
    tunnel: Optional[Tunnel] = None
    type_: Optional[Literal['NETWORK_INTERFACE_ETHERNET', 'NETWORK_INTERFACE_VLAN_INTERFACE', 'NETWORK_INTERFACE_LACP_INTERFACE', 'NETWORK_INTERFACE_TUNNEL_INTERFACE', 'NETWORK_INTERFACE_LOOPBACK_INTERFACE', 'NETWORK_INTERFACE_LAYER2_INTERFACE']] = Field(default=None, alias="type")
    virtual_network: Optional[list[ObjectRefType]] = None
    vlan_tag: Optional[int] = None
    vlan_tagging: Optional[Literal['NETWORK_INTERFACE_VLAN_TAGGING_DISABLE', 'NETWORK_INTERFACE_VLAN_TAGGING_ENABLE']] = None


class GetSpecType(F5XCBaseModel):
    """Get network interface from system namespace"""

    dhcp_server: Optional[Literal['NETWORK_INTERFACE_DHCP_SERVER_DISABLE', 'NETWORK_INTERFACE_DHCP_SERVER_ENABLE', 'NETWORK_INTERFACE_ENHANCED_DHCP_SERVER_ENABLE']] = Field(default=None, alias="DHCP_server")
    dns_server: Optional[DNS] = Field(default=None, alias="DNS_server")
    address_allocator: Optional[list[ObjectRefType]] = None
    dedicated_interface: Optional[DedicatedInterfaceType] = None
    dedicated_management_interface: Optional[DedicatedManagementInterfaceType] = None
    default_gateway: Optional[DFGW] = None
    device_name: Optional[str] = None
    dhcp_address: Optional[Literal['NETWORK_INTERFACE_DHCP_DISABLE', 'NETWORK_INTERFACE_DHCP_ENABLE']] = None
    ethernet_interface: Optional[EthernetInterfaceType] = None
    interface_ip_map: Optional[dict[str, Any]] = None
    is_primary: Optional[bool] = None
    layer2_interface: Optional[Layer2InterfaceType] = None
    legacy_interface: Optional[LegacyInterfaceType] = None
    monitor: Optional[Any] = None
    monitor_disabled: Optional[Any] = None
    mtu: Optional[int] = None
    priority: Optional[int] = None
    static_addresses: Optional[list[Ipv4SubnetType]] = None
    tunnel: Optional[Tunnel] = None
    tunnel_interface: Optional[TunnelInterfaceType] = None
    type_: Optional[Literal['NETWORK_INTERFACE_ETHERNET', 'NETWORK_INTERFACE_VLAN_INTERFACE', 'NETWORK_INTERFACE_LACP_INTERFACE', 'NETWORK_INTERFACE_TUNNEL_INTERFACE', 'NETWORK_INTERFACE_LOOPBACK_INTERFACE', 'NETWORK_INTERFACE_LAYER2_INTERFACE']] = Field(default=None, alias="type")
    virtual_network: Optional[list[ObjectRefType]] = None
    vlan_tag: Optional[int] = None
    vlan_tagging: Optional[Literal['NETWORK_INTERFACE_VLAN_TAGGING_DISABLE', 'NETWORK_INTERFACE_VLAN_TAGGING_ENABLE']] = None


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
    """Network interface represents configuration of a network device. Replace..."""

    dedicated_interface: Optional[DedicatedInterfaceType] = None
    dedicated_management_interface: Optional[DedicatedManagementInterfaceType] = None
    ethernet_interface: Optional[EthernetInterfaceType] = None
    layer2_interface: Optional[Layer2InterfaceType] = None
    legacy_interface: Optional[LegacyInterfaceType] = None
    tunnel_interface: Optional[TunnelInterfaceType] = None


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


class Status(F5XCBaseModel):
    """Current Status of the Network interface"""

    up_down: Optional[Literal['NETWORK_INTERFACE_ADMINISTRATIVELY_DOWN', 'NETWORK_INTERFACE_OPERATIONALY_DOWN', 'NETWORK_INTERFACE_OPERATIONALY_UP']] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    status: Optional[Status] = None


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
    """By default a summary of network_interface is returned in 'List'. By..."""

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
