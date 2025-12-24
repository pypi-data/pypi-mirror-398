"""Pydantic models for debug."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class HttpBody(F5XCBaseModel):
    """Message that represents an arbitrary HTTP body. It should only be used..."""

    content_type: Optional[str] = None
    data: Optional[str] = None
    extensions: Optional[list[ProtobufAny]] = None


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


class ChangePasswordRequest(F5XCBaseModel):
    """Change password request for host"""

    console_user: Optional[str] = None
    current_password: Optional[SecretType] = None
    new_password: Optional[SecretType] = None
    node: Optional[str] = None
    site: Optional[str] = None
    username: Optional[str] = None


class CheckDebugInfoCollectionResponse(F5XCBaseModel):
    """Check debug info from site"""

    collection_start_time: Optional[str] = None
    debug_in_progress: Optional[bool] = None
    node_name: Optional[str] = None
    validity: Optional[str] = None


class DiagnosisResponse(F5XCBaseModel):
    """Dignosis response info from site"""

    curl_response: Optional[dict[str, Any]] = None
    registration_status: Optional[dict[str, Any]] = None
    responses: Optional[dict[str, Any]] = None


class ExecLogResponse(F5XCBaseModel):
    """Exec Log response"""

    exec_log: Optional[str] = None


class ExecResponse(F5XCBaseModel):
    """Exec response"""

    output: Optional[str] = None
    return_code: Optional[int] = None


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


class HealthResponse(F5XCBaseModel):
    """Health response info from site"""

    fqdn: Optional[str] = None
    hostname: Optional[str] = None
    initial_password_changed: Optional[bool] = None
    lte_support: Optional[bool] = None
    os_info: Optional[OsInfo] = None
    os_version: Optional[str] = None
    public_ip: Optional[str] = None
    roles: Optional[list[str]] = None
    software_version: Optional[str] = None
    state: Optional[Literal['WAITING_FOR_CONFIG', 'WAITING_FOR_APPROVAL', 'PROVISIONING', 'PROVISIONED', 'FAILED', 'RESETTING']] = None
    version: Optional[str] = None
    wifi_support: Optional[bool] = None


class HostPingRequest(F5XCBaseModel):
    """Request to initiate ping from the site"""

    count: Optional[int] = None
    dest: Optional[str] = None
    interval: Optional[int] = None
    length: Optional[int] = None
    namespace: Optional[str] = None
    node: Optional[str] = None
    site: Optional[str] = None


class HostPingResponse(F5XCBaseModel):
    """Response to initiated ping from the site"""

    avg_rtt: Optional[str] = None
    dest_ip: Optional[str] = None
    lost: Optional[int] = None
    max_rtt: Optional[str] = None
    min_rtt: Optional[str] = None
    received: Optional[int] = None
    sent: Optional[int] = None
    std_dev_rtt: Optional[str] = None


class Service(F5XCBaseModel):
    """Name and formal displayed name of the service"""

    name: Optional[str] = None
    node: Optional[str] = None
    value: Optional[str] = None


class ListServicesResponse(F5XCBaseModel):
    """List Services response"""

    service: Optional[list[Service]] = None


class LogResponse(F5XCBaseModel):
    """Log response"""

    log: Optional[str] = None


class RebootRequest(F5XCBaseModel):
    """Request to reboot specific node in site"""

    namespace: Optional[str] = None
    node: Optional[str] = None
    site: Optional[str] = None


class RebootResponse(F5XCBaseModel):
    """Reboot response"""

    pass


class SoftRestartRequest(F5XCBaseModel):
    """Request to soft restart reloads VER instance on the node"""

    namespace: Optional[str] = None
    node: Optional[str] = None
    service: Optional[str] = None
    site: Optional[str] = None


class SoftRestartResponse(F5XCBaseModel):
    """Soft Restart response"""

    pass


class Status(F5XCBaseModel):
    """Status of the service"""

    message: Optional[str] = None
    name: Optional[str] = None
    node: Optional[str] = None
    status: Optional[str] = None


class StatusResponse(F5XCBaseModel):
    """Status response"""

    status: Optional[list[Status]] = None


# Convenience aliases
