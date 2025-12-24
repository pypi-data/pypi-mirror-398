"""Pydantic models for advertise_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AdvertisePolicyListItem(F5XCBaseModel):
    """List item for advertise_policy resources."""


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


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


class SiteRefType(F5XCBaseModel):
    """This specifies a direct reference to a site configuration object"""

    disable_internet_vip: Optional[Any] = None
    enable_internet_vip: Optional[Any] = None
    network_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None
    ref: Optional[list[ObjectRefType]] = None


class NetworkRefType(F5XCBaseModel):
    """This specifies a direct reference to a network configuration object"""

    ref: Optional[list[ObjectRefType]] = None


class VSiteRefType(F5XCBaseModel):
    """A reference to virtual_site object"""

    disable_internet_vip: Optional[Any] = None
    enable_internet_vip: Optional[Any] = None
    network_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None
    ref: Optional[list[ObjectRefType]] = None


class NetworkSiteRefSelector(F5XCBaseModel):
    """NetworkSiteRefSelector defines a union of reference to site or reference..."""

    site: Optional[SiteRefType] = None
    virtual_network: Optional[NetworkRefType] = None
    virtual_site: Optional[VSiteRefType] = None


class CreateSpecType(F5XCBaseModel):
    """advertise_policy object controls how and where a service represented by..."""

    address: Optional[str] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None
    protocol: Optional[str] = None
    public_ip: Optional[list[ObjectRefType]] = None
    skip_xff_append: Optional[bool] = None
    tls_parameters: Optional[DownstreamTlsParamsType] = None
    where: Optional[NetworkSiteRefSelector] = None


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
    """Get advertise_policy read a given object from storage backend for..."""

    address: Optional[str] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None
    protocol: Optional[str] = None
    public_ip: Optional[list[ObjectRefType]] = None
    skip_xff_append: Optional[bool] = None
    tls_parameters: Optional[DownstreamTlsParamsType] = None
    where: Optional[NetworkSiteRefSelector] = None


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
    """advertise_policy object controls how and where a service represented by..."""

    address: Optional[str] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None
    protocol: Optional[str] = None
    public_ip: Optional[list[ObjectRefType]] = None
    skip_xff_append: Optional[bool] = None
    tls_parameters: Optional[DownstreamTlsParamsType] = None
    where: Optional[NetworkSiteRefSelector] = None


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


class ListenerConfig(F5XCBaseModel):
    name: Optional[str] = None
    port: Optional[int] = None
    status: Optional[str] = None


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
    """Status for advertise policy"""

    conditions: Optional[list[ConditionType]] = None
    listeners: Optional[list[ListenerConfig]] = None
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
    """By default a summary of advertise_policy is returned in 'List'. By..."""

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
