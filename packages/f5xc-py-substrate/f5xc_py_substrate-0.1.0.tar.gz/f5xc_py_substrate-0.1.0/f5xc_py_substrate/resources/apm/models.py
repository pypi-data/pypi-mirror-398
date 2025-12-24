"""Pydantic models for apm."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ApmListItem(F5XCBaseModel):
    """List item for apm resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class PortRangesType(F5XCBaseModel):
    """List of port ranges"""

    ports: Optional[list[str]] = None


class EndpointServiceReplaceType(F5XCBaseModel):
    """Endpoint Service is a type of NFV service where the packets are destined..."""

    advertise_on_slo_ip: Optional[Any] = None
    advertise_on_slo_ip_external: Optional[Any] = None
    custom_tcp_ports: Optional[PortRangesType] = None
    custom_udp_ports: Optional[PortRangesType] = None
    default_tcp_ports: Optional[Any] = None
    disable_advertise_on_slo_ip: Optional[Any] = None
    http_port: Optional[Any] = None
    https_port: Optional[Any] = None
    no_tcp_ports: Optional[Any] = None
    no_udp_ports: Optional[Any] = None


class APMBigIpAWSReplaceType(F5XCBaseModel):
    """Virtual F5 BIG-IP specification for AWS TGW Site"""

    endpoint_service: Optional[EndpointServiceReplaceType] = None
    tags: Optional[dict[str, Any]] = None


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


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class F5BigIpAWSTGWSiteType(F5XCBaseModel):
    """BIG-IP AWS TGW site specification"""

    aws_tgw_site: Optional[ObjectRefType] = None


class EndpointServiceType(F5XCBaseModel):
    """Endpoint Service is a type of service where the packets are destined to..."""

    advertise_on_slo_ip: Optional[Any] = None
    advertise_on_slo_ip_external: Optional[Any] = None
    automatic_vip: Optional[Any] = None
    configured_vip: Optional[str] = None
    custom_tcp_ports: Optional[PortRangesType] = None
    custom_udp_ports: Optional[PortRangesType] = None
    default_tcp_ports: Optional[Any] = None
    disable_advertise_on_slo_ip: Optional[Any] = None
    http_port: Optional[Any] = None
    https_port: Optional[Any] = None
    no_tcp_ports: Optional[Any] = None
    no_udp_ports: Optional[Any] = None


class CloudSubnetParamType(F5XCBaseModel):
    """Parameters for creating a new cloud subnet"""

    ipv4: Optional[str] = None


class CloudSubnetType(F5XCBaseModel):
    """Parameters for AWS subnet"""

    existing_subnet_id: Optional[str] = None
    subnet_param: Optional[CloudSubnetParamType] = None


class ServiceNodesAWSType(F5XCBaseModel):
    """Specification for service nodes, how and where"""

    automatic_prefix: Optional[Any] = None
    aws_az_name: Optional[str] = None
    mgmt_subnet: Optional[CloudSubnetType] = None
    node_name: Optional[str] = None
    reserved_mgmt_subnet: Optional[Any] = None
    tunnel_prefix: Optional[str] = None


class APMBigIpAWSType(F5XCBaseModel):
    """Virtual F5 BIG-IP configuration for AWS TGW Site using BIG-IP APM service"""

    admin_password: Optional[SecretType] = None
    admin_username: Optional[str] = None
    aws_tgw_site: Optional[F5BigIpAWSTGWSiteType] = None
    endpoint_service: Optional[EndpointServiceType] = None
    nodes: Optional[list[ServiceNodesAWSType]] = None
    ssh_key: Optional[str] = None
    tags: Optional[dict[str, Any]] = None


class AWSMarketPlaceImageTypeAPMaaS(F5XCBaseModel):
    """Select the flavor of BIG-IP AWS Marketplace to launch the instance on..."""

    best_plus_pay_g200_mbps: Optional[Any] = Field(default=None, alias="BestPlusPayG200Mbps")
    best_plus_payg_1gbps: Optional[Any] = None


class AWSSiteTypeChoice(F5XCBaseModel):
    """Virtual F5 BIG-IP APM service to be deployed as external service on AWS..."""

    apm_aws_site: Optional[APMBigIpAWSType] = None
    market_place_image: Optional[AWSMarketPlaceImageTypeAPMaaS] = None


class AWSSiteTypeChoiceReplaceType(F5XCBaseModel):
    """Virtual F5 BIG-IP service to be deployed on AWS Transit Gateway Site"""

    apm_aws_site: Optional[APMBigIpAWSReplaceType] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class BigIqInstanceType(F5XCBaseModel):
    """Specification for BIG-IQ Instance, where and what"""

    license_pool_name: Optional[str] = None
    license_server_ip: Optional[str] = None
    password: Optional[SecretType] = None
    sku_name: Optional[str] = None
    username: Optional[str] = None


class InterfaceDetails(F5XCBaseModel):
    """x-required BIG-IP interface details"""

    interface: Optional[ObjectRefType] = None
    network_gateway: Optional[str] = None
    network_self_ip: Optional[str] = None


class ServiceNodesBareMetalType(F5XCBaseModel):
    """Specification for service nodes, how and where"""

    bm_node_memory_size: Optional[Literal['BM_8_GB_MEMORY', 'BM_16_GB_MEMORY', 'BM_32_GB_MEMORY']] = None
    bm_virtual_cpu_count: Optional[Literal['BM_4_VCPU', 'BM_8_VCPU']] = None
    external_interface: Optional[InterfaceDetails] = None
    internal_interface: Optional[InterfaceDetails] = None
    node_name: Optional[str] = None


class F5BigIpAppStackBareMetalType(F5XCBaseModel):
    """Virtual BIG-IP specification for App Stack bare metal"""

    admin_password: Optional[SecretType] = None
    admin_username: Optional[str] = None
    bare_metal_site: Optional[ObjectRefType] = None
    bigiq_instance: Optional[BigIqInstanceType] = None
    nodes: Optional[list[ServiceNodesBareMetalType]] = None
    public_download_url: Optional[str] = None
    ssh_key: Optional[str] = None


class F5BigIpAppStackBareMetalTypeChoice(F5XCBaseModel):
    """Virtual BIG-IP specification for App Stack Bare Metal Site"""

    f5_bare_metal_site: Optional[F5BigIpAppStackBareMetalType] = None


class AdvertisePublic(F5XCBaseModel):
    """This defines a way to advertise a load balancer on public. If optional..."""

    public_ip: Optional[ObjectRefType] = None


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


class ServiceHttpsManagementType(F5XCBaseModel):
    """HTTPS based configuration"""

    advertise_on_internet: Optional[AdvertisePublic] = None
    advertise_on_internet_default_vip: Optional[Any] = None
    advertise_on_sli_vip: Optional[DownstreamTlsParamsType] = None
    advertise_on_slo_internet_vip: Optional[DownstreamTlsParamsType] = None
    advertise_on_slo_sli: Optional[DownstreamTlsParamsType] = None
    advertise_on_slo_vip: Optional[DownstreamTlsParamsType] = None
    default_https_port: Optional[Any] = None
    domain_suffix: Optional[str] = None
    https_port: Optional[int] = None


class CreateSpecType(F5XCBaseModel):
    """Creates a new APM as a service with configured parameters"""

    aws_site_type_choice: Optional[AWSSiteTypeChoice] = None
    baremetal_site_type_choice: Optional[F5BigIpAppStackBareMetalTypeChoice] = None
    https_management: Optional[ServiceHttpsManagementType] = None


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
    """Gets APM Service parameters"""

    aws_site_type_choice: Optional[AWSSiteTypeChoice] = None
    baremetal_site_type_choice: Optional[F5BigIpAppStackBareMetalTypeChoice] = None
    https_management: Optional[ServiceHttpsManagementType] = None


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


class F5BigIpAppStackBareMetalChoiceReplaceType(F5XCBaseModel):
    """Virtual F5 BIG-IP APM service to be deployed on App Stack Bare Metal Site"""

    pass


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
    """Replaces configured APM Service with new set of parameters"""

    aws_site_type_choice: Optional[AWSSiteTypeChoiceReplaceType] = None
    baremetal_site_type_choice: Optional[Any] = None
    https_management: Optional[ServiceHttpsManagementType] = None


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


class ApplyStatus(F5XCBaseModel):
    apply_state: Optional[Literal['APPLIED', 'APPLY_ERRORED', 'APPLY_INIT_ERRORED', 'APPLYING', 'APPLY_PLANNING', 'APPLY_PLAN_ERRORED', 'APPLY_QUEUED']] = None
    container_version: Optional[str] = None
    destroy_state: Optional[Literal['DESTROYED', 'DESTROY_ERRORED', 'DESTROYING', 'DESTROY_QUEUED']] = None
    error_output: Optional[str] = None
    infra_state: Optional[Literal['PROVISIONED', 'TIMED_OUT', 'ERRORED', 'PROVISIONING']] = None
    modification_timestamp: Optional[str] = None
    suggested_action: Optional[str] = None
    tf_output: Optional[str] = None
    tf_stdout: Optional[str] = None


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
    deployment_status: Optional[ApplyStatus] = None
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
    """By default a summary of apm is returned in 'List'. By setting..."""

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


class MetricTypeData(F5XCBaseModel):
    """Metric Type Data contains key/value pair that uniquely identifies the..."""

    key: Optional[dict[str, Any]] = None
    value: Optional[list[MetricValue]] = None


class MetricData(F5XCBaseModel):
    """Metric data contains the metric type and the corresponding metric value"""

    data: Optional[list[MetricTypeData]] = None
    type_: Optional[Literal['CPU_UTILIZATION', 'NETWORK_IN_PACKETS', 'NETWORK_OUT_PACKETS', 'ACCESS_SESSIONS_COUNT', 'RX_THROUGHPUT_BYTES', 'RX_TRANSFERRED_BYTES', 'CONNECTIONS_RATE', 'CONNECTIONS_TOTAL', 'MAX_ACCESS_SESSIONS_COUNT', 'HEALTHSCORE']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None


class MetricsRequest(F5XCBaseModel):
    """Request to get the metrics for BIG-IP APM services"""

    end_time: Optional[str] = None
    field_selector: Optional[list[Literal['CPU_UTILIZATION', 'NETWORK_IN_PACKETS', 'NETWORK_OUT_PACKETS', 'ACCESS_SESSIONS_COUNT', 'RX_THROUGHPUT_BYTES', 'RX_TRANSFERRED_BYTES', 'CONNECTIONS_RATE', 'CONNECTIONS_TOTAL', 'MAX_ACCESS_SESSIONS_COUNT', 'HEALTHSCORE']]] = None
    filter: Optional[str] = None
    group_by: Optional[list[Literal['SITE', 'SERVICE', 'SERVICE_INSTANCE']]] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class MetricsResponse(F5XCBaseModel):
    """Metrics for BIG-IP APM Services"""

    data: Optional[list[MetricData]] = None
    step: Optional[str] = None


class ReplaceResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
