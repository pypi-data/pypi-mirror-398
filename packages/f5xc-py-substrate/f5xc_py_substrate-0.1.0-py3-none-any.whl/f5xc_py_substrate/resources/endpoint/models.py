"""Pydantic models for endpoint."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class EndpointListItem(F5XCBaseModel):
    """List item for endpoint resources."""


class ConsulInfo(F5XCBaseModel):
    """Service instance resolved from Consul discovery"""

    instance_name: Optional[list[str]] = None
    labels: Optional[dict[str, Any]] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class DnsNameAdvancedType(F5XCBaseModel):
    """Specifies name and TTL used for DNS resolution."""

    name: Optional[str] = None
    refresh_interval: Optional[int] = None


class LabelSelectorType(F5XCBaseModel):
    """This type can be used to establish a 'selector reference' from one..."""

    expressions: Optional[list[str]] = None


class ServiceInfoType(F5XCBaseModel):
    """Specifies whether endpoint service is discovered by name or labels"""

    discovery_type: Optional[Literal['INVALID_DISCOVERY', 'K8S', 'CONSUL', 'CLASSIC_BIGIP', 'THIRD_PARTY']] = None
    service_name: Optional[str] = None
    service_selector: Optional[LabelSelectorType] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class PrefixStringListType(F5XCBaseModel):
    """x-example: '192.168.20.0/24' List of IPv4 prefixes that represent an endpoint"""

    prefixes: Optional[list[str]] = None


class SnatPoolConfiguration(F5XCBaseModel):
    """Snat Pool configuration"""

    no_snat_pool: Optional[Any] = None
    snat_pool: Optional[PrefixStringListType] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class SiteRefType(F5XCBaseModel):
    """This specifies a direct reference to a site configuration object"""

    disable_internet_vip: Optional[Any] = None
    enable_internet_vip: Optional[Any] = None
    network_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None
    ref: Optional[list[ObjectRefType]] = None


class NetworkRefType(F5XCBaseModel):
    """This specifies a direct reference to a network configuration object"""

    ref: Optional[list[ObjectRefType]] = None


class VSiteRefType(F5XCBaseModel):
    """A reference to virtual_site object"""

    disable_internet_vip: Optional[Any] = None
    enable_internet_vip: Optional[Any] = None
    network_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None
    ref: Optional[list[ObjectRefType]] = None


class NetworkSiteRefSelector(F5XCBaseModel):
    """NetworkSiteRefSelector defines a union of reference to site or reference..."""

    site: Optional[SiteRefType] = None
    virtual_network: Optional[NetworkRefType] = None
    virtual_site: Optional[VSiteRefType] = None


class CreateSpecType(F5XCBaseModel):
    """Create endpoint will create the object in the storage backend for..."""

    dns_name: Optional[str] = None
    dns_name_advanced: Optional[DnsNameAdvancedType] = None
    health_check_port: Optional[int] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    service_info: Optional[ServiceInfoType] = None
    snat_pool: Optional[SnatPoolConfiguration] = None
    where: Optional[NetworkSiteRefSelector] = None


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


class GetSpecType(F5XCBaseModel):
    """Get endpoint will get the object from the storage backend for namespace..."""

    dns_name: Optional[str] = None
    dns_name_advanced: Optional[DnsNameAdvancedType] = None
    health_check_port: Optional[int] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    service_info: Optional[ServiceInfoType] = None
    snat_pool: Optional[SnatPoolConfiguration] = None
    where: Optional[NetworkSiteRefSelector] = None


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


class DNSInfo(F5XCBaseModel):
    """Addresses resolved from DNS discovery"""

    resolved_ips: Optional[list[str]] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class K8SInfo(F5XCBaseModel):
    """Discovered Information for Kubernetes endpoints"""

    in_cluster_discovery: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    pod_name: Optional[list[str]] = None


class DiscoveredInfoType(F5XCBaseModel):
    """Discovered Information for endpoints"""

    consul_info: Optional[ConsulInfo] = None
    dns_info: Optional[DNSInfo] = None
    k8s_info: Optional[K8SInfo] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replacing an endpoint object will update the object by replacing the..."""

    dns_name: Optional[str] = None
    dns_name_advanced: Optional[DnsNameAdvancedType] = None
    health_check_port: Optional[int] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    service_info: Optional[ServiceInfoType] = None
    snat_pool: Optional[SnatPoolConfiguration] = None
    where: Optional[NetworkSiteRefSelector] = None


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


class Ipv6AddressType(F5XCBaseModel):
    """IPv6 Address specified as hexadecimal numbers separated by ':'"""

    addr: Optional[str] = None


class Ipv4AddressType(F5XCBaseModel):
    """IPv4 Address in dot-decimal notation"""

    addr: Optional[str] = None


class IpAddressType(F5XCBaseModel):
    """IP Address used to specify an IPv4 or IPv6 address"""

    ipv4: Optional[Ipv4AddressType] = None
    ipv6: Optional[Ipv6AddressType] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class HealthCheckInfoType(F5XCBaseModel):
    """Health status information sent for endpoints"""

    health_check: Optional[ObjectRefType] = None
    health_status: Optional[str] = None
    health_status_failure_details: Optional[str] = None
    health_status_failure_reason: Optional[str] = None
    health_status_update_time: Optional[str] = None
    last_health_status_failure_details: Optional[str] = None
    last_health_status_failure_reason: Optional[str] = None
    last_health_status_update_time: Optional[str] = None


class VerStatusType(F5XCBaseModel):
    """Status information sent for endpoints"""

    allocated_ip: Optional[Ipv6AddressType] = None
    discovered_info: Optional[DiscoveredInfoType] = None
    discovered_ip: Optional[IpAddressType] = None
    discovered_port: Optional[int] = None
    health_check_details: Optional[list[HealthCheckInfoType]] = None
    service_name: Optional[str] = None
    site: Optional[str] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of endpoint"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    origin_span: Optional[Literal['Local', 'Global']] = None
    ver_status: Optional[list[VerStatusType]] = None


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
    """By default a summary of endpoint is returned in 'List'. By setting..."""

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


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
