"""Pydantic models for service_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ServicePolicyListItem(F5XCBaseModel):
    """List item for service_policy resources."""


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


class AppFirewallAttackTypeContext(F5XCBaseModel):
    """App Firewall Attack Type context changes to be applied for this request"""

    context: Optional[Literal['CONTEXT_ANY', 'CONTEXT_BODY', 'CONTEXT_REQUEST', 'CONTEXT_RESPONSE', 'CONTEXT_PARAMETER', 'CONTEXT_HEADER', 'CONTEXT_COOKIE', 'CONTEXT_URL', 'CONTEXT_URI']] = None
    context_name: Optional[str] = None
    exclude_attack_type: Optional[Literal['ATTACK_TYPE_NONE', 'ATTACK_TYPE_NON_BROWSER_CLIENT', 'ATTACK_TYPE_OTHER_APPLICATION_ATTACKS', 'ATTACK_TYPE_TROJAN_BACKDOOR_SPYWARE', 'ATTACK_TYPE_DETECTION_EVASION', 'ATTACK_TYPE_VULNERABILITY_SCAN', 'ATTACK_TYPE_ABUSE_OF_FUNCTIONALITY', 'ATTACK_TYPE_AUTHENTICATION_AUTHORIZATION_ATTACKS', 'ATTACK_TYPE_BUFFER_OVERFLOW', 'ATTACK_TYPE_PREDICTABLE_RESOURCE_LOCATION', 'ATTACK_TYPE_INFORMATION_LEAKAGE', 'ATTACK_TYPE_DIRECTORY_INDEXING', 'ATTACK_TYPE_PATH_TRAVERSAL', 'ATTACK_TYPE_XPATH_INJECTION', 'ATTACK_TYPE_LDAP_INJECTION', 'ATTACK_TYPE_SERVER_SIDE_CODE_INJECTION', 'ATTACK_TYPE_COMMAND_EXECUTION', 'ATTACK_TYPE_SQL_INJECTION', 'ATTACK_TYPE_CROSS_SITE_SCRIPTING', 'ATTACK_TYPE_DENIAL_OF_SERVICE', 'ATTACK_TYPE_HTTP_PARSER_ATTACK', 'ATTACK_TYPE_SESSION_HIJACKING', 'ATTACK_TYPE_HTTP_RESPONSE_SPLITTING', 'ATTACK_TYPE_FORCEFUL_BROWSING', 'ATTACK_TYPE_REMOTE_FILE_INCLUDE', 'ATTACK_TYPE_MALICIOUS_FILE_UPLOAD', 'ATTACK_TYPE_GRAPHQL_PARSER_ATTACK']] = None


class BotNameContext(F5XCBaseModel):
    """Specifies bot to be excluded by its name."""

    bot_name: Optional[str] = None


class AppFirewallSignatureContext(F5XCBaseModel):
    """App Firewall signature context changes to be applied for this request"""

    context: Optional[Literal['CONTEXT_ANY', 'CONTEXT_BODY', 'CONTEXT_REQUEST', 'CONTEXT_RESPONSE', 'CONTEXT_PARAMETER', 'CONTEXT_HEADER', 'CONTEXT_COOKIE', 'CONTEXT_URL', 'CONTEXT_URI']] = None
    context_name: Optional[str] = None
    signature_id: Optional[int] = None


class AppFirewallViolationContext(F5XCBaseModel):
    """App Firewall violation context changes to be applied for this request"""

    context: Optional[Literal['CONTEXT_ANY', 'CONTEXT_BODY', 'CONTEXT_REQUEST', 'CONTEXT_RESPONSE', 'CONTEXT_PARAMETER', 'CONTEXT_HEADER', 'CONTEXT_COOKIE', 'CONTEXT_URL', 'CONTEXT_URI']] = None
    context_name: Optional[str] = None
    exclude_violation: Optional[Literal['VIOL_NONE', 'VIOL_FILETYPE', 'VIOL_METHOD', 'VIOL_MANDATORY_HEADER', 'VIOL_HTTP_RESPONSE_STATUS', 'VIOL_REQUEST_MAX_LENGTH', 'VIOL_FILE_UPLOAD', 'VIOL_FILE_UPLOAD_IN_BODY', 'VIOL_XML_MALFORMED', 'VIOL_JSON_MALFORMED', 'VIOL_ASM_COOKIE_MODIFIED', 'VIOL_HTTP_PROTOCOL_MULTIPLE_HOST_HEADERS', 'VIOL_HTTP_PROTOCOL_BAD_HOST_HEADER_VALUE', 'VIOL_HTTP_PROTOCOL_UNPARSABLE_REQUEST_CONTENT', 'VIOL_HTTP_PROTOCOL_NULL_IN_REQUEST', 'VIOL_HTTP_PROTOCOL_BAD_HTTP_VERSION', 'VIOL_HTTP_PROTOCOL_CRLF_CHARACTERS_BEFORE_REQUEST_START', 'VIOL_HTTP_PROTOCOL_NO_HOST_HEADER_IN_HTTP_1_1_REQUEST', 'VIOL_HTTP_PROTOCOL_BAD_MULTIPART_PARAMETERS_PARSING', 'VIOL_HTTP_PROTOCOL_SEVERAL_CONTENT_LENGTH_HEADERS', 'VIOL_HTTP_PROTOCOL_CONTENT_LENGTH_SHOULD_BE_A_POSITIVE_NUMBER', 'VIOL_EVASION_DIRECTORY_TRAVERSALS', 'VIOL_MALFORMED_REQUEST', 'VIOL_EVASION_MULTIPLE_DECODING', 'VIOL_DATA_GUARD', 'VIOL_EVASION_APACHE_WHITESPACE', 'VIOL_COOKIE_MODIFIED', 'VIOL_EVASION_IIS_UNICODE_CODEPOINTS', 'VIOL_EVASION_IIS_BACKSLASHES', 'VIOL_EVASION_PERCENT_U_DECODING', 'VIOL_EVASION_BARE_BYTE_DECODING', 'VIOL_EVASION_BAD_UNESCAPE', 'VIOL_HTTP_PROTOCOL_BAD_MULTIPART_FORMDATA_REQUEST_PARSING', 'VIOL_HTTP_PROTOCOL_BODY_IN_GET_OR_HEAD_REQUEST', 'VIOL_HTTP_PROTOCOL_HIGH_ASCII_CHARACTERS_IN_HEADERS', 'VIOL_ENCODING', 'VIOL_COOKIE_MALFORMED', 'VIOL_GRAPHQL_FORMAT', 'VIOL_GRAPHQL_MALFORMED', 'VIOL_GRAPHQL_INTROSPECTION_QUERY']] = None


class AppFirewallDetectionControl(F5XCBaseModel):
    """Define the list of Signature IDs, Violations, Attack Types and Bot Names..."""

    exclude_attack_type_contexts: Optional[list[AppFirewallAttackTypeContext]] = None
    exclude_bot_name_contexts: Optional[list[BotNameContext]] = None
    exclude_signature_contexts: Optional[list[AppFirewallSignatureContext]] = None
    exclude_violation_contexts: Optional[list[AppFirewallViolationContext]] = None


class MatcherType(F5XCBaseModel):
    """A matcher specifies multiple criteria for matching an input string. The..."""

    exact_values: Optional[list[str]] = None
    regex_values: Optional[list[str]] = None
    transformers: Optional[list[Literal['LOWER_CASE', 'UPPER_CASE', 'BASE64_DECODE', 'NORMALIZE_PATH', 'REMOVE_WHITESPACE', 'URL_DECODE', 'TRIM_LEFT', 'TRIM_RIGHT', 'TRIM']]] = None


class ArgMatcherType(F5XCBaseModel):
    """A argument matcher specifies the name of a single argument in the body..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    name: Optional[str] = None


class AsnMatchList(F5XCBaseModel):
    """An unordered set of RFC 6793 defined 4-byte AS numbers that can be used..."""

    as_numbers: Optional[list[int]] = None


class AsnMatcherType(F5XCBaseModel):
    """Match any AS number contained in the list of bgp_asn_sets."""

    asn_sets: Optional[list[ObjectRefType]] = None


class CookieMatcherType(F5XCBaseModel):
    """A cookie matcher specifies the name of a single cookie and the criteria..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    name: Optional[str] = None


class HttpMethodMatcherType(F5XCBaseModel):
    """A http method matcher specifies a list of methods to match an input HTTP..."""

    invert_matcher: Optional[bool] = None
    methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None


class IpMatcherType(F5XCBaseModel):
    """Match any ip prefix contained in the list of ip_prefix_sets. The result..."""

    invert_matcher: Optional[bool] = None
    prefix_sets: Optional[list[ObjectRefType]] = None


class JA4TlsFingerprintMatcherType(F5XCBaseModel):
    """An extended version of JA3 that includes additional fields for more..."""

    exact_values: Optional[list[str]] = None


class JWTClaimMatcherType(F5XCBaseModel):
    """A JWT claim matcher specifies the name of a single JWT claim and the..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    name: Optional[str] = None


class MatcherTypeBasic(F5XCBaseModel):
    """A matcher specifies multiple criteria for matching an input string. The..."""

    exact_values: Optional[list[str]] = None
    regex_values: Optional[list[str]] = None


class ModifyAction(F5XCBaseModel):
    """Modify behavior for a matching request. The modification could be to..."""

    default: Optional[Any] = None
    skip_processing: Optional[Any] = None


class PrefixMatchList(F5XCBaseModel):
    """List of IP Prefix strings to match against."""

    invert_match: Optional[bool] = None
    ip_prefixes: Optional[list[str]] = None


class RequestConstraintType(F5XCBaseModel):
    max_cookie_count_exceeds: Optional[int] = None
    max_cookie_count_none: Optional[Any] = None
    max_cookie_key_size_exceeds: Optional[int] = None
    max_cookie_key_size_none: Optional[Any] = None
    max_cookie_value_size_exceeds: Optional[int] = None
    max_cookie_value_size_none: Optional[Any] = None
    max_header_count_exceeds: Optional[int] = None
    max_header_count_none: Optional[Any] = None
    max_header_key_size_exceeds: Optional[int] = None
    max_header_key_size_none: Optional[Any] = None
    max_header_value_size_exceeds: Optional[int] = None
    max_header_value_size_none: Optional[Any] = None
    max_parameter_count_exceeds: Optional[int] = None
    max_parameter_count_none: Optional[Any] = None
    max_parameter_name_size_exceeds: Optional[int] = None
    max_parameter_name_size_none: Optional[Any] = None
    max_parameter_value_size_exceeds: Optional[int] = None
    max_parameter_value_size_none: Optional[Any] = None
    max_query_size_exceeds: Optional[int] = None
    max_query_size_none: Optional[Any] = None
    max_request_line_size_exceeds: Optional[int] = None
    max_request_line_size_none: Optional[Any] = None
    max_request_size_exceeds: Optional[int] = None
    max_request_size_none: Optional[Any] = None
    max_url_size_exceeds: Optional[int] = None
    max_url_size_none: Optional[Any] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class SegmentRefList(F5XCBaseModel):
    """List of references to Segments"""

    segments: Optional[list[ObjectRefType]] = None


class SegmentPolicyType(F5XCBaseModel):
    """Configure source and destination segment for policy"""

    dst_any: Optional[Any] = None
    dst_segments: Optional[SegmentRefList] = None
    intra_segment: Optional[Any] = None
    src_any: Optional[Any] = None
    src_segments: Optional[SegmentRefList] = None


class StringMatcherType(F5XCBaseModel):
    """A matcher specifies a list of values for matching an input string. The..."""

    invert_matcher: Optional[bool] = None
    match: Optional[list[str]] = None


class TlsFingerprintMatcherType(F5XCBaseModel):
    """A TLS fingerprint matcher specifies multiple criteria for matching a TLS..."""

    classes: Optional[list[Literal['TLS_FINGERPRINT_NONE', 'ANY_MALICIOUS_FINGERPRINT', 'ADWARE', 'ADWIND', 'DRIDEX', 'GOOTKIT', 'GOZI', 'JBIFROST', 'QUAKBOT', 'RANSOMWARE', 'TROLDESH', 'TOFSEE', 'TORRENTLOCKER', 'TRICKBOT']]] = None
    exact_values: Optional[list[str]] = None
    excluded_values: Optional[list[str]] = None


class WafAction(F5XCBaseModel):
    """Modify App Firewall behavior for a matching request. The modification..."""

    app_firewall_detection_control: Optional[AppFirewallDetectionControl] = None
    none: Optional[Any] = None
    waf_skip_processing: Optional[Any] = None


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


class LabelMatcherType(F5XCBaseModel):
    """A label matcher specifies a list of label keys whose values need to..."""

    keys: Optional[list[str]] = None


class LabelSelectorType(F5XCBaseModel):
    """This type can be used to establish a 'selector reference' from one..."""

    expressions: Optional[list[str]] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


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


class BotAction(F5XCBaseModel):
    """Modify Bot protection behavior for a matching request. The modification..."""

    bot_skip_processing: Optional[Any] = None
    none: Optional[Any] = None


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


class PortMatcherType(F5XCBaseModel):
    """A port matcher specifies a list of port ranges as match criteria. The..."""

    invert_matcher: Optional[bool] = None
    ports: Optional[list[str]] = None


class QueryParameterMatcherType(F5XCBaseModel):
    """A query parameter matcher specifies the name of a single query parameter..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    key: Optional[str] = None


class PrefixStringListType(F5XCBaseModel):
    """x-example: '192.168.20.0/24' List of IPv4 prefixes that represent an endpoint"""

    prefixes: Optional[list[str]] = None


class SourceList(F5XCBaseModel):
    """List of sources. A request belongs to this list if it satisfies any of..."""

    asn_list: Optional[AsnMatchList] = None
    asn_set: Optional[list[ObjectRefType]] = None
    country_list: Optional[list[Literal['COUNTRY_NONE', 'COUNTRY_AD', 'COUNTRY_AE', 'COUNTRY_AF', 'COUNTRY_AG', 'COUNTRY_AI', 'COUNTRY_AL', 'COUNTRY_AM', 'COUNTRY_AN', 'COUNTRY_AO', 'COUNTRY_AQ', 'COUNTRY_AR', 'COUNTRY_AS', 'COUNTRY_AT', 'COUNTRY_AU', 'COUNTRY_AW', 'COUNTRY_AX', 'COUNTRY_AZ', 'COUNTRY_BA', 'COUNTRY_BB', 'COUNTRY_BD', 'COUNTRY_BE', 'COUNTRY_BF', 'COUNTRY_BG', 'COUNTRY_BH', 'COUNTRY_BI', 'COUNTRY_BJ', 'COUNTRY_BL', 'COUNTRY_BM', 'COUNTRY_BN', 'COUNTRY_BO', 'COUNTRY_BQ', 'COUNTRY_BR', 'COUNTRY_BS', 'COUNTRY_BT', 'COUNTRY_BV', 'COUNTRY_BW', 'COUNTRY_BY', 'COUNTRY_BZ', 'COUNTRY_CA', 'COUNTRY_CC', 'COUNTRY_CD', 'COUNTRY_CF', 'COUNTRY_CG', 'COUNTRY_CH', 'COUNTRY_CI', 'COUNTRY_CK', 'COUNTRY_CL', 'COUNTRY_CM', 'COUNTRY_CN', 'COUNTRY_CO', 'COUNTRY_CR', 'COUNTRY_CS', 'COUNTRY_CU', 'COUNTRY_CV', 'COUNTRY_CW', 'COUNTRY_CX', 'COUNTRY_CY', 'COUNTRY_CZ', 'COUNTRY_DE', 'COUNTRY_DJ', 'COUNTRY_DK', 'COUNTRY_DM', 'COUNTRY_DO', 'COUNTRY_DZ', 'COUNTRY_EC', 'COUNTRY_EE', 'COUNTRY_EG', 'COUNTRY_EH', 'COUNTRY_ER', 'COUNTRY_ES', 'COUNTRY_ET', 'COUNTRY_FI', 'COUNTRY_FJ', 'COUNTRY_FK', 'COUNTRY_FM', 'COUNTRY_FO', 'COUNTRY_FR', 'COUNTRY_GA', 'COUNTRY_GB', 'COUNTRY_GD', 'COUNTRY_GE', 'COUNTRY_GF', 'COUNTRY_GG', 'COUNTRY_GH', 'COUNTRY_GI', 'COUNTRY_GL', 'COUNTRY_GM', 'COUNTRY_GN', 'COUNTRY_GP', 'COUNTRY_GQ', 'COUNTRY_GR', 'COUNTRY_GS', 'COUNTRY_GT', 'COUNTRY_GU', 'COUNTRY_GW', 'COUNTRY_GY', 'COUNTRY_HK', 'COUNTRY_HM', 'COUNTRY_HN', 'COUNTRY_HR', 'COUNTRY_HT', 'COUNTRY_HU', 'COUNTRY_ID', 'COUNTRY_IE', 'COUNTRY_IL', 'COUNTRY_IM', 'COUNTRY_IN', 'COUNTRY_IO', 'COUNTRY_IQ', 'COUNTRY_IR', 'COUNTRY_IS', 'COUNTRY_IT', 'COUNTRY_JE', 'COUNTRY_JM', 'COUNTRY_JO', 'COUNTRY_JP', 'COUNTRY_KE', 'COUNTRY_KG', 'COUNTRY_KH', 'COUNTRY_KI', 'COUNTRY_KM', 'COUNTRY_KN', 'COUNTRY_KP', 'COUNTRY_KR', 'COUNTRY_KW', 'COUNTRY_KY', 'COUNTRY_KZ', 'COUNTRY_LA', 'COUNTRY_LB', 'COUNTRY_LC', 'COUNTRY_LI', 'COUNTRY_LK', 'COUNTRY_LR', 'COUNTRY_LS', 'COUNTRY_LT', 'COUNTRY_LU', 'COUNTRY_LV', 'COUNTRY_LY', 'COUNTRY_MA', 'COUNTRY_MC', 'COUNTRY_MD', 'COUNTRY_ME', 'COUNTRY_MF', 'COUNTRY_MG', 'COUNTRY_MH', 'COUNTRY_MK', 'COUNTRY_ML', 'COUNTRY_MM', 'COUNTRY_MN', 'COUNTRY_MO', 'COUNTRY_MP', 'COUNTRY_MQ', 'COUNTRY_MR', 'COUNTRY_MS', 'COUNTRY_MT', 'COUNTRY_MU', 'COUNTRY_MV', 'COUNTRY_MW', 'COUNTRY_MX', 'COUNTRY_MY', 'COUNTRY_MZ', 'COUNTRY_NA', 'COUNTRY_NC', 'COUNTRY_NE', 'COUNTRY_NF', 'COUNTRY_NG', 'COUNTRY_NI', 'COUNTRY_NL', 'COUNTRY_NO', 'COUNTRY_NP', 'COUNTRY_NR', 'COUNTRY_NU', 'COUNTRY_NZ', 'COUNTRY_OM', 'COUNTRY_PA', 'COUNTRY_PE', 'COUNTRY_PF', 'COUNTRY_PG', 'COUNTRY_PH', 'COUNTRY_PK', 'COUNTRY_PL', 'COUNTRY_PM', 'COUNTRY_PN', 'COUNTRY_PR', 'COUNTRY_PS', 'COUNTRY_PT', 'COUNTRY_PW', 'COUNTRY_PY', 'COUNTRY_QA', 'COUNTRY_RE', 'COUNTRY_RO', 'COUNTRY_RS', 'COUNTRY_RU', 'COUNTRY_RW', 'COUNTRY_SA', 'COUNTRY_SB', 'COUNTRY_SC', 'COUNTRY_SD', 'COUNTRY_SE', 'COUNTRY_SG', 'COUNTRY_SH', 'COUNTRY_SI', 'COUNTRY_SJ', 'COUNTRY_SK', 'COUNTRY_SL', 'COUNTRY_SM', 'COUNTRY_SN', 'COUNTRY_SO', 'COUNTRY_SR', 'COUNTRY_SS', 'COUNTRY_ST', 'COUNTRY_SV', 'COUNTRY_SX', 'COUNTRY_SY', 'COUNTRY_SZ', 'COUNTRY_TC', 'COUNTRY_TD', 'COUNTRY_TF', 'COUNTRY_TG', 'COUNTRY_TH', 'COUNTRY_TJ', 'COUNTRY_TK', 'COUNTRY_TL', 'COUNTRY_TM', 'COUNTRY_TN', 'COUNTRY_TO', 'COUNTRY_TR', 'COUNTRY_TT', 'COUNTRY_TV', 'COUNTRY_TW', 'COUNTRY_TZ', 'COUNTRY_UA', 'COUNTRY_UG', 'COUNTRY_UM', 'COUNTRY_US', 'COUNTRY_UY', 'COUNTRY_UZ', 'COUNTRY_VA', 'COUNTRY_VC', 'COUNTRY_VE', 'COUNTRY_VG', 'COUNTRY_VI', 'COUNTRY_VN', 'COUNTRY_VU', 'COUNTRY_WF', 'COUNTRY_WS', 'COUNTRY_XK', 'COUNTRY_XT', 'COUNTRY_YE', 'COUNTRY_YT', 'COUNTRY_ZA', 'COUNTRY_ZM', 'COUNTRY_ZW']]] = None
    default_action_allow: Optional[Any] = None
    default_action_deny: Optional[Any] = None
    default_action_next_policy: Optional[Any] = None
    ip_prefix_set: Optional[list[ObjectRefType]] = None
    prefix_list: Optional[PrefixStringListType] = None
    tls_fingerprint_classes: Optional[list[Literal['TLS_FINGERPRINT_NONE', 'ANY_MALICIOUS_FINGERPRINT', 'ADWARE', 'ADWIND', 'DRIDEX', 'GOOTKIT', 'GOZI', 'JBIFROST', 'QUAKBOT', 'RANSOMWARE', 'TROLDESH', 'TOFSEE', 'TORRENTLOCKER', 'TRICKBOT']]] = None
    tls_fingerprint_values: Optional[list[str]] = None


class IPThreatCategoryListType(F5XCBaseModel):
    """List of ip threat categories"""

    ip_threat_categories: Optional[list[Literal['SPAM_SOURCES', 'WINDOWS_EXPLOITS', 'WEB_ATTACKS', 'BOTNETS', 'SCANNERS', 'REPUTATION', 'PHISHING', 'PROXY', 'MOBILE_THREATS', 'TOR_PROXY', 'DENIAL_OF_SERVICE', 'NETWORK']]] = None


class GlobalSpecType(F5XCBaseModel):
    """Shape of service_policy_rule in the storage backend."""

    action: Optional[Literal['DENY', 'ALLOW', 'NEXT_POLICY']] = None
    any_asn: Optional[Any] = None
    any_client: Optional[Any] = None
    any_ip: Optional[Any] = None
    api_group_matcher: Optional[StringMatcherType] = None
    arg_matchers: Optional[list[ArgMatcherType]] = None
    asn_list: Optional[AsnMatchList] = None
    asn_matcher: Optional[AsnMatcherType] = None
    body_matcher: Optional[MatcherType] = None
    bot_action: Optional[BotAction] = None
    client_name: Optional[str] = None
    client_name_matcher: Optional[MatcherType] = None
    client_selector: Optional[LabelSelectorType] = None
    cookie_matchers: Optional[list[CookieMatcherType]] = None
    domain_matcher: Optional[MatcherType] = None
    expiration_timestamp: Optional[str] = None
    headers: Optional[list[HeaderMatcherType]] = None
    http_method: Optional[HttpMethodMatcherType] = None
    ip_matcher: Optional[IpMatcherType] = None
    ip_prefix_list: Optional[PrefixMatchList] = None
    ip_threat_category_list: Optional[IPThreatCategoryListType] = None
    ja4_tls_fingerprint: Optional[JA4TlsFingerprintMatcherType] = None
    jwt_claims: Optional[list[JWTClaimMatcherType]] = None
    label_matcher: Optional[LabelMatcherType] = None
    mum_action: Optional[ModifyAction] = None
    path: Optional[PathMatcherType] = None
    port_matcher: Optional[PortMatcherType] = None
    query_params: Optional[list[QueryParameterMatcherType]] = None
    request_constraints: Optional[RequestConstraintType] = None
    segment_policy: Optional[SegmentPolicyType] = None
    tls_fingerprint_matcher: Optional[TlsFingerprintMatcherType] = None
    user_identity_matcher: Optional[MatcherTypeBasic] = None
    waf_action: Optional[WafAction] = None


class Rule(F5XCBaseModel):
    """A Rule consists of an unordered list of predicates and an action. The..."""

    metadata: Optional[MessageMetaType] = None
    spec: Optional[GlobalSpecType] = None


class RuleList(F5XCBaseModel):
    """A list of rules. The order of evaluation of the rules depends on the..."""

    rules: Optional[list[Rule]] = None


class CreateSpecType(F5XCBaseModel):
    """Create service_policy creates a new object in the storage backend for..."""

    allow_all_requests: Optional[Any] = None
    allow_list: Optional[SourceList] = None
    any_server: Optional[Any] = None
    deny_all_requests: Optional[Any] = None
    deny_list: Optional[SourceList] = None
    rule_list: Optional[RuleList] = None
    server_name: Optional[str] = None
    server_name_matcher: Optional[MatcherTypeBasic] = None
    server_selector: Optional[LabelSelectorType] = None


class LegacyRuleList(F5XCBaseModel):
    """A list of references to service_policy_rule objects. The order of..."""

    rules: Optional[list[ObjectRefType]] = None


class GetSpecType(F5XCBaseModel):
    """Get service_policy reads a given object from storage backend for..."""

    allow_all_requests: Optional[Any] = None
    allow_list: Optional[SourceList] = None
    any_server: Optional[Any] = None
    deny_all_requests: Optional[Any] = None
    deny_list: Optional[SourceList] = None
    legacy_rule_list: Optional[LegacyRuleList] = None
    rule_list: Optional[RuleList] = None
    server_name: Optional[str] = None
    server_name_matcher: Optional[MatcherTypeBasic] = None
    server_selector: Optional[LabelSelectorType] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace service_policy replaces an existing object in the storage..."""

    allow_all_requests: Optional[Any] = None
    allow_list: Optional[SourceList] = None
    any_server: Optional[Any] = None
    deny_all_requests: Optional[Any] = None
    deny_list: Optional[SourceList] = None
    legacy_rule_list: Optional[LegacyRuleList] = None
    rule_list: Optional[RuleList] = None
    server_name: Optional[str] = None
    server_name_matcher: Optional[MatcherTypeBasic] = None
    server_selector: Optional[LabelSelectorType] = None


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[CreateSpecType] = None


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[GetSpecType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class DeleteRequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


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


class ListResponseItem(F5XCBaseModel):
    """By default a summary of service_policy is returned in 'List'. By setting..."""

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


class HitsId(F5XCBaseModel):
    """ServicePolicyHitsId uniquely identifies an entry in the response to..."""

    action: Optional[str] = None
    namespace: Optional[str] = None
    policy: Optional[str] = None
    policy_rule: Optional[str] = None
    policy_set: Optional[str] = None
    site: Optional[str] = None
    virtual_host: Optional[str] = None


class Hits(F5XCBaseModel):
    """ServicePolicyHits contains the timeseries data of Service policy hits"""

    id_: Optional[HitsId] = Field(default=None, alias="id")
    metric: Optional[list[MetricValue]] = None


class HitsResponse(F5XCBaseModel):
    """Number of Service policy rule hits for each unique combination of..."""

    data: Optional[list[Hits]] = None
    step: Optional[str] = None


# Convenience aliases
Spec = GlobalSpecType
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
