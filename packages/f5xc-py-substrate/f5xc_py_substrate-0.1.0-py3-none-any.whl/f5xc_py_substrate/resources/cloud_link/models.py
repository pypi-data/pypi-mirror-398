"""Pydantic models for cloud_link."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class CloudLinkListItem(F5XCBaseModel):
    """List item for cloud_link resources."""


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


class Ipv4Type(F5XCBaseModel):
    """Configure BGP IPv4 peering for endpoints"""

    aws_router_peer_address: Optional[str] = None
    router_peer_address: Optional[str] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class AWSBYOCType(F5XCBaseModel):
    """AWS Bring You Own Connection. F5XC supports Virtual interfaces from the..."""

    auth_key: Optional[SecretType] = None
    bgp_asn: Optional[int] = None
    connection_id: Optional[str] = None
    ipv4: Optional[Ipv4Type] = None
    metadata: Optional[MessageMetaType] = None
    region: Optional[str] = None
    system_generated_name: Optional[Any] = None
    tags: Optional[dict[str, Any]] = None
    user_assigned_name: Optional[str] = None
    virtual_interface_type: Optional[Literal['PRIVATE']] = None
    vlan: Optional[int] = None


class AWSBYOCListType(F5XCBaseModel):
    """List of Bring You Own Connection"""

    connections: Optional[list[AWSBYOCType]] = None


class DirectConnectGatewayStatusType(F5XCBaseModel):
    """Status reported by Amazon Web Services (AWS) Direct Connect Gateway..."""

    amazon_asn: Optional[str] = None
    aws_path: Optional[str] = None
    direct_connect_gateway_id: Optional[str] = None
    direct_connect_gateway_name: Optional[str] = None
    direct_connect_gateway_state: Optional[str] = None
    owner_account: Optional[str] = None
    state_change_error: Optional[str] = None


class BGPPeerType(F5XCBaseModel):
    """The BGP peer object."""

    address_family: Optional[str] = None
    asn: Optional[int] = None
    bgp_peer_id: Optional[str] = None
    bgp_peer_state: Optional[str] = None
    bgp_status: Optional[str] = None
    cloud_provider_address: Optional[str] = None
    customer_address: Optional[str] = None


class VirtualInterfaceStatusType(F5XCBaseModel):
    """Status reported by Amazon Web Services (AWS) Virtual Interface Status..."""

    address_family: Optional[str] = None
    amazon_address: Optional[str] = None
    amazon_asn: Optional[str] = None
    attachment_state_change_error: Optional[str] = None
    aws_path: Optional[str] = None
    bgp_asn: Optional[int] = None
    bgp_peers: Optional[list[BGPPeerType]] = None
    connection_id: Optional[str] = None
    direct_connect_attachment_state: Optional[str] = None
    direct_connect_gateway_id: Optional[str] = None
    direct_connect_gateway_name: Optional[str] = None
    jumbo_frame_capable: Optional[bool] = None
    location: Optional[str] = None
    mtu: Optional[int] = None
    owner_account: Optional[str] = None
    region: Optional[str] = None
    tags: Optional[dict[str, Any]] = None
    virtual_interface_id: Optional[str] = None
    virtual_interface_name: Optional[str] = None
    virtual_interface_state: Optional[str] = None
    virtual_interface_type: Optional[str] = None
    vlan: Optional[int] = None


class DirectConnectConnectionStatusType(F5XCBaseModel):
    """Status reported by Amazon Web Services (AWS) Direct Connect Connection..."""

    aws_path: Optional[str] = None
    bandwidth: Optional[str] = None
    connection_id: Optional[str] = None
    connection_name: Optional[str] = None
    connection_state: Optional[str] = None
    gateway_status: Optional[DirectConnectGatewayStatusType] = None
    has_logical_redundancy: Optional[str] = None
    jumbo_frame_capable: Optional[bool] = None
    location: Optional[str] = None
    owner_account: Optional[str] = None
    partner_name: Optional[str] = None
    provider_name: Optional[str] = None
    region: Optional[str] = None
    tags: Optional[dict[str, Any]] = None
    vif_status: Optional[VirtualInterfaceStatusType] = None
    vlan: Optional[int] = None


class AWSStatusType(F5XCBaseModel):
    """Status reported by this Cloud Link and associated Amazon Web Services..."""

    cloud_link_state: Optional[Literal['UP', 'DOWN', 'DEGRADED', 'NOT_APPLICABLE']] = None
    connection_status: Optional[list[DirectConnectConnectionStatusType]] = None
    deployment_status: Optional[Literal['IN_PROGRESS', 'ERROR', 'READY', 'DELETING', 'CUSTOMER_DEPLOYED', 'NOT_APPLICABLE']] = None
    error_description: Optional[str] = None
    suggested_action: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class AWSType(F5XCBaseModel):
    """CloudLink for AWS Cloud Provider"""

    aws_cred: Optional[ObjectRefType] = None
    byoc: Optional[AWSBYOCListType] = None
    custom_asn: Optional[int] = None


class AzureStatusType(F5XCBaseModel):
    """Status reported by associated Azure cloud components"""

    pass


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ADNType(F5XCBaseModel):
    cloudlink_network_name: Optional[str] = None


class GCPBYOCType(F5XCBaseModel):
    """GCP Bring You Own Connection."""

    interconnect_attachment_name: Optional[str] = None
    metadata: Optional[MessageMetaType] = None
    project: Optional[str] = None
    region: Optional[str] = None
    same_as_credential: Optional[Any] = None


class GCPBYOCListType(F5XCBaseModel):
    """List of GCP Bring You Own Connections"""

    connections: Optional[list[GCPBYOCType]] = None


class GCPType(F5XCBaseModel):
    """CloudLink for GCP Cloud Provider"""

    byoc: Optional[GCPBYOCListType] = None
    gcp_cred: Optional[ObjectRefType] = None


class CreateSpecType(F5XCBaseModel):
    """Creates a new CloudLink with configured parameters"""

    aws: Optional[AWSType] = None
    disabled: Optional[Any] = None
    enabled: Optional[ADNType] = None
    gcp: Optional[GCPType] = None


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
    """Gets CloudLink parameters"""

    aws: Optional[AWSType] = None
    cloud_link_state: Optional[Literal['UP', 'DOWN', 'DEGRADED', 'NOT_APPLICABLE']] = None
    disabled: Optional[Any] = None
    enabled: Optional[ADNType] = None
    gcp: Optional[GCPType] = None
    sites: Optional[int] = None
    status: Optional[Literal['IN_PROGRESS', 'ERROR', 'READY', 'DELETING', 'CUSTOMER_DEPLOYED', 'NOT_APPLICABLE']] = None


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


class GCPPartnerMetadata(F5XCBaseModel):
    """Partner metadata for a GCP Cloud Interconnect attachment"""

    interconnect: Optional[str] = None
    name: Optional[str] = None
    portal_url: Optional[str] = None


class GCPCloudInterconnectAttachmentStatusType(F5XCBaseModel):
    """Status reported by Google Cloud Platform (GCP) Cloud Interconnect..."""

    admin_enabled: Optional[bool] = None
    attachment_state: Optional[str] = None
    availability_domain: Optional[str] = None
    bandwidth: Optional[str] = None
    bgp_peers: Optional[list[BGPPeerType]] = None
    cloud_router_ip: Optional[str] = None
    customer_router_ip: Optional[str] = None
    dataplane_version: Optional[int] = None
    encryption: Optional[str] = None
    gcp_path: Optional[str] = None
    interconnect: Optional[str] = None
    labels: Optional[dict[str, Any]] = None
    mtu: Optional[int] = None
    name: Optional[str] = None
    operational_status: Optional[str] = None
    partner_asn: Optional[int] = None
    partner_metadata: Optional[GCPPartnerMetadata] = None
    project: Optional[str] = None
    region: Optional[str] = None
    router: Optional[str] = None
    stack_type: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")
    vlan: Optional[int] = None
    vpc_network: Optional[str] = None


class GCPStatusType(F5XCBaseModel):
    """Status reported by associated GCP cloud components"""

    cloud_link_state: Optional[Literal['UP', 'DOWN', 'DEGRADED', 'NOT_APPLICABLE']] = None
    connection_status: Optional[list[GCPCloudInterconnectAttachmentStatusType]] = None


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
    """Replaces configured CloudLink with new set of parameters"""

    aws: Optional[AWSType] = None
    disabled: Optional[Any] = None
    enabled: Optional[ADNType] = None
    gcp: Optional[GCPType] = None


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

    aws_status: Optional[AWSStatusType] = None
    azure_status: Optional[Any] = None
    conditions: Optional[list[ConditionType]] = None
    gcp_status: Optional[GCPStatusType] = None
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
    """By default a summary of cloud_link is returned in 'List'. By setting..."""

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


class ReapplyConfigRequest(F5XCBaseModel):
    """Reapply CloudLink Config"""

    name: Optional[str] = None


class ReapplyConfigResponse(F5XCBaseModel):
    """Reapply CloudLink Config"""

    pass


class ReplaceResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
