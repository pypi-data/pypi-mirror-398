"""Pydantic models for policy_based_routing."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class PolicyBasedRoutingListItem(F5XCBaseModel):
    """List item for policy_based_routing resources."""


class DomainType(F5XCBaseModel):
    """Domains names"""

    exact_value: Optional[str] = None
    regex_value: Optional[str] = None
    suffix_value: Optional[str] = None


class DomainListType(F5XCBaseModel):
    tls_list: Optional[list[DomainType]] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class URLType(F5XCBaseModel):
    """URL strings in form 'http://<domian>/<path>'"""

    any_path: Optional[Any] = None
    exact_value: Optional[str] = None
    path_exact_value: Optional[str] = None
    path_prefix_value: Optional[str] = None
    path_regex_value: Optional[str] = None
    regex_value: Optional[str] = None
    suffix_value: Optional[str] = None


class URLListType(F5XCBaseModel):
    http_list: Optional[list[URLType]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ApplicationsType(F5XCBaseModel):
    """Application protocols like HTTP, SNMP"""

    applications: Optional[list[Literal['APPLICATION_HTTP', 'APPLICATION_HTTPS', 'APPLICATION_SNMP', 'APPLICATION_DNS']]] = None


class ProtocolPortType(F5XCBaseModel):
    """Protocol and Port ranges"""

    port_ranges: Optional[list[str]] = None
    protocol: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class LabelSelectorType(F5XCBaseModel):
    """This type can be used to establish a 'selector reference' from one..."""

    expressions: Optional[list[str]] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class PrefixStringListType(F5XCBaseModel):
    """x-example: '192.168.20.0/24' List of IPv4 prefixes that represent an endpoint"""

    prefixes: Optional[list[str]] = None


class ForwardProxyPBRRuleType(F5XCBaseModel):
    """URL(s) and domains policy for forward proxy for a connection type (TLS or HTTP)"""

    all_destinations: Optional[Any] = None
    all_sources: Optional[Any] = None
    forwarding_class_list: Optional[list[ObjectRefType]] = None
    http_list: Optional[URLListType] = None
    ip_prefix_set: Optional[ObjectRefType] = None
    label_selector: Optional[LabelSelectorType] = None
    metadata: Optional[MessageMetaType] = None
    prefix_list: Optional[PrefixStringListType] = None
    tls_list: Optional[DomainListType] = None


class ForwardProxyPBRType(F5XCBaseModel):
    """Network(L3/L4) routing policy rule"""

    forward_proxy_pbr_rules: Optional[list[ForwardProxyPBRRuleType]] = None


class IpPrefixSetRefType(F5XCBaseModel):
    """A list of references to ip_prefix_set objects."""

    ref: Optional[list[ObjectRefType]] = None


class NetworkPBRRuleType(F5XCBaseModel):
    """Shape of Network PBR Rule"""

    all_tcp_traffic: Optional[Any] = None
    all_traffic: Optional[Any] = None
    all_udp_traffic: Optional[Any] = None
    any: Optional[Any] = None
    applications: Optional[ApplicationsType] = None
    dns_name: Optional[str] = None
    forwarding_class_list: Optional[list[ObjectRefType]] = None
    ip_prefix_set: Optional[IpPrefixSetRefType] = None
    metadata: Optional[MessageMetaType] = None
    prefix_list: Optional[PrefixStringListType] = None
    protocol_port_range: Optional[ProtocolPortType] = None


class NetworkPBRType(F5XCBaseModel):
    """Network(L3/L4) routing policy rule"""

    any: Optional[Any] = None
    label_selector: Optional[LabelSelectorType] = None
    network_pbr_rules: Optional[list[NetworkPBRRuleType]] = None
    prefix_list: Optional[PrefixStringListType] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the Network Policy based routing create specification"""

    forward_proxy_pbr: Optional[ForwardProxyPBRType] = None
    forwarding_class_list: Optional[list[ObjectRefType]] = None
    network_pbr: Optional[NetworkPBRType] = None


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
    """Shape of the Network Policy based routing get specification"""

    forward_proxy_pbr: Optional[ForwardProxyPBRType] = None
    forwarding_class_list: Optional[list[ObjectRefType]] = None
    network_pbr: Optional[NetworkPBRType] = None


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
    """Shape of the Network Policy based routing replace specification"""

    forward_proxy_pbr: Optional[ForwardProxyPBRType] = None
    forwarding_class_list: Optional[list[ObjectRefType]] = None
    network_pbr: Optional[NetworkPBRType] = None


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
    """By default a summary of policy_based_routing is returned in 'List'. By..."""

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
