"""Pydantic models for network_policy_view."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class NetworkPolicyViewListItem(F5XCBaseModel):
    """List item for network_policy_view resources."""


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


class ApplicationsType(F5XCBaseModel):
    """Application protocols like HTTP, SNMP"""

    applications: Optional[list[Literal['APPLICATION_HTTP', 'APPLICATION_HTTPS', 'APPLICATION_SNMP', 'APPLICATION_DNS']]] = None


class LabelSelectorType(F5XCBaseModel):
    """This type can be used to establish a 'selector reference' from one..."""

    expressions: Optional[list[str]] = None


class PrefixStringListType(F5XCBaseModel):
    """x-example: '192.168.20.0/24' List of IPv4 prefixes that represent an endpoint"""

    prefixes: Optional[list[str]] = None


class EndpointChoiceType(F5XCBaseModel):
    """Shape of the endpoint choices for a view"""

    any: Optional[Any] = None
    inside_endpoints: Optional[Any] = None
    label_selector: Optional[LabelSelectorType] = None
    outside_endpoints: Optional[Any] = None
    prefix_list: Optional[PrefixStringListType] = None


class NetworkPolicyRuleAdvancedAction(F5XCBaseModel):
    """Network Policy Rule Advanced Action provides additional options along..."""

    action: Optional[Literal['NOLOG', 'LOG']] = None


class IpPrefixSetRefType(F5XCBaseModel):
    """A list of references to ip_prefix_set objects."""

    ref: Optional[list[ObjectRefType]] = None


class LabelMatcherType(F5XCBaseModel):
    """A label matcher specifies a list of label keys whose values need to..."""

    keys: Optional[list[str]] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class ProtocolPortType(F5XCBaseModel):
    """Protocol and Port ranges"""

    port_ranges: Optional[list[str]] = None
    protocol: Optional[str] = None


class NetworkPolicyRuleType(F5XCBaseModel):
    """Shape of Network Policy Rule"""

    action: Optional[Literal['DENY', 'ALLOW']] = None
    adv_action: Optional[NetworkPolicyRuleAdvancedAction] = None
    all_tcp_traffic: Optional[Any] = None
    all_traffic: Optional[Any] = None
    all_udp_traffic: Optional[Any] = None
    any: Optional[Any] = None
    applications: Optional[ApplicationsType] = None
    inside_endpoints: Optional[Any] = None
    ip_prefix_set: Optional[IpPrefixSetRefType] = None
    label_matcher: Optional[LabelMatcherType] = None
    label_selector: Optional[LabelSelectorType] = None
    metadata: Optional[MessageMetaType] = None
    outside_endpoints: Optional[Any] = None
    prefix_list: Optional[PrefixStringListType] = None
    protocol_port_range: Optional[ProtocolPortType] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the Network policy view specification"""

    egress_rules: Optional[list[NetworkPolicyRuleType]] = None
    endpoint: Optional[EndpointChoiceType] = None
    ingress_rules: Optional[list[NetworkPolicyRuleType]] = None


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
    """Shape of the Network policy view specification"""

    egress_rules: Optional[list[NetworkPolicyRuleType]] = None
    endpoint: Optional[EndpointChoiceType] = None
    ingress_rules: Optional[list[NetworkPolicyRuleType]] = None


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
    """Shape of the Network policy view replace specification"""

    egress_rules: Optional[list[NetworkPolicyRuleType]] = None
    endpoint: Optional[EndpointChoiceType] = None
    ingress_rules: Optional[list[NetworkPolicyRuleType]] = None


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
    """By default a summary of network_policy_view is returned in 'List'. By..."""

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


class NetworkPolicyHitsId(F5XCBaseModel):
    """NetworkPolicyHitsId uniquely identifies an entry in the response to..."""

    action: Optional[str] = None
    namespace: Optional[str] = None
    policy: Optional[str] = None
    policy_rule: Optional[str] = None
    site: Optional[str] = None


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


class NetworkPolicyHits(F5XCBaseModel):
    """NetworkPolicyHits contains the timeseries data of network policy hits"""

    id_: Optional[NetworkPolicyHitsId] = Field(default=None, alias="id")
    metric: Optional[list[MetricValue]] = None


class NetworkPolicyMetricLabelFilter(F5XCBaseModel):
    """Label filter can be specified to filter metrics based on label match"""

    label: Optional[Literal['NAMESPACE', 'POLICY', 'POLICY_RULE', 'ACTION', 'SITE']] = None
    op: Optional[Literal['EQ', 'NEQ']] = None
    value: Optional[str] = None


class NetworkPolicyHitsRequest(F5XCBaseModel):
    """Request to get the network policy hits counter."""

    end_time: Optional[str] = None
    group_by: Optional[list[Literal['NAMESPACE', 'POLICY', 'POLICY_RULE', 'ACTION', 'SITE']]] = None
    label_filter: Optional[list[NetworkPolicyMetricLabelFilter]] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class NetworkPolicyHitsResponse(F5XCBaseModel):
    """Number of network policy rule hits for each unique combination of..."""

    data: Optional[list[NetworkPolicyHits]] = None
    step: Optional[str] = None


class ReplaceResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
