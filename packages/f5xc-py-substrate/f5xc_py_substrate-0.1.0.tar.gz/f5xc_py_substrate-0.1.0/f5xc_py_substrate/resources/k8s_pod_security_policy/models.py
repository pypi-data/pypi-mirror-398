"""Pydantic models for k8s_pod_security_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class K8sPodSecurityPolicyListItem(F5XCBaseModel):
    """List item for k8s_pod_security_policy resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class K8sPodSecurityPolicycapabilitylisttype(F5XCBaseModel):
    """List of capabilities that docker container has."""

    capabilities: Optional[list[str]] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class K8sPodSecurityPolicyhostpathtype(F5XCBaseModel):
    """Host path and read/write or read-only"""

    path_prefix: Optional[str] = None
    read_only: Optional[bool] = None


class K8sPodSecurityPolicyidrangetype(F5XCBaseModel):
    max_id: Optional[int] = None
    min_id: Optional[int] = None


class K8sPodSecurityPolicyidstrategyoptionstype(F5XCBaseModel):
    """ID ranges and rules"""

    id_ranges: Optional[list[K8sPodSecurityPolicyidrangetype]] = None
    rule: Optional[str] = None


class K8sPodSecurityPolicypodsecuritypolicyspectype(F5XCBaseModel):
    """Form based pod security specification"""

    allow_privilege_escalation: Optional[bool] = None
    allowed_capabilities: Optional[K8sPodSecurityPolicycapabilitylisttype] = None
    allowed_csi_drivers: Optional[list[str]] = None
    allowed_flex_volumes: Optional[list[str]] = None
    allowed_host_paths: Optional[list[K8sPodSecurityPolicyhostpathtype]] = None
    allowed_proc_mounts: Optional[list[str]] = None
    allowed_unsafe_sysctls: Optional[list[str]] = None
    default_allow_privilege_escalation: Optional[bool] = None
    default_capabilities: Optional[K8sPodSecurityPolicycapabilitylisttype] = None
    drop_capabilities: Optional[K8sPodSecurityPolicycapabilitylisttype] = None
    forbidden_sysctls: Optional[list[str]] = None
    fs_group_strategy_options: Optional[K8sPodSecurityPolicyidstrategyoptionstype] = None
    host_ipc: Optional[bool] = None
    host_network: Optional[bool] = None
    host_pid: Optional[bool] = None
    host_port_ranges: Optional[str] = None
    no_allowed_capabilities: Optional[Any] = None
    no_default_capabilities: Optional[Any] = None
    no_drop_capabilities: Optional[Any] = None
    no_fs_groups: Optional[Any] = None
    no_run_as_group: Optional[Any] = None
    no_run_as_user: Optional[Any] = None
    no_runtime_class: Optional[Any] = None
    no_se_linux_options: Optional[Any] = None
    no_supplemental_groups: Optional[Any] = None
    privileged: Optional[bool] = None
    read_only_root_filesystem: Optional[bool] = None
    run_as_group: Optional[K8sPodSecurityPolicyidstrategyoptionstype] = None
    run_as_user: Optional[K8sPodSecurityPolicyidstrategyoptionstype] = None
    supplemental_groups: Optional[K8sPodSecurityPolicyidstrategyoptionstype] = None
    volumes: Optional[list[str]] = None


class K8sPodSecurityPolicycreatespectype(F5XCBaseModel):
    """Create k8s_pod_security_policy will create the object in the storage..."""

    psp_spec: Optional[K8sPodSecurityPolicypodsecuritypolicyspectype] = None
    yaml: Optional[str] = None


class K8sPodSecurityPolicycreaterequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[K8sPodSecurityPolicycreatespectype] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class K8sPodSecurityPolicygetspectype(F5XCBaseModel):
    """Get k8s_pod_security_policy will get the object from the storage backend..."""

    psp_spec: Optional[K8sPodSecurityPolicypodsecuritypolicyspectype] = None
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


class K8sPodSecurityPolicycreateresponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[K8sPodSecurityPolicygetspectype] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class K8sPodSecurityPolicydeleterequest(F5XCBaseModel):
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


class K8sPodSecurityPolicyreplacespectype(F5XCBaseModel):
    """Replacing an k8s_pod_security_policy object will update the object by..."""

    psp_spec: Optional[K8sPodSecurityPolicypodsecuritypolicyspectype] = None
    yaml: Optional[str] = None


class K8sPodSecurityPolicyreplacerequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[K8sPodSecurityPolicyreplacespectype] = None


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


class K8sPodSecurityPolicystatusobject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


class K8sPodSecurityPolicygetresponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[K8sPodSecurityPolicycreaterequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[K8sPodSecurityPolicyreplacerequest] = None
    spec: Optional[K8sPodSecurityPolicygetspectype] = None
    status: Optional[list[K8sPodSecurityPolicystatusobject]] = None
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


class K8sPodSecurityPolicylistresponseitem(F5XCBaseModel):
    """By default a summary of k8s_pod_security_policy is returned in 'List'...."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[K8sPodSecurityPolicygetspectype] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[K8sPodSecurityPolicystatusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class K8sPodSecurityPolicylistresponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[K8sPodSecurityPolicylistresponseitem]] = None


class K8sPodSecurityPolicyreplaceresponse(F5XCBaseModel):
    pass


# Convenience aliases
