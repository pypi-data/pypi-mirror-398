"""Pydantic models for rule_suggestion."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


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


class ApiEndpointDetails(F5XCBaseModel):
    """This defines api endpoint"""

    methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None
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


class BodySectionMaskingOptions(F5XCBaseModel):
    """Options for HTTP Body Masking"""

    fields: Optional[list[str]] = None


class SensitiveDataTypes(F5XCBaseModel):
    """Settings to mask sensitive data in request/response payload"""

    api_endpoint: Optional[ApiEndpointDetails] = None
    body: Optional[BodySectionMaskingOptions] = None
    mask: Optional[Any] = None
    report: Optional[Any] = None


class GetSuggestedAPIEndpointProtectionRuleReq(F5XCBaseModel):
    """Get suggested API endpoint protection rule for a given path"""

    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    namespace: Optional[str] = None
    path: Optional[str] = None
    virtual_host_name: Optional[str] = None


class GetSuggestedAPIEndpointProtectionRuleRsp(F5XCBaseModel):
    """Get suggested API endpoint protection rule for a given path"""

    found_existing_rule: Optional[Any] = None
    loadbalancer_type: Optional[Literal['VIRTUAL_SERVICE', 'HTTP_LOAD_BALANCER', 'API_GATEWAY', 'TCP_LOAD_BALANCER', 'PROXY', 'CDN_LOAD_BALANCER', 'NGINX_SERVER', 'UDP_LOAD_BALANCER']] = None
    rule: Optional[APIEndpointProtectionRule] = None


class GetSuggestedOasValidationRuleReq(F5XCBaseModel):
    """Get suggested Open API specification validation for a given path"""

    api_groups: Optional[list[str]] = None
    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    namespace: Optional[str] = None
    path: Optional[str] = None
    virtual_host_name: Optional[str] = None


class GetSuggestedOasValidationRuleRsp(F5XCBaseModel):
    """Get suggested Open API specification validation for a given path"""

    all_endpoints_oas_validation: Optional[OpenApiValidationAllSpecEndpointsSettings] = None
    custom_oas_validation: Optional[OpenApiValidationRule] = None
    found_existing_rule: Optional[Any] = None
    loadbalancer_type: Optional[Literal['VIRTUAL_SERVICE', 'HTTP_LOAD_BALANCER', 'API_GATEWAY', 'TCP_LOAD_BALANCER', 'PROXY', 'CDN_LOAD_BALANCER', 'NGINX_SERVER', 'UDP_LOAD_BALANCER']] = None


class GetSuggestedRateLimitRuleReq(F5XCBaseModel):
    """Get suggested rate limit rule for a given path"""

    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    namespace: Optional[str] = None
    path: Optional[str] = None
    virtual_host_name: Optional[str] = None


class GetSuggestedRateLimitRuleRsp(F5XCBaseModel):
    """Get suggested rate limit rule for a given path"""

    found_existing_rule: Optional[Any] = None
    loadbalancer_type: Optional[Literal['VIRTUAL_SERVICE', 'HTTP_LOAD_BALANCER', 'API_GATEWAY', 'TCP_LOAD_BALANCER', 'PROXY', 'CDN_LOAD_BALANCER', 'NGINX_SERVER', 'UDP_LOAD_BALANCER']] = None
    rule: Optional[ApiEndpointRule] = None


class GetSuggestedSensitiveDataRuleReq(F5XCBaseModel):
    """Get suggested sensitive data rule for a given path"""

    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    namespace: Optional[str] = None
    path: Optional[str] = None
    virtual_host_name: Optional[str] = None


class GetSuggestedSensitiveDataRuleRsp(F5XCBaseModel):
    """Get suggested sensitive data rule for a given path"""

    found_existing_rule: Optional[Any] = None
    loadbalancer_type: Optional[Literal['VIRTUAL_SERVICE', 'HTTP_LOAD_BALANCER', 'API_GATEWAY', 'TCP_LOAD_BALANCER', 'PROXY', 'CDN_LOAD_BALANCER', 'NGINX_SERVER', 'UDP_LOAD_BALANCER']] = None
    rule: Optional[SensitiveDataTypes] = None


# Convenience aliases
Spec = OpenApiValidationAllSpecEndpointsSettings
