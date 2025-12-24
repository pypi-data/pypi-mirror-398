"""Pydantic models for enhanced_firewall_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class EnhancedFirewallPolicyListItem(F5XCBaseModel):
    """List item for enhanced_firewall_policy resources."""


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class PrefixListType(F5XCBaseModel):
    """List of IP Address prefixes. Prefix must contain both prefix and..."""

    prefix: Optional[list[str]] = None


class NetworkPolicyRuleAdvancedAction(F5XCBaseModel):
    """Network Policy Rule Advanced Action provides additional options along..."""

    action: Optional[Literal['NOLOG', 'LOG']] = None


class ApplicationsType(F5XCBaseModel):
    """Application protocols like HTTP, SNMP"""

    applications: Optional[list[Literal['APPLICATION_HTTP', 'APPLICATION_HTTPS', 'APPLICATION_SNMP', 'APPLICATION_DNS']]] = None


class AwsVpcList(F5XCBaseModel):
    """List of VPC Identifiers in AWS"""

    vpc_id: Optional[list[str]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class IpPrefixSetRefType(F5XCBaseModel):
    """A list of references to ip_prefix_set objects."""

    ref: Optional[list[ObjectRefType]] = None


class LabelSelectorType(F5XCBaseModel):
    """This type can be used to establish a 'selector reference' from one..."""

    expressions: Optional[list[str]] = None


class PrefixStringListType(F5XCBaseModel):
    """x-example: '192.168.20.0/24' List of IPv4 prefixes that represent an endpoint"""

    prefixes: Optional[list[str]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class ServiceActionType(F5XCBaseModel):
    """Action to forward traffic to external service"""

    nfv_service: Optional[ObjectRefType] = None


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


class RuleType(F5XCBaseModel):
    """Enhanced Firewall Policy rules definition"""

    advanced_action: Optional[NetworkPolicyRuleAdvancedAction] = None
    all_destinations: Optional[Any] = None
    all_sli_vips: Optional[Any] = None
    all_slo_vips: Optional[Any] = None
    all_sources: Optional[Any] = None
    all_tcp_traffic: Optional[Any] = None
    all_traffic: Optional[Any] = None
    all_udp_traffic: Optional[Any] = None
    allow: Optional[Any] = None
    applications: Optional[ApplicationsType] = None
    deny: Optional[Any] = None
    destination_aws_vpc_ids: Optional[AwsVpcList] = None
    destination_ip_prefix_set: Optional[IpPrefixSetRefType] = None
    destination_label_selector: Optional[LabelSelectorType] = None
    destination_prefix_list: Optional[PrefixStringListType] = None
    insert_service: Optional[ServiceActionType] = None
    inside_destinations: Optional[Any] = None
    inside_sources: Optional[Any] = None
    label_matcher: Optional[LabelMatcherType] = None
    metadata: Optional[MessageMetaType] = None
    outside_destinations: Optional[Any] = None
    outside_sources: Optional[Any] = None
    protocol_port_range: Optional[ProtocolPortType] = None
    source_aws_vpc_ids: Optional[AwsVpcList] = None
    source_ip_prefix_set: Optional[IpPrefixSetRefType] = None
    source_label_selector: Optional[LabelSelectorType] = None
    source_prefix_list: Optional[PrefixStringListType] = None


class RuleListType(F5XCBaseModel):
    """Custom Enhanced Firewall Policy Rules"""

    rules: Optional[list[RuleType]] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of Enhanced Firewall Policy specification"""

    allow_all: Optional[Any] = None
    allowed_destinations: Optional[PrefixListType] = None
    allowed_sources: Optional[PrefixListType] = None
    denied_destinations: Optional[PrefixListType] = None
    denied_sources: Optional[PrefixListType] = None
    deny_all: Optional[Any] = None
    rule_list: Optional[RuleListType] = None


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
    """Shape of the Enhanced Firewall Policy specification"""

    allow_all: Optional[Any] = None
    allowed_destinations: Optional[PrefixListType] = None
    allowed_sources: Optional[PrefixListType] = None
    denied_destinations: Optional[PrefixListType] = None
    denied_sources: Optional[PrefixListType] = None
    deny_all: Optional[Any] = None
    rule_list: Optional[RuleListType] = None


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


class HitsId(F5XCBaseModel):
    """EnhancedFirewallPolicyHitsId uniquely identifies an entry in the..."""

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


class Hits(F5XCBaseModel):
    """EnhancedFirewallPolicyHits contains the timeseries data of Enhanced..."""

    id_: Optional[HitsId] = Field(default=None, alias="id")
    metric: Optional[list[MetricValue]] = None


class MetricLabelFilter(F5XCBaseModel):
    """Label filter can be specified to filter metrics based on label match"""

    label: Optional[Literal['NAMESPACE', 'POLICY', 'POLICY_RULE', 'ACTION', 'SITE']] = None
    op: Optional[Literal['EQ', 'NEQ']] = None
    value: Optional[str] = None


class HitsRequest(F5XCBaseModel):
    """Request to get the Enhanced Firewall Policy hits counter."""

    end_time: Optional[str] = None
    group_by: Optional[list[Literal['NAMESPACE', 'POLICY', 'POLICY_RULE', 'ACTION', 'SITE']]] = None
    label_filter: Optional[list[MetricLabelFilter]] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class HitsResponse(F5XCBaseModel):
    """Number of Enhanced Firewall Policy rule hits for each unique combination..."""

    data: Optional[list[Hits]] = None
    step: Optional[str] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Shape of Enhanced Firewall Policy replace specification"""

    allow_all: Optional[Any] = None
    allowed_destinations: Optional[PrefixListType] = None
    allowed_sources: Optional[PrefixListType] = None
    denied_destinations: Optional[PrefixListType] = None
    denied_sources: Optional[PrefixListType] = None
    deny_all: Optional[Any] = None
    rule_list: Optional[RuleListType] = None


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
    """By default a summary of enhanced_firewall_policy is returned in 'List'...."""

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
Spec = ReplaceSpecType
