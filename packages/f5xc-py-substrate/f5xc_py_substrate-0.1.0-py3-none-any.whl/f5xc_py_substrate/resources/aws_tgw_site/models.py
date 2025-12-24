"""Pydantic models for aws_tgw_site."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AwsTgwSiteListItem(F5XCBaseModel):
    """List item for aws_tgw_site resources."""


class AWSSubnetInfoType(F5XCBaseModel):
    """AWS Subnets Info Type"""

    az_name: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    ipv4_prefix: Optional[str] = None


class AWSSubnetIdsType(F5XCBaseModel):
    """AWS Subnet Ids used by volterra site"""

    az_name: Optional[str] = None
    inside_subnet: Optional[AWSSubnetInfoType] = None
    inside_subnet_id: Optional[str] = None
    outside_subnet: Optional[AWSSubnetInfoType] = None
    outside_subnet_id: Optional[str] = None
    workload_subnet: Optional[AWSSubnetInfoType] = None
    workload_subnet_id: Optional[str] = None


class AWSTGWInfoConfigType(F5XCBaseModel):
    """AWS tgw information like tgw-id and site's vpc-id"""

    private_ips: Optional[list[str]] = None
    public_ips: Optional[list[str]] = None
    subnet_ids: Optional[list[AWSSubnetIdsType]] = None
    tgw_id: Optional[str] = None
    vpc_id: Optional[str] = None
    vpc_name: Optional[str] = None


class AWSTGWResourceShareType(F5XCBaseModel):
    """AWS Resource Share Status Type"""

    allow_external_principles: Optional[bool] = None
    creation_time: Optional[str] = None
    deployment_status: Optional[str] = None
    invitation_status: Optional[str] = None
    last_updated_time: Optional[str] = None
    owner_account_id: Optional[str] = None
    receiver_account_id: Optional[list[str]] = None
    resource_share_arn: Optional[str] = None
    resource_share_invitation_arn: Optional[str] = None
    resource_share_name: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[dict[str, Any]] = None


class AWSTGWStatusType(F5XCBaseModel):
    """AWS Transit Gateway Status Type"""

    status_msg: Optional[str] = None
    tags: Optional[dict[str, Any]] = None
    tgw_amazon_asn: Optional[str] = None
    tgw_arn: Optional[str] = None
    tgw_cidrs: Optional[list[str]] = None
    tgw_creation_time: Optional[str] = None
    tgw_id: Optional[str] = None
    tgw_owner_account: Optional[str] = None
    tgw_region: Optional[str] = None
    tgw_state: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


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


class CloudSubnetParamType(F5XCBaseModel):
    """Parameters for creating a new cloud subnet"""

    ipv4: Optional[str] = None


class CloudSubnetType(F5XCBaseModel):
    """Parameters for AWS subnet"""

    existing_subnet_id: Optional[str] = None
    subnet_param: Optional[CloudSubnetParamType] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class AWSVPCTwoInterfaceNodeType(F5XCBaseModel):
    """Parameters for creating two interface Node in one AZ"""

    aws_az_name: Optional[str] = None
    inside_subnet: Optional[CloudSubnetType] = None
    outside_subnet: Optional[CloudSubnetType] = None
    reserved_inside_subnet: Optional[Any] = None
    workload_subnet: Optional[CloudSubnetType] = None


class SecurityGroupType(F5XCBaseModel):
    """Enter pre created security groups for slo(Site Local Outside) and..."""

    inside_security_group_id: Optional[str] = None
    outside_security_group_id: Optional[str] = None


class ExistingTGWType(F5XCBaseModel):
    """Information needed for existing TGW"""

    tgw_asn: Optional[int] = None
    tgw_id: Optional[str] = None
    volterra_site_asn: Optional[int] = None


class TGWAssignedASNType(F5XCBaseModel):
    """Information needed when ASNs are assigned by the user"""

    tgw_asn: Optional[int] = None
    volterra_site_asn: Optional[int] = None


class TGWParamsType(F5XCBaseModel):
    system_generated: Optional[Any] = None
    user_assigned: Optional[TGWAssignedASNType] = None


class AWSVPCParamsType(F5XCBaseModel):
    """Parameters to create new AWS VPC"""

    autogenerate: Optional[Any] = None
    name_tag: Optional[str] = None
    primary_ipv4: Optional[str] = None


class ServicesVPCType(F5XCBaseModel):
    """Setup AWS services VPC, transit gateway and site"""

    admin_password: Optional[SecretType] = None
    aws_cred: Optional[ObjectRefType] = None
    aws_region: Optional[str] = None
    az_nodes: Optional[list[AWSVPCTwoInterfaceNodeType]] = None
    custom_security_group: Optional[SecurityGroupType] = None
    disable_internet_vip: Optional[Any] = None
    disk_size: Optional[int] = None
    enable_internet_vip: Optional[Any] = None
    existing_tgw: Optional[ExistingTGWType] = None
    f5xc_security_group: Optional[Any] = None
    instance_type: Optional[str] = None
    new_tgw: Optional[TGWParamsType] = None
    new_vpc: Optional[AWSVPCParamsType] = None
    no_worker_nodes: Optional[Any] = None
    nodes_per_az: Optional[int] = None
    reserved_tgw_cidr: Optional[Any] = None
    ssh_key: Optional[str] = None
    tgw_cidr: Optional[CloudSubnetParamType] = None
    total_nodes: Optional[int] = None
    vpc_id: Optional[str] = None


class BlockedServices(F5XCBaseModel):
    """Disable a node local service on this site."""

    dns: Optional[Any] = None
    network_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None
    ssh: Optional[Any] = None
    web_user_interface: Optional[Any] = None


class BlockedServicesListType(F5XCBaseModel):
    """Disable node local services on this site. Note: The chosen services will..."""

    blocked_sevice: Optional[list[BlockedServices]] = None


class Coordinates(F5XCBaseModel):
    """Coordinates of the site which provides the site physical location"""

    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CustomDNS(F5XCBaseModel):
    """Custom DNS is the configured for specify CE site"""

    inside_nameserver: Optional[str] = None
    outside_nameserver: Optional[str] = None


class CloudLinkADNType(F5XCBaseModel):
    cloudlink_network_name: Optional[str] = None


class VifRegionConfig(F5XCBaseModel):
    """x-example: 'value' AWS Direct Connect Hosted VIF Config Per Region Object"""

    other_region: Optional[str] = None
    same_as_site_region: Optional[Any] = None
    vif_id: Optional[str] = None


class HostedVIFConfigType(F5XCBaseModel):
    """x-example: 'value' AWS Direct Connect Hosted VIF Configuration"""

    site_registration_over_direct_connect: Optional[CloudLinkADNType] = None
    site_registration_over_internet: Optional[Any] = None
    vif_list: Optional[list[VifRegionConfig]] = None


class DirectConnectConfigType(F5XCBaseModel):
    """Direct Connect Configuration"""

    auto_asn: Optional[Any] = None
    custom_asn: Optional[int] = None
    hosted_vifs: Optional[HostedVIFConfigType] = None
    standard_vifs: Optional[Any] = None


class KubernetesUpgradeDrainConfig(F5XCBaseModel):
    """Specify batch upgrade settings for worker nodes within a site."""

    disable_vega_upgrade_mode: Optional[Any] = None
    drain_max_unavailable_node_count: Optional[int] = None
    drain_node_timeout: Optional[int] = None
    enable_vega_upgrade_mode: Optional[Any] = None


class KubernetesUpgradeDrain(F5XCBaseModel):
    """Specify how worker nodes within a site will be upgraded."""

    disable_upgrade_drain: Optional[Any] = None
    enable_upgrade_drain: Optional[KubernetesUpgradeDrainConfig] = None


class OfflineSurvivabilityModeType(F5XCBaseModel):
    """Offline Survivability allows the Site to continue functioning normally..."""

    enable_offline_survivability_mode: Optional[Any] = None
    no_offline_survivability_mode: Optional[Any] = None


class OperatingSystemType(F5XCBaseModel):
    """Select the F5XC Operating System Version for the site. By default,..."""

    default_os_version: Optional[Any] = None
    operating_system_version: Optional[str] = None


class L3PerformanceEnhancementType(F5XCBaseModel):
    """x-required L3 enhanced performance mode options"""

    jumbo: Optional[Any] = None
    no_jumbo: Optional[Any] = None


class PerformanceEnhancementModeType(F5XCBaseModel):
    """x-required Optimize the site for L3 or L7 traffic processing. L7..."""

    perf_mode_l3_enhanced: Optional[L3PerformanceEnhancementType] = None
    perf_mode_l7_enhanced: Optional[Any] = None


class PrivateConnectConfigType(F5XCBaseModel):
    """Private Connect Configuration"""

    cloud_link: Optional[ObjectRefType] = None
    inside: Optional[Any] = None
    outside: Optional[Any] = None


class VolterraSoftwareType(F5XCBaseModel):
    """Select the F5XC Software Version for the site. By default, latest..."""

    default_sw_version: Optional[Any] = None
    volterra_software_version: Optional[str] = None


class ActiveServicePoliciesType(F5XCBaseModel):
    """Active service policies for the east-west  proxy"""

    service_policies: Optional[list[ObjectRefType]] = None


class ActiveEnhancedFirewallPoliciesType(F5XCBaseModel):
    """List of Enhanced Firewall Policies These policies use session-based..."""

    enhanced_firewall_policies: Optional[list[ObjectRefType]] = None


class ActiveForwardProxyPoliciesType(F5XCBaseModel):
    """Ordered List of Forward Proxy Policies active"""

    forward_proxy_policies: Optional[list[ObjectRefType]] = None


class ActiveNetworkPoliciesType(F5XCBaseModel):
    """List of firewall policy views."""

    network_policies: Optional[list[ObjectRefType]] = None


class SecurityConfigType(F5XCBaseModel):
    """Security Configuration for transit gateway"""

    active_east_west_service_policies: Optional[ActiveServicePoliciesType] = None
    active_enhanced_firewall_policies: Optional[ActiveEnhancedFirewallPoliciesType] = None
    active_forward_proxy_policies: Optional[ActiveForwardProxyPoliciesType] = None
    active_network_policies: Optional[ActiveNetworkPoliciesType] = None
    east_west_service_policy_allow_all: Optional[Any] = None
    forward_proxy_allow_all: Optional[Any] = None
    no_east_west_policy: Optional[Any] = None
    no_forward_proxy: Optional[Any] = None
    no_network_policy: Optional[Any] = None


class CustomPorts(F5XCBaseModel):
    """List of Custom port"""

    port_ranges: Optional[str] = None


class AllowedVIPPorts(F5XCBaseModel):
    """This defines the TCP port(s) which will be opened on the cloud..."""

    custom_ports: Optional[CustomPorts] = None
    disable_allowed_vip_port: Optional[Any] = None
    use_http_https_port: Optional[Any] = None
    use_http_port: Optional[Any] = None
    use_https_port: Optional[Any] = None


class GlobalConnectorType(F5XCBaseModel):
    """Global network reference for direct connection"""

    global_vn: Optional[ObjectRefType] = None


class GlobalNetworkConnectionType(F5XCBaseModel):
    """Global network connection"""

    sli_to_global_dr: Optional[GlobalConnectorType] = None
    slo_to_global_dr: Optional[GlobalConnectorType] = None


class GlobalNetworkConnectionListType(F5XCBaseModel):
    """List of global network connections"""

    global_network_connections: Optional[list[GlobalNetworkConnectionType]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class Ipv4AddressType(F5XCBaseModel):
    """IPv4 Address in dot-decimal notation"""

    addr: Optional[str] = None


class Ipv6AddressType(F5XCBaseModel):
    """IPv6 Address specified as hexadecimal numbers separated by ':'"""

    addr: Optional[str] = None


class IpAddressType(F5XCBaseModel):
    """IP Address used to specify an IPv4 or IPv6 address"""

    ipv4: Optional[Ipv4AddressType] = None
    ipv6: Optional[Ipv6AddressType] = None


class NextHopType(F5XCBaseModel):
    """Identifies the next-hop for a route"""

    interface: Optional[list[ObjectRefType]] = None
    nexthop_address: Optional[IpAddressType] = None
    type_: Optional[Literal['NEXT_HOP_DEFAULT_GATEWAY', 'NEXT_HOP_USE_CONFIGURED', 'NEXT_HOP_NETWORK_INTERFACE']] = Field(default=None, alias="type")


class Ipv4SubnetType(F5XCBaseModel):
    """IPv4 subnets specified as prefix and prefix-length. Prefix length must be <= 32"""

    plen: Optional[int] = None
    prefix: Optional[str] = None


class Ipv6SubnetType(F5XCBaseModel):
    """IPv6 subnets specified as prefix and prefix-length. prefix-legnth must be <= 128"""

    plen: Optional[int] = None
    prefix: Optional[str] = None


class IpSubnetType(F5XCBaseModel):
    """IP Address used to specify an IPv4 or IPv6 subnet addresses"""

    ipv4: Optional[Ipv4SubnetType] = None
    ipv6: Optional[Ipv6SubnetType] = None


class StaticRouteType(F5XCBaseModel):
    """Defines a static route, configuring a list of prefixes and a next-hop to..."""

    attrs: Optional[list[Literal['ROUTE_ATTR_NO_OP', 'ROUTE_ATTR_ADVERTISE', 'ROUTE_ATTR_INSTALL_HOST', 'ROUTE_ATTR_INSTALL_FORWARDING', 'ROUTE_ATTR_MERGE_ONLY']]] = None
    labels: Optional[dict[str, Any]] = None
    nexthop: Optional[NextHopType] = None
    subnets: Optional[list[IpSubnetType]] = None


class SiteStaticRoutesType(F5XCBaseModel):
    """Different ways to configure static routes"""

    custom_static_route: Optional[StaticRouteType] = None
    simple_static_route: Optional[str] = None


class SiteStaticRoutesListType(F5XCBaseModel):
    """List of static routes"""

    static_route_list: Optional[list[SiteStaticRoutesType]] = None


class VnConfiguration(F5XCBaseModel):
    """Virtual Network Configuration"""

    allowed_vip_port: Optional[AllowedVIPPorts] = None
    allowed_vip_port_sli: Optional[AllowedVIPPorts] = None
    dc_cluster_group_inside_vn: Optional[ObjectRefType] = None
    dc_cluster_group_outside_vn: Optional[ObjectRefType] = None
    global_network_list: Optional[GlobalNetworkConnectionListType] = None
    inside_static_routes: Optional[SiteStaticRoutesListType] = None
    no_dc_cluster_group: Optional[Any] = None
    no_global_network: Optional[Any] = None
    no_inside_static_routes: Optional[Any] = None
    no_outside_static_routes: Optional[Any] = None
    outside_static_routes: Optional[SiteStaticRoutesListType] = None
    sm_connection_public_ip: Optional[Any] = None
    sm_connection_pvt_ip: Optional[Any] = None


class VPCAttachmentType(F5XCBaseModel):
    """VPC attachments to transit gateway"""

    labels: Optional[dict[str, Any]] = None
    vpc_id: Optional[str] = None


class VPCAttachmentListType(F5XCBaseModel):
    """Spoke VPCs to be attached to the AWS TGW Site"""

    vpc_list: Optional[list[VPCAttachmentType]] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the AWS TGW site specification"""

    aws_parameters: Optional[ServicesVPCType] = None
    block_all_services: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_dns: Optional[CustomDNS] = None
    default_blocked_services: Optional[Any] = None
    direct_connect_disabled: Optional[Any] = None
    direct_connect_enabled: Optional[DirectConnectConfigType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    os: Optional[OperatingSystemType] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    private_connectivity: Optional[PrivateConnectConfigType] = None
    sw: Optional[VolterraSoftwareType] = None
    tags: Optional[dict[str, Any]] = None
    tgw_security: Optional[SecurityConfigType] = None
    vn_config: Optional[VnConfiguration] = None
    vpc_attachments: Optional[VPCAttachmentListType] = None


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


class DirectConnectInfo(F5XCBaseModel):
    """DirectConnect Info"""

    asn: Optional[int] = None
    direct_connect_gateway_id: Optional[str] = None
    vgw_id: Optional[str] = None


class SiteError(F5XCBaseModel):
    """Site Error"""

    error_description: Optional[str] = None
    suggested_action: Optional[str] = None


class PublishVIPParamsPerAz(F5XCBaseModel):
    """Per AZ parameters needed to publish VIP for public cloud sites"""

    az_name: Optional[str] = None
    inside_vip: Optional[list[str]] = None
    inside_vip_cname: Optional[str] = None
    inside_vip_v6: Optional[list[str]] = None
    outside_vip: Optional[list[str]] = None
    outside_vip_cname: Optional[str] = None
    outside_vip_v6: Optional[list[str]] = None


class GetSpecType(F5XCBaseModel):
    """Shape of the AWS TGW site specification"""

    aws_parameters: Optional[ServicesVPCType] = None
    block_all_services: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_dns: Optional[CustomDNS] = None
    default_blocked_services: Optional[Any] = None
    direct_connect_disabled: Optional[Any] = None
    direct_connect_enabled: Optional[DirectConnectConfigType] = None
    direct_connect_info: Optional[DirectConnectInfo] = None
    error_description: Optional[str] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    private_connectivity: Optional[PrivateConnectConfigType] = None
    site_errors: Optional[list[SiteError]] = None
    site_state: Optional[Literal['ONLINE', 'PROVISIONING', 'UPGRADING', 'STANDBY', 'FAILED', 'REREGISTRATION', 'WAITINGNODES', 'DECOMMISSIONING', 'WAITING_FOR_REGISTRATION', 'ORCHESTRATION_IN_PROGRESS', 'ORCHESTRATION_COMPLETE', 'ERROR_IN_ORCHESTRATION', 'DELETING_CLOUD_RESOURCES', 'DELETED_CLOUD_RESOURCES', 'ERROR_DELETING_CLOUD_RESOURCES', 'VALIDATION_IN_PROGRESS', 'VALIDATION_SUCCESS', 'VALIDATION_FAILED']] = None
    suggested_action: Optional[str] = None
    tags: Optional[dict[str, Any]] = None
    tgw_info: Optional[AWSTGWInfoConfigType] = None
    tgw_security: Optional[SecurityConfigType] = None
    tunnel_type: Optional[Literal['TUNNEL_IPSEC', 'TUNNEL_GRE']] = None
    validation_state: Optional[Literal['VALIDATION_STATE_NONE', 'VALIDATION_IN_PROGRESS', 'VALIDATION_FAILED', 'VALIDATION_SUCCEEDED']] = None
    vip_params_per_az: Optional[list[PublishVIPParamsPerAz]] = None
    vn_config: Optional[VnConfiguration] = None
    vpc_attachments: Optional[VPCAttachmentListType] = None


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


class ServicesVPCReplaceType(F5XCBaseModel):
    """AWS Services VPC Replace config"""

    aws_cred: Optional[ObjectRefType] = None
    aws_region: Optional[str] = None
    az_nodes: Optional[list[AWSVPCTwoInterfaceNodeType]] = None
    custom_security_group: Optional[SecurityGroupType] = None
    disable_internet_vip: Optional[Any] = None
    disk_size: Optional[int] = None
    enable_internet_vip: Optional[Any] = None
    existing_tgw: Optional[ExistingTGWType] = None
    f5xc_security_group: Optional[Any] = None
    instance_type: Optional[str] = None
    new_tgw: Optional[TGWParamsType] = None
    new_vpc: Optional[AWSVPCParamsType] = None
    no_worker_nodes: Optional[Any] = None
    nodes_per_az: Optional[int] = None
    ssh_key: Optional[str] = None
    total_nodes: Optional[int] = None
    vpc_id: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Shape of the AWS TGW site replace specification"""

    aws_parameters: Optional[ServicesVPCReplaceType] = None
    block_all_services: Optional[Any] = None
    blocked_services: Optional[BlockedServicesListType] = None
    coordinates: Optional[Coordinates] = None
    custom_dns: Optional[CustomDNS] = None
    default_blocked_services: Optional[Any] = None
    direct_connect_disabled: Optional[Any] = None
    direct_connect_enabled: Optional[DirectConnectConfigType] = None
    kubernetes_upgrade_drain: Optional[KubernetesUpgradeDrain] = None
    log_receiver: Optional[ObjectRefType] = None
    logs_streaming_disabled: Optional[Any] = None
    offline_survivability_mode: Optional[OfflineSurvivabilityModeType] = None
    performance_enhancement_mode: Optional[PerformanceEnhancementModeType] = None
    private_connectivity: Optional[PrivateConnectConfigType] = None
    tgw_security: Optional[SecurityConfigType] = None
    vn_config: Optional[VnConfiguration] = None
    vpc_attachments: Optional[VPCAttachmentListType] = None


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


class PlanStatus(F5XCBaseModel):
    error_output: Optional[str] = None
    infra_state: Optional[Literal['PROVISIONED', 'TIMED_OUT', 'ERRORED', 'PROVISIONING']] = None
    modification_timestamp: Optional[str] = None
    plan_state: Optional[Literal['PLANNING', 'PLAN_ERRORED', 'NO_CHANGES', 'HAS_CHANGES', 'DISCARDED', 'PLAN_INIT_ERRORED', 'PLAN_QUEUED']] = None
    suggested_action: Optional[str] = None
    tf_plan_output: Optional[str] = None


class DeploymentStatusType(F5XCBaseModel):
    apply_status: Optional[ApplyStatus] = None
    expected_container_version: Optional[str] = None
    plan_status: Optional[PlanStatus] = None


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


class AWSRouteTableType(F5XCBaseModel):
    """AWS Route Table"""

    route_table_id: Optional[str] = None
    static_routes: Optional[list[str]] = None


class AWSRouteTableListType(F5XCBaseModel):
    """AWS Route Table List"""

    route_tables: Optional[list[AWSRouteTableType]] = None


class SubnetStatusType(F5XCBaseModel):
    """Network Interface Status"""

    availability_zone: Optional[str] = None
    interface_type: Optional[str] = None
    network_interface_id: Optional[str] = None
    private_ipv4_address: Optional[str] = None
    status: Optional[str] = None
    subnet_id: Optional[str] = None


class AWSAttachmentsStatusType(F5XCBaseModel):
    """AWS Attachment Status Type"""

    association_route_table_id: Optional[str] = None
    association_state: Optional[str] = None
    creation_time: Optional[str] = None
    deployment_status: Optional[str] = None
    installed_routes: Optional[AWSRouteTableListType] = None
    subnets: Optional[list[SubnetStatusType]] = None
    tags: Optional[dict[str, Any]] = None
    tgw_attachment_id: Optional[str] = None
    tgw_attachment_name: Optional[str] = None
    vpc_cidr: Optional[str] = None
    vpc_deployment_state: Optional[Literal['AVAILABLE', 'PENDING', 'FAILED', 'DELETED', 'DELETING', 'INITIATED']] = None
    vpc_id: Optional[str] = None
    vpc_name: Optional[str] = None
    vpc_owner_id: Optional[str] = None


class AWSConnectPeerStatusType(F5XCBaseModel):
    """AWS Connect Peer Status Type"""

    connect_attachment_id: Optional[str] = None
    connect_peer_deployment_state: Optional[Literal['AVAILABLE', 'PENDING', 'FAILED', 'DELETED', 'DELETING', 'INITIATED']] = None
    connect_peer_id: Optional[str] = None
    deployment_status: Optional[str] = None
    name: Optional[str] = None
    tags: Optional[dict[str, Any]] = None


class AWSConnectAttachmentStatusType(F5XCBaseModel):
    """AWS Connect Attachment Status Type"""

    association_route_table_id: Optional[str] = None
    association_state: Optional[str] = None
    connect_deployment_state: Optional[Literal['AVAILABLE', 'PENDING', 'FAILED', 'DELETED', 'DELETING', 'INITIATED']] = None
    deployment_status: Optional[str] = None
    peers: Optional[list[AWSConnectPeerStatusType]] = None
    protocol: Optional[str] = None
    tags: Optional[dict[str, Any]] = None
    transit_gateway_asn: Optional[str] = None
    transit_gateway_attachment_id: Optional[str] = None
    transit_gateway_attachment_name: Optional[str] = None
    transit_gateway_id: Optional[str] = None
    transport_attachment_id: Optional[str] = None


class AWSTGWResourceReference(F5XCBaseModel):
    """AWS Transit Gateway Route Table Associations"""

    attachment_id: Optional[str] = None
    deployment_status: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    state: Optional[Literal['AVAILABLE', 'PENDING', 'FAILED', 'DELETED', 'DELETING', 'INITIATED']] = None


class AWSTGWRouteTableStatusType(F5XCBaseModel):
    """AWS Transit Gateway Route Table Status Type"""

    associations: Optional[list[AWSTGWResourceReference]] = None
    deployment_status: Optional[str] = None
    propagations: Optional[list[AWSTGWResourceReference]] = None
    tags: Optional[dict[str, Any]] = None
    tgw_rt_deployment_state: Optional[Literal['AVAILABLE', 'PENDING', 'FAILED', 'DELETED', 'DELETING', 'INITIATED']] = None
    transit_gateway_id: Optional[str] = None
    transit_gateway_route_table_id: Optional[str] = None
    transit_gateway_route_table_name: Optional[str] = None


class AWSAttachmentsListStatusType(F5XCBaseModel):
    """AWS VPC Attachment List Status Type"""

    attachment_status: Optional[list[AWSAttachmentsStatusType]] = None
    connect_attachment_status: Optional[list[AWSConnectAttachmentStatusType]] = None
    tgw_route_table_status: Optional[list[AWSTGWRouteTableStatusType]] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    deployment: Optional[DeploymentStatusType] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    resource_share_status: Optional[AWSTGWResourceShareType] = None
    tgw: Optional[AWSTGWStatusType] = None
    vpc_attachments: Optional[AWSAttachmentsListStatusType] = None


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
    """By default a summary of aws_tgw_site is returned in 'List'. By setting..."""

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


class SetTGWInfoRequest(F5XCBaseModel):
    """Request to configure TGW Information"""

    direct_connect_info: Optional[DirectConnectInfo] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tgw_info: Optional[AWSTGWInfoConfigType] = None


class SetTGWInfoResponse(F5XCBaseModel):
    """Response to configure TGW info"""

    pass


class SetVIPInfoRequest(F5XCBaseModel):
    """Request to configure AWS TGW Site VIP information"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    vip_params_per_az: Optional[list[PublishVIPParamsPerAz]] = None


class SetVIPInfoResponse(F5XCBaseModel):
    pass


class SetVPCIpPrefixesRequest(F5XCBaseModel):
    """Request to configure VPC IP prefix set"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    vpc_ip_prefixes: Optional[dict[str, Any]] = None


class SetVPCIpPrefixesResponse(F5XCBaseModel):
    """Response to configure VPC IP prefix set"""

    pass


class SetVPNTunnelsRequest(F5XCBaseModel):
    """Request to configure VPN Tunnels"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class SetVPNTunnelsResponse(F5XCBaseModel):
    """Response to configure VPN Tunnels"""

    pass


class ValidateConfigRequest(F5XCBaseModel):
    """Request to validate AWS VPC site configuration"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class ValidateConfigResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
