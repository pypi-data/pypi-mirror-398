"""Pydantic models for http_loadbalancer."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class HttpLoadbalancerListItem(F5XCBaseModel):
    """List item for http_loadbalancer resources."""


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class HttpBody(F5XCBaseModel):
    """Message that represents an arbitrary HTTP body. It should only be used..."""

    content_type: Optional[str] = None
    data: Optional[str] = None
    extensions: Optional[list[ProtobufAny]] = None


class DiscoveredAPISettings(F5XCBaseModel):
    """x-example: '2' Configure Discovered API Settings."""

    purge_duration_for_inactive_discovered_apis: Optional[int] = None


class RiskScore(F5XCBaseModel):
    """Risk score of the vulnerabilities found for this API Endpoint."""

    score: Optional[float] = None
    severity: Optional[Literal['APIEP_SEC_RISK_NONE', 'APIEP_SEC_RISK_LOW', 'APIEP_SEC_RISK_MED', 'APIEP_SEC_RISK_HIGH', 'APIEP_SEC_RISK_CRITICAL']] = None


class CircuitBreaker(F5XCBaseModel):
    """CircuitBreaker provides a mechanism for watching failures in upstream..."""

    connection_limit: Optional[int] = None
    max_requests: Optional[int] = None
    pending_requests: Optional[int] = None
    priority: Optional[Literal['DEFAULT', 'HIGH']] = None
    retries: Optional[int] = None


class EndpointSubsetSelectorType(F5XCBaseModel):
    """Upstream cluster may be configured to divide its endpoints into subsets..."""

    keys: Optional[list[str]] = None


class Http2ProtocolOptions(F5XCBaseModel):
    """Http2 Protocol options for upstream connections"""

    enabled: Optional[bool] = None


class OutlierDetectionType(F5XCBaseModel):
    """Outlier detection and ejection is the process of dynamically determining..."""

    base_ejection_time: Optional[int] = None
    consecutive_5xx: Optional[int] = None
    consecutive_gateway_failure: Optional[int] = None
    interval: Optional[int] = None
    max_ejection_percent: Optional[int] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class CustomCacheRule(F5XCBaseModel):
    """Caching policies for CDN"""

    cdn_cache_rules: Optional[list[ObjectRefType]] = None


class CDNControllerStatus(F5XCBaseModel):
    """CDN Controller Status"""

    cfg_version: Optional[int] = None
    cp_version: Optional[int] = None
    deployment_status: Optional[Literal['CDN_LB_STATUS_CREATED', 'CDN_LB_STATUS_DEPLOYING', 'CDN_LB_STATUS_DEPLOY_FAILED', 'CDN_LB_STATUS_DEPLOYED', 'CDN_LB_STATUS_FAILED']] = None
    error: Optional[str] = None


class CDNSiteStatus(F5XCBaseModel):
    """This CDN status is per site and it indicates the status of the CDN..."""

    error: Optional[str] = None
    site: Optional[str] = None
    status: Optional[Literal['DEPLOYMENT_STATUS_NOT_DEPLOYED', 'DEPLOYMENT_STATUS_DEPLOYING', 'DEPLOYMENT_STATUS_DEPLOY_FAILED', 'DEPLOYMENT_STATUS_DEPLOYED']] = None


class GetServiceOperationReq(F5XCBaseModel):
    """Get Service Operation Request"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    service_op_id: Optional[int] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class PurgeOperationItem(F5XCBaseModel):
    """Purge Operation Status"""

    bytes_not_purged: Optional[str] = None
    bytes_purged: Optional[str] = None
    finish_time: Optional[str] = None
    hard_purge: Optional[bool] = None
    purge_time: Optional[str] = None
    regexp: Optional[str] = None
    site: Optional[str] = None
    start_time: Optional[str] = None


class ServiceOperationItem(F5XCBaseModel):
    """Service Operation Item"""

    purge: Optional[PurgeOperationItem] = None
    service_op_id: Optional[int] = None
    status: Optional[str] = None


class GetServiceOperationRsp(F5XCBaseModel):
    """Get Service Operation Response"""

    error: Optional[ErrorType] = None
    items: Optional[list[ServiceOperationItem]] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class LilacCDNCachePurgeRequest(F5XCBaseModel):
    """CDN Cache Purge"""

    hard_purge: Optional[Any] = None
    hostname: Optional[str] = None
    pattern: Optional[str] = None
    purge_all: Optional[Any] = None
    soft_purge: Optional[Any] = None
    url: Optional[str] = None


class LilacCDNCachePurgeResponse(F5XCBaseModel):
    """Cache Purge message"""

    purge_request_id: Optional[int] = None


class ServiceOperationsTimeRange(F5XCBaseModel):
    """Option to specify lastn or start-end time."""

    finish_time: Optional[str] = None
    start_time: Optional[str] = None


class ListServiceOperationsReq(F5XCBaseModel):
    """List Service Operations Request"""

    lastn: Optional[int] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    time_range: Optional[ServiceOperationsTimeRange] = None


class ServiceOperationsItem(F5XCBaseModel):
    """List of Service Operations"""

    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    service_op_id: Optional[int] = None
    svc_version: Optional[int] = None


class ListServiceOperationsRsp(F5XCBaseModel):
    """Get Service Operations Response"""

    error: Optional[ErrorType] = None
    items: Optional[list[ServiceOperationsItem]] = None


class DomainType(F5XCBaseModel):
    """Domains names"""

    exact_value: Optional[str] = None
    regex_value: Optional[str] = None
    suffix_value: Optional[str] = None


class BotDefenseFlowLabelAccountManagementChoiceType(F5XCBaseModel):
    """Bot Defense Flow Label Account Management Category"""

    create: Optional[Any] = None
    password_reset: Optional[Any] = None


class BotDefenseTransactionResultCondition(F5XCBaseModel):
    """Bot Defense Transaction Result Condition"""

    name: Optional[str] = None
    regex_values: Optional[list[str]] = None
    status: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None


class BotDefenseTransactionResultType(F5XCBaseModel):
    """Bot Defense Transaction ResultType"""

    failure_conditions: Optional[list[BotDefenseTransactionResultCondition]] = None
    success_conditions: Optional[list[BotDefenseTransactionResultCondition]] = None


class BotDefenseTransactionResult(F5XCBaseModel):
    """Bot Defense Transaction Result"""

    disable_transaction_result: Optional[Any] = None
    transaction_result: Optional[BotDefenseTransactionResultType] = None


class BotDefenseFlowLabelAuthenticationChoiceType(F5XCBaseModel):
    """Bot Defense Flow Label Authentication Category"""

    login: Optional[BotDefenseTransactionResult] = None
    login_mfa: Optional[Any] = None
    login_partner: Optional[Any] = None
    logout: Optional[Any] = None
    token_refresh: Optional[Any] = None


class BotDefenseFlowLabelFinancialServicesChoiceType(F5XCBaseModel):
    """Bot Defense Flow Label Financial Services Category"""

    apply: Optional[Any] = None
    money_transfer: Optional[Any] = None


class BotDefenseFlowLabelFlightChoiceType(F5XCBaseModel):
    """Bot Defense Flow Label Flight Category"""

    checkin: Optional[Any] = None


class BotDefenseFlowLabelProfileManagementChoiceType(F5XCBaseModel):
    """Bot Defense Flow Label Profile Management Category"""

    create: Optional[Any] = None
    update: Optional[Any] = None
    view: Optional[Any] = None


class BotDefenseFlowLabelSearchChoiceType(F5XCBaseModel):
    """Bot Defense Flow Label Search Category"""

    flight_search: Optional[Any] = None
    product_search: Optional[Any] = None
    reservation_search: Optional[Any] = None
    room_search: Optional[Any] = None


class BotDefenseFlowLabelShoppingGiftCardsChoiceType(F5XCBaseModel):
    """Bot Defense Flow Label Shopping & Gift Cards Category"""

    gift_card_make_purchase_with_gift_card: Optional[Any] = None
    gift_card_validation: Optional[Any] = None
    shop_add_to_cart: Optional[Any] = None
    shop_checkout: Optional[Any] = None
    shop_choose_seat: Optional[Any] = None
    shop_enter_drawing_submission: Optional[Any] = None
    shop_make_payment: Optional[Any] = None
    shop_order: Optional[Any] = None
    shop_price_inquiry: Optional[Any] = None
    shop_promo_code_validation: Optional[Any] = None
    shop_purchase_gift_card: Optional[Any] = None
    shop_update_quantity: Optional[Any] = None


class BotDefenseFlowLabelCategoriesChoiceType(F5XCBaseModel):
    """Bot Defense Flow Label Category allows to associate traffic with..."""

    account_management: Optional[BotDefenseFlowLabelAccountManagementChoiceType] = None
    authentication: Optional[BotDefenseFlowLabelAuthenticationChoiceType] = None
    financial_services: Optional[BotDefenseFlowLabelFinancialServicesChoiceType] = None
    flight: Optional[BotDefenseFlowLabelFlightChoiceType] = None
    profile_management: Optional[BotDefenseFlowLabelProfileManagementChoiceType] = None
    search: Optional[BotDefenseFlowLabelSearchChoiceType] = None
    shopping_gift_cards: Optional[BotDefenseFlowLabelShoppingGiftCardsChoiceType] = None


class MatcherType(F5XCBaseModel):
    """A matcher specifies multiple criteria for matching an input string. The..."""

    exact_values: Optional[list[str]] = None
    regex_values: Optional[list[str]] = None
    transformers: Optional[list[Literal['LOWER_CASE', 'UPPER_CASE', 'BASE64_DECODE', 'NORMALIZE_PATH', 'REMOVE_WHITESPACE', 'URL_DECODE', 'TRIM_LEFT', 'TRIM_RIGHT', 'TRIM']]] = None


class HeaderMatcherType(F5XCBaseModel):
    """A header matcher specifies the name of a single HTTP header and the..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    name: Optional[str] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class ShapeBotBlockMitigationActionType(F5XCBaseModel):
    """Block request and respond with custom content."""

    body: Optional[str] = None
    status: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None


class ShapeBotFlagMitigationActionType(F5XCBaseModel):
    """Append flag mitigation headers to forwarded request."""

    auto_type_header_name: Optional[str] = None
    inference_header_name: Optional[str] = None


class ShapeBotFlagMitigationActionChoiceType(F5XCBaseModel):
    """Flag mitigation action."""

    append_headers: Optional[ShapeBotFlagMitigationActionType] = None
    no_headers: Optional[Any] = None


class ShapeBotRedirectMitigationActionType(F5XCBaseModel):
    """Redirect request to a custom URI."""

    uri: Optional[str] = None


class ShapeBotMitigationAction(F5XCBaseModel):
    """Modify Bot Defense behavior for a matching request."""

    block: Optional[ShapeBotBlockMitigationActionType] = None
    flag: Optional[ShapeBotFlagMitigationActionChoiceType] = None
    redirect: Optional[ShapeBotRedirectMitigationActionType] = None


class PathMatcherType(F5XCBaseModel):
    """Path match of the URI can be either be, Prefix match or exact match or..."""

    path: Optional[str] = None
    prefix: Optional[str] = None
    regex: Optional[str] = None


class QueryParameterMatcherType(F5XCBaseModel):
    """A query parameter matcher specifies the name of a single query parameter..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    key: Optional[str] = None


class WebMobileTrafficType(F5XCBaseModel):
    """Web and Mobile traffic type"""

    mobile_identifier: Optional[Literal['HEADERS']] = None


class AppEndpointType(F5XCBaseModel):
    """Application Endpoint."""

    allow_good_bots: Optional[Any] = None
    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None
    flow_label: Optional[BotDefenseFlowLabelCategoriesChoiceType] = None
    headers: Optional[list[HeaderMatcherType]] = None
    http_methods: Optional[list[Literal['METHOD_ANY', 'METHOD_GET', 'METHOD_POST', 'METHOD_PUT', 'METHOD_PATCH', 'METHOD_DELETE', 'METHOD_GET_DOCUMENT']]] = None
    metadata: Optional[MessageMetaType] = None
    mitigate_good_bots: Optional[Any] = None
    mitigation: Optional[ShapeBotMitigationAction] = None
    mobile: Optional[Any] = None
    path: Optional[PathMatcherType] = None
    protocol: Optional[Literal['BOTH', 'HTTP', 'HTTPS']] = None
    query_params: Optional[list[QueryParameterMatcherType]] = None
    undefined_flow_label: Optional[Any] = None
    web: Optional[Any] = None
    web_mobile: Optional[WebMobileTrafficType] = None


class HeaderMatcherTypeBasic(F5XCBaseModel):
    """A header matcher specifies the name of a single HTTP header and the..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    item: Optional[MatcherType] = None
    name: Optional[str] = None


class MobileTrafficIdentifierType(F5XCBaseModel):
    """Mobile traffic identifier type."""

    headers: Optional[list[HeaderMatcherTypeBasic]] = None


class BotAdvancedMobileSDKConfigType(F5XCBaseModel):
    """Mobile Request Identifier Headers."""

    mobile_identifier: Optional[MobileTrafficIdentifierType] = None


class ShapeJavaScriptInsertAllType(F5XCBaseModel):
    """Insert Bot Defense JavaScript in all pages"""

    javascript_location: Optional[Literal['AFTER_HEAD', 'AFTER_TITLE_END', 'BEFORE_SCRIPT']] = None


class ShapeJavaScriptExclusionRule(F5XCBaseModel):
    """Define JavaScript insertion exclusion rule"""

    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None
    metadata: Optional[MessageMetaType] = None
    path: Optional[PathMatcherType] = None


class ShapeJavaScriptInsertAllWithExceptionsType(F5XCBaseModel):
    """Insert Bot Defense JavaScript in all pages  with the exceptions"""

    exclude_list: Optional[list[ShapeJavaScriptExclusionRule]] = None
    javascript_location: Optional[Literal['AFTER_HEAD', 'AFTER_TITLE_END', 'BEFORE_SCRIPT']] = None


class ShapeJavaScriptInsertionRule(F5XCBaseModel):
    """This defines a rule for Bot Defense JavaScript insertion."""

    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None
    javascript_location: Optional[Literal['AFTER_HEAD', 'AFTER_TITLE_END', 'BEFORE_SCRIPT']] = None
    metadata: Optional[MessageMetaType] = None
    path: Optional[PathMatcherType] = None


class ShapeJavaScriptInsertType(F5XCBaseModel):
    """This defines custom JavaScript insertion rules for Bot Defense Policy."""

    exclude_list: Optional[list[ShapeJavaScriptExclusionRule]] = None
    rules: Optional[list[ShapeJavaScriptInsertionRule]] = None


class BotDefenseAdvancedType(F5XCBaseModel):
    """Bot Defense Advanced"""

    disable_js_insert: Optional[Any] = None
    disable_mobile_sdk: Optional[Any] = None
    js_insert_all_pages: Optional[ShapeJavaScriptInsertAllType] = None
    js_insert_all_pages_except: Optional[ShapeJavaScriptInsertAllWithExceptionsType] = None
    js_insertion_rules: Optional[ShapeJavaScriptInsertType] = None
    mobile: Optional[ObjectRefType] = None
    mobile_sdk_config: Optional[BotAdvancedMobileSDKConfigType] = None
    web: Optional[ObjectRefType] = None


class CSDJavaScriptInsertAllWithExceptionsType(F5XCBaseModel):
    """Insert Client-Side Defense JavaScript in all pages  with the exceptions"""

    exclude_list: Optional[list[ShapeJavaScriptExclusionRule]] = None


class CSDJavaScriptInsertionRule(F5XCBaseModel):
    """This defines a rule for Client-Side Defense JavaScript insertion."""

    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None
    metadata: Optional[MessageMetaType] = None
    path: Optional[PathMatcherType] = None


class CSDJavaScriptInsertType(F5XCBaseModel):
    """This defines custom JavaScript insertion rules for Client-Side Defense Policy."""

    exclude_list: Optional[list[ShapeJavaScriptExclusionRule]] = None
    rules: Optional[list[CSDJavaScriptInsertionRule]] = None


class ClientSideDefensePolicyType(F5XCBaseModel):
    """This defines various configuration options for Client-Side Defense policy."""

    disable_js_insert: Optional[Any] = None
    js_insert_all_pages: Optional[Any] = None
    js_insert_all_pages_except: Optional[CSDJavaScriptInsertAllWithExceptionsType] = None
    js_insertion_rules: Optional[CSDJavaScriptInsertType] = None


class ClientSideDefenseType(F5XCBaseModel):
    """This defines various configuration options for Client-Side Defense Policy."""

    policy: Optional[ClientSideDefensePolicyType] = None


class AsnMatchList(F5XCBaseModel):
    """An unordered set of RFC 6793 defined 4-byte AS numbers that can be used..."""

    as_numbers: Optional[list[int]] = None


class JA4TlsFingerprintMatcherType(F5XCBaseModel):
    """An extended version of JA3 that includes additional fields for more..."""

    exact_values: Optional[list[str]] = None


class TlsFingerprintMatcherType(F5XCBaseModel):
    """A TLS fingerprint matcher specifies multiple criteria for matching a TLS..."""

    classes: Optional[list[Literal['TLS_FINGERPRINT_NONE', 'ANY_MALICIOUS_FINGERPRINT', 'ADWARE', 'ADWIND', 'DRIDEX', 'GOOTKIT', 'GOZI', 'JBIFROST', 'QUAKBOT', 'RANSOMWARE', 'TROLDESH', 'TOFSEE', 'TORRENTLOCKER', 'TRICKBOT']]] = None
    exact_values: Optional[list[str]] = None
    excluded_values: Optional[list[str]] = None


class DDoSClientSource(F5XCBaseModel):
    """DDoS Mitigation sources to be blocked"""

    asn_list: Optional[AsnMatchList] = None
    country_list: Optional[list[Literal['COUNTRY_NONE', 'COUNTRY_AD', 'COUNTRY_AE', 'COUNTRY_AF', 'COUNTRY_AG', 'COUNTRY_AI', 'COUNTRY_AL', 'COUNTRY_AM', 'COUNTRY_AN', 'COUNTRY_AO', 'COUNTRY_AQ', 'COUNTRY_AR', 'COUNTRY_AS', 'COUNTRY_AT', 'COUNTRY_AU', 'COUNTRY_AW', 'COUNTRY_AX', 'COUNTRY_AZ', 'COUNTRY_BA', 'COUNTRY_BB', 'COUNTRY_BD', 'COUNTRY_BE', 'COUNTRY_BF', 'COUNTRY_BG', 'COUNTRY_BH', 'COUNTRY_BI', 'COUNTRY_BJ', 'COUNTRY_BL', 'COUNTRY_BM', 'COUNTRY_BN', 'COUNTRY_BO', 'COUNTRY_BQ', 'COUNTRY_BR', 'COUNTRY_BS', 'COUNTRY_BT', 'COUNTRY_BV', 'COUNTRY_BW', 'COUNTRY_BY', 'COUNTRY_BZ', 'COUNTRY_CA', 'COUNTRY_CC', 'COUNTRY_CD', 'COUNTRY_CF', 'COUNTRY_CG', 'COUNTRY_CH', 'COUNTRY_CI', 'COUNTRY_CK', 'COUNTRY_CL', 'COUNTRY_CM', 'COUNTRY_CN', 'COUNTRY_CO', 'COUNTRY_CR', 'COUNTRY_CS', 'COUNTRY_CU', 'COUNTRY_CV', 'COUNTRY_CW', 'COUNTRY_CX', 'COUNTRY_CY', 'COUNTRY_CZ', 'COUNTRY_DE', 'COUNTRY_DJ', 'COUNTRY_DK', 'COUNTRY_DM', 'COUNTRY_DO', 'COUNTRY_DZ', 'COUNTRY_EC', 'COUNTRY_EE', 'COUNTRY_EG', 'COUNTRY_EH', 'COUNTRY_ER', 'COUNTRY_ES', 'COUNTRY_ET', 'COUNTRY_FI', 'COUNTRY_FJ', 'COUNTRY_FK', 'COUNTRY_FM', 'COUNTRY_FO', 'COUNTRY_FR', 'COUNTRY_GA', 'COUNTRY_GB', 'COUNTRY_GD', 'COUNTRY_GE', 'COUNTRY_GF', 'COUNTRY_GG', 'COUNTRY_GH', 'COUNTRY_GI', 'COUNTRY_GL', 'COUNTRY_GM', 'COUNTRY_GN', 'COUNTRY_GP', 'COUNTRY_GQ', 'COUNTRY_GR', 'COUNTRY_GS', 'COUNTRY_GT', 'COUNTRY_GU', 'COUNTRY_GW', 'COUNTRY_GY', 'COUNTRY_HK', 'COUNTRY_HM', 'COUNTRY_HN', 'COUNTRY_HR', 'COUNTRY_HT', 'COUNTRY_HU', 'COUNTRY_ID', 'COUNTRY_IE', 'COUNTRY_IL', 'COUNTRY_IM', 'COUNTRY_IN', 'COUNTRY_IO', 'COUNTRY_IQ', 'COUNTRY_IR', 'COUNTRY_IS', 'COUNTRY_IT', 'COUNTRY_JE', 'COUNTRY_JM', 'COUNTRY_JO', 'COUNTRY_JP', 'COUNTRY_KE', 'COUNTRY_KG', 'COUNTRY_KH', 'COUNTRY_KI', 'COUNTRY_KM', 'COUNTRY_KN', 'COUNTRY_KP', 'COUNTRY_KR', 'COUNTRY_KW', 'COUNTRY_KY', 'COUNTRY_KZ', 'COUNTRY_LA', 'COUNTRY_LB', 'COUNTRY_LC', 'COUNTRY_LI', 'COUNTRY_LK', 'COUNTRY_LR', 'COUNTRY_LS', 'COUNTRY_LT', 'COUNTRY_LU', 'COUNTRY_LV', 'COUNTRY_LY', 'COUNTRY_MA', 'COUNTRY_MC', 'COUNTRY_MD', 'COUNTRY_ME', 'COUNTRY_MF', 'COUNTRY_MG', 'COUNTRY_MH', 'COUNTRY_MK', 'COUNTRY_ML', 'COUNTRY_MM', 'COUNTRY_MN', 'COUNTRY_MO', 'COUNTRY_MP', 'COUNTRY_MQ', 'COUNTRY_MR', 'COUNTRY_MS', 'COUNTRY_MT', 'COUNTRY_MU', 'COUNTRY_MV', 'COUNTRY_MW', 'COUNTRY_MX', 'COUNTRY_MY', 'COUNTRY_MZ', 'COUNTRY_NA', 'COUNTRY_NC', 'COUNTRY_NE', 'COUNTRY_NF', 'COUNTRY_NG', 'COUNTRY_NI', 'COUNTRY_NL', 'COUNTRY_NO', 'COUNTRY_NP', 'COUNTRY_NR', 'COUNTRY_NU', 'COUNTRY_NZ', 'COUNTRY_OM', 'COUNTRY_PA', 'COUNTRY_PE', 'COUNTRY_PF', 'COUNTRY_PG', 'COUNTRY_PH', 'COUNTRY_PK', 'COUNTRY_PL', 'COUNTRY_PM', 'COUNTRY_PN', 'COUNTRY_PR', 'COUNTRY_PS', 'COUNTRY_PT', 'COUNTRY_PW', 'COUNTRY_PY', 'COUNTRY_QA', 'COUNTRY_RE', 'COUNTRY_RO', 'COUNTRY_RS', 'COUNTRY_RU', 'COUNTRY_RW', 'COUNTRY_SA', 'COUNTRY_SB', 'COUNTRY_SC', 'COUNTRY_SD', 'COUNTRY_SE', 'COUNTRY_SG', 'COUNTRY_SH', 'COUNTRY_SI', 'COUNTRY_SJ', 'COUNTRY_SK', 'COUNTRY_SL', 'COUNTRY_SM', 'COUNTRY_SN', 'COUNTRY_SO', 'COUNTRY_SR', 'COUNTRY_SS', 'COUNTRY_ST', 'COUNTRY_SV', 'COUNTRY_SX', 'COUNTRY_SY', 'COUNTRY_SZ', 'COUNTRY_TC', 'COUNTRY_TD', 'COUNTRY_TF', 'COUNTRY_TG', 'COUNTRY_TH', 'COUNTRY_TJ', 'COUNTRY_TK', 'COUNTRY_TL', 'COUNTRY_TM', 'COUNTRY_TN', 'COUNTRY_TO', 'COUNTRY_TR', 'COUNTRY_TT', 'COUNTRY_TV', 'COUNTRY_TW', 'COUNTRY_TZ', 'COUNTRY_UA', 'COUNTRY_UG', 'COUNTRY_UM', 'COUNTRY_US', 'COUNTRY_UY', 'COUNTRY_UZ', 'COUNTRY_VA', 'COUNTRY_VC', 'COUNTRY_VE', 'COUNTRY_VG', 'COUNTRY_VI', 'COUNTRY_VN', 'COUNTRY_VU', 'COUNTRY_WF', 'COUNTRY_WS', 'COUNTRY_XK', 'COUNTRY_XT', 'COUNTRY_YE', 'COUNTRY_YT', 'COUNTRY_ZA', 'COUNTRY_ZM', 'COUNTRY_ZW']]] = None
    ja4_tls_fingerprint_matcher: Optional[JA4TlsFingerprintMatcherType] = None
    tls_fingerprint_matcher: Optional[TlsFingerprintMatcherType] = None


class PrefixMatchList(F5XCBaseModel):
    """List of IP Prefix strings to match against."""

    invert_match: Optional[bool] = None
    ip_prefixes: Optional[list[str]] = None


class DDoSMitigationRule(F5XCBaseModel):
    """DDoS Mitigation Rule specifies the sources to be blocked"""

    block: Optional[Any] = None
    ddos_client_source: Optional[DDoSClientSource] = None
    expiration_timestamp: Optional[str] = None
    ip_prefix_list: Optional[PrefixMatchList] = None
    metadata: Optional[MessageMetaType] = None


class DeleteDoSAutoMitigationRuleRsp(F5XCBaseModel):
    """Response of Delete DoS Auto-Mitigation Rule API"""

    name: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class Destination(F5XCBaseModel):
    """A reference to the object on which the DoS Attack is going to be mitigated"""

    virtual_host: Optional[list[ObjectRefType]] = None


class GetSpecType(F5XCBaseModel):
    """Get DoS Mitigation"""

    as_numbers: Optional[list[int]] = None
    countries: Optional[list[Literal['COUNTRY_NONE', 'COUNTRY_AD', 'COUNTRY_AE', 'COUNTRY_AF', 'COUNTRY_AG', 'COUNTRY_AI', 'COUNTRY_AL', 'COUNTRY_AM', 'COUNTRY_AN', 'COUNTRY_AO', 'COUNTRY_AQ', 'COUNTRY_AR', 'COUNTRY_AS', 'COUNTRY_AT', 'COUNTRY_AU', 'COUNTRY_AW', 'COUNTRY_AX', 'COUNTRY_AZ', 'COUNTRY_BA', 'COUNTRY_BB', 'COUNTRY_BD', 'COUNTRY_BE', 'COUNTRY_BF', 'COUNTRY_BG', 'COUNTRY_BH', 'COUNTRY_BI', 'COUNTRY_BJ', 'COUNTRY_BL', 'COUNTRY_BM', 'COUNTRY_BN', 'COUNTRY_BO', 'COUNTRY_BQ', 'COUNTRY_BR', 'COUNTRY_BS', 'COUNTRY_BT', 'COUNTRY_BV', 'COUNTRY_BW', 'COUNTRY_BY', 'COUNTRY_BZ', 'COUNTRY_CA', 'COUNTRY_CC', 'COUNTRY_CD', 'COUNTRY_CF', 'COUNTRY_CG', 'COUNTRY_CH', 'COUNTRY_CI', 'COUNTRY_CK', 'COUNTRY_CL', 'COUNTRY_CM', 'COUNTRY_CN', 'COUNTRY_CO', 'COUNTRY_CR', 'COUNTRY_CS', 'COUNTRY_CU', 'COUNTRY_CV', 'COUNTRY_CW', 'COUNTRY_CX', 'COUNTRY_CY', 'COUNTRY_CZ', 'COUNTRY_DE', 'COUNTRY_DJ', 'COUNTRY_DK', 'COUNTRY_DM', 'COUNTRY_DO', 'COUNTRY_DZ', 'COUNTRY_EC', 'COUNTRY_EE', 'COUNTRY_EG', 'COUNTRY_EH', 'COUNTRY_ER', 'COUNTRY_ES', 'COUNTRY_ET', 'COUNTRY_FI', 'COUNTRY_FJ', 'COUNTRY_FK', 'COUNTRY_FM', 'COUNTRY_FO', 'COUNTRY_FR', 'COUNTRY_GA', 'COUNTRY_GB', 'COUNTRY_GD', 'COUNTRY_GE', 'COUNTRY_GF', 'COUNTRY_GG', 'COUNTRY_GH', 'COUNTRY_GI', 'COUNTRY_GL', 'COUNTRY_GM', 'COUNTRY_GN', 'COUNTRY_GP', 'COUNTRY_GQ', 'COUNTRY_GR', 'COUNTRY_GS', 'COUNTRY_GT', 'COUNTRY_GU', 'COUNTRY_GW', 'COUNTRY_GY', 'COUNTRY_HK', 'COUNTRY_HM', 'COUNTRY_HN', 'COUNTRY_HR', 'COUNTRY_HT', 'COUNTRY_HU', 'COUNTRY_ID', 'COUNTRY_IE', 'COUNTRY_IL', 'COUNTRY_IM', 'COUNTRY_IN', 'COUNTRY_IO', 'COUNTRY_IQ', 'COUNTRY_IR', 'COUNTRY_IS', 'COUNTRY_IT', 'COUNTRY_JE', 'COUNTRY_JM', 'COUNTRY_JO', 'COUNTRY_JP', 'COUNTRY_KE', 'COUNTRY_KG', 'COUNTRY_KH', 'COUNTRY_KI', 'COUNTRY_KM', 'COUNTRY_KN', 'COUNTRY_KP', 'COUNTRY_KR', 'COUNTRY_KW', 'COUNTRY_KY', 'COUNTRY_KZ', 'COUNTRY_LA', 'COUNTRY_LB', 'COUNTRY_LC', 'COUNTRY_LI', 'COUNTRY_LK', 'COUNTRY_LR', 'COUNTRY_LS', 'COUNTRY_LT', 'COUNTRY_LU', 'COUNTRY_LV', 'COUNTRY_LY', 'COUNTRY_MA', 'COUNTRY_MC', 'COUNTRY_MD', 'COUNTRY_ME', 'COUNTRY_MF', 'COUNTRY_MG', 'COUNTRY_MH', 'COUNTRY_MK', 'COUNTRY_ML', 'COUNTRY_MM', 'COUNTRY_MN', 'COUNTRY_MO', 'COUNTRY_MP', 'COUNTRY_MQ', 'COUNTRY_MR', 'COUNTRY_MS', 'COUNTRY_MT', 'COUNTRY_MU', 'COUNTRY_MV', 'COUNTRY_MW', 'COUNTRY_MX', 'COUNTRY_MY', 'COUNTRY_MZ', 'COUNTRY_NA', 'COUNTRY_NC', 'COUNTRY_NE', 'COUNTRY_NF', 'COUNTRY_NG', 'COUNTRY_NI', 'COUNTRY_NL', 'COUNTRY_NO', 'COUNTRY_NP', 'COUNTRY_NR', 'COUNTRY_NU', 'COUNTRY_NZ', 'COUNTRY_OM', 'COUNTRY_PA', 'COUNTRY_PE', 'COUNTRY_PF', 'COUNTRY_PG', 'COUNTRY_PH', 'COUNTRY_PK', 'COUNTRY_PL', 'COUNTRY_PM', 'COUNTRY_PN', 'COUNTRY_PR', 'COUNTRY_PS', 'COUNTRY_PT', 'COUNTRY_PW', 'COUNTRY_PY', 'COUNTRY_QA', 'COUNTRY_RE', 'COUNTRY_RO', 'COUNTRY_RS', 'COUNTRY_RU', 'COUNTRY_RW', 'COUNTRY_SA', 'COUNTRY_SB', 'COUNTRY_SC', 'COUNTRY_SD', 'COUNTRY_SE', 'COUNTRY_SG', 'COUNTRY_SH', 'COUNTRY_SI', 'COUNTRY_SJ', 'COUNTRY_SK', 'COUNTRY_SL', 'COUNTRY_SM', 'COUNTRY_SN', 'COUNTRY_SO', 'COUNTRY_SR', 'COUNTRY_SS', 'COUNTRY_ST', 'COUNTRY_SV', 'COUNTRY_SX', 'COUNTRY_SY', 'COUNTRY_SZ', 'COUNTRY_TC', 'COUNTRY_TD', 'COUNTRY_TF', 'COUNTRY_TG', 'COUNTRY_TH', 'COUNTRY_TJ', 'COUNTRY_TK', 'COUNTRY_TL', 'COUNTRY_TM', 'COUNTRY_TN', 'COUNTRY_TO', 'COUNTRY_TR', 'COUNTRY_TT', 'COUNTRY_TV', 'COUNTRY_TW', 'COUNTRY_TZ', 'COUNTRY_UA', 'COUNTRY_UG', 'COUNTRY_UM', 'COUNTRY_US', 'COUNTRY_UY', 'COUNTRY_UZ', 'COUNTRY_VA', 'COUNTRY_VC', 'COUNTRY_VE', 'COUNTRY_VG', 'COUNTRY_VI', 'COUNTRY_VN', 'COUNTRY_VU', 'COUNTRY_WF', 'COUNTRY_WS', 'COUNTRY_XK', 'COUNTRY_XT', 'COUNTRY_YE', 'COUNTRY_YT', 'COUNTRY_ZA', 'COUNTRY_ZM', 'COUNTRY_ZW']]] = None
    destination: Optional[Destination] = None
    expiration_never: Optional[Any] = None
    expiration_timestamp: Optional[str] = None
    expiration_ttl: Optional[int] = None
    ip_prefixes: Optional[list[str]] = None
    paths: Optional[list[str]] = None
    tls_fingerprints: Optional[list[str]] = None
    type_: Optional[Literal['MITIGATION_MANUAL', 'MITIGATION_AUTOMATIC']] = Field(default=None, alias="type")


class DoSMitigationRuleInfo(F5XCBaseModel):
    """DoS Mitigation Object to auto-configure rules to block attackers"""

    creation_timestamp: Optional[str] = None
    item: Optional[GetSpecType] = None
    name: Optional[str] = None
    uid: Optional[str] = None


class GetDoSAutoMitigationRulesRsp(F5XCBaseModel):
    """Response of GET DDoS Auto-Mitigation Rules API"""

    dos_automitigation_rules: Optional[list[DoSMitigationRuleInfo]] = None


class GetSecurityConfigRsp(F5XCBaseModel):
    api_protection: Optional[list[str]] = None
    app_firewall: Optional[list[str]] = None
    app_firewall_per_route: Optional[list[str]] = None
    bot_defense: Optional[list[str]] = None
    ddos_detection: Optional[list[str]] = None
    protected: Optional[list[str]] = None


class Action(F5XCBaseModel):
    block: Optional[Any] = None
    report: Optional[Any] = None


class DomainMatcherType(F5XCBaseModel):
    """Domain to be matched"""

    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None


class MalwareProtectionRule(F5XCBaseModel):
    """Configure the match criteria to trigger Malware Protection Scan"""

    action: Optional[Action] = None
    domain: Optional[DomainMatcherType] = None
    http_methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None
    metadata: Optional[MessageMetaType] = None
    path: Optional[PathMatcherType] = None


class MalwareProtectionPolicy(F5XCBaseModel):
    """Malware Protection protects Web Apps and APIs, from malicious file..."""

    malware_protection_rules: Optional[list[MalwareProtectionRule]] = None


class MobileSDKConfigType(F5XCBaseModel):
    """Mobile SDK configuration."""

    mobile_identifier: Optional[MobileTrafficIdentifierType] = None


class SensitiveDataPolicySettings(F5XCBaseModel):
    """Settings for data type policy"""

    sensitive_data_policy_ref: Optional[ObjectRefType] = None


class ShapeBotDefensePolicyType(F5XCBaseModel):
    """This defines various configuration options for Bot Defense policy."""

    disable_js_insert: Optional[Any] = None
    disable_mobile_sdk: Optional[Any] = None
    javascript_mode: Optional[Literal['ASYNC_JS_NO_CACHING', 'ASYNC_JS_CACHING', 'SYNC_JS_NO_CACHING', 'SYNC_JS_CACHING']] = None
    js_download_path: Optional[str] = None
    js_insert_all_pages: Optional[ShapeJavaScriptInsertAllType] = None
    js_insert_all_pages_except: Optional[ShapeJavaScriptInsertAllWithExceptionsType] = None
    js_insertion_rules: Optional[ShapeJavaScriptInsertType] = None
    mobile_sdk_config: Optional[MobileSDKConfigType] = None
    protected_app_endpoints: Optional[list[AppEndpointType]] = None


class ShapeBotDefenseType(F5XCBaseModel):
    """This defines various configuration options for Bot Defense Policy."""

    disable_cors_support: Optional[Any] = None
    enable_cors_support: Optional[Any] = None
    policy: Optional[ShapeBotDefensePolicyType] = None
    regional_endpoint: Optional[Literal['AUTO', 'US', 'EU', 'ASIA']] = None
    timeout: Optional[int] = None


class APIProtectionRuleAction(F5XCBaseModel):
    """The action to take if the input request matches the rule."""

    allow: Optional[Any] = None
    deny: Optional[Any] = None


class HttpMethodMatcherType(F5XCBaseModel):
    """A http method matcher specifies a list of methods to match an input HTTP..."""

    invert_matcher: Optional[bool] = None
    methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None


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


class IPThreatCategoryListType(F5XCBaseModel):
    """List of ip threat categories"""

    ip_threat_categories: Optional[list[Literal['SPAM_SOURCES', 'WINDOWS_EXPLOITS', 'WEB_ATTACKS', 'BOTNETS', 'SCANNERS', 'REPUTATION', 'PHISHING', 'PROXY', 'MOBILE_THREATS', 'TOR_PROXY', 'DENIAL_OF_SERVICE', 'NETWORK']]] = None


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


class CookieMatcherType(F5XCBaseModel):
    """A cookie matcher specifies the name of a single cookie and the criteria..."""

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


class APIGroupProtectionRule(F5XCBaseModel):
    """API Protection Rule for a group or a base url"""

    action: Optional[APIProtectionRuleAction] = None
    any_domain: Optional[Any] = None
    api_group: Optional[str] = None
    base_path: Optional[str] = None
    client_matcher: Optional[ClientMatcher] = None
    metadata: Optional[MessageMetaType] = None
    request_matcher: Optional[RequestMatcher] = None
    specific_domain: Optional[str] = None


class APIGroups(F5XCBaseModel):
    api_groups: Optional[list[str]] = None


class APIProtectionRules(F5XCBaseModel):
    """API Protection Rules"""

    api_endpoint_rules: Optional[list[APIEndpointProtectionRule]] = None
    api_groups_rules: Optional[list[APIGroupProtectionRule]] = None


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


class ApiEndpointDetails(F5XCBaseModel):
    """This defines api endpoint"""

    methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None
    path: Optional[str] = None


class BypassRateLimitingRule(F5XCBaseModel):
    any_domain: Optional[Any] = None
    any_url: Optional[Any] = None
    api_endpoint: Optional[ApiEndpointDetails] = None
    api_groups: Optional[APIGroups] = None
    base_path: Optional[str] = None
    client_matcher: Optional[ClientMatcher] = None
    request_matcher: Optional[RequestMatcher] = None
    specific_domain: Optional[str] = None


class BypassRateLimitingRules(F5XCBaseModel):
    """This category defines rules per URL or API group. If request matches any..."""

    bypass_rate_limiting_rules: Optional[list[BypassRateLimitingRule]] = None


class CustomIpAllowedList(F5XCBaseModel):
    """IP Allowed list using existing ip_prefix_set objects"""

    rate_limiter_allowed_prefixes: Optional[list[ObjectRefType]] = None


class PrefixStringListType(F5XCBaseModel):
    """x-example: '192.168.20.0/24' List of IPv4 prefixes that represent an endpoint"""

    prefixes: Optional[list[str]] = None


class ServerUrlRule(F5XCBaseModel):
    any_domain: Optional[Any] = None
    api_group: Optional[str] = None
    base_path: Optional[str] = None
    client_matcher: Optional[ClientMatcher] = None
    inline_rate_limiter: Optional[InlineRateLimiter] = None
    ref_rate_limiter: Optional[ObjectRefType] = None
    request_matcher: Optional[RequestMatcher] = None
    specific_domain: Optional[str] = None


class APIRateLimit(F5XCBaseModel):
    api_endpoint_rules: Optional[list[ApiEndpointRule]] = None
    bypass_rate_limiting_rules: Optional[BypassRateLimitingRules] = None
    custom_ip_allowed_list: Optional[CustomIpAllowedList] = None
    ip_allowed_list: Optional[PrefixStringListType] = None
    no_ip_allowed_list: Optional[Any] = None
    server_url_rules: Optional[list[ServerUrlRule]] = None


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


class ValidateApiBySpecRule(F5XCBaseModel):
    """Define API groups, base paths, or API endpoints and their OpenAPI..."""

    fall_through_mode: Optional[OpenApiFallThroughMode] = None
    open_api_validation_rules: Optional[list[OpenApiValidationRule]] = None
    settings: Optional[OpenApiValidationCommonSettings] = None


class APISpecificationSettings(F5XCBaseModel):
    """Settings for api specification (api definition, OpenAPI validation, etc.)"""

    api_definition: Optional[ObjectRefType] = None
    validation_all_spec_endpoints: Optional[OpenApiValidationAllSpecEndpointsSettings] = None
    validation_custom_list: Optional[ValidateApiBySpecRule] = None
    validation_disabled: Optional[Any] = None


class ApiCodeRepos(F5XCBaseModel):
    """Select which API repositories represent the LB applications"""

    api_code_repo: Optional[list[str]] = None


class BlindfoldSecretInfoType(F5XCBaseModel):
    """BlindfoldSecretInfoType specifies information about the Secret managed..."""

    decryption_provider: Optional[str] = None
    location: Optional[str] = None
    store_provider: Optional[str] = None


class ClearSecretInfoType(F5XCBaseModel):
    """ClearSecretInfoType specifies information about the Secret that is not encrypted."""

    provider: Optional[str] = None
    url: Optional[str] = None


class SecretType(F5XCBaseModel):
    """SecretType is used in an object to indicate a sensitive/confidential field"""

    blindfold_secret_info: Optional[BlindfoldSecretInfoType] = None
    clear_secret_info: Optional[ClearSecretInfoType] = None


class SimpleLogin(F5XCBaseModel):
    password: Optional[SecretType] = None
    user: Optional[str] = None


class DomainConfiguration(F5XCBaseModel):
    """The DomainConfiguration message"""

    domain: Optional[str] = None
    simple_login: Optional[SimpleLogin] = None


class ApiCrawlerConfiguration(F5XCBaseModel):
    domains: Optional[list[DomainConfiguration]] = None


class ApiCrawler(F5XCBaseModel):
    """Api Crawler message"""

    api_crawler_config: Optional[ApiCrawlerConfiguration] = None
    disable_api_crawler: Optional[Any] = None


class ApiDiscoveryAdvancedSettings(F5XCBaseModel):
    """API Discovery Advanced settings"""

    api_discovery_ref: Optional[ObjectRefType] = None


class CodeBaseIntegrationSelection(F5XCBaseModel):
    all_repos: Optional[Any] = None
    code_base_integration: Optional[ObjectRefType] = None
    selected_repos: Optional[ApiCodeRepos] = None


class ApiDiscoveryFromCodeScan(F5XCBaseModel):
    """x-required"""

    code_base_integrations: Optional[list[CodeBaseIntegrationSelection]] = None


class ApiDiscoverySetting(F5XCBaseModel):
    """Specifies the settings used for API discovery"""

    api_crawler: Optional[ApiCrawler] = None
    api_discovery_from_code_scan: Optional[ApiDiscoveryFromCodeScan] = None
    custom_api_auth_discovery: Optional[ApiDiscoveryAdvancedSettings] = None
    default_api_auth_discovery: Optional[Any] = None
    disable_learn_from_redirect_traffic: Optional[Any] = None
    discovered_api_settings: Optional[DiscoveredAPISettings] = None
    enable_learn_from_redirect_traffic: Optional[Any] = None


class Audiences(F5XCBaseModel):
    audiences: Optional[list[str]] = None


class BasePathsType(F5XCBaseModel):
    base_paths: Optional[list[str]] = None


class ArgMatcherType(F5XCBaseModel):
    """A argument matcher specifies the name of a single argument in the body..."""

    check_not_present: Optional[Any] = None
    check_present: Optional[Any] = None
    invert_matcher: Optional[bool] = None
    item: Optional[MatcherType] = None
    name: Optional[str] = None


class MatcherTypeBasic(F5XCBaseModel):
    """A matcher specifies multiple criteria for matching an input string. The..."""

    exact_values: Optional[list[str]] = None
    regex_values: Optional[list[str]] = None


class PathMatcherType(F5XCBaseModel):
    """A path matcher specifies multiple criteria for matching an HTTP path..."""

    exact_values: Optional[list[str]] = None
    invert_matcher: Optional[bool] = None
    prefix_values: Optional[list[str]] = None
    regex_values: Optional[list[str]] = None
    suffix_values: Optional[list[str]] = None
    transformers: Optional[list[Literal['LOWER_CASE', 'UPPER_CASE', 'BASE64_DECODE', 'NORMALIZE_PATH', 'REMOVE_WHITESPACE', 'URL_DECODE', 'TRIM_LEFT', 'TRIM_RIGHT', 'TRIM']]] = None


class ChallengeRuleSpec(F5XCBaseModel):
    """A Challenge Rule consists of an unordered list of predicates and an..."""

    any_asn: Optional[Any] = None
    any_client: Optional[Any] = None
    any_ip: Optional[Any] = None
    arg_matchers: Optional[list[ArgMatcherType]] = None
    asn_list: Optional[AsnMatchList] = None
    asn_matcher: Optional[AsnMatcherType] = None
    body_matcher: Optional[MatcherType] = None
    client_selector: Optional[LabelSelectorType] = None
    cookie_matchers: Optional[list[CookieMatcherType]] = None
    disable_challenge: Optional[Any] = None
    domain_matcher: Optional[MatcherTypeBasic] = None
    enable_captcha_challenge: Optional[Any] = None
    enable_javascript_challenge: Optional[Any] = None
    expiration_timestamp: Optional[str] = None
    headers: Optional[list[HeaderMatcherType]] = None
    http_method: Optional[HttpMethodMatcherType] = None
    ip_matcher: Optional[IpMatcherType] = None
    ip_prefix_list: Optional[PrefixMatchList] = None
    path: Optional[PathMatcherType] = None
    query_params: Optional[list[QueryParameterMatcherType]] = None
    tls_fingerprint_matcher: Optional[TlsFingerprintMatcherType] = None


class ChallengeRule(F5XCBaseModel):
    """Challenge rule"""

    metadata: Optional[MessageMetaType] = None
    spec: Optional[ChallengeRuleSpec] = None


class ChallengeRuleList(F5XCBaseModel):
    """List of challenge rules to be used in policy based challenge"""

    rules: Optional[list[ChallengeRule]] = None


class CaptchaChallengeType(F5XCBaseModel):
    """ Enables loadbalancer to perform captcha challenge  Captcha challenge..."""

    cookie_expiry: Optional[int] = None
    custom_page: Optional[str] = None


class JavascriptChallengeType(F5XCBaseModel):
    """ Enables loadbalancer to perform client browser compatibility test by..."""

    cookie_expiry: Optional[int] = None
    custom_page: Optional[str] = None
    js_script_delay: Optional[int] = None


class EnableChallenge(F5XCBaseModel):
    """Configure auto mitigation i.e risk based challenges for malicious users"""

    captcha_challenge_parameters: Optional[CaptchaChallengeType] = None
    default_captcha_challenge_parameters: Optional[Any] = None
    default_js_challenge_parameters: Optional[Any] = None
    default_mitigation_settings: Optional[Any] = None
    js_challenge_parameters: Optional[JavascriptChallengeType] = None
    malicious_user_mitigation: Optional[ObjectRefType] = None


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


class JWKS(F5XCBaseModel):
    """The JSON Web Key Set (JWKS) is a set of keys used to verify JSON Web..."""

    cleartext: Optional[str] = None


class MandatoryClaims(F5XCBaseModel):
    """Configurable Validation of mandatory Claims."""

    claim_names: Optional[list[str]] = None


class ReservedClaims(F5XCBaseModel):
    """Configurable Validation of reserved Claims"""

    audience: Optional[Audiences] = None
    audience_disable: Optional[Any] = None
    issuer: Optional[str] = None
    issuer_disable: Optional[Any] = None
    validate_period_disable: Optional[Any] = None
    validate_period_enable: Optional[Any] = None


class Target(F5XCBaseModel):
    """Define endpoints for which JWT token validation will be performed"""

    all_endpoint: Optional[Any] = None
    api_groups: Optional[APIGroups] = None
    base_paths: Optional[BasePathsType] = None


class TokenLocation(F5XCBaseModel):
    """Location of JWT in Http request"""

    bearer_token: Optional[Any] = None


class JWTValidation(F5XCBaseModel):
    """JWT Validation stops JWT replay attacks and JWT tampering by..."""

    action: Optional[Action] = None
    jwks_config: Optional[JWKS] = None
    mandatory_claims: Optional[MandatoryClaims] = None
    reserved_claims: Optional[ReservedClaims] = None
    target: Optional[Target] = None
    token_location: Optional[TokenLocation] = None


class PolicyList(F5XCBaseModel):
    """List of rate limiter policies to be applied."""

    policies: Optional[list[ObjectRefType]] = None


class InputHours(F5XCBaseModel):
    """Input Duration Hours"""

    duration: Optional[int] = None


class InputMinutes(F5XCBaseModel):
    """Input Duration Minutes"""

    duration: Optional[int] = None


class InputSeconds(F5XCBaseModel):
    """Input Duration Seconds"""

    duration: Optional[int] = None


class RateLimitBlockAction(F5XCBaseModel):
    """Action where a user is blocked from making further requests after..."""

    hours: Optional[InputHours] = None
    minutes: Optional[InputMinutes] = None
    seconds: Optional[InputSeconds] = None


class LeakyBucketRateLimiter(F5XCBaseModel):
    """Leaky-Bucket is the default rate limiter algorithm for F5"""

    pass


class TokenBucketRateLimiter(F5XCBaseModel):
    """Token-Bucket is a rate limiter algorithm that is stricter with enforcing limits"""

    pass


class RateLimitValue(F5XCBaseModel):
    """A tuple consisting of a rate limit period unit and the total number of..."""

    action_block: Optional[RateLimitBlockAction] = None
    burst_multiplier: Optional[int] = None
    disabled: Optional[Any] = None
    leaky_bucket: Optional[Any] = None
    period_multiplier: Optional[int] = None
    token_bucket: Optional[Any] = None
    total_number: Optional[int] = None
    unit: Optional[Literal['SECOND', 'MINUTE', 'HOUR']] = None


class RateLimitConfigType(F5XCBaseModel):
    custom_ip_allowed_list: Optional[CustomIpAllowedList] = None
    ip_allowed_list: Optional[PrefixStringListType] = None
    no_ip_allowed_list: Optional[Any] = None
    no_policies: Optional[Any] = None
    policies: Optional[PolicyList] = None
    rate_limiter: Optional[RateLimitValue] = None


class ServicePolicyList(F5XCBaseModel):
    """List of service policies."""

    policies: Optional[list[ObjectRefType]] = None


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


class WafExclusionInlineRules(F5XCBaseModel):
    """A list of WAF exclusion rules that will be applied inline"""

    rules: Optional[list[SimpleWafExclusionRule]] = None


class WafExclusion(F5XCBaseModel):
    waf_exclusion_inline_rules: Optional[WafExclusionInlineRules] = None
    waf_exclusion_policy: Optional[ObjectRefType] = None


class APIGroupsApiep(F5XCBaseModel):
    """Apiep for the Evaluate Api Group Builder response."""

    category: Optional[list[Literal['APIEP_CATEGORY_DISCOVERED', 'APIEP_CATEGORY_SWAGGER', 'APIEP_CATEGORY_INVENTORY', 'APIEP_CATEGORY_SHADOW', 'APIEP_CATEGORY_DEPRECATED', 'APIEP_CATEGORY_NON_API']]] = None
    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    path: Optional[str] = None
    risk_score: Optional[RiskScore] = None
    sensitive_data: Optional[list[Literal['SENSITIVE_DATA_TYPE_CCN', 'SENSITIVE_DATA_TYPE_SSN', 'SENSITIVE_DATA_TYPE_IP', 'SENSITIVE_DATA_TYPE_EMAIL', 'SENSITIVE_DATA_TYPE_PHONE', 'SENSITIVE_DATA_TYPE_CREDENTIALS', 'SENSITIVE_DATA_TYPE_APP_INFO_LEAKAGE', 'SENSITIVE_DATA_TYPE_MASKED_PII', 'SENSITIVE_DATA_TYPE_LOCATION']]] = None
    sensitive_data_types: Optional[list[str]] = None


class BufferConfigType(F5XCBaseModel):
    """Some upstream applications are not capable of handling streamed data...."""

    disabled: Optional[bool] = None
    max_request_bytes: Optional[int] = None


class CompressionType(F5XCBaseModel):
    """Enables loadbalancer to compress dispatched data from an upstream..."""

    content_length: Optional[int] = None
    content_type: Optional[list[str]] = None
    disable_on_etag_header: Optional[bool] = None
    remove_accept_encoding_header: Optional[bool] = None


class CookieValueOption(F5XCBaseModel):
    """Cookie name and value for cookie header"""

    name: Optional[str] = None
    overwrite: Optional[bool] = None
    secret_value: Optional[SecretType] = None
    value: Optional[str] = None


class HeaderManipulationOptionType(F5XCBaseModel):
    """HTTP header is a key-value pair. The name acts as key of HTTP header The..."""

    append: Optional[bool] = None
    name: Optional[str] = None
    secret_value: Optional[SecretType] = None
    value: Optional[str] = None


class SetCookieValueOption(F5XCBaseModel):
    """Cookie name and its attribute values in set-cookie header"""

    add_domain: Optional[str] = None
    add_expiry: Optional[str] = None
    add_httponly: Optional[Any] = None
    add_partitioned: Optional[Any] = None
    add_path: Optional[str] = None
    add_secure: Optional[Any] = None
    ignore_domain: Optional[Any] = None
    ignore_expiry: Optional[Any] = None
    ignore_httponly: Optional[Any] = None
    ignore_max_age: Optional[Any] = None
    ignore_partitioned: Optional[Any] = None
    ignore_path: Optional[Any] = None
    ignore_samesite: Optional[Any] = None
    ignore_secure: Optional[Any] = None
    ignore_value: Optional[Any] = None
    max_age_value: Optional[int] = None
    name: Optional[str] = None
    overwrite: Optional[bool] = None
    samesite_lax: Optional[Any] = None
    samesite_none: Optional[Any] = None
    samesite_strict: Optional[Any] = None
    secret_value: Optional[SecretType] = None
    value: Optional[str] = None


class AdvancedOptionsType(F5XCBaseModel):
    """This defines various options to define a route"""

    buffer_policy: Optional[BufferConfigType] = None
    compression_params: Optional[CompressionType] = None
    custom_errors: Optional[dict[str, Any]] = None
    disable_default_error_pages: Optional[bool] = None
    disable_path_normalize: Optional[Any] = None
    enable_path_normalize: Optional[Any] = None
    idle_timeout: Optional[int] = None
    max_request_header_size: Optional[int] = None
    request_cookies_to_add: Optional[list[CookieValueOption]] = None
    request_cookies_to_remove: Optional[list[str]] = None
    request_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    request_headers_to_remove: Optional[list[str]] = None
    response_cookies_to_add: Optional[list[SetCookieValueOption]] = None
    response_cookies_to_remove: Optional[list[str]] = None
    response_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    response_headers_to_remove: Optional[list[str]] = None


class ApiKey(F5XCBaseModel):
    key: Optional[str] = None
    value: Optional[SecretType] = None


class BasicAuthentication(F5XCBaseModel):
    password: Optional[SecretType] = None
    user: Optional[str] = None


class Bearer(F5XCBaseModel):
    token: Optional[SecretType] = None


class LoginEndpoint(F5XCBaseModel):
    json_payload: Optional[SecretType] = None
    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    path: Optional[str] = None
    token_response_key: Optional[str] = None


class Credentials(F5XCBaseModel):
    """Configure credential details, including type(e.g., API Key, bearer..."""

    admin: Optional[Any] = None
    api_key: Optional[ApiKey] = None
    basic_auth: Optional[BasicAuthentication] = None
    bearer_token: Optional[Bearer] = None
    credential_name: Optional[str] = None
    login_endpoint: Optional[LoginEndpoint] = None
    standard: Optional[Any] = None


class DomainConfiguration(F5XCBaseModel):
    """The Domain configuration message"""

    allow_destructive_methods: Optional[bool] = None
    credentials: Optional[list[Credentials]] = None
    domain: Optional[str] = None


class ApiTesting(F5XCBaseModel):
    custom_header_value: Optional[str] = None
    domains: Optional[list[DomainConfiguration]] = None
    every_day: Optional[Any] = None
    every_month: Optional[Any] = None
    every_week: Optional[Any] = None


class AssignAPIDefinitionReq(F5XCBaseModel):
    """Request form for Assign API Definition"""

    api_definition: Optional[ObjectRefType] = None
    create_if_not_exists: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class AssignAPIDefinitionResp(F5XCBaseModel):
    """Response form for Assign API Definition"""

    pass


class BodySectionMaskingOptions(F5XCBaseModel):
    """Options for HTTP Body Masking"""

    fields: Optional[list[str]] = None


class DefaultCacheAction(F5XCBaseModel):
    """This defines a Default Cache Action"""

    cache_disabled: Optional[Any] = None
    cache_ttl_default: Optional[str] = None
    cache_ttl_override: Optional[str] = None


class CachingPolicy(F5XCBaseModel):
    """x-required Caching Policies for the CDN"""

    custom_cache_rule: Optional[CustomCacheRule] = None
    default_cache_action: Optional[DefaultCacheAction] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class AdvertisePublic(F5XCBaseModel):
    """This defines a way to advertise a load balancer on public. If optional..."""

    public_ip: Optional[ObjectRefType] = None


class WhereSite(F5XCBaseModel):
    """This defines a reference to a CE site along with network type and an..."""

    ip: Optional[str] = None
    network: Optional[Literal['SITE_NETWORK_INSIDE_AND_OUTSIDE', 'SITE_NETWORK_INSIDE', 'SITE_NETWORK_OUTSIDE', 'SITE_NETWORK_SERVICE', 'SITE_NETWORK_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_INSIDE_AND_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_IP_FABRIC']] = None
    site: Optional[ObjectRefType] = None


class WhereVirtualNetwork(F5XCBaseModel):
    """Parameters to advertise on a given virtual network"""

    default_v6_vip: Optional[Any] = None
    default_vip: Optional[Any] = None
    specific_v6_vip: Optional[str] = None
    specific_vip: Optional[str] = None
    virtual_network: Optional[ObjectRefType] = None


class WhereVirtualSite(F5XCBaseModel):
    """This defines a reference to a customer site virtual site along with..."""

    network: Optional[Literal['SITE_NETWORK_INSIDE_AND_OUTSIDE', 'SITE_NETWORK_INSIDE', 'SITE_NETWORK_OUTSIDE', 'SITE_NETWORK_SERVICE', 'SITE_NETWORK_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_INSIDE_AND_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_IP_FABRIC']] = None
    virtual_site: Optional[ObjectRefType] = None


class WhereVirtualSiteSpecifiedVIP(F5XCBaseModel):
    """This defines a reference to a customer site virtual site along with..."""

    ip: Optional[str] = None
    network: Optional[Literal['SITE_NETWORK_SPECIFIED_VIP_OUTSIDE', 'SITE_NETWORK_SPECIFIED_VIP_INSIDE']] = None
    virtual_site: Optional[ObjectRefType] = None


class WhereVK8SService(F5XCBaseModel):
    """This defines a reference to a RE site or virtual site where a load..."""

    site: Optional[ObjectRefType] = None
    virtual_site: Optional[ObjectRefType] = None


class WhereType(F5XCBaseModel):
    """This defines various options where a Loadbalancer could be advertised"""

    advertise_on_public: Optional[AdvertisePublic] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None
    site: Optional[WhereSite] = None
    use_default_port: Optional[Any] = None
    virtual_network: Optional[WhereVirtualNetwork] = None
    virtual_site: Optional[WhereVirtualSite] = None
    virtual_site_with_vip: Optional[WhereVirtualSiteSpecifiedVIP] = None
    vk8s_service: Optional[WhereVK8SService] = None


class AdvertiseCustom(F5XCBaseModel):
    """This defines a way to advertise a VIP on specific sites"""

    advertise_where: Optional[list[WhereType]] = None


class CookieForHashing(F5XCBaseModel):
    """Two types of cookie affinity:  1. Passive. Takes a cookie that's present..."""

    add_httponly: Optional[Any] = None
    add_secure: Optional[Any] = None
    ignore_httponly: Optional[Any] = None
    ignore_samesite: Optional[Any] = None
    ignore_secure: Optional[Any] = None
    name: Optional[str] = None
    path: Optional[str] = None
    samesite_lax: Optional[Any] = None
    samesite_none: Optional[Any] = None
    samesite_strict: Optional[Any] = None
    ttl: Optional[int] = None


class CorsPolicy(F5XCBaseModel):
    """Cross-Origin Resource Sharing requests configuration specified at..."""

    allow_credentials: Optional[bool] = None
    allow_headers: Optional[str] = None
    allow_methods: Optional[str] = None
    allow_origin: Optional[list[str]] = None
    allow_origin_regex: Optional[list[str]] = None
    disabled: Optional[bool] = None
    expose_headers: Optional[str] = None
    maximum_age: Optional[int] = None


class DomainNameList(F5XCBaseModel):
    """List of domain names used for Host header matching"""

    domains: Optional[list[str]] = None


class CsrfPolicy(F5XCBaseModel):
    """To mitigate CSRF attack , the policy checks where a request is coming..."""

    all_load_balancer_domains: Optional[Any] = None
    custom_domain_list: Optional[DomainNameList] = None
    disabled: Optional[Any] = None


class SimpleDataGuardRule(F5XCBaseModel):
    """Simple Data Guard rule specifies a simple set of match conditions to..."""

    any_domain: Optional[Any] = None
    apply_data_guard: Optional[Any] = None
    exact_value: Optional[str] = None
    metadata: Optional[MessageMetaType] = None
    path: Optional[PathMatcherType] = None
    skip_data_guard: Optional[Any] = None
    suffix_value: Optional[str] = None


class OriginPoolDefaultSubset(F5XCBaseModel):
    """Default Subset definition"""

    default_subset: Optional[dict[str, Any]] = None


class OriginPoolSubsets(F5XCBaseModel):
    """Configure subset options for origin pool"""

    any_endpoint: Optional[Any] = None
    default_subset: Optional[OriginPoolDefaultSubset] = None
    endpoint_subsets: Optional[list[EndpointSubsetSelectorType]] = None
    fail_request: Optional[Any] = None


class HeaderTransformationType(F5XCBaseModel):
    """Header Transformation options for HTTP/1.1 request/response headers"""

    default_header_transformation: Optional[Any] = None
    legacy_header_transformation: Optional[Any] = None
    preserve_case_header_transformation: Optional[Any] = None
    proper_case_header_transformation: Optional[Any] = None


class Http1ProtocolOptions(F5XCBaseModel):
    """HTTP/1.1 Protocol options for upstream connections"""

    header_transformation: Optional[HeaderTransformationType] = None


class OriginPoolAdvancedOptions(F5XCBaseModel):
    """Configure Advanced options for origin pool"""

    auto_http_config: Optional[Any] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    connection_timeout: Optional[int] = None
    default_circuit_breaker: Optional[Any] = None
    disable_circuit_breaker: Optional[Any] = None
    disable_lb_source_ip_persistance: Optional[Any] = None
    disable_outlier_detection: Optional[Any] = None
    disable_proxy_protocol: Optional[Any] = None
    disable_subsets: Optional[Any] = None
    enable_lb_source_ip_persistance: Optional[Any] = None
    enable_subsets: Optional[OriginPoolSubsets] = None
    http1_config: Optional[Http1ProtocolOptions] = None
    http2_options: Optional[Http2ProtocolOptions] = None
    http_idle_timeout: Optional[int] = None
    no_panic_threshold: Optional[Any] = None
    outlier_detection: Optional[OutlierDetectionType] = None
    panic_threshold: Optional[int] = None
    proxy_protocol_v1: Optional[Any] = None
    proxy_protocol_v2: Optional[Any] = None


class OriginServerCBIPService(F5XCBaseModel):
    """Specify origin server with Classic BIG-IP Service (Virtual Server)"""

    service_name: Optional[str] = None


class SiteLocator(F5XCBaseModel):
    """This message defines a reference to a site or virtual site object"""

    site: Optional[ObjectRefType] = None
    virtual_site: Optional[ObjectRefType] = None


class SnatPoolConfiguration(F5XCBaseModel):
    """Snat Pool configuration"""

    no_snat_pool: Optional[Any] = None
    snat_pool: Optional[PrefixStringListType] = None


class OriginServerConsulService(F5XCBaseModel):
    """Specify origin server with Hashi Corp Consul service name and site information"""

    inside_network: Optional[Any] = None
    outside_network: Optional[Any] = None
    service_name: Optional[str] = None
    site_locator: Optional[SiteLocator] = None
    snat_pool: Optional[SnatPoolConfiguration] = None


class OriginServerCustomEndpoint(F5XCBaseModel):
    """Specify origin server with a reference to endpoint object"""

    endpoint: Optional[ObjectRefType] = None


class OriginServerK8SService(F5XCBaseModel):
    """Specify origin server with K8s service name and site information"""

    inside_network: Optional[Any] = None
    outside_network: Optional[Any] = None
    protocol: Optional[Literal['PROTOCOL_TCP', 'PROTOCOL_UDP']] = None
    service_name: Optional[str] = None
    site_locator: Optional[SiteLocator] = None
    snat_pool: Optional[SnatPoolConfiguration] = None
    vk8s_networks: Optional[Any] = None


class OriginServerPrivateIP(F5XCBaseModel):
    """Specify origin server with private or public IP address and site information"""

    inside_network: Optional[Any] = None
    ip: Optional[str] = None
    outside_network: Optional[Any] = None
    segment: Optional[ObjectRefType] = None
    site_locator: Optional[SiteLocator] = None
    snat_pool: Optional[SnatPoolConfiguration] = None


class OriginServerPrivateName(F5XCBaseModel):
    """Specify origin server with private or public DNS name and site information"""

    dns_name: Optional[str] = None
    inside_network: Optional[Any] = None
    outside_network: Optional[Any] = None
    refresh_interval: Optional[int] = None
    segment: Optional[ObjectRefType] = None
    site_locator: Optional[SiteLocator] = None
    snat_pool: Optional[SnatPoolConfiguration] = None


class OriginServerPublicIP(F5XCBaseModel):
    """Specify origin server with public IP address"""

    ip: Optional[str] = None


class OriginServerPublicName(F5XCBaseModel):
    """Specify origin server with public DNS name"""

    dns_name: Optional[str] = None
    refresh_interval: Optional[int] = None


class OriginServerVirtualNetworkIP(F5XCBaseModel):
    """Specify origin server with IP on Virtual Network"""

    ip: Optional[str] = None
    virtual_network: Optional[ObjectRefType] = None


class OriginServerVirtualNetworkName(F5XCBaseModel):
    """Specify origin server with DNS name on Virtual Network"""

    dns_name: Optional[str] = None
    private_network: Optional[ObjectRefType] = None


class OriginServerType(F5XCBaseModel):
    """Various options to specify origin server"""

    cbip_service: Optional[OriginServerCBIPService] = None
    consul_service: Optional[OriginServerConsulService] = None
    custom_endpoint_object: Optional[OriginServerCustomEndpoint] = None
    k8s_service: Optional[OriginServerK8SService] = None
    labels: Optional[dict[str, Any]] = None
    private_ip: Optional[OriginServerPrivateIP] = None
    private_name: Optional[OriginServerPrivateName] = None
    public_ip: Optional[OriginServerPublicIP] = None
    public_name: Optional[OriginServerPublicName] = None
    vn_private_ip: Optional[OriginServerVirtualNetworkIP] = None
    vn_private_name: Optional[OriginServerVirtualNetworkName] = None


class UpstreamConnPoolReuseType(F5XCBaseModel):
    """Select upstream connection pool reuse state for every downstream..."""

    disable_conn_pool_reuse: Optional[Any] = None
    enable_conn_pool_reuse: Optional[Any] = None


class CustomCiphers(F5XCBaseModel):
    """This defines TLS protocol config including min/max versions and allowed ciphers"""

    cipher_suites: Optional[list[str]] = None
    max_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None
    min_version: Optional[Literal['TLS_AUTO', 'TLSv1_0', 'TLSv1_1', 'TLSv1_2', 'TLSv1_3']] = None


class TlsConfig(F5XCBaseModel):
    """This defines various options to configure TLS configuration parameters"""

    custom_security: Optional[CustomCiphers] = None
    default_security: Optional[Any] = None
    low_security: Optional[Any] = None
    medium_security: Optional[Any] = None


class HashAlgorithms(F5XCBaseModel):
    """Specifies the hash algorithms to be used"""

    hash_algorithms: Optional[list[Literal['INVALID_HASH_ALGORITHM', 'SHA256', 'SHA1']]] = None


class TlsCertificateType(F5XCBaseModel):
    """Handle to fetch certificate and key"""

    certificate_url: Optional[str] = None
    custom_hash_algorithms: Optional[HashAlgorithms] = None
    description: Optional[str] = None
    disable_ocsp_stapling: Optional[Any] = None
    private_key: Optional[SecretType] = None
    use_system_defaults: Optional[Any] = None


class TlsCertificatesType(F5XCBaseModel):
    """mTLS Client Certificate"""

    tls_certificates: Optional[list[TlsCertificateType]] = None


class UpstreamTlsValidationContext(F5XCBaseModel):
    """Upstream TLS Validation Context"""

    trusted_ca: Optional[ObjectRefType] = None
    trusted_ca_url: Optional[str] = None


class UpstreamTlsParameters(F5XCBaseModel):
    """Upstream TLS Parameters"""

    default_session_key_caching: Optional[Any] = None
    disable_session_key_caching: Optional[Any] = None
    disable_sni: Optional[Any] = None
    max_session_keys: Optional[int] = None
    no_mtls: Optional[Any] = None
    skip_server_verification: Optional[Any] = None
    sni: Optional[str] = None
    tls_config: Optional[TlsConfig] = None
    use_host_header_as_sni: Optional[Any] = None
    use_mtls: Optional[TlsCertificatesType] = None
    use_mtls_obj: Optional[ObjectRefType] = None
    use_server_verification: Optional[UpstreamTlsValidationContext] = None
    volterra_trusted_ca: Optional[Any] = None


class GlobalSpecType(F5XCBaseModel):
    """Shape of the origin pool specification"""

    advanced_options: Optional[OriginPoolAdvancedOptions] = None
    automatic_port: Optional[Any] = None
    endpoint_selection: Optional[Literal['DISTRIBUTED', 'LOCAL_ONLY', 'LOCAL_PREFERRED']] = None
    health_check_port: Optional[int] = None
    healthcheck: Optional[list[ObjectRefType]] = None
    lb_port: Optional[Any] = None
    loadbalancer_algorithm: Optional[Literal['ROUND_ROBIN', 'LEAST_REQUEST', 'RING_HASH', 'RANDOM', 'LB_OVERRIDE']] = None
    no_tls: Optional[Any] = None
    origin_servers: Optional[list[OriginServerType]] = None
    port: Optional[int] = None
    same_as_endpoint_port: Optional[Any] = None
    upstream_conn_pool_reuse_type: Optional[UpstreamConnPoolReuseType] = None
    use_tls: Optional[UpstreamTlsParameters] = None
    view_internal: Optional[ObjectRefType] = None


class OriginPoolWithWeight(F5XCBaseModel):
    """This defines a combination of origin pool with weight and priority"""

    cluster: Optional[ObjectRefType] = None
    endpoint_subsets: Optional[dict[str, Any]] = None
    pool: Optional[ObjectRefType] = None
    priority: Optional[int] = None
    weight: Optional[int] = None


class OriginPoolListType(F5XCBaseModel):
    """List of Origin Pools"""

    pools: Optional[list[OriginPoolWithWeight]] = None


class IPThreatCategoryListType(F5XCBaseModel):
    """List of ip threat categories"""

    ip_threat_categories: Optional[list[Literal['SPAM_SOURCES', 'WINDOWS_EXPLOITS', 'WEB_ATTACKS', 'BOTNETS', 'SCANNERS', 'REPUTATION', 'PHISHING', 'PROXY', 'MOBILE_THREATS', 'TOR_PROXY', 'DENIAL_OF_SERVICE', 'NETWORK']]] = None


class ClientIPHeaders(F5XCBaseModel):
    """List of Client IP Headers"""

    client_ip_headers: Optional[list[str]] = None


class GraphQLSettingsType(F5XCBaseModel):
    """GraphQL configuration."""

    disable_introspection: Optional[Any] = None
    enable_introspection: Optional[Any] = None
    max_batched_queries: Optional[int] = None
    max_depth: Optional[int] = None
    max_total_length: Optional[int] = None


class GraphQLRule(F5XCBaseModel):
    """This section defines various configuration options for GraphQL inspection."""

    any_domain: Optional[Any] = None
    exact_path: Optional[str] = None
    exact_value: Optional[str] = None
    graphql_settings: Optional[GraphQLSettingsType] = None
    metadata: Optional[MessageMetaType] = None
    method_get: Optional[Any] = None
    method_post: Optional[Any] = None
    suffix_value: Optional[str] = None


class ProxyTypeHttp(F5XCBaseModel):
    """Choice for selecting HTTP proxy"""

    dns_volterra_managed: Optional[bool] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None


class TLSCoalescingOptions(F5XCBaseModel):
    """TLS connection coalescing configuration (not compatible with mTLS)"""

    default_coalescing: Optional[Any] = None
    strict_coalescing: Optional[Any] = None


class Http1ProtocolOptions(F5XCBaseModel):
    """HTTP/1.1 Protocol options for downstream connections"""

    header_transformation: Optional[HeaderTransformationType] = None


class HttpProtocolOptions(F5XCBaseModel):
    """HTTP protocol configuration options for downstream connections"""

    http_protocol_enable_v1_only: Optional[Http1ProtocolOptions] = None
    http_protocol_enable_v1_v2: Optional[Any] = None
    http_protocol_enable_v2_only: Optional[Any] = None


class XfccHeaderKeys(F5XCBaseModel):
    """X-Forwarded-Client-Cert header elements to be added to requests"""

    xfcc_header_elements: Optional[list[Literal['XFCC_NONE', 'XFCC_CERT', 'XFCC_CHAIN', 'XFCC_SUBJECT', 'XFCC_URI', 'XFCC_DNS']]] = None


class DownstreamTlsValidationContext(F5XCBaseModel):
    """Validation context for downstream client TLS connections"""

    client_certificate_optional: Optional[bool] = None
    crl: Optional[ObjectRefType] = None
    no_crl: Optional[Any] = None
    trusted_ca: Optional[ObjectRefType] = None
    trusted_ca_url: Optional[str] = None
    xfcc_disabled: Optional[Any] = None
    xfcc_options: Optional[XfccHeaderKeys] = None


class DownstreamTLSCertsParams(F5XCBaseModel):
    """Select TLS Parameters and Certificates"""

    certificates: Optional[list[ObjectRefType]] = None
    no_mtls: Optional[Any] = None
    tls_config: Optional[TlsConfig] = None
    use_mtls: Optional[DownstreamTlsValidationContext] = None


class DownstreamTlsParamsType(F5XCBaseModel):
    """Inline TLS parameters"""

    no_mtls: Optional[Any] = None
    tls_certificates: Optional[list[TlsCertificateType]] = None
    tls_config: Optional[TlsConfig] = None
    use_mtls: Optional[DownstreamTlsValidationContext] = None


class ProxyTypeHttps(F5XCBaseModel):
    """Choice for selecting HTTP proxy with bring your own certificates"""

    add_hsts: Optional[bool] = None
    append_server_name: Optional[str] = None
    coalescing_options: Optional[TLSCoalescingOptions] = None
    connection_idle_timeout: Optional[int] = None
    default_header: Optional[Any] = None
    default_loadbalancer: Optional[Any] = None
    disable_path_normalize: Optional[Any] = None
    enable_path_normalize: Optional[Any] = None
    http_protocol_options: Optional[HttpProtocolOptions] = None
    http_redirect: Optional[bool] = None
    non_default_loadbalancer: Optional[Any] = None
    pass_through: Optional[Any] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None
    server_name: Optional[str] = None
    tls_cert_params: Optional[DownstreamTLSCertsParams] = None
    tls_parameters: Optional[DownstreamTlsParamsType] = None


class ProxyTypeHttpsAutoCerts(F5XCBaseModel):
    """Choice for selecting HTTP proxy with bring your own certificates"""

    add_hsts: Optional[bool] = None
    append_server_name: Optional[str] = None
    coalescing_options: Optional[TLSCoalescingOptions] = None
    connection_idle_timeout: Optional[int] = None
    default_header: Optional[Any] = None
    default_loadbalancer: Optional[Any] = None
    disable_path_normalize: Optional[Any] = None
    enable_path_normalize: Optional[Any] = None
    http_protocol_options: Optional[HttpProtocolOptions] = None
    http_redirect: Optional[bool] = None
    no_mtls: Optional[Any] = None
    non_default_loadbalancer: Optional[Any] = None
    pass_through: Optional[Any] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None
    server_name: Optional[str] = None
    tls_config: Optional[TlsConfig] = None
    use_mtls: Optional[DownstreamTlsValidationContext] = None


class L7DDoSProtectionSettings(F5XCBaseModel):
    """L7 DDoS protection is critical for safeguarding web applications, APIs,..."""

    clientside_action_captcha_challenge: Optional[CaptchaChallengeType] = None
    clientside_action_js_challenge: Optional[JavascriptChallengeType] = None
    clientside_action_none: Optional[Any] = None
    ddos_policy_custom: Optional[ObjectRefType] = None
    ddos_policy_none: Optional[Any] = None
    default_rps_threshold: Optional[Any] = None
    mitigation_block: Optional[Any] = None
    mitigation_captcha_challenge: Optional[CaptchaChallengeType] = None
    mitigation_js_challenge: Optional[JavascriptChallengeType] = None
    rps_threshold: Optional[int] = None


class OriginServerSubsetRule(F5XCBaseModel):
    """'Origin Server Subset rule specifies a simple set of match conditions to..."""

    any_asn: Optional[Any] = None
    any_ip: Optional[Any] = None
    asn_list: Optional[AsnMatchList] = None
    asn_matcher: Optional[AsnMatcherType] = None
    client_selector: Optional[LabelSelectorType] = None
    country_codes: Optional[list[Literal['COUNTRY_NONE', 'COUNTRY_AD', 'COUNTRY_AE', 'COUNTRY_AF', 'COUNTRY_AG', 'COUNTRY_AI', 'COUNTRY_AL', 'COUNTRY_AM', 'COUNTRY_AN', 'COUNTRY_AO', 'COUNTRY_AQ', 'COUNTRY_AR', 'COUNTRY_AS', 'COUNTRY_AT', 'COUNTRY_AU', 'COUNTRY_AW', 'COUNTRY_AX', 'COUNTRY_AZ', 'COUNTRY_BA', 'COUNTRY_BB', 'COUNTRY_BD', 'COUNTRY_BE', 'COUNTRY_BF', 'COUNTRY_BG', 'COUNTRY_BH', 'COUNTRY_BI', 'COUNTRY_BJ', 'COUNTRY_BL', 'COUNTRY_BM', 'COUNTRY_BN', 'COUNTRY_BO', 'COUNTRY_BQ', 'COUNTRY_BR', 'COUNTRY_BS', 'COUNTRY_BT', 'COUNTRY_BV', 'COUNTRY_BW', 'COUNTRY_BY', 'COUNTRY_BZ', 'COUNTRY_CA', 'COUNTRY_CC', 'COUNTRY_CD', 'COUNTRY_CF', 'COUNTRY_CG', 'COUNTRY_CH', 'COUNTRY_CI', 'COUNTRY_CK', 'COUNTRY_CL', 'COUNTRY_CM', 'COUNTRY_CN', 'COUNTRY_CO', 'COUNTRY_CR', 'COUNTRY_CS', 'COUNTRY_CU', 'COUNTRY_CV', 'COUNTRY_CW', 'COUNTRY_CX', 'COUNTRY_CY', 'COUNTRY_CZ', 'COUNTRY_DE', 'COUNTRY_DJ', 'COUNTRY_DK', 'COUNTRY_DM', 'COUNTRY_DO', 'COUNTRY_DZ', 'COUNTRY_EC', 'COUNTRY_EE', 'COUNTRY_EG', 'COUNTRY_EH', 'COUNTRY_ER', 'COUNTRY_ES', 'COUNTRY_ET', 'COUNTRY_FI', 'COUNTRY_FJ', 'COUNTRY_FK', 'COUNTRY_FM', 'COUNTRY_FO', 'COUNTRY_FR', 'COUNTRY_GA', 'COUNTRY_GB', 'COUNTRY_GD', 'COUNTRY_GE', 'COUNTRY_GF', 'COUNTRY_GG', 'COUNTRY_GH', 'COUNTRY_GI', 'COUNTRY_GL', 'COUNTRY_GM', 'COUNTRY_GN', 'COUNTRY_GP', 'COUNTRY_GQ', 'COUNTRY_GR', 'COUNTRY_GS', 'COUNTRY_GT', 'COUNTRY_GU', 'COUNTRY_GW', 'COUNTRY_GY', 'COUNTRY_HK', 'COUNTRY_HM', 'COUNTRY_HN', 'COUNTRY_HR', 'COUNTRY_HT', 'COUNTRY_HU', 'COUNTRY_ID', 'COUNTRY_IE', 'COUNTRY_IL', 'COUNTRY_IM', 'COUNTRY_IN', 'COUNTRY_IO', 'COUNTRY_IQ', 'COUNTRY_IR', 'COUNTRY_IS', 'COUNTRY_IT', 'COUNTRY_JE', 'COUNTRY_JM', 'COUNTRY_JO', 'COUNTRY_JP', 'COUNTRY_KE', 'COUNTRY_KG', 'COUNTRY_KH', 'COUNTRY_KI', 'COUNTRY_KM', 'COUNTRY_KN', 'COUNTRY_KP', 'COUNTRY_KR', 'COUNTRY_KW', 'COUNTRY_KY', 'COUNTRY_KZ', 'COUNTRY_LA', 'COUNTRY_LB', 'COUNTRY_LC', 'COUNTRY_LI', 'COUNTRY_LK', 'COUNTRY_LR', 'COUNTRY_LS', 'COUNTRY_LT', 'COUNTRY_LU', 'COUNTRY_LV', 'COUNTRY_LY', 'COUNTRY_MA', 'COUNTRY_MC', 'COUNTRY_MD', 'COUNTRY_ME', 'COUNTRY_MF', 'COUNTRY_MG', 'COUNTRY_MH', 'COUNTRY_MK', 'COUNTRY_ML', 'COUNTRY_MM', 'COUNTRY_MN', 'COUNTRY_MO', 'COUNTRY_MP', 'COUNTRY_MQ', 'COUNTRY_MR', 'COUNTRY_MS', 'COUNTRY_MT', 'COUNTRY_MU', 'COUNTRY_MV', 'COUNTRY_MW', 'COUNTRY_MX', 'COUNTRY_MY', 'COUNTRY_MZ', 'COUNTRY_NA', 'COUNTRY_NC', 'COUNTRY_NE', 'COUNTRY_NF', 'COUNTRY_NG', 'COUNTRY_NI', 'COUNTRY_NL', 'COUNTRY_NO', 'COUNTRY_NP', 'COUNTRY_NR', 'COUNTRY_NU', 'COUNTRY_NZ', 'COUNTRY_OM', 'COUNTRY_PA', 'COUNTRY_PE', 'COUNTRY_PF', 'COUNTRY_PG', 'COUNTRY_PH', 'COUNTRY_PK', 'COUNTRY_PL', 'COUNTRY_PM', 'COUNTRY_PN', 'COUNTRY_PR', 'COUNTRY_PS', 'COUNTRY_PT', 'COUNTRY_PW', 'COUNTRY_PY', 'COUNTRY_QA', 'COUNTRY_RE', 'COUNTRY_RO', 'COUNTRY_RS', 'COUNTRY_RU', 'COUNTRY_RW', 'COUNTRY_SA', 'COUNTRY_SB', 'COUNTRY_SC', 'COUNTRY_SD', 'COUNTRY_SE', 'COUNTRY_SG', 'COUNTRY_SH', 'COUNTRY_SI', 'COUNTRY_SJ', 'COUNTRY_SK', 'COUNTRY_SL', 'COUNTRY_SM', 'COUNTRY_SN', 'COUNTRY_SO', 'COUNTRY_SR', 'COUNTRY_SS', 'COUNTRY_ST', 'COUNTRY_SV', 'COUNTRY_SX', 'COUNTRY_SY', 'COUNTRY_SZ', 'COUNTRY_TC', 'COUNTRY_TD', 'COUNTRY_TF', 'COUNTRY_TG', 'COUNTRY_TH', 'COUNTRY_TJ', 'COUNTRY_TK', 'COUNTRY_TL', 'COUNTRY_TM', 'COUNTRY_TN', 'COUNTRY_TO', 'COUNTRY_TR', 'COUNTRY_TT', 'COUNTRY_TV', 'COUNTRY_TW', 'COUNTRY_TZ', 'COUNTRY_UA', 'COUNTRY_UG', 'COUNTRY_UM', 'COUNTRY_US', 'COUNTRY_UY', 'COUNTRY_UZ', 'COUNTRY_VA', 'COUNTRY_VC', 'COUNTRY_VE', 'COUNTRY_VG', 'COUNTRY_VI', 'COUNTRY_VN', 'COUNTRY_VU', 'COUNTRY_WF', 'COUNTRY_WS', 'COUNTRY_XK', 'COUNTRY_XT', 'COUNTRY_YE', 'COUNTRY_YT', 'COUNTRY_ZA', 'COUNTRY_ZM', 'COUNTRY_ZW']]] = None
    ip_matcher: Optional[IpMatcherType] = None
    ip_prefix_list: Optional[PrefixMatchList] = None
    metadata: Optional[MessageMetaType] = None
    none: Optional[Any] = None
    origin_server_subsets_action: Optional[dict[str, Any]] = None
    re_name_list: Optional[list[str]] = None


class OriginServerSubsetRuleListType(F5XCBaseModel):
    """List of Origin Pools"""

    origin_server_subset_rules: Optional[list[OriginServerSubsetRule]] = None


class TemporaryUserBlockingType(F5XCBaseModel):
    """ Specifies configuration for temporary user blocking resulting from user..."""

    custom_page: Optional[str] = None


class PolicyBasedChallenge(F5XCBaseModel):
    """Specifies the settings for policy rule based challenge"""

    always_enable_captcha_challenge: Optional[Any] = None
    always_enable_js_challenge: Optional[Any] = None
    captcha_challenge_parameters: Optional[CaptchaChallengeType] = None
    default_captcha_challenge_parameters: Optional[Any] = None
    default_js_challenge_parameters: Optional[Any] = None
    default_mitigation_settings: Optional[Any] = None
    default_temporary_blocking_parameters: Optional[Any] = None
    js_challenge_parameters: Optional[JavascriptChallengeType] = None
    malicious_user_mitigation: Optional[ObjectRefType] = None
    no_challenge: Optional[Any] = None
    rule_list: Optional[ChallengeRuleList] = None
    temporary_user_blocking: Optional[TemporaryUserBlockingType] = None


class CookieManipulationOptionType(F5XCBaseModel):
    """Set Cookie protection attributes."""

    add_httponly: Optional[Any] = None
    add_secure: Optional[Any] = None
    disable_tampering_protection: Optional[Any] = None
    enable_tampering_protection: Optional[Any] = None
    ignore_httponly: Optional[Any] = None
    ignore_max_age: Optional[Any] = None
    ignore_samesite: Optional[Any] = None
    ignore_secure: Optional[Any] = None
    max_age_value: Optional[int] = None
    name: Optional[str] = None
    samesite_lax: Optional[Any] = None
    samesite_none: Optional[Any] = None
    samesite_strict: Optional[Any] = None


class HashPolicyType(F5XCBaseModel):
    """HashPolicyType specifies the field of the incoming request that will be..."""

    cookie: Optional[CookieForHashing] = None
    header_name: Optional[str] = None
    source_ip: Optional[bool] = None
    terminal: Optional[bool] = None


class HashPolicyListType(F5XCBaseModel):
    """List of hash policy rules"""

    hash_policy: Optional[list[HashPolicyType]] = None


class RouteTypeCustomRoute(F5XCBaseModel):
    """A custom route uses a route object created outside of this view."""

    route_ref: Optional[ObjectRefType] = None


class PortMatcherType(F5XCBaseModel):
    """Port match of the request can be a range or a specific port"""

    no_port_match: Optional[Any] = None
    port: Optional[int] = None
    port_ranges: Optional[str] = None


class RouteDirectResponse(F5XCBaseModel):
    """Send this direct response in case of route match action is direct response"""

    response_body_encoded: Optional[str] = None
    response_code: Optional[int] = None


class RouteTypeDirectResponse(F5XCBaseModel):
    """A direct response route matches on path, incoming header, incoming port..."""

    headers: Optional[list[HeaderMatcherType]] = None
    http_method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    incoming_port: Optional[PortMatcherType] = None
    path: Optional[PathMatcherType] = None
    route_direct_response: Optional[RouteDirectResponse] = None


class RouteRedirect(F5XCBaseModel):
    """route redirect parameters when match action is redirect."""

    host_redirect: Optional[str] = None
    path_redirect: Optional[str] = None
    prefix_rewrite: Optional[str] = None
    proto_redirect: Optional[str] = None
    remove_all_params: Optional[Any] = None
    replace_params: Optional[str] = None
    response_code: Optional[int] = None
    retain_all_params: Optional[Any] = None


class RouteTypeRedirect(F5XCBaseModel):
    """A redirect route matches on path, incoming header, incoming port and/or..."""

    headers: Optional[list[HeaderMatcherType]] = None
    http_method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    incoming_port: Optional[PortMatcherType] = None
    path: Optional[PathMatcherType] = None
    route_redirect: Optional[RouteRedirect] = None


class TagAttribute(F5XCBaseModel):
    """Attribute for JavaScript tag"""

    javascript_tag: Optional[Literal['JS_ATTR_ID', 'JS_ATTR_CID', 'JS_ATTR_CN', 'JS_ATTR_API_DOMAIN', 'JS_ATTR_API_URL', 'JS_ATTR_API_PATH', 'JS_ATTR_ASYNC', 'JS_ATTR_DEFER']] = None
    tag_value: Optional[str] = None


class JavaScriptTag(F5XCBaseModel):
    """JavaScript URL and attributes"""

    javascript_url: Optional[str] = None
    tag_attributes: Optional[list[TagAttribute]] = None


class BotDefenseJavascriptInjectionType(F5XCBaseModel):
    """Bot Defense Javascript Injection Configuration for inline bot defense deployments"""

    javascript_location: Optional[Literal['AFTER_HEAD', 'AFTER_TITLE_END', 'BEFORE_SCRIPT']] = None
    javascript_tags: Optional[list[JavaScriptTag]] = None


class FractionalPercent(F5XCBaseModel):
    """Fraction used where sampling percentages are needed. example sampled requests"""

    denominator: Optional[Literal['HUNDRED', 'TEN_THOUSAND', 'MILLION']] = None
    numerator: Optional[int] = None


class MirrorPolicyType(F5XCBaseModel):
    """MirrorPolicy is used for shadowing traffic from one origin pool to..."""

    origin_pool: Optional[ObjectRefType] = None
    percent: Optional[FractionalPercent] = None


class RegexMatchRewrite(F5XCBaseModel):
    """RegexMatchRewrite describes how to match a string and then produce a new..."""

    pattern: Optional[str] = None
    substitution: Optional[str] = None


class RetryBackOff(F5XCBaseModel):
    """Specifies parameters that control retry back off."""

    base_interval: Optional[int] = None
    max_interval: Optional[int] = None


class RetryPolicyType(F5XCBaseModel):
    """Retry policy configuration for route destination."""

    back_off: Optional[RetryBackOff] = None
    num_retries: Optional[int] = None
    per_try_timeout: Optional[int] = None
    retriable_status_codes: Optional[list[int]] = None
    retry_condition: Optional[list[str]] = None


class WebsocketConfigType(F5XCBaseModel):
    """Configuration to allow Websocket  Request headers of such upgrade looks..."""

    use_websocket: Optional[bool] = None


class RouteSimpleAdvancedOptions(F5XCBaseModel):
    """Configure advanced options for route like path rewrite, hash policy, etc."""

    app_firewall: Optional[ObjectRefType] = None
    bot_defense_javascript_injection: Optional[BotDefenseJavascriptInjectionType] = None
    buffer_policy: Optional[BufferConfigType] = None
    common_buffering: Optional[Any] = None
    common_hash_policy: Optional[Any] = None
    cors_policy: Optional[CorsPolicy] = None
    csrf_policy: Optional[CsrfPolicy] = None
    default_retry_policy: Optional[Any] = None
    disable_location_add: Optional[bool] = None
    disable_mirroring: Optional[Any] = None
    disable_prefix_rewrite: Optional[Any] = None
    disable_spdy: Optional[Any] = None
    disable_waf: Optional[Any] = None
    disable_web_socket_config: Optional[Any] = None
    do_not_retract_cluster: Optional[Any] = None
    enable_spdy: Optional[Any] = None
    endpoint_subsets: Optional[dict[str, Any]] = None
    inherited_bot_defense_javascript_injection: Optional[Any] = None
    inherited_waf: Optional[Any] = None
    inherited_waf_exclusion: Optional[Any] = None
    mirror_policy: Optional[MirrorPolicyType] = None
    no_retry_policy: Optional[Any] = None
    prefix_rewrite: Optional[str] = None
    priority: Optional[Literal['DEFAULT', 'HIGH']] = None
    regex_rewrite: Optional[RegexMatchRewrite] = None
    request_cookies_to_add: Optional[list[CookieValueOption]] = None
    request_cookies_to_remove: Optional[list[str]] = None
    request_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    request_headers_to_remove: Optional[list[str]] = None
    response_cookies_to_add: Optional[list[SetCookieValueOption]] = None
    response_cookies_to_remove: Optional[list[str]] = None
    response_headers_to_add: Optional[list[HeaderManipulationOptionType]] = None
    response_headers_to_remove: Optional[list[str]] = None
    retract_cluster: Optional[Any] = None
    retry_policy: Optional[RetryPolicyType] = None
    specific_hash_policy: Optional[HashPolicyListType] = None
    timeout: Optional[int] = None
    waf_exclusion_policy: Optional[ObjectRefType] = None
    web_socket_config: Optional[WebsocketConfigType] = None


class QueryParamsSimpleRoute(F5XCBaseModel):
    """Handling of incoming query parameters in simple route."""

    remove_all_params: Optional[Any] = None
    replace_params: Optional[str] = None
    retain_all_params: Optional[Any] = None


class RouteTypeSimple(F5XCBaseModel):
    """A simple route matches on path, incoming header, incoming port and/or..."""

    advanced_options: Optional[RouteSimpleAdvancedOptions] = None
    auto_host_rewrite: Optional[Any] = None
    disable_host_rewrite: Optional[Any] = None
    headers: Optional[list[HeaderMatcherType]] = None
    host_rewrite: Optional[str] = None
    http_method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    incoming_port: Optional[PortMatcherType] = None
    origin_pools: Optional[list[OriginPoolWithWeight]] = None
    path: Optional[PathMatcherType] = None
    query_params: Optional[QueryParamsSimpleRoute] = None


class RouteType(F5XCBaseModel):
    """This defines various options to define a route"""

    custom_route_object: Optional[RouteTypeCustomRoute] = None
    direct_response_route: Optional[RouteTypeDirectResponse] = None
    redirect_route: Optional[RouteTypeRedirect] = None
    simple_route: Optional[RouteTypeSimple] = None


class SensitiveDataTypes(F5XCBaseModel):
    """Settings to mask sensitive data in request/response payload"""

    api_endpoint: Optional[ApiEndpointDetails] = None
    body: Optional[BodySectionMaskingOptions] = None
    mask: Optional[Any] = None
    report: Optional[Any] = None


class SensitiveDataDisclosureRules(F5XCBaseModel):
    """Sensitive Data Exposure Rules allows specifying rules to mask sensitive..."""

    sensitive_data_types_in_response: Optional[list[SensitiveDataTypes]] = None


class SingleLoadBalancerAppSetting(F5XCBaseModel):
    """Specific settings for Machine learning analysis on this HTTP LB,..."""

    disable_discovery: Optional[Any] = None
    disable_malicious_user_detection: Optional[Any] = None
    enable_discovery: Optional[ApiDiscoverySetting] = None
    enable_malicious_user_detection: Optional[Any] = None


class SlowDDoSMitigation(F5XCBaseModel):
    """'Slow and low' attacks tie up server resources, leaving none available..."""

    disable_request_timeout: Optional[Any] = None
    request_headers_timeout: Optional[int] = None
    request_timeout: Optional[int] = None


class CreateSpecType(F5XCBaseModel):
    """Shape of the HTTP load balancer specification"""

    active_service_policies: Optional[ServicePolicyList] = None
    add_location: Optional[bool] = None
    advertise_custom: Optional[AdvertiseCustom] = None
    advertise_on_public: Optional[AdvertisePublic] = None
    advertise_on_public_default_vip: Optional[Any] = None
    api_protection_rules: Optional[APIProtectionRules] = None
    api_rate_limit: Optional[APIRateLimit] = None
    api_specification: Optional[APISpecificationSettings] = None
    api_testing: Optional[ApiTesting] = None
    app_firewall: Optional[ObjectRefType] = None
    blocked_clients: Optional[list[SimpleClientSrcRule]] = None
    bot_defense: Optional[ShapeBotDefenseType] = None
    bot_defense_advanced: Optional[BotDefenseAdvancedType] = None
    caching_policy: Optional[CachingPolicy] = None
    captcha_challenge: Optional[CaptchaChallengeType] = None
    client_side_defense: Optional[ClientSideDefenseType] = None
    cookie_stickiness: Optional[CookieForHashing] = None
    cors_policy: Optional[CorsPolicy] = None
    csrf_policy: Optional[CsrfPolicy] = None
    data_guard_rules: Optional[list[SimpleDataGuardRule]] = None
    ddos_mitigation_rules: Optional[list[DDoSMitigationRule]] = None
    default_pool: Optional[GlobalSpecType] = None
    default_pool_list: Optional[OriginPoolListType] = None
    default_route_pools: Optional[list[OriginPoolWithWeight]] = None
    default_sensitive_data_policy: Optional[Any] = None
    disable_api_definition: Optional[Any] = None
    disable_api_discovery: Optional[Any] = None
    disable_api_testing: Optional[Any] = None
    disable_bot_defense: Optional[Any] = None
    disable_caching: Optional[Any] = None
    disable_client_side_defense: Optional[Any] = None
    disable_ip_reputation: Optional[Any] = None
    disable_malicious_user_detection: Optional[Any] = None
    disable_malware_protection: Optional[Any] = None
    disable_rate_limit: Optional[Any] = None
    disable_threat_mesh: Optional[Any] = None
    disable_trust_client_ip_headers: Optional[Any] = None
    disable_waf: Optional[Any] = None
    do_not_advertise: Optional[Any] = None
    domains: Optional[list[str]] = None
    enable_api_discovery: Optional[ApiDiscoverySetting] = None
    enable_challenge: Optional[EnableChallenge] = None
    enable_ip_reputation: Optional[IPThreatCategoryListType] = None
    enable_malicious_user_detection: Optional[Any] = None
    enable_threat_mesh: Optional[Any] = None
    enable_trust_client_ip_headers: Optional[ClientIPHeaders] = None
    graphql_rules: Optional[list[GraphQLRule]] = None
    http: Optional[ProxyTypeHttp] = None
    https: Optional[ProxyTypeHttps] = None
    https_auto_cert: Optional[ProxyTypeHttpsAutoCerts] = None
    js_challenge: Optional[JavascriptChallengeType] = None
    jwt_validation: Optional[JWTValidation] = None
    l7_ddos_action_block: Optional[Any] = None
    l7_ddos_action_default: Optional[Any] = None
    l7_ddos_action_js_challenge: Optional[JavascriptChallengeType] = None
    l7_ddos_protection: Optional[L7DDoSProtectionSettings] = None
    least_active: Optional[Any] = None
    malware_protection_settings: Optional[MalwareProtectionPolicy] = None
    more_option: Optional[AdvancedOptionsType] = None
    multi_lb_app: Optional[Any] = None
    no_challenge: Optional[Any] = None
    no_service_policies: Optional[Any] = None
    origin_server_subset_rule_list: Optional[OriginServerSubsetRuleListType] = None
    policy_based_challenge: Optional[PolicyBasedChallenge] = None
    protected_cookies: Optional[list[CookieManipulationOptionType]] = None
    random: Optional[Any] = None
    rate_limit: Optional[RateLimitConfigType] = None
    ring_hash: Optional[HashPolicyListType] = None
    round_robin: Optional[Any] = None
    routes: Optional[list[RouteType]] = None
    sensitive_data_disclosure_rules: Optional[SensitiveDataDisclosureRules] = None
    sensitive_data_policy: Optional[SensitiveDataPolicySettings] = None
    service_policies_from_namespace: Optional[Any] = None
    single_lb_app: Optional[SingleLoadBalancerAppSetting] = None
    slow_ddos_mitigation: Optional[SlowDDoSMitigation] = None
    source_ip_stickiness: Optional[Any] = None
    system_default_timeouts: Optional[Any] = None
    trusted_clients: Optional[list[SimpleClientSrcRule]] = None
    user_id_client_ip: Optional[Any] = None
    user_identification: Optional[ObjectRefType] = None
    waf_exclusion: Optional[WafExclusion] = None


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


class DNSRecord(F5XCBaseModel):
    """Defines a DNS record"""

    name: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")
    value: Optional[str] = None


class AutoCertInfoType(F5XCBaseModel):
    """Information related to auto certificate"""

    auto_cert_expiry: Optional[str] = None
    auto_cert_issuer: Optional[str] = None
    auto_cert_state: Optional[Literal['AutoCertDisabled', 'DnsDomainVerification', 'AutoCertStarted', 'DomainChallengePending', 'DomainChallengeVerified', 'AutoCertFinalize', 'CertificateInvalid', 'CertificateValid', 'AutoCertNotApplicable', 'AutoCertRateLimited', 'AutoCertGenerationRetry', 'AutoCertError', 'PreDomainChallengePending', 'DomainChallengeStarted', 'AutoCertInitialize', 'AutoCertAccountRateLimited', 'AutoCertDomainRateLimited', 'CertificateExpired']] = None
    auto_cert_subject: Optional[str] = None
    dns_records: Optional[list[DNSRecord]] = None


class DnsInfo(F5XCBaseModel):
    """A message that contains DNS information for a given IP address"""

    ip_address: Optional[str] = None


class InternetVIPListenerStatusType(F5XCBaseModel):
    arn: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class InternetVIPTargetGroupStatusType(F5XCBaseModel):
    arn: Optional[str] = None
    listener_status: Optional[list[InternetVIPListenerStatusType]] = None
    name: Optional[str] = None
    protocol: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class InternetVIPStatus(F5XCBaseModel):
    """CName and installation info"""

    arn: Optional[str] = None
    name: Optional[str] = None
    nlb_cname: Optional[str] = None
    nlb_status: Optional[str] = None
    reason: Optional[str] = None
    target_group_status: Optional[list[InternetVIPTargetGroupStatusType]] = None


class InternetVIPInfo(F5XCBaseModel):
    """Internet VIP Info"""

    site_name: Optional[str] = None
    site_network_type: Optional[Literal['SITE_NETWORK_INSIDE_AND_OUTSIDE', 'SITE_NETWORK_INSIDE', 'SITE_NETWORK_OUTSIDE', 'SITE_NETWORK_SERVICE', 'SITE_NETWORK_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_INSIDE_AND_OUTSIDE_WITH_INTERNET_VIP', 'SITE_NETWORK_IP_FABRIC']] = None
    status: Optional[InternetVIPStatus] = None


class GetSpecType(F5XCBaseModel):
    """Shape of the HTTP load balancer specification"""

    active_service_policies: Optional[ServicePolicyList] = None
    add_location: Optional[bool] = None
    advertise_custom: Optional[AdvertiseCustom] = None
    advertise_on_public: Optional[AdvertisePublic] = None
    advertise_on_public_default_vip: Optional[Any] = None
    api_protection_rules: Optional[APIProtectionRules] = None
    api_rate_limit: Optional[APIRateLimit] = None
    api_specification: Optional[APISpecificationSettings] = None
    api_testing: Optional[ApiTesting] = None
    app_firewall: Optional[ObjectRefType] = None
    auto_cert_info: Optional[AutoCertInfoType] = None
    blocked_clients: Optional[list[SimpleClientSrcRule]] = None
    bot_defense: Optional[ShapeBotDefenseType] = None
    bot_defense_advanced: Optional[BotDefenseAdvancedType] = None
    caching_policy: Optional[CachingPolicy] = None
    captcha_challenge: Optional[CaptchaChallengeType] = None
    cert_state: Optional[Literal['AutoCertDisabled', 'DnsDomainVerification', 'AutoCertStarted', 'DomainChallengePending', 'DomainChallengeVerified', 'AutoCertFinalize', 'CertificateInvalid', 'CertificateValid', 'AutoCertNotApplicable', 'AutoCertRateLimited', 'AutoCertGenerationRetry', 'AutoCertError', 'PreDomainChallengePending', 'DomainChallengeStarted', 'AutoCertInitialize', 'AutoCertAccountRateLimited', 'AutoCertDomainRateLimited', 'CertificateExpired']] = None
    client_side_defense: Optional[ClientSideDefenseType] = None
    cookie_stickiness: Optional[CookieForHashing] = None
    cors_policy: Optional[CorsPolicy] = None
    csrf_policy: Optional[CsrfPolicy] = None
    data_guard_rules: Optional[list[SimpleDataGuardRule]] = None
    ddos_mitigation_rules: Optional[list[DDoSMitigationRule]] = None
    default_pool: Optional[GlobalSpecType] = None
    default_pool_list: Optional[OriginPoolListType] = None
    default_route_pools: Optional[list[OriginPoolWithWeight]] = None
    default_sensitive_data_policy: Optional[Any] = None
    disable_api_definition: Optional[Any] = None
    disable_api_discovery: Optional[Any] = None
    disable_api_testing: Optional[Any] = None
    disable_bot_defense: Optional[Any] = None
    disable_caching: Optional[Any] = None
    disable_client_side_defense: Optional[Any] = None
    disable_ip_reputation: Optional[Any] = None
    disable_malicious_user_detection: Optional[Any] = None
    disable_malware_protection: Optional[Any] = None
    disable_rate_limit: Optional[Any] = None
    disable_threat_mesh: Optional[Any] = None
    disable_trust_client_ip_headers: Optional[Any] = None
    disable_waf: Optional[Any] = None
    dns_info: Optional[list[DnsInfo]] = None
    do_not_advertise: Optional[Any] = None
    domains: Optional[list[str]] = None
    enable_api_discovery: Optional[ApiDiscoverySetting] = None
    enable_challenge: Optional[EnableChallenge] = None
    enable_ip_reputation: Optional[IPThreatCategoryListType] = None
    enable_malicious_user_detection: Optional[Any] = None
    enable_threat_mesh: Optional[Any] = None
    enable_trust_client_ip_headers: Optional[ClientIPHeaders] = None
    graphql_rules: Optional[list[GraphQLRule]] = None
    host_name: Optional[str] = None
    http: Optional[ProxyTypeHttp] = None
    https: Optional[ProxyTypeHttps] = None
    https_auto_cert: Optional[ProxyTypeHttpsAutoCerts] = None
    internet_vip_info: Optional[list[InternetVIPInfo]] = None
    js_challenge: Optional[JavascriptChallengeType] = None
    jwt_validation: Optional[JWTValidation] = None
    l7_ddos_action_block: Optional[Any] = None
    l7_ddos_action_default: Optional[Any] = None
    l7_ddos_action_js_challenge: Optional[JavascriptChallengeType] = None
    l7_ddos_protection: Optional[L7DDoSProtectionSettings] = None
    least_active: Optional[Any] = None
    malware_protection_settings: Optional[MalwareProtectionPolicy] = None
    more_option: Optional[AdvancedOptionsType] = None
    multi_lb_app: Optional[Any] = None
    no_challenge: Optional[Any] = None
    no_service_policies: Optional[Any] = None
    origin_server_subset_rule_list: Optional[OriginServerSubsetRuleListType] = None
    policy_based_challenge: Optional[PolicyBasedChallenge] = None
    protected_cookies: Optional[list[CookieManipulationOptionType]] = None
    random: Optional[Any] = None
    rate_limit: Optional[RateLimitConfigType] = None
    ring_hash: Optional[HashPolicyListType] = None
    round_robin: Optional[Any] = None
    routes: Optional[list[RouteType]] = None
    sensitive_data_disclosure_rules: Optional[SensitiveDataDisclosureRules] = None
    sensitive_data_policy: Optional[SensitiveDataPolicySettings] = None
    service_policies_from_namespace: Optional[Any] = None
    single_lb_app: Optional[SingleLoadBalancerAppSetting] = None
    slow_ddos_mitigation: Optional[SlowDDoSMitigation] = None
    source_ip_stickiness: Optional[Any] = None
    state: Optional[Literal['VIRTUAL_HOST_READY', 'VIRTUAL_HOST_PENDING_VERIFICATION', 'VIRTUAL_HOST_VERIFICATION_FAILED', 'VIRTUAL_HOST_PENDING_DNS_DELEGATION', 'VIRTUAL_HOST_PENDING_A_RECORD', 'VIRTUAL_HOST_DNS_A_RECORD_ADDED', 'VIRTUAL_HOST_INTERNET_NLB_PENDING_CREATION', 'VIRTUAL_HOST_INTERNET_NLB_CREATION_FAILED']] = None
    system_default_timeouts: Optional[Any] = None
    trusted_clients: Optional[list[SimpleClientSrcRule]] = None
    user_id_client_ip: Optional[Any] = None
    user_identification: Optional[ObjectRefType] = None
    waf_exclusion: Optional[WafExclusion] = None


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


class GetAPIEndpointsForGroupsReq(F5XCBaseModel):
    """Request shape for Get API Endpoints For Groups"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class GetAPIEndpointsForGroupsRsp(F5XCBaseModel):
    """Response shape for Get API Endpoints For Groups request"""

    api_endpoints: Optional[list[APIGroupsApiep]] = None
    apieps_timestamp: Optional[str] = None


class ApiOperation(F5XCBaseModel):
    """API operation according to OpenAPI specification."""

    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    path: Optional[str] = None


class GetAPIEndpointsSchemaUpdatesReq(F5XCBaseModel):
    """Request shape for Get API Endpoints Schema Updates"""

    api_endpoints_filter: Optional[list[ApiOperation]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    query_type: Optional[Literal['API_INVENTORY_SCHEMA_FULL_RESPONSE', 'API_INVENTORY_SCHEMA_CURRENT', 'API_INVENTORY_SCHEMA_UPDATED']] = None


class ApiEndpointWithSchema(F5XCBaseModel):
    """API endpoint and its schema"""

    api_operation: Optional[ApiOperation] = None
    schema_json_: Optional[str] = Field(default=None, alias="schema_json")


class GetAPIEndpointsSchemaUpdatesResp(F5XCBaseModel):
    """Response shape for Get API Endpoints Schema Updates"""

    api_endpoints_current_schemas: Optional[list[ApiEndpointWithSchema]] = None
    api_endpoints_updated_schemas: Optional[list[ApiEndpointWithSchema]] = None


class GlobalSpecType(F5XCBaseModel):
    """Shape of the virtual host DNS info global specification"""

    dns_info: Optional[list[DnsInfo]] = None
    host_name: Optional[str] = None
    virtual_host: Optional[list[ObjectRefType]] = None


class GetDnsInfoResponse(F5XCBaseModel):
    """Response for get-dns-info API"""

    dns_info: Optional[GlobalSpecType] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Shape of the HTTP load balancer specification"""

    active_service_policies: Optional[ServicePolicyList] = None
    add_location: Optional[bool] = None
    advertise_custom: Optional[AdvertiseCustom] = None
    advertise_on_public: Optional[AdvertisePublic] = None
    advertise_on_public_default_vip: Optional[Any] = None
    api_protection_rules: Optional[APIProtectionRules] = None
    api_rate_limit: Optional[APIRateLimit] = None
    api_specification: Optional[APISpecificationSettings] = None
    api_testing: Optional[ApiTesting] = None
    app_firewall: Optional[ObjectRefType] = None
    blocked_clients: Optional[list[SimpleClientSrcRule]] = None
    bot_defense: Optional[ShapeBotDefenseType] = None
    bot_defense_advanced: Optional[BotDefenseAdvancedType] = None
    caching_policy: Optional[CachingPolicy] = None
    captcha_challenge: Optional[CaptchaChallengeType] = None
    client_side_defense: Optional[ClientSideDefenseType] = None
    cookie_stickiness: Optional[CookieForHashing] = None
    cors_policy: Optional[CorsPolicy] = None
    csrf_policy: Optional[CsrfPolicy] = None
    data_guard_rules: Optional[list[SimpleDataGuardRule]] = None
    ddos_mitigation_rules: Optional[list[DDoSMitigationRule]] = None
    default_pool: Optional[GlobalSpecType] = None
    default_pool_list: Optional[OriginPoolListType] = None
    default_route_pools: Optional[list[OriginPoolWithWeight]] = None
    default_sensitive_data_policy: Optional[Any] = None
    disable_api_definition: Optional[Any] = None
    disable_api_discovery: Optional[Any] = None
    disable_api_testing: Optional[Any] = None
    disable_bot_defense: Optional[Any] = None
    disable_caching: Optional[Any] = None
    disable_client_side_defense: Optional[Any] = None
    disable_ip_reputation: Optional[Any] = None
    disable_malicious_user_detection: Optional[Any] = None
    disable_malware_protection: Optional[Any] = None
    disable_rate_limit: Optional[Any] = None
    disable_threat_mesh: Optional[Any] = None
    disable_trust_client_ip_headers: Optional[Any] = None
    disable_waf: Optional[Any] = None
    do_not_advertise: Optional[Any] = None
    domains: Optional[list[str]] = None
    enable_api_discovery: Optional[ApiDiscoverySetting] = None
    enable_challenge: Optional[EnableChallenge] = None
    enable_ip_reputation: Optional[IPThreatCategoryListType] = None
    enable_malicious_user_detection: Optional[Any] = None
    enable_threat_mesh: Optional[Any] = None
    enable_trust_client_ip_headers: Optional[ClientIPHeaders] = None
    graphql_rules: Optional[list[GraphQLRule]] = None
    http: Optional[ProxyTypeHttp] = None
    https: Optional[ProxyTypeHttps] = None
    https_auto_cert: Optional[ProxyTypeHttpsAutoCerts] = None
    js_challenge: Optional[JavascriptChallengeType] = None
    jwt_validation: Optional[JWTValidation] = None
    l7_ddos_action_block: Optional[Any] = None
    l7_ddos_action_default: Optional[Any] = None
    l7_ddos_action_js_challenge: Optional[JavascriptChallengeType] = None
    l7_ddos_protection: Optional[L7DDoSProtectionSettings] = None
    least_active: Optional[Any] = None
    malware_protection_settings: Optional[MalwareProtectionPolicy] = None
    more_option: Optional[AdvancedOptionsType] = None
    multi_lb_app: Optional[Any] = None
    no_challenge: Optional[Any] = None
    no_service_policies: Optional[Any] = None
    origin_server_subset_rule_list: Optional[OriginServerSubsetRuleListType] = None
    policy_based_challenge: Optional[PolicyBasedChallenge] = None
    protected_cookies: Optional[list[CookieManipulationOptionType]] = None
    random: Optional[Any] = None
    rate_limit: Optional[RateLimitConfigType] = None
    ring_hash: Optional[HashPolicyListType] = None
    round_robin: Optional[Any] = None
    routes: Optional[list[RouteType]] = None
    sensitive_data_disclosure_rules: Optional[SensitiveDataDisclosureRules] = None
    sensitive_data_policy: Optional[SensitiveDataPolicySettings] = None
    service_policies_from_namespace: Optional[Any] = None
    single_lb_app: Optional[SingleLoadBalancerAppSetting] = None
    slow_ddos_mitigation: Optional[SlowDDoSMitigation] = None
    source_ip_stickiness: Optional[Any] = None
    system_default_timeouts: Optional[Any] = None
    trusted_clients: Optional[list[SimpleClientSrcRule]] = None
    user_id_client_ip: Optional[Any] = None
    user_identification: Optional[ObjectRefType] = None
    waf_exclusion: Optional[WafExclusion] = None


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


class DNSVHostStatusType(F5XCBaseModel):
    """DNS related Virtual Host status"""

    error_description: Optional[str] = None
    existing_certificate_state: Optional[str] = None
    renew_certificate_state: Optional[Literal['AutoCertDisabled', 'DnsDomainVerification', 'AutoCertStarted', 'DomainChallengePending', 'DomainChallengeVerified', 'AutoCertFinalize', 'CertificateInvalid', 'CertificateValid', 'AutoCertNotApplicable', 'AutoCertRateLimited', 'AutoCertGenerationRetry', 'AutoCertError', 'PreDomainChallengePending', 'DomainChallengeStarted', 'AutoCertInitialize', 'AutoCertAccountRateLimited', 'AutoCertDomainRateLimited', 'CertificateExpired']] = None
    state: Optional[Literal['VIRTUAL_HOST_READY', 'VIRTUAL_HOST_PENDING_VERIFICATION', 'VIRTUAL_HOST_VERIFICATION_FAILED', 'VIRTUAL_HOST_PENDING_DNS_DELEGATION', 'VIRTUAL_HOST_PENDING_A_RECORD', 'VIRTUAL_HOST_DNS_A_RECORD_ADDED', 'VIRTUAL_HOST_INTERNET_NLB_PENDING_CREATION', 'VIRTUAL_HOST_INTERNET_NLB_CREATION_FAILED']] = None
    suggested_action: Optional[str] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of object"""

    cdn_site_status: Optional[CDNSiteStatus] = None
    cdn_status: Optional[CDNControllerStatus] = None
    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    virtual_host_status: Optional[DNSVHostStatusType] = None


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


class HTTPLoadBalancerList(F5XCBaseModel):
    http_loadbalancer: Optional[list[str]] = None


class GetSecurityConfigReq(F5XCBaseModel):
    """Request of GET Security Config Spec API"""

    all_http_loadbalancers: Optional[Any] = None
    http_loadbalancers_list: Optional[HTTPLoadBalancerList] = None
    namespace: Optional[str] = None


class ListAvailableAPIDefinitionsResp(F5XCBaseModel):
    available_api_definitions: Optional[list[ObjectRefType]] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of http_loadbalancer is returned in 'List'. By..."""

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


class SetL7DDoSRPSThresholdReq(F5XCBaseModel):
    """Request to set L7 DDoS RPS Threshold"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    rps_threshold: Optional[int] = None


class SetL7DDoSRPSThresholdRsp(F5XCBaseModel):
    """Response message for setting the RPS threshold"""

    pass


class UpdateAPIEndpointsSchemasReq(F5XCBaseModel):
    """Request shape for Update API Endpoints Schemas"""

    api_endpoints_schema_updates: Optional[list[ApiEndpointWithSchema]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class UpdateAPIEndpointsSchemasResp(F5XCBaseModel):
    """Response shape for Update API Endpoints With Newly Discovered Schema"""

    updated_api_endpoints: Optional[list[ApiOperation]] = None


# Convenience aliases
Spec = GetSpecType
Spec = OpenApiValidationAllSpecEndpointsSettings
Spec = ValidateApiBySpecRule
Spec = APISpecificationSettings
Spec = ChallengeRuleSpec
Spec = WhereVirtualSiteSpecifiedVIP
Spec = GlobalSpecType
Spec = CreateSpecType
Spec = GetSpecType
Spec = GlobalSpecType
Spec = ReplaceSpecType
