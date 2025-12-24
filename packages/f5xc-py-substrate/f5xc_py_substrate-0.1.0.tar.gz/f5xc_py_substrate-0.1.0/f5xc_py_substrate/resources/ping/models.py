"""Pydantic models for ping."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class HostIdentifier(F5XCBaseModel):
    """Host Identifier identifies a host, either by its DNS name (hostname) or..."""

    hostname: Optional[str] = None
    ip: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class InterfaceIdentifier(F5XCBaseModel):
    """Interface Identifier identifies one or all interfaces on a node"""

    any_intf: Optional[Any] = None
    intf: Optional[str] = None


class Request(F5XCBaseModel):
    """Request to run ping to a destination"""

    count: Optional[int] = None
    dest: Optional[HostIdentifier] = None
    interval: Optional[int] = None
    intf: Optional[InterfaceIdentifier] = None
    namespace: Optional[str] = None
    node: Optional[str] = None
    pkt_size: Optional[int] = None
    site: Optional[str] = None


class Response(F5XCBaseModel):
    """Response to the ping request"""

    avg_rtt: Optional[str] = None
    dest: Optional[str] = None
    lost: Optional[int] = None
    max_rtt: Optional[str] = None
    min_rtt: Optional[str] = None
    received: Optional[int] = None
    sent: Optional[int] = None
    std_dev_rtt: Optional[str] = None


# Convenience aliases
