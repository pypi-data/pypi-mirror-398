"""Pydantic models for dns_load_balancer."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class DnsLoadBalancerListItem(F5XCBaseModel):
    """List item for dns_load_balancer resources."""


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ResponseCacheParameters(F5XCBaseModel):
    cache_cidr_ipv4: Optional[int] = None
    cache_cidr_ipv6: Optional[int] = None
    cache_ttl: Optional[int] = None


class ResponseCache(F5XCBaseModel):
    """Response Cache x-required"""

    default_response_cache_parameters: Optional[Any] = None
    disable: Optional[Any] = None
    response_cache_parameters: Optional[ResponseCacheParameters] = None


class AsnMatchList(F5XCBaseModel):
    """An unordered set of RFC 6793 defined 4-byte AS numbers that can be used..."""

    as_numbers: Optional[list[int]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class AsnMatcherType(F5XCBaseModel):
    """Match any AS number contained in the list of bgp_asn_sets."""

    asn_sets: Optional[list[ObjectRefType]] = None


class LabelSelectorType(F5XCBaseModel):
    """This type can be used to establish a 'selector reference' from one..."""

    expressions: Optional[list[str]] = None


class PrefixMatchList(F5XCBaseModel):
    """List of IP Prefix strings to match against."""

    invert_match: Optional[bool] = None
    ip_prefixes: Optional[list[str]] = None


class IpMatcherType(F5XCBaseModel):
    """Match any ip prefix contained in the list of ip_prefix_sets. The result..."""

    invert_matcher: Optional[bool] = None
    prefix_sets: Optional[list[ObjectRefType]] = None


class LoadBalancingRule(F5XCBaseModel):
    asn_list: Optional[AsnMatchList] = None
    asn_matcher: Optional[AsnMatcherType] = None
    geo_location_label_selector: Optional[LabelSelectorType] = None
    geo_location_set: Optional[ObjectRefType] = None
    ip_prefix_list: Optional[PrefixMatchList] = None
    ip_prefix_set: Optional[IpMatcherType] = None
    pool: Optional[ObjectRefType] = None
    score: Optional[int] = None


class LoadBalancingRuleList(F5XCBaseModel):
    """List of the Load Balancing Rules"""

    rules: Optional[list[LoadBalancingRule]] = None


class CreateSpecType(F5XCBaseModel):
    """Create DNS Load Balancer in a given namespace. If one already exist it..."""

    fallback_pool: Optional[ObjectRefType] = None
    record_type: Optional[Literal['A', 'AAAA', 'MX', 'CNAME', 'SRV']] = None
    response_cache: Optional[ResponseCache] = None
    rule_list: Optional[LoadBalancingRuleList] = None


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
    """Get DNS Load Balancer details."""

    dns_zones: Optional[list[ObjectRefType]] = None
    fallback_pool: Optional[ObjectRefType] = None
    record_type: Optional[Literal['A', 'AAAA', 'MX', 'CNAME', 'SRV']] = None
    response_cache: Optional[ResponseCache] = None
    rule_list: Optional[LoadBalancingRuleList] = None


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


class HealthStatusSummary(F5XCBaseModel):
    """Health Status Summary"""

    count: Optional[list[MetricValue]] = None
    status: Optional[Literal['HEALTH_STATUS_UNHEALTHY', 'HEALTH_STATUS_DEGRADED', 'HEALTH_STATUS_HEALTHY', 'HEALTH_STATUS_DISABLED']] = None


class DNSLBHealthStatusListResponseItem(F5XCBaseModel):
    """Individual item in a collection of DNS Load Balancer"""

    dns_lb_pools_status_summary: Optional[list[HealthStatusSummary]] = None
    name: Optional[str] = None
    status: Optional[list[MetricValue]] = None


class DNSLBHealthStatusListResponse(F5XCBaseModel):
    """Response for DNS Load Balancer Health Status List Request"""

    dns_lb_pools_status_summary: Optional[list[HealthStatusSummary]] = None
    dns_load_balancer_status_summary: Optional[list[HealthStatusSummary]] = None
    items: Optional[list[DNSLBHealthStatusListResponseItem]] = None


class DNSLBPoolHealthStatusListResponseItem(F5XCBaseModel):
    """Individual item in a collection of DNS Load Balancer Pool"""

    dns_lb_pool_members_status_summary: Optional[list[HealthStatusSummary]] = None
    health_check_type: Optional[str] = None
    name: Optional[str] = None
    status: Optional[list[MetricValue]] = None


class DNSLBHealthStatusResponse(F5XCBaseModel):
    """Response for DNS Load Balancer Health Status Request"""

    dns_lb_pool_items: Optional[list[DNSLBPoolHealthStatusListResponseItem]] = None
    status: Optional[list[MetricValue]] = None


class DNSLBPoolMemberHealthStatusListResponseItem(F5XCBaseModel):
    """Individual item in a collection of DNS Load Balancer Pool Member"""

    dns_lb_name: Optional[str] = None
    dns_lb_pool_name: Optional[str] = None
    error_code: Optional[Literal['ERR_NIL', 'ERR_UNDEFINED', 'ERR_RECEIVE_STRING_MISMATCH', 'ERR_INTERNAL', 'ERR_MSG_SEND', 'ERR_TIMEOUT', 'ERR_MSG_RECEIVE', 'ERR_MAX_RECEIVE_BYTES', 'ERR_ICMP_PING', 'ERR_CONNECTION_REFUSED', 'ERR_CONNECTION_ABORTED', 'ERR_CONNECTION_RESET', 'ERR_NET_UN_REACHABLE', 'ERR_HOST_UN_REACHABLE', 'ERR_UNKNOWN', 'ERR_TLS_HANDSHAKE_FAILURE', 'ERR_CONNECTION_TIMEDOUT']] = None
    error_description: Optional[str] = None
    health_check_type: Optional[str] = None
    http_status_code: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None
    name: Optional[str] = None
    ports: Optional[list[int]] = None
    status: Optional[list[MetricValue]] = None
    unhealthy_ports: Optional[list[int]] = None


class DNSLBPoolHealthStatusResponse(F5XCBaseModel):
    """Response for DNS Load Balancer Pool Health Status Request"""

    dns_lb_pool_member_items: Optional[list[DNSLBPoolMemberHealthStatusListResponseItem]] = None
    status: Optional[list[MetricValue]] = None


class DNSLBPoolMemberHealthStatusEvent(F5XCBaseModel):
    """Pool member health status change event data"""

    error_code: Optional[Literal['ERR_NIL', 'ERR_UNDEFINED', 'ERR_RECEIVE_STRING_MISMATCH', 'ERR_INTERNAL', 'ERR_MSG_SEND', 'ERR_TIMEOUT', 'ERR_MSG_RECEIVE', 'ERR_MAX_RECEIVE_BYTES', 'ERR_ICMP_PING', 'ERR_CONNECTION_REFUSED', 'ERR_CONNECTION_ABORTED', 'ERR_CONNECTION_RESET', 'ERR_NET_UN_REACHABLE', 'ERR_HOST_UN_REACHABLE', 'ERR_UNKNOWN', 'ERR_TLS_HANDSHAKE_FAILURE', 'ERR_CONNECTION_TIMEDOUT']] = None
    error_description: Optional[str] = None
    pool_member_address: Optional[str] = None
    status: Optional[list[MetricValue]] = None


class DNSLBPoolMemberHealthStatusListResponse(F5XCBaseModel):
    """Response for DNS Load Balancer Pool Member Health Status List Request"""

    items: Optional[list[DNSLBPoolMemberHealthStatusListResponseItem]] = None


class DNSLBPoolMemberHealthStatusResponse(F5XCBaseModel):
    """Response for DNS Load Balancer Pool Member Health Status Events Request"""

    dns_lb_pool_member_events: Optional[list[DNSLBPoolMemberHealthStatusEvent]] = None


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
    """Replace DNS Load Balancer in a given namespace."""

    fallback_pool: Optional[ObjectRefType] = None
    record_type: Optional[Literal['A', 'AAAA', 'MX', 'CNAME', 'SRV']] = None
    response_cache: Optional[ResponseCache] = None
    rule_list: Optional[LoadBalancingRuleList] = None


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
    """By default a summary of dns_load_balancer is returned in 'List'. By..."""

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


class SuggestedItem(F5XCBaseModel):
    """A tuple with a suggested value and it's description."""

    description: Optional[str] = None
    ref_value: Optional[ObjectRefType] = None
    str_value: Optional[str] = None


class SuggestValuesResp(F5XCBaseModel):
    """Response body of SuggestValues request"""

    items: Optional[list[SuggestedItem]] = None


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
