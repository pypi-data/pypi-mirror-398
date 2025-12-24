"""Pydantic models for bot_defense_app_infrastructure."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class BotDefenseAppInfrastructureListItem(F5XCBaseModel):
    """List item for bot_defense_app_infrastructure resources."""


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class Egress(F5XCBaseModel):
    """Egress"""

    ip_address: Optional[str] = None
    location: Optional[Literal['AWS_AP_NORTHEAST_1', 'AWS_AP_NORTHEAST_3', 'AWS_AP_SOUTH_1', 'AWS_AP_SOUTH_2', 'AWS_AP_SOUTHEAST_1', 'AWS_AP_SOUTHEAST_2', 'AWS_AP_SOUTHEAST_3', 'AWS_EU_CENTRAL_1', 'AWS_EU_NORTH_1', 'AWS_EU_WEST_1', 'AWS_ME_SOUTH_1', 'AWS_SA_EAST_1', 'AWS_US_EAST_1', 'AWS_US_EAST_2', 'AWS_US_WEST_1', 'AWS_US_WEST_2', 'GCP_ASIA_EAST_1', 'GCP_ASIA_EAST_2', 'GCP_ASIA_NORTHEAST_1', 'GCP_ASIA_NORTHEAST_2', 'GCP_ASIA_NORTHEAST_3', 'GCP_ASIA_SOUTH_1', 'GCP_ASIA_SOUTHEAST_1', 'GCP_ASIA_SOUTHEAST_2', 'GCP_AUSTRALIA_SOUTHEAST_1', 'GCP_EUROPE_WEST_1', 'GCP_EUROPE_WEST_2', 'GCP_EUROPE_WEST_3', 'GCP_NORTHAMERICA_NORTHEAST_1', 'GCP_NORTHAMERICA_NORTHEAST_2', 'GCP_SOUTHAMERICA_EAST_1', 'GCP_SOUTHAMERICA_WEST_1', 'GCP_US_CENTRAL_1', 'GCP_US_EAST_1', 'GCP_US_EAST_4', 'GCP_US_WEST_1', 'GCP_US_WEST_2']] = None


class Ingress(F5XCBaseModel):
    """Ingress"""

    host_name: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[Literal['AWS_AP_NORTHEAST_1', 'AWS_AP_NORTHEAST_3', 'AWS_AP_SOUTH_1', 'AWS_AP_SOUTH_2', 'AWS_AP_SOUTHEAST_1', 'AWS_AP_SOUTHEAST_2', 'AWS_AP_SOUTHEAST_3', 'AWS_EU_CENTRAL_1', 'AWS_EU_NORTH_1', 'AWS_EU_WEST_1', 'AWS_ME_SOUTH_1', 'AWS_SA_EAST_1', 'AWS_US_EAST_1', 'AWS_US_EAST_2', 'AWS_US_WEST_1', 'AWS_US_WEST_2', 'GCP_ASIA_EAST_1', 'GCP_ASIA_EAST_2', 'GCP_ASIA_NORTHEAST_1', 'GCP_ASIA_NORTHEAST_2', 'GCP_ASIA_NORTHEAST_3', 'GCP_ASIA_SOUTH_1', 'GCP_ASIA_SOUTHEAST_1', 'GCP_ASIA_SOUTHEAST_2', 'GCP_AUSTRALIA_SOUTHEAST_1', 'GCP_EUROPE_WEST_1', 'GCP_EUROPE_WEST_2', 'GCP_EUROPE_WEST_3', 'GCP_NORTHAMERICA_NORTHEAST_1', 'GCP_NORTHAMERICA_NORTHEAST_2', 'GCP_SOUTHAMERICA_EAST_1', 'GCP_SOUTHAMERICA_WEST_1', 'GCP_US_CENTRAL_1', 'GCP_US_EAST_1', 'GCP_US_EAST_4', 'GCP_US_WEST_1', 'GCP_US_WEST_2']] = None


class InfraF5Hosted(F5XCBaseModel):
    """Infra F5 Hosted"""

    egress: Optional[list[Egress]] = None
    infra_host_name: Optional[str] = None
    ingress: Optional[list[Ingress]] = None
    region: Optional[Literal['US', 'EU', 'ASIA']] = None


class CreateSpecType(F5XCBaseModel):
    """Creates Bot Defense App Infrastructure in a given namespace."""

    cloud_hosted: Optional[InfraF5Hosted] = None
    data_center_hosted: Optional[InfraF5Hosted] = None
    environment_type: Optional[Literal['PRODUCTION', 'TESTING']] = None
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


class GetSpecType(F5XCBaseModel):
    """Get Bot Defense App Infrastructure from a given namespace."""

    cloud_hosted: Optional[InfraF5Hosted] = None
    data_center_hosted: Optional[InfraF5Hosted] = None
    environment_type: Optional[Literal['PRODUCTION', 'TESTING']] = None
    traffic_type: Optional[Literal['WEB', 'MOBILE']] = None


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
    """Replace a given Bot Defense App Infrastructure in a given namespace."""

    cloud_hosted: Optional[InfraF5Hosted] = None
    data_center_hosted: Optional[InfraF5Hosted] = None
    environment_type: Optional[Literal['PRODUCTION', 'TESTING']] = None
    traffic_type: Optional[Literal['WEB', 'MOBILE']] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[CreateRequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[ReplaceRequest] = None
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
    """By default a summary of bot_defense_app_infrastructure is returned in..."""

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


class ReplaceResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
