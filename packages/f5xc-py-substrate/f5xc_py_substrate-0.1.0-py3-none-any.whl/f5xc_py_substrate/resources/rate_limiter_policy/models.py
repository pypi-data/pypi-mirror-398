"""Pydantic models for rate_limiter_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class RateLimiterPolicyListItem(F5XCBaseModel):
    """List item for rate_limiter_policy resources."""


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


class AsnMatchList(F5XCBaseModel):
    """An unordered set of RFC 6793 defined 4-byte AS numbers that can be used..."""

    as_numbers: Optional[list[int]] = None


class AsnMatcherType(F5XCBaseModel):
    """Match any AS number contained in the list of bgp_asn_sets."""

    asn_sets: Optional[list[ObjectRefType]] = None


class CountryCodeList(F5XCBaseModel):
    """List of Country Codes to match against."""

    country_codes: Optional[list[Literal['COUNTRY_NONE', 'COUNTRY_AD', 'COUNTRY_AE', 'COUNTRY_AF', 'COUNTRY_AG', 'COUNTRY_AI', 'COUNTRY_AL', 'COUNTRY_AM', 'COUNTRY_AN', 'COUNTRY_AO', 'COUNTRY_AQ', 'COUNTRY_AR', 'COUNTRY_AS', 'COUNTRY_AT', 'COUNTRY_AU', 'COUNTRY_AW', 'COUNTRY_AX', 'COUNTRY_AZ', 'COUNTRY_BA', 'COUNTRY_BB', 'COUNTRY_BD', 'COUNTRY_BE', 'COUNTRY_BF', 'COUNTRY_BG', 'COUNTRY_BH', 'COUNTRY_BI', 'COUNTRY_BJ', 'COUNTRY_BL', 'COUNTRY_BM', 'COUNTRY_BN', 'COUNTRY_BO', 'COUNTRY_BQ', 'COUNTRY_BR', 'COUNTRY_BS', 'COUNTRY_BT', 'COUNTRY_BV', 'COUNTRY_BW', 'COUNTRY_BY', 'COUNTRY_BZ', 'COUNTRY_CA', 'COUNTRY_CC', 'COUNTRY_CD', 'COUNTRY_CF', 'COUNTRY_CG', 'COUNTRY_CH', 'COUNTRY_CI', 'COUNTRY_CK', 'COUNTRY_CL', 'COUNTRY_CM', 'COUNTRY_CN', 'COUNTRY_CO', 'COUNTRY_CR', 'COUNTRY_CS', 'COUNTRY_CU', 'COUNTRY_CV', 'COUNTRY_CW', 'COUNTRY_CX', 'COUNTRY_CY', 'COUNTRY_CZ', 'COUNTRY_DE', 'COUNTRY_DJ', 'COUNTRY_DK', 'COUNTRY_DM', 'COUNTRY_DO', 'COUNTRY_DZ', 'COUNTRY_EC', 'COUNTRY_EE', 'COUNTRY_EG', 'COUNTRY_EH', 'COUNTRY_ER', 'COUNTRY_ES', 'COUNTRY_ET', 'COUNTRY_FI', 'COUNTRY_FJ', 'COUNTRY_FK', 'COUNTRY_FM', 'COUNTRY_FO', 'COUNTRY_FR', 'COUNTRY_GA', 'COUNTRY_GB', 'COUNTRY_GD', 'COUNTRY_GE', 'COUNTRY_GF', 'COUNTRY_GG', 'COUNTRY_GH', 'COUNTRY_GI', 'COUNTRY_GL', 'COUNTRY_GM', 'COUNTRY_GN', 'COUNTRY_GP', 'COUNTRY_GQ', 'COUNTRY_GR', 'COUNTRY_GS', 'COUNTRY_GT', 'COUNTRY_GU', 'COUNTRY_GW', 'COUNTRY_GY', 'COUNTRY_HK', 'COUNTRY_HM', 'COUNTRY_HN', 'COUNTRY_HR', 'COUNTRY_HT', 'COUNTRY_HU', 'COUNTRY_ID', 'COUNTRY_IE', 'COUNTRY_IL', 'COUNTRY_IM', 'COUNTRY_IN', 'COUNTRY_IO', 'COUNTRY_IQ', 'COUNTRY_IR', 'COUNTRY_IS', 'COUNTRY_IT', 'COUNTRY_JE', 'COUNTRY_JM', 'COUNTRY_JO', 'COUNTRY_JP', 'COUNTRY_KE', 'COUNTRY_KG', 'COUNTRY_KH', 'COUNTRY_KI', 'COUNTRY_KM', 'COUNTRY_KN', 'COUNTRY_KP', 'COUNTRY_KR', 'COUNTRY_KW', 'COUNTRY_KY', 'COUNTRY_KZ', 'COUNTRY_LA', 'COUNTRY_LB', 'COUNTRY_LC', 'COUNTRY_LI', 'COUNTRY_LK', 'COUNTRY_LR', 'COUNTRY_LS', 'COUNTRY_LT', 'COUNTRY_LU', 'COUNTRY_LV', 'COUNTRY_LY', 'COUNTRY_MA', 'COUNTRY_MC', 'COUNTRY_MD', 'COUNTRY_ME', 'COUNTRY_MF', 'COUNTRY_MG', 'COUNTRY_MH', 'COUNTRY_MK', 'COUNTRY_ML', 'COUNTRY_MM', 'COUNTRY_MN', 'COUNTRY_MO', 'COUNTRY_MP', 'COUNTRY_MQ', 'COUNTRY_MR', 'COUNTRY_MS', 'COUNTRY_MT', 'COUNTRY_MU', 'COUNTRY_MV', 'COUNTRY_MW', 'COUNTRY_MX', 'COUNTRY_MY', 'COUNTRY_MZ', 'COUNTRY_NA', 'COUNTRY_NC', 'COUNTRY_NE', 'COUNTRY_NF', 'COUNTRY_NG', 'COUNTRY_NI', 'COUNTRY_NL', 'COUNTRY_NO', 'COUNTRY_NP', 'COUNTRY_NR', 'COUNTRY_NU', 'COUNTRY_NZ', 'COUNTRY_OM', 'COUNTRY_PA', 'COUNTRY_PE', 'COUNTRY_PF', 'COUNTRY_PG', 'COUNTRY_PH', 'COUNTRY_PK', 'COUNTRY_PL', 'COUNTRY_PM', 'COUNTRY_PN', 'COUNTRY_PR', 'COUNTRY_PS', 'COUNTRY_PT', 'COUNTRY_PW', 'COUNTRY_PY', 'COUNTRY_QA', 'COUNTRY_RE', 'COUNTRY_RO', 'COUNTRY_RS', 'COUNTRY_RU', 'COUNTRY_RW', 'COUNTRY_SA', 'COUNTRY_SB', 'COUNTRY_SC', 'COUNTRY_SD', 'COUNTRY_SE', 'COUNTRY_SG', 'COUNTRY_SH', 'COUNTRY_SI', 'COUNTRY_SJ', 'COUNTRY_SK', 'COUNTRY_SL', 'COUNTRY_SM', 'COUNTRY_SN', 'COUNTRY_SO', 'COUNTRY_SR', 'COUNTRY_SS', 'COUNTRY_ST', 'COUNTRY_SV', 'COUNTRY_SX', 'COUNTRY_SY', 'COUNTRY_SZ', 'COUNTRY_TC', 'COUNTRY_TD', 'COUNTRY_TF', 'COUNTRY_TG', 'COUNTRY_TH', 'COUNTRY_TJ', 'COUNTRY_TK', 'COUNTRY_TL', 'COUNTRY_TM', 'COUNTRY_TN', 'COUNTRY_TO', 'COUNTRY_TR', 'COUNTRY_TT', 'COUNTRY_TV', 'COUNTRY_TW', 'COUNTRY_TZ', 'COUNTRY_UA', 'COUNTRY_UG', 'COUNTRY_UM', 'COUNTRY_US', 'COUNTRY_UY', 'COUNTRY_UZ', 'COUNTRY_VA', 'COUNTRY_VC', 'COUNTRY_VE', 'COUNTRY_VG', 'COUNTRY_VI', 'COUNTRY_VN', 'COUNTRY_VU', 'COUNTRY_WF', 'COUNTRY_WS', 'COUNTRY_XK', 'COUNTRY_XT', 'COUNTRY_YE', 'COUNTRY_YT', 'COUNTRY_ZA', 'COUNTRY_ZM', 'COUNTRY_ZW']]] = None
    invert_match: Optional[bool] = None


class HttpMethodMatcherType(F5XCBaseModel):
    """A http method matcher specifies a list of methods to match an input HTTP..."""

    invert_matcher: Optional[bool] = None
    methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None


class IpMatcherType(F5XCBaseModel):
    """Match any ip prefix contained in the list of ip_prefix_sets. The result..."""

    invert_matcher: Optional[bool] = None
    prefix_sets: Optional[list[ObjectRefType]] = None


class MatcherType(F5XCBaseModel):
    """A matcher specifies multiple criteria for matching an input string. The..."""

    exact_values: Optional[list[str]] = None
    regex_values: Optional[list[str]] = None
    transformers: Optional[list[Literal['LOWER_CASE', 'UPPER_CASE', 'BASE64_DECODE', 'NORMALIZE_PATH', 'REMOVE_WHITESPACE', 'URL_DECODE', 'TRIM_LEFT', 'TRIM_RIGHT', 'TRIM']]] = None


class MatcherTypeBasic(F5XCBaseModel):
    """A matcher specifies multiple criteria for matching an input string. The..."""

    exact_values: Optional[list[str]] = None
    regex_values: Optional[list[str]] = None


class PrefixMatchList(F5XCBaseModel):
    """List of IP Prefix strings to match against."""

    invert_match: Optional[bool] = None
    ip_prefixes: Optional[list[str]] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class HeaderMatcherType(F5XCBaseModel):
    """A header matcher specifies the name of a single HTTP header and the..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    name: Optional[str] = None


class PathMatcherType(F5XCBaseModel):
    """A path matcher specifies multiple criteria for matching an HTTP path..."""

    exact_values: Optional[list[str]] = None
    invert_matcher: Optional[bool] = None
    prefix_values: Optional[list[str]] = None
    regex_values: Optional[list[str]] = None
    suffix_values: Optional[list[str]] = None
    transformers: Optional[list[Literal['LOWER_CASE', 'UPPER_CASE', 'BASE64_DECODE', 'NORMALIZE_PATH', 'REMOVE_WHITESPACE', 'URL_DECODE', 'TRIM_LEFT', 'TRIM_RIGHT', 'TRIM']]] = None


class RateLimiterRuleSpec(F5XCBaseModel):
    """Shape of Rate Limiter Rule"""

    any_asn: Optional[Any] = None
    any_country: Optional[Any] = None
    any_ip: Optional[Any] = None
    apply_rate_limiter: Optional[Any] = None
    asn_list: Optional[AsnMatchList] = None
    asn_matcher: Optional[AsnMatcherType] = None
    bypass_rate_limiter: Optional[Any] = None
    country_list: Optional[CountryCodeList] = None
    custom_rate_limiter: Optional[ObjectRefType] = None
    domain_matcher: Optional[MatcherTypeBasic] = None
    headers: Optional[list[HeaderMatcherType]] = None
    http_method: Optional[HttpMethodMatcherType] = None
    ip_matcher: Optional[IpMatcherType] = None
    ip_prefix_list: Optional[PrefixMatchList] = None
    path: Optional[PathMatcherType] = None


class RateLimiterRule(F5XCBaseModel):
    """Shape of Rate Limiter Rule"""

    metadata: Optional[MessageMetaType] = None
    spec: Optional[RateLimiterRuleSpec] = None


class LabelSelectorType(F5XCBaseModel):
    """This type can be used to establish a 'selector reference' from one..."""

    expressions: Optional[list[str]] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the Rate Limiter Policy Create specification"""

    any_server: Optional[Any] = None
    rules: Optional[list[RateLimiterRule]] = None
    server_name: Optional[str] = None
    server_name_matcher: Optional[MatcherTypeBasic] = None
    server_selector: Optional[LabelSelectorType] = None


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
    """Shape of the Rate Limiter Policy Get specification"""

    any_server: Optional[Any] = None
    rules: Optional[list[RateLimiterRule]] = None
    server_name: Optional[str] = None
    server_name_matcher: Optional[MatcherTypeBasic] = None
    server_selector: Optional[LabelSelectorType] = None


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
    """Shape of the Rate Limiter Policy Replace specification"""

    any_server: Optional[Any] = None
    rules: Optional[list[RateLimiterRule]] = None
    server_name: Optional[str] = None
    server_name_matcher: Optional[MatcherTypeBasic] = None
    server_selector: Optional[LabelSelectorType] = None


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


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of rate_limiter_policy is returned in 'List'. By..."""

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
Spec = RateLimiterRuleSpec
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
