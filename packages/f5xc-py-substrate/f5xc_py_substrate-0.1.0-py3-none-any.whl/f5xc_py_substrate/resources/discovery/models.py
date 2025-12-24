"""Pydantic models for discovery."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class DiscoveryListItem(F5XCBaseModel):
    """List item for discovery resources."""


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class CBIPDeviceStatus(F5XCBaseModel):
    cbip_mgmt_ip: Optional[str] = None
    condition: Optional[ConditionType] = None


class CBIPStatusType(F5XCBaseModel):
    """This status captures the status of the cBIP discovery and its internal..."""

    device_status: Optional[list[CBIPDeviceStatus]] = None


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


class TLSClientConfigType(F5XCBaseModel):
    """TLS config for client of discovery service"""

    certificate: Optional[str] = None
    key_url: Optional[SecretType] = None
    server_name: Optional[str] = None
    trusted_ca_url: Optional[str] = None


class RestConfigType(F5XCBaseModel):
    """Configuration details to access discovery service rest API."""

    api_server: Optional[str] = None
    tls_info: Optional[TLSClientConfigType] = None


class ConsulHttpBasicAuthInfoType(F5XCBaseModel):
    """Authentication parameters to access Hashicorp Consul."""

    passwd_url: Optional[SecretType] = None
    user_name: Optional[str] = None


class ConsulAccessInfo(F5XCBaseModel):
    """Hashicorp Consul API server information"""

    connection_info: Optional[RestConfigType] = None
    http_basic_auth_info: Optional[ConsulHttpBasicAuthInfoType] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ConsulVipDiscoveryInfoType(F5XCBaseModel):
    """Consul Configuration to publish VIPs"""

    disable: Optional[Any] = None
    publish: Optional[Any] = None


class ConsulDiscoveryType(F5XCBaseModel):
    """Discovery configuration for Hashicorp Consul"""

    access_info: Optional[ConsulAccessInfo] = None
    publish_info: Optional[ConsulVipDiscoveryInfoType] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class K8SAccessInfo(F5XCBaseModel):
    """K8S API server access"""

    connection_info: Optional[RestConfigType] = None
    isolated: Optional[Any] = None
    kubeconfig_url: Optional[SecretType] = None
    reachable: Optional[Any] = None


class K8SNamespaceMappingItem(F5XCBaseModel):
    """Map K8s Namespace(s) to an App Namespace. If not specified, all virtual..."""

    namespace: Optional[str] = None
    namespace_regex: Optional[str] = None


class K8SNamespaceMapping(F5XCBaseModel):
    """Select the mapping between K8s namespaces from which services will be..."""

    items: Optional[list[K8SNamespaceMappingItem]] = None


class K8SDelegationType(F5XCBaseModel):
    dns_mode: Optional[Literal['CORE_DNS', 'KUBE_DNS']] = None
    subdomain: Optional[str] = None


class K8SPublishType(F5XCBaseModel):
    namespace: Optional[str] = None


class K8SVipDiscoveryInfoType(F5XCBaseModel):
    """K8S Configuration to publish VIPs"""

    disable: Optional[Any] = None
    dns_delegation: Optional[K8SDelegationType] = None
    publish: Optional[K8SPublishType] = None
    publish_fqdns: Optional[Any] = None


class K8SDiscoveryType(F5XCBaseModel):
    """Discovery configuration for K8s."""

    access_info: Optional[K8SAccessInfo] = None
    default_all: Optional[Any] = None
    namespace_mapping: Optional[K8SNamespaceMapping] = None
    publish_info: Optional[K8SVipDiscoveryInfoType] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


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
    """API to create discovery object for a site or virtual site in system namespace"""

    cluster_id: Optional[str] = None
    discovery_consul: Optional[ConsulDiscoveryType] = None
    discovery_k8s: Optional[K8SDiscoveryType] = None
    no_cluster_id: Optional[Any] = None
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
    """API to Get discovery object for a site or virtual site in system namespace"""

    cluster_id: Optional[str] = None
    discovery_consul: Optional[ConsulDiscoveryType] = None
    discovery_k8s: Optional[K8SDiscoveryType] = None
    no_cluster_id: Optional[Any] = None
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


class PodInfoType(F5XCBaseModel):
    """Information about POD providing the service"""

    ip: Optional[str] = None
    pod_name: Optional[str] = None


class PortInfoType(F5XCBaseModel):
    """Information about port and protocol on which the service is provided"""

    port: Optional[int] = None
    protocol: Optional[str] = None
    target_port: Optional[int] = None


class DiscoveredServiceType(F5XCBaseModel):
    """Details of each Discovered Service"""

    cluster_ip: Optional[str] = None
    cluster_ipv6: Optional[str] = None
    labels: Optional[dict[str, Any]] = None
    namespace: Optional[str] = None
    pods: Optional[list[PodInfoType]] = None
    ports: Optional[list[PortInfoType]] = None
    service_name: Optional[str] = None
    service_type: Optional[str] = None


class DownloadCertificatesRequest(F5XCBaseModel):
    """Download Certificates Of Log Collector"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class DownloadCertificatesResponse(F5XCBaseModel):
    """Response to the DownloadCertificatesResponse A zip file with the..."""

    data: Optional[str] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """API to replace discovery object for a site or virtual site in system namespace"""

    cluster_id: Optional[str] = None
    discovery_consul: Optional[ConsulDiscoveryType] = None
    discovery_k8s: Optional[K8SDiscoveryType] = None
    no_cluster_id: Optional[Any] = None
    where: Optional[NetworkSiteRefSelector] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


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


class VerStatusType(F5XCBaseModel):
    """This VER status is per site on which discovery is happening and it lists..."""

    connected: Optional[bool] = None
    services: Optional[list[DiscoveredServiceType]] = None
    site: Optional[str] = None
    type_: Optional[Literal['INVALID_DISCOVERY', 'K8S', 'CONSUL', 'CLASSIC_BIGIP', 'THIRD_PARTY']] = Field(default=None, alias="type")


class StatusObject(F5XCBaseModel):
    """Most recently observed status of object"""

    cbip_status: Optional[CBIPStatusType] = None
    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    ver_status: Optional[VerStatusType] = None


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
    """By default a summary of discovery is returned in 'List'. By setting..."""

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
