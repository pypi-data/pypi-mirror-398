"""Pydantic models for dhcp."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class KeyValuePair(F5XCBaseModel):
    """DHCP Option information as a (key, value) pair."""

    key: Optional[str] = None
    value: Optional[str] = None


class LeaseInfo(F5XCBaseModel):
    """Information about DHCP lease given by VER DHCP server."""

    client_id: Optional[str] = None
    description: Optional[str] = None
    expiry: Optional[str] = None
    hostname: Optional[str] = None
    interface: Optional[str] = None
    ip: Optional[str] = None
    issue_time: Optional[str] = None
    mac: Optional[str] = None
    options: Optional[list[KeyValuePair]] = None
    subnet: Optional[str] = None


class SubnetInfo(F5XCBaseModel):
    """Information about DHCP subnet"""

    address_count: Optional[int] = None
    free_address_count: Optional[int] = None
    interface: Optional[str] = None
    subnet: Optional[str] = None


class Leases(F5XCBaseModel):
    """Active list of DHCP leases that have been leased by VER DHCP server."""

    lease_info: Optional[list[LeaseInfo]] = None
    subnet_info: Optional[list[SubnetInfo]] = None


# Convenience aliases
