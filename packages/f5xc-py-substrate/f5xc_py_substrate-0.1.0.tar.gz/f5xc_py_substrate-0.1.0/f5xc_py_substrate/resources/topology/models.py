"""Pydantic models for topology."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class DCClusterGroupMeshType(F5XCBaseModel):
    """Details of DC Cluster Group Mesh Type"""

    control_and_data_plane_mesh: Optional[Any] = None
    data_plane_mesh: Optional[Any] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


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


class Node(F5XCBaseModel):
    """Node Information for connectivity across sites."""

    name: Optional[str] = None
    sli_address: Optional[str] = None
    slo_address: Optional[str] = None


class MetricTypeData(F5XCBaseModel):
    """Metric Type Data contains key that uniquely identifies individual entity..."""

    labels: Optional[dict[str, Any]] = None
    values: Optional[list[MetricValue]] = None


class DCClusterGroupType(F5XCBaseModel):
    """A canonical form of the DC cluster group."""

    type_: Optional[DCClusterGroupMeshType] = Field(default=None, alias="type")


class DCClusterGroupSummaryInfo(F5XCBaseModel):
    """Summary information related to the DC Cluster Group"""

    sites: Optional[int] = None


class NodeTypeDCClusterGroup(F5XCBaseModel):
    """DC Cluster group is represented as a node in the site topology graph. In..."""

    info: Optional[DCClusterGroupType] = None
    summary: Optional[DCClusterGroupSummaryInfo] = None


class BondMembersType(F5XCBaseModel):
    """BondMembersType represents the bond interface members  along with the..."""

    link_speed: Optional[int] = None
    link_state: Optional[bool] = None
    name: Optional[str] = None


class InterfaceStatus(F5XCBaseModel):
    """Status of Interfaces in ver"""

    active_state: Optional[Literal['STATE_UNKNOWN', 'STATE_ACTIVE', 'STATE_BACKUP']] = None
    bond_members: Optional[list[BondMembersType]] = None
    dhcp_server: Optional[bool] = None
    ip: Optional[IpSubnetType] = None
    ip_mode: Optional[Literal['STATIC', 'DHCP']] = None
    ipv6: Optional[IpSubnetType] = None
    link_quality: Optional[Literal['QUALITY_UNKNOWN', 'QUALITY_GOOD', 'QUALITY_POOR', 'QUALITY_DISABLED']] = None
    link_state: Optional[bool] = None
    link_type: Optional[Literal['LINK_TYPE_UNKNOWN', 'LINK_TYPE_ETHERNET', 'LINK_TYPE_WIFI_802_11AC', 'LINK_TYPE_WIFI_802_11BGN', 'LINK_TYPE_4G', 'LINK_TYPE_WIFI', 'LINK_TYPE_WAN']] = None
    mac: Optional[str] = None
    name: Optional[str] = None
    network_name: Optional[str] = None
    network_type: Optional[Literal['VIRTUAL_NETWORK_SITE_LOCAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE', 'VIRTUAL_NETWORK_PER_SITE', 'VIRTUAL_NETWORK_PUBLIC', 'VIRTUAL_NETWORK_GLOBAL', 'VIRTUAL_NETWORK_SITE_SERVICE', 'VIRTUAL_NETWORK_VER_INTERNAL', 'VIRTUAL_NETWORK_SITE_LOCAL_INSIDE_OUTSIDE', 'VIRTUAL_NETWORK_IP_AUTO', 'VIRTUAL_NETWORK_VOLTADN_PRIVATE_NETWORK', 'VIRTUAL_NETWORK_SRV6_NETWORK', 'VIRTUAL_NETWORK_IP_FABRIC', 'VIRTUAL_NETWORK_SEGMENT']] = None


class AddressInfoType(F5XCBaseModel):
    """Address with additional information"""

    address: Optional[str] = None
    dns_name: Optional[str] = None
    primary: Optional[bool] = None


class NetworkInterfaceType(F5XCBaseModel):
    """A canonical form of the network interface."""

    f5xc_status: Optional[InterfaceStatus] = None
    name: Optional[str] = None
    private_addresses: Optional[list[AddressInfoType]] = None
    public_address: Optional[list[AddressInfoType]] = None
    security_group: Optional[list[str]] = None
    status: Optional[str] = None
    subnet: Optional[list[ObjectRefType]] = None


class InstanceType(F5XCBaseModel):
    """A canonical form of the instance."""

    architecture: Optional[str] = None
    availability_zone: Optional[str] = None
    cpu: Optional[int] = None
    f5xc_node_name: Optional[str] = None
    instance_type: Optional[str] = None
    interfaces: Optional[list[NetworkInterfaceType]] = None
    platform: Optional[str] = None
    private_address: Optional[str] = None
    private_dns_name: Optional[str] = None
    public_address: Optional[str] = None
    public_dns_name: Optional[str] = None
    security_group: Optional[list[str]] = None


class MetricData(F5XCBaseModel):
    """Metric Data contains the metric type and the metric data."""

    data: Optional[list[MetricTypeData]] = None
    type_: Optional[Literal['METRIC_TYPE_IN_BYTES', 'METRIC_TYPE_OUT_BYTES', 'METRIC_TYPE_IN_DROP_PACKETS', 'METRIC_TYPE_OUT_DROP_PACKETS', 'METRIC_TYPE_REACHABILITY_PERCENT', 'METRIC_TYPE_LATENCY_SECONDS', 'METRIC_TYPE_CPU_USAGE_PERCENT', 'METRIC_TYPE_MEMORY_USAGE_PERCENT', 'METRIC_TYPE_DISK_USAGE_PERCENT', 'METRIC_TYPE_DATA_PLANE_CONNECTION_STATUS', 'METRIC_TYPE_CONTROL_PLANE_CONNECTION_STATUS']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None


class NodeTypeInstance(F5XCBaseModel):
    """NodeTypeInstance contains details about the instance and the metrics (if..."""

    info: Optional[InstanceType] = None
    metric: Optional[list[MetricData]] = None


class NodeMetaData(F5XCBaseModel):
    """Metadata for node"""

    cloud_resource_id: Optional[str] = None
    description: Optional[str] = None
    level: Optional[int] = None
    name: Optional[str] = None
    owner_id: Optional[str] = None
    provider_type: Optional[Literal['PROVIDER_TYPE_UNSPECIFIED', 'PROVIDER_TYPE_AWS', 'PROVIDER_TYPE_GCP', 'PROVIDER_TYPE_AZURE', 'PROVIDER_TYPE_VOLTERRA', 'PROVIDER_TYPE_VMWARE', 'PROVIDER_TYPE_KVM', 'PROVIDER_TYPE_OCI', 'PROVIDER_TYPE_BAREMETAL', 'PROVIDER_TYPE_F5RSERIES', 'PROVIDER_TYPE_K8S']] = None
    status: Optional[str] = None
    tags: Optional[dict[str, Any]] = None


class LoadBalancer(F5XCBaseModel):
    """Load Balancer"""

    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None


class NetworkType(F5XCBaseModel):
    """A canonical form of the network."""

    cidr_v4: Optional[list[str]] = None
    cidr_v6: Optional[list[str]] = None
    load_balancer: Optional[list[LoadBalancer]] = None
    network_peers: Optional[list[ObjectRefType]] = None
    region: Optional[list[ObjectRefType]] = None


class RouteTableMetaData(F5XCBaseModel):
    """Metadata associated with the route table"""

    cloud_resource_id: Optional[str] = None
    name: Optional[str] = None
    tags: Optional[dict[str, Any]] = None


class NetworkSummaryInfo(F5XCBaseModel):
    """Summary information related to the network"""

    route_tables: Optional[list[RouteTableMetaData]] = None


class NodeTypeNetwork(F5XCBaseModel):
    """NodeTypeNetwork contains details about the network and the metrics (if..."""

    info: Optional[NetworkType] = None
    metric: Optional[list[MetricData]] = None
    summary: Optional[NetworkSummaryInfo] = None


class SiteType(F5XCBaseModel):
    """A canonical form of the site."""

    app_type: Optional[Literal['SITE_APPTYPE_NONE', 'SITE_APPTYPE_APPSTACK', 'SITE_APPTYPE_MESH']] = None
    dc_cluster_group: Optional[list[ObjectRefType]] = None
    gateway_type: Optional[Literal['INGRESS_GATEWAY', 'INGRESS_EGRESS_GATEWAY']] = None
    network: Optional[list[ObjectRefType]] = None
    orchestration_mode: Optional[Literal['NOT_MANAGED', 'MANAGED']] = None
    site_type: Optional[Literal['INVALID', 'REGIONAL_EDGE', 'CUSTOMER_EDGE', 'NGINX_ONE']] = None
    tgw: Optional[list[ObjectRefType]] = None


class SiteSummaryInfo(F5XCBaseModel):
    """Summary information related to the site"""

    availability_zone: Optional[list[str]] = None
    node_count: Optional[int] = None
    node_info: Optional[list[Node]] = None


class NodeTypeSite(F5XCBaseModel):
    """NodeTypeSite contains details about the site and the metrics (if..."""

    info: Optional[SiteType] = None
    metric: Optional[list[MetricData]] = None
    summary: Optional[SiteSummaryInfo] = None


class FullMeshGroupType(F5XCBaseModel):
    """Details of Full Mesh Group Type"""

    control_and_data_plane_mesh: Optional[Any] = None
    data_plane_mesh: Optional[Any] = None


class HubFullMeshGroupType(F5XCBaseModel):
    """Details of Hub Full Mesh Group Type"""

    control_and_data_plane_mesh: Optional[Any] = None
    data_plane_mesh: Optional[Any] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class SpokeMeshGroupType(F5XCBaseModel):
    """Details of Spoke Mesh Group Type"""

    control_and_data_plane_mesh: Optional[Any] = None
    data_plane_mesh: Optional[Any] = None
    hub_mesh_group: Optional[ObjectRefType] = None


class SiteMeshGroupType(F5XCBaseModel):
    """A canonical form of the site mesh group."""

    full_mesh: Optional[FullMeshGroupType] = None
    hub: Optional[list[ObjectRefType]] = None
    hub_mesh: Optional[HubFullMeshGroupType] = None
    site_type: Optional[Literal['INVALID', 'REGIONAL_EDGE', 'CUSTOMER_EDGE', 'NGINX_ONE']] = None
    spoke_mesh: Optional[SpokeMeshGroupType] = None
    topology_site: Optional[list[ObjectRefType]] = None
    type_: Optional[Literal['SITE_MESH_GROUP_TYPE_INVALID', 'SITE_MESH_GROUP_TYPE_HUB_FULL_MESH', 'SITE_MESH_GROUP_TYPE_SPOKE', 'SITE_MESH_GROUP_TYPE_FULL_MESH']] = Field(default=None, alias="type")
    virtual_site: Optional[list[ObjectRefType]] = None


class EdgeInfoSummary(F5XCBaseModel):
    """Summary information for an edge"""

    count: Optional[int] = None
    status: Optional[Literal['LINK_STATUS_NOT_APPLICABLE', 'LINK_STATUS_UNKNOWN', 'LINK_STATUS_UP', 'LINK_STATUS_DOWN', 'LINK_STATUS_DEGRADED']] = None


class LinkInfoSummary(F5XCBaseModel):
    """Summary information for a link type"""

    count: Optional[int] = None
    status: Optional[Literal['LINK_STATUS_NOT_APPLICABLE', 'LINK_STATUS_UNKNOWN', 'LINK_STATUS_UP', 'LINK_STATUS_DOWN', 'LINK_STATUS_DEGRADED']] = None
    type_: Optional[Literal['LINK_TYPE_TUNNEL', 'LINK_TYPE_NETWORK', 'LINK_TYPE_SUBNET', 'LINK_TYPE_INSTANCE', 'LINK_TYPE_SITE_MESH_GROUP', 'LINK_TYPE_DC_CLUSTER_GROUP', 'LINK_TYPE_L3', 'LINK_TYPE_CONTROL_PLANE', 'LINK_TYPE_BGP_CONNECTION']] = Field(default=None, alias="type")


class SiteMeshGroupSummaryInfo(F5XCBaseModel):
    """Summary information related to the site mesh group"""

    edge_status_summary: Optional[list[EdgeInfoSummary]] = None
    link_status_summary: Optional[list[LinkInfoSummary]] = None
    other_connected_site_mesh_group_sites: Optional[int] = None
    sites: Optional[int] = None


class NodeTypeSiteMeshGroup(F5XCBaseModel):
    """Site mesh group is represented as a node in the site topology graph. In..."""

    info: Optional[SiteMeshGroupType] = None
    summary: Optional[SiteMeshGroupSummaryInfo] = None


class SubnetType(F5XCBaseModel):
    """A canonical form of the subnet."""

    availability_zone: Optional[str] = None
    cidr_v4: Optional[list[str]] = None
    cidr_v6: Optional[list[str]] = None
    interface_type: Optional[Literal['OUTSIDE', 'INSIDE', 'WORKLOAD', 'NOT_APPLICABLE']] = None
    network: Optional[list[ObjectRefType]] = None
    region: Optional[list[ObjectRefType]] = None


class SubnetSummaryInfo(F5XCBaseModel):
    """Summary information related to the subnet"""

    route_tables: Optional[list[RouteTableMetaData]] = None


class NodeTypeSubnet(F5XCBaseModel):
    """NodeTypeSubnet contains details about the subnet and the metrics (if..."""

    info: Optional[SubnetType] = None
    metric: Optional[list[MetricData]] = None
    summary: Optional[SubnetSummaryInfo] = None


class AWSTGWAttachment(F5XCBaseModel):
    """AWS TGW Attachment"""

    associated_route_table_id: Optional[str] = None
    association_state: Optional[str] = None
    cidr: Optional[str] = None
    cloud_connect: Optional[list[ObjectRefType]] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    resource_type: Optional[str] = None
    segment: Optional[list[ObjectRefType]] = None


class TransitGatewayType(F5XCBaseModel):
    """A canonical form of the transit gateway."""

    attachments: Optional[list[AWSTGWAttachment]] = None
    auto_accept_shared_attachments: Optional[bool] = None
    dns_support: Optional[bool] = None
    network: Optional[list[ObjectRefType]] = None
    vpn_ecmp_support: Optional[bool] = None


class NodeTypeTransitGateway(F5XCBaseModel):
    """NodeTypeTransitGateway contains details about the transit gateway and..."""

    info: Optional[TransitGatewayType] = None
    metric: Optional[list[MetricData]] = None


class Node(F5XCBaseModel):
    """Canonical representation of Node in the topology graph."""

    dc_cluster_group: Optional[NodeTypeDCClusterGroup] = None
    id_: Optional[str] = Field(default=None, alias="id")
    instance: Optional[NodeTypeInstance] = None
    metadata: Optional[NodeMetaData] = None
    network: Optional[NodeTypeNetwork] = None
    site: Optional[NodeTypeSite] = None
    site_mesh_group: Optional[NodeTypeSiteMeshGroup] = None
    subnet: Optional[NodeTypeSubnet] = None
    transit_gateway: Optional[NodeTypeTransitGateway] = None


class MetaType(F5XCBaseModel):
    """A metadata for topology objects."""

    creds: Optional[list[ObjectRefType]] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None
    owner_id: Optional[str] = None
    provider_type: Optional[Literal['PROVIDER_TYPE_UNSPECIFIED', 'PROVIDER_TYPE_AWS', 'PROVIDER_TYPE_GCP', 'PROVIDER_TYPE_AZURE', 'PROVIDER_TYPE_VOLTERRA', 'PROVIDER_TYPE_VMWARE', 'PROVIDER_TYPE_KVM', 'PROVIDER_TYPE_OCI', 'PROVIDER_TYPE_BAREMETAL', 'PROVIDER_TYPE_F5RSERIES', 'PROVIDER_TYPE_K8S']] = None
    raw_json: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[dict[str, Any]] = None


class AWSNetworkMetaData(F5XCBaseModel):
    """Network attributes specific to AWS."""

    metadata: Optional[MetaType] = None
    transit_gateway: Optional[TransitGatewayType] = None


class AWSTGWAttachmentMetaData(F5XCBaseModel):
    """AWS TGW AWSTGWAttachment MetaData"""

    id_: Optional[str] = Field(default=None, alias="id")
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    resource_type: Optional[str] = None
    state: Optional[str] = None


class AWSTgwRouteAttributes(F5XCBaseModel):
    """Route attributes specific to AWS TGW."""

    next_hop_attachment: Optional[list[AWSTGWAttachmentMetaData]] = None
    route_type: Optional[str] = None


class AWSRouteAttributes(F5XCBaseModel):
    """Route attributes specific to AWS."""

    propagated: Optional[bool] = None
    tgw: Optional[AWSTgwRouteAttributes] = None


class MetricSelector(F5XCBaseModel):
    """MetricSelector is used to specify the list of metrics to be returned in..."""

    edge: Optional[list[Literal['METRIC_TYPE_IN_BYTES', 'METRIC_TYPE_OUT_BYTES', 'METRIC_TYPE_IN_DROP_PACKETS', 'METRIC_TYPE_OUT_DROP_PACKETS', 'METRIC_TYPE_REACHABILITY_PERCENT', 'METRIC_TYPE_LATENCY_SECONDS', 'METRIC_TYPE_CPU_USAGE_PERCENT', 'METRIC_TYPE_MEMORY_USAGE_PERCENT', 'METRIC_TYPE_DISK_USAGE_PERCENT', 'METRIC_TYPE_DATA_PLANE_CONNECTION_STATUS', 'METRIC_TYPE_CONTROL_PLANE_CONNECTION_STATUS']]] = None
    end_time: Optional[str] = None
    node: Optional[list[Literal['METRIC_TYPE_IN_BYTES', 'METRIC_TYPE_OUT_BYTES', 'METRIC_TYPE_IN_DROP_PACKETS', 'METRIC_TYPE_OUT_DROP_PACKETS', 'METRIC_TYPE_REACHABILITY_PERCENT', 'METRIC_TYPE_LATENCY_SECONDS', 'METRIC_TYPE_CPU_USAGE_PERCENT', 'METRIC_TYPE_MEMORY_USAGE_PERCENT', 'METRIC_TYPE_DISK_USAGE_PERCENT', 'METRIC_TYPE_DATA_PLANE_CONNECTION_STATUS', 'METRIC_TYPE_CONTROL_PLANE_CONNECTION_STATUS']]] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class DCClusterTopologyRequest(F5XCBaseModel):
    """Request to get DC Cluster group topology and the associated metrics."""

    dc_cluster_group: Optional[str] = None
    metric_selector: Optional[MetricSelector] = None


class LinkInfo(F5XCBaseModel):
    """Information about the link that connects 2 nodes in the topology graph."""

    dst_id: Optional[str] = None
    name: Optional[str] = None
    src_id: Optional[str] = None
    status: Optional[Literal['LINK_STATUS_NOT_APPLICABLE', 'LINK_STATUS_UNKNOWN', 'LINK_STATUS_UP', 'LINK_STATUS_DOWN', 'LINK_STATUS_DEGRADED']] = None
    type_: Optional[Literal['LINK_TYPE_TUNNEL', 'LINK_TYPE_NETWORK', 'LINK_TYPE_SUBNET', 'LINK_TYPE_INSTANCE', 'LINK_TYPE_SITE_MESH_GROUP', 'LINK_TYPE_DC_CLUSTER_GROUP', 'LINK_TYPE_L3', 'LINK_TYPE_CONTROL_PLANE', 'LINK_TYPE_BGP_CONNECTION']] = Field(default=None, alias="type")


class LinkTypeData(F5XCBaseModel):
    """LinkTypeData contains details about the link and the metrics (if..."""

    info: Optional[LinkInfo] = None
    metric: Optional[list[MetricData]] = None


class Edge(F5XCBaseModel):
    """Canonical representation of Edge in the topology graph."""

    links: Optional[list[LinkTypeData]] = None
    node_id1: Optional[str] = None
    node_id2: Optional[str] = None
    status: Optional[Literal['LINK_STATUS_NOT_APPLICABLE', 'LINK_STATUS_UNKNOWN', 'LINK_STATUS_UP', 'LINK_STATUS_DOWN', 'LINK_STATUS_DEGRADED']] = None


class GCPRouteAttributes(F5XCBaseModel):
    """Route attributes specific to GCP."""

    ip_version: Optional[str] = None
    priority: Optional[int] = None
    route_name: Optional[str] = None
    route_type: Optional[Literal['GCP_ROUTE_TYPE_NONE', 'GCP_ROUTE_TYPE_TRANSIT', 'GCP_ROUTE_TYPE_SUBNET', 'GCP_ROUTE_TYPE_STATIC', 'GCP_ROUTE_TYPE_BGP']] = None
    scope_limits: Optional[list[str]] = None


class RouteType(F5XCBaseModel):
    """A canonical form of the route."""

    aws: Optional[AWSRouteAttributes] = None
    destination: Optional[str] = None
    gcp: Optional[GCPRouteAttributes] = None
    next_hop_type: Optional[Literal['VIRTUAL_NETWORK_GATEWAY', 'VNET_LOCAL', 'INTERNET', 'VIRTUAL_APPLIANCE', 'NONE', 'VNET_PEERING', 'VIRTUAL_NETWORK_SERVICE_ENDPOINT', 'NEXT_HOP_TYPE_NOT_APPLICABLE', 'LOADBALANCER', 'VPC_NETWORK', 'VPC_PEERING', 'INTERNAL_LOAD_BALANCER', 'INSTANCE', 'INTERCONNECT', 'INTERNET_GATEWAY', 'IP', 'VPN_TUNNEL', 'TGW_ATTACHMENT']] = None
    nexthop: Optional[str] = None
    source: Optional[Literal['INVALID_SOURCE', 'DEFAULT', 'USER', 'UNKNOWN', 'VIRTUAL_NETWORK_GATEWAY_SOURCE', 'SOURCE_NOT_APPLICABLE']] = None
    state: Optional[Literal['ACTIVE_STATE', 'INVALID_STATE', 'STATE_NOT_APPLICABLE', 'STATE_BLACKHOLE', 'STATE_UNAVAILABLE', 'STATE_PENDING', 'STATE_DELETING', 'STATE_DELETED']] = None
    user_defined_route_name: Optional[str] = None


class RouteTableType(F5XCBaseModel):
    """A canonical form of the route table."""

    associations: Optional[list[AWSTGWAttachmentMetaData]] = None
    explicit_subnet: Optional[list[ObjectRefType]] = None
    implicit_subnet: Optional[list[ObjectRefType]] = None
    network: Optional[list[ObjectRefType]] = None
    propagations: Optional[list[AWSTGWAttachmentMetaData]] = None
    route_table_state: Optional[Literal['ROUTE_TABLE_STATE_NONE', 'ROUTE_TABLE_STATE_PENDING', 'ROUTE_TABLE_STATE_AVAILABLE', 'ROUTE_TABLE_STATE_DELETING', 'ROUTE_TABLE_STATE_DELETED']] = None
    route_table_type: Optional[Literal['ROUTE_TABLE_NETWORK', 'ROUTE_TABLE_TGW']] = None
    routes: Optional[list[RouteType]] = None
    subnet: Optional[list[ObjectRefType]] = None
    transit_gateway: Optional[list[ObjectRefType]] = None


class RouteTableData(F5XCBaseModel):
    """Data associated with the route table"""

    metadata: Optional[RouteTableMetaData] = None
    route_table: Optional[RouteTableType] = None


class SubnetMetaData(F5XCBaseModel):
    """Metadata associated with the subnets"""

    cidr_v4: Optional[list[str]] = None
    cidr_v6: Optional[list[str]] = None
    cloud_resource_id: Optional[str] = None
    name: Optional[str] = None


class SubnetData(F5XCBaseModel):
    """Data associated with the subnets"""

    metadata: Optional[SubnetMetaData] = None
    subnet: Optional[SubnetType] = None


class NetworkRouteTableData(F5XCBaseModel):
    """Data associated with the  network route tables"""

    route_table_data: Optional[RouteTableData] = None
    subnet_data: Optional[list[SubnetData]] = None


class NetworkRouteTableMetaData(F5XCBaseModel):
    """Metadata associated with the network route tables"""

    route_table_metadata: Optional[RouteTableMetaData] = None
    subnet_metadata: Optional[list[SubnetMetaData]] = None


class NetworkRoutesData(F5XCBaseModel):
    """Data associated with the network routes"""

    network_id: Optional[str] = None
    route_tables_data: Optional[list[NetworkRouteTableData]] = None


class NetworkRouteTablesResponse(F5XCBaseModel):
    """List of RouteTables Associated in the Network"""

    routes_data: Optional[list[NetworkRoutesData]] = None


class NetworkRoutesMetaData(F5XCBaseModel):
    """Metadata associated with the network routes"""

    cloud_resource_id: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None
    network_type: Optional[Literal['NETWORK_TYPE_NONE', 'NETWORK_TYPE_HUB_VNET', 'NETWORK_TYPE_SPOKE_VNET', 'NETWORK_TYPE_SERVICE_VPC', 'NETWORK_TYPE_SPOKE_VPC']] = None
    regions: Optional[list[str]] = None
    route_tables_metadata: Optional[list[NetworkRouteTableMetaData]] = None


class RouteTableResponse(F5XCBaseModel):
    """Route table"""

    metadata: Optional[RouteTableMetaData] = None
    route_table: Optional[RouteTableType] = None


class SiteMeshTopologyRequest(F5XCBaseModel):
    """Request to get site mesh group topology and the associated metrics."""

    metric_selector: Optional[MetricSelector] = None
    site_mesh_group: Optional[str] = None


class SiteNetworksResponse(F5XCBaseModel):
    """List of Networks Associated to Site"""

    aws: Optional[AWSNetworkMetaData] = None
    routes_metadata: Optional[list[NetworkRoutesMetaData]] = None


class SiteTopologyRequest(F5XCBaseModel):
    """Request to get site topology and the associated metrics."""

    group_dc_cluster_nodes: Optional[bool] = None
    group_site_mesh_nodes: Optional[bool] = None
    level: Optional[int] = None
    metric_selector: Optional[MetricSelector] = None
    node_id: Optional[str] = None
    site: Optional[str] = None


class TGWRouteTablesResponse(F5XCBaseModel):
    """List of RouteTables Associated with TGW"""

    routes_data: Optional[list[RouteTableData]] = None


class Response(F5XCBaseModel):
    """Relationship between the resources associated with a site is represented..."""

    edges: Optional[list[Edge]] = None
    nodes: Optional[list[Node]] = None
    step: Optional[str] = None


# Convenience aliases
