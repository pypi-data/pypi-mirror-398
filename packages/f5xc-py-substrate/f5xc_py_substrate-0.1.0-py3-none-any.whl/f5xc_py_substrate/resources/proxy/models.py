"""Pydantic models for proxy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ProxyListItem(F5XCBaseModel):
    """List item for proxy resources."""


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class HttpBody(F5XCBaseModel):
    """Message that represents an arbitrary HTTP body. It should only be used..."""

    content_type: Optional[str] = None
    data: Optional[str] = None
    extensions: Optional[list[ProtobufAny]] = None


class BufferConfigType(F5XCBaseModel):
    """Some upstream applications are not capable of handling streamed data...."""

    disabled: Optional[bool] = None
    max_request_bytes: Optional[int] = None


class CompressionType(F5XCBaseModel):
    """Enables loadbalancer to compress dispatched data from an upstream..."""

    content_length: Optional[int] = None
    content_type: Optional[list[str]] = None
    disable_on_etag_header: Optional[bool] = None
    remove_accept_encoding_header: Optional[bool] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


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


class CookieValueOption(F5XCBaseModel):
    """Cookie name and value for cookie header"""

    name: Optional[str] = None
    overwrite: Optional[bool] = None
    secret_value: Optional[SecretType] = None
    value: Optional[str] = None


class HeaderManipulationOptionType(F5XCBaseModel):
    """HTTP header is a key-value pair. The name acts as key of HTTP header The..."""

    append: Optional[bool] = None
    name: Optional[str] = None
    secret_value: Optional[SecretType] = None
    value: Optional[str] = None


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


class AdvancedOptionsType(F5XCBaseModel):
    """This defines various options to define a route"""

    buffer_policy: Optional[BufferConfigType] = None
    compression_params: Optional[CompressionType] = None
    custom_errors: Optional[dict[str, Any]] = None
    disable_default_error_pages: Optional[bool] = None
    disable_path_normalize: Optional[Any] = None
    enable_path_normalize: Optional[Any] = None
    idle_timeout: Optional[int] = None
    max_request_header_size: Optional[int] = None
    request_cookies_to_add: Optional[list[CookieValueOption]] = None
    request_cookies_to_remove: Optional[list[str]] = None
    request_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    request_headers_to_remove: Optional[list[str]] = None
    response_cookies_to_add: Optional[list[SetCookieValueOption]] = None
    response_cookies_to_remove: Optional[list[str]] = None
    response_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    response_headers_to_remove: Optional[list[str]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class ActiveForwardProxyPoliciesType(F5XCBaseModel):
    """Ordered List of Forward Proxy Policies active"""

    forward_proxy_policies: Optional[list[ObjectRefType]] = None


class DynamicHttpProxyType(F5XCBaseModel):
    """Parameters for dynamic HTTP proxy"""

    more_option: Optional[AdvancedOptionsType] = None


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


class CustomCiphers(F5XCBaseModel):
    """This defines TLS protocol config including min/max versions and allowed ciphers"""

    cipher_suites: Optional[list[str]] = None
    max_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    min_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None


class TlsConfig(F5XCBaseModel):
    """This defines various options to configure TLS configuration parameters"""

    custom_security: Optional[CustomCiphers] = None
    default_security: Optional[Any] = None
    low_security: Optional[Any] = None
    medium_security: Optional[Any] = None


class XfccHeaderKeys(F5XCBaseModel):
    """X-Forwarded-Client-Cert header elements to be added to requests"""

    xfcc_header_elements: Optional[list[Literal['XFCC_NONE', 'XFCC_CERT', 'XFCC_CHAIN', 'XFCC_SUBJECT', 'XFCC_URI', 'XFCC_DNS']]] = None


class DownstreamTlsValidationContext(F5XCBaseModel):
    """Validation context for downstream client TLS connections"""

    client_certificate_optional: Optional[bool] = None
    crl: Optional[ObjectRefType] = None
    no_crl: Optional[Any] = None
    trusted_ca: Optional[ObjectRefType] = None
    trusted_ca_url: Optional[str] = None
    xfcc_disabled: Optional[Any] = None
    xfcc_options: Optional[XfccHeaderKeys] = None


class DownstreamTlsParamsType(F5XCBaseModel):
    """Inline TLS parameters"""

    no_mtls: Optional[Any] = None
    tls_certificates: Optional[list[TlsCertificateType]] = None
    tls_config: Optional[TlsConfig] = None
    use_mtls: Optional[DownstreamTlsValidationContext] = None


class DynamicHttpsProxyType(F5XCBaseModel):
    """Parameters for dynamic HTTPS proxy"""

    more_option: Optional[AdvancedOptionsType] = None
    tls_params: Optional[DownstreamTlsParamsType] = None


class DynamicSniProxyType(F5XCBaseModel):
    """Parameters for dynamic SNI proxy"""

    idle_timeout: Optional[int] = None


class DynamicProxyType(F5XCBaseModel):
    disable_dns_masquerade: Optional[Any] = None
    domains: Optional[list[str]] = None
    enable_dns_masquerade: Optional[Any] = None
    http_proxy: Optional[DynamicHttpProxyType] = None
    https_proxy: Optional[DynamicHttpsProxyType] = None
    sni_proxy: Optional[DynamicSniProxyType] = None


class HttpConnectProxyType(F5XCBaseModel):
    """Parameters for Http Connect Proxy"""

    enable_http: Optional[Any] = None
    more_option: Optional[AdvancedOptionsType] = None


class WhereSite(F5XCBaseModel):
    """This defines a reference to a CE site along with network type and an..."""

    ip: Optional[str] = None
    network: Optional[Literal['SITE_NETWORK_INSIDE_AND_OUTSIDE', 'SITE_NETWORK_INSIDE', 'SITE_NETWORK_OUTSIDE', 'SITE_NETWORK_SERVICE', 'SITE_NETWORK_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_INSIDE_AND_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_IP_FABRIC']] = None
    site: Optional[ObjectRefType] = None


class WhereVirtualSite(F5XCBaseModel):
    """This defines a reference to a customer site virtual site along with..."""

    network: Optional[Literal['SITE_NETWORK_INSIDE_AND_OUTSIDE', 'SITE_NETWORK_INSIDE', 'SITE_NETWORK_OUTSIDE', 'SITE_NETWORK_SERVICE', 'SITE_NETWORK_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_INSIDE_AND_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_IP_FABRIC']] = None
    virtual_site: Optional[ObjectRefType] = None


class WhereTypeSiteVsite(F5XCBaseModel):
    """This defines various options where a Loadbalancer could be advertised"""

    port: Optional[int] = None
    site: Optional[WhereSite] = None
    use_default_port: Optional[Any] = None
    virtual_site: Optional[WhereVirtualSite] = None


class AdvertiseSiteVsite(F5XCBaseModel):
    """This defines a way to advertise a VIP on specific sites"""

    advertise_where: Optional[list[WhereTypeSiteVsite]] = None


class DomainType(F5XCBaseModel):
    """Domains names"""

    exact_value: Optional[str] = None
    regex_value: Optional[str] = None
    suffix_value: Optional[str] = None


class TlsInterceptionRule(F5XCBaseModel):
    """x-required Rule to enable or disable TLS interception based on domain match"""

    disable_interception: Optional[Any] = None
    domain_match: Optional[DomainType] = None
    enable_interception: Optional[Any] = None


class TlsInterceptionPolicy(F5XCBaseModel):
    """Policy to enable or disable TLS interception."""

    interception_rules: Optional[list[TlsInterceptionRule]] = None


class TlsInterceptionType(F5XCBaseModel):
    """Configuration to enable TLS interception"""

    custom_certificate: Optional[TlsCertificateType] = None
    enable_for_all_domains: Optional[Any] = None
    policy: Optional[TlsInterceptionPolicy] = None
    trusted_ca_url: Optional[str] = None
    volterra_certificate: Optional[Any] = None
    volterra_trusted_ca: Optional[Any] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the TCP loadbalancer create specification"""

    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    connection_timeout: Optional[int] = None
    do_not_advertise: Optional[Any] = None
    dynamic_proxy: Optional[DynamicProxyType] = None
    http_proxy: Optional[HttpConnectProxyType] = None
    no_forward_proxy_policy: Optional[Any] = None
    no_interception: Optional[Any] = None
    site_local_inside_network: Optional[Any] = None
    site_local_network: Optional[Any] = None
    site_virtual_sites: Optional[AdvertiseSiteVsite] = None
    tls_intercept: Optional[TlsInterceptionType] = None


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
    """Shape of the TCP loadbalancer get specification"""

    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    connection_timeout: Optional[int] = None
    do_not_advertise: Optional[Any] = None
    dynamic_proxy: Optional[DynamicProxyType] = None
    http_proxy: Optional[HttpConnectProxyType] = None
    no_forward_proxy_policy: Optional[Any] = None
    no_interception: Optional[Any] = None
    site_local_inside_network: Optional[Any] = None
    site_local_network: Optional[Any] = None
    site_virtual_sites: Optional[AdvertiseSiteVsite] = None
    tls_intercept: Optional[TlsInterceptionType] = None


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
    """Shape of the TCP loadbalancer replace specification"""

    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    connection_timeout: Optional[int] = None
    do_not_advertise: Optional[Any] = None
    dynamic_proxy: Optional[DynamicProxyType] = None
    http_proxy: Optional[HttpConnectProxyType] = None
    no_forward_proxy_policy: Optional[Any] = None
    no_interception: Optional[Any] = None
    site_local_inside_network: Optional[Any] = None
    site_local_network: Optional[Any] = None
    site_virtual_sites: Optional[AdvertiseSiteVsite] = None
    tls_intercept: Optional[TlsInterceptionType] = None


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
    """By default a summary of proxy is returned in 'List'. By setting..."""

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
