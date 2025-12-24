"""Pydantic models for v1_dns_monitor."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class V1DnsMonitorListItem(F5XCBaseModel):
    """List item for v1_dns_monitor resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


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


class ObjectMetaType(F5XCBaseModel):
    """ObjectMetaType is metadata(common attributes) of an object that all..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


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


class AWSRegions(F5XCBaseModel):
    """x-example: 'us-east-1' A specific source location within AWS"""

    regions: Optional[list[str]] = None


class AWSRegionsExternal(F5XCBaseModel):
    """x-example: 'us-east-1' A specific source location within AWS"""

    regions: Optional[list[str]] = None


class DynamicThreshold(F5XCBaseModel):
    eval_period: Optional[Literal['EVAL_PERIOD_3_MINS', 'EVAL_PERIOD_5_MINS', 'EVAL_PERIOD_10_MINS', 'EVAL_PERIOD_15_MINS']] = None
    std_dev_val: Optional[Literal['STD_DEV_VAL_3', 'STD_DEV_VAL_4', 'STD_DEV_VAL_5', 'STD_DEV_VAL_6']] = None


class StaticMaxThreshold(F5XCBaseModel):
    eval_period: Optional[Literal['EVAL_PERIOD_3_MINS', 'EVAL_PERIOD_5_MINS', 'EVAL_PERIOD_10_MINS', 'EVAL_PERIOD_15_MINS']] = None
    max_response_time: Optional[int] = None


class StaticMinThreshold(F5XCBaseModel):
    eval_period: Optional[Literal['EVAL_PERIOD_3_MINS', 'EVAL_PERIOD_5_MINS', 'EVAL_PERIOD_10_MINS', 'EVAL_PERIOD_15_MINS']] = None
    min_response_time: Optional[int] = None


class HealthPolicy(F5XCBaseModel):
    dynamic_threshold: Optional[DynamicThreshold] = None
    dynamic_threshold_disabled: Optional[Any] = None
    static_max_threshold: Optional[StaticMaxThreshold] = None
    static_max_threshold_disabled: Optional[Any] = None
    static_min_threshold: Optional[StaticMinThreshold] = None
    static_min_threshold_disabled: Optional[Any] = None


class RegionalEdgeExternal(F5XCBaseModel):
    """A specific source location within F5 Distributed Cloud"""

    regions: Optional[list[str]] = None


class RegionalEdgeRegions(F5XCBaseModel):
    """A specific source location within F5 Distributed Cloud"""

    regions: Optional[list[str]] = None


class Source(F5XCBaseModel):
    """A location where a monitor runs"""

    aws: Optional[AWSRegions] = None
    f5xc: Optional[RegionalEdgeRegions] = None


class SourceExternal(F5XCBaseModel):
    """A location where a monitor runs"""

    aws: Optional[AWSRegionsExternal] = None
    f5xc: Optional[RegionalEdgeExternal] = None


class V1DnsMonitornameserver(F5XCBaseModel):
    """Custom nameserver to execute the monitor against"""

    name_server: Optional[str] = None
    port: Optional[int] = None


class V1DnsMonitorcreatespectype(F5XCBaseModel):
    """Create a new DNS Monitor"""

    domain: Optional[str] = None
    external_sources: Optional[list[SourceExternal]] = None
    health_policy: Optional[HealthPolicy] = None
    interval_12_hours: Optional[Any] = None
    interval_15_mins: Optional[Any] = None
    interval_1_day: Optional[Any] = None
    interval_1_hour: Optional[Any] = None
    interval_1_min: Optional[Any] = None
    interval_30_mins: Optional[Any] = None
    interval_30_secs: Optional[Any] = None
    interval_5_mins: Optional[Any] = None
    interval_6_hours: Optional[Any] = None
    lookup_timeout: Optional[int] = None
    name_servers: Optional[list[V1DnsMonitornameserver]] = None
    on_failure_count: Optional[int] = None
    on_failure_to_all: Optional[Any] = None
    on_failure_to_any: Optional[Any] = None
    protocol: Optional[str] = None
    receive: Optional[str] = None
    record_type: Optional[str] = None
    source_critical_threshold: Optional[int] = None


class V1DnsMonitorcreaterequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[V1DnsMonitorcreatespectype] = None


class V1DnsMonitorgetspectype(F5XCBaseModel):
    """Get a DNS Monitor"""

    domain: Optional[str] = None
    external_sources: Optional[list[SourceExternal]] = None
    health_policy: Optional[HealthPolicy] = None
    interval_12_hours: Optional[Any] = None
    interval_15_mins: Optional[Any] = None
    interval_1_day: Optional[Any] = None
    interval_1_hour: Optional[Any] = None
    interval_1_min: Optional[Any] = None
    interval_30_mins: Optional[Any] = None
    interval_30_secs: Optional[Any] = None
    interval_5_mins: Optional[Any] = None
    interval_6_hours: Optional[Any] = None
    lookup_timeout: Optional[int] = None
    name_servers: Optional[list[V1DnsMonitornameserver]] = None
    on_failure_count: Optional[int] = None
    on_failure_to_all: Optional[Any] = None
    on_failure_to_any: Optional[Any] = None
    protocol: Optional[str] = None
    receive: Optional[str] = None
    record_type: Optional[str] = None
    source_critical_threshold: Optional[int] = None


class V1DnsMonitorcreateresponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[V1DnsMonitorgetspectype] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class V1DnsMonitordeleterequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class V1DnsMonitorglobalspectype(F5XCBaseModel):
    """DNS Monitor spec"""

    domain: Optional[str] = None
    external_sources: Optional[list[Source]] = None
    health_policy: Optional[HealthPolicy] = None
    interval_12_hours: Optional[Any] = None
    interval_15_mins: Optional[Any] = None
    interval_1_day: Optional[Any] = None
    interval_1_hour: Optional[Any] = None
    interval_1_min: Optional[Any] = None
    interval_30_mins: Optional[Any] = None
    interval_30_secs: Optional[Any] = None
    interval_5_mins: Optional[Any] = None
    interval_6_hours: Optional[Any] = None
    lookup_timeout: Optional[int] = None
    name_servers: Optional[list[V1DnsMonitornameserver]] = None
    on_failure_count: Optional[int] = None
    on_failure_to_all: Optional[Any] = None
    on_failure_to_any: Optional[Any] = None
    protocol: Optional[str] = None
    receive: Optional[str] = None
    record_type: Optional[str] = None
    source_critical_threshold: Optional[int] = None


class V1DnsMonitorspectype(F5XCBaseModel):
    """Shape of the v1_dns_monitor specification"""

    gc_spec: Optional[V1DnsMonitorglobalspectype] = None


class V1DnsMonitorobject(F5XCBaseModel):
    """DNS Monitor Object"""

    metadata: Optional[ObjectMetaType] = None
    spec: Optional[V1DnsMonitorspectype] = None
    system_metadata: Optional[SystemObjectMetaType] = None


class V1DnsMonitorgetfiltereddnsmonitorlistresponse(F5XCBaseModel):
    """Response body of GetFilteredDNSMonitorList request"""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[V1DnsMonitorobject]] = None


class V1DnsMonitorreplacespectype(F5XCBaseModel):
    """Replace the contents of a DNS Monitor"""

    domain: Optional[str] = None
    external_sources: Optional[list[SourceExternal]] = None
    health_policy: Optional[HealthPolicy] = None
    interval_12_hours: Optional[Any] = None
    interval_15_mins: Optional[Any] = None
    interval_1_day: Optional[Any] = None
    interval_1_hour: Optional[Any] = None
    interval_1_min: Optional[Any] = None
    interval_30_mins: Optional[Any] = None
    interval_30_secs: Optional[Any] = None
    interval_5_mins: Optional[Any] = None
    interval_6_hours: Optional[Any] = None
    lookup_timeout: Optional[int] = None
    name_servers: Optional[list[V1DnsMonitornameserver]] = None
    on_failure_count: Optional[int] = None
    on_failure_to_all: Optional[Any] = None
    on_failure_to_any: Optional[Any] = None
    protocol: Optional[str] = None
    receive: Optional[str] = None
    record_type: Optional[str] = None
    source_critical_threshold: Optional[int] = None


class V1DnsMonitorreplacerequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[V1DnsMonitorreplacespectype] = None


class V1DnsMonitorstatusobject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


class V1DnsMonitorgetresponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[V1DnsMonitorcreaterequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[V1DnsMonitorreplacerequest] = None
    spec: Optional[V1DnsMonitorgetspectype] = None
    status: Optional[list[V1DnsMonitorstatusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class V1DnsMonitorlistresponseitem(F5XCBaseModel):
    """By default a summary of v1_dns_monitor is returned in 'List'. By setting..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[V1DnsMonitorgetspectype] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[V1DnsMonitorstatusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class V1DnsMonitorlistresponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[V1DnsMonitorlistresponseitem]] = None


class V1DnsMonitorreplaceresponse(F5XCBaseModel):
    pass


# Convenience aliases
