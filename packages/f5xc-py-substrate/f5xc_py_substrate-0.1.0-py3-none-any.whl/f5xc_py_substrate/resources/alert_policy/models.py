"""Pydantic models for alert_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AlertPolicyListItem(F5XCBaseModel):
    """List item for alert_policy resources."""


class Match(F5XCBaseModel):
    """Alert Policy info that matches AlertPolicyMatchRequest giving   alert..."""

    policy_name: Optional[str] = None
    policy_status: Optional[Literal['INACTIVE', 'ACTIVE']] = None


class MatchRequest(F5XCBaseModel):
    """Request message for GetAlertPolicyMatch RPC, describing alert to match..."""

    labels: Optional[dict[str, Any]] = None
    namespace: Optional[str] = None


class MatchResponse(F5XCBaseModel):
    """Response of matching Alert Policies from Get Alert Policy Match request"""

    alert_match: Optional[list[Match]] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class CustomGroupBy(F5XCBaseModel):
    """Specify list of custom labels to group/aggregate the alerts"""

    labels: Optional[list[str]] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class NotificationParameters(F5XCBaseModel):
    """Set of notification parameters to decide how and when the alert..."""

    custom: Optional[CustomGroupBy] = None
    default: Optional[Any] = None
    group_interval: Optional[str] = None
    group_wait: Optional[str] = None
    individual: Optional[Any] = None
    repeat_interval: Optional[str] = None
    ves_io_group: Optional[Any] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class LabelMatcher(F5XCBaseModel):
    exact_match: Optional[str] = None
    regex_match: Optional[str] = None


class CustomMatcher(F5XCBaseModel):
    """A set of matchers an alert has to fulfill to match the route"""

    alertlabel: Optional[dict[str, Any]] = None
    alertname: Optional[LabelMatcher] = None
    group: Optional[LabelMatcher] = None
    severity: Optional[LabelMatcher] = None


class GroupMatcher(F5XCBaseModel):
    """Select one or more known group names to match the incoming alert"""

    groups: Optional[list[Literal['INFRASTRUCTURE', 'IAAS_CAAS', 'VIRTUAL_HOST', 'VOLT_SHARE', 'UAM', 'SECURITY', 'TIMESERIES_ANOMALY', 'SHAPE_SECURITY', 'SECURITY_CSD', 'CDN', 'SYNTHETIC_MONITORS', 'TLS', 'SECURITY_BOT_DEFENSE', 'CLOUD_LINK', 'DNS', 'ROUTED_DDOS']]] = None


class SeverityMatcher(F5XCBaseModel):
    """Select one or more severity levels to match the incoming alert"""

    severities: Optional[list[Literal['MINOR', 'MAJOR', 'CRITICAL']]] = None


class Route(F5XCBaseModel):
    """Route defines the match conditions to match the incoming alert and the..."""

    alertname: Optional[Literal['SITE_CUSTOMER_TUNNEL_INTERFACE_DOWN', 'SITE_PHYSICAL_INTERFACE_DOWN', 'TUNNELS_TO_CUSTOMER_SITE_DOWN', 'SERVICE_SERVER_ERROR', 'SERVICE_CLIENT_ERROR', 'SERVICE_HEALTH_LOW', 'SERVICE_UNAVAILABLE', 'SERVICE_SERVER_ERROR_PER_SOURCE_SITE', 'SERVICE_CLIENT_ERROR_PER_SOURCE_SITE', 'SERVICE_ENDPOINT_HEALTHCHECK_FAILURE', 'SYNTHETIC_MONITOR_HEALTH_CRITICAL', 'MALICIOUS_USER_DETECTED', 'WAF_TOO_MANY_ATTACKS', 'API_SECURITY_TOO_MANY_ATTACKS', 'SERVICE_POLICY_TOO_MANY_ATTACKS', 'WAF_TOO_MANY_MALICIOUS_BOTS', 'BOT_DEFENSE_TOO_MANY_SECURITY_EVENTS', 'THREAT_CAMPAIGN', 'VES_CLIENT_SIDE_DEFENSE_SUSPICIOUS_DOMAIN', 'VES_CLIENT_SIDE_DEFENSE_SENSITIVE_FIELD_READ', 'ERROR_RATE_ANOMALY', 'REQUEST_RATE_ANOMALY', 'REQUEST_THROUGHPUT_ANOMALY', 'RESPONSE_LATENCY_ANOMALY', 'RESPONSE_THROUGHPUT_ANOMALY', 'TLS_AUTOMATIC_CERTIFICATE_RENEWAL_FAILURE', 'TLS_AUTOMATIC_CERTIFICATE_RENEWAL_STILL_FAILING', 'TLS_AUTOMATIC_CERTIFICATE_EXPIRED', 'TLS_CUSTOM_CERTIFICATE_EXPIRING', 'TLS_CUSTOM_CERTIFICATE_EXPIRING_SOON', 'TLS_CUSTOM_CERTIFICATE_EXPIRED', 'L7DDOS', 'DNS_ZONE_IGNORED_DUPLICATE_RECORD', 'API_SECURITY_UNUSED_API_DETECTED', 'API_SECURITY_SHADOW_API_DETECTED', 'API_SECURITY_SENSITIVE_DATA_IN_RESPONSE_DETECTED', 'API_SECURITY_RISK_SCORE_HIGH_DETECTED', 'ROUTED_DDOS_ALERT_NOTIFICATION', 'ROUTED_DDOS_MITIGATION_NOTIFICATION']] = None
    alertname_regex: Optional[str] = None
    any: Optional[Any] = None
    custom: Optional[CustomMatcher] = None
    dont_send: Optional[Any] = None
    group: Optional[GroupMatcher] = None
    notification_parameters: Optional[NotificationParameters] = None
    send: Optional[Any] = None
    severity: Optional[SeverityMatcher] = None


class CreateSpecType(F5XCBaseModel):
    """Creates a new Alert Policy Object"""

    notification_parameters: Optional[NotificationParameters] = None
    receivers: Optional[list[ObjectRefType]] = None
    routes: Optional[list[Route]] = None


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
    """Get the Alert Policy Object"""

    notification_parameters: Optional[NotificationParameters] = None
    receivers: Optional[list[ObjectRefType]] = None
    routes: Optional[list[Route]] = None


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


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replaces the content of the Alert Policy Object"""

    notification_parameters: Optional[NotificationParameters] = None
    receivers: Optional[list[ObjectRefType]] = None
    routes: Optional[list[Route]] = None


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
    """By default a summary of alert_policy is returned in 'List'. By setting..."""

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
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
