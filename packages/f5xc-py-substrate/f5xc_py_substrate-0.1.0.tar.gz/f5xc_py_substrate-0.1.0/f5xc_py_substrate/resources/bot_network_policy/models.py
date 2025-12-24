"""Pydantic models for bot_network_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class BotNetworkPolicyListItem(F5XCBaseModel):
    """List item for bot_network_policy resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ManualRoutingDetail(F5XCBaseModel):
    """Manual Routing value"""

    domain_name: Optional[str] = None
    http: Optional[Any] = None
    https: Optional[Any] = None
    outbound_domain_name: Optional[str] = None
    port: Optional[int] = None
    protocol_http: Optional[Any] = None
    protocol_https: Optional[Any] = None


class ManualRoutings(F5XCBaseModel):
    """The list of manual routing"""

    manual_routing: Optional[list[ManualRoutingDetail]] = None


class UpstreamRoutingDetail(F5XCBaseModel):
    """Upstream Routing value"""

    domain_name: Optional[str] = None


class UpstreamRoutings(F5XCBaseModel):
    """Upstream DNS Routings"""

    upstream_routing: Optional[list[UpstreamRoutingDetail]] = None


class NetworkPolicyContent(F5XCBaseModel):
    """Network Policy Content"""

    manual_routing_list: Optional[ManualRoutings] = None
    upstream_routing_list: Optional[UpstreamRoutings] = None


class PolicyVersion(F5XCBaseModel):
    """Policy version"""

    bot_infras_name: Optional[list[str]] = None
    update_time: Optional[str] = None
    update_user: Optional[str] = None
    version_number: Optional[str] = None
    version_status: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace Bot network Policy"""

    network_policy_content: Optional[NetworkPolicyContent] = None


class CustomReplaceRequest(F5XCBaseModel):
    name: Optional[str] = None
    namespace: Optional[str] = None
    spec: Optional[ReplaceSpecType] = None


class CustomReplaceResponse(F5XCBaseModel):
    pass


class GetContentResponse(F5XCBaseModel):
    network_policy_content: Optional[NetworkPolicyContent] = None


class Policy(F5XCBaseModel):
    """Policy name and versions"""

    policy_name: Optional[str] = None
    policy_versions: Optional[list[PolicyVersion]] = None


class GetPoliciesAndVersionsListResponse(F5XCBaseModel):
    """List All Bot Policies And Versions Response"""

    policies: Optional[list[Policy]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
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


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class GetSpecType(F5XCBaseModel):
    """Get Bot network Policy"""

    latest_version: Optional[str] = None
    network_policy_content: Optional[NetworkPolicyContent] = None


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


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

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
    """By default a summary of bot_network_policy is returned in 'List'. By..."""

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


class PolicyVersionsResponse(F5XCBaseModel):
    """Policy versions response"""

    policy_versions: Optional[list[PolicyVersion]] = None


class ReplaceResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = ReplaceSpecType
Spec = GetSpecType
