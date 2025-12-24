"""Pydantic models for workload."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class WorkloadListItem(F5XCBaseModel):
    """List item for workload resources."""


class ProxyTypeHttp(F5XCBaseModel):
    """Choice for selecting HTTP proxy"""

    dns_volterra_managed: Optional[bool] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class TLSCoalescingOptions(F5XCBaseModel):
    """TLS connection coalescing configuration (not compatible with mTLS)"""

    default_coalescing: Optional[Any] = None
    strict_coalescing: Optional[Any] = None


class HeaderTransformationType(F5XCBaseModel):
    """Header Transformation options for HTTP/1.1 request/response headers"""

    default_header_transformation: Optional[Any] = None
    legacy_header_transformation: Optional[Any] = None
    preserve_case_header_transformation: Optional[Any] = None
    proper_case_header_transformation: Optional[Any] = None


class Http1ProtocolOptions(F5XCBaseModel):
    """HTTP/1.1 Protocol options for downstream connections"""

    header_transformation: Optional[HeaderTransformationType] = None


class HttpProtocolOptions(F5XCBaseModel):
    """HTTP protocol configuration options for downstream connections"""

    http_protocol_enable_v1_only: Optional[Http1ProtocolOptions] = None
    http_protocol_enable_v1_v2: Optional[Any] = None
    http_protocol_enable_v2_only: Optional[Any] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


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


class DownstreamTLSCertsParams(F5XCBaseModel):
    """Select TLS Parameters and Certificates"""

    certificates: Optional[list[ObjectRefType]] = None
    no_mtls: Optional[Any] = None
    tls_config: Optional[TlsConfig] = None
    use_mtls: Optional[DownstreamTlsValidationContext] = None


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


class DownstreamTlsParamsType(F5XCBaseModel):
    """Inline TLS parameters"""

    no_mtls: Optional[Any] = None
    tls_certificates: Optional[list[TlsCertificateType]] = None
    tls_config: Optional[TlsConfig] = None
    use_mtls: Optional[DownstreamTlsValidationContext] = None


class ProxyTypeHttps(F5XCBaseModel):
    """Choice for selecting HTTP proxy with bring your own certificates"""

    add_hsts: Optional[bool] = None
    append_server_name: Optional[str] = None
    coalescing_options: Optional[TLSCoalescingOptions] = None
    connection_idle_timeout: Optional[int] = None
    default_header: Optional[Any] = None
    default_loadbalancer: Optional[Any] = None
    disable_path_normalize: Optional[Any] = None
    enable_path_normalize: Optional[Any] = None
    http_protocol_options: Optional[HttpProtocolOptions] = None
    http_redirect: Optional[bool] = None
    non_default_loadbalancer: Optional[Any] = None
    pass_through: Optional[Any] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None
    server_name: Optional[str] = None
    tls_cert_params: Optional[DownstreamTLSCertsParams] = None
    tls_parameters: Optional[DownstreamTlsParamsType] = None


class ProxyTypeHttpsAutoCerts(F5XCBaseModel):
    """Choice for selecting HTTP proxy with bring your own certificates"""

    add_hsts: Optional[bool] = None
    append_server_name: Optional[str] = None
    coalescing_options: Optional[TLSCoalescingOptions] = None
    connection_idle_timeout: Optional[int] = None
    default_header: Optional[Any] = None
    default_loadbalancer: Optional[Any] = None
    disable_path_normalize: Optional[Any] = None
    enable_path_normalize: Optional[Any] = None
    http_protocol_options: Optional[HttpProtocolOptions] = None
    http_redirect: Optional[bool] = None
    no_mtls: Optional[Any] = None
    non_default_loadbalancer: Optional[Any] = None
    pass_through: Optional[Any] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None
    server_name: Optional[str] = None
    tls_config: Optional[TlsConfig] = None
    use_mtls: Optional[DownstreamTlsValidationContext] = None


class RouteTypeCustomRoute(F5XCBaseModel):
    """A custom route uses a route object created outside of this view."""

    route_ref: Optional[ObjectRefType] = None


class HeaderMatcherType(F5XCBaseModel):
    """Header match is done using the name of the header and its value. The..."""

    exact: Optional[str] = None
    invert_match: Optional[bool] = None
    name: Optional[str] = None
    presence: Optional[bool] = None
    regex: Optional[str] = None


class PortMatcherType(F5XCBaseModel):
    """Port match of the request can be a range or a specific port"""

    no_port_match: Optional[Any] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None


class PathMatcherType(F5XCBaseModel):
    """Path match of the URI can be either be, Prefix match or exact match or..."""

    path: Optional[str] = None
    prefix: Optional[str] = None
    regex: Optional[str] = None


class RouteDirectResponse(F5XCBaseModel):
    """Send this direct response in case of route match action is direct response"""

    response_body_encoded: Optional[str] = None
    response_code: Optional[int] = None


class RouteTypeDirectResponse(F5XCBaseModel):
    """A direct response route matches on path, incoming header, incoming port..."""

    headers: Optional[list[HeaderMatcherType]] = None
    http_method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    incoming_port: Optional[PortMatcherType] = None
    path: Optional[PathMatcherType] = None
    route_direct_response: Optional[RouteDirectResponse] = None


class RouteRedirect(F5XCBaseModel):
    """route redirect parameters when match action is redirect."""

    host_redirect: Optional[str] = None
    path_redirect: Optional[str] = None
    prefix_rewrite: Optional[str] = None
    proto_redirect: Optional[str] = None
    remove_all_params: Optional[Any] = None
    replace_params: Optional[str] = None
    response_code: Optional[int] = None
    retain_all_params: Optional[Any] = None


class RouteTypeRedirect(F5XCBaseModel):
    """A redirect route matches on path, incoming header, incoming port and/or..."""

    headers: Optional[list[HeaderMatcherType]] = None
    http_method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    incoming_port: Optional[PortMatcherType] = None
    path: Optional[PathMatcherType] = None
    route_redirect: Optional[RouteRedirect] = None


class RouteTypeSimpleWithDefaultOriginPool(F5XCBaseModel):
    """A simple route matches on path and/or HTTP method and forwards the..."""

    auto_host_rewrite: Optional[Any] = None
    disable_host_rewrite: Optional[Any] = None
    host_rewrite: Optional[str] = None
    http_method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    path: Optional[PathMatcherType] = None


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


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


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


class KubeRefType(F5XCBaseModel):
    """KubeRefType represents a reference to a Kubernetes (K8s) object"""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class TrendValue(F5XCBaseModel):
    """Trend value contains trend value, trend sentiment and trend calculation..."""

    description: Optional[str] = None
    previous_value: Optional[str] = None
    sentiment: Optional[Literal['TREND_SENTIMENT_NONE', 'TREND_SENTIMENT_POSITIVE', 'TREND_SENTIMENT_NEGATIVE']] = None
    value: Optional[str] = None


class MetricValue(F5XCBaseModel):
    """Metric data contains timestamp and the value."""

    timestamp: Optional[float] = None
    trend_value: Optional[TrendValue] = None
    value: Optional[str] = None


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


class WhereSite(F5XCBaseModel):
    """This defines a reference to a CE site along with network type and an..."""

    ip: Optional[str] = None
    network: Optional[Literal['SITE_NETWORK_INSIDE_AND_OUTSIDE', 'SITE_NETWORK_INSIDE', 'SITE_NETWORK_OUTSIDE', 'SITE_NETWORK_SERVICE', 'SITE_NETWORK_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_INSIDE_AND_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_IP_FABRIC']] = None
    site: Optional[ObjectRefType] = None


class WhereVK8SService(F5XCBaseModel):
    """This defines a reference to a RE site or virtual site where a load..."""

    site: Optional[ObjectRefType] = None
    virtual_site: Optional[ObjectRefType] = None


class WhereVirtualSite(F5XCBaseModel):
    """This defines a reference to a customer site virtual site along with..."""

    network: Optional[Literal['SITE_NETWORK_INSIDE_AND_OUTSIDE', 'SITE_NETWORK_INSIDE', 'SITE_NETWORK_OUTSIDE', 'SITE_NETWORK_SERVICE', 'SITE_NETWORK_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_INSIDE_AND_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_IP_FABRIC']] = None
    virtual_site: Optional[ObjectRefType] = None


class EnvironmentVariableType(F5XCBaseModel):
    """Environment Variable"""

    name: Optional[str] = None
    value: Optional[str] = None


class VolumeMountType(F5XCBaseModel):
    """Volume mount describes how volume is mounted inside a workload"""

    mode: Optional[Literal['VOLUME_MOUNT_READ_ONLY', 'VOLUME_MOUNT_READ_WRITE']] = None
    mount_path: Optional[str] = None
    sub_path: Optional[str] = None


class ConfigurationFileType(F5XCBaseModel):
    """Configuration File for the workload"""

    data: Optional[str] = None
    mount: Optional[VolumeMountType] = None
    name: Optional[str] = None
    volume_name: Optional[str] = None


class ConfigurationParameterType(F5XCBaseModel):
    """Configuration parameter for the workload"""

    env_var: Optional[EnvironmentVariableType] = None
    file: Optional[ConfigurationFileType] = None


class ConfigurationParametersType(F5XCBaseModel):
    """Configuration parameters of the workload"""

    parameters: Optional[list[ConfigurationParameterType]] = None


class ImageType(F5XCBaseModel):
    """ImageType configures the image to use, how to pull the image, and the..."""

    container_registry: Optional[ObjectRefType] = None
    name: Optional[str] = None
    public: Optional[Any] = None
    pull_policy: Optional[Literal['IMAGE_PULL_POLICY_DEFAULT', 'IMAGE_PULL_POLICY_IF_NOT_PRESENT', 'IMAGE_PULL_POLICY_ALWAYS', 'IMAGE_PULL_POLICY_NEVER']] = None


class ExecHealthCheckType(F5XCBaseModel):
    """ExecHealthCheckType describes a health check based on 'run in container'..."""

    command: Optional[list[str]] = None


class PortChoiceType(F5XCBaseModel):
    """Port"""

    name: Optional[str] = None
    num: Optional[int] = None


class HTTPHealthCheckType(F5XCBaseModel):
    """HTTPHealthCheckType describes a health check based on HTTP GET requests."""

    headers: Optional[dict[str, Any]] = None
    host_header: Optional[str] = None
    path: Optional[str] = None
    port: Optional[PortChoiceType] = None


class TCPHealthCheckType(F5XCBaseModel):
    """TCPHealthCheckType describes a health check based on opening a TCP connection"""

    port: Optional[PortChoiceType] = None


class HealthCheckType(F5XCBaseModel):
    """HealthCheckType describes a health check to be performed against a..."""

    exec_health_check: Optional[ExecHealthCheckType] = None
    healthy_threshold: Optional[int] = None
    http_health_check: Optional[HTTPHealthCheckType] = None
    initial_delay: Optional[int] = None
    interval: Optional[int] = None
    tcp_health_check: Optional[TCPHealthCheckType] = None
    timeout: Optional[int] = None
    unhealthy_threshold: Optional[int] = None


class ContainerType(F5XCBaseModel):
    """ContainerType configures the container information"""

    args: Optional[list[str]] = None
    command: Optional[list[str]] = None
    custom_flavor: Optional[ObjectRefType] = None
    default_flavor: Optional[Any] = None
    flavor: Optional[Literal['CONTAINER_FLAVOR_TYPE_TINY', 'CONTAINER_FLAVOR_TYPE_MEDIUM', 'CONTAINER_FLAVOR_TYPE_LARGE']] = None
    image: Optional[ImageType] = None
    init_container: Optional[bool] = None
    liveness_check: Optional[HealthCheckType] = None
    name: Optional[str] = None
    readiness_check: Optional[HealthCheckType] = None


class DeployCESiteType(F5XCBaseModel):
    """This defines a way to deploy a workload on specific Customer sites"""

    site: Optional[list[ObjectRefType]] = None


class DeployCEVirtualSiteType(F5XCBaseModel):
    """This defines a way to deploy a workload on specific Customer virtual sites"""

    virtual_site: Optional[list[ObjectRefType]] = None


class DeployRESiteType(F5XCBaseModel):
    """This defines a way to deploy a workload on specific Regional Edge sites"""

    site: Optional[list[ObjectRefType]] = None


class DeployREVirtualSiteType(F5XCBaseModel):
    """This defines a way to deploy a workload on specific Regional Edge virtual sites"""

    virtual_site: Optional[list[ObjectRefType]] = None


class DeployOptionsType(F5XCBaseModel):
    """Deploy Options are used to configure the workload deployment options"""

    all_res: Optional[Any] = None
    default_virtual_sites: Optional[Any] = None
    deploy_ce_sites: Optional[DeployCESiteType] = None
    deploy_ce_virtual_sites: Optional[DeployCEVirtualSiteType] = None
    deploy_re_sites: Optional[DeployRESiteType] = None
    deploy_re_virtual_sites: Optional[DeployREVirtualSiteType] = None


class EmptyDirectoryVolumeType(F5XCBaseModel):
    """Volume containing a temporary directory whose lifetime is the same as a..."""

    mount: Optional[VolumeMountType] = None
    size_limit: Optional[float] = None


class HostPathVolumeType(F5XCBaseModel):
    """Volume containing a host mapped path into the workload"""

    mount: Optional[VolumeMountType] = None
    path: Optional[str] = None


class PersistentStorageType(F5XCBaseModel):
    """Persistent storage configuration is used to configure Persistent Volume..."""

    access_mode: Optional[Literal['ACCESS_MODE_READ_WRITE_ONCE', 'ACCESS_MODE_READ_WRITE_MANY', 'ACCESS_MODE_READ_ONLY_MANY']] = None
    class_name: Optional[str] = None
    default: Optional[Any] = None
    storage_size: Optional[float] = None


class PersistentStorageVolumeType(F5XCBaseModel):
    """Volume containing the Persistent Storage for the workload"""

    mount: Optional[VolumeMountType] = None
    storage: Optional[PersistentStorageType] = None


class StorageVolumeType(F5XCBaseModel):
    """Storage volume configuration for the workload"""

    empty_dir: Optional[EmptyDirectoryVolumeType] = None
    host_path: Optional[HostPathVolumeType] = None
    name: Optional[str] = None
    persistent_volume: Optional[PersistentStorageVolumeType] = None


class JobType(F5XCBaseModel):
    """Jobs are used for running batch processing tasks and run to completion...."""

    configuration: Optional[ConfigurationParametersType] = None
    containers: Optional[list[ContainerType]] = None
    deploy_options: Optional[DeployOptionsType] = None
    num_replicas: Optional[int] = None
    volumes: Optional[list[StorageVolumeType]] = None


class AdvertiseWhereType(F5XCBaseModel):
    """This defines various options where a load balancer could be advertised"""

    site: Optional[WhereSite] = None
    virtual_site: Optional[WhereVirtualSite] = None
    vk8s_service: Optional[WhereVK8SService] = None


class MatchAllRouteType(F5XCBaseModel):
    """Default route matching all APIs"""

    auto_host_rewrite: Optional[Any] = None
    disable_host_rewrite: Optional[Any] = None
    host_rewrite: Optional[str] = None


class RouteInfoType(F5XCBaseModel):
    """This defines various options to define a route"""

    custom_route_object: Optional[RouteTypeCustomRoute] = None
    direct_response_route: Optional[RouteTypeDirectResponse] = None
    redirect_route: Optional[RouteTypeRedirect] = None
    simple_route: Optional[RouteTypeSimpleWithDefaultOriginPool] = None


class RouteType(F5XCBaseModel):
    """This defines various options to define a route"""

    routes: Optional[list[RouteInfoType]] = None


class HTTPLoadBalancerType(F5XCBaseModel):
    """ HTTP/HTTPS Load balancer"""

    default_route: Optional[MatchAllRouteType] = None
    domains: Optional[list[str]] = None
    http: Optional[ProxyTypeHttp] = None
    https: Optional[ProxyTypeHttps] = None
    https_auto_cert: Optional[ProxyTypeHttpsAutoCerts] = None
    specific_routes: Optional[RouteType] = None


class PortInfoType(F5XCBaseModel):
    """Port information"""

    port: Optional[int] = None
    protocol: Optional[Literal['PROTOCOL_TCP', 'PROTOCOL_HTTP', 'PROTOCOL_HTTP2', 'PROTOCOL_TLS_WITH_SNI', 'PROTOCOL_UDP']] = None
    same_as_port: Optional[Any] = None
    target_port: Optional[int] = None


class PortType(F5XCBaseModel):
    """Port of the workload"""

    info: Optional[PortInfoType] = None
    name: Optional[str] = None


class TCPLoadBalancerType(F5XCBaseModel):
    """TCP loadbalancer"""

    domains: Optional[list[str]] = None
    with_sni: Optional[bool] = None


class AdvertisePortType(F5XCBaseModel):
    """Advertise port"""

    http_loadbalancer: Optional[HTTPLoadBalancerType] = None
    port: Optional[PortType] = None
    tcp_loadbalancer: Optional[TCPLoadBalancerType] = None


class AdvertiseCustomType(F5XCBaseModel):
    """Advertise this workload via loadbalancer on specific sites"""

    advertise_where: Optional[list[AdvertiseWhereType]] = None
    ports: Optional[list[AdvertisePortType]] = None


class MultiPortType(F5XCBaseModel):
    """Multiple ports"""

    ports: Optional[list[PortType]] = None


class SinglePortType(F5XCBaseModel):
    """Single port"""

    info: Optional[PortInfoType] = None


class AdvertiseInClusterType(F5XCBaseModel):
    """Advertise the workload locally in-cluster"""

    multi_ports: Optional[MultiPortType] = None
    port: Optional[SinglePortType] = None


class AdvertiseMultiPortType(F5XCBaseModel):
    """Advertise multiple ports"""

    ports: Optional[list[AdvertisePortType]] = None


class AdvertiseSinglePortType(F5XCBaseModel):
    """Advertise single port"""

    http_loadbalancer: Optional[HTTPLoadBalancerType] = None
    port: Optional[SinglePortType] = None
    tcp_loadbalancer: Optional[TCPLoadBalancerType] = None


class AdvertisePublicType(F5XCBaseModel):
    """Advertise this workload via loadbalancer on Internet with default VIP"""

    multi_ports: Optional[AdvertiseMultiPortType] = None
    port: Optional[AdvertiseSinglePortType] = None


class AdvertiseOptionsType(F5XCBaseModel):
    """ Advertise options are used to configure how and where to advertise the..."""

    advertise_custom: Optional[AdvertiseCustomType] = None
    advertise_in_cluster: Optional[AdvertiseInClusterType] = None
    advertise_on_public: Optional[AdvertisePublicType] = None
    do_not_advertise: Optional[Any] = None


class ServiceType(F5XCBaseModel):
    """Service does not maintain per replica state, however it can be..."""

    advertise_options: Optional[AdvertiseOptionsType] = None
    configuration: Optional[ConfigurationParametersType] = None
    containers: Optional[list[ContainerType]] = None
    deploy_options: Optional[DeployOptionsType] = None
    num_replicas: Optional[int] = None
    scale_to_zero: Optional[Any] = None
    volumes: Optional[list[StorageVolumeType]] = None


class PersistentVolumeType(F5XCBaseModel):
    """Persistent storage volume configuration for the workload"""

    name: Optional[str] = None
    persistent_volume: Optional[PersistentStorageVolumeType] = None


class AdvertiseSimpleServiceType(F5XCBaseModel):
    """Advertise options for Simple Service"""

    domains: Optional[list[str]] = None
    service_port: Optional[int] = None


class SimpleServiceType(F5XCBaseModel):
    """SimpleService is a service having one container and one replica that is..."""

    configuration: Optional[ConfigurationParametersType] = None
    container: Optional[ContainerType] = None
    disabled: Optional[Any] = None
    do_not_advertise: Optional[Any] = None
    enabled: Optional[PersistentVolumeType] = None
    scale_to_zero: Optional[bool] = None
    simple_advertise: Optional[AdvertiseSimpleServiceType] = None


class EphemeralStorageVolumeType(F5XCBaseModel):
    """Ephemeral storage volume configuration for the workload"""

    empty_dir: Optional[EmptyDirectoryVolumeType] = None
    host_path: Optional[HostPathVolumeType] = None
    name: Optional[str] = None


class StatefulServiceType(F5XCBaseModel):
    """StatefulService maintains per replica state and each replica has its own..."""

    advertise_options: Optional[AdvertiseOptionsType] = None
    configuration: Optional[ConfigurationParametersType] = None
    containers: Optional[list[ContainerType]] = None
    deploy_options: Optional[DeployOptionsType] = None
    num_replicas: Optional[int] = None
    persistent_volumes: Optional[list[PersistentVolumeType]] = None
    scale_to_zero: Optional[Any] = None
    volumes: Optional[list[EphemeralStorageVolumeType]] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of Workload"""

    job: Optional[JobType] = None
    service: Optional[ServiceType] = None
    simple_service: Optional[SimpleServiceType] = None
    stateful_service: Optional[StatefulServiceType] = None


class GetSpecType(F5XCBaseModel):
    """Shape of Workload"""

    job: Optional[JobType] = None
    service: Optional[ServiceType] = None
    simple_service: Optional[SimpleServiceType] = None
    stateful_service: Optional[StatefulServiceType] = None


class ReplaceSpecType(F5XCBaseModel):
    """Shape of Workload"""

    job: Optional[JobType] = None
    service: Optional[ServiceType] = None
    simple_service: Optional[SimpleServiceType] = None
    stateful_service: Optional[StatefulServiceType] = None


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of the workload"""

    child_objects: Optional[list[KubeRefType]] = None
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


class ListResponseItem(F5XCBaseModel):
    """By default a summary of workload is returned in 'List'. By setting..."""

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


class UsageTypeData(F5XCBaseModel):
    """Usage Type Data contains key/value pair that uniquely identifies a..."""

    key: Optional[dict[str, Any]] = None
    value: Optional[list[MetricValue]] = None


class UsageData(F5XCBaseModel):
    """Usage data contains the usage type and the corresponding metric"""

    data: Optional[list[UsageTypeData]] = None
    type_: Optional[Literal['CPU_USAGE', 'MEMORY_USAGE', 'DISK_READS', 'DISK_WRITES']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None


class UsageRequest(F5XCBaseModel):
    """Request to get workload usage in the given namespace"""

    end_time: Optional[str] = None
    field_selector: Optional[list[Literal['CPU_USAGE', 'MEMORY_USAGE', 'DISK_READS', 'DISK_WRITES']]] = None
    filter: Optional[str] = None
    group_by: Optional[list[Literal['NAMESPACE', 'CONTAINER', 'POD', 'SITE', 'WORKLOAD']]] = None
    include_system_workloads: Optional[bool] = None
    namespace: Optional[str] = None
    range: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class UsageResponse(F5XCBaseModel):
    """Workload usage response"""

    data: Optional[list[UsageData]] = None
    step: Optional[str] = None


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
