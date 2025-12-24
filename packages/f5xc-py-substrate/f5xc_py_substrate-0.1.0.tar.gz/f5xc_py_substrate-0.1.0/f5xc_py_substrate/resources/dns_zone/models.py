"""Pydantic models for dns_zone."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class DnsZoneListItem(F5XCBaseModel):
    """List item for dns_zone resources."""


class AFSDBRecordValue(F5XCBaseModel):
    hostname: Optional[str] = None
    subtype: Optional[Literal['NONE', 'AFSVolumeLocationServer', 'DCEAuthenticationServer']] = None


class CERTRecordValue(F5XCBaseModel):
    algorithm: Optional[Literal['RESERVEDALGORITHM', 'RSAMD5', 'DH', 'DSASHA1', 'ECC', 'RSASHA1ALGORITHM', 'INDIRECT', 'PRIVATEDNS', 'PRIVATEOID']] = None
    cert_key_tag: Optional[int] = None
    cert_type: Optional[Literal['INVALIDCERTTYPE', 'PKIX', 'SPKI', 'PGP', 'IPKIX', 'ISPKI', 'IPGP', 'ACPKIX', 'IACPKIX', 'URI_', 'OID']] = None
    certificate: Optional[str] = None


class CERTResourceRecord(F5XCBaseModel):
    """DNS CERT Record"""

    name: Optional[str] = None
    values: Optional[list[CERTRecordValue]] = None


class CertificationAuthorityAuthorization(F5XCBaseModel):
    flags: Optional[int] = None
    tag: Optional[str] = None
    value: Optional[str] = None


class CloneReq(F5XCBaseModel):
    """Clone Request"""

    tenant: Optional[str] = None


class CloneResp(F5XCBaseModel):
    """Clone Response"""

    failed_zones: Optional[list[str]] = None
    success_zones: Optional[list[str]] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class DNSAResourceRecord(F5XCBaseModel):
    """A Records"""

    name: Optional[str] = None
    values: Optional[list[str]] = None


class DNSAAAAResourceRecord(F5XCBaseModel):
    """RecordSet for AAAA Records"""

    name: Optional[str] = None
    values: Optional[list[str]] = None


class DNSAFSDBRecord(F5XCBaseModel):
    """DNS AFSDB Record"""

    name: Optional[str] = None
    values: Optional[list[AFSDBRecordValue]] = None


class DNSAliasResourceRecord(F5XCBaseModel):
    value: Optional[str] = None


class DNSCAAResourceRecord(F5XCBaseModel):
    name: Optional[str] = None
    values: Optional[list[CertificationAuthorityAuthorization]] = None


class SHA1Digest(F5XCBaseModel):
    digest: Optional[str] = None


class SHA256Digest(F5XCBaseModel):
    digest: Optional[str] = None


class SHA384Digest(F5XCBaseModel):
    digest: Optional[str] = None


class DSRecordValue(F5XCBaseModel):
    ds_key_algorithm: Optional[Literal['UNSPECIFIED', 'RSASHA1', 'RSASHA1NSEC3SHA1', 'RSASHA256', 'RSASHA512', 'ECDSAP256SHA256', 'ECDSAP384SHA384', 'ED25519', 'ED448']] = None
    key_tag: Optional[int] = None
    sha1_digest: Optional[SHA1Digest] = None
    sha256_digest: Optional[SHA256Digest] = None
    sha384_digest: Optional[SHA384Digest] = None


class DNSCDSRecord(F5XCBaseModel):
    """DNS CDS Record"""

    name: Optional[str] = None
    values: Optional[list[DSRecordValue]] = None


class DNSCNAMEResourceRecord(F5XCBaseModel):
    name: Optional[str] = None
    value: Optional[str] = None


class DNSDSRecord(F5XCBaseModel):
    """DNS DS Record"""

    name: Optional[str] = None
    values: Optional[list[DSRecordValue]] = None


class DNSEUI48ResourceRecord(F5XCBaseModel):
    """DNS EUI48 Record"""

    name: Optional[str] = None
    value: Optional[str] = None


class DNSEUI64ResourceRecord(F5XCBaseModel):
    """DNS EUI64 Record"""

    name: Optional[str] = None
    value: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class DNSLBResourceRecord(F5XCBaseModel):
    """DNS Load Balancer Record"""

    name: Optional[str] = None
    value: Optional[ObjectRefType] = None


class LOCValue(F5XCBaseModel):
    altitude: Optional[float] = None
    horizontal_precision: Optional[float] = None
    latitude_degree: Optional[int] = None
    latitude_hemisphere: Optional[Literal['N', 'S']] = None
    latitude_minute: Optional[int] = None
    latitude_second: Optional[float] = None
    location_diameter: Optional[float] = None
    longitude_degree: Optional[int] = None
    longitude_hemisphere: Optional[Literal['E', 'W']] = None
    longitude_minute: Optional[int] = None
    longitude_second: Optional[float] = None
    vertical_precision: Optional[float] = None


class DNSLOCResourceRecord(F5XCBaseModel):
    """DNS LOC Record"""

    name: Optional[str] = None
    values: Optional[list[LOCValue]] = None


class MailExchanger(F5XCBaseModel):
    domain: Optional[str] = None
    priority: Optional[int] = None


class DNSMXResourceRecord(F5XCBaseModel):
    name: Optional[str] = None
    values: Optional[list[MailExchanger]] = None


class NAPTRValue(F5XCBaseModel):
    flags: Optional[str] = None
    order: Optional[int] = None
    preference: Optional[int] = None
    regexp: Optional[str] = None
    replacement: Optional[str] = None
    service: Optional[str] = None


class DNSNAPTRResourceRecord(F5XCBaseModel):
    """DNS NAPTR Record"""

    name: Optional[str] = None
    values: Optional[list[NAPTRValue]] = None


class DNSNSResourceRecord(F5XCBaseModel):
    name: Optional[str] = None
    values: Optional[list[str]] = None


class DNSPTRResourceRecord(F5XCBaseModel):
    name: Optional[str] = None
    values: Optional[list[str]] = None


class SRVService(F5XCBaseModel):
    port: Optional[int] = None
    priority: Optional[int] = None
    target: Optional[str] = None
    weight: Optional[int] = None


class DNSSRVResourceRecord(F5XCBaseModel):
    name: Optional[str] = None
    values: Optional[list[SRVService]] = None


class SHA1Fingerprint(F5XCBaseModel):
    fingerprint: Optional[str] = None


class SHA256Fingerprint(F5XCBaseModel):
    fingerprint: Optional[str] = None


class SSHFPRecordValue(F5XCBaseModel):
    algorithm: Optional[Literal['UNSPECIFIEDALGORITHM', 'RSA', 'DSA', 'ECDSA', 'Ed25519', 'Ed448']] = None
    sha1_fingerprint: Optional[SHA1Fingerprint] = None
    sha256_fingerprint: Optional[SHA256Fingerprint] = None


class SSHFPResourceRecord(F5XCBaseModel):
    """DNS SSHFP Record"""

    name: Optional[str] = None
    values: Optional[list[SSHFPRecordValue]] = None


class TLSARecordValue(F5XCBaseModel):
    certificate_association_data: Optional[str] = None
    certificate_usage: Optional[Literal['CertificateAuthorityConstraint', 'ServiceCertificateConstraint', 'TrustAnchorAssertion', 'DomainIssuedCertificate']] = None
    matching_type: Optional[Literal['NoHash', 'SHA256', 'SHA512']] = None
    selector: Optional[Literal['FullCertificate', 'UseSubjectPublicKey']] = None


class TLSAResourceRecord(F5XCBaseModel):
    """DNS TLSA Record"""

    name: Optional[str] = None
    values: Optional[list[TLSARecordValue]] = None


class DNSTXTResourceRecord(F5XCBaseModel):
    name: Optional[str] = None
    values: Optional[list[str]] = None


class RRSet(F5XCBaseModel):
    a_record: Optional[DNSAResourceRecord] = None
    aaaa_record: Optional[DNSAAAAResourceRecord] = None
    afsdb_record: Optional[DNSAFSDBRecord] = None
    alias_record: Optional[DNSAliasResourceRecord] = None
    caa_record: Optional[DNSCAAResourceRecord] = None
    cds_record: Optional[DNSCDSRecord] = None
    cert_record: Optional[CERTResourceRecord] = None
    cname_record: Optional[DNSCNAMEResourceRecord] = None
    description: Optional[str] = None
    ds_record: Optional[DNSDSRecord] = None
    eui48_record: Optional[DNSEUI48ResourceRecord] = None
    eui64_record: Optional[DNSEUI64ResourceRecord] = None
    lb_record: Optional[DNSLBResourceRecord] = None
    loc_record: Optional[DNSLOCResourceRecord] = None
    mx_record: Optional[DNSMXResourceRecord] = None
    naptr_record: Optional[DNSNAPTRResourceRecord] = None
    ns_record: Optional[DNSNSResourceRecord] = None
    ptr_record: Optional[DNSPTRResourceRecord] = None
    srv_record: Optional[DNSSRVResourceRecord] = None
    sshfp_record: Optional[SSHFPResourceRecord] = None
    tlsa_record: Optional[TLSAResourceRecord] = None
    ttl: Optional[int] = None
    txt_record: Optional[DNSTXTResourceRecord] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class DNSSECModeEnable(F5XCBaseModel):
    """DNSSEC enable"""

    pass


class DNSSECMode(F5XCBaseModel):
    disable: Optional[Any] = None
    enable: Optional[Any] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class RRSetGroup(F5XCBaseModel):
    metadata: Optional[MessageMetaType] = None
    rr_set: Optional[list[RRSet]] = None


class SOARecordParameterConfig(F5XCBaseModel):
    expire: Optional[int] = None
    negative_ttl: Optional[int] = None
    refresh: Optional[int] = None
    retry: Optional[int] = None
    ttl: Optional[int] = None


class PrimaryDNSCreateSpecType(F5XCBaseModel):
    allow_http_lb_managed_records: Optional[bool] = None
    default_rr_set_group: Optional[list[RRSet]] = None
    default_soa_parameters: Optional[Any] = None
    dnssec_mode: Optional[DNSSECMode] = None
    rr_set_group: Optional[list[RRSetGroup]] = None
    soa_parameters: Optional[SOARecordParameterConfig] = None


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


class SecondaryDNSCreateSpecType(F5XCBaseModel):
    primary_servers: Optional[list[str]] = None
    tsig_key_algorithm: Optional[Literal['HMAC_MD5', 'UNDEFINED', 'HMAC_SHA1', 'HMAC_SHA224', 'HMAC_SHA256', 'HMAC_SHA384', 'HMAC_SHA512']] = None
    tsig_key_name: Optional[str] = None
    tsig_key_value: Optional[SecretType] = None


class CreateSpecType(F5XCBaseModel):
    """Create DNS Zone in a given namespace. If one already exist it will give a error."""

    primary: Optional[PrimaryDNSCreateSpecType] = None
    secondary: Optional[SecondaryDNSCreateSpecType] = None


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


class PrimaryDNSGetSpecType(F5XCBaseModel):
    admin: Optional[str] = None
    allow_http_lb_managed_records: Optional[bool] = None
    default_rr_set_group: Optional[list[RRSet]] = None
    default_soa_parameters: Optional[Any] = None
    dnssec_mode: Optional[DNSSECMode] = None
    rr_set_group: Optional[list[RRSetGroup]] = None
    serial: Optional[int] = None
    soa_parameters: Optional[SOARecordParameterConfig] = None


class SecondaryDNSGetSpecType(F5XCBaseModel):
    last_axfr_timestamp: Optional[str] = None
    primary_servers: Optional[list[str]] = None
    tsig_key_algorithm: Optional[Literal['HMAC_MD5', 'UNDEFINED', 'HMAC_SHA1', 'HMAC_SHA224', 'HMAC_SHA256', 'HMAC_SHA384', 'HMAC_SHA512']] = None
    tsig_key_name: Optional[str] = None
    tsig_key_value: Optional[SecretType] = None


class GetSpecType(F5XCBaseModel):
    """Get DNS Zone details."""

    domain: Optional[str] = None
    num_of_dns_records: Optional[int] = None
    primary: Optional[PrimaryDNSGetSpecType] = None
    secondary: Optional[SecondaryDNSGetSpecType] = None


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


class DSRecord(F5XCBaseModel):
    """DNSSEC Record details"""

    algorithm: Optional[str] = None
    digest: Optional[str] = None
    digest_type: Optional[str] = None
    flags: Optional[int] = None
    key_tag: Optional[int] = None
    public_key: Optional[str] = None
    ttl: Optional[int] = None


class DNSSECStatus(F5XCBaseModel):
    """DNSSEC details."""

    ds_records: Optional[list[DSRecord]] = None
    mode: Optional[DNSSECMode] = None


class DNSZoneStatus(F5XCBaseModel):
    """Status DNS Zone"""

    deployment_status: Optional[Literal['DNS_ZONE_ACTIVE', 'DNS_ZONE_PENDING', 'DNS_ZONE_DISABLED', 'DNS_ZONE_FAILED']] = None
    dnssec: Optional[DNSSECStatus] = None
    volterra_nameservers: Optional[list[str]] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class MetricsRequest(F5XCBaseModel):
    end_time: Optional[str] = None
    filter: Optional[str] = None
    group_by: Optional[list[Literal['COUNTRY_CODE', 'DOMAIN', 'QUERY_TYPE', 'RESPONSE_CODE', 'DNS_ZONE_NAME', 'CLIENT_SUBNET']]] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


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


class MetricsData(F5XCBaseModel):
    """Metrics Data contains key/value pairs that uniquely identifies the..."""

    labels: Optional[dict[str, Any]] = None
    value: Optional[list[MetricValue]] = None


class MetricsResponse(F5XCBaseModel):
    data: Optional[list[MetricsData]] = None
    step: Optional[str] = None
    total_hits: Optional[str] = None


class RequestLogRequest(F5XCBaseModel):
    """Request to fetch request logs."""

    end_time: Optional[str] = None
    filter: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None


class RequestLogsResponseData(F5XCBaseModel):
    """Dns Zone Request-Log item"""

    client_subnet: Optional[str] = None
    country_code: Optional[str] = None
    dns_zone_name: Optional[str] = None
    domain: Optional[str] = None
    query_type: Optional[str] = None
    response_code: Optional[str] = None
    timestamp: Optional[str] = None


class RequestLogResponse(F5XCBaseModel):
    """Response message for RequestLogRequest"""

    logs: Optional[list[RequestLogsResponseData]] = None
    total_hits: Optional[str] = None


class ExportZoneFileResponse(F5XCBaseModel):
    """Export Zone File Response"""

    html_data: Optional[str] = None


class F5CSDNSZoneConfiguration(F5XCBaseModel):
    """F5 Cloud Services DNS primary or secondary zone configuration"""

    adns_service: Optional[dict[str, Any]] = None
    dns_service: Optional[dict[str, Any]] = None


class GetLocalZoneFileResponse(F5XCBaseModel):
    """Get local zone file Response"""

    last_axfr_timestamp: Optional[str] = None
    zone_file: Optional[str] = None


class GetRemoteZoneFileResponse(F5XCBaseModel):
    """Get remote zone file Response"""

    zone_file: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace DNS Zone in a given namespace."""

    primary: Optional[PrimaryDNSCreateSpecType] = None
    secondary: Optional[SecondaryDNSCreateSpecType] = None


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
    verification_status: Optional[DNSZoneStatus] = None


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


class TSIGConfiguration(F5XCBaseModel):
    tsig_key_algorithm: Optional[Literal['HMAC_MD5', 'UNDEFINED', 'HMAC_SHA1', 'HMAC_SHA224', 'HMAC_SHA256', 'HMAC_SHA384', 'HMAC_SHA512']] = None
    tsig_key_name: Optional[str] = None
    tsig_key_value: Optional[SecretType] = None


class ImportAXFRRequest(F5XCBaseModel):
    """DNS zone import via AXFR"""

    domain_name: Optional[str] = None
    primary_server: Optional[str] = None
    tsig_configuration: Optional[TSIGConfiguration] = None


class ImportAXFRResponse(F5XCBaseModel):
    """Import AXFR Response"""

    configuration: Optional[PrimaryDNSGetSpecType] = None


class ImportBINDCreateRequest(F5XCBaseModel):
    description: Optional[str] = None
    file: Optional[str] = None


class InvalidZone(F5XCBaseModel):
    validation_error: Optional[str] = None
    zone_name: Optional[str] = None


class ValidZone(F5XCBaseModel):
    record_count: Optional[int] = None
    zone_name: Optional[str] = None


class ImportBINDResponse(F5XCBaseModel):
    invalid_zone_list: Optional[list[InvalidZone]] = None
    success_created_zone_count: Optional[int] = None
    valid_zone_list: Optional[list[ValidZone]] = None


class ImportBINDValidateRequest(F5XCBaseModel):
    description: Optional[str] = None
    file: Optional[str] = None


class ImportF5CSZoneRequest(F5XCBaseModel):
    """Import F5 Cloud Services DNS zone"""

    configuration: Optional[F5CSDNSZoneConfiguration] = None


class ImportF5CSZoneResponse(F5XCBaseModel):
    """Import F5 Cloud Services DNS zone response"""

    metadata: Optional[ObjectGetMetaType] = None
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
    """By default a summary of dns_zone is returned in 'List'. By setting..."""

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
Spec = PrimaryDNSCreateSpecType
Spec = SecondaryDNSCreateSpecType
Spec = CreateSpecType
Spec = PrimaryDNSGetSpecType
Spec = SecondaryDNSGetSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
