"""Pydantic models for app_security."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class GetSuggestedAPIEndpointProtectionRuleReq(F5XCBaseModel):
    """Get suggested API endpoint protection rule for a given path"""

    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    path: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class APIProtectionRuleAction(F5XCBaseModel):
    """The action to take if the input request matches the rule."""

    allow: Optional[Any] = None
    deny: Optional[Any] = None


class HttpMethodMatcherType(F5XCBaseModel):
    """A http method matcher specifies a list of methods to match an input HTTP..."""

    invert_matcher: Optional[bool] = None
    methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None


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


class IpMatcherType(F5XCBaseModel):
    """Match any ip prefix contained in the list of ip_prefix_sets. The result..."""

    invert_matcher: Optional[bool] = None
    prefix_sets: Optional[list[ObjectRefType]] = None


class PrefixMatchList(F5XCBaseModel):
    """List of IP Prefix strings to match against."""

    invert_match: Optional[bool] = None
    ip_prefixes: Optional[list[str]] = None


class IPThreatCategoryListType(F5XCBaseModel):
    """List of ip threat categories"""

    ip_threat_categories: Optional[list[Literal['SPAM_SOURCES', 'WINDOWS_EXPLOITS', 'WEB_ATTACKS', 'BOTNETS', 'SCANNERS', 'REPUTATION', 'PHISHING', 'PROXY', 'MOBILE_THREATS', 'TOR_PROXY', 'DENIAL_OF_SERVICE', 'NETWORK']]] = None


class TlsFingerprintMatcherType(F5XCBaseModel):
    """A TLS fingerprint matcher specifies multiple criteria for matching a TLS..."""

    classes: Optional[list[Literal['TLS_FINGERPRINT_NONE', 'ANY_MALICIOUS_FINGERPRINT', 'ADWARE', 'ADWIND', 'DRIDEX', 'GOOTKIT', 'GOZI', 'JBIFROST', 'QUAKBOT', 'RANSOMWARE', 'TROLDESH', 'TOFSEE', 'TORRENTLOCKER', 'TRICKBOT']]] = None
    exact_values: Optional[list[str]] = None
    excluded_values: Optional[list[str]] = None


class ClientMatcher(F5XCBaseModel):
    """Client conditions for matching a rule"""

    any_client: Optional[Any] = None
    any_ip: Optional[Any] = None
    asn_list: Optional[AsnMatchList] = None
    asn_matcher: Optional[AsnMatcherType] = None
    client_selector: Optional[LabelSelectorType] = None
    ip_matcher: Optional[IpMatcherType] = None
    ip_prefix_list: Optional[PrefixMatchList] = None
    ip_threat_category_list: Optional[IPThreatCategoryListType] = None
    tls_fingerprint_matcher: Optional[TlsFingerprintMatcherType] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class MatcherType(F5XCBaseModel):
    """A matcher specifies multiple criteria for matching an input string. The..."""

    exact_values: Optional[list[str]] = None
    regex_values: Optional[list[str]] = None
    transformers: Optional[list[Literal['LOWER_CASE', 'UPPER_CASE', 'BASE64_DECODE', 'NORMALIZE_PATH', 'REMOVE_WHITESPACE', 'URL_DECODE', 'TRIM_LEFT', 'TRIM_RIGHT', 'TRIM']]] = None


class CookieMatcherType(F5XCBaseModel):
    """A cookie matcher specifies the name of a single cookie and the criteria..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    name: Optional[str] = None


class HeaderMatcherType(F5XCBaseModel):
    """A header matcher specifies the name of a single HTTP header and the..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    name: Optional[str] = None


class JWTClaimMatcherType(F5XCBaseModel):
    """A JWT claim matcher specifies the name of a single JWT claim and the..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    name: Optional[str] = None


class QueryParameterMatcherType(F5XCBaseModel):
    """A query parameter matcher specifies the name of a single query parameter..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    key: Optional[str] = None


class RequestMatcher(F5XCBaseModel):
    """Request conditions for matching a rule"""

    cookie_matchers: Optional[list[CookieMatcherType]] = None
    headers: Optional[list[HeaderMatcherType]] = None
    jwt_claims: Optional[list[JWTClaimMatcherType]] = None
    query_params: Optional[list[QueryParameterMatcherType]] = None


class APIEndpointProtectionRule(F5XCBaseModel):
    """API Protection Rule for a specific endpoint"""

    action: Optional[APIProtectionRuleAction] = None
    any_domain: Optional[Any] = None
    api_endpoint_method: Optional[HttpMethodMatcherType] = None
    api_endpoint_path: Optional[str] = None
    client_matcher: Optional[ClientMatcher] = None
    metadata: Optional[MessageMetaType] = None
    request_matcher: Optional[RequestMatcher] = None
    specific_domain: Optional[str] = None


class GetSuggestedAPIEndpointProtectionRuleRsp(F5XCBaseModel):
    """Get suggested API endpoint protection rule for a given path"""

    found_existing_rule: Optional[Any] = None
    rule: Optional[APIEndpointProtectionRule] = None


class HeaderMatcherType(F5XCBaseModel):
    """Header match is done using the name of the header and its value. The..."""

    exact: Optional[str] = None
    invert_match: Optional[bool] = None
    name: Optional[str] = None
    presence: Optional[bool] = None
    regex: Optional[str] = None


class HttpHeaderMatcherList(F5XCBaseModel):
    """Request header name and value pairs"""

    headers: Optional[list[HeaderMatcherType]] = None


class SimpleClientSrcRule(F5XCBaseModel):
    """Simple client source rule specifies the sources to be blocked or trusted..."""

    actions: Optional[list[Literal['SKIP_PROCESSING_WAF', 'SKIP_PROCESSING_BOT', 'SKIP_PROCESSING_MUM', 'SKIP_PROCESSING_IP_REPUTATION', 'SKIP_PROCESSING_API_PROTECTION', 'SKIP_PROCESSING_OAS_VALIDATION', 'SKIP_PROCESSING_DDOS_PROTECTION', 'SKIP_PROCESSING_THREAT_MESH', 'SKIP_PROCESSING_MALWARE_PROTECTION']]] = None
    as_number: Optional[int] = None
    bot_skip_processing: Optional[Any] = None
    expiration_timestamp: Optional[str] = None
    http_header: Optional[HttpHeaderMatcherList] = None
    ip_prefix: Optional[str] = None
    ipv6_prefix: Optional[str] = None
    metadata: Optional[MessageMetaType] = None
    skip_processing: Optional[Any] = None
    user_identifier: Optional[str] = None
    waf_skip_processing: Optional[Any] = None


class GetSuggestedBlockClientRuleRsp(F5XCBaseModel):
    """Get suggested blocking SimpleClientSrcRule for a given IP/ASN"""

    found_existing_rule: Optional[Any] = None
    name: Optional[str] = None
    rule: Optional[SimpleClientSrcRule] = None


class JA4TlsFingerprintMatcherType(F5XCBaseModel):
    """An extended version of JA3 that includes additional fields for more..."""

    exact_values: Optional[list[str]] = None


class DDoSClientSource(F5XCBaseModel):
    """DDoS Mitigation sources to be blocked"""

    asn_list: Optional[AsnMatchList] = None
    country_list: Optional[list[Literal['COUNTRY_NONE', 'COUNTRY_AD', 'COUNTRY_AE', 'COUNTRY_AF', 'COUNTRY_AG', 'COUNTRY_AI', 'COUNTRY_AL', 'COUNTRY_AM', 'COUNTRY_AN', 'COUNTRY_AO', 'COUNTRY_AQ', 'COUNTRY_AR', 'COUNTRY_AS', 'COUNTRY_AT', 'COUNTRY_AU', 'COUNTRY_AW', 'COUNTRY_AX', 'COUNTRY_AZ', 'COUNTRY_BA', 'COUNTRY_BB', 'COUNTRY_BD', 'COUNTRY_BE', 'COUNTRY_BF', 'COUNTRY_BG', 'COUNTRY_BH', 'COUNTRY_BI', 'COUNTRY_BJ', 'COUNTRY_BL', 'COUNTRY_BM', 'COUNTRY_BN', 'COUNTRY_BO', 'COUNTRY_BQ', 'COUNTRY_BR', 'COUNTRY_BS', 'COUNTRY_BT', 'COUNTRY_BV', 'COUNTRY_BW', 'COUNTRY_BY', 'COUNTRY_BZ', 'COUNTRY_CA', 'COUNTRY_CC', 'COUNTRY_CD', 'COUNTRY_CF', 'COUNTRY_CG', 'COUNTRY_CH', 'COUNTRY_CI', 'COUNTRY_CK', 'COUNTRY_CL', 'COUNTRY_CM', 'COUNTRY_CN', 'COUNTRY_CO', 'COUNTRY_CR', 'COUNTRY_CS', 'COUNTRY_CU', 'COUNTRY_CV', 'COUNTRY_CW', 'COUNTRY_CX', 'COUNTRY_CY', 'COUNTRY_CZ', 'COUNTRY_DE', 'COUNTRY_DJ', 'COUNTRY_DK', 'COUNTRY_DM', 'COUNTRY_DO', 'COUNTRY_DZ', 'COUNTRY_EC', 'COUNTRY_EE', 'COUNTRY_EG', 'COUNTRY_EH', 'COUNTRY_ER', 'COUNTRY_ES', 'COUNTRY_ET', 'COUNTRY_FI', 'COUNTRY_FJ', 'COUNTRY_FK', 'COUNTRY_FM', 'COUNTRY_FO', 'COUNTRY_FR', 'COUNTRY_GA', 'COUNTRY_GB', 'COUNTRY_GD', 'COUNTRY_GE', 'COUNTRY_GF', 'COUNTRY_GG', 'COUNTRY_GH', 'COUNTRY_GI', 'COUNTRY_GL', 'COUNTRY_GM', 'COUNTRY_GN', 'COUNTRY_GP', 'COUNTRY_GQ', 'COUNTRY_GR', 'COUNTRY_GS', 'COUNTRY_GT', 'COUNTRY_GU', 'COUNTRY_GW', 'COUNTRY_GY', 'COUNTRY_HK', 'COUNTRY_HM', 'COUNTRY_HN', 'COUNTRY_HR', 'COUNTRY_HT', 'COUNTRY_HU', 'COUNTRY_ID', 'COUNTRY_IE', 'COUNTRY_IL', 'COUNTRY_IM', 'COUNTRY_IN', 'COUNTRY_IO', 'COUNTRY_IQ', 'COUNTRY_IR', 'COUNTRY_IS', 'COUNTRY_IT', 'COUNTRY_JE', 'COUNTRY_JM', 'COUNTRY_JO', 'COUNTRY_JP', 'COUNTRY_KE', 'COUNTRY_KG', 'COUNTRY_KH', 'COUNTRY_KI', 'COUNTRY_KM', 'COUNTRY_KN', 'COUNTRY_KP', 'COUNTRY_KR', 'COUNTRY_KW', 'COUNTRY_KY', 'COUNTRY_KZ', 'COUNTRY_LA', 'COUNTRY_LB', 'COUNTRY_LC', 'COUNTRY_LI', 'COUNTRY_LK', 'COUNTRY_LR', 'COUNTRY_LS', 'COUNTRY_LT', 'COUNTRY_LU', 'COUNTRY_LV', 'COUNTRY_LY', 'COUNTRY_MA', 'COUNTRY_MC', 'COUNTRY_MD', 'COUNTRY_ME', 'COUNTRY_MF', 'COUNTRY_MG', 'COUNTRY_MH', 'COUNTRY_MK', 'COUNTRY_ML', 'COUNTRY_MM', 'COUNTRY_MN', 'COUNTRY_MO', 'COUNTRY_MP', 'COUNTRY_MQ', 'COUNTRY_MR', 'COUNTRY_MS', 'COUNTRY_MT', 'COUNTRY_MU', 'COUNTRY_MV', 'COUNTRY_MW', 'COUNTRY_MX', 'COUNTRY_MY', 'COUNTRY_MZ', 'COUNTRY_NA', 'COUNTRY_NC', 'COUNTRY_NE', 'COUNTRY_NF', 'COUNTRY_NG', 'COUNTRY_NI', 'COUNTRY_NL', 'COUNTRY_NO', 'COUNTRY_NP', 'COUNTRY_NR', 'COUNTRY_NU', 'COUNTRY_NZ', 'COUNTRY_OM', 'COUNTRY_PA', 'COUNTRY_PE', 'COUNTRY_PF', 'COUNTRY_PG', 'COUNTRY_PH', 'COUNTRY_PK', 'COUNTRY_PL', 'COUNTRY_PM', 'COUNTRY_PN', 'COUNTRY_PR', 'COUNTRY_PS', 'COUNTRY_PT', 'COUNTRY_PW', 'COUNTRY_PY', 'COUNTRY_QA', 'COUNTRY_RE', 'COUNTRY_RO', 'COUNTRY_RS', 'COUNTRY_RU', 'COUNTRY_RW', 'COUNTRY_SA', 'COUNTRY_SB', 'COUNTRY_SC', 'COUNTRY_SD', 'COUNTRY_SE', 'COUNTRY_SG', 'COUNTRY_SH', 'COUNTRY_SI', 'COUNTRY_SJ', 'COUNTRY_SK', 'COUNTRY_SL', 'COUNTRY_SM', 'COUNTRY_SN', 'COUNTRY_SO', 'COUNTRY_SR', 'COUNTRY_SS', 'COUNTRY_ST', 'COUNTRY_SV', 'COUNTRY_SX', 'COUNTRY_SY', 'COUNTRY_SZ', 'COUNTRY_TC', 'COUNTRY_TD', 'COUNTRY_TF', 'COUNTRY_TG', 'COUNTRY_TH', 'COUNTRY_TJ', 'COUNTRY_TK', 'COUNTRY_TL', 'COUNTRY_TM', 'COUNTRY_TN', 'COUNTRY_TO', 'COUNTRY_TR', 'COUNTRY_TT', 'COUNTRY_TV', 'COUNTRY_TW', 'COUNTRY_TZ', 'COUNTRY_UA', 'COUNTRY_UG', 'COUNTRY_UM', 'COUNTRY_US', 'COUNTRY_UY', 'COUNTRY_UZ', 'COUNTRY_VA', 'COUNTRY_VC', 'COUNTRY_VE', 'COUNTRY_VG', 'COUNTRY_VI', 'COUNTRY_VN', 'COUNTRY_VU', 'COUNTRY_WF', 'COUNTRY_WS', 'COUNTRY_XK', 'COUNTRY_XT', 'COUNTRY_YE', 'COUNTRY_YT', 'COUNTRY_ZA', 'COUNTRY_ZM', 'COUNTRY_ZW']]] = None
    ja4_tls_fingerprint_matcher: Optional[JA4TlsFingerprintMatcherType] = None
    tls_fingerprint_matcher: Optional[TlsFingerprintMatcherType] = None


class DDoSMitigationRule(F5XCBaseModel):
    """DDoS Mitigation Rule specifies the sources to be blocked"""

    block: Optional[Any] = None
    ddos_client_source: Optional[DDoSClientSource] = None
    expiration_timestamp: Optional[str] = None
    ip_prefix_list: Optional[PrefixMatchList] = None
    metadata: Optional[MessageMetaType] = None


class GetSuggestedDDoSMitigtionRuleRsp(F5XCBaseModel):
    """Get suggested DDoS Mitigtion Rule for a given IP/ASN/Country/TLS"""

    found_existing_mitigation_rule: Optional[Any] = None
    mitigation_rule: Optional[DDoSMitigationRule] = None
    mitigation_rule_name: Optional[str] = None


class GetSuggestedOasValidationRuleReq(F5XCBaseModel):
    """Get suggested Open API specification validation for a given path"""

    api_groups: Optional[list[str]] = None
    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    path: Optional[str] = None


class ApiEndpointDetails(F5XCBaseModel):
    """This defines api endpoint"""

    methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None
    path: Optional[str] = None


class FallThroughRule(F5XCBaseModel):
    """Fall Through Rule for a specific endpoint, base-path, or API group"""

    action_block: Optional[Any] = None
    action_report: Optional[Any] = None
    action_skip: Optional[Any] = None
    api_endpoint: Optional[ApiEndpointDetails] = None
    api_group: Optional[str] = None
    base_path: Optional[str] = None
    metadata: Optional[MessageMetaType] = None


class CustomFallThroughMode(F5XCBaseModel):
    """Define the fall through settings"""

    open_api_validation_rules: Optional[list[FallThroughRule]] = None


class OpenApiFallThroughMode(F5XCBaseModel):
    """x-required Determine what to do with unprotected endpoints (not in the..."""

    fall_through_mode_allow: Optional[Any] = None
    fall_through_mode_custom: Optional[CustomFallThroughMode] = None


class ValidationSettingForQueryParameters(F5XCBaseModel):
    """Custom settings for query parameters validation"""

    allow_additional_parameters: Optional[Any] = None
    disallow_additional_parameters: Optional[Any] = None


class ValidationPropertySetting(F5XCBaseModel):
    """Custom property validation settings"""

    query_parameters: Optional[ValidationSettingForQueryParameters] = Field(default=None, alias="queryParameters")


class OpenApiValidationCommonSettings(F5XCBaseModel):
    """OpenAPI specification validation settings relevant for 'API Inventory'..."""

    oversized_body_fail_validation: Optional[Any] = None
    oversized_body_skip_validation: Optional[Any] = None
    property_validation_settings_custom: Optional[ValidationPropertySetting] = None
    property_validation_settings_default: Optional[Any] = None


class OpenApiValidationModeActiveResponse(F5XCBaseModel):
    """Validation mode properties of response"""

    enforcement_block: Optional[Any] = None
    enforcement_report: Optional[Any] = None
    response_validation_properties: Optional[list[Literal['PROPERTY_QUERY_PARAMETERS', 'PROPERTY_PATH_PARAMETERS', 'PROPERTY_CONTENT_TYPE', 'PROPERTY_COOKIE_PARAMETERS', 'PROPERTY_HTTP_HEADERS', 'PROPERTY_HTTP_BODY', 'PROPERTY_SECURITY_SCHEMA', 'PROPERTY_RESPONSE_CODE']]] = None


class OpenApiValidationModeActive(F5XCBaseModel):
    """Validation mode properties of request"""

    enforcement_block: Optional[Any] = None
    enforcement_report: Optional[Any] = None
    request_validation_properties: Optional[list[Literal['PROPERTY_QUERY_PARAMETERS', 'PROPERTY_PATH_PARAMETERS', 'PROPERTY_CONTENT_TYPE', 'PROPERTY_COOKIE_PARAMETERS', 'PROPERTY_HTTP_HEADERS', 'PROPERTY_HTTP_BODY', 'PROPERTY_SECURITY_SCHEMA', 'PROPERTY_RESPONSE_CODE']]] = None


class OpenApiValidationMode(F5XCBaseModel):
    """x-required Validation mode of OpenAPI specification.  When a validation..."""

    response_validation_mode_active: Optional[OpenApiValidationModeActiveResponse] = None
    skip_response_validation: Optional[Any] = None
    skip_validation: Optional[Any] = None
    validation_mode_active: Optional[OpenApiValidationModeActive] = None


class OpenApiValidationAllSpecEndpointsSettings(F5XCBaseModel):
    """Settings for API Inventory validation"""

    fall_through_mode: Optional[OpenApiFallThroughMode] = None
    settings: Optional[OpenApiValidationCommonSettings] = None
    validation_mode: Optional[OpenApiValidationMode] = None


class OpenApiValidationRule(F5XCBaseModel):
    """OpenAPI Validation Rule for a specific endpoint, base-path, or API group"""

    any_domain: Optional[Any] = None
    api_endpoint: Optional[ApiEndpointDetails] = None
    api_group: Optional[str] = None
    base_path: Optional[str] = None
    metadata: Optional[MessageMetaType] = None
    specific_domain: Optional[str] = None
    validation_mode: Optional[OpenApiValidationMode] = None


class GetSuggestedOasValidationRuleRsp(F5XCBaseModel):
    """Get suggested Open API specification validation for a given path"""

    all_endpoints_oas_validation: Optional[OpenApiValidationAllSpecEndpointsSettings] = None
    custom_oas_validation: Optional[OpenApiValidationRule] = None
    found_existing_rule: Optional[Any] = None


class GetSuggestedRateLimitRuleReq(F5XCBaseModel):
    """Get suggested rate limit rule for a given path"""

    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    path: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class InlineRateLimiter(F5XCBaseModel):
    ref_user_id: Optional[ObjectRefType] = None
    threshold: Optional[int] = None
    unit: Optional[Literal['SECOND', 'MINUTE', 'HOUR']] = None
    use_http_lb_user_id: Optional[Any] = None


class ApiEndpointRule(F5XCBaseModel):
    any_domain: Optional[Any] = None
    api_endpoint_method: Optional[HttpMethodMatcherType] = None
    api_endpoint_path: Optional[str] = None
    client_matcher: Optional[ClientMatcher] = None
    inline_rate_limiter: Optional[InlineRateLimiter] = None
    ref_rate_limiter: Optional[ObjectRefType] = None
    request_matcher: Optional[RequestMatcher] = None
    specific_domain: Optional[str] = None


class GetSuggestedRateLimitRuleRsp(F5XCBaseModel):
    """Get suggested rate limit rule for a given path"""

    found_existing_rule: Optional[Any] = None
    rule: Optional[ApiEndpointRule] = None


class GetSuggestedSensitiveDataRuleReq(F5XCBaseModel):
    """Get suggested sensitive data rule for a given path"""

    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    path: Optional[str] = None


class BodySectionMaskingOptions(F5XCBaseModel):
    """Options for HTTP Body Masking"""

    fields: Optional[list[str]] = None


class SensitiveDataTypes(F5XCBaseModel):
    """Settings to mask sensitive data in request/response payload"""

    api_endpoint: Optional[ApiEndpointDetails] = None
    body: Optional[BodySectionMaskingOptions] = None
    mask: Optional[Any] = None
    report: Optional[Any] = None


class GetSuggestedSensitiveDataRuleRsp(F5XCBaseModel):
    """Get suggested sensitive data rule for a given path"""

    found_existing_rule: Optional[Any] = None
    rule: Optional[SensitiveDataTypes] = None


class GetSuggestedTrustClientRuleRsp(F5XCBaseModel):
    """Get suggested SimpleClientSrcRule to trust a given IP/ASN"""

    found_existing_rule: Optional[Any] = None
    name: Optional[str] = None
    rule: Optional[SimpleClientSrcRule] = None


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


class SimpleWafExclusionRule(F5XCBaseModel):
    """Simple WAF exclusion rule specifies a simple set of match conditions to..."""

    any_domain: Optional[Any] = None
    any_path: Optional[Any] = None
    app_firewall_detection_control: Optional[AppFirewallDetectionControl] = None
    exact_value: Optional[str] = None
    expiration_timestamp: Optional[str] = None
    metadata: Optional[MessageMetaType] = None
    methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None
    path_prefix: Optional[str] = None
    path_regex: Optional[str] = None
    suffix_value: Optional[str] = None
    waf_skip_processing: Optional[Any] = None


class GetSuggestedWAFExclusionRuleRsp(F5XCBaseModel):
    """Get suggested service policy rule to set up WAF rule exclusion for a..."""

    found_existing_rule: Optional[Any] = None
    name: Optional[str] = None
    waf_exclusion_policy: Optional[ObjectRefType] = None
    waf_exclusion_rule: Optional[SimpleWafExclusionRule] = None


class RequestData(F5XCBaseModel):
    """Request Data"""

    count: Optional[str] = None
    max_time: Optional[str] = None
    min_time: Optional[str] = None


class SecurityEventsData(F5XCBaseModel):
    """Security events data"""

    count: Optional[str] = None
    max_time: Optional[str] = None
    min_time: Optional[str] = None


class LoadbalancerData(F5XCBaseModel):
    """List of virtual hosts in all the namespaces matching filter provided in..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    request_data: Optional[RequestData] = None
    security_events_data: Optional[SecurityEventsData] = None


class SearchLoadBalancersResponse(F5XCBaseModel):
    """List of virtual hosts in all the namespaces matching filter provided in..."""

    loadbalancers: Optional[list[LoadbalancerData]] = None


class SecurityEventsAggregationResponse(F5XCBaseModel):
    """Response message for SecurityEventsAggregationRequest"""

    aggs: Optional[dict[str, Any]] = None
    total_hits: Optional[str] = None


class SecurityMetricLabelFilter(F5XCBaseModel):
    """Label based filtering for Security Events metrics.  Security Events..."""

    label: Optional[Literal['NAMESPACE', 'VH_NAME', 'SEC_EVENT_TYPE', 'SRC_SITE', 'SRC_INSTANCE']] = None
    op: Optional[Literal['EQ', 'NEQ']] = None
    value: Optional[str] = None


class SecurityEventsCountRequest(F5XCBaseModel):
    """Request to get number of security events for a given namespace."""

    end_time: Optional[str] = None
    group_by: Optional[list[Literal['NAMESPACE', 'VH_NAME', 'SEC_EVENT_TYPE', 'SRC_SITE', 'SRC_INSTANCE']]] = None
    label_filter: Optional[list[SecurityMetricLabelFilter]] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class SecurityEventsId(F5XCBaseModel):
    """SecurityEventsId uniquely identifies an entry in the response for..."""

    namespace: Optional[str] = None
    sec_event_type: Optional[str] = None
    src_instance: Optional[str] = None
    src_site: Optional[str] = None
    vh_name: Optional[str] = None


class SecurityMetricValue(F5XCBaseModel):
    """Value returned for a Security Events Metrics query"""

    timestamp: Optional[float] = None
    value: Optional[str] = None


class SecurityEventsCounter(F5XCBaseModel):
    """SecurityEventsCounter contains the timeseries data of security events counter."""

    id_: Optional[SecurityEventsId] = Field(default=None, alias="id")
    metric: Optional[list[SecurityMetricValue]] = None


class SecurityEventsCountResponse(F5XCBaseModel):
    """Number of security events for each unique combination of group_by labels..."""

    data: Optional[list[SecurityEventsCounter]] = None
    step: Optional[str] = None


class SecurityEventsResponse(F5XCBaseModel):
    """Response message for SecurityEventsRequest/SecurityEventsScrollRequest"""

    aggs: Optional[dict[str, Any]] = None
    events: Optional[list[str]] = None
    scroll_id: Optional[str] = None
    total_hits: Optional[str] = None


class SecurityEventsScrollRequest(F5XCBaseModel):
    """Scroll request is used to fetch large number of security events in..."""

    namespace: Optional[str] = None
    scroll_id: Optional[str] = None


class SecurityIncidentsAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for security incidents"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None


class SecurityIncidentsAggregationResponse(F5XCBaseModel):
    """Response message for SecurityIncidentsAggregationRequest"""

    aggs: Optional[dict[str, Any]] = None
    total_hits: Optional[str] = None


class SecurityIncidentsRequest(F5XCBaseModel):
    """Request to fetch security incidents"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    sort_by: Optional[str] = None
    start_time: Optional[str] = None


class SecurityIncidentsResponse(F5XCBaseModel):
    """Response message for SecurityIncidentsRequest/SecurityIncidentsScrollRequest"""

    aggs: Optional[dict[str, Any]] = None
    incidents: Optional[list[str]] = None
    scroll_id: Optional[str] = None
    total_hits: Optional[str] = None


class SecurityIncidentsScrollRequest(F5XCBaseModel):
    """Scroll request is used to fetch large number of security incidents in..."""

    namespace: Optional[str] = None
    scroll_id: Optional[str] = None


class SuspiciousUserLogsAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for suspicious user logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None


class SuspiciousUserLogsAggregationResponse(F5XCBaseModel):
    """Response message for SuspiciousUserLogsAggregationRequest"""

    aggs: Optional[dict[str, Any]] = None
    total_hits: Optional[str] = None


class SuspiciousUserLogsRequest(F5XCBaseModel):
    """Request to fetch suspicious user logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    sort_by: Optional[str] = None
    start_time: Optional[str] = None


class SuspiciousUserLogsResponse(F5XCBaseModel):
    """Response message for Suspicious User Logs Request"""

    aggs: Optional[dict[str, Any]] = None
    logs: Optional[list[str]] = None
    scroll_id: Optional[str] = None
    total_hits: Optional[str] = None


class SuspiciousUserLogsScrollRequest(F5XCBaseModel):
    """Scroll request is used to fetch large number of suspicious user logs in..."""

    namespace: Optional[str] = None
    scroll_id: Optional[str] = None


class ThreatCampaign(F5XCBaseModel):
    """Threat Campaign object representing the created threat campaign."""

    attack_type: Optional[str] = None
    description: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    intent: Optional[str] = None
    last_update: Optional[str] = None
    malwares: Optional[list[str]] = None
    name: Optional[str] = None
    references: Optional[list[str]] = None
    risk: Optional[str] = None
    systems: Optional[list[str]] = None


# Convenience aliases
Spec = OpenApiValidationAllSpecEndpointsSettings
