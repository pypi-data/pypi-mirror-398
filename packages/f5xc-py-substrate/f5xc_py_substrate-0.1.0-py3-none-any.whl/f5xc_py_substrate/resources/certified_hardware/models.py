"""Pydantic models for certified_hardware."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class CertifiedHardwareListItem(F5XCBaseModel):
    """List item for certified_hardware resources."""


class AwsImage(F5XCBaseModel):
    image_id: Optional[str] = None
    region: Optional[str] = None


class Aws(F5XCBaseModel):
    """AWS specific information"""

    image_id: Optional[AwsImage] = None


class AzureImage(F5XCBaseModel):
    image_id: Optional[str] = None


class Marketplace(F5XCBaseModel):
    """Azure Marketplace image information"""

    name: Optional[str] = None
    offer: Optional[str] = None
    publisher: Optional[str] = None
    sku: Optional[str] = None
    version: Optional[str] = None


class Azure(F5XCBaseModel):
    """Azure specific information"""

    image_id: Optional[AzureImage] = None
    marketplace: Optional[Marketplace] = None


class Status(F5XCBaseModel):
    """Current status of Certified Hardware"""

    latest_version: Optional[str] = None


class DeviceType(F5XCBaseModel):
    """Different type of devices supported by Certified Hardware"""

    device_list: Optional[list[str]] = None
    max_unit: Optional[int] = None
    min_unit: Optional[int] = None
    name: Optional[str] = None
    type_: Optional[Literal['HARDWARE_DEVICE_INVALID', 'HARDWARE_DEVICE_ETHERNET', 'HARDWARE_DEVICE_VIRTIO', 'HARDWARE_DEVICE_TUNTAP', 'HARDWARE_DEVICE_BOND', 'HARDWARE_DEVICE_EXTERNAL_ISCSI_STORTAGE', 'HARDWARE_DEVICE_NVIDIA_GPU']] = Field(default=None, alias="type")
    use: Optional[Literal['HARDWARE_DEVICE_USE_REGULAR', 'HARDWARE_DEVICE_USE_INTERNAL', 'HARDWARE_NETWORK_DEVICE_USE_REGULAR', 'HARDWARE_NETWORK_DEVICE_USE_INTERNAL', 'HARDWARE_NETWORK_DEVICE_USE_MANAGEMENT', 'HARDWARE_NETWORK_DEVICE_USE_OUTSIDE', 'HARDWARE_NETWORK_DEVICE_USE_INSIDE', 'HARDWARE_NETWORK_DEVICE_USE_OUTSIDE_LAG', 'HARDWARE_NETWORK_DEVICE_USE_INSIDE_LAG', 'HARDWARE_NETWORK_DEVICE_USE_LAG_MEMBER', 'HARDWARE_NETWORK_DEVICE_USE_STORAGE', 'HARDWARE_NETWORK_DEVICE_USE_FALLBACK_MANAGEMENT']] = None


class GcpImage(F5XCBaseModel):
    image_id: Optional[str] = None


class Gcp(F5XCBaseModel):
    """GCP specific information"""

    image_id: Optional[GcpImage] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ImageType(F5XCBaseModel):
    """Describes the image to be used for this certified hardware"""

    aws: Optional[Aws] = None
    azure: Optional[Azure] = None
    gcp: Optional[Gcp] = None
    name: Optional[str] = None
    provider: Optional[str] = None


class Rule(F5XCBaseModel):
    """USB Enablement Rule"""

    b_device_class: Optional[str] = None
    b_device_protocol: Optional[str] = None
    b_device_sub_class: Optional[str] = None
    i_serial: Optional[str] = None
    id_product: Optional[str] = None
    id_vendor: Optional[str] = None


class NumaMem(F5XCBaseModel):
    """Defines amount of memory (in MB) allocated for a NUMA node"""

    memory: Optional[int] = None
    node: Optional[int] = None


class HardwareVendorModel(F5XCBaseModel):
    """Gives vendor and model for the hardware device"""

    model: Optional[str] = None
    vendor: Optional[str] = None


class GetSpecType(F5XCBaseModel):
    """Get Certified Hardware object"""

    certified_hardware_type: Optional[Literal['VOLTMESH', 'VOLTSTACK_COMBO', 'CLOUD_MARKET_PLACE']] = None
    devices: Optional[list[DeviceType]] = None
    image_list: Optional[list[ImageType]] = None
    internal_usb_device_rule: Optional[list[Rule]] = None
    mem_page_number: Optional[int] = None
    mem_page_size: Optional[Literal['HARDWARE_MEM_PAGE_SIZE_INVALID', 'HARDWARE_MEM_PAGE_SIZE_4KB', 'HARDWARE_MEM_PAGE_SIZE_2MB', 'HARDWARE_MEM_PAGE_SIZE_1GB']] = None
    numa_mem: Optional[list[NumaMem]] = None
    numa_nodes: Optional[int] = None
    vendor_model_list: Optional[list[HardwareVendorModel]] = None


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
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    status: Optional[Status] = None


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


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
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
    """By default a summary of certified_hardware is returned in 'List'. By..."""

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


# Convenience aliases
Spec = GetSpecType
