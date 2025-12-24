"""Pydantic models for origin_pool."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class OriginPoolListItem(F5XCBaseModel):
    """List item for origin_pool resources."""


class CircuitBreaker(F5XCBaseModel):
    """CircuitBreaker provides a mechanism for watching failures in upstream..."""

    connection_limit: Optional[int] = None
    max_requests: Optional[int] = None
    pending_requests: Optional[int] = None
    priority: Optional[Literal['DEFAULT', 'HIGH']] = None
    retries: Optional[int] = None


class EndpointSubsetSelectorType(F5XCBaseModel):
    """Upstream cluster may be configured to divide its endpoints into subsets..."""

    keys: Optional[list[str]] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


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


class DefaultSubset(F5XCBaseModel):
    """Default Subset definition"""

    default_subset: Optional[dict[str, Any]] = None


class Subsets(F5XCBaseModel):
    """Configure subset options for origin pool"""

    any_endpoint: Optional[Any] = None
    default_subset: Optional[DefaultSubset] = None
    endpoint_subsets: Optional[list[EndpointSubsetSelectorType]] = None
    fail_request: Optional[Any] = None


class AdvancedOptions(F5XCBaseModel):
    """Configure Advanced options for origin pool"""

    auto_http_config: Optional[Any] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    connection_timeout: Optional[int] = None
    default_circuit_breaker: Optional[Any] = None
    disable_circuit_breaker: Optional[Any] = None
    disable_lb_source_ip_persistance: Optional[Any] = None
    disable_outlier_detection: Optional[Any] = None
    disable_proxy_protocol: Optional[Any] = None
    disable_subsets: Optional[Any] = None
    enable_lb_source_ip_persistance: Optional[Any] = None
    enable_subsets: Optional[Subsets] = None
    http1_config: Optional[Http1ProtocolOptions] = None
    http2_options: Optional[Http2ProtocolOptions] = None
    http_idle_timeout: Optional[int] = None
    no_panic_threshold: Optional[Any] = None
    outlier_detection: Optional[OutlierDetectionType] = None
    panic_threshold: Optional[int] = None
    proxy_protocol_v1: Optional[Any] = None
    proxy_protocol_v2: Optional[Any] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class OriginServerCBIPService(F5XCBaseModel):
    """Specify origin server with Classic BIG-IP Service (Virtual Server)"""

    service_name: Optional[str] = None


class SiteLocator(F5XCBaseModel):
    """This message defines a reference to a site or virtual site object"""

    site: Optional[ObjectRefType] = None
    virtual_site: Optional[ObjectRefType] = None


class PrefixStringListType(F5XCBaseModel):
    """x-example: '192.168.20.0/24' List of IPv4 prefixes that represent an endpoint"""

    prefixes: Optional[list[str]] = None


class SnatPoolConfiguration(F5XCBaseModel):
    """Snat Pool configuration"""

    no_snat_pool: Optional[Any] = None
    snat_pool: Optional[PrefixStringListType] = None


class OriginServerConsulService(F5XCBaseModel):
    """Specify origin server with Hashi Corp Consul service name and site information"""

    inside_network: Optional[Any] = None
    outside_network: Optional[Any] = None
    service_name: Optional[str] = None
    site_locator: Optional[SiteLocator] = None
    snat_pool: Optional[SnatPoolConfiguration] = None


class OriginServerCustomEndpoint(F5XCBaseModel):
    """Specify origin server with a reference to endpoint object"""

    endpoint: Optional[ObjectRefType] = None


class OriginServerK8SService(F5XCBaseModel):
    """Specify origin server with K8s service name and site information"""

    inside_network: Optional[Any] = None
    outside_network: Optional[Any] = None
    protocol: Optional[Literal['PROTOCOL_TCP', 'PROTOCOL_UDP']] = None
    service_name: Optional[str] = None
    site_locator: Optional[SiteLocator] = None
    snat_pool: Optional[SnatPoolConfiguration] = None
    vk8s_networks: Optional[Any] = None


class OriginServerPrivateIP(F5XCBaseModel):
    """Specify origin server with private or public IP address and site information"""

    inside_network: Optional[Any] = None
    ip: Optional[str] = None
    outside_network: Optional[Any] = None
    segment: Optional[ObjectRefType] = None
    site_locator: Optional[SiteLocator] = None
    snat_pool: Optional[SnatPoolConfiguration] = None


class OriginServerPrivateName(F5XCBaseModel):
    """Specify origin server with private or public DNS name and site information"""

    dns_name: Optional[str] = None
    inside_network: Optional[Any] = None
    outside_network: Optional[Any] = None
    refresh_interval: Optional[int] = None
    segment: Optional[ObjectRefType] = None
    site_locator: Optional[SiteLocator] = None
    snat_pool: Optional[SnatPoolConfiguration] = None


class OriginServerPublicIP(F5XCBaseModel):
    """Specify origin server with public IP address"""

    ip: Optional[str] = None


class OriginServerPublicName(F5XCBaseModel):
    """Specify origin server with public DNS name"""

    dns_name: Optional[str] = None
    refresh_interval: Optional[int] = None


class OriginServerVirtualNetworkIP(F5XCBaseModel):
    """Specify origin server with IP on Virtual Network"""

    ip: Optional[str] = None
    virtual_network: Optional[ObjectRefType] = None


class OriginServerVirtualNetworkName(F5XCBaseModel):
    """Specify origin server with DNS name on Virtual Network"""

    dns_name: Optional[str] = None
    private_network: Optional[ObjectRefType] = None


class OriginServerType(F5XCBaseModel):
    """Various options to specify origin server"""

    cbip_service: Optional[OriginServerCBIPService] = None
    consul_service: Optional[OriginServerConsulService] = None
    custom_endpoint_object: Optional[OriginServerCustomEndpoint] = None
    k8s_service: Optional[OriginServerK8SService] = None
    labels: Optional[dict[str, Any]] = None
    private_ip: Optional[OriginServerPrivateIP] = None
    private_name: Optional[OriginServerPrivateName] = None
    public_ip: Optional[OriginServerPublicIP] = None
    public_name: Optional[OriginServerPublicName] = None
    vn_private_ip: Optional[OriginServerVirtualNetworkIP] = None
    vn_private_name: Optional[OriginServerVirtualNetworkName] = None


class UpstreamConnPoolReuseType(F5XCBaseModel):
    """Select upstream connection pool reuse state for every downstream..."""

    disable_conn_pool_reuse: Optional[Any] = None
    enable_conn_pool_reuse: Optional[Any] = None


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


class TlsCertificatesType(F5XCBaseModel):
    """mTLS Client Certificate"""

    tls_certificates: Optional[list[TlsCertificateType]] = None


class UpstreamTlsValidationContext(F5XCBaseModel):
    """Upstream TLS Validation Context"""

    trusted_ca: Optional[ObjectRefType] = None
    trusted_ca_url: Optional[str] = None


class UpstreamTlsParameters(F5XCBaseModel):
    """Upstream TLS Parameters"""

    default_session_key_caching: Optional[Any] = None
    disable_session_key_caching: Optional[Any] = None
    disable_sni: Optional[Any] = None
    max_session_keys: Optional[int] = None
    no_mtls: Optional[Any] = None
    skip_server_verification: Optional[Any] = None
    sni: Optional[str] = None
    tls_config: Optional[TlsConfig] = None
    use_host_header_as_sni: Optional[Any] = None
    use_mtls: Optional[TlsCertificatesType] = None
    use_mtls_obj: Optional[ObjectRefType] = None
    use_server_verification: Optional[UpstreamTlsValidationContext] = None
    volterra_trusted_ca: Optional[Any] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the origin pool create specification"""

    advanced_options: Optional[AdvancedOptions] = None
    automatic_port: Optional[Any] = None
    endpoint_selection: Optional[Literal['DISTRIBUTED', 'LOCAL_ONLY', 'LOCAL_PREFERRED']] = None
    health_check_port: Optional[int] = None
    healthcheck: Optional[list[ObjectRefType]] = None
    lb_port: Optional[Any] = None
    loadbalancer_algorithm: Optional[Literal['ROUND_ROBIN', 'LEAST_REQUEST', 'RING_HASH', 'RANDOM', 'LB_OVERRIDE']] = None
    no_tls: Optional[Any] = None
    origin_servers: Optional[list[OriginServerType]] = None
    port: Optional[int] = None
    same_as_endpoint_port: Optional[Any] = None
    upstream_conn_pool_reuse_type: Optional[UpstreamConnPoolReuseType] = None
    use_tls: Optional[UpstreamTlsParameters] = None


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
    """Shape of the origin pool get specification"""

    advanced_options: Optional[AdvancedOptions] = None
    automatic_port: Optional[Any] = None
    endpoint_selection: Optional[Literal['DISTRIBUTED', 'LOCAL_ONLY', 'LOCAL_PREFERRED']] = None
    health_check_port: Optional[int] = None
    healthcheck: Optional[list[ObjectRefType]] = None
    lb_port: Optional[Any] = None
    loadbalancer_algorithm: Optional[Literal['ROUND_ROBIN', 'LEAST_REQUEST', 'RING_HASH', 'RANDOM', 'LB_OVERRIDE']] = None
    no_tls: Optional[Any] = None
    origin_servers: Optional[list[OriginServerType]] = None
    port: Optional[int] = None
    same_as_endpoint_port: Optional[Any] = None
    upstream_conn_pool_reuse_type: Optional[UpstreamConnPoolReuseType] = None
    use_tls: Optional[UpstreamTlsParameters] = None


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
    """Shape of the origin pool create specification"""

    advanced_options: Optional[AdvancedOptions] = None
    automatic_port: Optional[Any] = None
    endpoint_selection: Optional[Literal['DISTRIBUTED', 'LOCAL_ONLY', 'LOCAL_PREFERRED']] = None
    health_check_port: Optional[int] = None
    healthcheck: Optional[list[ObjectRefType]] = None
    lb_port: Optional[Any] = None
    loadbalancer_algorithm: Optional[Literal['ROUND_ROBIN', 'LEAST_REQUEST', 'RING_HASH', 'RANDOM', 'LB_OVERRIDE']] = None
    no_tls: Optional[Any] = None
    origin_servers: Optional[list[OriginServerType]] = None
    port: Optional[int] = None
    same_as_endpoint_port: Optional[Any] = None
    upstream_conn_pool_reuse_type: Optional[UpstreamConnPoolReuseType] = None
    use_tls: Optional[UpstreamTlsParameters] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


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
    """By default a summary of origin_pool is returned in 'List'. By setting..."""

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


class ReplaceResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
