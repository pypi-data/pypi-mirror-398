"""Pydantic models for k8s_cluster_role."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class K8sClusterRoleListItem(F5XCBaseModel):
    """List item for k8s_cluster_role resources."""


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class LabelSelectorType(F5XCBaseModel):
    """This type can be used to establish a 'selector reference' from one..."""

    expressions: Optional[list[str]] = None


class K8sClusterRolenonresourceurllisttype(F5XCBaseModel):
    """permissions for URL(s) that do not represent K8s resource"""

    urls: Optional[list[str]] = None
    verbs: Optional[list[str]] = None


class K8sClusterRoleresourcelisttype(F5XCBaseModel):
    """List of resources in terms of api groups/resource types/resource..."""

    api_groups: Optional[list[str]] = None
    resource_instances: Optional[list[str]] = None
    resource_types: Optional[list[str]] = None
    verbs: Optional[list[str]] = None


class K8sClusterRolepolicyruletype(F5XCBaseModel):
    """Rule for role permission"""

    non_resource_url_list: Optional[K8sClusterRolenonresourceurllisttype] = None
    resource_list: Optional[K8sClusterRoleresourcelisttype] = None


class K8sClusterRolepolicyrulelisttype(F5XCBaseModel):
    """List of rules for role permissions"""

    policy_rule: Optional[list[K8sClusterRolepolicyruletype]] = None


class K8sClusterRolecreatespectype(F5XCBaseModel):
    """Create k8s_cluster_role will create the object in the storage backend..."""

    k8s_cluster_role_selector: Optional[LabelSelectorType] = None
    policy_rule_list: Optional[K8sClusterRolepolicyrulelisttype] = None
    yaml: Optional[str] = None


class K8sClusterRolecreaterequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[K8sClusterRolecreatespectype] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class K8sClusterRolegetspectype(F5XCBaseModel):
    """Get k8s_cluster_role will get the object from the storage backend for..."""

    k8s_cluster_role_selector: Optional[LabelSelectorType] = None
    policy_rule_list: Optional[K8sClusterRolepolicyrulelisttype] = None
    yaml: Optional[str] = None


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


class K8sClusterRolecreateresponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[K8sClusterRolegetspectype] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class K8sClusterRoledeleterequest(F5XCBaseModel):
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


class K8sClusterRolereplacespectype(F5XCBaseModel):
    """Replacing an k8s_cluster_role object will update the object by replacing..."""

    k8s_cluster_role_selector: Optional[LabelSelectorType] = None
    policy_rule_list: Optional[K8sClusterRolepolicyrulelisttype] = None
    yaml: Optional[str] = None


class K8sClusterRolereplacerequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[K8sClusterRolereplacespectype] = None


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


class K8sClusterRolestatusobject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


class K8sClusterRolegetresponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[K8sClusterRolecreaterequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[K8sClusterRolereplacerequest] = None
    spec: Optional[K8sClusterRolegetspectype] = None
    status: Optional[list[K8sClusterRolestatusobject]] = None
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


class K8sClusterRolelistresponseitem(F5XCBaseModel):
    """By default a summary of k8s_cluster_role is returned in 'List'. By..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[K8sClusterRolegetspectype] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[K8sClusterRolestatusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class K8sClusterRolelistresponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[K8sClusterRolelistresponseitem]] = None


class K8sClusterRolereplaceresponse(F5XCBaseModel):
    pass


# Convenience aliases
