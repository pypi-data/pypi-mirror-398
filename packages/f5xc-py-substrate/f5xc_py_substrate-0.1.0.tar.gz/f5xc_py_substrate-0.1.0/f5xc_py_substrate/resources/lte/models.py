"""Pydantic models for lte."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class Signal(F5XCBaseModel):
    """Advanced Signal Information"""

    rsrp: Optional[float] = None
    rsrq: Optional[float] = None
    rssi: Optional[float] = None
    sinr: Optional[float] = None


class Sim(F5XCBaseModel):
    """SIM Account Details"""

    iccid: Optional[str] = None
    imei: Optional[str] = None
    imsi: Optional[str] = None
    number: Optional[list[str]] = None


class Lte(F5XCBaseModel):
    """status of LTE connection"""

    connected: Optional[bool] = None
    operator: Optional[str] = None
    service_type: Optional[str] = None
    signal: Optional[Signal] = None
    signal_strength: Optional[Literal['UNKNOWN', 'EXCELLENT', 'GOOD', 'FAIR', 'POOR']] = None
    sim: Optional[Sim] = None
    uptime: Optional[int] = None


class Config(F5XCBaseModel):
    """Configuration of LTE"""

    apn: Optional[str] = None
    password: Optional[str] = None
    pin: Optional[str] = None
    primary: Optional[bool] = None
    user: Optional[str] = None


class DisconnectRequest(F5XCBaseModel):
    """Request to get Disconnect from LTE"""

    namespace: Optional[str] = None
    node: Optional[str] = None
    site: Optional[str] = None


class DisconnectResponse(F5XCBaseModel):
    """Response to get Disconnect from LTE"""

    pass


class GetConfigResponse(F5XCBaseModel):
    """Current LTE configuration."""

    config: Optional[Config] = None


class InfoResponse(F5XCBaseModel):
    """Runtime LTE information obtained from site."""

    lte_info: Optional[Lte] = None


class UpdateConfigRequest(F5XCBaseModel):
    """Updates LTE configuration."""

    config: Optional[Config] = None
    namespace: Optional[str] = None
    node: Optional[str] = None
    site: Optional[str] = None


class UpdateConfigResponse(F5XCBaseModel):
    """Response of Updates LTE configuration."""

    pass


# Convenience aliases
