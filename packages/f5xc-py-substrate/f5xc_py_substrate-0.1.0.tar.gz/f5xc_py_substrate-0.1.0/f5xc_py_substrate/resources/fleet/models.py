"""Pydantic models for fleet."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class FleetListItem(F5XCBaseModel):
    """List item for fleet resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class BlockedServices(F5XCBaseModel):
    """Disable a node local service on this site."""

    dns: Optional[Any] = None
    network_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None
    ssh: Optional[Any] = None
    web_user_interface: Optional[Any] = None


class BondLacpType(F5XCBaseModel):
    """LACP parameters for the bond device"""

    rate: Optional[int] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class BondDeviceType(F5XCBaseModel):
    """Bond devices configuration for fleet"""

    active_backup: Optional[Any] = None
    devices: Optional[list[str]] = None
    lacp: Optional[BondLacpType] = None
    link_polling_interval: Optional[int] = None
    link_up_delay: Optional[int] = None
    name: Optional[str] = None


class BondDevicesListType(F5XCBaseModel):
    """List of bond devices for this fleet"""

    bond_devices: Optional[list[BondDeviceType]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class NetworkingDeviceInstanceType(F5XCBaseModel):
    """Represents physical network interface. The 'interface' reference points..."""

    interface: Optional[list[ObjectRefType]] = None
    use: Optional[Literal['NETWORK_INTERFACE_USE_REGULAR', 'NETWORK_INTERFACE_USE_OUTSIDE', 'NETWORK_INTERFACE_USE_INSIDE']] = None


class DeviceInstanceType(F5XCBaseModel):
    """Device Instance describes a single device in fleet A device can be of..."""

    name: Optional[str] = None
    network_device: Optional[NetworkingDeviceInstanceType] = None
    owner: Optional[Literal['DEVICE_OWNER_INVALID', 'DEVICE_OWNER_VER', 'DEVICE_OWNER_VK8S_WORK_LOAD', 'DEVICE_OWNER_HOST']] = None


class DeviceListType(F5XCBaseModel):
    """Add device for all interfaces belonging to this fleet"""

    devices: Optional[list[DeviceInstanceType]] = None


class VGPUConfiguration(F5XCBaseModel):
    """Licensing configuration for NVIDIA vGPU"""

    feature_type: Optional[Literal['UNLICENSED', 'VGPU', 'VWS', 'VCS']] = None
    server_address: Optional[str] = None
    server_port: Optional[int] = None


class VMConfiguration(F5XCBaseModel):
    """VMs support configuration"""

    pass


class InterfaceListType(F5XCBaseModel):
    """Add all interfaces belonging to this fleet"""

    interfaces: Optional[list[ObjectRefType]] = None


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


class L3PerformanceEnhancementType(F5XCBaseModel):
    """x-required L3 enhanced performance mode options"""

    jumbo: Optional[Any] = None
    no_jumbo: Optional[Any] = None


class PerformanceEnhancementModeType(F5XCBaseModel):
    """x-required Optimize the site for L3 or L7 traffic processing. L7..."""

    perf_mode_l3_enhanced: Optional[L3PerformanceEnhancementType] = None
    perf_mode_l7_enhanced: Optional[Any] = None


class SriovInterface(F5XCBaseModel):
    """Single Root I/O Virtualization interfaces configured explicitly By..."""

    interface_name: Optional[str] = None
    number_of_vfio_vfs: Optional[int] = None
    number_of_vfs: Optional[int] = None


class SriovInterfacesListType(F5XCBaseModel):
    """List of all custom SR-IOV interfaces configuration"""

    sriov_interface: Optional[list[SriovInterface]] = None


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


class StorageClassType(F5XCBaseModel):
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


class StorageClassListType(F5XCBaseModel):
    """Add additional custom storage classes in kubernetes for this fleet"""

    storage_classes: Optional[list[StorageClassType]] = None


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


class DeviceNetappBackendOntapSanChapType(F5XCBaseModel):
    """Device NetApp Backend ONTAP SAN CHAP configuration options for enabled CHAP"""

    chap_initiator_secret: Optional[SecretType] = None
    chap_target_initiator_secret: Optional[SecretType] = None
    chap_target_username: Optional[str] = None
    chap_username: Optional[str] = None


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


class StorageDeviceType(F5XCBaseModel):
    """Configuration of storage device"""

    advanced_advanced_parameters: Optional[dict[str, Any]] = None
    custom_storage: Optional[Any] = None
    hpe_storage: Optional[StorageDeviceHpeStorageType] = None
    netapp_trident: Optional[StorageDeviceNetappTridentType] = None
    pure_service_orchestrator: Optional[StorageDevicePureStorageServiceOrchestratorType] = None
    storage_device: Optional[str] = None


class StorageDeviceListType(F5XCBaseModel):
    """Add additional custom storage classes in kubernetes for this fleet"""

    storage_devices: Optional[list[StorageDeviceType]] = None


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


class StorageStaticRoutesListType(F5XCBaseModel):
    """List of storage static routes"""

    storage_routes: Optional[list[StaticRouteType]] = None


class CreateSpecType(F5XCBaseModel):
    """Create fleet will create a fleet object in 'system' namespace of the user"""

    allow_all_usb: Optional[Any] = None
    blocked_services: Optional[list[BlockedServices]] = None
    bond_device_list: Optional[BondDevicesListType] = None
    dc_cluster_group: Optional[ObjectRefType] = None
    dc_cluster_group_inside: Optional[ObjectRefType] = None
    default_config: Optional[Any] = None
    default_sriov_interface: Optional[Any] = None
    default_storage_class: Optional[Any] = None
    deny_all_usb: Optional[Any] = None
    device_list: Optional[DeviceListType] = None
    disable_gpu: Optional[Any] = None
    disable_vm: Optional[Any] = None
    enable_default_fleet_config_download: Optional[bool] = None
    enable_gpu: Optional[Any] = None
    enable_vgpu: Optional[VGPUConfiguration] = None
    enable_vm: Optional[Any] = None
    fleet_label: Optional[str] = None
    inside_virtual_network: Optional[list[ObjectRefType]] = None
    interface_list: Optional[InterfaceListType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    network_connectors: Optional[list[ObjectRefType]] = None
    network_firewall: Optional[list[ObjectRefType]] = None
    no_bond_devices: Optional[Any] = None
    no_dc_cluster_group: Optional[Any] = None
    no_storage_device: Optional[Any] = None
    no_storage_interfaces: Optional[Any] = None
    no_storage_static_routes: Optional[Any] = None
    operating_system_version: Optional[str] = None
    outside_virtual_network: Optional[list[ObjectRefType]] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    sriov_interfaces: Optional[SriovInterfacesListType] = None
    storage_class_list: Optional[StorageClassListType] = None
    storage_device_list: Optional[StorageDeviceListType] = None
    storage_interface_list: Optional[InterfaceListType] = None
    storage_static_routes: Optional[StorageStaticRoutesListType] = None
    usb_policy: Optional[ObjectRefType] = None
    volterra_software_version: Optional[str] = None


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


class GetSpecType(F5XCBaseModel):
    """Get fleet will get fleet object from system namespace"""

    allow_all_usb: Optional[Any] = None
    blocked_services: Optional[list[BlockedServices]] = None
    bond_device_list: Optional[BondDevicesListType] = None
    dc_cluster_group: Optional[ObjectRefType] = None
    dc_cluster_group_inside: Optional[ObjectRefType] = None
    default_config: Optional[Any] = None
    default_sriov_interface: Optional[Any] = None
    default_storage_class: Optional[Any] = None
    deny_all_usb: Optional[Any] = None
    device_list: Optional[DeviceListType] = None
    disable_gpu: Optional[Any] = None
    disable_vm: Optional[Any] = None
    enable_default_fleet_config_download: Optional[bool] = None
    enable_gpu: Optional[Any] = None
    enable_vgpu: Optional[VGPUConfiguration] = None
    enable_vm: Optional[Any] = None
    fleet_label: Optional[str] = None
    inside_virtual_network: Optional[list[ObjectRefType]] = None
    interface_list: Optional[InterfaceListType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    network_connectors: Optional[list[ObjectRefType]] = None
    network_firewall: Optional[list[ObjectRefType]] = None
    no_bond_devices: Optional[Any] = None
    no_dc_cluster_group: Optional[Any] = None
    no_storage_device: Optional[Any] = None
    no_storage_interfaces: Optional[Any] = None
    no_storage_static_routes: Optional[Any] = None
    operating_system_version: Optional[str] = None
    outside_virtual_network: Optional[list[ObjectRefType]] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    sriov_interfaces: Optional[SriovInterfacesListType] = None
    storage_class_list: Optional[StorageClassListType] = None
    storage_device_list: Optional[StorageDeviceListType] = None
    storage_interface_list: Optional[InterfaceListType] = None
    storage_static_routes: Optional[StorageStaticRoutesListType] = None
    usb_policy: Optional[ObjectRefType] = None
    volterra_software_version: Optional[str] = None


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


class Status(F5XCBaseModel):
    """Current status of fleet"""

    available_software_version: Optional[str] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace fleet will replace the contents of given fleet object"""

    allow_all_usb: Optional[Any] = None
    blocked_services: Optional[list[BlockedServices]] = None
    bond_device_list: Optional[BondDevicesListType] = None
    dc_cluster_group: Optional[ObjectRefType] = None
    dc_cluster_group_inside: Optional[ObjectRefType] = None
    default_config: Optional[Any] = None
    default_sriov_interface: Optional[Any] = None
    default_storage_class: Optional[Any] = None
    deny_all_usb: Optional[Any] = None
    device_list: Optional[DeviceListType] = None
    disable_gpu: Optional[Any] = None
    disable_vm: Optional[Any] = None
    enable_default_fleet_config_download: Optional[bool] = None
    enable_gpu: Optional[Any] = None
    enable_vgpu: Optional[VGPUConfiguration] = None
    enable_vm: Optional[Any] = None
    inside_virtual_network: Optional[list[ObjectRefType]] = None
    interface_list: Optional[InterfaceListType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    network_connectors: Optional[list[ObjectRefType]] = None
    network_firewall: Optional[list[ObjectRefType]] = None
    no_bond_devices: Optional[Any] = None
    no_dc_cluster_group: Optional[Any] = None
    no_storage_device: Optional[Any] = None
    no_storage_interfaces: Optional[Any] = None
    no_storage_static_routes: Optional[Any] = None
    operating_system_version: Optional[str] = None
    outside_virtual_network: Optional[list[ObjectRefType]] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    sriov_interfaces: Optional[SriovInterfacesListType] = None
    storage_class_list: Optional[StorageClassListType] = None
    storage_device_list: Optional[StorageDeviceListType] = None
    storage_interface_list: Optional[InterfaceListType] = None
    storage_static_routes: Optional[StorageStaticRoutesListType] = None
    usb_policy: Optional[ObjectRefType] = None
    volterra_software_version: Optional[str] = None


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


class StatusObject(F5XCBaseModel):
    """Most recently observed status of fleet object"""

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
    """By default a summary of fleet is returned in 'List'. By setting..."""

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
