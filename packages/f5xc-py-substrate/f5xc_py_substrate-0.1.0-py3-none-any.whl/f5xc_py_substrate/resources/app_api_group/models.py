"""Pydantic models for app_api_group."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AppApiGroupListItem(F5XCBaseModel):
    """List item for app_api_group resources."""


class ApiEndpoint(F5XCBaseModel):
    """The API Endpoint according to OpenAPI specification."""

    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    path: Optional[str] = None


class ApiGroupId(F5XCBaseModel):
    """The API Group ID for the API Groups stats response"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class ApiGroupScopeBIGIPVirtualServer(F5XCBaseModel):
    """Set the scope of the API Group to a specific BIGIP Virtual Server"""

    bigip_virtual_server: Optional[ObjectRefType] = None


class ApiGroupScopeCDNLoadbalancer(F5XCBaseModel):
    """Set the scope of the API Group to a specific CDN Loadbalancer"""

    cdn_loadbalancer: Optional[ObjectRefType] = None


class ApiGroupScopeHttpLoadbalancer(F5XCBaseModel):
    """Set the scope of the API Group to a specific HTTP Loadbalancer"""

    http_loadbalancer: Optional[ObjectRefType] = None


class ApiGroupStats(F5XCBaseModel):
    """The API Group Stats for the API Groups stats response"""

    outdated_api_endpoints_count: Optional[int] = None


class ApiGroupsStatsItem(F5XCBaseModel):
    """API Groups Stats Item"""

    id_: Optional[ApiGroupId] = Field(default=None, alias="id")
    stats: Optional[ApiGroupStats] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    """Shape of api_group_element in the storage backend."""

    methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None
    path_regex: Optional[str] = None


class CreateSpecType(F5XCBaseModel):
    """Create app_api_group creates a new object in the storage backend for..."""

    bigip_virtual_server: Optional[ApiGroupScopeBIGIPVirtualServer] = None
    cdn_loadbalancer: Optional[ApiGroupScopeCDNLoadbalancer] = None
    elements: Optional[list[GlobalSpecType]] = None
    http_loadbalancer: Optional[ApiGroupScopeHttpLoadbalancer] = None


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
    """Get app_api_group reads a given object from storage backend for..."""

    api_endpoints_count: Optional[int] = None
    bigip_virtual_server: Optional[ApiGroupScopeBIGIPVirtualServer] = None
    cdn_loadbalancer: Optional[ApiGroupScopeCDNLoadbalancer] = None
    elements: Optional[list[GlobalSpecType]] = None
    http_loadbalancer: Optional[ApiGroupScopeHttpLoadbalancer] = None


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


class GlobalSpecType(F5XCBaseModel):
    """Shape of app_api_group in the storage backend."""

    api_endpoints_count: Optional[int] = None
    bigip_virtual_server: Optional[ApiGroupScopeBIGIPVirtualServer] = None
    cdn_loadbalancer: Optional[ApiGroupScopeCDNLoadbalancer] = None
    elements: Optional[list[GlobalSpecType]] = None
    http_loadbalancer: Optional[ApiGroupScopeHttpLoadbalancer] = None


class EvaluateApiGroupReq(F5XCBaseModel):
    """Request shape for Evaluate API Group"""

    api_group: Optional[GlobalSpecType] = None
    namespace: Optional[str] = None


class EvaluateApiGroupRsp(F5XCBaseModel):
    """Response for the Evaluate API Group request"""

    api_group: Optional[GlobalSpecType] = None
    apieps_timestamp: Optional[str] = None
    matching_api_endpoints: Optional[list[ApiEndpoint]] = None


class GetApiGroupsStatsReq(F5XCBaseModel):
    """Request shape for API Groups Stats"""

    namespace: Optional[str] = None


class GetApiGroupsStatsRsp(F5XCBaseModel):
    """Response for the API Groups Stats request"""

    items: Optional[list[ApiGroupsStatsItem]] = None


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
    """Replace app_api_group replaces an existing object in the storage backend..."""

    bigip_virtual_server: Optional[ApiGroupScopeBIGIPVirtualServer] = None
    cdn_loadbalancer: Optional[ApiGroupScopeCDNLoadbalancer] = None
    elements: Optional[list[GlobalSpecType]] = None
    http_loadbalancer: Optional[ApiGroupScopeHttpLoadbalancer] = None


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
    """By default a summary of app_api_group is returned in 'List'. By setting..."""

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
Spec = GlobalSpecType
Spec = CreateSpecType
Spec = GetSpecType
Spec = GlobalSpecType
Spec = ReplaceSpecType
