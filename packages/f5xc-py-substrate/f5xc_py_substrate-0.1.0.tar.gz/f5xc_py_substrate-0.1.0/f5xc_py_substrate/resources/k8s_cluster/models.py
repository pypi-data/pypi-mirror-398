"""Pydantic models for k8s_cluster."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class K8sClusterListItem(F5XCBaseModel):
    """List item for k8s_cluster resources."""


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


class K8sClusterlocalaccessargocdtype(F5XCBaseModel):
    """Parameters required to enable local access"""

    default_port: Optional[Any] = None
    local_domain: Optional[str] = None
    password: Optional[SecretType] = None
    port: Optional[int] = None


class K8sClusterapplicationargocdtype(F5XCBaseModel):
    """description Parameters for Argo Continuous Deployment(CD) application"""

    local_domain: Optional[K8sClusterlocalaccessargocdtype] = None


class K8sClusterapplicationdashboardtype(F5XCBaseModel):
    """description Parameters for K8s dashboard"""

    pass


class K8sClusterapplicationmetricsservertype(F5XCBaseModel):
    """description Parameters for Kubernetes Metrics Server application"""

    pass


class K8sClusterapplicationprometheustype(F5XCBaseModel):
    """description Parameters for Prometheus server access"""

    pass


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class K8sClusterclusterrolebindinglisttype(F5XCBaseModel):
    """List of active cluster role binding list for a K8s cluster"""

    cluster_role_bindings: Optional[list[ObjectRefType]] = None


class K8sClusterclusterrolelisttype(F5XCBaseModel):
    """List of active cluster role list for a K8s cluster"""

    cluster_roles: Optional[list[ObjectRefType]] = None


class K8sClusterclusterwideapptype(F5XCBaseModel):
    """Cluster wide application configuration"""

    argo_cd: Optional[K8sClusterapplicationargocdtype] = None
    dashboard: Optional[Any] = None
    metrics_server: Optional[Any] = None
    prometheus: Optional[Any] = None


class K8sClusterclusterwideapplisttype(F5XCBaseModel):
    """List of cluster wide applications"""

    cluster_wide_apps: Optional[list[K8sClusterclusterwideapptype]] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class K8sClusterinsecureregistrylisttype(F5XCBaseModel):
    """List of docker insecure registries"""

    insecure_registries: Optional[list[str]] = None


class K8sClusterlocalaccessconfigtype(F5XCBaseModel):
    """Parameters required to enable local access"""

    default_port: Optional[Any] = None
    local_domain: Optional[str] = None
    port: Optional[int] = None


class K8sClusterpodsecuritypolicylisttype(F5XCBaseModel):
    """List of active Pod security policies for a K8s cluster"""

    pod_security_policies: Optional[list[ObjectRefType]] = None


class K8sClustercreatespectype(F5XCBaseModel):
    """Create k8s_cluster will create the object in the storage backend for..."""

    cluster_scoped_access_deny: Optional[Any] = None
    cluster_scoped_access_permit: Optional[Any] = None
    cluster_wide_app_list: Optional[K8sClusterclusterwideapplisttype] = None
    global_access_enable: Optional[Any] = None
    insecure_registry_list: Optional[K8sClusterinsecureregistrylisttype] = None
    local_access_config: Optional[K8sClusterlocalaccessconfigtype] = None
    no_cluster_wide_apps: Optional[Any] = None
    no_global_access: Optional[Any] = None
    no_insecure_registries: Optional[Any] = None
    no_local_access: Optional[Any] = None
    use_custom_cluster_role_bindings: Optional[K8sClusterclusterrolebindinglisttype] = None
    use_custom_cluster_role_list: Optional[K8sClusterclusterrolelisttype] = None
    use_custom_pod_security_admission: Optional[ObjectRefType] = None
    use_custom_psp_list: Optional[K8sClusterpodsecuritypolicylisttype] = None
    use_default_cluster_role_bindings: Optional[Any] = None
    use_default_cluster_roles: Optional[Any] = None
    use_default_pod_security_admission: Optional[Any] = None
    use_default_psp: Optional[Any] = None
    vk8s_namespace_access_deny: Optional[Any] = None
    vk8s_namespace_access_permit: Optional[Any] = None


class K8sClustercreaterequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[K8sClustercreatespectype] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class K8sClustergetspectype(F5XCBaseModel):
    """Get k8s_cluster will get the object from the storage backend for..."""

    cluster_scoped_access_deny: Optional[Any] = None
    cluster_scoped_access_permit: Optional[Any] = None
    cluster_wide_app_list: Optional[K8sClusterclusterwideapplisttype] = None
    global_access_enable: Optional[Any] = None
    insecure_registry_list: Optional[K8sClusterinsecureregistrylisttype] = None
    local_access_config: Optional[K8sClusterlocalaccessconfigtype] = None
    no_cluster_wide_apps: Optional[Any] = None
    no_global_access: Optional[Any] = None
    no_insecure_registries: Optional[Any] = None
    no_local_access: Optional[Any] = None
    use_custom_cluster_role_bindings: Optional[K8sClusterclusterrolebindinglisttype] = None
    use_custom_cluster_role_list: Optional[K8sClusterclusterrolelisttype] = None
    use_custom_pod_security_admission: Optional[ObjectRefType] = None
    use_custom_psp_list: Optional[K8sClusterpodsecuritypolicylisttype] = None
    use_default_cluster_role_bindings: Optional[Any] = None
    use_default_cluster_roles: Optional[Any] = None
    use_default_pod_security_admission: Optional[Any] = None
    use_default_psp: Optional[Any] = None
    vk8s_namespace_access_deny: Optional[Any] = None
    vk8s_namespace_access_permit: Optional[Any] = None


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


class K8sClustercreateresponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[K8sClustergetspectype] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class K8sClusterdeleterequest(F5XCBaseModel):
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


class K8sClusterreplacespectype(F5XCBaseModel):
    """Replacing an k8s_cluster object will update the object by replacing the..."""

    cluster_scoped_access_deny: Optional[Any] = None
    cluster_scoped_access_permit: Optional[Any] = None
    cluster_wide_app_list: Optional[K8sClusterclusterwideapplisttype] = None
    global_access_enable: Optional[Any] = None
    insecure_registry_list: Optional[K8sClusterinsecureregistrylisttype] = None
    local_access_config: Optional[K8sClusterlocalaccessconfigtype] = None
    no_cluster_wide_apps: Optional[Any] = None
    no_global_access: Optional[Any] = None
    no_insecure_registries: Optional[Any] = None
    no_local_access: Optional[Any] = None
    use_custom_cluster_role_bindings: Optional[K8sClusterclusterrolebindinglisttype] = None
    use_custom_cluster_role_list: Optional[K8sClusterclusterrolelisttype] = None
    use_custom_pod_security_admission: Optional[ObjectRefType] = None
    use_custom_psp_list: Optional[K8sClusterpodsecuritypolicylisttype] = None
    use_default_cluster_role_bindings: Optional[Any] = None
    use_default_cluster_roles: Optional[Any] = None
    use_default_pod_security_admission: Optional[Any] = None
    use_default_psp: Optional[Any] = None
    vk8s_namespace_access_deny: Optional[Any] = None
    vk8s_namespace_access_permit: Optional[Any] = None


class K8sClusterreplacerequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[K8sClusterreplacespectype] = None


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


class K8sClusterstatusobject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


class K8sClustergetresponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[K8sClustercreaterequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[K8sClusterreplacerequest] = None
    spec: Optional[K8sClustergetspectype] = None
    status: Optional[list[K8sClusterstatusobject]] = None
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


class K8sClusterlistresponseitem(F5XCBaseModel):
    """By default a summary of k8s_cluster is returned in 'List'. By setting..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[K8sClustergetspectype] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[K8sClusterstatusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class K8sClusterlistresponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[K8sClusterlistresponseitem]] = None


class K8sClusterreplaceresponse(F5XCBaseModel):
    pass


# Convenience aliases
