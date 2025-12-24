"""Pydantic models for user_group."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class UserGroupListItem(F5XCBaseModel):
    """List item for user_group resources."""


class UserGroupListItem(F5XCBaseModel):
    """List item for user_group resources."""


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


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


class NamespaceRoleType(F5XCBaseModel):
    """Allows linking namespaces and roles"""

    namespace: Optional[str] = None
    role: Optional[str] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


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


class Empty(F5XCBaseModel):
    """Data for empty response."""

    pass


class NamespaceNameIdentifier(F5XCBaseModel):
    """NamespaceNameIdentifier holds the name and namespace of the specific object"""

    object_name: Optional[str] = None
    object_namespace: Optional[str] = None


class AnalyzeForDeletionRequest(F5XCBaseModel):
    """Analyze For Deletion Request.  AnalyzeForDeletionRequest is for the..."""

    namespace_name_identifier: Optional[NamespaceNameIdentifier] = None
    object_uid: Optional[str] = None


class AnalyzeForDeletionResponse(F5XCBaseModel):
    """Response holds the references of the object and also talks about the..."""

    back_referencing_items: Optional[dict[str, Any]] = None
    deletion_analysis: Optional[Literal['Unknown', 'Deletable', 'Internal', 'ReferencesAutoRemovable', 'ReferencesRemovable', 'ReferencesNonRemovable']] = None
    referenced_items: Optional[dict[str, Any]] = None


class GetSpecType(F5XCBaseModel):
    display_name: Optional[str] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    spec: Optional[GetSpecType] = None
    status: Optional[list[StatusObject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of user_group is returned in 'List'. By setting..."""

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


class Response(F5XCBaseModel):
    """Response which return the created user group with the list of the users."""

    description: Optional[str] = None
    display_name: Optional[str] = None
    error: Optional[ErrorType] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None
    namespace_roles: Optional[list[NamespaceRoleType]] = None
    references_count: Optional[dict[str, Any]] = None
    sync_id: Optional[str] = None
    sync_mode: Optional[Literal['SELF', 'SCIM']] = None
    uid: Optional[str] = None
    usernames: Optional[list[str]] = None


class ListUserGroupsResponse(F5XCBaseModel):
    """Response for receiving all existing group created for the tenant."""

    user_groups: Optional[list[Response]] = None


# Convenience aliases
Spec = GetSpecType
