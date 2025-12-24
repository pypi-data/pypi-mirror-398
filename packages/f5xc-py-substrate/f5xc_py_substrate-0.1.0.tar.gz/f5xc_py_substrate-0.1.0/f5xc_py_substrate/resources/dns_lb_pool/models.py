"""Pydantic models for dns_lb_pool."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class DnsLbPoolListItem(F5XCBaseModel):
    """List item for dns_lb_pool resources."""


class AddressMember(F5XCBaseModel):
    """Public IP address which can be IPv4 or IPv6. This can be a member of..."""

    disable: Optional[bool] = None
    ip_endpoint: Optional[str] = None
    name: Optional[str] = None
    priority: Optional[int] = None
    ratio: Optional[int] = None


class AAAAPool(F5XCBaseModel):
    max_answers: Optional[int] = None
    members: Optional[list[AddressMember]] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class APool(F5XCBaseModel):
    disable_health_check: Optional[Any] = None
    health_check: Optional[ObjectRefType] = None
    max_answers: Optional[int] = None
    members: Optional[list[AddressMember]] = None


class CNAMEMember(F5XCBaseModel):
    """CNAME Record which can be a member of a CNAME type pool"""

    domain: Optional[str] = None
    final_translation: Optional[bool] = None
    name: Optional[str] = None
    ratio: Optional[int] = None


class CNAMEPool(F5XCBaseModel):
    members: Optional[list[CNAMEMember]] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class MXMember(F5XCBaseModel):
    """MX Record which can be a member of a MX type pool"""

    domain: Optional[str] = None
    name: Optional[str] = None
    priority: Optional[int] = None
    ratio: Optional[int] = None


class MXPool(F5XCBaseModel):
    max_answers: Optional[int] = None
    members: Optional[list[MXMember]] = None


class SRVMember(F5XCBaseModel):
    """SRV Record which can be a member of a SRV type pool"""

    final_translation: Optional[bool] = None
    name: Optional[str] = None
    port: Optional[int] = None
    priority: Optional[int] = None
    ratio: Optional[int] = None
    target: Optional[str] = None
    weight: Optional[int] = None


class SRVPool(F5XCBaseModel):
    max_answers: Optional[int] = None
    members: Optional[list[SRVMember]] = None


class CreateSpecType(F5XCBaseModel):
    """Create DNS Load Balancer Pool in a given namespace. If one already exist..."""

    a_pool: Optional[APool] = None
    aaaa_pool: Optional[AAAAPool] = None
    cname_pool: Optional[CNAMEPool] = None
    load_balancing_mode: Optional[Literal['ROUND_ROBIN', 'RATIO_MEMBER', 'STATIC_PERSIST', 'PRIORITY']] = None
    mx_pool: Optional[MXPool] = None
    srv_pool: Optional[SRVPool] = None
    ttl: Optional[int] = None
    use_rrset_ttl: Optional[Any] = None


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
    """Get DNS Load Balancer Pool details."""

    a_pool: Optional[APool] = None
    aaaa_pool: Optional[AAAAPool] = None
    cname_pool: Optional[CNAMEPool] = None
    dns_load_balancers: Optional[list[ObjectRefType]] = None
    load_balancing_mode: Optional[Literal['ROUND_ROBIN', 'RATIO_MEMBER', 'STATIC_PERSIST', 'PRIORITY']] = None
    mx_pool: Optional[MXPool] = None
    srv_pool: Optional[SRVPool] = None
    ttl: Optional[int] = None
    use_rrset_ttl: Optional[Any] = None


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
    """Replace DNS Load Balancer Pool in a given namespace."""

    a_pool: Optional[APool] = None
    aaaa_pool: Optional[AAAAPool] = None
    cname_pool: Optional[CNAMEPool] = None
    load_balancing_mode: Optional[Literal['ROUND_ROBIN', 'RATIO_MEMBER', 'STATIC_PERSIST', 'PRIORITY']] = None
    mx_pool: Optional[MXPool] = None
    srv_pool: Optional[SRVPool] = None
    ttl: Optional[int] = None
    use_rrset_ttl: Optional[Any] = None


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
    """By default a summary of dns_lb_pool is returned in 'List'. By setting..."""

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
