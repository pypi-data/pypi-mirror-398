"""Pydantic models for bgp."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class BGPPath(F5XCBaseModel):
    """A BGP path"""

    as_path: Optional[str] = None
    local_pref: Optional[int] = None
    med: Optional[int] = None
    nh: Optional[list[str]] = None
    peer: Optional[str] = None


class Ipv4AddressType(F5XCBaseModel):
    """IPv4 Address in dot-decimal notation"""

    addr: Optional[str] = None


class Ipv6AddressType(F5XCBaseModel):
    """IPv6 Address specified as hexadecimal numbers separated by ':'"""

    addr: Optional[str] = None


class IpAddressType(F5XCBaseModel):
    """IP Address used to specify an IPv4 or IPv6 address"""

    ipv4: Optional[Ipv4AddressType] = None
    ipv6: Optional[Ipv6AddressType] = None


class PeerStatusType(F5XCBaseModel):
    """Most recently observed status of the BGP Peering session"""

    advertised_prefix_count: Optional[int] = None
    connection_flap_count: Optional[int] = None
    interface_name: Optional[str] = None
    local_address: Optional[str] = None
    peer_address: Optional[IpAddressType] = None
    peer_asn: Optional[int] = None
    peer_port: Optional[int] = None
    peer_router_id: Optional[str] = None
    protocol_status: Optional[Literal['Unknown', 'Idle', 'Connect', 'Active', 'OpenSent', 'OpenConfirm', 'Established', 'Clearing', 'Deleted']] = None
    received_prefix_count: Optional[int] = None
    up_down: Optional[Literal['BGP_PEER_DOWN', 'BGP_PEER_UP']] = None
    up_down_timestamp: Optional[str] = None


class VerBGPPeers(F5XCBaseModel):
    """List of BGP peers and their status from a ver instance"""

    name: Optional[str] = None
    peer: Optional[list[PeerStatusType]] = None


class BGPPeersResponse(F5XCBaseModel):
    """List of BGP peers and their status from all ver instances in the site"""

    ver: Optional[list[VerBGPPeers]] = None


class BGPRoute(F5XCBaseModel):
    """A BGP route"""

    path: Optional[list[BGPPath]] = None
    subnet: Optional[str] = None


class BGPRouteTable(F5XCBaseModel):
    """A route table"""

    exported: Optional[list[BGPRoute]] = None
    imported: Optional[list[BGPRoute]] = None
    name: Optional[str] = None


class BGPRoutingInstanceTable(F5XCBaseModel):
    """BGP tables per instance"""

    routing_instance: Optional[str] = None
    rt_table: Optional[list[BGPRouteTable]] = None


class VerBGPRoutes(F5XCBaseModel):
    """All BGP routes per instance per table from a ver instance"""

    name: Optional[str] = None
    ri_table: Optional[list[BGPRoutingInstanceTable]] = None


class BGPRoutesResponse(F5XCBaseModel):
    """All BGP routes per instance per table from all ver instances in the site"""

    ver: Optional[list[VerBGPRoutes]] = None


# Convenience aliases
