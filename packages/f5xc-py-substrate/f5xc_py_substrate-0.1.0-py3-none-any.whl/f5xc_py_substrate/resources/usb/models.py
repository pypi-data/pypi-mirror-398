"""Pydantic models for usb."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class UsbListItem(F5XCBaseModel):
    """List item for usb resources."""


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


class Rule(F5XCBaseModel):
    """USB Enablement Rule"""

    b_device_class: Optional[str] = None
    b_device_protocol: Optional[str] = None
    b_device_sub_class: Optional[str] = None
    i_serial: Optional[str] = None
    id_product: Optional[str] = None
    id_vendor: Optional[str] = None


class AddRulesRequest(F5XCBaseModel):
    """Request to add USB Enablement Rules"""

    namespace: Optional[str] = None
    node: Optional[str] = None
    rules: Optional[list[Rule]] = None
    site: Optional[str] = None


class AddRulesResponse(F5XCBaseModel):
    """Response to add USB Enablement Rules"""

    rules: Optional[list[Rule]] = None


class Config(F5XCBaseModel):
    """usb config"""

    usb_allow_list_enable: Optional[bool] = None


class DeleteRulesRequest(F5XCBaseModel):
    """Request to delete USB Enablement Rules"""

    namespace: Optional[str] = None
    node: Optional[str] = None
    rules: Optional[list[Rule]] = None
    site: Optional[str] = None


class DeleteRulesResponse(F5XCBaseModel):
    """Response to delete USB Enablement Rules"""

    rules: Optional[list[Rule]] = None


class GetConfigResponse(F5XCBaseModel):
    """Current USB configuration."""

    config: Optional[Config] = None


class ListResponse(F5XCBaseModel):
    """Response to list available USB devices"""

    namespace: Optional[str] = None
    node: Optional[str] = None
    site: Optional[str] = None
    usb: Optional[list[USBDevice]] = None


class ListRulesResponse(F5XCBaseModel):
    """Response to list USB Enablement Rules"""

    rules: Optional[list[Rule]] = None


class UpdateConfigRequest(F5XCBaseModel):
    """Updates USB configuration."""

    config: Optional[Config] = None
    namespace: Optional[str] = None
    node: Optional[str] = None
    site: Optional[str] = None


class UpdateConfigResponse(F5XCBaseModel):
    """Response of Updates USB configuration."""

    pass


# Convenience aliases
