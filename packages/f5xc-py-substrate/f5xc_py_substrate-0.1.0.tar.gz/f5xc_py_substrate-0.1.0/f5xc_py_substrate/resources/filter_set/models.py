"""Pydantic models for filter_set."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class FilterSetListItem(F5XCBaseModel):
    """List item for filter_set resources."""


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class DateRange(F5XCBaseModel):
    """Date range is for selecting a date range"""

    end_date: Optional[str] = None
    start_date: Optional[str] = None


class FilterTimeRangeField(F5XCBaseModel):
    """either an absolute time range or a relative time interval"""

    absolute: Optional[DateRange] = None
    relative: Optional[str] = None


class FilterExpressionField(F5XCBaseModel):
    expression: Optional[str] = None


class FilterStringField(F5XCBaseModel):
    field_values: Optional[list[str]] = None


class Field(F5XCBaseModel):
    """a field ID and its value selected by the user"""

    date_field: Optional[FilterTimeRangeField] = None
    field_id: Optional[str] = None
    filter_expression_field: Optional[FilterExpressionField] = None
    string_field: Optional[FilterStringField] = None


class CreateSpecType(F5XCBaseModel):
    """Create specification"""

    context_key: Optional[str] = None
    filter_fields: Optional[list[Field]] = None


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
    """Get specification"""

    context_key: Optional[str] = None
    filter_fields: Optional[list[Field]] = None


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


class FindFilterSetsReq(F5XCBaseModel):
    """Find Filter Sets API returns FilterSets that match the given context key(s)"""

    context_keys: Optional[list[str]] = None
    namespace: Optional[str] = None


class ObjectMetaType(F5XCBaseModel):
    """ObjectMetaType is metadata(common attributes) of an object that all..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    """Global specification"""

    context_key: Optional[str] = None
    filter_fields: Optional[list[Field]] = None


class SpecType(F5XCBaseModel):
    """Shape of the Filter Set specification. This not exposed to customers"""

    gc_spec: Optional[GlobalSpecType] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class SystemObjectMetaType(F5XCBaseModel):
    """SystemObjectMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_cookie: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    direct_ref_hash: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    namespace: Optional[list[ObjectRefType]] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    revision: Optional[str] = None
    sre_disable: Optional[bool] = None
    tenant: Optional[str] = None
    trace_info: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class Object(F5XCBaseModel):
    """Filter Set object"""

    metadata: Optional[ObjectMetaType] = None
    spec: Optional[SpecType] = None
    system_metadata: Optional[SystemObjectMetaType] = None


class FindFilterSetsRsp(F5XCBaseModel):
    """Response for Find Filter Sets API"""

    filter_sets: Optional[list[Object]] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace specification"""

    context_key: Optional[str] = None
    filter_fields: Optional[list[Field]] = None


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
    """Most recently observed status of the object"""

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
    """By default a summary of filter_set is returned in 'List'. By setting..."""

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
Spec = GlobalSpecType
Spec = SpecType
Spec = ReplaceSpecType
