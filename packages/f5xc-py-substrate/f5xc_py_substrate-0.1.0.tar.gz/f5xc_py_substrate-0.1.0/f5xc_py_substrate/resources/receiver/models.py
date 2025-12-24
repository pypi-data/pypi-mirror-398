"""Pydantic models for receiver."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ReceiverListItem(F5XCBaseModel):
    """List item for receiver resources."""


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


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


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


class BatchOptionType(F5XCBaseModel):
    """Batch Options allow tuning for how batches of logs are sent to an endpoint"""

    default_timeout_seconds: Optional[Any] = None
    max_bytes: Optional[int] = None
    max_bytes_disabled: Optional[Any] = None
    max_events: Optional[int] = None
    max_events_disabled: Optional[Any] = None
    timeout_seconds: Optional[str] = None


class CompressionType(F5XCBaseModel):
    """Compression Type"""

    gzip_compression: Optional[Any] = None
    no_compression: Optional[Any] = None


class AzureBlobConfig(F5XCBaseModel):
    """Azure Blob Configuration for Data Delivery"""

    batch: Optional[BatchOptionType] = None
    compression: Optional[CompressionType] = None
    connection_string: Optional[SecretType] = None
    container_name: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class TLSClientConfigType(F5XCBaseModel):
    """mTLS Client config allows configuration of mtls client options"""

    certificate: Optional[str] = None
    key_url: Optional[SecretType] = None


class TLSConfigType(F5XCBaseModel):
    """TLS Parameters for client connection to the endpoint"""

    disable_verify_certificate: Optional[Any] = None
    disable_verify_hostname: Optional[Any] = None
    enable_verify_certificate: Optional[Any] = None
    enable_verify_hostname: Optional[Any] = None
    mtls_disabled: Optional[Any] = None
    mtls_enable: Optional[TLSClientConfigType] = None
    no_ca: Optional[Any] = None
    trusted_ca_url: Optional[str] = None


class DatadogConfig(F5XCBaseModel):
    """Configuration for Datadog endpoint"""

    batch: Optional[BatchOptionType] = None
    compression: Optional[CompressionType] = None
    datadog_api_key: Optional[SecretType] = None
    endpoint: Optional[str] = None
    no_tls: Optional[Any] = None
    site: Optional[str] = None
    use_tls: Optional[TLSConfigType] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class GCPBucketConfig(F5XCBaseModel):
    """GCP Bucket Configuration for Global Log Receiver"""

    batch: Optional[BatchOptionType] = None
    bucket: Optional[str] = None
    compression: Optional[CompressionType] = None
    gcp_cred: Optional[ObjectRefType] = None


class HttpAuthBasic(F5XCBaseModel):
    """Authentication parameters to access HTTP Log Receiver Endpoint."""

    password: Optional[SecretType] = None
    user_name: Optional[str] = None


class HTTPConfig(F5XCBaseModel):
    """Configuration for HTTP endpoint"""

    auth_basic: Optional[HttpAuthBasic] = None
    auth_none: Optional[Any] = None
    auth_token: Optional[AuthToken] = None
    batch: Optional[BatchOptionType] = None
    compression: Optional[CompressionType] = None
    no_tls: Optional[Any] = None
    uri: Optional[str] = None
    use_tls: Optional[TLSConfigType] = None


class S3Config(F5XCBaseModel):
    """S3 Configuration for Data Delivery"""

    aws_cred: Optional[ObjectRefType] = None
    aws_region: Optional[str] = None
    batch: Optional[BatchOptionType] = None
    bucket: Optional[str] = None
    compression: Optional[CompressionType] = None


class SplunkConfig(F5XCBaseModel):
    """Configuration for Splunk HEC Logs endpoint"""

    batch: Optional[BatchOptionType] = None
    compression: Optional[CompressionType] = None
    endpoint: Optional[str] = None
    no_tls: Optional[Any] = None
    splunk_hec_token: Optional[SecretType] = None
    use_tls: Optional[TLSConfigType] = None


class CreateSpecType(F5XCBaseModel):
    """Creates a new Data Delivery object"""

    azure_receiver: Optional[AzureBlobConfig] = None
    datadog_receiver: Optional[DatadogConfig] = None
    dataset_type: Optional[str] = None
    gcp_bucket_receiver: Optional[GCPBucketConfig] = None
    http_receiver: Optional[HTTPConfig] = None
    s3_receiver: Optional[S3Config] = None
    splunk_receiver: Optional[SplunkConfig] = None


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
    """Get the Data Delivery object"""

    azure_receiver: Optional[AzureBlobConfig] = None
    datadog_receiver: Optional[DatadogConfig] = None
    dataset_type: Optional[str] = None
    delivery_status: Optional[str] = None
    frequency_seconds: Optional[str] = None
    gcp_bucket_receiver: Optional[GCPBucketConfig] = None
    http_receiver: Optional[HTTPConfig] = None
    last_sent: Optional[str] = None
    receiver_state: Optional[str] = None
    s3_receiver: Optional[S3Config] = None
    splunk_receiver: Optional[SplunkConfig] = None


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
    """Replaces the content of an Data Delivery object"""

    azure_receiver: Optional[AzureBlobConfig] = None
    datadog_receiver: Optional[DatadogConfig] = None
    dataset_type: Optional[str] = None
    gcp_bucket_receiver: Optional[GCPBucketConfig] = None
    http_receiver: Optional[HTTPConfig] = None
    s3_receiver: Optional[S3Config] = None
    splunk_receiver: Optional[SplunkConfig] = None


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


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of receiver is returned in 'List'. By setting..."""

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
