"""Pydantic models for cloud_connect."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class CloudConnectListItem(F5XCBaseModel):
    """List item for cloud_connect resources."""


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


class AWSDefaultRoutesRouteTable(F5XCBaseModel):
    """AWS Route Table"""

    route_table_id: Optional[list[str]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


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


class NodeType(F5XCBaseModel):
    """Node"""

    address: Optional[IpAddressType] = None
    name: Optional[str] = None
    site: Optional[ObjectRefType] = None


class PeerType(F5XCBaseModel):
    """List of peer node and GRE tunnel configuration."""

    inside_gre_subnet: Optional[str] = None
    node: Optional[NodeType] = None
    peer_asn: Optional[str] = None
    tgw_address: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class DefaultRoute(F5XCBaseModel):
    """Select Override Default Route Choice"""

    all_route_tables: Optional[Any] = None
    selective_route_tables: Optional[AWSDefaultRoutesRouteTable] = None


class AWSVPCAttachmentType(F5XCBaseModel):
    custom_routing: Optional[AWSRouteTableListType] = None
    default_route: Optional[DefaultRoute] = None
    labels: Optional[dict[str, Any]] = None
    manual_routing: Optional[Any] = None
    vpc_id: Optional[str] = None


class AWSVPCAttachmentListType(F5XCBaseModel):
    vpc_list: Optional[list[AWSVPCAttachmentType]] = None


class AWSTGWSiteType(F5XCBaseModel):
    """Cloud Connect AWS TGW Site Type"""

    cred: Optional[ObjectRefType] = None
    peers: Optional[list[PeerType]] = None
    site: Optional[ObjectRefType] = None
    vpc_attachments: Optional[AWSVPCAttachmentListType] = None


class AzureRouteTableWithStaticRoute(F5XCBaseModel):
    """Azure Route Table with Static Route"""

    route_table_id: Optional[str] = None
    static_routes: Optional[list[str]] = None


class AzureRouteTableWithStaticRouteListType(F5XCBaseModel):
    """List Azure Route Table with Static Route"""

    route_tables: Optional[list[AzureRouteTableWithStaticRoute]] = None


class AzureAttachmentsStatusType(F5XCBaseModel):
    """Azure Attachment Status Type"""

    deployment_status: Optional[str] = None
    hub_owner_subscriptionid: Optional[str] = None
    hub_vnet_name: Optional[str] = None
    hub_vnet_resource_group: Optional[str] = None
    installed_routes: Optional[AzureRouteTableWithStaticRouteListType] = None
    peering_state: Optional[str] = None
    peering_sync_level: Optional[str] = None
    provisioning_state: Optional[str] = None
    spoke_subscription_id: Optional[str] = None
    spoke_vnet_id: Optional[str] = None
    subnets: Optional[list[SubnetStatusType]] = None
    tags: Optional[dict[str, Any]] = None
    vnet_attachment_id: Optional[str] = None
    vnet_cidr: Optional[str] = None


class AzureAttachmentsListStatusType(F5XCBaseModel):
    """Azure VEspokeNT Attachment List Status Type"""

    attachment_status: Optional[list[AzureAttachmentsStatusType]] = None


class AzureRouteTables(F5XCBaseModel):
    """Azure Route Table"""

    route_table_id: Optional[list[str]] = None


class AzureDefaultRoute(F5XCBaseModel):
    """Select Override Default Route Choice"""

    all_route_tables: Optional[Any] = None
    selective_route_tables: Optional[AzureRouteTables] = None


class AzureVNETAttachmentType(F5XCBaseModel):
    custom_routing: Optional[AzureRouteTableWithStaticRouteListType] = None
    default_route: Optional[AzureDefaultRoute] = None
    labels: Optional[dict[str, Any]] = None
    manual_routing: Optional[Any] = None
    subscription_id: Optional[str] = None
    vnet_id: Optional[str] = None


class AzureVnetAttachmentListType(F5XCBaseModel):
    vnet_list: Optional[list[AzureVNETAttachmentType]] = None


class AzureVNETSiteType(F5XCBaseModel):
    """Cloud Connect Azure VNET Site Type"""

    site: Optional[ObjectRefType] = None
    vnet_attachments: Optional[AzureVnetAttachmentListType] = None


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


class MetricData(F5XCBaseModel):
    """MetricData contains metric type and the corresponding value for a cloud connect"""

    type_: Optional[Literal['METRIC_TYPE_NONE', 'METRIC_TYPE_IN_BYTES', 'METRIC_TYPE_OUT_BYTES', 'METRIC_TYPE_TOTAL_BYTES']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None
    values: Optional[list[MetricValue]] = None


class Data(F5XCBaseModel):
    """CloudConnectData wraps all the response data for a cloud connect."""

    data: Optional[list[MetricData]] = None
    labels: Optional[dict[str, Any]] = None


class StatusType(F5XCBaseModel):
    """Cloud Connect Status"""

    cloud_connect_aws_site: Optional[AWSAttachmentsListStatusType] = None
    cloud_connect_azure_site: Optional[AzureAttachmentsListStatusType] = None


class CreateAWSTGWSiteType(F5XCBaseModel):
    """Cloud Connect AWS TGW Site Type"""

    cred: Optional[ObjectRefType] = None
    site: Optional[ObjectRefType] = None
    vpc_attachments: Optional[AWSVPCAttachmentListType] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the Cloud Connect specification"""

    aws_tgw_site: Optional[CreateAWSTGWSiteType] = None
    azure_vnet_site: Optional[AzureVNETSiteType] = None
    segment: Optional[ObjectRefType] = None


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
    """Shape of the Cloud Connect specification"""

    aws_tgw_site: Optional[AWSTGWSiteType] = None
    azure_vnet_site: Optional[AzureVNETSiteType] = None
    segment: Optional[ObjectRefType] = None
    state: Optional[Literal['DOWN', 'DEGRADED', 'UP']] = None


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


class CredentialsRequest(F5XCBaseModel):
    """Request to return all the credentials for the matching cloud site type."""

    provider: Optional[Literal['AWS', 'AZURE', 'GCP']] = None


class CredentialsResponse(F5XCBaseModel):
    """Response that returns all the credentials for the matching provider."""

    cred: Optional[list[ObjectRefType]] = None


class CustomerEdge(F5XCBaseModel):
    """Customer Edge uniquely identifies customer edge i.e. site."""

    name: Optional[str] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class DiscoverVPCRequest(F5XCBaseModel):
    """Request body to discover vpcs for a given cloud provider, region and cred."""

    cred: Optional[ObjectRefType] = None
    edge_site: Optional[ObjectRefType] = None
    provider: Optional[Literal['AWS', 'AZURE', 'GCP']] = None
    region: Optional[str] = None


class DiscoveredVPCType(F5XCBaseModel):
    """Discover VPC Type"""

    cred: Optional[ObjectRefType] = None
    provider: Optional[Literal['AWS', 'AZURE', 'GCP']] = None
    region: Optional[str] = None
    vpc_id: Optional[str] = None
    vpc_name: Optional[str] = None


class DiscoverVPCResponse(F5XCBaseModel):
    """VPC discovery response body for a cloud provider."""

    discovered_vpc: Optional[list[DiscoveredVPCType]] = None


class SegmentationData(F5XCBaseModel):
    """SegmentationData contains metric type and the corresponding value for a..."""

    data: Optional[list[MetricData]] = None
    type_: Optional[Literal['TRAFFIC_TYPE_NONE', 'TRAFFIC_TYPE_INTER_SEGMENT', 'TRAFFIC_TYPE_INTRA_SEGMENT', 'TRAFFIC_TYPE_INTERNET']] = Field(default=None, alias="type")


class EdgeData(F5XCBaseModel):
    """EdgeData wraps all the response data for a customer edge."""

    ce: Optional[CustomerEdge] = None
    segments: Optional[list[SegmentationData]] = None


class Coordinates(F5XCBaseModel):
    """x-displayName: 'Site Coordinates' Coordinates of the site which provides..."""

    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EdgeSite(F5XCBaseModel):
    """Reference to a edge site"""

    coordinates: Optional[Coordinates] = None
    edge_site: Optional[ObjectRefType] = None
    provider: Optional[Literal['AWS', 'AZURE', 'GCP']] = None
    region: Optional[str] = None


class EdgeListResponse(F5XCBaseModel):
    """Response body that returns online edge sites both customer edge and cloud edge."""

    edge_site: Optional[list[EdgeSite]] = None


class FieldData(F5XCBaseModel):
    """Field Data contains key/value pairs that uniquely identifies the..."""

    labels: Optional[dict[str, Any]] = None
    status: Optional[Literal['STATUS_UNKNOWN', 'STATUS_DOWN', 'STATUS_DEGRADED', 'STATUS_UP']] = None
    value: Optional[list[MetricValue]] = None


class GetMetricsRequest(F5XCBaseModel):
    """Request to get cloud connect data"""

    end_time: Optional[str] = None
    field_selector: Optional[list[Literal['METRIC_TYPE_NONE', 'METRIC_TYPE_IN_BYTES', 'METRIC_TYPE_OUT_BYTES', 'METRIC_TYPE_TOTAL_BYTES']]] = None
    is_trend_request: Optional[bool] = None
    name: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class GetMetricsResponse(F5XCBaseModel):
    """Get Metrics Response"""

    data: Optional[list[MetricData]] = None
    step: Optional[str] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceAWSTGWSiteType(F5XCBaseModel):
    """Cloud Connect AWS TGW Site Type"""

    vpc_attachments: Optional[AWSVPCAttachmentListType] = None


class ReplaceAzureVNETSiteType(F5XCBaseModel):
    """Cloud Connect Azure Vnet Site Type"""

    vnet_attachments: Optional[AzureVnetAttachmentListType] = None


class ReplaceSpecType(F5XCBaseModel):
    """Shape of the Cloud Connect specification"""

    aws_tgw_site: Optional[ReplaceAWSTGWSiteType] = None
    azure_vnet_site: Optional[ReplaceAzureVNETSiteType] = None


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

    cloud_connect_status: Optional[StatusType] = None
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


class LabelFilter(F5XCBaseModel):
    """Metrics used in the cloud connect are tagged with labels listed in the..."""

    label: Optional[Literal['LABEL_NONE', 'LABEL_CUSTOMER_EDGE', 'LABEL_CLOUD_CONNECT']] = None
    op: Optional[Literal['EQ', 'NEQ']] = None
    value: Optional[str] = None


class ListMetricsRequest(F5XCBaseModel):
    """cloud_connect API is used to get the in/out throughput for the tenant's..."""

    end_time: Optional[str] = None
    field_selector: Optional[list[Literal['METRIC_TYPE_NONE', 'METRIC_TYPE_IN_BYTES', 'METRIC_TYPE_OUT_BYTES', 'METRIC_TYPE_TOTAL_BYTES']]] = None
    label_filter: Optional[list[LabelFilter]] = None
    start_time: Optional[str] = None


class ListMetricsResponse(F5XCBaseModel):
    """Response for cloud connect API contains list of customer edges & cloud..."""

    cloud_connect: Optional[list[Data]] = None
    step: Optional[str] = None


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
    """By default a summary of cloud_connect is returned in 'List'. By setting..."""

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


class ListSegmentMetricsRequest(F5XCBaseModel):
    """cloud_connect API is used to get the in/out throughput for the tenant's..."""

    end_time: Optional[str] = None
    field_selector: Optional[list[Literal['METRIC_TYPE_NONE', 'METRIC_TYPE_IN_BYTES', 'METRIC_TYPE_OUT_BYTES', 'METRIC_TYPE_TOTAL_BYTES']]] = None
    is_trend_request: Optional[bool] = None
    label_filter: Optional[list[LabelFilter]] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class ListSegmentMetricsResponse(F5XCBaseModel):
    """Response for cloud connect API contains list of customer edges & cloud..."""

    edges: Optional[list[EdgeData]] = None
    segment: Optional[list[SegmentationData]] = None
    step: Optional[str] = None


class ReApplyVPCAttachmentRequest(F5XCBaseModel):
    """Request of vpc attachment reapply event."""

    cloud_connect: Optional[ObjectRefType] = None
    provider: Optional[Literal['AWS', 'AZURE', 'GCP']] = None
    vpc_id: Optional[str] = None


class ReApplyVPCAttachmentResponse(F5XCBaseModel):
    """Reponse of vpc attachment reapply event."""

    pass


class ReplaceResponse(F5XCBaseModel):
    pass


class TopCloudConnectData(F5XCBaseModel):
    """TopCloudConnectData wraps all the response data"""

    data: Optional[list[FieldData]] = None
    type_: Optional[Literal['METRIC_TYPE_NONE', 'METRIC_TYPE_IN_BYTES', 'METRIC_TYPE_OUT_BYTES', 'METRIC_TYPE_TOTAL_BYTES']] = Field(default=None, alias="type")


class TopCloudConnectRequest(F5XCBaseModel):
    end_time: Optional[str] = None
    field_selector: Optional[list[Literal['METRIC_TYPE_NONE', 'METRIC_TYPE_IN_BYTES', 'METRIC_TYPE_OUT_BYTES', 'METRIC_TYPE_TOTAL_BYTES']]] = None
    filter: Optional[str] = None
    limit: Optional[int] = None
    start_time: Optional[str] = None


class TopCloudConnectResponse(F5XCBaseModel):
    data: Optional[list[TopCloudConnectData]] = None
    step: Optional[str] = None


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
