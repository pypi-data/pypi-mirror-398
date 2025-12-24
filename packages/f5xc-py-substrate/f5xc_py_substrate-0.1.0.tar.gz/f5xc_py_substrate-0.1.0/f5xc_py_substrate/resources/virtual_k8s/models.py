"""Pydantic models for virtual_k8s."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class VirtualK8sListItem(F5XCBaseModel):
    """List item for virtual_k8s resources."""


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


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


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


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
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


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class VirtualK8screatespectype(F5XCBaseModel):
    """Create virtual_k8s will create the object in the storage backend for..."""

    default_flavor_ref: Optional[ObjectRefType] = None
    disabled: Optional[Any] = None
    isolated: Optional[Any] = None
    vsite_refs: Optional[list[ObjectRefType]] = None


class VirtualK8screaterequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[VirtualK8screatespectype] = None


class VirtualK8sgetspectype(F5XCBaseModel):
    """Get virtual_k8s will get the object from the storage backend for..."""

    default_flavor_ref: Optional[ObjectRefType] = None
    disabled: Optional[Any] = None
    isolated: Optional[Any] = None
    vsite_refs: Optional[list[ObjectRefType]] = None


class VirtualK8screateresponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[VirtualK8sgetspectype] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class VirtualK8sdeleterequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class VirtualK8sreplacespectype(F5XCBaseModel):
    """Replacing an endpoint object will update the object by replacing the..."""

    default_flavor_ref: Optional[ObjectRefType] = None
    disabled: Optional[Any] = None
    isolated: Optional[Any] = None
    vsite_refs: Optional[list[ObjectRefType]] = None


class VirtualK8sreplacerequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[VirtualK8sreplacespectype] = None


class VirtualK8sstatusobject(F5XCBaseModel):
    """Most recently observed status of the Virtual K8s object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


class VirtualK8sgetresponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[VirtualK8screaterequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[VirtualK8sreplacerequest] = None
    spec: Optional[VirtualK8sgetspectype] = None
    status: Optional[list[VirtualK8sstatusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class VirtualK8slistresponseitem(F5XCBaseModel):
    """By default a summary of virtual_k8s is returned in 'List'. By setting..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[VirtualK8sgetspectype] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[VirtualK8sstatusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class VirtualK8slistresponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[VirtualK8slistresponseitem]] = None


class VirtualK8spvcmetrictypedata(F5XCBaseModel):
    """PVC Metric Type Data contains key/value pair that uniquely identifies..."""

    key: Optional[dict[str, Any]] = None
    value: Optional[list[MetricValue]] = None


class VirtualK8spvcmetricdata(F5XCBaseModel):
    """PVC Metric data contains the metric type and the corresponding metric value"""

    data: Optional[list[VirtualK8spvcmetrictypedata]] = None
    type_: Optional[Literal['PVC_USAGE', 'PVC_CAPACITY']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None


class VirtualK8spvcmetricsrequest(F5XCBaseModel):
    """Request to get the metrics for PVC"""

    end_time: Optional[str] = None
    field_selector: Optional[list[Literal['PVC_USAGE', 'PVC_CAPACITY']]] = None
    filter: Optional[str] = None
    group_by: Optional[list[Literal['NAMESPACE', 'PVC', 'SITE']]] = None
    namespace: Optional[str] = None
    range: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class VirtualK8spvcmetricsresponse(F5XCBaseModel):
    """Metrics response for PVC"""

    data: Optional[list[VirtualK8spvcmetricdata]] = None
    step: Optional[str] = None


class VirtualK8sreplaceresponse(F5XCBaseModel):
    pass


# Convenience aliases
