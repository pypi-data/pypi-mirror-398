"""Pydantic models for api_credential."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ApiCredentialListItem(F5XCBaseModel):
    """List item for api_credential resources."""


class ApiCertificateType(F5XCBaseModel):
    """Service API Certificate parameters"""

    password: Optional[str] = None


class BulkRevokeResponse(F5XCBaseModel):
    """response format for revoking multiple api credentials."""

    credentials_failed: Optional[list[str]] = None
    credentials_marked_for_deletion: Optional[list[str]] = None
    error_message: Optional[str] = None


class CustomCreateSpecType(F5XCBaseModel):
    """Create request specification."""

    password: Optional[str] = None
    type_: Optional[Literal['API_CERTIFICATE', 'KUBE_CONFIG', 'API_TOKEN', 'SERVICE_API_TOKEN', 'SERVICE_API_CERTIFICATE', 'SERVICE_KUBE_CONFIG', 'SITE_GLOBAL_KUBE_CONFIG', 'SCIM_API_TOKEN', 'SERVICE_SITE_GLOBAL_KUBE_CONFIG']] = Field(default=None, alias="type")
    virtual_k8s_name: Optional[str] = None
    virtual_k8s_namespace: Optional[str] = None


class CreateRequest(F5XCBaseModel):
    """CreateRequest is the request format for generating api credential."""

    expiration_days: Optional[int] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    spec: Optional[CustomCreateSpecType] = None


class CreateResponse(F5XCBaseModel):
    """CreateResponse is the response format for the credential's create request."""

    active: Optional[bool] = None
    data: Optional[str] = None
    expiration_timestamp: Optional[str] = None
    name: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class NamespaceRoleType(F5XCBaseModel):
    """Allows linking namespaces and roles"""

    namespace: Optional[str] = None
    role: Optional[str] = None


class SiteKubeconfigType(F5XCBaseModel):
    """Site Global Kube Config parameters"""

    site: Optional[str] = None


class Vk8sKubeconfigType(F5XCBaseModel):
    """Service Kube Config parameters"""

    vk8s_cluster_name: Optional[str] = None
    vk8s_namespace: Optional[str] = None


class CreateServiceCredentialsRequest(F5XCBaseModel):
    """CreateServiceCredentialsRequest is the request format for creating..."""

    api_certificate: Optional[ApiCertificateType] = None
    api_token: Optional[Any] = None
    expiration_days: Optional[int] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    namespace_roles: Optional[list[NamespaceRoleType]] = None
    password: Optional[str] = None
    site_kubeconfig: Optional[SiteKubeconfigType] = None
    type_: Optional[Literal['API_CERTIFICATE', 'KUBE_CONFIG', 'API_TOKEN', 'SERVICE_API_TOKEN', 'SERVICE_API_CERTIFICATE', 'SERVICE_KUBE_CONFIG', 'SITE_GLOBAL_KUBE_CONFIG', 'SCIM_API_TOKEN', 'SERVICE_SITE_GLOBAL_KUBE_CONFIG']] = Field(default=None, alias="type")
    user_group_names: Optional[list[str]] = None
    virtual_k8s_name: Optional[str] = None
    virtual_k8s_namespace: Optional[str] = None
    vk8s_kubeconfig: Optional[Vk8sKubeconfigType] = None


class ObjectMetaType(F5XCBaseModel):
    """ObjectMetaType is metadata(common attributes) of an object that all..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    """Keeps track of user requested API credentials"""

    active: Optional[bool] = None
    certificate_serial_num: Optional[str] = None
    created_timestamp: Optional[str] = None
    digest: Optional[str] = None
    expiration_timestamp: Optional[str] = None
    site_name: Optional[str] = None
    type_: Optional[Literal['API_CERTIFICATE', 'KUBE_CONFIG', 'API_TOKEN', 'SERVICE_API_TOKEN', 'SERVICE_API_CERTIFICATE', 'SERVICE_KUBE_CONFIG', 'SITE_GLOBAL_KUBE_CONFIG', 'SCIM_API_TOKEN', 'SERVICE_SITE_GLOBAL_KUBE_CONFIG']] = Field(default=None, alias="type")
    users: Optional[list[ObjectRefType]] = None
    virtual_k8s_name: Optional[str] = None
    virtual_k8s_namespace: Optional[str] = None


class SpecType(F5XCBaseModel):
    """Shape of the api credential specification"""

    gc_spec: Optional[GlobalSpecType] = None


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


class SystemObjectMetaType(F5XCBaseModel):
    """SystemObjectMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_cookie: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    direct_ref_hash: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    namespace: Optional[list[ObjectRefType]] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    revision: Optional[str] = None
    sre_disable: Optional[bool] = None
    tenant: Optional[str] = None
    trace_info: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class Object(F5XCBaseModel):
    """API Credential object represents the user request to create a certificate."""

    metadata: Optional[ObjectMetaType] = None
    spec: Optional[SpecType] = None
    system_metadata: Optional[SystemObjectMetaType] = None


class GetResponse(F5XCBaseModel):
    """Response of get credential request with a given name."""

    object_: Optional[Object] = Field(default=None, alias="object")


class NamespaceAccessType(F5XCBaseModel):
    """Access info in the namespaces for the entity"""

    namespace_role_map: Optional[dict[str, Any]] = None


class GetServiceCredentialsResponse(F5XCBaseModel):
    """Response of get service credentials request with a given name."""

    active: Optional[bool] = None
    create_timestamp: Optional[str] = None
    expiry_timestamp: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    namespace_access: Optional[NamespaceAccessType] = None
    type_: Optional[Literal['API_CERTIFICATE', 'KUBE_CONFIG', 'API_TOKEN', 'SERVICE_API_TOKEN', 'SERVICE_API_CERTIFICATE', 'SERVICE_KUBE_CONFIG', 'SITE_GLOBAL_KUBE_CONFIG', 'SCIM_API_TOKEN', 'SERVICE_SITE_GLOBAL_KUBE_CONFIG']] = Field(default=None, alias="type")
    uid: Optional[str] = None
    user_email: Optional[str] = None
    user_group_names: Optional[list[str]] = None


class ListResponseItem(F5XCBaseModel):
    """Each item of credential list request."""

    active: Optional[bool] = None
    create_timestamp: Optional[str] = None
    expiry_timestamp: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    type_: Optional[Literal['API_CERTIFICATE', 'KUBE_CONFIG', 'API_TOKEN', 'SERVICE_API_TOKEN', 'SERVICE_API_CERTIFICATE', 'SERVICE_KUBE_CONFIG', 'SITE_GLOBAL_KUBE_CONFIG', 'SCIM_API_TOKEN', 'SERVICE_SITE_GLOBAL_KUBE_CONFIG']] = Field(default=None, alias="type")
    uid: Optional[str] = None
    user_email: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """Response of request to list all of users credential objects."""

    items: Optional[list[ListResponseItem]] = None


class ListServiceCredentialsResponseItem(F5XCBaseModel):
    """Each item of service credential list request."""

    active: Optional[bool] = None
    create_timestamp: Optional[str] = None
    expiry_timestamp: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    namespace_access: Optional[NamespaceAccessType] = None
    type_: Optional[Literal['API_CERTIFICATE', 'KUBE_CONFIG', 'API_TOKEN', 'SERVICE_API_TOKEN', 'SERVICE_API_CERTIFICATE', 'SERVICE_KUBE_CONFIG', 'SITE_GLOBAL_KUBE_CONFIG', 'SCIM_API_TOKEN', 'SERVICE_SITE_GLOBAL_KUBE_CONFIG']] = Field(default=None, alias="type")
    uid: Optional[str] = None
    user_email: Optional[str] = None
    user_group_names: Optional[list[str]] = None


class ListServiceCredentialsResponse(F5XCBaseModel):
    """Response of request to list all of service credential objects."""

    items: Optional[list[ListServiceCredentialsResponseItem]] = None


class RecreateScimTokenRequest(F5XCBaseModel):
    """RecreateScimTokenRequest is the request format for generating SCIM api..."""

    expiration_days: Optional[int] = None
    namespace: Optional[str] = None


class ReplaceServiceCredentialsRequest(F5XCBaseModel):
    """request format for replacing service credentials."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    namespace_access: Optional[NamespaceAccessType] = None
    user_group_names: Optional[list[str]] = None


class ReplaceServiceCredentialsResponse(F5XCBaseModel):
    """response format for the credential's replace request."""

    active: Optional[bool] = None
    expiration_timestamp: Optional[str] = None
    name: Optional[str] = None


class ScimTokenRequest(F5XCBaseModel):
    """ScimTokenRequest is used for fetching or revoking scim token"""

    namespace: Optional[str] = None


class StatusResponse(F5XCBaseModel):
    """API credential status response"""

    status: Optional[bool] = None


# Convenience aliases
Spec = CustomCreateSpecType
Spec = GlobalSpecType
Spec = SpecType
