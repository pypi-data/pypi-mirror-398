"""Pydantic models for route."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


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


class DcgHop(F5XCBaseModel):
    """DC Cluster Group intermediate hop type"""

    site_ip: Optional[IpAddressType] = None
    site_name: Optional[str] = None


class DropNH(F5XCBaseModel):
    """Nexthop type to drop packets"""

    pass


class GREHop(F5XCBaseModel):
    """GRE Tunnel intermediate hop type"""

    site_ip: Optional[IpAddressType] = None
    site_name: Optional[str] = None


class GREType(F5XCBaseModel):
    """x-displaName: 'GRE Tunnel Type' GRE tunnel type"""

    interface: Optional[str] = None


class IPSecType(F5XCBaseModel):
    """x-displaName: 'IPSec Tunnel Type' IPSec tunnel type"""

    interface: Optional[str] = None


class IpSecHop(F5XCBaseModel):
    """IPSec Tunnel intermediate hop type"""

    site_ip: Optional[IpAddressType] = None
    site_name: Optional[str] = None


class SslHop(F5XCBaseModel):
    """SSL Tunnel intermediate hop type"""

    site_ip: Optional[IpAddressType] = None
    site_name: Optional[str] = None


class IntermediateHop(F5XCBaseModel):
    """Type of entity via which packet is routed to final destination"""

    dcg: Optional[DcgHop] = None
    gre: Optional[GREHop] = None
    ipsec: Optional[IpSecHop] = None
    node: Optional[str] = None
    ssl: Optional[SslHop] = None


class IPinIPType(F5XCBaseModel):
    """x-displaName: 'IPinIP Tunnel Type' IPinIP tunnel type"""

    intermediate_hop: Optional[list[IntermediateHop]] = None


class IPinUDPType(F5XCBaseModel):
    """x-displaName: 'IPinUDP Tunnel Type' IPinUDP tunnel type"""

    intermediate_hop: Optional[list[IntermediateHop]] = None


class LocalNH(F5XCBaseModel):
    """x-dsiplayName: 'Local Nexthop Type' Nexthop type for packets destined to..."""

    interface: Optional[str] = None


class MPLSType(F5XCBaseModel):
    """x-displaName: 'MPLS Tunnel Type' MPLS tunnel type"""

    intermediate_hop: Optional[list[IntermediateHop]] = None


class Info(F5XCBaseModel):
    """Route information"""

    flags: Optional[str] = None
    label: Optional[int] = None
    nh: Optional[int] = None
    nh_info: Optional[str] = None
    prefix: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class PrefixListType(F5XCBaseModel):
    """List of IP Address prefixes. Prefix must contain both prefix and..."""

    prefix: Optional[list[str]] = None


class Request(F5XCBaseModel):
    """Request to get list of VER routes matching the request"""

    cluster_wide: Optional[Any] = None
    family: Optional[Literal['INET4', 'INET6']] = None
    namespace: Optional[str] = None
    node: Optional[str] = None
    prefix: Optional[PrefixListType] = None
    segment: Optional[str] = None
    site: Optional[str] = None
    vn: Optional[str] = None
    vn_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None


class RouteRoutes(F5XCBaseModel):
    """Matching routes from VER"""

    node: Optional[str] = None
    route: Optional[list[Info]] = None


class Response(F5XCBaseModel):
    """List of routes from ver instances in the site"""

    ver_routes: Optional[list[RouteRoutes]] = None


class SSLType(F5XCBaseModel):
    """x-displaName: 'SSL Tunnel Type' SSL tunnel type"""

    interface: Optional[str] = None


class SubnetNH(F5XCBaseModel):
    """Nexthop type for packets coming to a subnet"""

    intf_name: Optional[str] = None


class TunnelNH(F5XCBaseModel):
    """Nexthop type for packets going out on a tunnel/tunnel interface"""

    gre: Optional[GREType] = None
    ip_in_ip: Optional[IPinIPType] = None
    ip_in_udp: Optional[IPinUDPType] = None
    ipsec: Optional[IPSecType] = None
    mpls: Optional[MPLSType] = None
    remote_ip: Optional[IpAddressType] = None
    remote_site: Optional[str] = None
    ssl: Optional[SSLType] = None


class SimplifiedNexthopType(F5XCBaseModel):
    """Information about the nexthop based on type"""

    drop: Optional[Any] = None
    local: Optional[LocalNH] = None
    subnet: Optional[SubnetNH] = None
    tunnel: Optional[TunnelNH] = None


class SimplifiedEcmpNH(F5XCBaseModel):
    """ECMP type nexthop contains multiple member nexthops"""

    members: Optional[list[SimplifiedNexthopType]] = None


class SimplifiedRouteInfo(F5XCBaseModel):
    """Simplified Route information"""

    ecmp: Optional[SimplifiedEcmpNH] = None
    flags: Optional[list[str]] = None
    nexthop: Optional[SimplifiedNexthopType] = None
    prefix: Optional[str] = None
    route_type: Optional[Literal['REMOTE_SITE_ROUTE', 'LOCAL_ROUTE', 'STATIC_ROUTE', 'BGP_ROUTE']] = None


class SimplifiedRouteRequest(F5XCBaseModel):
    """Request to get list of VER routes matching the request"""

    all_nodes: Optional[Any] = None
    family: Optional[Literal['INET4', 'INET6']] = None
    global_network: Optional[str] = None
    namespace: Optional[str] = None
    node: Optional[str] = None
    prefix: Optional[PrefixListType] = None
    segment: Optional[str] = None
    site: Optional[str] = None
    sli: Optional[Any] = None
    slo: Optional[Any] = None


class SimplifiedRoutes(F5XCBaseModel):
    """Matching routes from VER"""

    node: Optional[str] = None
    route: Optional[list[SimplifiedRouteInfo]] = None


class SimplifiedRouteResponse(F5XCBaseModel):
    """List of routes from ver instances in the site"""

    ver_routes: Optional[list[SimplifiedRoutes]] = None


# Convenience aliases
