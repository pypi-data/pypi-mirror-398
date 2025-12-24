"""Pydantic models for registration."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class RegistrationListItem(F5XCBaseModel):
    """List item for registration resources."""


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


class StatusType(F5XCBaseModel):
    """Status is a return value for calls that don't return other objects."""

    code: Optional[int] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class Passport(F5XCBaseModel):
    """Passport stores information about identification and node configuration..."""

    cluster_name: Optional[str] = None
    cluster_size: Optional[int] = None
    cluster_type: Optional[str] = None
    default_os_version: Optional[Any] = None
    default_sw_version: Optional[Any] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    operating_system_version: Optional[str] = None
    private_network_name: Optional[str] = None
    volterra_software_version: Optional[str] = None


class ApprovalReq(F5XCBaseModel):
    """Request for admission approval"""

    annotations: Optional[dict[str, Any]] = None
    connected_region: Optional[str] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    passport: Optional[Passport] = None
    preferred_active_re: Optional[str] = None
    tunnel_type: Optional[Literal['SITE_TO_SITE_TUNNEL_IPSEC_OR_SSL', 'SITE_TO_SITE_TUNNEL_IPSEC', 'SITE_TO_SITE_TUNNEL_SSL']] = None


class ConfigReq(F5XCBaseModel):
    """Request to get configuration"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    token: Optional[str] = None


class ConfigResp(F5XCBaseModel):
    """Response for configuration request. This response is consumed by node."""

    hash: Optional[str] = None
    workload: Optional[dict[str, Any]] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class Bios(F5XCBaseModel):
    """BIOS information."""

    date: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None


class Board(F5XCBaseModel):
    """Board information"""

    asset_tag: Optional[str] = None
    name: Optional[str] = None
    serial: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None


class Chassis(F5XCBaseModel):
    """Chassis information."""

    asset_tag: Optional[str] = None
    serial: Optional[str] = None
    type_: Optional[int] = Field(default=None, alias="type")
    vendor: Optional[str] = None
    version: Optional[str] = None


class Cpu(F5XCBaseModel):
    """CPU information"""

    cache: Optional[int] = None
    cores: Optional[int] = None
    cpus: Optional[int] = None
    model: Optional[str] = None
    speed: Optional[int] = None
    threads: Optional[int] = None
    vendor: Optional[str] = None


class GPUDevice(F5XCBaseModel):
    id_: Optional[str] = Field(default=None, alias="id")
    processes: Optional[str] = None
    product_name: Optional[str] = None


class GPU(F5XCBaseModel):
    """GPU information on server"""

    cuda_version: Optional[str] = None
    driver_version: Optional[str] = None
    gpu_device: Optional[list[GPUDevice]] = None


class Kernel(F5XCBaseModel):
    """Kernel information"""

    architecture: Optional[str] = None
    release: Optional[str] = None
    version: Optional[str] = None


class Memory(F5XCBaseModel):
    """Memory information."""

    size_mb: Optional[int] = None
    speed: Optional[int] = None
    type_: Optional[str] = Field(default=None, alias="type")


class NetworkDevice(F5XCBaseModel):
    """NetworkDevice information."""

    driver: Optional[str] = None
    ip_address: Optional[list[str]] = None
    link_quality: Optional[Literal['QUALITY_UNKNOWN', 'QUALITY_GOOD', 'QUALITY_POOR', 'QUALITY_DISABLED']] = None
    link_type: Optional[Literal['LINK_TYPE_UNKNOWN', 'LINK_TYPE_ETHERNET', 'LINK_TYPE_WIFI_802_11AC', 'LINK_TYPE_WIFI_802_11BGN', 'LINK_TYPE_4G', 'LINK_TYPE_WIFI', 'LINK_TYPE_WAN']] = None
    mac_address: Optional[str] = None
    name: Optional[str] = None
    port: Optional[str] = None
    speed: Optional[int] = None


class OS(F5XCBaseModel):
    """Details of Operating System"""

    architecture: Optional[str] = None
    name: Optional[str] = None
    release: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None


class Product(F5XCBaseModel):
    """Product information"""

    name: Optional[str] = None
    serial: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None


class StorageDevice(F5XCBaseModel):
    """StorageDevice information."""

    driver: Optional[str] = None
    model: Optional[str] = None
    name: Optional[str] = None
    serial: Optional[str] = None
    size_gb: Optional[int] = None
    vendor: Optional[str] = None


class USBDevice(F5XCBaseModel):
    """Information about USB device"""

    address: Optional[int] = None
    b_device_class: Optional[str] = None
    b_device_protocol: Optional[str] = None
    b_device_sub_class: Optional[str] = None
    b_max_packet_size: Optional[int] = None
    bcd_device: Optional[str] = None
    bcd_usb: Optional[str] = None
    bus: Optional[int] = None
    description: Optional[str] = None
    i_manufacturer: Optional[str] = None
    i_product: Optional[str] = None
    i_serial: Optional[str] = None
    id_product: Optional[str] = None
    id_vendor: Optional[str] = None
    port: Optional[int] = None
    product_name: Optional[str] = None
    speed: Optional[str] = None
    usb_type: Optional[Literal['UNKNOWN_USB', 'INTERNAL', 'REGISTERED', 'CONFIGURABLE']] = None
    vendor_name: Optional[str] = None


class OsInfo(F5XCBaseModel):
    """OsInfo holds information about host OS and HW"""

    bios: Optional[Bios] = None
    board: Optional[Board] = None
    chassis: Optional[Chassis] = None
    cpu: Optional[Cpu] = None
    gpu: Optional[GPU] = None
    kernel: Optional[Kernel] = None
    memory: Optional[Memory] = None
    network: Optional[list[NetworkDevice]] = None
    numa_nodes: Optional[int] = None
    os: Optional[OS] = None
    product: Optional[Product] = None
    storage: Optional[list[StorageDevice]] = None
    usb: Optional[list[USBDevice]] = None


class InternetProxy(F5XCBaseModel):
    """Proxy describes options for HTTP or HTTPS proxy configurations"""

    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    no_proxy: Optional[str] = None
    proxy_cacert_url: Optional[str] = None


class SWInfo(F5XCBaseModel):
    """SWInfo holds information about sw version"""

    sw_version: Optional[str] = None


class Infra(F5XCBaseModel):
    """InfraMetadata stores information about instance infrastructure"""

    availability_zone: Optional[str] = None
    certified_hw: Optional[str] = None
    domain: Optional[str] = None
    hostname: Optional[str] = None
    hw_info: Optional[OsInfo] = None
    instance_id: Optional[str] = None
    interfaces: Optional[dict[str, Any]] = None
    internet_proxy: Optional[InternetProxy] = None
    machine_id: Optional[str] = None
    provider: Optional[Literal['UNKNOWN', 'AWS', 'GOOGLE', 'AZURE', 'VMWARE', 'KVM', 'OTHER', 'VOLTERRA', 'IBMCLOUD', 'UNKNOWN_K8S', 'AWS_K8S', 'GCP_K8S', 'AZURE_K8S', 'VMWARE_K8S', 'KVM_K8S', 'OTHER_K8S', 'VOLTERRA_K8S', 'IBMCLOUD_K8S', 'F5OS', 'RSERIES', 'OCI', 'NUTANIX', 'OPENSTACK', 'EQUINIX']] = None
    sw_info: Optional[SWInfo] = None
    timestamp: Optional[str] = None
    zone: Optional[str] = None


class CreateSpecType(F5XCBaseModel):
    """VPM creates registration using this message, never used by users."""

    infra: Optional[Infra] = None
    passport: Optional[Passport] = None
    token: Optional[str] = None


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
    """Get registration specification"""

    infra: Optional[Infra] = None
    passport: Optional[Passport] = None
    token: Optional[str] = None


class InitializerType(F5XCBaseModel):
    """Initializer is information about an initializer that has not yet completed."""

    name: Optional[str] = None


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


class GetImageDownloadUrlReq(F5XCBaseModel):
    """Request to get image download url"""

    provider: Optional[str] = None


class GetImageDownloadUrlResp(F5XCBaseModel):
    """Response to get image download url"""

    image_download_url: Optional[str] = None
    image_md5_download_url: Optional[str] = None


class GetRegistrationsBySiteTokenReq(F5XCBaseModel):
    """Request to get registration uuids by site token"""

    site_token: Optional[str] = None


class GetRegistrationsBySiteTokenResp(F5XCBaseModel):
    """Response for querying registration uuids by site token"""

    registration_uuids: Optional[list[str]] = None


class ObjectMetaType(F5XCBaseModel):
    """ObjectMetaType is metadata(common attributes) of an object that all..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    infra: Optional[Infra] = None
    passport: Optional[Passport] = None
    role: Optional[list[str]] = None
    site: Optional[list[ObjectRefType]] = None
    token: Optional[str] = None
    tunnel_type: Optional[Literal['SITE_TO_SITE_TUNNEL_IPSEC_OR_SSL', 'SITE_TO_SITE_TUNNEL_IPSEC', 'SITE_TO_SITE_TUNNEL_SSL']] = None


class SpecType(F5XCBaseModel):
    """Shape of the registration specification"""

    gc_spec: Optional[GlobalSpecType] = None


class StatusType(F5XCBaseModel):
    """Most recent observer status of object"""

    current_state: Optional[Literal['NOTSET', 'NEW', 'APPROVED', 'ADMITTED', 'RETIRED', 'FAILED', 'DONE', 'PENDING', 'ONLINE', 'UPGRADING', 'MAINTENANCE']] = None
    object_status: Optional[StatusType] = None


class SystemObjectMetaType(F5XCBaseModel):
    """SystemObjectMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_cookie: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    direct_ref_hash: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    namespace: Optional[list[ObjectRefType]] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    revision: Optional[str] = None
    sre_disable: Optional[bool] = None
    tenant: Optional[str] = None
    trace_info: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class Object(F5XCBaseModel):
    """Registration object stores node registration and information regarding the node"""

    metadata: Optional[ObjectMetaType] = None
    spec: Optional[SpecType] = None
    status: Optional[StatusType] = None
    system_metadata: Optional[SystemObjectMetaType] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """NO fields are allowed to be replaced"""

    pass


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[Any] = None


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[CreateRequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    object_: Optional[Object] = Field(default=None, alias="object")
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[ReplaceRequest] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of registration is returned in 'List'. By setting..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[GetSpecType] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    object_: Optional[Object] = Field(default=None, alias="object")
    owner_view: Optional[ViewRefType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[ListResponseItem]] = None


class ListStateReq(F5XCBaseModel):
    """Request for list registrations"""

    namespace: Optional[str] = None
    state: Optional[Literal['NOTSET', 'NEW', 'APPROVED', 'ADMITTED', 'RETIRED', 'FAILED', 'DONE', 'PENDING', 'ONLINE', 'UPGRADING', 'MAINTENANCE']] = None


class ObjectChangeResp(F5XCBaseModel):
    """Generic response when object is changed, registration can be changed..."""

    obj: Optional[Object] = None


class CreateRequest(F5XCBaseModel):
    """Register node. This API isn't designed to be used by users, it's only for node."""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


class ReplaceResponse(F5XCBaseModel):
    pass


class SuggestValuesReq(F5XCBaseModel):
    """Request body of SuggestValues request"""

    field_path: Optional[str] = None
    match_value: Optional[str] = None
    namespace: Optional[str] = None
    request_body: Optional[ProtobufAny] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class SuggestedItem(F5XCBaseModel):
    """A tuple with a suggested value and it's description."""

    description: Optional[str] = None
    ref_value: Optional[ObjectRefType] = None
    str_value: Optional[str] = None


class SuggestValuesResp(F5XCBaseModel):
    """Response body of SuggestValues request"""

    items: Optional[list[SuggestedItem]] = None


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = GlobalSpecType
Spec = SpecType
Spec = ReplaceSpecType
