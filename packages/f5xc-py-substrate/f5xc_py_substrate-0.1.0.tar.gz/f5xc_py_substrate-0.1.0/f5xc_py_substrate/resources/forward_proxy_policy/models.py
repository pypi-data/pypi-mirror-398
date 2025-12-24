"""Pydantic models for forward_proxy_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ForwardProxyPolicyListItem(F5XCBaseModel):
    """List item for forward_proxy_policy resources."""


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


class L4DestType(F5XCBaseModel):
    """L4 Destination consisting of IPv4 Prefixes and TCP Port Range"""

    ipv6_prefixes: Optional[list[str]] = None
    port_ranges: Optional[str] = None
    prefixes: Optional[list[str]] = None


class URLType(F5XCBaseModel):
    """URL strings in form 'http://<domian>/<path>'"""

    any_path: Optional[Any] = None
    exact_value: Optional[str] = None
    path_exact_value: Optional[str] = None
    path_prefix_value: Optional[str] = None
    path_regex_value: Optional[str] = None
    regex_value: Optional[str] = None
    suffix_value: Optional[str] = None


class DomainType(F5XCBaseModel):
    """Domains names"""

    exact_value: Optional[str] = None
    regex_value: Optional[str] = None
    suffix_value: Optional[str] = None


class ForwardProxySimpleRuleType(F5XCBaseModel):
    """URL(s) and domains policy for forward proxy for a connection type (TLS or HTTP)"""

    default_action_allow: Optional[Any] = None
    default_action_deny: Optional[Any] = None
    default_action_next_policy: Optional[Any] = None
    dest_list: Optional[list[L4DestType]] = None
    http_list: Optional[list[URLType]] = None
    tls_list: Optional[list[DomainType]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class LabelSelectorType(F5XCBaseModel):
    """This type can be used to establish a 'selector reference' from one..."""

    expressions: Optional[list[str]] = None


class AsnMatchList(F5XCBaseModel):
    """An unordered set of RFC 6793 defined 4-byte AS numbers that can be used..."""

    as_numbers: Optional[list[int]] = None


class PrefixStringListType(F5XCBaseModel):
    """x-example: '192.168.20.0/24' List of IPv4 prefixes that represent an endpoint"""

    prefixes: Optional[list[str]] = None


class URLListType(F5XCBaseModel):
    http_list: Optional[list[URLType]] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class PortMatcherType(F5XCBaseModel):
    """A port matcher specifies a list of port ranges as match criteria. The..."""

    invert_matcher: Optional[bool] = None
    ports: Optional[list[str]] = None


class DomainListType(F5XCBaseModel):
    tls_list: Optional[list[DomainType]] = None


class URLCategoryListType(F5XCBaseModel):
    """List of url categories"""

    url_categories: Optional[list[Literal['UNCATEGORIZED', 'REAL_ESTATE', 'COMPUTER_AND_INTERNET_SECURITY', 'FINANCIAL_SERVICES', 'BUSINESS_AND_ECONOMY', 'COMPUTER_AND_INTERNET_INFO', 'AUCTIONS', 'SHOPPING', 'CULT_AND_OCCULT', 'TRAVEL', 'ABUSED_DRUGS', 'ADULT_AND_PORNOGRAPHY', 'HOME_AND_GARDEN', 'MILITARY', 'SOCIAL_NETWORKING', 'DEAD_SITES', 'INDIVIDUAL_STOCK_ADVICE_AND_TOOLS', 'TRAINING_AND_TOOLS', 'DATING', 'SEX_EDUCATION', 'RELIGION', 'ENTERTAINMENT_AND_ARTS', 'PERSONAL_SITES_AND_BLOGS', 'LEGAL', 'LOCAL_INFORMATION', 'STREAMING_MEDIA', 'JOB_SEARCH', 'GAMBLING', 'TRANSLATION', 'REFERENCE_AND_RESEARCH', 'SHAREWARE_AND_FREEWARE', 'PEER_TO_PEER', 'MARIJUANA', 'HACKING', 'GAMES', 'PHILOSOPHY_AND_POLITICAL_ADVOCACY', 'WEAPONS', 'PAY_TO_SURF', 'HUNTING_AND_FISHING', 'SOCIETY', 'EDUCATIONAL_INSTITUTIONS', 'ONLINE_GREETING_CARDS', 'SPORTS', 'SWIMSUITS_AND_INTIMATE_APPAREL', 'QUESTIONABLE', 'KIDS', 'HATE_AND_RACISM', 'PERSONAL_STORAGE', 'VIOLENCE', 'KEYLOGGERS_AND_MONITORING', 'SEARCH_ENGINES', 'INTERNET_PORTALS', 'WEB_ADVERTISEMENTS', 'CHEATING', 'GROSS', 'WEB_BASED_EMAIL', 'MALWARE_SITES', 'PHISHING_AND_OTHER_FRAUDS', 'PROXY_AVOIDANCE_AND_ANONYMIZERS', 'SPYWARE_AND_ADWARE', 'MUSIC', 'GOVERNMENT', 'NUDITY', 'NEWS_AND_MEDIA', 'ILLEGAL', 'CONTENT_DELIVERY_NETWORKS', 'INTERNET_COMMUNICATIONS', 'BOT_NETS', 'ABORTION', 'HEALTH_AND_MEDICINE', 'CONFIRMED_SPAM_SOURCES', 'SPAM_URLS', 'UNCONFIRMED_SPAM_SOURCES', 'OPEN_HTTP_PROXIES', 'DYNAMICALLY_GENERATED_CONTENT', 'PARKED_DOMAINS', 'ALCOHOL_AND_TOBACCO', 'PRIVATE_IP_ADDRESSES', 'IMAGE_AND_VIDEO_SEARCH', 'FASHION_AND_BEAUTY', 'RECREATION_AND_HOBBIES', 'MOTOR_VEHICLES', 'WEB_HOSTING']]] = None


class ForwardProxyAdvancedRuleType(F5XCBaseModel):
    """URL(s) and domains policy for forward proxy for a connection type (TLS or HTTP)"""

    action: Optional[Literal['DENY', 'ALLOW', 'NEXT_POLICY']] = None
    all_destinations: Optional[Any] = None
    all_sources: Optional[Any] = None
    dst_asn_list: Optional[AsnMatchList] = None
    dst_asn_set: Optional[ObjectRefType] = None
    dst_ip_prefix_set: Optional[ObjectRefType] = None
    dst_label_selector: Optional[LabelSelectorType] = None
    dst_prefix_list: Optional[PrefixStringListType] = None
    http_list: Optional[URLListType] = None
    ip_prefix_set: Optional[ObjectRefType] = None
    label_selector: Optional[LabelSelectorType] = None
    metadata: Optional[MessageMetaType] = None
    no_http_connect_port: Optional[Any] = None
    port_matcher: Optional[PortMatcherType] = None
    prefix_list: Optional[PrefixStringListType] = None
    tls_list: Optional[DomainListType] = None
    url_category_list: Optional[URLCategoryListType] = None


class ForwardProxyRuleListType(F5XCBaseModel):
    """List of custom rules"""

    rules: Optional[list[ForwardProxyAdvancedRuleType]] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the Forward Proxy Policy specification"""

    allow_all: Optional[Any] = None
    allow_list: Optional[ForwardProxySimpleRuleType] = None
    any_proxy: Optional[Any] = None
    deny_list: Optional[ForwardProxySimpleRuleType] = None
    drp_http_connect: Optional[Any] = None
    network_connector: Optional[ObjectRefType] = None
    proxy_label_selector: Optional[LabelSelectorType] = None
    rule_list: Optional[ForwardProxyRuleListType] = None


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
    """Shape of the Forward Proxy Policy specification"""

    allow_all: Optional[Any] = None
    allow_list: Optional[ForwardProxySimpleRuleType] = None
    any_proxy: Optional[Any] = None
    deny_list: Optional[ForwardProxySimpleRuleType] = None
    drp_http_connect: Optional[Any] = None
    network_connector: Optional[ObjectRefType] = None
    proxy_label_selector: Optional[LabelSelectorType] = None
    rule_list: Optional[ForwardProxyRuleListType] = None


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
    """ForwardProxyPolicyHitsId uniquely identifies an entry in the response to..."""

    action: Optional[str] = None
    namespace: Optional[str] = None
    policy: Optional[str] = None
    policy_rule: Optional[str] = None
    site: Optional[str] = None
    virtual_host: Optional[str] = None


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
    """ForwardProxyPolicyHits contains the timeseries data of forward proxy policy hits"""

    id_: Optional[HitsId] = Field(default=None, alias="id")
    metric: Optional[list[MetricValue]] = None


class MetricLabelFilter(F5XCBaseModel):
    """Label filter can be specified to filter metrics based on label match"""

    label: Optional[Literal['NAMESPACE', 'POLICY', 'POLICY_RULE', 'ACTION', 'SITE', 'VIRTUAL_HOST']] = None
    op: Optional[Literal['EQ', 'NEQ']] = None
    value: Optional[str] = None


class HitsRequest(F5XCBaseModel):
    """Request to get the forward proxy policy hits counter."""

    end_time: Optional[str] = None
    group_by: Optional[list[Literal['NAMESPACE', 'POLICY', 'POLICY_RULE', 'ACTION', 'SITE', 'VIRTUAL_HOST']]] = None
    label_filter: Optional[list[MetricLabelFilter]] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class HitsResponse(F5XCBaseModel):
    """Number of forward proxy policy rule hits for each unique combination of..."""

    data: Optional[list[Hits]] = None
    step: Optional[str] = None


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
    """Shape of the Forward Proxy Policy replace specification"""

    allow_all: Optional[Any] = None
    allow_list: Optional[ForwardProxySimpleRuleType] = None
    any_proxy: Optional[Any] = None
    deny_list: Optional[ForwardProxySimpleRuleType] = None
    drp_http_connect: Optional[Any] = None
    network_connector: Optional[ObjectRefType] = None
    proxy_label_selector: Optional[LabelSelectorType] = None
    rule_list: Optional[ForwardProxyRuleListType] = None


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
    """By default a summary of forward_proxy_policy is returned in 'List'. By..."""

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
