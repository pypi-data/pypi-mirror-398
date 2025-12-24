"""Pydantic models for nat_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class NatPolicyListItem(F5XCBaseModel):
    """List item for nat_policy resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class CloudElasticIpRefListType(F5XCBaseModel):
    """List of references to Cloud Elastic IP Object"""

    refs: Optional[list[ObjectRefType]] = None


class PrefixStringListType(F5XCBaseModel):
    """x-example: '192.168.20.0/24' List of IPv4 prefixes that represent an endpoint"""

    prefixes: Optional[list[str]] = None


class DynamicPool(F5XCBaseModel):
    """Dynamic Pool Configuration"""

    elastic_ips: Optional[CloudElasticIpRefListType] = None
    pools: Optional[PrefixStringListType] = None


class ActionType(F5XCBaseModel):
    """Action to apply on the packet if the NAT rule is applied"""

    dynamic: Optional[DynamicPool] = None
    virtual_cidr: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class CloudConnectRefType(F5XCBaseModel):
    """Reference to Cloud connect Object"""

    refs: Optional[list[ObjectRefType]] = None


class PortMatcherType(F5XCBaseModel):
    """Port match of the request can be a range or a specific port"""

    no_port_match: Optional[Any] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None


class SegmentRefType(F5XCBaseModel):
    """Reference to Segment Object"""

    refs: Optional[list[ObjectRefType]] = None


class PortConfiguration(F5XCBaseModel):
    """Action to apply on the packet if the NAT rule is applied"""

    destination_port: Optional[PortMatcherType] = None
    source_port: Optional[PortMatcherType] = None


class VirtualNetworkReferenceType(F5XCBaseModel):
    """Carries the reference to virtual network"""

    refs: Optional[list[ObjectRefType]] = None


class MatchCriteriaType(F5XCBaseModel):
    """Match criteria of the packet to apply the NAT Rule"""

    any: Optional[Any] = None
    destination_cidr: Optional[list[str]] = None
    destination_port: Optional[PortMatcherType] = None
    icmp: Optional[Any] = None
    protocol: Optional[Literal['ALL', 'ICMP', 'TCP', 'UDP']] = None
    segment: Optional[SegmentRefType] = None
    source_cidr: Optional[list[str]] = None
    source_port: Optional[PortMatcherType] = None
    tcp: Optional[PortConfiguration] = None
    udp: Optional[PortConfiguration] = None
    virtual_network: Optional[VirtualNetworkReferenceType] = None


class NetworkInterfaceRefType(F5XCBaseModel):
    """Reference to Network Interface Object"""

    refs: Optional[list[ObjectRefType]] = None


class RuleType(F5XCBaseModel):
    """Rule specifies configuration of where, when and how to apply the NAT Policy"""

    action: Optional[ActionType] = None
    cloud_connect: Optional[CloudConnectRefType] = None
    criteria: Optional[MatchCriteriaType] = None
    disable: Optional[Any] = None
    enable: Optional[Any] = None
    name: Optional[str] = None
    network_interface: Optional[NetworkInterfaceRefType] = None
    segment: Optional[SegmentRefType] = None
    virtual_network: Optional[VirtualNetworkReferenceType] = None


class SiteReferenceType(F5XCBaseModel):
    """Reference to Site Object"""

    refs: Optional[list[ObjectRefType]] = None


class CreateSpecType(F5XCBaseModel):
    """NAT Policy create specification configures NAT Policy with multiple Rules,"""

    rules: Optional[list[RuleType]] = None
    site: Optional[SiteReferenceType] = None


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
    """NAT Policy Get specification fetches the configuration from store which..."""

    rules: Optional[list[RuleType]] = None
    site: Optional[SiteReferenceType] = None


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


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """NAT Policy replaces specification condigures NAT Policy with multiple..."""

    rules: Optional[list[RuleType]] = None
    site: Optional[SiteReferenceType] = None


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
    """Most recently observed status of object"""

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
    """By default a summary of nat_policy is returned in 'List'. By setting..."""

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
