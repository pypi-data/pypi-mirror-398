"""Pydantic models for addon_service."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AddonServiceListItem(F5XCBaseModel):
    """List item for addon_service resources."""


class Content(F5XCBaseModel):
    """Content holds the subject and the description"""

    description: Optional[str] = None
    subject: Optional[str] = None


class CustomSupportTicket(F5XCBaseModel):
    """CustomSupportTicket holds the template details provided by the service owner"""

    priority: Optional[Literal['PRIORITY_UNKNOWN', 'PRIORITY_NORMAL', 'PRIORITY_HIGH', 'PRIORITY_URGENT']] = None
    service: Optional[Literal['SS_UNKNOWN', 'SS_ACCOUNT_PROTECTION', 'SS_ADMINISTRATION', 'SS_APPLICATION_TRAFFIC_INSIGHT', 'SS_AUDIT_LOGS_AND_ALERTS', 'SS_AUTHENTICATION_INTELLIGENCE', 'SS_BILLING', 'SS_CLIENT_SIDE_DEFENSE', 'SS_CLOUD_AND_EDGE_SITES', 'SS_DDOS_AND_TRANSIT_SERVICES', 'SS_DISTRIBUTED_APPS', 'SS_DNS_MANAGEMENT', 'SS_LOAD_BALANCERS', 'SS_SHARED_CONFIGURATION', 'SS_WEB_APP_AND_API_PROTECTION', 'SS_OTHER', 'SS_BOT_DEFENSE', 'SS_CDN', 'SS_OBSERVABILITY', 'SS_DELEGATED_ACCESS', 'SS_MULTI_CLOUD_NETWORK_CONNECT', 'SS_MULTI_CLOUD_APP_CONNECT', 'SS_BIG_IP_APM', 'SS_DATA_INTELLIGENCE', 'SS_NGINX_ONE', 'SS_WEB_APP_SCANNING', 'SS_ROUTED_DDOS', 'SS_MOBILE_APP_SHIELD']] = None
    subscribe_content: Optional[Content] = None
    unsubscribe_content: Optional[Content] = None


class EmailDL(F5XCBaseModel):
    """Addon Subscription Emails associated with the Addon Subscription"""

    email_ids: Optional[list[str]] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class SupportTicketOptions(F5XCBaseModel):
    """SupportTicketOptions deals with whether the support ticket needs to be created"""

    no_support_ticket: Optional[Any] = None
    support_ticket_with_custom_template: Optional[CustomSupportTicket] = None
    support_ticket_with_default_template: Optional[Any] = None


class NotificationPreference(F5XCBaseModel):
    """NotificationPreference preference for receiving addon subscription notifications."""

    emails: Optional[EmailDL] = None
    support_ticket_option: Optional[SupportTicketOptions] = None


class FullyManagedActivationType(F5XCBaseModel):
    """Managed Activation and require complete manual intervention."""

    notification_preference: Optional[NotificationPreference] = None


class GetActivationStatusResp(F5XCBaseModel):
    """Response shape for addon service activation status"""

    state: Optional[Literal['AS_NONE', 'AS_PENDING', 'AS_SUBSCRIBED', 'AS_ERROR']] = None


class PartiallyManagedActivationType(F5XCBaseModel):
    """Addon service activation will require partial management from backend or SRE."""

    pass


class SelfActivationType(F5XCBaseModel):
    """Addon service can be subscribed and activated by user directly without..."""

    default_tile_name: Optional[str] = None


class GetAddonServiceDetailsResp(F5XCBaseModel):
    """Response shape for addon service details"""

    addon_service_group_display_name: Optional[str] = None
    addon_service_group_name: Optional[str] = None
    display_name: Optional[str] = None
    managed_activation: Optional[FullyManagedActivationType] = None
    partially_managed_activation: Optional[Any] = None
    self_activation: Optional[SelfActivationType] = None
    tier: Optional[Literal['NO_TIER', 'BASIC', 'STANDARD', 'ADVANCED', 'PREMIUM']] = None


class GetAllServiceTiersActivationStatusResp(F5XCBaseModel):
    """Response shape for addon service feature tier activation statuses"""

    activation_states: Optional[dict[str, Any]] = None


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


class GetSpecType(F5XCBaseModel):
    """Get addon_service reads a given object from storage backend for..."""

    api_groups: Optional[list[ObjectRefType]] = None
    dependent_services: Optional[list[ObjectRefType]] = None
    display_name: Optional[str] = None
    included_services: Optional[list[ObjectRefType]] = None
    managed_activation: Optional[FullyManagedActivationType] = None
    partially_managed_activation: Optional[Any] = None
    self_activation: Optional[SelfActivationType] = None
    tags: Optional[list[Literal['NONE', 'NEW', 'PREVIEW', 'PRIVATE_PREVIEW']]] = None
    tier: Optional[Literal['NO_TIER', 'BASIC', 'STANDARD', 'ADVANCED', 'PREMIUM']] = None


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
    """By default a summary of addon_service is returned in 'List'. By setting..."""

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


# Convenience aliases
Spec = GetSpecType
