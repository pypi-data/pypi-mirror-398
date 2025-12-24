"""Pydantic models for cdn_cache_rule."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class CdnCacheRuleListItem(F5XCBaseModel):
    """List item for cdn_cache_rule resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class CacheTTLEnableProps(F5XCBaseModel):
    """Cache TTL Enable Values"""

    cache_override: Optional[bool] = None
    cache_ttl: Optional[str] = None
    ignore_response_cookie: Optional[bool] = None


class CacheEligibleOptions(F5XCBaseModel):
    """List of options for Cache Action"""

    scheme_proxy_host_request_uri: Optional[CacheTTLEnableProps] = None
    scheme_proxy_host_uri: Optional[CacheTTLEnableProps] = None


class CacheOperator(F5XCBaseModel):
    contains: Optional[str] = Field(default=None, alias="Contains")
    does_not_contain: Optional[str] = Field(default=None, alias="DoesNotContain")
    does_not_end_with: Optional[str] = Field(default=None, alias="DoesNotEndWith")
    does_not_equal: Optional[str] = Field(default=None, alias="DoesNotEqual")
    does_not_start_with: Optional[str] = Field(default=None, alias="DoesNotStartWith")
    endswith: Optional[str] = Field(default=None, alias="Endswith")
    equals: Optional[str] = Field(default=None, alias="Equals")
    match_regex: Optional[str] = Field(default=None, alias="MatchRegex")
    startswith: Optional[str] = Field(default=None, alias="Startswith")


class CacheHeaderMatcherType(F5XCBaseModel):
    """Header match is done using the name of the header and its value. The..."""

    name: Optional[Literal['PROXY_HOST', 'REFERER', 'SCHEME', 'USER_AGENT']] = None
    operator: Optional[CacheOperator] = None


class CacheCookieMatcherType(F5XCBaseModel):
    """A cookie matcher specifies the name of a single cookie and the criteria..."""

    name: Optional[str] = None
    operator: Optional[CacheOperator] = None


class CDNPathMatcherType(F5XCBaseModel):
    """Path match of the URI can be either be, Prefix match or exact match or..."""

    operator: Optional[CacheOperator] = None


class CacheQueryParameterMatcherType(F5XCBaseModel):
    """Query parameter match can be either regex match on value or exact match..."""

    key: Optional[str] = None
    operator: Optional[CacheOperator] = None


class CDNCacheRuleExpression(F5XCBaseModel):
    """Select one of the field options"""

    cache_headers: Optional[list[CacheHeaderMatcherType]] = None
    cookie_matcher: Optional[list[CacheCookieMatcherType]] = None
    path_match: Optional[CDNPathMatcherType] = None
    query_parameters: Optional[list[CacheQueryParameterMatcherType]] = None


class CDNCacheRuleExpressionList(F5XCBaseModel):
    """CDN Cache Rule Expressions."""

    cache_rule_expression: Optional[list[CDNCacheRuleExpression]] = None
    expression_name: Optional[str] = None


class CDNCacheRule(F5XCBaseModel):
    """This defines a CDN Cache Rule"""

    cache_bypass: Optional[Any] = None
    eligible_for_cache: Optional[CacheEligibleOptions] = None
    rule_expression_list: Optional[list[CDNCacheRuleExpressionList]] = None
    rule_name: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the CDN loadbalancer specification"""

    cache_rules: Optional[CDNCacheRule] = None


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
    """Shape of the CDN loadbalancer specification"""

    cache_rules: Optional[CDNCacheRule] = None


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
    """Shape of the CDN loadbalancer specification"""

    cache_rules: Optional[CDNCacheRule] = None


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
    """By default a summary of cdn_cache_rule is returned in 'List'. By setting..."""

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
