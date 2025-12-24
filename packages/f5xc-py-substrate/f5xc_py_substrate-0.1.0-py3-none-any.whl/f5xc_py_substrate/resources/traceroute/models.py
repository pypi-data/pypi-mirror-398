"""Pydantic models for traceroute."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class HostIdentifier(F5XCBaseModel):
    """Host Identifier identifies a host, either by its DNS name (hostname) or..."""

    hostname: Optional[str] = None
    ip: Optional[str] = None


class InterfaceIdentifier(F5XCBaseModel):
    """Interface Identifier identifies one or all interfaces on a node"""

    any_intf: Optional[Any] = None
    intf: Optional[str] = None


class Hop(F5XCBaseModel):
    """Hop info for each Traceroute response"""

    addr: Optional[str] = None
    elapsed_time_ms: Optional[int] = None
    host: Optional[str] = None
    ttl: Optional[int] = None


class Request(F5XCBaseModel):
    """Request to run traceroute to a destination"""

    dest: Optional[HostIdentifier] = None
    hops: Optional[int] = None
    intf: Optional[InterfaceIdentifier] = None
    namespace: Optional[str] = None
    node: Optional[str] = None
    retries: Optional[int] = None
    site: Optional[str] = None


class Response(F5XCBaseModel):
    """Response to Traceroute request"""

    hops: Optional[list[Hop]] = None


# Convenience aliases
