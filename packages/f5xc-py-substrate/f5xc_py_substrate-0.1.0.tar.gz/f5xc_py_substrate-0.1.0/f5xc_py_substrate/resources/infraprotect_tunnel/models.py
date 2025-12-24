"""Pydantic models for infraprotect_tunnel."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class InfraprotectTunnelListItem(F5XCBaseModel):
    """List item for infraprotect_tunnel resources."""


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


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


class BGPInformation(F5XCBaseModel):
    """BGP information associated with a DDoS transit tunnel."""

    asn: Optional[ObjectRefType] = None
    holddown_timer_seconds: Optional[int] = None
    no_secret: Optional[Any] = None
    peer_secret_override: Optional[SecretType] = None
    use_default_secret: Optional[Any] = None


class Bandwidth(F5XCBaseModel):
    """Bandwidth max allowed"""

    bandwidth_max_mb: Optional[int] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class GreIpv4Tunnel(F5XCBaseModel):
    """IPv4 Tunnel."""

    customer_endpoint_ipv4: Optional[str] = None
    fragmentation_disabled: Optional[Any] = None
    fragmentation_enabled: Optional[Any] = None
    ipv6_interconnect_disabled: Optional[Any] = None
    ipv6_interconnect_enabled: Optional[Any] = None
    keepalive_disabled: Optional[Any] = None
    keepalive_enabled: Optional[Any] = None


class GreIpv6Tunnel(F5XCBaseModel):
    """IPv6 Tunnel."""

    customer_endpoint_ipv6: Optional[str] = None
    ipv4_interconnect_disabled: Optional[Any] = None
    ipv4_interconnect_enabled: Optional[Any] = None


class IpInIpTunnel(F5XCBaseModel):
    """IP in IP Tunnel."""

    customer_endpoint_ipv4: Optional[str] = None


class Ipv6ToIpv6Tunnel(F5XCBaseModel):
    """IPv6 to IPv6 Tunnel."""

    customer_endpoint_ipv6: Optional[str] = None


class TunnelLocation(F5XCBaseModel):
    """Location of a DDoS transit tunnel."""

    name: Optional[str] = None
    zone1: Optional[Any] = None
    zone2: Optional[Any] = None


class CreateSpecType(F5XCBaseModel):
    """Creates a DDoS transit tunnel"""

    bandwidth: Optional[Bandwidth] = None
    bgp_information: Optional[BGPInformation] = None
    firewall_rule_group: Optional[ObjectRefType] = None
    gre_ipv4: Optional[GreIpv4Tunnel] = None
    gre_ipv6: Optional[GreIpv6Tunnel] = None
    ip_in_ip: Optional[IpInIpTunnel] = None
    ipv6_to_ipv6: Optional[Ipv6ToIpv6Tunnel] = None
    tunnel_location: Optional[TunnelLocation] = None


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class L2DirectConnectTunnel(F5XCBaseModel):
    """L2 Direct Connect Tunnel"""

    pass


class L2EquinixTunnel(F5XCBaseModel):
    """L2 Equinix Tunnel"""

    pass


class L2MegaportTunnel(F5XCBaseModel):
    """L2 Megaport Tunnel"""

    pass


class L2PacketFabricTunnel(F5XCBaseModel):
    """L2 Packet Fabric Tunnel"""

    pass


class GetSpecType(F5XCBaseModel):
    """Get DDoS transit tunnel"""

    bandwidth: Optional[Bandwidth] = None
    bgp_information: Optional[BGPInformation] = None
    customer_asn: Optional[int] = None
    customer_ipv4_interconnect: Optional[str] = None
    customer_ipv6_interconnect: Optional[str] = None
    f5_endpoint_ip: Optional[str] = None
    f5_ipv4_interconnect: Optional[str] = None
    f5_ipv6_interconnect: Optional[str] = None
    f5_peer_asn: Optional[int] = None
    firewall_rule_group: Optional[ObjectRefType] = None
    gre_ipv4: Optional[GreIpv4Tunnel] = None
    gre_ipv6: Optional[GreIpv6Tunnel] = None
    id_: Optional[str] = Field(default=None, alias="id")
    ip_in_ip: Optional[IpInIpTunnel] = None
    ipv6_to_ipv6: Optional[Ipv6ToIpv6Tunnel] = None
    l2_direct_connect: Optional[Any] = None
    l2_equinix: Optional[Any] = None
    l2_megaport: Optional[Any] = None
    l2_packet_fabric: Optional[Any] = None
    tunnel_location: Optional[TunnelLocation] = None
    tunnel_status: Optional[Literal['TUNNEL_STATUS_INACTIVE', 'TUNNEL_STATUS_DOWN', 'TUNNEL_STATUS_ACTIVE', 'TUNNEL_STATUS_ACTIVATION_PENDING', 'TUNNEL_STATUS_ACTIVATION_ERROR', 'TUNNEL_STATUS_ACTIVATION_INITIALIZING']] = None


class InitializerType(F5XCBaseModel):
    """Initializer is information about an initializer that has not yet completed."""

    name: Optional[str] = None


class StatusType(F5XCBaseModel):
    """Status is a return value for calls that don't return other objects."""

    code: Optional[int] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class InitializersType(F5XCBaseModel):
    """Initializers tracks the progress of initialization of a configuration object"""

    pending: Optional[list[InitializerType]] = None
    result: Optional[StatusType] = None


class ViewRefType(F5XCBaseModel):
    """ViewRefType represents a reference to a view"""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class SystemObjectGetMetaType(F5XCBaseModel):
    """SystemObjectGetMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Amends a DDoS transit tunnel"""

    bandwidth: Optional[Bandwidth] = None
    firewall_rule_group: Optional[ObjectRefType] = None
    gre_ipv4: Optional[GreIpv4Tunnel] = None
    gre_ipv6: Optional[GreIpv6Tunnel] = None
    ip_in_ip: Optional[IpInIpTunnel] = None
    ipv6_to_ipv6: Optional[Ipv6ToIpv6Tunnel] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class StatusMetaType(F5XCBaseModel):
    """StatusMetaType is metadata that all status must have."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_id: Optional[str] = None
    publish: Optional[Literal['STATUS_DO_NOT_PUBLISH', 'STATUS_PUBLISH']] = None
    status_id: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class StatusObject(F5XCBaseModel):
    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[CreateRequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[ReplaceRequest] = None
    spec: Optional[GetSpecType] = None
    status: Optional[list[StatusObject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of infraprotect_tunnel is returned in 'List'. By..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[GetSpecType] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[StatusObject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[ListResponseItem]] = None


class ReplaceResponse(F5XCBaseModel):
    pass


class UpdateTunnelStatusRequest(F5XCBaseModel):
    """Request to update tunnel status"""

    namespace: Optional[str] = None
    tunnel_id: Optional[str] = None
    tunnel_status: Optional[Literal['TUNNEL_STATUS_INACTIVE', 'TUNNEL_STATUS_DOWN', 'TUNNEL_STATUS_ACTIVE', 'TUNNEL_STATUS_ACTIVATION_PENDING', 'TUNNEL_STATUS_ACTIVATION_ERROR', 'TUNNEL_STATUS_ACTIVATION_INITIALIZING']] = None


class UpdateTunnelStatusResponse(F5XCBaseModel):
    """Response returned from a tunnel status update"""

    pass


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
