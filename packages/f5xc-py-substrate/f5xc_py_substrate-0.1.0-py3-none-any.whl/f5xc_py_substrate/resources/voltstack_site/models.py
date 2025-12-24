"""Pydantic models for voltstack_site."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class VoltstackSiteListItem(F5XCBaseModel):
    """List item for voltstack_site resources."""


class BFD(F5XCBaseModel):
    """BFD parameters."""

    multiplier: Optional[int] = None
    receive_interval_milliseconds: Optional[int] = None
    transmit_interval_milliseconds: Optional[int] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class Nodes(F5XCBaseModel):
    """List of nodes on which BGP routing policy has to be applied"""

    node: Optional[list[str]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class BgpRoutePolicy(F5XCBaseModel):
    """List of filter rules which can be applied on all or particular nodes"""

    all_nodes: Optional[Any] = None
    inbound: Optional[Any] = None
    node_name: Optional[Nodes] = None
    object_refs: Optional[list[ObjectRefType]] = None
    outbound: Optional[Any] = None


class BgpRoutePolicies(F5XCBaseModel):
    """List of rules which can be applied on all or particular nodes"""

    route_policy: Optional[list[BgpRoutePolicy]] = None


class FamilyInet(F5XCBaseModel):
    """Parameters for inet family."""

    disable: Optional[Any] = None
    enable: Optional[Any] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class InterfaceList(F5XCBaseModel):
    """List of network interfaces."""

    interfaces: Optional[list[ObjectRefType]] = None


class PeerExternal(F5XCBaseModel):
    """External BGP Peer parameters."""

    address: Optional[str] = None
    address_ipv6: Optional[str] = None
    asn: Optional[int] = None
    default_gateway: Optional[Any] = None
    default_gateway_v6: Optional[Any] = None
    disable: Optional[Any] = None
    disable_v6: Optional[Any] = None
    external_connector: Optional[Any] = None
    family_inet: Optional[FamilyInet] = None
    from_site: Optional[Any] = None
    from_site_v6: Optional[Any] = None
    interface: Optional[ObjectRefType] = None
    interface_list: Optional[InterfaceList] = None
    md5_auth_key: Optional[str] = None
    no_authentication: Optional[Any] = None
    port: Optional[int] = None
    subnet_begin_offset: Optional[int] = None
    subnet_begin_offset_v6: Optional[int] = None
    subnet_end_offset: Optional[int] = None
    subnet_end_offset_v6: Optional[int] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class Peer(F5XCBaseModel):
    """BGP Peer parameters"""

    bfd_disabled: Optional[Any] = None
    bfd_enabled: Optional[BFD] = None
    disable: Optional[Any] = None
    external: Optional[PeerExternal] = None
    label: Optional[str] = None
    metadata: Optional[MessageMetaType] = None
    passive_mode_disabled: Optional[Any] = None
    passive_mode_enabled: Optional[Any] = None
    routing_policies: Optional[BgpRoutePolicies] = None


class BGPConfiguration(F5XCBaseModel):
    """BGP configuration parameters"""

    asn: Optional[int] = None
    peers: Optional[list[Peer]] = None


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


class DeviceNetappBackendOntapSanChapType(F5XCBaseModel):
    """Device NetApp Backend ONTAP SAN CHAP configuration options for enabled CHAP"""

    chap_initiator_secret: Optional[SecretType] = None
    chap_target_initiator_secret: Optional[SecretType] = None
    chap_target_username: Optional[str] = None
    chap_username: Optional[str] = None


class FlashArrayEndpoint(F5XCBaseModel):
    """For FlashArrays you must set the 'mgmt_endpoint' and 'api_token'"""

    api_token: Optional[SecretType] = None
    labels: Optional[dict[str, Any]] = None
    mgmt_dns_name: Optional[str] = None
    mgmt_ip: Optional[str] = None


class FlashArrayType(F5XCBaseModel):
    """Specify what storage flash arrays should be managed the plugin"""

    default_fs_opt: Optional[str] = None
    default_fs_type: Optional[str] = None
    default_mount_opts: Optional[list[str]] = None
    disable_preempt_attachments: Optional[bool] = None
    flash_arrays: Optional[list[FlashArrayEndpoint]] = None
    iscsi_login_timeout: Optional[int] = None
    san_type: Optional[str] = None


class FlashBladeEndpoint(F5XCBaseModel):
    """For FlashBlades you must set the 'mgmt_endpoint', 'api_token' and nfs_endpoint"""

    api_token: Optional[SecretType] = None
    lables: Optional[dict[str, Any]] = None
    mgmt_dns_name: Optional[str] = None
    mgmt_ip: Optional[str] = None
    nfs_endpoint_dns_name: Optional[str] = None
    nfs_endpoint_ip: Optional[str] = None


class FlashBladeType(F5XCBaseModel):
    """Specify what storage flash blades should be managed the plugin"""

    enable_snapshot_directory: Optional[bool] = None
    export_rules: Optional[str] = None
    flash_blades: Optional[list[FlashBladeEndpoint]] = None


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


class StorageClassCustomType(F5XCBaseModel):
    """Custom Storage Class allows to insert Kubernetes storageclass definition..."""

    yaml: Optional[str] = None


class StorageClassHpeStorageType(F5XCBaseModel):
    """Storage class Device configuration for HPE Storage"""

    allow_mutations: Optional[str] = None
    allow_overrides: Optional[str] = None
    dedupe_enabled: Optional[bool] = None
    description: Optional[str] = None
    destroy_on_delete: Optional[bool] = None
    encrypted: Optional[bool] = None
    folder: Optional[str] = None
    limit_iops: Optional[str] = None
    limit_mbps: Optional[str] = None
    performance_policy: Optional[str] = None
    pool: Optional[str] = None
    protection_template: Optional[str] = None
    secret_name: Optional[str] = None
    secret_namespace: Optional[str] = None
    sync_on_detach: Optional[bool] = None
    thick: Optional[bool] = None


class StorageClassNetappTridentType(F5XCBaseModel):
    """Storage class Device configuration for NetApp Trident"""

    selector: Optional[dict[str, Any]] = None
    storage_pools: Optional[str] = None


class StorageClassPureServiceOrchestratorType(F5XCBaseModel):
    """Storage class Device configuration for Pure Service Orchestrator"""

    backend: Optional[str] = None
    bandwidth_limit: Optional[str] = None
    iops_limit: Optional[int] = None


class FleetStorageClassType(F5XCBaseModel):
    """Configuration of custom storage class"""

    advanced_storage_parameters: Optional[dict[str, Any]] = None
    allow_volume_expansion: Optional[bool] = None
    custom_storage: Optional[StorageClassCustomType] = None
    default_storage_class: Optional[bool] = None
    description: Optional[str] = None
    hpe_storage: Optional[StorageClassHpeStorageType] = None
    netapp_trident: Optional[StorageClassNetappTridentType] = None
    pure_service_orchestrator: Optional[StorageClassPureServiceOrchestratorType] = None
    reclaim_policy: Optional[str] = None
    storage_class_name: Optional[str] = None
    storage_device: Optional[str] = None


class FleetStorageClassListType(F5XCBaseModel):
    """Add additional custom storage classes in kubernetes for this fleet"""

    storage_classes: Optional[list[FleetStorageClassType]] = None


class StorageDeviceHpeStorageType(F5XCBaseModel):
    """Device configuration for HPE Storage"""

    api_server_port: Optional[int] = None
    iscsi_chap_password: Optional[SecretType] = None
    iscsi_chap_user: Optional[str] = None
    password: Optional[SecretType] = None
    storage_server_ip_address: Optional[str] = None
    storage_server_name: Optional[str] = None
    username: Optional[str] = None


class PrefixStringListType(F5XCBaseModel):
    """x-example: '192.168.20.0/24' List of IPv4 prefixes that represent an endpoint"""

    prefixes: Optional[list[str]] = None


class OntapVolumeDefaults(F5XCBaseModel):
    """It controls how each volume is provisioned by default using these..."""

    adaptive_qos_policy: Optional[str] = None
    encryption: Optional[bool] = None
    export_policy: Optional[str] = None
    no_qos: Optional[Any] = None
    qos_policy: Optional[str] = None
    security_style: Optional[str] = None
    snapshot_dir: Optional[bool] = None
    snapshot_policy: Optional[str] = None
    snapshot_reserve: Optional[str] = None
    space_reserve: Optional[str] = None
    split_on_clone: Optional[bool] = None
    tiering_policy: Optional[str] = None
    unix_permissions: Optional[int] = None


class OntapVirtualStoragePoolType(F5XCBaseModel):
    """ONTAP Virtual Storage Pool definition"""

    labels: Optional[dict[str, Any]] = None
    volume_defaults: Optional[OntapVolumeDefaults] = None
    zone: Optional[str] = None


class StorageDeviceNetappBackendOntapNasType(F5XCBaseModel):
    """Configuration of storage backend for NetApp ONTAP NAS"""

    auto_export_cidrs: Optional[PrefixStringListType] = None
    auto_export_policy: Optional[bool] = None
    backend_name: Optional[str] = None
    client_certificate: Optional[str] = None
    client_private_key: Optional[SecretType] = None
    data_lif_dns_name: Optional[str] = None
    data_lif_ip: Optional[str] = None
    labels: Optional[dict[str, Any]] = None
    limit_aggregate_usage: Optional[str] = None
    limit_volume_size: Optional[str] = None
    management_lif_dns_name: Optional[str] = None
    management_lif_ip: Optional[str] = None
    nfs_mount_options: Optional[str] = None
    password: Optional[SecretType] = None
    region: Optional[str] = None
    storage: Optional[list[OntapVirtualStoragePoolType]] = None
    storage_driver_name: Optional[str] = None
    storage_prefix: Optional[str] = None
    svm: Optional[str] = None
    trusted_ca_certificate: Optional[str] = None
    username: Optional[str] = None
    volume_defaults: Optional[OntapVolumeDefaults] = None


class StorageDeviceNetappBackendOntapSanType(F5XCBaseModel):
    """Configuration of storage backend for NetApp ONTAP SAN"""

    client_certificate: Optional[str] = None
    client_private_key: Optional[SecretType] = None
    data_lif_dns_name: Optional[str] = None
    data_lif_ip: Optional[str] = None
    igroup_name: Optional[str] = None
    labels: Optional[dict[str, Any]] = None
    limit_aggregate_usage: Optional[int] = None
    limit_volume_size: Optional[int] = None
    management_lif_dns_name: Optional[str] = None
    management_lif_ip: Optional[str] = None
    no_chap: Optional[Any] = None
    password: Optional[SecretType] = None
    region: Optional[str] = None
    storage: Optional[list[OntapVirtualStoragePoolType]] = None
    storage_driver_name: Optional[str] = None
    storage_prefix: Optional[str] = None
    svm: Optional[str] = None
    trusted_ca_certificate: Optional[str] = None
    use_chap: Optional[DeviceNetappBackendOntapSanChapType] = None
    username: Optional[str] = None
    volume_defaults: Optional[OntapVolumeDefaults] = None


class StorageDeviceNetappTridentType(F5XCBaseModel):
    """Device configuration for NetApp Trident Storage"""

    netapp_backend_ontap_nas: Optional[StorageDeviceNetappBackendOntapNasType] = None
    netapp_backend_ontap_san: Optional[StorageDeviceNetappBackendOntapSanType] = None


class PsoArrayConfiguration(F5XCBaseModel):
    """Device configuration for PSO Arrays"""

    flash_array: Optional[FlashArrayType] = None
    flash_blade: Optional[FlashBladeType] = None


class StorageDevicePureStorageServiceOrchestratorType(F5XCBaseModel):
    """Device configuration for Pure Storage Service Orchestrator"""

    arrays: Optional[PsoArrayConfiguration] = None
    cluster_id: Optional[str] = None
    enable_storage_topology: Optional[bool] = None
    enable_strict_topology: Optional[bool] = None


class FleetStorageDeviceType(F5XCBaseModel):
    """Configuration of storage device"""

    advanced_advanced_parameters: Optional[dict[str, Any]] = None
    custom_storage: Optional[Any] = None
    hpe_storage: Optional[StorageDeviceHpeStorageType] = None
    netapp_trident: Optional[StorageDeviceNetappTridentType] = None
    pure_service_orchestrator: Optional[StorageDevicePureStorageServiceOrchestratorType] = None
    storage_device: Optional[str] = None


class FleetStorageDeviceListType(F5XCBaseModel):
    """Add additional custom storage classes in kubernetes for this fleet"""

    storage_devices: Optional[list[FleetStorageDeviceType]] = None


class LocalControlPlaneType(F5XCBaseModel):
    """Enable local control plane for L3VPN, SRV6, EVPN etc"""

    bgp_config: Optional[BGPConfiguration] = None
    inside_vn: Optional[Any] = None
    outside_vn: Optional[Any] = None


class SriovInterface(F5XCBaseModel):
    """Single Root I/O Virtualization interfaces configured explicitly By..."""

    interface_name: Optional[str] = None
    number_of_vfio_vfs: Optional[int] = None
    number_of_vfs: Optional[int] = None


class SriovInterfacesListType(F5XCBaseModel):
    """List of all custom SR-IOV interfaces configuration"""

    sriov_interface: Optional[list[SriovInterface]] = None


class VGPUConfiguration(F5XCBaseModel):
    """Licensing configuration for NVIDIA vGPU"""

    feature_type: Optional[Literal['UNLICENSED', 'VGPU', 'VWS', 'VCS']] = None
    server_address: Optional[str] = None
    server_port: Optional[int] = None


class VMConfiguration(F5XCBaseModel):
    """VMs support configuration"""

    pass


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


class TunnelInterfaceType(F5XCBaseModel):
    """Tunnel Interface Configuration"""

    mtu: Optional[int] = None
    node: Optional[str] = None
    priority: Optional[int] = None
    site_local_inside_network: Optional[Any] = None
    site_local_network: Optional[Any] = None
    static_ip: Optional[StaticIPParametersType] = None
    tunnel: Optional[ObjectRefType] = None


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


class VolterraSoftwareType(F5XCBaseModel):
    """Select the F5XC Software Version for the site. By default, latest..."""

    default_sw_version: Optional[Any] = None
    volterra_software_version: Optional[str] = None


class Interface(F5XCBaseModel):
    """Interface definition"""

    dc_cluster_group_connectivity_interface_disabled: Optional[Any] = None
    dc_cluster_group_connectivity_interface_enabled: Optional[Any] = None
    dedicated_interface: Optional[DedicatedInterfaceType] = None
    dedicated_management_interface: Optional[DedicatedManagementInterfaceType] = None
    description: Optional[str] = None
    ethernet_interface: Optional[EthernetInterfaceType] = None
    labels: Optional[dict[str, Any]] = None
    tunnel_interface: Optional[TunnelInterfaceType] = None


class InterfaceListType(F5XCBaseModel):
    """Configure network interfaces for this App Stack site"""

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


class SliVnConfiguration(F5XCBaseModel):
    """Site local inside network configuration"""

    no_static_routes: Optional[Any] = None
    no_v6_static_routes: Optional[Any] = None
    static_routes: Optional[StaticRoutesListType] = None
    static_v6_routes: Optional[StaticV6RoutesListType] = None


class VnConfiguration(F5XCBaseModel):
    """Site local network configuration"""

    dc_cluster_group: Optional[ObjectRefType] = None
    labels: Optional[dict[str, Any]] = None
    no_dc_cluster_group: Optional[Any] = None
    no_static_routes: Optional[Any] = None
    no_static_v6_routes: Optional[Any] = None
    static_routes: Optional[StaticRoutesListType] = None
    static_v6_routes: Optional[StaticV6RoutesListType] = None


class VssNetworkConfiguration(F5XCBaseModel):
    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    bgp_peer_address: Optional[str] = None
    bgp_router_id: Optional[str] = None
    default_config: Optional[Any] = None
    default_interface_config: Optional[Any] = None
    default_sli_config: Optional[Any] = None
    forward_proxy_allow_all: Optional[Any] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    interface_list: Optional[InterfaceListType] = None
    no_forward_proxy: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_network_policy: Optional[Any] = None
    outside_nameserver: Optional[str] = None
    outside_vip: Optional[str] = None
    site_to_site_tunnel_ip: Optional[str] = None
    sli_config: Optional[SliVnConfiguration] = None
    slo_config: Optional[VnConfiguration] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None
    tunnel_dead_timeout: Optional[int] = None
    vip_vrrp_mode: Optional[Literal['VIP_VRRP_INVALID', 'VIP_VRRP_ENABLE', 'VIP_VRRP_DISABLE']] = None


class StorageInterfaceType(F5XCBaseModel):
    """Configure storage interface for this App Stack site"""

    description: Optional[str] = None
    labels: Optional[dict[str, Any]] = None
    storage_interface: Optional[EthernetInterfaceType] = None


class StorageInterfaceListType(F5XCBaseModel):
    """Configure storage interfaces for this App Stack site"""

    storage_interfaces: Optional[list[StorageInterfaceType]] = None


class VssStorageConfiguration(F5XCBaseModel):
    default_storage_class: Optional[Any] = None
    no_static_routes: Optional[Any] = None
    no_storage_device: Optional[Any] = None
    no_storage_interfaces: Optional[Any] = None
    static_routes: Optional[StaticRoutesListType] = None
    storage_class_list: Optional[FleetStorageClassListType] = None
    storage_device_list: Optional[FleetStorageDeviceListType] = None
    storage_interface_list: Optional[StorageInterfaceListType] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the App Stack site specification"""

    address: Optional[str] = None
    allow_all_usb: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    bond_device_list: Optional[FleetBondDevicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_dns: Optional[CustomDNS] = None
    custom_network_config: Optional[VssNetworkConfiguration] = None
    custom_storage_config: Optional[VssStorageConfiguration] = None
    default_blocked_services: Optional[Any] = None
    default_network_config: Optional[Any] = None
    default_sriov_interface: Optional[Any] = None
    default_storage_config: Optional[Any] = None
    deny_all_usb: Optional[Any] = None
    disable_gpu: Optional[Any] = None
    disable_vm: Optional[Any] = None
    enable_gpu: Optional[Any] = None
    enable_vgpu: Optional[VGPUConfiguration] = None
    enable_vm: Optional[Any] = None
    k8s_cluster: Optional[ObjectRefType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    local_control_plane: Optional[LocalControlPlaneType] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    master_node_configuration: Optional[list[MasterNode]] = None
    no_bond_devices: Optional[Any] = None
    no_k8s_cluster: Optional[Any] = None
    no_local_control_plane: Optional[Any] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    os: Optional[OperatingSystemType] = None
    sriov_interfaces: Optional[SriovInterfacesListType] = None
    sw: Optional[VolterraSoftwareType] = None
    usb_policy: Optional[ObjectRefType] = None
    volterra_certified_hw: Optional[str] = None
    worker_nodes: Optional[list[str]] = None


class GetSpecType(F5XCBaseModel):
    """Shape of the App Stack site specification"""

    address: Optional[str] = None
    allow_all_usb: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    bond_device_list: Optional[FleetBondDevicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_dns: Optional[CustomDNS] = None
    custom_network_config: Optional[VssNetworkConfiguration] = None
    custom_storage_config: Optional[VssStorageConfiguration] = None
    default_blocked_services: Optional[Any] = None
    default_network_config: Optional[Any] = None
    default_sriov_interface: Optional[Any] = None
    default_storage_config: Optional[Any] = None
    deny_all_usb: Optional[Any] = None
    disable_gpu: Optional[Any] = None
    disable_vm: Optional[Any] = None
    enable_gpu: Optional[Any] = None
    enable_vgpu: Optional[VGPUConfiguration] = None
    enable_vm: Optional[Any] = None
    k8s_cluster: Optional[ObjectRefType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    local_control_plane: Optional[LocalControlPlaneType] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    master_node_configuration: Optional[list[MasterNode]] = None
    no_bond_devices: Optional[Any] = None
    no_k8s_cluster: Optional[Any] = None
    no_local_control_plane: Optional[Any] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    operating_system_version: Optional[str] = None
    site_state: Optional[Literal['ONLINE', 'PROVISIONING', 'UPGRADING', 'STANDBY', 'FAILED', 'REREGISTRATION', 'WAITINGNODES', 'DECOMMISSIONING', 'WAITING_FOR_REGISTRATION', 'ORCHESTRATION_IN_PROGRESS', 'ORCHESTRATION_COMPLETE', 'ERROR_IN_ORCHESTRATION', 'DELETING_CLOUD_RESOURCES', 'DELETED_CLOUD_RESOURCES', 'ERROR_DELETING_CLOUD_RESOURCES', 'VALIDATION_IN_PROGRESS', 'VALIDATION_SUCCESS', 'VALIDATION_FAILED']] = None
    sriov_interfaces: Optional[SriovInterfacesListType] = None
    usb_policy: Optional[ObjectRefType] = None
    volterra_certified_hw: Optional[str] = None
    volterra_software_version: Optional[str] = None
    worker_nodes: Optional[list[str]] = None


class ReplaceSpecType(F5XCBaseModel):
    """Shape of the App Stack site replace specification"""

    address: Optional[str] = None
    allow_all_usb: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    bond_device_list: Optional[FleetBondDevicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_dns: Optional[CustomDNS] = None
    custom_network_config: Optional[VssNetworkConfiguration] = None
    custom_storage_config: Optional[VssStorageConfiguration] = None
    default_blocked_services: Optional[Any] = None
    default_network_config: Optional[Any] = None
    default_sriov_interface: Optional[Any] = None
    default_storage_config: Optional[Any] = None
    deny_all_usb: Optional[Any] = None
    disable_gpu: Optional[Any] = None
    disable_vm: Optional[Any] = None
    enable_gpu: Optional[Any] = None
    enable_vgpu: Optional[VGPUConfiguration] = None
    enable_vm: Optional[Any] = None
    k8s_cluster: Optional[ObjectRefType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    local_control_plane: Optional[LocalControlPlaneType] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    master_node_configuration: Optional[list[MasterNode]] = None
    no_bond_devices: Optional[Any] = None
    no_k8s_cluster: Optional[Any] = None
    no_local_control_plane: Optional[Any] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    os: Optional[OperatingSystemType] = None
    sriov_interfaces: Optional[SriovInterfacesListType] = None
    sw: Optional[VolterraSoftwareType] = None
    usb_policy: Optional[ObjectRefType] = None
    volterra_certified_hw: Optional[str] = None
    worker_nodes: Optional[list[str]] = None


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


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
    """By default a summary of voltstack_site is returned in 'List'. By setting..."""

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
