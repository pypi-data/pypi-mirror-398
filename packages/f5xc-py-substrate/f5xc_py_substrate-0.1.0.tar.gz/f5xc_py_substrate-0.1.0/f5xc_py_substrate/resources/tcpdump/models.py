"""Pydantic models for tcpdump."""

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


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class InterfaceOrNetwork(F5XCBaseModel):
    """Selects an interface on a node"""

    intf: Optional[str] = None
    pod: Optional[str] = None
    vn: Optional[str] = None
    vn_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None


class InterfaceTcpdumpStatus(F5XCBaseModel):
    """Status of tcpdump capture on an interface"""

    intf: Optional[InterfaceOrNetwork] = None
    last_capture_timestamp: Optional[str] = None
    status: Optional[Literal['RUNNING', 'COMPLETED', 'FAILED', 'NOT_STARTED']] = None


class ListRequest(F5XCBaseModel):
    """Request to list Tcpdump capture status on a node"""

    namespace: Optional[str] = None
    node: Optional[str] = None
    site: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """List of Tcpdump capture status on a node"""

    intf_status: Optional[list[InterfaceTcpdumpStatus]] = None


class StopResponse(F5XCBaseModel):
    """Response for a stop tcpdump request"""

    pass


class Request(F5XCBaseModel):
    """Request to run tcpdump on a ver interface"""

    count: Optional[int] = None
    intf: Optional[InterfaceOrNetwork] = None
    max_time_period: Optional[int] = None
    namespace: Optional[str] = None
    node: Optional[str] = None
    options: Optional[str] = None
    site: Optional[str] = None


class Response(F5XCBaseModel):
    """Response to the Tcpdump request"""

    count: Optional[int] = None
    duration: Optional[int] = None
    error: Optional[ErrorType] = None
    interface_name: Optional[str] = None
    node: Optional[str] = None
    status: Optional[str] = None


# Convenience aliases
