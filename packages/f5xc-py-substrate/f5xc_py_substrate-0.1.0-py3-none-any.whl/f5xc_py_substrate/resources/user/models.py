"""Pydantic models for user."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class UserListItem(F5XCBaseModel):
    """List item for user resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


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


class NamespaceAccessType(F5XCBaseModel):
    """Access info in the namespaces for the entity"""

    namespace_role_map: Optional[dict[str, Any]] = None


class NamespaceRoleType(F5XCBaseModel):
    """Allows linking namespaces and roles"""

    namespace: Optional[str] = None
    role: Optional[str] = None


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


class Empty(F5XCBaseModel):
    """Empty is a message without actual content/body."""

    pass


class AcceptTOSRequest(F5XCBaseModel):
    """Accept TOS request model"""

    namespace: Optional[str] = None
    tos_accepted: Optional[str] = None
    tos_accepted_at: Optional[str] = None
    tos_version: Optional[str] = None


class AcceptTOSResponse(F5XCBaseModel):
    """Accept TOS response model"""

    pass


class NamespacesRoleType(F5XCBaseModel):
    """Association of a role to namespaces"""

    namespaces: Optional[list[str]] = None
    role: Optional[str] = None


class AssignRoleRequest(F5XCBaseModel):
    """Allows assigning user's role in a namespace or set of namespaces."""

    namespace: Optional[str] = None
    namespaces_role: Optional[NamespacesRoleType] = None
    username: Optional[list[str]] = None


class BillingFeatureIndicator(F5XCBaseModel):
    """Single instance of a billing indicator. It informs the customer of any..."""

    action: Optional[Literal['NO_ACTION', 'ADD_NEW_PAYMENT_METHOD', 'CONTACT_US']] = None
    additional_info: Optional[str] = None
    billing_flag: Optional[Literal['VALID_PAYMENT_METHOD', 'OVERDUE_INVOICE', 'LAST_TRANSACTION_STATUS', 'PAYMENT_METHOD_EXPIRED', 'PAYMENT_METHOD_INSUFFICIENT_FUNDS', 'PAYMENT_METHOD_PRIMARY_DECLINED', 'PAYMENT_METHOD_CVC_INVALID', 'PAYMENT_METHOD_ZIP_INVALID', 'PAYMENT_METHOD_INSUFFICIENT_FUNDS_SECONDARY_CHARGED', 'PAYMENT_METHOD_PRIMARY_EXPIRED_SECONDARY_CHARGED', 'PAYMENT_METHOD_PRIMARY_DECLINED_SECONDARY_CHARGED', 'PAYMENT_METHOD_BOTH_PAYMENT_METHOD_FAILED', 'PAYMENT_METHOD_GENERIC_FAILURE', 'PAYMENT_METHOD_GENERIC_ADD_FAILURE']] = None
    failed: Optional[bool] = None


class CascadeDeleteItemType(F5XCBaseModel):
    """CascadeDeleteItemType contains details of object that was handled as..."""

    error_message: Optional[str] = None
    object_name: Optional[str] = None
    object_type: Optional[str] = None
    object_uid: Optional[str] = None


class CascadeDeleteRequest(F5XCBaseModel):
    """CascadeDeleteRequest is the request to delete the user along with the..."""

    email: Optional[str] = None
    namespace: Optional[str] = None


class CascadeDeleteResponse(F5XCBaseModel):
    """CascadeDeleteResponse contains a list of user objects that were deleted..."""

    delete_ok: Optional[bool] = None
    items: Optional[list[CascadeDeleteItemType]] = None


class FeatureFlagType(F5XCBaseModel):
    disabled: Optional[bool] = None
    name: Optional[str] = None


class GetTOSResponse(F5XCBaseModel):
    """Get TOS response model"""

    text: Optional[str] = None
    version: Optional[str] = None


class MSPManaged(F5XCBaseModel):
    """MSP information for tenant."""

    msp_id: Optional[str] = None
    node_type: Optional[Literal['MspNodeTypeUnknown', 'MspNodeTypeChild', 'MspNodeTypeParent']] = None
    parent_tenant_id: Optional[str] = None
    tier: Optional[int] = None


class GetUserRoleResponse(F5XCBaseModel):
    """Detailed information about user including role assigments and other..."""

    access_type: Optional[Literal['UNKNOWN_ACCESS', 'DIRECT_ACCESS', 'MSP_ACCESS', 'DELEGATED_ACCESS', 'SUPPORT_ACCESS']] = None
    active_plan_transition_uid: Optional[str] = None
    addon_service_status: Optional[dict[str, Any]] = None
    billing_flags: Optional[list[BillingFeatureIndicator]] = None
    billing_plan_name: Optional[str] = None
    cname: Optional[str] = None
    company: Optional[str] = None
    creation_timestamp: Optional[str] = None
    disabled: Optional[bool] = None
    domain_owner: Optional[bool] = None
    email: Optional[str] = None
    environment: Optional[str] = None
    feature_flags: Optional[list[FeatureFlagType]] = None
    first_name: Optional[str] = None
    group_names: Optional[list[str]] = None
    idm_type: Optional[Literal['SSO', 'VOLTERRA_MANAGED', 'UNDEFINED']] = None
    last_login_timestamp: Optional[str] = None
    last_name: Optional[str] = None
    msp_managed: Optional[MSPManaged] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    namespace_access: Optional[NamespaceAccessType] = None
    namespace_roles: Optional[list[NamespaceRoleType]] = None
    original_tenant: Optional[str] = None
    plan_type: Optional[Literal['FREE', 'INDIVIDUAL', 'TEAM', 'ORGANIZATION', 'PLAN_TYPE_UNSPECIFIED']] = None
    self_managed: Optional[Any] = None
    signup_origin: Optional[Literal['ORIGIN_UNKNOWN', 'ORIGIN_F5XC', 'ORIGIN_AWS', 'ORIGIN_ASB']] = None
    state: Optional[Literal['StateUndefined', 'StateCreating', 'StateCreateFailed', 'StateActive', 'StateDisabled']] = None
    sync_mode: Optional[Literal['SELF', 'SCIM']] = None
    tenant: Optional[str] = None
    tenant_flags: Optional[dict[str, Any]] = None
    tenant_state: Optional[str] = None
    tenant_type: Optional[Literal['UNKNOWN', 'FREEMIUM', 'ENTERPRISE']] = None
    tile_access: Optional[dict[str, Any]] = None
    tos_accepted: Optional[str] = None
    tos_accepted_at: Optional[str] = None
    tos_current_version: Optional[str] = None
    tos_version: Optional[str] = None
    type_: Optional[Literal['USER', 'SERVICE', 'DEBUG']] = Field(default=None, alias="type")
    user_uuid: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    contacts: Optional[list[ObjectRefType]] = None
    domain_owner: Optional[bool] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    groups: Optional[list[ObjectRefType]] = None
    idm_type: Optional[Literal['SSO', 'VOLTERRA_MANAGED', 'UNDEFINED']] = None
    last_login_timestamp: Optional[str] = None
    last_name: Optional[str] = None
    locale: Optional[str] = None
    state: Optional[Literal['StateUndefined', 'StateCreating', 'StateCreateFailed', 'StateActive', 'StateDisabled']] = None
    sync_mode: Optional[Literal['SELF', 'SCIM']] = None
    tos_accepted: Optional[str] = None
    tos_accepted_at: Optional[str] = None
    tos_version: Optional[str] = None
    type_: Optional[Literal['USER', 'SERVICE', 'DEBUG']] = Field(default=None, alias="type")


class ListUserRoleResponseItem(F5XCBaseModel):
    """Allows user namespace role retrieval"""

    creation_timestamp: Optional[str] = None
    disabled: Optional[bool] = None
    domain_owner: Optional[bool] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    group_names: Optional[list[str]] = None
    idm_type: Optional[Literal['SSO', 'VOLTERRA_MANAGED', 'UNDEFINED']] = None
    last_login_timestamp: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    namespace_roles: Optional[list[NamespaceRoleType]] = None
    otp_enabled: Optional[bool] = None
    sync_mode: Optional[Literal['SELF', 'SCIM']] = None
    tenant: Optional[str] = None
    tenant_type: Optional[Literal['UNKNOWN', 'FREEMIUM', 'ENTERPRISE']] = None
    type_: Optional[Literal['USER', 'SERVICE', 'DEBUG']] = Field(default=None, alias="type")


class ListUserRoleResponse(F5XCBaseModel):
    """Allows user namespace roles retrieval"""

    items: Optional[list[ListUserRoleResponseItem]] = None


class SpecType(F5XCBaseModel):
    """Shape of the User specification"""

    gc_spec: Optional[GlobalSpecType] = None


class Object(F5XCBaseModel):
    """User object"""

    metadata: Optional[ObjectMetaType] = None
    spec: Optional[SpecType] = None
    system_metadata: Optional[SystemObjectMetaType] = None


class ResetPasswordByAdminRequest(F5XCBaseModel):
    """Reset password by admin request contains email of user for which..."""

    email: Optional[str] = None


class SendPasswordEmailRequest(F5XCBaseModel):
    """SendPasswordEmailRequest is the request parameters for sending the..."""

    email: Optional[str] = None
    namespace: Optional[str] = None


class SendPasswordEmailResponse(F5XCBaseModel):
    """SendPasswordEmailResponse is an empty response after an email had been sent."""

    pass


class GroupResponse(F5XCBaseModel):
    error: Optional[ErrorType] = None


# Convenience aliases
Spec = GlobalSpecType
Spec = SpecType
