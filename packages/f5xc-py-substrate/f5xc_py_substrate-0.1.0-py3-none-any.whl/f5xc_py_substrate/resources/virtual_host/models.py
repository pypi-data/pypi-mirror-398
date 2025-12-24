"""Pydantic models for virtual_host."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class VirtualHostListItem(F5XCBaseModel):
    """List item for virtual_host resources."""


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class HttpBody(F5XCBaseModel):
    """Message that represents an arbitrary HTTP body. It should only be used..."""

    content_type: Optional[str] = None
    data: Optional[str] = None
    extensions: Optional[list[ProtobufAny]] = None


class APIEPDynExample(F5XCBaseModel):
    """List of Examples of expanded URL components for API endpoints that are..."""

    component_examples: Optional[list[str]] = None
    component_identifier: Optional[str] = None


class AuthenticationTypeLocPair(F5XCBaseModel):
    """API Endpoint's Authentication Type and Location."""

    auth_type: Optional[str] = None
    location: Optional[Literal['AUTH_LOCATION_HEADER', 'AUTH_LOCATION_QUERY', 'AUTH_LOCATION_BODY', 'AUTH_LOCATION_COOKIE']] = None
    type_: Optional[Literal['AUTH_TYPE_BASIC', 'AUTH_TYPE_BEARER', 'AUTH_TYPE_JWT', 'AUTH_TYPE_API_KEY', 'AUTH_TYPE_OAUTH2', 'AUTH_TYPE_OPENID', 'AUTH_TYPE_HTTP', 'AUTH_TYPE_OAUTH1', 'AUTH_TYPE_DIGEST', 'AUTH_TYPE_NEGOTIATE']] = Field(default=None, alias="type")


class PDFSpec(F5XCBaseModel):
    """Probability Density point in (PDF(x)) of the metric. x is the value of..."""

    probability: Optional[float] = None
    x: Optional[float] = None


class PDFStat(F5XCBaseModel):
    """Probability Density Function statistics of the metric. pdf_mean is the..."""

    pdf_95: Optional[float] = None
    pdf_mean: Optional[float] = None


class APIEPPDFInfo(F5XCBaseModel):
    """Metrics supported currently are request_size response_size..."""

    creation_timestamp: Optional[str] = None
    error_rate: Optional[list[PDFSpec]] = None
    error_rate_stat: Optional[PDFStat] = None
    latency_no_data: Optional[list[PDFSpec]] = None
    latency_no_data_stat: Optional[PDFStat] = None
    latency_with_data: Optional[list[PDFSpec]] = None
    latency_with_data_stat: Optional[PDFStat] = None
    request_rate: Optional[list[PDFSpec]] = None
    request_rate_stat: Optional[PDFStat] = None
    request_size: Optional[list[PDFSpec]] = None
    request_size_stat: Optional[PDFStat] = None
    response_size: Optional[list[PDFSpec]] = None
    response_size_stat: Optional[PDFStat] = None
    response_throughput: Optional[list[PDFSpec]] = None
    response_throughput_stat: Optional[PDFStat] = None


class RiskScore(F5XCBaseModel):
    """Risk score of the vulnerabilities found for this API Endpoint."""

    score: Optional[float] = None
    severity: Optional[Literal['APIEP_SEC_RISK_NONE', 'APIEP_SEC_RISK_LOW', 'APIEP_SEC_RISK_MED', 'APIEP_SEC_RISK_HIGH', 'APIEP_SEC_RISK_CRITICAL']] = None


class APIEPInfo(F5XCBaseModel):
    """Information about automatically identified API endpoint Each identified..."""

    access_discovery_time: Optional[str] = None
    api_groups: Optional[list[str]] = None
    api_type: Optional[Literal['API_TYPE_UNKNOWN', 'API_TYPE_GRAPHQL', 'API_TYPE_REST', 'API_TYPE_GRPC']] = None
    attributes: Optional[list[str]] = None
    authentication_state: Optional[Literal['AUTH_STATE_UNKNOWN', 'AUTH_STATE_AUTHENTICATED', 'AUTH_STATE_UNAUTHENTICATED']] = None
    authentication_types: Optional[list[AuthenticationTypeLocPair]] = None
    avg_latency: Optional[float] = None
    base_path: Optional[str] = None
    category: Optional[list[Literal['APIEP_CATEGORY_DISCOVERED', 'APIEP_CATEGORY_SWAGGER', 'APIEP_CATEGORY_INVENTORY', 'APIEP_CATEGORY_SHADOW', 'APIEP_CATEGORY_DEPRECATED', 'APIEP_CATEGORY_NON_API']]] = None
    collapsed_url: Optional[str] = None
    compliances: Optional[list[str]] = None
    domains: Optional[list[str]] = None
    dyn_examples: Optional[list[APIEPDynExample]] = None
    engines: Optional[list[str]] = None
    err_rsp_count: Optional[str] = None
    has_learnt_schema: Optional[bool] = None
    last_tested: Optional[str] = None
    max_latency: Optional[float] = None
    method: Optional[str] = None
    pdf_info: Optional[APIEPPDFInfo] = None
    pii_level: Optional[Literal['APIEP_PII_NOT_DETECTED', 'APIEP_PII_DETECTED']] = None
    req_rate: Optional[float] = None
    request_percentage: Optional[float] = None
    requests_count: Optional[int] = None
    risk_score: Optional[RiskScore] = None
    schema_status: Optional[str] = None
    sec_events_count: Optional[int] = None
    security_risk: Optional[Literal['APIEP_SEC_RISK_NONE', 'APIEP_SEC_RISK_LOW', 'APIEP_SEC_RISK_MED', 'APIEP_SEC_RISK_HIGH', 'APIEP_SEC_RISK_CRITICAL']] = None
    sensitive_data: Optional[list[Literal['SENSITIVE_DATA_TYPE_CCN', 'SENSITIVE_DATA_TYPE_SSN', 'SENSITIVE_DATA_TYPE_IP', 'SENSITIVE_DATA_TYPE_EMAIL', 'SENSITIVE_DATA_TYPE_PHONE', 'SENSITIVE_DATA_TYPE_CREDENTIALS', 'SENSITIVE_DATA_TYPE_APP_INFO_LEAKAGE', 'SENSITIVE_DATA_TYPE_MASKED_PII', 'SENSITIVE_DATA_TYPE_LOCATION']]] = None
    sensitive_data_location: Optional[list[str]] = None
    sensitive_data_types: Optional[list[str]] = None


class Authentication(F5XCBaseModel):
    """Authentication details for a given API endpoint."""

    auth_data_per_definition: Optional[dict[str, Any]] = None


class SchemaStruct(F5XCBaseModel):
    """Schema structure for a given API endpoint."""

    examples: Optional[list[str]] = None
    schema_: Optional[str] = Field(default=None, alias="schema")


class RequestSchema(F5XCBaseModel):
    """Request schema for a given API endpoint."""

    body_per_content_type: Optional[dict[str, Any]] = None
    cookies: Optional[SchemaStruct] = None
    headers: Optional[SchemaStruct] = None
    query_params: Optional[SchemaStruct] = None


class DiscoveredSchema(F5XCBaseModel):
    """Discovery schema for request API endpoint."""

    last_updated_time: Optional[str] = None
    request_schema: Optional[RequestSchema] = None
    response_schema_per_rsp_code: Optional[dict[str, Any]] = None


class SensitiveData(F5XCBaseModel):
    """Sensitive data for a given API endpoint."""

    compliances: Optional[list[str]] = None
    examples: Optional[list[str]] = None
    field: Optional[str] = None
    rule_type: Optional[Literal['RULE_TYPE_BUILT_IN', 'RULE_TYPE_CUSTOM']] = None
    section: Optional[str] = None
    sensitive_data_type: Optional[str] = None
    type_: Optional[Literal['SENSITIVE_DATA_TYPE_CCN', 'SENSITIVE_DATA_TYPE_SSN', 'SENSITIVE_DATA_TYPE_IP', 'SENSITIVE_DATA_TYPE_EMAIL', 'SENSITIVE_DATA_TYPE_PHONE', 'SENSITIVE_DATA_TYPE_CREDENTIALS', 'SENSITIVE_DATA_TYPE_APP_INFO_LEAKAGE', 'SENSITIVE_DATA_TYPE_MASKED_PII', 'SENSITIVE_DATA_TYPE_LOCATION']] = Field(default=None, alias="type")


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


class HMACKeyPair(F5XCBaseModel):
    """HMAC primary and secondary keys to be used for hashing the Cookie. Each..."""

    prim_key: Optional[SecretType] = None
    prim_key_expiry: Optional[str] = None
    sec_key: Optional[SecretType] = None
    sec_key_expiry: Optional[str] = None


class KMSKeyRefType(F5XCBaseModel):
    """Reference to KMS Key Object"""

    pass


class CookieParams(F5XCBaseModel):
    """Specifies different cookie related config parameters for authentication"""

    auth_hmac: Optional[HMACKeyPair] = None
    cookie_expiry: Optional[int] = None
    cookie_refresh_interval: Optional[int] = None
    kms_key_hmac: Optional[Any] = None
    session_expiry: Optional[int] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class HashAlgorithms(F5XCBaseModel):
    """Specifies the hash algorithms to be used"""

    hash_algorithms: Optional[list[Literal['INVALID_HASH_ALGORITHM', 'SHA256', 'SHA1']]] = None


class TlsCertificateType(F5XCBaseModel):
    """Handle to fetch certificate and key"""

    certificate_url: Optional[str] = None
    custom_hash_algorithms: Optional[HashAlgorithms] = None
    description: Optional[str] = None
    disable_ocsp_stapling: Optional[Any] = None
    private_key: Optional[SecretType] = None
    use_system_defaults: Optional[Any] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class TrustedCAList(F5XCBaseModel):
    """Reference to Root CA Certificate"""

    trusted_ca_list: Optional[list[ObjectRefType]] = None


class TlsValidationParamsType(F5XCBaseModel):
    """This includes URL for a trust store, whether SAN verification is..."""

    skip_hostname_verification: Optional[bool] = None
    trusted_ca: Optional[TrustedCAList] = None
    trusted_ca_url: Optional[str] = None
    verify_subject_alt_names: Optional[list[str]] = None


class TlsParamsType(F5XCBaseModel):
    """Information of different aspects for TLS authentication related to..."""

    cipher_suites: Optional[list[str]] = None
    maximum_protocol_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    minimum_protocol_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    tls_certificates: Optional[list[TlsCertificateType]] = None
    validation_params: Optional[TlsValidationParamsType] = None


class DownstreamTlsParamsType(F5XCBaseModel):
    """TLS configuration for downstream connections"""

    client_certificate_optional: Optional[Any] = None
    client_certificate_required: Optional[Any] = None
    common_params: Optional[TlsParamsType] = None
    no_client_certificate: Optional[Any] = None
    xfcc_header_elements: Optional[list[Literal['XFCC_NONE', 'XFCC_CERT', 'XFCC_CHAIN', 'XFCC_SUBJECT', 'XFCC_URI', 'XFCC_DNS']]] = None


class AppFirewallRefType(F5XCBaseModel):
    """A list of references to the app_firewall configuration objects"""

    app_firewall: Optional[list[ObjectRefType]] = None


class BufferConfigType(F5XCBaseModel):
    """Some upstream applications are not capable of handling streamed data...."""

    disabled: Optional[bool] = None
    max_request_bytes: Optional[int] = None


class CertificateParamsType(F5XCBaseModel):
    """Certificate Parameters for authentication, TLS ciphers, and trust store"""

    certificates: Optional[list[ObjectRefType]] = None
    cipher_suites: Optional[list[str]] = None
    client_certificate_optional: Optional[Any] = None
    client_certificate_required: Optional[Any] = None
    maximum_protocol_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    minimum_protocol_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    no_client_certificate: Optional[Any] = None
    validation_params: Optional[TlsValidationParamsType] = None
    xfcc_header_elements: Optional[list[Literal['XFCC_NONE', 'XFCC_CERT', 'XFCC_CHAIN', 'XFCC_SUBJECT', 'XFCC_URI', 'XFCC_DNS']]] = None


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class CookieValueOption(F5XCBaseModel):
    """Cookie name and value for cookie header"""

    name: Optional[str] = None
    overwrite: Optional[bool] = None
    secret_value: Optional[SecretType] = None
    value: Optional[str] = None


class CorsPolicy(F5XCBaseModel):
    """Cross-Origin Resource Sharing requests configuration specified at..."""

    allow_credentials: Optional[bool] = None
    allow_headers: Optional[str] = None
    allow_methods: Optional[str] = None
    allow_origin: Optional[list[str]] = None
    allow_origin_regex: Optional[list[str]] = None
    disabled: Optional[bool] = None
    expose_headers: Optional[str] = None
    maximum_age: Optional[int] = None


class DomainNameList(F5XCBaseModel):
    """List of domain names used for Host header matching"""

    domains: Optional[list[str]] = None


class CsrfPolicy(F5XCBaseModel):
    """To mitigate CSRF attack , the policy checks where a request is coming..."""

    all_load_balancer_domains: Optional[Any] = None
    custom_domain_list: Optional[DomainNameList] = None
    disabled: Optional[Any] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class HeaderManipulationOptionType(F5XCBaseModel):
    """HTTP header is a key-value pair. The name acts as key of HTTP header The..."""

    append: Optional[bool] = None
    name: Optional[str] = None
    secret_value: Optional[SecretType] = None
    value: Optional[str] = None


class HeaderTransformationType(F5XCBaseModel):
    """Header Transformation options for HTTP/1.1 request/response headers"""

    default_header_transformation: Optional[Any] = None
    legacy_header_transformation: Optional[Any] = None
    preserve_case_header_transformation: Optional[Any] = None
    proper_case_header_transformation: Optional[Any] = None


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


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
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


class RetryBackOff(F5XCBaseModel):
    """Specifies parameters that control retry back off."""

    base_interval: Optional[int] = None
    max_interval: Optional[int] = None


class RetryPolicyType(F5XCBaseModel):
    """Retry policy configuration for route destination."""

    back_off: Optional[RetryBackOff] = None
    num_retries: Optional[int] = None
    per_try_timeout: Optional[int] = None
    retriable_status_codes: Optional[list[int]] = None
    retry_condition: Optional[list[str]] = None


class SetCookieValueOption(F5XCBaseModel):
    """Cookie name and its attribute values in set-cookie header"""

    add_domain: Optional[str] = None
    add_expiry: Optional[str] = None
    add_httponly: Optional[Any] = None
    add_partitioned: Optional[Any] = None
    add_path: Optional[str] = None
    add_secure: Optional[Any] = None
    ignore_domain: Optional[Any] = None
    ignore_expiry: Optional[Any] = None
    ignore_httponly: Optional[Any] = None
    ignore_max_age: Optional[Any] = None
    ignore_partitioned: Optional[Any] = None
    ignore_path: Optional[Any] = None
    ignore_samesite: Optional[Any] = None
    ignore_secure: Optional[Any] = None
    ignore_value: Optional[Any] = None
    max_age_value: Optional[int] = None
    name: Optional[str] = None
    overwrite: Optional[bool] = None
    samesite_lax: Optional[Any] = None
    samesite_none: Optional[Any] = None
    samesite_strict: Optional[Any] = None
    secret_value: Optional[SecretType] = None
    value: Optional[str] = None


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


class TLSCoalescingOptions(F5XCBaseModel):
    """TLS connection coalescing configuration (not compatible with mTLS)"""

    default_coalescing: Optional[Any] = None
    strict_coalescing: Optional[Any] = None


class WafType(F5XCBaseModel):
    """WAF instance will be pointing to an app_firewall object"""

    app_firewall: Optional[AppFirewallRefType] = None
    disable_waf: Optional[Any] = None
    inherit_waf: Optional[Any] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class APIEndpoint(F5XCBaseModel):
    """APIEndpoint Object."""

    collapsed_url: Optional[str] = None
    method: Optional[str] = None


class AuthenticationDetails(F5XCBaseModel):
    """Authentication related information. This allows to configure the URL to..."""

    auth_config: Optional[list[ObjectRefType]] = None
    cookie_params: Optional[CookieParams] = None
    redirect_dynamic: Optional[Any] = None
    redirect_url: Optional[str] = None
    use_auth_object_config: Optional[Any] = None


class CaptchaChallengeType(F5XCBaseModel):
    """ Enables loadbalancer to perform captcha challenge  Captcha challenge..."""

    cookie_expiry: Optional[int] = None
    custom_page: Optional[str] = None


class CompressionType(F5XCBaseModel):
    """Enables loadbalancer to compress dispatched data from an upstream..."""

    content_length: Optional[int] = None
    content_type: Optional[list[str]] = None
    disable_on_etag_header: Optional[bool] = None
    remove_accept_encoding_header: Optional[bool] = None


class DynamicReverseProxyType(F5XCBaseModel):
    """In this mode of proxy, virtual host will resolve the destination..."""

    connection_timeout: Optional[int] = None
    resolution_network: Optional[list[ObjectRefType]] = None
    resolution_network_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None
    resolve_endpoint_dynamically: Optional[bool] = None


class Http1ProtocolOptions(F5XCBaseModel):
    """HTTP/1.1 Protocol options for downstream connections"""

    header_transformation: Optional[HeaderTransformationType] = None


class HttpProtocolOptions(F5XCBaseModel):
    """HTTP protocol configuration options for downstream connections"""

    http_protocol_enable_v1_only: Optional[Http1ProtocolOptions] = None
    http_protocol_enable_v1_v2: Optional[Any] = None
    http_protocol_enable_v2_only: Optional[Any] = None


class JavascriptChallengeType(F5XCBaseModel):
    """ Enables loadbalancer to perform client browser compatibility test by..."""

    cookie_expiry: Optional[int] = None
    custom_page: Optional[str] = None
    js_script_delay: Optional[int] = None


class SlowDDoSMitigation(F5XCBaseModel):
    """'Slow and low' attacks tie up server resources, leaving none available..."""

    disable_request_timeout: Optional[Any] = None
    request_headers_timeout: Optional[int] = None
    request_timeout: Optional[int] = None


class CreateSpecType(F5XCBaseModel):
    """Creates virtual host in a given namespace."""

    add_location: Optional[bool] = None
    advertise_policies: Optional[list[ObjectRefType]] = None
    append_server_name: Optional[str] = None
    authentication: Optional[AuthenticationDetails] = None
    buffer_policy: Optional[BufferConfigType] = None
    captcha_challenge: Optional[CaptchaChallengeType] = None
    coalescing_options: Optional[TLSCoalescingOptions] = None
    compression_params: Optional[CompressionType] = None
    connection_idle_timeout: Optional[int] = None
    cors_policy: Optional[CorsPolicy] = None
    csrf_policy: Optional[CsrfPolicy] = None
    custom_errors: Optional[dict[str, Any]] = None
    default_header: Optional[Any] = None
    default_loadbalancer: Optional[Any] = None
    disable_default_error_pages: Optional[bool] = None
    disable_dns_resolve: Optional[bool] = None
    disable_path_normalize: Optional[Any] = None
    domains: Optional[list[str]] = None
    dynamic_reverse_proxy: Optional[DynamicReverseProxyType] = None
    enable_path_normalize: Optional[Any] = None
    http_protocol_options: Optional[HttpProtocolOptions] = None
    idle_timeout: Optional[int] = None
    js_challenge: Optional[JavascriptChallengeType] = None
    max_request_header_size: Optional[int] = None
    no_authentication: Optional[Any] = None
    no_challenge: Optional[Any] = None
    non_default_loadbalancer: Optional[Any] = None
    pass_through: Optional[Any] = None
    proxy: Optional[Literal['UDP_PROXY', 'SMA_PROXY', 'DNS_PROXY', 'ZTNA_PROXY', 'UZTNA_PROXY']] = None
    rate_limiter_allowed_prefixes: Optional[list[ObjectRefType]] = None
    request_cookies_to_add: Optional[list[CookieValueOption]] = None
    request_cookies_to_remove: Optional[list[str]] = None
    request_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    request_headers_to_remove: Optional[list[str]] = None
    response_cookies_to_add: Optional[list[SetCookieValueOption]] = None
    response_cookies_to_remove: Optional[list[str]] = None
    response_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    response_headers_to_remove: Optional[list[str]] = None
    retry_policy: Optional[RetryPolicyType] = None
    routes: Optional[list[ObjectRefType]] = None
    sensitive_data_policy: Optional[list[ObjectRefType]] = None
    server_name: Optional[str] = None
    slow_ddos_mitigation: Optional[SlowDDoSMitigation] = None
    tls_cert_params: Optional[CertificateParamsType] = None
    tls_parameters: Optional[DownstreamTlsParamsType] = None
    user_identification: Optional[list[ObjectRefType]] = None
    waf_type: Optional[WafType] = None


class DNSRecord(F5XCBaseModel):
    """Defines a DNS record"""

    name: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")
    value: Optional[str] = None


class AutoCertInfoType(F5XCBaseModel):
    """Information related to auto certificate"""

    auto_cert_expiry: Optional[str] = None
    auto_cert_issuer: Optional[str] = None
    auto_cert_state: Optional[Literal['AutoCertDisabled', 'DnsDomainVerification', 'AutoCertStarted', 'DomainChallengePending', 'DomainChallengeVerified', 'AutoCertFinalize', 'CertificateInvalid', 'CertificateValid', 'AutoCertNotApplicable', 'AutoCertRateLimited', 'AutoCertGenerationRetry', 'AutoCertError', 'PreDomainChallengePending', 'DomainChallengeStarted', 'AutoCertInitialize', 'AutoCertAccountRateLimited', 'AutoCertDomainRateLimited', 'CertificateExpired']] = None
    auto_cert_subject: Optional[str] = None
    dns_records: Optional[list[DNSRecord]] = None


class CdnServiceType(F5XCBaseModel):
    download_delivery: Optional[Any] = None
    live_streaming: Optional[Any] = None


class DnsInfo(F5XCBaseModel):
    """A message that contains DNS information for a given IP address"""

    ip_address: Optional[str] = None


class GetSpecType(F5XCBaseModel):
    """Get virtual host from a given namespace."""

    add_location: Optional[bool] = None
    advertise_policies: Optional[list[ObjectRefType]] = None
    append_server_name: Optional[str] = None
    authentication: Optional[AuthenticationDetails] = None
    auto_cert_error_msg: Optional[str] = None
    auto_cert_info: Optional[AutoCertInfoType] = None
    block: Optional[Any] = None
    buffer_policy: Optional[BufferConfigType] = None
    captcha_challenge: Optional[CaptchaChallengeType] = None
    cdn_service: Optional[CdnServiceType] = None
    coalescing_options: Optional[TLSCoalescingOptions] = None
    compression_params: Optional[CompressionType] = None
    connection_idle_timeout: Optional[int] = None
    cors_policy: Optional[CorsPolicy] = None
    csrf_policy: Optional[CsrfPolicy] = None
    custom_errors: Optional[dict[str, Any]] = None
    ddos_js_challenge: Optional[JavascriptChallengeType] = None
    default_header: Optional[Any] = None
    default_loadbalancer: Optional[Any] = None
    disable_default_error_pages: Optional[bool] = None
    disable_dns_resolve: Optional[bool] = None
    disable_path_normalize: Optional[Any] = None
    dns_info: Optional[list[DnsInfo]] = None
    domains: Optional[list[str]] = None
    dynamic_reverse_proxy: Optional[DynamicReverseProxyType] = None
    enable_path_normalize: Optional[Any] = None
    host_name: Optional[str] = None
    http_protocol_options: Optional[HttpProtocolOptions] = None
    idle_timeout: Optional[int] = None
    js_challenge: Optional[JavascriptChallengeType] = None
    l7_ddos_action_default: Optional[Any] = None
    l7_ddos_captcha_challenge: Optional[CaptchaChallengeType] = None
    max_request_header_size: Optional[int] = None
    no_authentication: Optional[Any] = None
    no_challenge: Optional[Any] = None
    non_default_loadbalancer: Optional[Any] = None
    not_ready: Optional[Any] = None
    pass_through: Optional[Any] = None
    proxy: Optional[Literal['UDP_PROXY', 'SMA_PROXY', 'DNS_PROXY', 'ZTNA_PROXY', 'UZTNA_PROXY']] = None
    rate_limiter_allowed_prefixes: Optional[list[ObjectRefType]] = None
    ready: Optional[Any] = None
    request_cookies_to_add: Optional[list[CookieValueOption]] = None
    request_cookies_to_remove: Optional[list[str]] = None
    request_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    request_headers_to_remove: Optional[list[str]] = None
    response_cookies_to_add: Optional[list[SetCookieValueOption]] = None
    response_cookies_to_remove: Optional[list[str]] = None
    response_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    response_headers_to_remove: Optional[list[str]] = None
    retry_policy: Optional[RetryPolicyType] = None
    routes: Optional[list[ObjectRefType]] = None
    sensitive_data_policy: Optional[list[ObjectRefType]] = None
    server_name: Optional[str] = None
    slow_ddos_mitigation: Optional[SlowDDoSMitigation] = None
    state: Optional[Literal['VIRTUAL_HOST_READY', 'VIRTUAL_HOST_PENDING_VERIFICATION', 'VIRTUAL_HOST_VERIFICATION_FAILED', 'VIRTUAL_HOST_PENDING_DNS_DELEGATION', 'VIRTUAL_HOST_PENDING_A_RECORD', 'VIRTUAL_HOST_DNS_A_RECORD_ADDED', 'VIRTUAL_HOST_INTERNET_NLB_PENDING_CREATION', 'VIRTUAL_HOST_INTERNET_NLB_CREATION_FAILED']] = None
    tls_cert_params: Optional[CertificateParamsType] = None
    tls_parameters: Optional[DownstreamTlsParamsType] = None
    type_: Optional[Literal['VIRTUAL_SERVICE', 'HTTP_LOAD_BALANCER', 'API_GATEWAY', 'TCP_LOAD_BALANCER', 'PROXY', 'CDN_LOAD_BALANCER', 'NGINX_SERVER', 'UDP_LOAD_BALANCER']] = Field(default=None, alias="type")
    user_identification: Optional[list[ObjectRefType]] = None
    waf_type: Optional[WafType] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace a given virtual host in a given namespace."""

    add_location: Optional[bool] = None
    advertise_policies: Optional[list[ObjectRefType]] = None
    append_server_name: Optional[str] = None
    authentication: Optional[AuthenticationDetails] = None
    buffer_policy: Optional[BufferConfigType] = None
    captcha_challenge: Optional[CaptchaChallengeType] = None
    coalescing_options: Optional[TLSCoalescingOptions] = None
    compression_params: Optional[CompressionType] = None
    connection_idle_timeout: Optional[int] = None
    cors_policy: Optional[CorsPolicy] = None
    csrf_policy: Optional[CsrfPolicy] = None
    custom_errors: Optional[dict[str, Any]] = None
    default_header: Optional[Any] = None
    default_loadbalancer: Optional[Any] = None
    disable_default_error_pages: Optional[bool] = None
    disable_dns_resolve: Optional[bool] = None
    disable_path_normalize: Optional[Any] = None
    domains: Optional[list[str]] = None
    dynamic_reverse_proxy: Optional[DynamicReverseProxyType] = None
    enable_path_normalize: Optional[Any] = None
    http_protocol_options: Optional[HttpProtocolOptions] = None
    idle_timeout: Optional[int] = None
    js_challenge: Optional[JavascriptChallengeType] = None
    max_request_header_size: Optional[int] = None
    no_authentication: Optional[Any] = None
    no_challenge: Optional[Any] = None
    non_default_loadbalancer: Optional[Any] = None
    pass_through: Optional[Any] = None
    proxy: Optional[Literal['UDP_PROXY', 'SMA_PROXY', 'DNS_PROXY', 'ZTNA_PROXY', 'UZTNA_PROXY']] = None
    rate_limiter_allowed_prefixes: Optional[list[ObjectRefType]] = None
    request_cookies_to_add: Optional[list[CookieValueOption]] = None
    request_cookies_to_remove: Optional[list[str]] = None
    request_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    request_headers_to_remove: Optional[list[str]] = None
    response_cookies_to_add: Optional[list[SetCookieValueOption]] = None
    response_cookies_to_remove: Optional[list[str]] = None
    response_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    response_headers_to_remove: Optional[list[str]] = None
    retry_policy: Optional[RetryPolicyType] = None
    routes: Optional[list[ObjectRefType]] = None
    sensitive_data_policy: Optional[list[ObjectRefType]] = None
    server_name: Optional[str] = None
    slow_ddos_mitigation: Optional[SlowDDoSMitigation] = None
    tls_cert_params: Optional[CertificateParamsType] = None
    tls_parameters: Optional[DownstreamTlsParamsType] = None
    user_identification: Optional[list[ObjectRefType]] = None
    waf_type: Optional[WafType] = None


class GlobalSpecType(F5XCBaseModel):
    """Shape of the virtual host DNS info global specification"""

    dns_info: Optional[list[DnsInfo]] = None
    host_name: Optional[str] = None
    virtual_host: Optional[list[ObjectRefType]] = None


class JiraIssueType(F5XCBaseModel):
    """Issue (ticket) type information that's specific to Jira - modeled after..."""

    avatar_id: Optional[str] = None
    icon_url: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None


class JiraProject(F5XCBaseModel):
    """Contains fields and information that are specific to Jira projects -..."""

    id_: Optional[str] = Field(default=None, alias="id")
    issue_types: Optional[list[JiraIssueType]] = None
    key: Optional[str] = None
    name: Optional[str] = None


class JiraIssueStatusCategory(F5XCBaseModel):
    """Status category information like color name and ID - modeled after the..."""

    color_name: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")


class JiraIssueStatus(F5XCBaseModel):
    """Issue status type information that's specific to Jira - modeled after..."""

    icon_url: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None
    status_category: Optional[JiraIssueStatusCategory] = None


class JiraIssueFields(F5XCBaseModel):
    """Contains fields and information that are specific to Jira issues..."""

    description: Optional[dict[str, Any]] = None
    issuetype: Optional[JiraIssueType] = None
    project: Optional[JiraProject] = None
    status: Optional[JiraIssueStatus] = None
    summary: Optional[str] = None


class JiraIssue(F5XCBaseModel):
    """Top level object representing a Jira issue (ticket) - modeled after the..."""

    fields: Optional[JiraIssueFields] = None
    id_: Optional[str] = Field(default=None, alias="id")
    key: Optional[str] = None


class ApiOperation(F5XCBaseModel):
    """API operation according to OpenAPI specification."""

    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    path: Optional[str] = None


class ApiEndpointWithSchema(F5XCBaseModel):
    """API endpoint and its schema"""

    api_operation: Optional[ApiOperation] = None
    schema_json_: Optional[str] = Field(default=None, alias="schema_json")


class APIEPActivityMetrics(F5XCBaseModel):
    """This represents the API endpoint's activity metrics."""

    apiep_url: Optional[str] = None
    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    top_by_metric_value: Optional[int] = None


class APIEPSourceOpenApiSchemaRsp(F5XCBaseModel):
    """shape of response to get API endpoint Open API Schema request for..."""

    api_specs: Optional[dict[str, Any]] = None


class APIEPSummaryFilter(F5XCBaseModel):
    """Filter object for summary block."""

    apiep_category: Optional[list[Literal['APIEP_CATEGORY_DISCOVERED', 'APIEP_CATEGORY_SWAGGER', 'APIEP_CATEGORY_INVENTORY', 'APIEP_CATEGORY_SHADOW', 'APIEP_CATEGORY_DEPRECATED', 'APIEP_CATEGORY_NON_API']]] = None
    domains: Optional[list[str]] = None
    end_time: Optional[str] = None
    start_time: Optional[str] = None


class APIEndpointLearntSchemaRsp(F5XCBaseModel):
    """shape of response to get req body schema for a given API endpoint."""

    api_specs: Optional[dict[str, Any]] = None
    authentication: Optional[Authentication] = None
    discovered_schema: Optional[DiscoveredSchema] = None
    inventory_openapi_spec: Optional[str] = None
    pdf_info: Optional[APIEPPDFInfo] = None
    sensitive_data: Optional[list[SensitiveData]] = None


class APIEndpointPDFRsp(F5XCBaseModel):
    """shape of response to get PDF for a given API endpoint."""

    pdf_info: Optional[APIEPPDFInfo] = None


class APIEndpointReq(F5XCBaseModel):
    """Request shape for GET API endpoint API"""

    api_endpoint_info_request: Optional[list[Literal['API_ENDPOINT_INFO_NONE', 'API_ENDPOINT_INFO_PDF_SPARKLINES']]] = None
    collapsed_url: Optional[str] = None
    domains: Optional[list[str]] = None
    method: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class APIEndpointRsp(F5XCBaseModel):
    """Response shape for GET API endpoint API."""

    apiep: Optional[APIEPInfo] = None


class APIEndpointsRsp(F5XCBaseModel):
    """Response shape for GET API endpoints API. It is list of API endpoints discovered"""

    apiep_list: Optional[list[APIEPInfo]] = None
    last_update: Optional[str] = None


class ApiEndpointsStatsRsp(F5XCBaseModel):
    """Response shape for GET API endpoints Stats."""

    discovered: Optional[int] = None
    inventory: Optional[int] = None
    pii_detected: Optional[int] = None
    shadow: Optional[int] = None
    total_endpoints: Optional[int] = None


class AssignAPIDefinitionReq(F5XCBaseModel):
    """Request form for Assign API Definition"""

    api_definition: Optional[ObjectRefType] = None
    create_new: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class AssignAPIDefinitionResp(F5XCBaseModel):
    """Response form for Assign API Definition"""

    pass


class CreateJiraIssueRequest(F5XCBaseModel):
    description: Optional[str] = None
    issue_type: Optional[str] = None
    project: Optional[str] = None
    summary: Optional[str] = None


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class CreateTicketRequest(F5XCBaseModel):
    jira_issue: Optional[CreateJiraIssueRequest] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    ticket_tracking_system: Optional[str] = None


class CreateTicketResponse(F5XCBaseModel):
    errors: Optional[list[ErrorType]] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class GetAPICallSummaryReq(F5XCBaseModel):
    """Request model for GetAPICallSummary API"""

    apiep_summary_filter: Optional[APIEPSummaryFilter] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class RequestCountPerResponseClass(F5XCBaseModel):
    """Request count per response class."""

    count: Optional[int] = None
    rsp_code_class: Optional[Literal['HTTP_RESPONSE_CODE_CLASS_UNKNOWN', 'HTTP_RESPONSE_CODE_CLASS_1XX', 'HTTP_RESPONSE_CODE_CLASS_2XX', 'HTTP_RESPONSE_CODE_CLASS_3XX', 'HTTP_RESPONSE_CODE_CLASS_4XX', 'HTTP_RESPONSE_CODE_CLASS_5XX']] = None


class GetAPICallSummaryRsp(F5XCBaseModel):
    """Response model for GetSensitiveDataSummaryRsp API."""

    request_count_per_rsp_code: Optional[list[RequestCountPerResponseClass]] = None
    total_calls: Optional[str] = None


class GetAPIEndpointsSchemaUpdatesReq(F5XCBaseModel):
    """Request shape for Get API Endpoints Schema Updates"""

    api_endpoints_filter: Optional[list[ApiOperation]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    query_type: Optional[Literal['API_INVENTORY_SCHEMA_FULL_RESPONSE', 'API_INVENTORY_SCHEMA_CURRENT', 'API_INVENTORY_SCHEMA_UPDATED']] = None


class GetAPIEndpointsSchemaUpdatesResp(F5XCBaseModel):
    """Response shape for Get API Endpoints Schema Updates"""

    api_endpoints_current_schemas: Optional[list[ApiEndpointWithSchema]] = None
    api_endpoints_updated_schemas: Optional[list[ApiEndpointWithSchema]] = None


class GetDnsInfoResponse(F5XCBaseModel):
    """Response for get-dns-info API"""

    dns_info: Optional[GlobalSpecType] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class VerStatusType(F5XCBaseModel):
    """This VER status is per site on which virtual host configuration is..."""

    advertise_policy: Optional[ObjectRefType] = None
    coalesced_vhosts: Optional[list[ObjectRefType]] = None
    non_coalesced_vhosts: Optional[list[ObjectRefType]] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    status: Optional[list[VerStatusType]] = None


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


class GetTopAPIEndpointsReq(F5XCBaseModel):
    """Request model for GetTopAPIEndpointsReq API"""

    apiep_summary_filter: Optional[APIEPSummaryFilter] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    top_by_metric: Optional[Literal['ACTIVITY_METRIC_TYPE_SEC_EVENTS_PERCENTAGE', 'ACTIVITY_METRIC_TYPE_REQ_PERCENTAGE']] = None
    topk: Optional[int] = None


class GetTopAPIEndpointsRsp(F5XCBaseModel):
    """Response model for GetTopAttackedAPIEndpoints API."""

    top_apieps: Optional[list[APIEPActivityMetrics]] = None


class GetTopSensitiveDataReq(F5XCBaseModel):
    """Request model for GetTopSensitiveDataReq API"""

    apiep_category: Optional[list[Literal['APIEP_CATEGORY_DISCOVERED', 'APIEP_CATEGORY_SWAGGER', 'APIEP_CATEGORY_INVENTORY', 'APIEP_CATEGORY_SHADOW', 'APIEP_CATEGORY_DEPRECATED', 'APIEP_CATEGORY_NON_API']]] = None
    domains: Optional[list[str]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    topk: Optional[int] = None


class SensitiveDataCount(F5XCBaseModel):
    """Response model for GetTopSensitiveDataRsp API."""

    count: Optional[int] = None
    sensitive_data_type: Optional[Literal['SENSITIVE_DATA_TYPE_CCN', 'SENSITIVE_DATA_TYPE_SSN', 'SENSITIVE_DATA_TYPE_IP', 'SENSITIVE_DATA_TYPE_EMAIL', 'SENSITIVE_DATA_TYPE_PHONE', 'SENSITIVE_DATA_TYPE_CREDENTIALS', 'SENSITIVE_DATA_TYPE_APP_INFO_LEAKAGE', 'SENSITIVE_DATA_TYPE_MASKED_PII', 'SENSITIVE_DATA_TYPE_LOCATION']] = None
    type_: Optional[str] = Field(default=None, alias="type")


class GetTopSensitiveDataRsp(F5XCBaseModel):
    """Response model for GetTopSensitiveDataRsp API."""

    top_sensitive_data: Optional[list[SensitiveDataCount]] = None


class GetVulnerabilitiesReq(F5XCBaseModel):
    """Request model for GetVulnerabilitiesReq API"""

    api_endpoint: Optional[APIEndpoint] = None
    domains: Optional[list[str]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class VulnEvidenceSample(F5XCBaseModel):
    """Vulnerability evidence sample due to which vulnerability was found"""

    details: Optional[list[str]] = None
    req_id: Optional[str] = None


class VulnEvidence(F5XCBaseModel):
    """Evidence of the vulnerability found."""

    end_time: Optional[str] = None
    evidence_type: Optional[Literal['EVIDENCE_TYPE_REQUESTS', 'EVIDENCE_TYPE_SEC_EVENTS', 'EVIDENCE_TYPE_SEC_INCIDENTS']] = None
    samples: Optional[list[VulnEvidenceSample]] = None
    start_time: Optional[str] = None


class VulnRisk(F5XCBaseModel):
    """Risk of the vulnerability found."""

    level: Optional[Literal['RISK_LEVEL_NONE', 'RISK_LEVEL_LOW', 'RISK_LEVEL_MED', 'RISK_LEVEL_HIGH', 'RISK_LEVEL_CRITICAL']] = None
    score: Optional[float] = None


class TicketDetails(F5XCBaseModel):
    """Ticket details from the ticket tracking system - JIRA, ServiceNow, etc."""

    external_link: Optional[str] = None
    jira_issue: Optional[JiraIssue] = None
    ticket_tracking_system_type: Optional[Literal['TYPE_UNKNOWN', 'TYPE_JIRA']] = None


class Vulnerability(F5XCBaseModel):
    """Vulnerability object."""

    category: Optional[str] = None
    context: Optional[Literal['CONTEXT_API_ENDPOINT', 'CONTEXT_API_BASEPATH', 'CONTEXT_API_DOMAIN']] = None
    creation_time: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    evidence: Optional[VulnEvidence] = None
    last_observed_time: Optional[str] = None
    remediation: Optional[list[str]] = None
    risk: Optional[VulnRisk] = None
    source: Optional[Literal['VULNERABILITY_SOURCE_UNSPECIFIED', 'VULNERABILITY_SOURCE_TRAFFIC_ANALYSIS', 'VULNERABILITY_SOURCE_API_TESTING']] = None
    status: Optional[Literal['STATUS_NONE', 'STATUS_OPEN', 'STATUS_IGNORE', 'STATUS_RESOLUTION_CONFIRMED', 'STATUS_UNDER_REVIEW']] = None
    status_change_time: Optional[str] = None
    ticket: Optional[TicketDetails] = None
    title: Optional[str] = None
    vuln_id: Optional[str] = None


class GetVulnerabilitiesRsp(F5XCBaseModel):
    """Response model for GetVulnerabilitiesRsp API."""

    vulnerabilities: Optional[list[Vulnerability]] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of virtual_host is returned in 'List'. By setting..."""

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


class UnlinkTicketsRequest(F5XCBaseModel):
    label_filter: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    ticket_uid: Optional[str] = None


class UnlinkTicketsResponse(F5XCBaseModel):
    errors: Optional[list[ErrorType]] = None


class UnmergeAPIEPSourceOpenApiSchemaReq(F5XCBaseModel):
    """Unmerge Source from endpoint"""

    discovery_source_type: Optional[Literal['MERGED', 'TRAFFIC', 'CRAWLER', 'CODE_SCAN']] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None
    namespace: Optional[str] = None


class UpdateAPIEndpointsSchemasReq(F5XCBaseModel):
    """Request shape for Update API Endpoints Schemas"""

    api_endpoints_schema_updates: Optional[list[ApiEndpointWithSchema]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class UpdateAPIEndpointsSchemasResp(F5XCBaseModel):
    """Response shape for Update API Endpoints With Newly Discovered Schema"""

    updated_api_endpoints: Optional[list[ApiOperation]] = None


class UpdateVulnerabilitiesStateReq(F5XCBaseModel):
    """Request model for UpdateVulnerabilitiesStateReq API"""

    api_endpoint: Optional[APIEndpoint] = None
    domain: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    vuln_id: Optional[str] = None
    vuln_state: Optional[Literal['STATUS_NONE', 'STATUS_OPEN', 'STATUS_IGNORE', 'STATUS_RESOLUTION_CONFIRMED', 'STATUS_UNDER_REVIEW']] = None


class UpdateVulnerabilitiesStateRsp(F5XCBaseModel):
    """Response model for UpdateVulnerabilitiesStateRsp API."""

    pass


# Convenience aliases
Spec = PDFSpec
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
Spec = GlobalSpecType
