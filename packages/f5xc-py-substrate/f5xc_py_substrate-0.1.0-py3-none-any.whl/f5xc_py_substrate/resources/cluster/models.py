"""Pydantic models for cluster."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ClusterListItem(F5XCBaseModel):
    """List item for cluster resources."""


class CircuitBreaker(F5XCBaseModel):
    """CircuitBreaker provides a mechanism for watching failures in upstream..."""

    connection_limit: Optional[int] = None
    max_requests: Optional[int] = None
    pending_requests: Optional[int] = None
    priority: Optional[Literal['DEFAULT', 'HIGH']] = None
    retries: Optional[int] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class EndpointSubsetSelectorType(F5XCBaseModel):
    """Upstream cluster may be configured to divide its endpoints into subsets..."""

    keys: Optional[list[str]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class HeaderTransformationType(F5XCBaseModel):
    """Header Transformation options for HTTP/1.1 request/response headers"""

    default_header_transformation: Optional[Any] = None
    legacy_header_transformation: Optional[Any] = None
    preserve_case_header_transformation: Optional[Any] = None
    proper_case_header_transformation: Optional[Any] = None


class Http1ProtocolOptions(F5XCBaseModel):
    """HTTP/1.1 Protocol options for upstream connections"""

    header_transformation: Optional[HeaderTransformationType] = None


class Http2ProtocolOptions(F5XCBaseModel):
    """Http2 Protocol options for upstream connections"""

    enabled: Optional[bool] = None


class OutlierDetectionType(F5XCBaseModel):
    """Outlier detection and ejection is the process of dynamically determining..."""

    base_ejection_time: Optional[int] = None
    consecutive_5xx: Optional[int] = None
    consecutive_gateway_failure: Optional[int] = None
    interval: Optional[int] = None
    max_ejection_percent: Optional[int] = None


class TrustedCAList(F5XCBaseModel):
    """Reference to Root CA Certificate"""

    trusted_ca_list: Optional[list[ObjectRefType]] = None


class TlsValidationParamsType(F5XCBaseModel):
    """This includes URL for a trust store, whether SAN verification is..."""

    skip_hostname_verification: Optional[bool] = None
    trusted_ca: Optional[TrustedCAList] = None
    trusted_ca_url: Optional[str] = None
    verify_subject_alt_names: Optional[list[str]] = None


class UpstreamCertificateParamsType(F5XCBaseModel):
    """Certificate Parameters for authentication, TLS ciphers, and trust store"""

    certificates: Optional[list[ObjectRefType]] = None
    cipher_suites: Optional[list[str]] = None
    maximum_protocol_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    minimum_protocol_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    validation_params: Optional[TlsValidationParamsType] = None


class HashAlgorithms(F5XCBaseModel):
    """Specifies the hash algorithms to be used"""

    hash_algorithms: Optional[list[Literal['INVALID_HASH_ALGORITHM', 'SHA256', 'SHA1']]] = None


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


class TlsCertificateType(F5XCBaseModel):
    """Handle to fetch certificate and key"""

    certificate_url: Optional[str] = None
    custom_hash_algorithms: Optional[HashAlgorithms] = None
    description: Optional[str] = None
    disable_ocsp_stapling: Optional[Any] = None
    private_key: Optional[SecretType] = None
    use_system_defaults: Optional[Any] = None


class TlsParamsType(F5XCBaseModel):
    """Information of different aspects for TLS authentication related to..."""

    cipher_suites: Optional[list[str]] = None
    maximum_protocol_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    minimum_protocol_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    tls_certificates: Optional[list[TlsCertificateType]] = None
    validation_params: Optional[TlsValidationParamsType] = None


class UpstreamTlsParamsType(F5XCBaseModel):
    """TLS configuration for upstream connections"""

    cert_params: Optional[UpstreamCertificateParamsType] = None
    common_params: Optional[TlsParamsType] = None
    default_session_key_caching: Optional[Any] = None
    disable_session_key_caching: Optional[Any] = None
    disable_sni: Optional[Any] = None
    max_session_keys: Optional[int] = None
    sni: Optional[str] = None
    use_host_header_as_sni: Optional[Any] = None


class UpstreamConnPoolReuseType(F5XCBaseModel):
    """Select upstream connection pool reuse state for every downstream..."""

    disable_conn_pool_reuse: Optional[Any] = None
    enable_conn_pool_reuse: Optional[Any] = None


class CreateSpecType(F5XCBaseModel):
    """Create cluster will create the object in the storage backend for..."""

    auto_http_config: Optional[Any] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    connection_timeout: Optional[int] = None
    default_subset: Optional[dict[str, Any]] = None
    disable_proxy_protocol: Optional[Any] = None
    endpoint_selection: Optional[Literal['DISTRIBUTED', 'LOCAL_ONLY', 'LOCAL_PREFERRED']] = None
    endpoint_subsets: Optional[list[EndpointSubsetSelectorType]] = None
    endpoints: Optional[list[ObjectRefType]] = None
    fallback_policy: Optional[Literal['NO_FALLBACK', 'ANY_ENDPOINT', 'DEFAULT_SUBSET']] = None
    health_checks: Optional[list[ObjectRefType]] = None
    http1_config: Optional[Http1ProtocolOptions] = None
    http2_options: Optional[Http2ProtocolOptions] = None
    http_idle_timeout: Optional[int] = None
    loadbalancer_algorithm: Optional[Literal['ROUND_ROBIN', 'LEAST_REQUEST', 'RING_HASH', 'RANDOM', 'LB_OVERRIDE']] = None
    no_panic_threshold: Optional[Any] = None
    outlier_detection: Optional[OutlierDetectionType] = None
    panic_threshold: Optional[int] = None
    proxy_protocol_v1: Optional[Any] = None
    proxy_protocol_v2: Optional[Any] = None
    tls_parameters: Optional[UpstreamTlsParamsType] = None
    upstream_conn_pool_reuse_type: Optional[UpstreamConnPoolReuseType] = None


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
    """Get cluster will get the object from the storage backend for namespace..."""

    auto_http_config: Optional[Any] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    connection_timeout: Optional[int] = None
    default_subset: Optional[dict[str, Any]] = None
    disable_lb_source_ip_persistance: Optional[Any] = None
    disable_proxy_protocol: Optional[Any] = None
    enable_lb_source_ip_persistance: Optional[Any] = None
    endpoint_selection: Optional[Literal['DISTRIBUTED', 'LOCAL_ONLY', 'LOCAL_PREFERRED']] = None
    endpoint_subsets: Optional[list[EndpointSubsetSelectorType]] = None
    endpoints: Optional[list[ObjectRefType]] = None
    fallback_policy: Optional[Literal['NO_FALLBACK', 'ANY_ENDPOINT', 'DEFAULT_SUBSET']] = None
    health_checks: Optional[list[ObjectRefType]] = None
    http1_config: Optional[Http1ProtocolOptions] = None
    http2_options: Optional[Http2ProtocolOptions] = None
    http_idle_timeout: Optional[int] = None
    loadbalancer_algorithm: Optional[Literal['ROUND_ROBIN', 'LEAST_REQUEST', 'RING_HASH', 'RANDOM', 'LB_OVERRIDE']] = None
    no_panic_threshold: Optional[Any] = None
    outlier_detection: Optional[OutlierDetectionType] = None
    panic_threshold: Optional[int] = None
    proxy_protocol_v1: Optional[Any] = None
    proxy_protocol_v2: Optional[Any] = None
    tls_parameters: Optional[UpstreamTlsParamsType] = None
    upstream_conn_pool_reuse_type: Optional[UpstreamConnPoolReuseType] = None


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
    """Replacing an cluster object will update the object by replacing the..."""

    auto_http_config: Optional[Any] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    connection_timeout: Optional[int] = None
    default_subset: Optional[dict[str, Any]] = None
    disable_proxy_protocol: Optional[Any] = None
    endpoint_selection: Optional[Literal['DISTRIBUTED', 'LOCAL_ONLY', 'LOCAL_PREFERRED']] = None
    endpoint_subsets: Optional[list[EndpointSubsetSelectorType]] = None
    endpoints: Optional[list[ObjectRefType]] = None
    fallback_policy: Optional[Literal['NO_FALLBACK', 'ANY_ENDPOINT', 'DEFAULT_SUBSET']] = None
    health_checks: Optional[list[ObjectRefType]] = None
    http1_config: Optional[Http1ProtocolOptions] = None
    http2_options: Optional[Http2ProtocolOptions] = None
    http_idle_timeout: Optional[int] = None
    loadbalancer_algorithm: Optional[Literal['ROUND_ROBIN', 'LEAST_REQUEST', 'RING_HASH', 'RANDOM', 'LB_OVERRIDE']] = None
    no_panic_threshold: Optional[Any] = None
    outlier_detection: Optional[OutlierDetectionType] = None
    panic_threshold: Optional[int] = None
    proxy_protocol_v1: Optional[Any] = None
    proxy_protocol_v2: Optional[Any] = None
    tls_parameters: Optional[UpstreamTlsParamsType] = None
    upstream_conn_pool_reuse_type: Optional[UpstreamConnPoolReuseType] = None


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
    """By default a summary of cluster is returned in 'List'. By setting..."""

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
