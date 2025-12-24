"""Pydantic models for bot_infrastructure."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class BotInfrastructureListItem(F5XCBaseModel):
    """List item for bot_infrastructure resources."""


class PolicyMetadata(F5XCBaseModel):
    """on associated Policy object."""

    name: Optional[str] = None
    version: Optional[str] = None


class EndpointPolicyMetadata(F5XCBaseModel):
    """on associated endpoint policy object."""

    name: Optional[str] = None
    type_: Optional[Literal['WEB', 'MOBILE']] = Field(default=None, alias="type")
    version: Optional[str] = None


class Egress(F5XCBaseModel):
    """Egress"""

    ip_address: Optional[str] = None
    region: Optional[Literal['AP_NORTHEAST_1', 'AP_NORTHEAST_3', 'AP_SOUTH_1', 'AP_SOUTH_2', 'AP_SOUTHEAST_1', 'AP_SOUTHEAST_2', 'AP_SOUTHEAST_3', 'EU_CENTRAL_1', 'EU_NORTH_1', 'EU_WEST_1', 'ME_SOUTH_1', 'ME_CENTRAL_1', 'SA_EAST_1', 'US_EAST_1', 'US_EAST_2', 'US_WEST_1', 'US_WEST_2', 'AF_SOUTH_1', 'GCP_ASIA_EAST1', 'GCP_ASIA_EAST2', 'GCP_ASIA_NORTHEAST1', 'GCP_ASIA_NORTHEAST2', 'GCP_ASIA_NORTHEAST3', 'GCP_ASIA_SOUTH1', 'GCP_ASIA_SOUTHEAST1', 'GCP_ASIA_SOUTHEAST2', 'GCP_AUSTRALIA_SOUTHEAST1', 'GCP_EUROPE_WEST1', 'GCP_EUROPE_WEST2', 'GCP_EUROPE_WEST3', 'GCP_NORTHAMERICA_NORTHEAST1', 'GCP_NORTHAMERICA_NORTHEAST2', 'GCP_SOUTHAMERICA_EAST1', 'GCP_SOUTHAMERICA_WEST1', 'GCP_US_CENTRAL1', 'GCP_US_EAST1', 'GCP_US_EAST4', 'GCP_US_WEST1', 'GCP_US_WEST2']] = None


class Ingress(F5XCBaseModel):
    """Ingress"""

    host_name: Optional[str] = None
    ip_address: Optional[str] = None
    region: Optional[Literal['AP_NORTHEAST_1', 'AP_NORTHEAST_3', 'AP_SOUTH_1', 'AP_SOUTH_2', 'AP_SOUTHEAST_1', 'AP_SOUTHEAST_2', 'AP_SOUTHEAST_3', 'EU_CENTRAL_1', 'EU_NORTH_1', 'EU_WEST_1', 'ME_SOUTH_1', 'ME_CENTRAL_1', 'SA_EAST_1', 'US_EAST_1', 'US_EAST_2', 'US_WEST_1', 'US_WEST_2', 'AF_SOUTH_1', 'GCP_ASIA_EAST1', 'GCP_ASIA_EAST2', 'GCP_ASIA_NORTHEAST1', 'GCP_ASIA_NORTHEAST2', 'GCP_ASIA_NORTHEAST3', 'GCP_ASIA_SOUTH1', 'GCP_ASIA_SOUTHEAST1', 'GCP_ASIA_SOUTHEAST2', 'GCP_AUSTRALIA_SOUTHEAST1', 'GCP_EUROPE_WEST1', 'GCP_EUROPE_WEST2', 'GCP_EUROPE_WEST3', 'GCP_NORTHAMERICA_NORTHEAST1', 'GCP_NORTHAMERICA_NORTHEAST2', 'GCP_SOUTHAMERICA_EAST1', 'GCP_SOUTHAMERICA_WEST1', 'GCP_US_CENTRAL1', 'GCP_US_EAST1', 'GCP_US_EAST4', 'GCP_US_WEST1', 'GCP_US_WEST2']] = None


class InfraCloudHosted(F5XCBaseModel):
    egress: Optional[list[Egress]] = None
    firmware_version: Optional[str] = None
    host_names: Optional[list[str]] = None
    infra_host_name: Optional[str] = None
    ingress: Optional[list[Ingress]] = None
    ip_addresses: Optional[list[str]] = None


class IPInfo(F5XCBaseModel):
    """The IP address information for the device"""

    local: Optional[str] = None
    traffic: Optional[str] = None
    wan: Optional[str] = None


class Device(F5XCBaseModel):
    """The device details"""

    certification_status: Optional[str] = None
    device_firmware_version: Optional[str] = None
    device_name: Optional[str] = None
    ip_info: Optional[IPInfo] = None


class InfraF5HostedOnPrem(F5XCBaseModel):
    """Bot infra type is F5 Hosted/F5 On Premises"""

    devices: Optional[list[Device]] = None
    firmware_version: Optional[str] = None
    infra_host_name: Optional[str] = None


class GetSpecType(F5XCBaseModel):
    """Get Bot Infrastructure"""

    bot_allowlist_policy_metadata: Optional[PolicyMetadata] = None
    bot_endpoint_policy_metadata: Optional[EndpointPolicyMetadata] = None
    bot_network_policy_metadata: Optional[PolicyMetadata] = None
    cloud_hosted: Optional[InfraCloudHosted] = None
    cluster_state: Optional[Literal['ACTIVE', 'INACTIVE', 'PASSIVE_PROXY', 'EMERGENCY_STOP', 'UNAVAILABLE', 'RECONCILE', 'STARTING_ACTIVE', 'STOPPING_ACTIVE', 'UPDATING_FIRMWARE', 'UPDATING_POLICY', 'WAITING_ACTIVE', 'WAITING_START_TIMEOUT']] = None
    environment_type: Optional[Literal['PRODUCTION', 'TESTING']] = None
    on_prem: Optional[InfraF5HostedOnPrem] = None
    physical_hosted: Optional[InfraF5HostedOnPrem] = None
    traffic_type: Optional[Literal['WEB', 'MOBILE']] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace Bot Infrastructure"""

    cloud_hosted: Optional[InfraCloudHosted] = None
    environment_type: Optional[Literal['PRODUCTION', 'TESTING']] = None
    on_prem: Optional[InfraF5HostedOnPrem] = None
    physical_hosted: Optional[InfraF5HostedOnPrem] = None
    traffic_type: Optional[Literal['WEB', 'MOBILE']] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class Production(F5XCBaseModel):
    region_1: Optional[str] = None
    region_2: Optional[str] = None


class Testing(F5XCBaseModel):
    region_1: Optional[str] = None


class CreateSpecInfraCloudHosted(F5XCBaseModel):
    ip_addresses: Optional[list[str]] = None
    production: Optional[Production] = None
    testing: Optional[Testing] = None


class CreateSpecType(F5XCBaseModel):
    """Create Bot Infrastructure"""

    create_cloud_hosted: Optional[CreateSpecInfraCloudHosted] = None
    traffic_type: Optional[Literal['WEB', 'MOBILE']] = None


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


class DeployPolicyMetadata(F5XCBaseModel):
    """The metadata for deployed policy config"""

    policy_name: Optional[str] = None
    policy_type: Optional[Literal['ENDPOINT_POLICY', 'NETWORK_POLICY', 'ALLOWLIST_POLICY']] = None
    version: Optional[str] = None


class DeployPoliciesRequest(F5XCBaseModel):
    """Request for deploy policies"""

    comments: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    policy_metadata: Optional[list[DeployPolicyMetadata]] = None


class DeployPoliciesResponse(F5XCBaseModel):
    """response for deploy policies"""

    deploy_status: Optional[Literal['IN_PROGRESS', 'FINISHED', 'FAILED']] = None
    name: Optional[str] = None


class DeploymentData(F5XCBaseModel):
    """Deployment status of cluster after policies deployment"""

    deployment_status: Optional[str] = None
    deployment_type: Optional[Literal['CLOUD_HOSTED', 'HOSTED', 'ON_PREM']] = None
    details: Optional[str] = None
    last_deployed_by: Optional[str] = None
    last_deployed_on: Optional[str] = None
    name: Optional[str] = None
    policies: Optional[list[str]] = None
    region: Optional[str] = None


class DeploymentHistoryData(F5XCBaseModel):
    """Deployment history of cluster after policies deployment"""

    comments: Optional[str] = None
    organization: Optional[str] = None
    policy_metadata: Optional[list[DeployPolicyMetadata]] = None
    status: Optional[str] = None
    timestamp: Optional[str] = None
    user: Optional[str] = None


class DeploymentHistoryResponse(F5XCBaseModel):
    """Response for history of cluster after policies deployment"""

    deployment_history_data: Optional[list[DeploymentHistoryData]] = None


class DeploymentStatusResponse(F5XCBaseModel):
    """Response for status of cluster after policies deployment"""

    deployment_data: Optional[list[DeploymentData]] = None


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
    """By default a summary of bot_infrastructure is returned in 'List'. By..."""

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


class SuggestValuesReq(F5XCBaseModel):
    """Request body of SuggestValues request"""

    field_path: Optional[str] = None
    match_value: Optional[str] = None
    namespace: Optional[str] = None
    request_body: Optional[ProtobufAny] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class SuggestedItem(F5XCBaseModel):
    """A tuple with a suggested value and it's description."""

    description: Optional[str] = None
    ref_value: Optional[ObjectRefType] = None
    str_value: Optional[str] = None
    title: Optional[str] = None
    value: Optional[str] = None


class SuggestValuesResp(F5XCBaseModel):
    """Response body of SuggestValues request"""

    items: Optional[list[SuggestedItem]] = None


# Convenience aliases
Spec = GetSpecType
Spec = ReplaceSpecType
Spec = CreateSpecInfraCloudHosted
Spec = CreateSpecType
