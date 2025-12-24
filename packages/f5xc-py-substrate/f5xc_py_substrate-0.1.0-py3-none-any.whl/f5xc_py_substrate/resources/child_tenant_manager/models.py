"""Pydantic models for child_tenant_manager."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ChildTenantManagerListItem(F5XCBaseModel):
    """List item for child_tenant_manager resources."""


class CustomerInfo(F5XCBaseModel):
    """Optional details for the new child tenant"""

    additional_info: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class DateRange(F5XCBaseModel):
    """Date range is for selecting a date range"""

    end_date: Optional[str] = None
    start_date: Optional[str] = None


class CTBannerNotification(F5XCBaseModel):
    """CTBannerNotification. """

    content_html: Optional[str] = None
    content_text: Optional[str] = None
    time_period: Optional[DateRange] = None
    title: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class CTGroupAssignmentType(F5XCBaseModel):
    """The Group Mapping field is used to associate local user groups with user..."""

    child_tenant_groups: Optional[list[str]] = None
    group: Optional[ObjectRefType] = None


class GlobalSpecType(F5XCBaseModel):
    """Instance of one single contact that can be used to communicate with..."""

    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    contact_type: Optional[Literal['MAILING', 'BILLING', 'PAYMENT']] = None
    country: Optional[str] = None
    county: Optional[str] = None
    phone_number: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    zip_code: Optional[str] = None


class CRMInfo(F5XCBaseModel):
    """CRM Information"""

    pass


class GetSpecType(F5XCBaseModel):
    """Get child_tenant reads a given object from storage backend for..."""

    child_tenant_manager: Optional[ObjectRefType] = None
    company_name: Optional[str] = None
    contact_detail: Optional[GlobalSpecType] = None
    crm_details: Optional[Any] = None
    customer_info: Optional[CustomerInfo] = None
    domain: Optional[str] = None
    status: Optional[Literal['StateInitializing', 'StateCreating', 'StateCreateFailed', 'StateInactive', 'StateActive', 'StateConfiguring', 'StateConfiguringFailed', 'StateDeleteInProgress', 'StateDeleteFailed']] = None
    tenant_profile: Optional[ObjectRefType] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ViewRefType(F5XCBaseModel):
    """ViewRefType represents a reference to a view"""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


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


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


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


class CTListResponseItem(F5XCBaseModel):
    """Child Tenant Information"""

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


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class ListChildTenantsByCTMResp(F5XCBaseModel):
    """Response to get list of Child Tenant for a given CTM."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[CTListResponseItem]] = None


class CTListToCTM(F5XCBaseModel):
    """Child tenants reference to child tenant manager"""

    child_tenant_manager: Optional[str] = None
    child_tenants: Optional[list[str]] = None


class MigrateCTMChildTenantsReq(F5XCBaseModel):
    """Request to migrate child tenants to a specified child tenant manager"""

    ct_list_to_target_ctm: Optional[CTListToCTM] = None
    name: Optional[str] = None


class MigrateCTMChildTenantsResp(F5XCBaseModel):
    """Response of migrating child tenants to a specified CTM."""

    child_tenant_manager: Optional[str] = None
    errors: Optional[list[ErrorType]] = None
    migrate_initiated_for_ct_count: Optional[int] = None
    total_ct_count: Optional[int] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replaces attributes of a child_tenant_manager configuration."""

    banner_message: Optional[CTBannerNotification] = None
    group_assignments: Optional[list[CTGroupAssignmentType]] = None
    tenant_owner_group: Optional[ObjectRefType] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class ReplaceResponse(F5XCBaseModel):
    pass


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class CreateSpecType(F5XCBaseModel):
    """Creates a child_tenant_manager config instance. Name of the object is..."""

    group_assignments: Optional[list[CTGroupAssignmentType]] = None
    tenant_owner_group: Optional[ObjectRefType] = None


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


class GetSpecType(F5XCBaseModel):
    """Get child_tenant_manager reads a given object from storage backend for..."""

    banner_message: Optional[CTBannerNotification] = None
    group_assignments: Optional[list[CTGroupAssignmentType]] = None
    tenant_owner_group: Optional[ObjectRefType] = None


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[CreateRequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[ReplaceRequest] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of child_tenant_manager is returned in 'List'. By..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[GetSpecType] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[ListResponseItem]] = None


# Convenience aliases
Spec = GlobalSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
Spec = CreateSpecType
Spec = GetSpecType
