"""Pydantic models for customer_support."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class CustomerSupportListItem(F5XCBaseModel):
    """List item for customer_support resources."""


class AttachmentType(F5XCBaseModel):
    """Attachment represents a single support ticket comment attachment...."""

    attachment: Optional[str] = None
    content_type: Optional[str] = None
    filename: Optional[str] = None
    tp_id: Optional[str] = None


class CloseRequest(F5XCBaseModel):
    """Closes an open existing customer support ticket"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class CloseResponse(F5XCBaseModel):
    """Gives details of result of closing a customer support ticket."""

    err: Optional[Literal['EUNKNOWN', 'EOK', 'E_NOT_CLOSED', 'E_NOT_OPEN', 'E_NOT_ELIGIBLE', 'E_NOT_NOT_FOUND']] = None


class CommentRequest(F5XCBaseModel):
    """Adds a new comment to an existing customer support ticket"""

    attachments: Optional[list[AttachmentType]] = None
    comment: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class CommentResponse(F5XCBaseModel):
    """Gives details of result of adding a customer support ticket."""

    err: Optional[Literal['EUNKNOWN', 'EOK', 'E_NOT_CLOSED', 'E_NOT_OPEN', 'E_NOT_ELIGIBLE', 'E_NOT_NOT_FOUND']] = None


class CommentType(F5XCBaseModel):
    """Comment represents a single comment on an issue. It contains information..."""

    attachment_ids: Optional[list[str]] = None
    attachments_info: Optional[list[AttachmentType]] = None
    author_email: Optional[str] = None
    author_name: Optional[str] = None
    created_at: Optional[str] = None
    html: Optional[str] = None
    plain_text: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

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


class CreateSpecType(F5XCBaseModel):
    """Creates a new customer support ticket in our customer support provider system."""

    category: Optional[str] = None
    comments: Optional[list[CommentType]] = None
    description: Optional[str] = None
    ongoing: Optional[bool] = None
    priority: Optional[Literal['PRIORITY_UNKNOWN', 'PRIORITY_NORMAL', 'PRIORITY_HIGH', 'PRIORITY_URGENT']] = None
    product_data: Optional[str] = None
    relates_to: Optional[list[ObjectRefType]] = None
    service: Optional[Literal['SS_UNKNOWN', 'SS_ACCOUNT_PROTECTION', 'SS_ADMINISTRATION', 'SS_APPLICATION_TRAFFIC_INSIGHT', 'SS_AUDIT_LOGS_AND_ALERTS', 'SS_AUTHENTICATION_INTELLIGENCE', 'SS_BILLING', 'SS_CLIENT_SIDE_DEFENSE', 'SS_CLOUD_AND_EDGE_SITES', 'SS_DDOS_AND_TRANSIT_SERVICES', 'SS_DISTRIBUTED_APPS', 'SS_DNS_MANAGEMENT', 'SS_LOAD_BALANCERS', 'SS_SHARED_CONFIGURATION', 'SS_WEB_APP_AND_API_PROTECTION', 'SS_OTHER', 'SS_BOT_DEFENSE', 'SS_CDN', 'SS_OBSERVABILITY', 'SS_DELEGATED_ACCESS', 'SS_MULTI_CLOUD_NETWORK_CONNECT', 'SS_MULTI_CLOUD_APP_CONNECT', 'SS_BIG_IP_APM', 'SS_DATA_INTELLIGENCE', 'SS_NGINX_ONE', 'SS_WEB_APP_SCANNING', 'SS_ROUTED_DDOS', 'SS_MOBILE_APP_SHIELD']] = None
    status: Optional[Literal['STATUS_UNKNOWN', 'STATUS_NEW', 'STATUS_OPEN', 'STATUS_PENDING', 'STATUS_ONHOLD', 'STATUS_SOLVED', 'STATUS_CLOSED', 'STATUS_FAILED']] = None
    subject: Optional[str] = None
    timeline: Optional[str] = None
    topic: Optional[Literal['TOPIC_UNKNOWN', 'ACCOUNT_SUPPORT_TOPIC_ACCESS_REQUEST', 'ACCOUNT_SUPPORT_TOPIC_ACCOUNT', 'ACCOUNT_SUPPORT_TOPIC_BILLING', 'ACCOUNT_SUPPORT_TOPIC_BILLING_PLAN_CHANGE', 'ACCOUNT_SUPPORT_TOPIC_PUBLIC_IP', 'ACCOUNT_SUPPORT_TOPIC_QUOTA_INCREASE', 'ACCOUNT_SUPPORT_TOPIC_RMA', 'ACCOUNT_SUPPORT_TOPIC_TAX_EXEMPT_VERIFICATION', 'ACCOUNT_SUPPORT_TOPIC_OTHERS', 'TECHNICAL_SUPPORT_TOPIC_CONFIGURATION_CHANGES', 'TECHNICAL_SUPPORT_TOPIC_ERROR_MESSAGE', 'TECHNICAL_SUPPORT_TOPIC_NEW_CONFIGURATION', 'TECHNICAL_SUPPORT_TOPIC_PRODUCT_QUESTION', 'TECHNICAL_SUPPORT_TOPIC_TROUBLESHOOTING', 'TECHNICAL_SUPPORT_TOPIC_OTHERS', 'INCIDENT_SUPPORT_TOPIC_LATENCY', 'INCIDENT_SUPPORT_TOPIC_PERFORMANCE_DEGRADATION', 'INCIDENT_SUPPORT_TOPIC_PARTIAL_OUTAGE', 'INCIDENT_SUPPORT_TOPIC_COMPLETE_OUTAGE', 'INCIDENT_SUPPORT_TOPIC_OTHERS', 'TASK_TOPIC_PLAN_TRANSITION', 'PROBLEM_TOPIC_SUPPORT_ALERT', 'QUESTION_TOPIC_INFRASTRUCTURE', 'TECHNICAL_SUPPORT_TOPIC_DELEGATED_DOMAIN_MIGRATION']] = None
    tp_id: Optional[str] = None
    type_: Optional[Literal['TYPE_UNKNOWN', 'TYPE_PROBLEM', 'TYPE_TASK', 'TYPE_QUESTION', 'TYPE_INCIDENT', 'TYPE_TECHNICAL_SUPPORT', 'TYPE_ACCOUNT_SUPPORT', 'TYPE_INCIDENT_SUPPORT']] = Field(default=None, alias="type")


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
    """Support ticket representation we display to customers. There's much more..."""

    author_name: Optional[str] = None
    category: Optional[str] = None
    comments: Optional[list[CommentType]] = None
    created_at: Optional[str] = None
    custom_fields: Optional[list[str]] = None
    description: Optional[str] = None
    escalated: Optional[bool] = None
    followups: Optional[list[ObjectRefType]] = None
    ongoing: Optional[bool] = None
    priority: Optional[Literal['PRIORITY_UNKNOWN', 'PRIORITY_NORMAL', 'PRIORITY_HIGH', 'PRIORITY_URGENT']] = None
    product_data: Optional[str] = None
    relates_to: Optional[list[ObjectRefType]] = None
    service: Optional[Literal['SS_UNKNOWN', 'SS_ACCOUNT_PROTECTION', 'SS_ADMINISTRATION', 'SS_APPLICATION_TRAFFIC_INSIGHT', 'SS_AUDIT_LOGS_AND_ALERTS', 'SS_AUTHENTICATION_INTELLIGENCE', 'SS_BILLING', 'SS_CLIENT_SIDE_DEFENSE', 'SS_CLOUD_AND_EDGE_SITES', 'SS_DDOS_AND_TRANSIT_SERVICES', 'SS_DISTRIBUTED_APPS', 'SS_DNS_MANAGEMENT', 'SS_LOAD_BALANCERS', 'SS_SHARED_CONFIGURATION', 'SS_WEB_APP_AND_API_PROTECTION', 'SS_OTHER', 'SS_BOT_DEFENSE', 'SS_CDN', 'SS_OBSERVABILITY', 'SS_DELEGATED_ACCESS', 'SS_MULTI_CLOUD_NETWORK_CONNECT', 'SS_MULTI_CLOUD_APP_CONNECT', 'SS_BIG_IP_APM', 'SS_DATA_INTELLIGENCE', 'SS_NGINX_ONE', 'SS_WEB_APP_SCANNING', 'SS_ROUTED_DDOS', 'SS_MOBILE_APP_SHIELD']] = None
    status: Optional[Literal['STATUS_UNKNOWN', 'STATUS_NEW', 'STATUS_OPEN', 'STATUS_PENDING', 'STATUS_ONHOLD', 'STATUS_SOLVED', 'STATUS_CLOSED', 'STATUS_FAILED']] = None
    subject: Optional[str] = None
    tags: Optional[list[str]] = None
    timeline: Optional[str] = None
    topic: Optional[Literal['TOPIC_UNKNOWN', 'ACCOUNT_SUPPORT_TOPIC_ACCESS_REQUEST', 'ACCOUNT_SUPPORT_TOPIC_ACCOUNT', 'ACCOUNT_SUPPORT_TOPIC_BILLING', 'ACCOUNT_SUPPORT_TOPIC_BILLING_PLAN_CHANGE', 'ACCOUNT_SUPPORT_TOPIC_PUBLIC_IP', 'ACCOUNT_SUPPORT_TOPIC_QUOTA_INCREASE', 'ACCOUNT_SUPPORT_TOPIC_RMA', 'ACCOUNT_SUPPORT_TOPIC_TAX_EXEMPT_VERIFICATION', 'ACCOUNT_SUPPORT_TOPIC_OTHERS', 'TECHNICAL_SUPPORT_TOPIC_CONFIGURATION_CHANGES', 'TECHNICAL_SUPPORT_TOPIC_ERROR_MESSAGE', 'TECHNICAL_SUPPORT_TOPIC_NEW_CONFIGURATION', 'TECHNICAL_SUPPORT_TOPIC_PRODUCT_QUESTION', 'TECHNICAL_SUPPORT_TOPIC_TROUBLESHOOTING', 'TECHNICAL_SUPPORT_TOPIC_OTHERS', 'INCIDENT_SUPPORT_TOPIC_LATENCY', 'INCIDENT_SUPPORT_TOPIC_PERFORMANCE_DEGRADATION', 'INCIDENT_SUPPORT_TOPIC_PARTIAL_OUTAGE', 'INCIDENT_SUPPORT_TOPIC_COMPLETE_OUTAGE', 'INCIDENT_SUPPORT_TOPIC_OTHERS', 'TASK_TOPIC_PLAN_TRANSITION', 'PROBLEM_TOPIC_SUPPORT_ALERT', 'QUESTION_TOPIC_INFRASTRUCTURE', 'TECHNICAL_SUPPORT_TOPIC_DELEGATED_DOMAIN_MIGRATION']] = None
    tp_id: Optional[str] = None
    type_: Optional[Literal['TYPE_UNKNOWN', 'TYPE_PROBLEM', 'TYPE_TASK', 'TYPE_QUESTION', 'TYPE_INCIDENT', 'TYPE_TECHNICAL_SUPPORT', 'TYPE_ACCOUNT_SUPPORT', 'TYPE_INCIDENT_SUPPORT']] = Field(default=None, alias="type")
    update_at: Optional[str] = None
    user: Optional[list[ObjectRefType]] = None
    via: Optional[dict[str, Any]] = None


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


class EscalationRequest(F5XCBaseModel):
    """Changes priority of an existing customer support ticket"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class EscalationResponse(F5XCBaseModel):
    """Any error that may occurred during escalating of a ticket"""

    err: Optional[Literal['EUNKNOWN', 'EOK', 'E_NOT_CLOSED', 'E_NOT_OPEN', 'E_NOT_ELIGIBLE', 'E_NOT_NOT_FOUND']] = None


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
    """By default a summary of customer_support is returned in 'List'. By..."""

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


class ListSupportRequest(F5XCBaseModel):
    """This is the input message of the 'ListCTSupportTickets' RPC. Fields can..."""

    priority: Optional[list[Literal['PRIORITY_UNKNOWN', 'PRIORITY_NORMAL', 'PRIORITY_HIGH', 'PRIORITY_URGENT']]] = None
    status: Optional[list[Literal['STATUS_UNKNOWN', 'STATUS_NEW', 'STATUS_OPEN', 'STATUS_PENDING', 'STATUS_ONHOLD', 'STATUS_SOLVED', 'STATUS_CLOSED', 'STATUS_FAILED']]] = None


class ListSupportResponse(F5XCBaseModel):
    """This is the output message of 'ListCTSupportTickets' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[ListResponseItem]] = None


class PriorityRequest(F5XCBaseModel):
    """Changes priority of an existing customer support ticket"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    priority: Optional[Literal['PRIORITY_UNKNOWN', 'PRIORITY_NORMAL', 'PRIORITY_HIGH', 'PRIORITY_URGENT']] = None


class PriorityResponse(F5XCBaseModel):
    """Gives details of result of changing priority a customer support ticket."""

    err: Optional[Literal['EUNKNOWN', 'EOK', 'E_NOT_CLOSED', 'E_NOT_OPEN', 'E_NOT_ELIGIBLE', 'E_NOT_NOT_FOUND']] = None


class RaiseTaxExemptVerificationSupportTicketRequest(F5XCBaseModel):
    """Provides ability to request tax status of the customer, eventually..."""

    attachments: Optional[list[AttachmentType]] = None
    request_description: Optional[str] = None


class RaiseTaxExemptVerificationSupportTicketResponse(F5XCBaseModel):
    """Any error that may occurred during tax status verification request. Note..."""

    err: Optional[Literal['EUNKNOWN', 'EOK', 'E_NOT_CLOSED', 'E_NOT_OPEN', 'E_NOT_ELIGIBLE', 'E_NOT_NOT_FOUND']] = None
    name: Optional[str] = None


class ReopenRequest(F5XCBaseModel):
    """Reopens a closed existing customer support ticket"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class ReopenResponse(F5XCBaseModel):
    """Gives details of result of reopening a customer support ticket."""

    err: Optional[Literal['EUNKNOWN', 'EOK', 'E_NOT_CLOSED', 'E_NOT_OPEN', 'E_NOT_ELIGIBLE', 'E_NOT_NOT_FOUND']] = None


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
