"""Pydantic models for alert_receiver."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AlertReceiverListItem(F5XCBaseModel):
    """List item for alert_receiver resources."""


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


class AuthToken(F5XCBaseModel):
    """Authentication Token for access"""

    token: Optional[SecretType] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class CACertificateObj(F5XCBaseModel):
    """Configuration for CA certificate"""

    trusted_ca: Optional[list[ObjectRefType]] = None


class ClientCertificateObj(F5XCBaseModel):
    """Configuration for client certificate"""

    use_tls_obj: Optional[list[ObjectRefType]] = None


class ConfirmAlertReceiverRequest(F5XCBaseModel):
    """Request to confirm the Alert Receiver"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    verification_code: Optional[str] = None


class ConfirmAlertReceiverResponse(F5XCBaseModel):
    """Response for the Alert Receiver Confirm request; empty because the only..."""

    pass


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class EmailConfig(F5XCBaseModel):
    email: Optional[str] = None


class OpsGenieConfig(F5XCBaseModel):
    """OpsGenie configuration to send alert notifications"""

    api_key: Optional[SecretType] = None
    url: Optional[str] = None


class PagerDutyConfig(F5XCBaseModel):
    """PagerDuty configuration to send alert notifications"""

    routing_key: Optional[SecretType] = None
    url: Optional[str] = None


class SlackConfig(F5XCBaseModel):
    """Slack configuration to send alert notifications"""

    channel: Optional[str] = None
    url: Optional[SecretType] = None


class SMSConfig(F5XCBaseModel):
    contact_number: Optional[str] = None


class HttpBasicAuth(F5XCBaseModel):
    """Authorization parameters to access HTPP alert Receiver Endpoint."""

    password: Optional[SecretType] = None
    user_name: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class UpstreamTlsValidationContext(F5XCBaseModel):
    """Upstream TLS Validation Context"""

    ca_cert_obj: Optional[CACertificateObj] = None


class TLSConfig(F5XCBaseModel):
    """Configures the token request's TLS settings."""

    disable_sni: Optional[Any] = None
    max_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    min_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    sni: Optional[str] = None
    use_server_verification: Optional[UpstreamTlsValidationContext] = None
    volterra_trusted_ca: Optional[Any] = None


class HTTPConfig(F5XCBaseModel):
    """Configuration for HTTP endpoint"""

    auth_token: Optional[AuthToken] = None
    basic_auth: Optional[HttpBasicAuth] = None
    client_cert_obj: Optional[ClientCertificateObj] = None
    enable_http2: Optional[bool] = None
    follow_redirects: Optional[bool] = None
    no_authorization: Optional[Any] = None
    no_tls: Optional[Any] = None
    use_tls: Optional[TLSConfig] = None


class WebhookConfig(F5XCBaseModel):
    """Webhook configuration to send alert notifications"""

    http_config: Optional[HTTPConfig] = None
    url: Optional[SecretType] = None


class CreateSpecType(F5XCBaseModel):
    """Creates a new Alert Receiver object"""

    email: Optional[EmailConfig] = None
    opsgenie: Optional[OpsGenieConfig] = None
    pagerduty: Optional[PagerDutyConfig] = None
    slack: Optional[SlackConfig] = None
    sms: Optional[SMSConfig] = None
    webhook: Optional[WebhookConfig] = None


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
    """Get the Alert Receiver object"""

    email: Optional[EmailConfig] = None
    opsgenie: Optional[OpsGenieConfig] = None
    pagerduty: Optional[PagerDutyConfig] = None
    slack: Optional[SlackConfig] = None
    sms: Optional[SMSConfig] = None
    webhook: Optional[WebhookConfig] = None


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
    """Replaces the content of an Alert Receiver object"""

    email: Optional[EmailConfig] = None
    opsgenie: Optional[OpsGenieConfig] = None
    pagerduty: Optional[PagerDutyConfig] = None
    slack: Optional[SlackConfig] = None
    sms: Optional[SMSConfig] = None
    webhook: Optional[WebhookConfig] = None


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
    """By default a summary of alert_receiver is returned in 'List'. By setting..."""

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


class TestAlertReceiverRequest(F5XCBaseModel):
    """Request to send test alert"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class TestAlertReceiverResponse(F5XCBaseModel):
    """Response for the Alert Receiver test request; empty because the only..."""

    pass


class VerifyAlertReceiverRequest(F5XCBaseModel):
    """Send request to verify Alert Receiver"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class VerifyAlertReceiverResponse(F5XCBaseModel):
    """Response for the Alert Receiver Verify request; empty because the only..."""

    pass


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
