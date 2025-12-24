"""Pydantic models for discovered_service."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class DiscoveredServiceListItem(F5XCBaseModel):
    """List item for discovered_service resources."""


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class PodInfoType(F5XCBaseModel):
    """Information about POD providing the service"""

    ip: Optional[str] = None
    pod_name: Optional[str] = None


class PortInfoType(F5XCBaseModel):
    """Information about port and protocol on which the service is provided"""

    port: Optional[int] = None
    protocol: Optional[str] = None
    target_port: Optional[int] = None


class ConsulService(F5XCBaseModel):
    """Service details discovered from Consul."""

    discovery_object: Optional[ObjectRefType] = None
    pods: Optional[list[PodInfoType]] = None
    ports: Optional[list[PortInfoType]] = None
    service_name: Optional[str] = None


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


class WhereSite(F5XCBaseModel):
    """This defines a reference to a CE site where a load balancer could be advertised"""

    site: Optional[list[ObjectRefType]] = None


class WhereVirtualSite(F5XCBaseModel):
    """This defines a reference to a customer site virtual site where a load..."""

    virtual_site: Optional[list[ObjectRefType]] = None


class ProxyTypeHttp(F5XCBaseModel):
    """Choice for selecting HTTP proxy"""

    advertise_on_public_default_vip: Optional[Any] = None
    site: Optional[WhereSite] = None
    virtual_site: Optional[WhereVirtualSite] = None


class ProxyTypeHttps(F5XCBaseModel):
    """Choice for selecting HTTP proxy with bring your own certificate"""

    advertise_on_public_default_vip: Optional[Any] = None
    certificates: Optional[list[ObjectRefType]] = None
    site: Optional[WhereSite] = None
    virtual_site: Optional[WhereVirtualSite] = None


class HTTPLBRequest(F5XCBaseModel):
    """HTTP LB Request Parameters"""

    domain: Optional[str] = None
    http: Optional[ProxyTypeHttp] = None
    https: Optional[ProxyTypeHttps] = None
    https_auto_cert: Optional[Any] = None
    name: Optional[str] = None
    skip_server_verification: Optional[Any] = None
    trusted_ca: Optional[ObjectRefType] = None


class CreateHTTPLoadBalancerRequest(F5XCBaseModel):
    """CreateHTTPLoadBalancerRequest"""

    http_lb_request: Optional[HTTPLBRequest] = None


class CreateHTTPLoadBalancerResponse(F5XCBaseModel):
    """CreateHTTPLoadBalancerResponse"""

    http_loadbalancer: Optional[ObjectRefType] = None


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


class TCPLBRequest(F5XCBaseModel):
    """TCP LB Request"""

    advertise_custom: Optional[AdvertiseCustom] = None
    advertise_on_public_default_vip: Optional[Any] = None
    domain: Optional[str] = None
    listen_port: Optional[int] = None
    name: Optional[str] = None
    no_sni: Optional[Any] = None
    port_ranges: Optional[str] = None
    sni: Optional[Any] = None


class CreateTCPLoadBalancerRequest(F5XCBaseModel):
    """CreateTCPLoadBalancerRequest"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tcp_lb_request: Optional[TCPLBRequest] = None


class CreateTCPLoadBalancerResponse(F5XCBaseModel):
    """CreateTCPLoadBalancerResponse"""

    tcp_loadbalancer: Optional[ObjectRefType] = None


class DisableVisibilityRequest(F5XCBaseModel):
    """Disable visibility on the discovered service"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class DisableVisibilityResponse(F5XCBaseModel):
    """Response to the Disable Visibility request"""

    pass


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


class VirtualServerPoolHealthStatusListResponseItem(F5XCBaseModel):
    """Pool member health"""

    name: Optional[str] = None
    status: Optional[list[MetricValue]] = None


class VirtualServerPoolMemberHealth(F5XCBaseModel):
    """Health of each pool member of the virtual server"""

    virtual_server_pool_members: Optional[list[VirtualServerPoolHealthStatusListResponseItem]] = None


class HealthStatusResponse(F5XCBaseModel):
    """Response for Discovered Service Health Status Request"""

    status: Optional[list[MetricValue]] = None
    virtual_server_pool_members_health: Optional[VirtualServerPoolMemberHealth] = None


class EnableVisibilityRequest(F5XCBaseModel):
    """Enable visibility of the discovered service in all workspaces like WAAP,..."""

    name: Optional[str] = None
    namespace: Optional[str] = None


class EnableVisibilityResponse(F5XCBaseModel):
    """Response to the Enable Visibility request"""

    virtual_host_ref: Optional[ObjectRefType] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class K8sService(F5XCBaseModel):
    """Service details discovered from K8s."""

    discovery_object: Optional[ObjectRefType] = None
    pods: Optional[list[PodInfoType]] = None
    ports: Optional[list[PortInfoType]] = None
    service_name: Optional[str] = None


class NginxOneDiscoveredServer(F5XCBaseModel):
    """Discovered Servers Info"""

    domains: Optional[list[str]] = None
    nginx_one_object_id: Optional[str] = None
    nginx_one_object_name: Optional[str] = None
    nginx_service_discovery_ref: Optional[ObjectRefType] = None
    port: Optional[int] = None
    server_block: Optional[str] = None


class ThirdPartyApplicationDiscovery(F5XCBaseModel):
    """Configure third party log source applications to send logs to your XC..."""

    discovery_object: Optional[ObjectRefType] = None


class VirtualServer(F5XCBaseModel):
    """Virtual Server discovered from BIG-IP."""

    bigip_version: Optional[str] = None
    cbip_cluster: Optional[str] = None
    discovery_object: Optional[ObjectRefType] = None
    enabled_state: Optional[Literal['NONE', 'ENABLED', 'DISABLED']] = None
    ip_address: Optional[str] = None
    partition: Optional[str] = None
    port: Optional[int] = None
    server_name: Optional[str] = None
    status: Optional[Literal['UNSPECIFIED', 'AVAILABLE', 'OFFLINE', 'UNKNOWN', 'UNAVAILABLE', 'DELETED']] = None
    sub_path: Optional[str] = None


class GetSpecType(F5XCBaseModel):
    """Get Discovered Service Object."""

    consul_service: Optional[ConsulService] = None
    http_load_balancers: Optional[list[ObjectRefType]] = None
    k8s_service: Optional[K8sService] = None
    n1_discovered_server: Optional[NginxOneDiscoveredServer] = None
    tcp_load_balancers: Optional[list[ObjectRefType]] = None
    third_party: Optional[ThirdPartyApplicationDiscovery] = None
    virtual_server: Optional[VirtualServer] = None
    visibility_disabled: Optional[Any] = None
    visibility_enabled: Optional[Any] = None


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


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
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
    """By default a summary of discovered_service is returned in 'List'. By..."""

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


class ListServicesResponseItem(F5XCBaseModel):
    """By default a summary of discovered services is returned in 'List'. By..."""

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


class ListServicesResponse(F5XCBaseModel):
    """This is the output message of List for specific service type."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[ListServicesResponseItem]] = None


class SuggestValuesReq(F5XCBaseModel):
    """Request body of SuggestValues request"""

    field_path: Optional[str] = None
    match_value: Optional[str] = None
    namespace: Optional[str] = None
    request_body: Optional[ProtobufAny] = None


class SuggestedItem(F5XCBaseModel):
    """A tuple with a suggested value and it's description."""

    description: Optional[str] = None
    ref_value: Optional[ObjectRefType] = None
    str_value: Optional[str] = None


class SuggestValuesResp(F5XCBaseModel):
    """Response body of SuggestValues request"""

    items: Optional[list[SuggestedItem]] = None


# Convenience aliases
Spec = WhereVirtualSiteSpecifiedVIP
Spec = GetSpecType
