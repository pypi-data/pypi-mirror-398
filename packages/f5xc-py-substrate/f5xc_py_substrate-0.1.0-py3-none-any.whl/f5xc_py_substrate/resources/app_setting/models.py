"""Pydantic models for app_setting."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AppSettingListItem(F5XCBaseModel):
    """List item for app_setting resources."""


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class BusinessLogicMarkupSetting(F5XCBaseModel):
    """Settings specifying how API Discovery will be performed"""

    disable: Optional[Any] = None
    enable: Optional[Any] = None


class MetricSelector(F5XCBaseModel):
    """Specifies which metrics are selected to be analyzed"""

    metric: Optional[list[Literal['NO_METRICS', 'REQUEST_RATE', 'ERROR_RATE', 'LATENCY', 'THROUGHPUT']]] = None
    metrics_source: Optional[Literal['NONE', 'NODES', 'EDGES', 'VIRTUAL_HOSTS']] = None


class TimeseriesAnalysesSetting(F5XCBaseModel):
    """Configuration for DDoS Detection"""

    metric_selectors: Optional[list[MetricSelector]] = None


class FailedLoginActivitySetting(F5XCBaseModel):
    """When enabled, the system monitors persistent failed login attempts from..."""

    login_failures_threshold: Optional[int] = None


class ForbiddenActivitySetting(F5XCBaseModel):
    """When L7 policy rules are set up to disallow certain types of requests,..."""

    forbidden_requests_threshold: Optional[int] = None


class NonexistentUrlAutomaticActivitySetting(F5XCBaseModel):
    high: Optional[Any] = None
    low: Optional[Any] = None
    medium: Optional[Any] = None


class NonexistentUrlCustomActivitySetting(F5XCBaseModel):
    nonexistent_requests_threshold: Optional[int] = None


class MaliciousUserDetectionSetting(F5XCBaseModel):
    """Various factors about user activity are monitored and analysed to..."""

    bola_detection_automatic: Optional[Any] = None
    cooling_off_period: Optional[int] = None
    exclude_bola_detection: Optional[Any] = None
    exclude_bot_defense_activity: Optional[Any] = None
    exclude_failed_login_activity: Optional[Any] = None
    exclude_forbidden_activity: Optional[Any] = None
    exclude_ip_reputation: Optional[Any] = None
    exclude_non_existent_url_activity: Optional[Any] = None
    exclude_rate_limit: Optional[Any] = None
    exclude_waf_activity: Optional[Any] = None
    include_bot_defense_activity: Optional[Any] = None
    include_failed_login_activity: Optional[FailedLoginActivitySetting] = None
    include_forbidden_activity: Optional[ForbiddenActivitySetting] = None
    include_ip_reputation: Optional[Any] = None
    include_non_existent_url_activity_automatic: Optional[NonexistentUrlAutomaticActivitySetting] = None
    include_non_existent_url_activity_custom: Optional[NonexistentUrlCustomActivitySetting] = None
    include_rate_limit: Optional[Any] = None
    include_waf_activity: Optional[Any] = None


class UserBehaviorAnalysisSetting(F5XCBaseModel):
    """Configuration for user behavior analysis"""

    disable_detection: Optional[Any] = None
    disable_learning: Optional[Any] = None
    enable_detection: Optional[MaliciousUserDetectionSetting] = None
    enable_learning: Optional[Any] = None


class AppTypeSettings(F5XCBaseModel):
    """Namespace is considered an app instance which can be of one or more..."""

    app_type_ref: Optional[list[ObjectRefType]] = None
    business_logic_markup_setting: Optional[BusinessLogicMarkupSetting] = None
    timeseries_analyses_setting: Optional[TimeseriesAnalysesSetting] = None
    user_behavior_analysis_setting: Optional[UserBehaviorAnalysisSetting] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class CreateSpecType(F5XCBaseModel):
    """Create App setting configuration in namespace metadata.namespace"""

    app_type_settings: Optional[list[AppTypeSettings]] = None


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
    """Get App setting will retrieve the configuration from  namespace..."""

    app_type_settings: Optional[list[AppTypeSettings]] = None


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


class ReplaceSpecType(F5XCBaseModel):
    """Replacing an App setting will update the configuration by replacing the..."""

    app_type_settings: Optional[list[AppTypeSettings]] = None


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
    """By default a summary of app_setting is returned in 'List'. By setting..."""

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


class SuspiciousUser(F5XCBaseModel):
    """Message containing suspicious user data"""

    logs: Optional[list[str]] = None
    suspicion_score: Optional[float] = None
    user_id: Optional[str] = None


class SuspiciousUserStatusRsp(F5XCBaseModel):
    """Response message for SuspiciousUserStatusReq"""

    suspicious_users: Optional[list[SuspiciousUser]] = None


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
