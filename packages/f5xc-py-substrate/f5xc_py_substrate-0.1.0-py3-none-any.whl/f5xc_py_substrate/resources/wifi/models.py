"""Pydantic models for wifi."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class WifiListItem(F5XCBaseModel):
    """List item for wifi resources."""


class Wifi(F5XCBaseModel):
    """status of wifi connection"""

    bssid: Optional[str] = None
    connected: Optional[bool] = None
    frequency: Optional[int] = None
    receive_bitrate: Optional[int] = None
    signal: Optional[int] = None
    signal_strength: Optional[Literal['UNAVAILABLE', 'EXCELLENT', 'GOOD', 'FAIR', 'POOR']] = None
    ssid: Optional[str] = None
    transmit_bitrate: Optional[int] = None


class SecurityNone(F5XCBaseModel):
    """WIFI without any security mechanism"""

    pass


class SecurityWpa2Personal(F5XCBaseModel):
    """WIFI WPA2 Personal security mechanism"""

    password: Optional[str] = None


class Config(F5XCBaseModel):
    """Configuration of WIFI"""

    none: Optional[Any] = None
    ssid: Optional[str] = None
    wpa2_personal: Optional[SecurityWpa2Personal] = None


class DisconnectRequest(F5XCBaseModel):
    """Request to get Disconnect from WIFI"""

    namespace: Optional[str] = None
    node: Optional[str] = None
    site: Optional[str] = None


class DisconnectResponse(F5XCBaseModel):
    """Response to get Disconnect from WIFI"""

    pass


class GetConfigResponse(F5XCBaseModel):
    """Current WIFI configuration."""

    config: Optional[Config] = None


class InfoResponse(F5XCBaseModel):
    """Runtime WIFI information obtained from site."""

    wifi_info: Optional[Wifi] = None


class Item(F5XCBaseModel):
    """Available WIFI network information"""

    security_mechanism: Optional[Literal['UNKNOWN', 'NONE', 'WPA2_PERSONAL', 'WPA2_ENTERPRISE']] = None
    ssid: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """List of available WIFI networks."""

    wifi_item: Optional[list[Item]] = None


class UpdateConfigRequest(F5XCBaseModel):
    """Updates WIFI configuration."""

    config: Optional[Config] = None
    namespace: Optional[str] = None
    node: Optional[str] = None
    site: Optional[str] = None


class UpdateConfigResponse(F5XCBaseModel):
    """Response of Updates WIFI configuration."""

    pass


# Convenience aliases
