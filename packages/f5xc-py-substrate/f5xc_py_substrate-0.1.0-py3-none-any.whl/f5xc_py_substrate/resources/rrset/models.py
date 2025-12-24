"""Pydantic models for rrset."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


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


class DNSAAAAResourceRecord(F5XCBaseModel):
    """RecordSet for AAAA Records"""

    name: Optional[str] = None
    values: Optional[list[str]] = None


class DNSAFSDBRecord(F5XCBaseModel):
    """DNS AFSDB Record"""

    name: Optional[str] = None
    values: Optional[list[AFSDBRecordValue]] = None


class DNSAResourceRecord(F5XCBaseModel):
    """A Records"""

    name: Optional[str] = None
    values: Optional[list[str]] = None


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


class DNSTXTResourceRecord(F5XCBaseModel):
    name: Optional[str] = None
    values: Optional[list[str]] = None


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


class CreateRequest(F5XCBaseModel):
    dns_zone_name: Optional[str] = None
    group_name: Optional[str] = None
    rrset: Optional[RRSet] = None


class ReplaceRequest(F5XCBaseModel):
    dns_zone_name: Optional[str] = None
    group_name: Optional[str] = None
    record_name: Optional[str] = None
    rrset: Optional[RRSet] = None
    type_: Optional[str] = Field(default=None, alias="type")


class Response(F5XCBaseModel):
    dns_zone_name: Optional[str] = None
    group_name: Optional[str] = None
    namespace: Optional[str] = None
    record_name: Optional[str] = None
    rrset: Optional[RRSet] = None
    type_: Optional[str] = Field(default=None, alias="type")


# Convenience aliases
