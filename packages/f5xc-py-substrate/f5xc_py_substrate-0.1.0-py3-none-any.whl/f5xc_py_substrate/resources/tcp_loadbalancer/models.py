"""Pydantic models for tcp_loadbalancer."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class TcpLoadbalancerListItem(F5XCBaseModel):
    """List item for tcp_loadbalancer resources."""


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


class HashAlgorithms(F5XCBaseModel):
    """Specifies the hash algorithms to be used"""

    hash_algorithms: Optional[list[Literal['INVALID_HASH_ALGORITHM', 'SHA256', 'SHA1']]] = None


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


class SecretType(F5XCBaseModel):
    """SecretType is used in an object to indicate a sensitive/confidential field"""

    blindfold_secret_info: Optional[BlindfoldSecretInfoType] = None
    clear_secret_info: Optional[ClearSecretInfoType] = None


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


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


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


class DnsInfo(F5XCBaseModel):
    """A message that contains DNS information for a given IP address"""

    ip_address: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    """Shape of the virtual host DNS info global specification"""

    dns_info: Optional[list[DnsInfo]] = None
    host_name: Optional[str] = None
    virtual_host: Optional[list[ObjectRefType]] = None


class ServicePolicyList(F5XCBaseModel):
    """List of service policies."""

    policies: Optional[list[ObjectRefType]] = None


class AdvertisePublic(F5XCBaseModel):
    """This defines a way to advertise a load balancer on public. If optional..."""

    public_ip: Optional[ObjectRefType] = None


class WhereSite(F5XCBaseModel):
    """This defines a reference to a CE site along with network type and an..."""

    ip: Optional[str] = None
    network: Optional[Literal['SITE_NETWORK_INSIDE_AND_OUTSIDE', 'SITE_NETWORK_INSIDE', 'SITE_NETWORK_OUTSIDE', 'SITE_NETWORK_SERVICE', 'SITE_NETWORK_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_INSIDE_AND_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_IP_FABRIC']] = None
    site: Optional[ObjectRefType] = None


class WhereVirtualNetwork(F5XCBaseModel):
    """Parameters to advertise on a given virtual network"""

    default_v6_vip: Optional[Any] = None
    default_vip: Optional[Any] = None
    specific_v6_vip: Optional[str] = None
    specific_vip: Optional[str] = None
    virtual_network: Optional[ObjectRefType] = None


class WhereVirtualSite(F5XCBaseModel):
    """This defines a reference to a customer site virtual site along with..."""

    network: Optional[Literal['SITE_NETWORK_INSIDE_AND_OUTSIDE', 'SITE_NETWORK_INSIDE', 'SITE_NETWORK_OUTSIDE', 'SITE_NETWORK_SERVICE', 'SITE_NETWORK_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_INSIDE_AND_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_IP_FABRIC']] = None
    virtual_site: Optional[ObjectRefType] = None


class WhereVirtualSiteSpecifiedVIP(F5XCBaseModel):
    """This defines a reference to a customer site virtual site along with..."""

    ip: Optional[str] = None
    network: Optional[Literal['SITE_NETWORK_SPECIFIED_VIP_OUTSIDE', 'SITE_NETWORK_SPECIFIED_VIP_INSIDE']] = None
    virtual_site: Optional[ObjectRefType] = None


class WhereVK8SService(F5XCBaseModel):
    """This defines a reference to a RE site or virtual site where a load..."""

    site: Optional[ObjectRefType] = None
    virtual_site: Optional[ObjectRefType] = None


class WhereType(F5XCBaseModel):
    """This defines various options where a Loadbalancer could be advertised"""

    advertise_on_public: Optional[AdvertisePublic] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None
    site: Optional[WhereSite] = None
    use_default_port: Optional[Any] = None
    virtual_network: Optional[WhereVirtualNetwork] = None
    virtual_site: Optional[WhereVirtualSite] = None
    virtual_site_with_vip: Optional[WhereVirtualSiteSpecifiedVIP] = None
    vk8s_service: Optional[WhereVK8SService] = None


class AdvertiseCustom(F5XCBaseModel):
    """This defines a way to advertise a VIP on specific sites"""

    advertise_where: Optional[list[WhereType]] = None


class OriginPoolWithWeight(F5XCBaseModel):
    """This defines a combination of origin pool with weight and priority"""

    cluster: Optional[ObjectRefType] = None
    endpoint_subsets: Optional[dict[str, Any]] = None
    pool: Optional[ObjectRefType] = None
    priority: Optional[int] = None
    weight: Optional[int] = None


class DownstreamTLSCertsParams(F5XCBaseModel):
    """Select TLS Parameters and Certificates"""

    certificates: Optional[list[ObjectRefType]] = None
    no_mtls: Optional[Any] = None
    tls_config: Optional[TlsConfig] = None
    use_mtls: Optional[DownstreamTlsValidationContext] = None


class ProxyTypeTLSTCP(F5XCBaseModel):
    """Choice for selecting TLS over TCP proxy with bring your own certificates"""

    tls_cert_params: Optional[DownstreamTLSCertsParams] = None
    tls_parameters: Optional[DownstreamTlsParamsType] = None


class ProxyTypeTLSTCPAutoCerts(F5XCBaseModel):
    """Choice for selecting TLS over TCP proxy with automatic certificates"""

    no_mtls: Optional[Any] = None
    tls_config: Optional[TlsConfig] = None
    use_mtls: Optional[DownstreamTlsValidationContext] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the TCP load balancer create specification"""

    active_service_policies: Optional[ServicePolicyList] = None
    advertise_custom: Optional[AdvertiseCustom] = None
    advertise_on_public: Optional[AdvertisePublic] = None
    advertise_on_public_default_vip: Optional[Any] = None
    default_lb_with_sni: Optional[Any] = None
    dns_volterra_managed: Optional[bool] = None
    do_not_advertise: Optional[Any] = None
    do_not_retract_cluster: Optional[Any] = None
    domains: Optional[list[str]] = None
    hash_policy_choice_least_active: Optional[Any] = None
    hash_policy_choice_random: Optional[Any] = None
    hash_policy_choice_round_robin: Optional[Any] = None
    hash_policy_choice_source_ip_stickiness: Optional[Any] = None
    idle_timeout: Optional[int] = None
    listen_port: Optional[int] = None
    no_service_policies: Optional[Any] = None
    no_sni: Optional[Any] = None
    origin_pools_weights: Optional[list[OriginPoolWithWeight]] = None
    port_ranges: Optional[str] = None
    retract_cluster: Optional[Any] = None
    service_policies_from_namespace: Optional[Any] = None
    sni: Optional[Any] = None
    tcp: Optional[Any] = None
    tls_tcp: Optional[ProxyTypeTLSTCP] = None
    tls_tcp_auto_cert: Optional[ProxyTypeTLSTCPAutoCerts] = None


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


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


class InternetVIPListenerStatusType(F5XCBaseModel):
    arn: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class InternetVIPTargetGroupStatusType(F5XCBaseModel):
    arn: Optional[str] = None
    listener_status: Optional[list[InternetVIPListenerStatusType]] = None
    name: Optional[str] = None
    protocol: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class InternetVIPStatus(F5XCBaseModel):
    """CName and installation info"""

    arn: Optional[str] = None
    name: Optional[str] = None
    nlb_cname: Optional[str] = None
    nlb_status: Optional[str] = None
    reason: Optional[str] = None
    target_group_status: Optional[list[InternetVIPTargetGroupStatusType]] = None


class InternetVIPInfo(F5XCBaseModel):
    """Internet VIP Info"""

    site_name: Optional[str] = None
    site_network_type: Optional[Literal['SITE_NETWORK_INSIDE_AND_OUTSIDE', 'SITE_NETWORK_INSIDE', 'SITE_NETWORK_OUTSIDE', 'SITE_NETWORK_SERVICE', 'SITE_NETWORK_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_INSIDE_AND_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_IP_FABRIC']] = None
    status: Optional[InternetVIPStatus] = None


class GetSpecType(F5XCBaseModel):
    """Shape of the TCP load balancer get specification"""

    active_service_policies: Optional[ServicePolicyList] = None
    advertise_custom: Optional[AdvertiseCustom] = None
    advertise_on_public: Optional[AdvertisePublic] = None
    advertise_on_public_default_vip: Optional[Any] = None
    auto_cert_info: Optional[AutoCertInfoType] = None
    cert_state: Optional[Literal['AutoCertDisabled', 'DnsDomainVerification', 'AutoCertStarted', 'DomainChallengePending', 'DomainChallengeVerified', 'AutoCertFinalize', 'CertificateInvalid', 'CertificateValid', 'AutoCertNotApplicable', 'AutoCertRateLimited', 'AutoCertGenerationRetry', 'AutoCertError', 'PreDomainChallengePending', 'DomainChallengeStarted', 'AutoCertInitialize', 'AutoCertAccountRateLimited', 'AutoCertDomainRateLimited', 'CertificateExpired']] = None
    default_lb_with_sni: Optional[Any] = None
    dns_info: Optional[list[DnsInfo]] = None
    dns_volterra_managed: Optional[bool] = None
    do_not_advertise: Optional[Any] = None
    do_not_retract_cluster: Optional[Any] = None
    domains: Optional[list[str]] = None
    hash_policy_choice_least_active: Optional[Any] = None
    hash_policy_choice_random: Optional[Any] = None
    hash_policy_choice_round_robin: Optional[Any] = None
    hash_policy_choice_source_ip_stickiness: Optional[Any] = None
    host_name: Optional[str] = None
    idle_timeout: Optional[int] = None
    internet_vip_info: Optional[list[InternetVIPInfo]] = None
    listen_port: Optional[int] = None
    no_service_policies: Optional[Any] = None
    no_sni: Optional[Any] = None
    origin_pools_weights: Optional[list[OriginPoolWithWeight]] = None
    port_ranges: Optional[str] = None
    retract_cluster: Optional[Any] = None
    service_policies_from_namespace: Optional[Any] = None
    sni: Optional[Any] = None
    tcp: Optional[Any] = None
    tls_tcp: Optional[ProxyTypeTLSTCP] = None
    tls_tcp_auto_cert: Optional[ProxyTypeTLSTCPAutoCerts] = None


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class GetDnsInfoResponse(F5XCBaseModel):
    """Response for get-dns-info API"""

    dns_info: Optional[GlobalSpecType] = None


class ReplaceSpecType(F5XCBaseModel):
    """Shape of the TCP load balancer replace specification"""

    active_service_policies: Optional[ServicePolicyList] = None
    advertise_custom: Optional[AdvertiseCustom] = None
    advertise_on_public: Optional[AdvertisePublic] = None
    advertise_on_public_default_vip: Optional[Any] = None
    default_lb_with_sni: Optional[Any] = None
    dns_volterra_managed: Optional[bool] = None
    do_not_advertise: Optional[Any] = None
    do_not_retract_cluster: Optional[Any] = None
    domains: Optional[list[str]] = None
    hash_policy_choice_least_active: Optional[Any] = None
    hash_policy_choice_random: Optional[Any] = None
    hash_policy_choice_round_robin: Optional[Any] = None
    hash_policy_choice_source_ip_stickiness: Optional[Any] = None
    idle_timeout: Optional[int] = None
    listen_port: Optional[int] = None
    no_service_policies: Optional[Any] = None
    no_sni: Optional[Any] = None
    origin_pools_weights: Optional[list[OriginPoolWithWeight]] = None
    port_ranges: Optional[str] = None
    retract_cluster: Optional[Any] = None
    service_policies_from_namespace: Optional[Any] = None
    sni: Optional[Any] = None
    tcp: Optional[Any] = None
    tls_tcp: Optional[ProxyTypeTLSTCP] = None
    tls_tcp_auto_cert: Optional[ProxyTypeTLSTCPAutoCerts] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class DNSVHostStatusType(F5XCBaseModel):
    """DNS related Virtual Host status"""

    error_description: Optional[str] = None
    existing_certificate_state: Optional[str] = None
    renew_certificate_state: Optional[Literal['AutoCertDisabled', 'DnsDomainVerification', 'AutoCertStarted', 'DomainChallengePending', 'DomainChallengeVerified', 'AutoCertFinalize', 'CertificateInvalid', 'CertificateValid', 'AutoCertNotApplicable', 'AutoCertRateLimited', 'AutoCertGenerationRetry', 'AutoCertError', 'PreDomainChallengePending', 'DomainChallengeStarted', 'AutoCertInitialize', 'AutoCertAccountRateLimited', 'AutoCertDomainRateLimited', 'CertificateExpired']] = None
    state: Optional[Literal['VIRTUAL_HOST_READY', 'VIRTUAL_HOST_PENDING_VERIFICATION', 'VIRTUAL_HOST_VERIFICATION_FAILED', 'VIRTUAL_HOST_PENDING_DNS_DELEGATION', 'VIRTUAL_HOST_PENDING_A_RECORD', 'VIRTUAL_HOST_DNS_A_RECORD_ADDED', 'VIRTUAL_HOST_INTERNET_NLB_PENDING_CREATION', 'VIRTUAL_HOST_INTERNET_NLB_CREATION_FAILED']] = None
    suggested_action: Optional[str] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    virtual_host_status: Optional[DNSVHostStatusType] = None


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
    """By default a summary of tcp_loadbalancer is returned in 'List'. By..."""

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
Spec = GlobalSpecType
Spec = WhereVirtualSiteSpecifiedVIP
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
