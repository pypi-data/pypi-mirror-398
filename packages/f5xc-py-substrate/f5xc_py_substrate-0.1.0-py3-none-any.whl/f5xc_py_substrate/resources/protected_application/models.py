"""Pydantic models for protected_application."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ProtectedApplicationListItem(F5XCBaseModel):
    """List item for protected_application resources."""


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class DomainType(F5XCBaseModel):
    """Domains names"""

    exact_value: Optional[str] = None
    regex_value: Optional[str] = None
    suffix_value: Optional[str] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class PathMatcherType(F5XCBaseModel):
    """Path match of the URI can be either be, Prefix match or exact match or..."""

    path: Optional[str] = None
    prefix: Optional[str] = None
    regex: Optional[str] = None


class JavaScriptExclusionRule(F5XCBaseModel):
    """Define JavaScript insertion exclusion rule"""

    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None
    metadata: Optional[MessageMetaType] = None
    path: Optional[PathMatcherType] = None


class JavaScriptInsertionRule(F5XCBaseModel):
    """This defines a rule for Bot Defense JavaScript insertion."""

    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None
    exact_path: Optional[str] = None
    glob: Optional[str] = None
    metadata: Optional[MessageMetaType] = None
    prefix: Optional[str] = None


class JavaScriptInsertType(F5XCBaseModel):
    """This defines custom JavaScript insertion rules for Bot Defense Policy."""

    exclude_list: Optional[list[JavaScriptExclusionRule]] = None
    javascript_location: Optional[Literal['JAVA_SCRIPT_LOCATION_UNDEFINED', 'AFTER_HEAD', 'AFTER_TITLE_END', 'BEFORE_SCRIPT']] = None
    js_download_path: Optional[str] = None
    rules: Optional[list[JavaScriptInsertionRule]] = None


class JavaScriptInsertManualType(F5XCBaseModel):
    """Insert JavaScript manually"""

    js_download_path: Optional[str] = None


class HeaderMatcherType(F5XCBaseModel):
    """Header match is done using the name of the header and its value. The..."""

    exact: Optional[str] = None
    name: Optional[str] = None
    regex: Optional[str] = None


class MobileTrafficIdentifierType(F5XCBaseModel):
    """Mobile traffic identifier type."""

    headers: Optional[list[HeaderMatcherType]] = None


class MobileSDKConfigType(F5XCBaseModel):
    """Mobile SDK configuration."""

    mobile_identifier: Optional[MobileTrafficIdentifierType] = None


class BlockMobileMitigationChoiceType(F5XCBaseModel):
    """Block Response."""

    body: Optional[str] = None
    content_type: Optional[str] = None
    status: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None


class ContinueMitigationChoiceType(F5XCBaseModel):
    """Continue mitigation action."""

    add_header: Optional[Any] = None
    no_header: Optional[Any] = None


class MobileClientType(F5XCBaseModel):
    """Mobile client configuration options"""

    block: Optional[BlockMobileMitigationChoiceType] = None
    continue_: Optional[ContinueMitigationChoiceType] = Field(default=None, alias="continue")


class PathType(F5XCBaseModel):
    """Uri Path"""

    caseinsensitive: Optional[bool] = None
    path: Optional[str] = None


class BlockMitigationChoiceType(F5XCBaseModel):
    """Block Response."""

    body: Optional[str] = None
    content_type: Optional[str] = None
    status: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None


class RedirectMitigationChoiceType(F5XCBaseModel):
    """Redirect."""

    location: Optional[str] = None
    status: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None


class WebClientType(F5XCBaseModel):
    """Web client configuration options"""

    block: Optional[BlockMitigationChoiceType] = None
    continue_: Optional[ContinueMitigationChoiceType] = Field(default=None, alias="continue")
    redirect: Optional[RedirectMitigationChoiceType] = None


class WebMobileClientType(F5XCBaseModel):
    """Web and Mobile client configuration options"""

    block_mobile: Optional[BlockMobileMitigationChoiceType] = None
    block_web: Optional[BlockMitigationChoiceType] = None
    continue_mobile: Optional[ContinueMitigationChoiceType] = None
    continue_web: Optional[ContinueMitigationChoiceType] = None
    redirect_web: Optional[RedirectMitigationChoiceType] = None


class ProtectedEndpointType(F5XCBaseModel):
    """Add the name and description for the protected endpoint"""

    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None
    http_methods: Optional[list[Literal['METHOD_ANY', 'METHOD_GET', 'METHOD_POST', 'METHOD_PUT', 'METHOD_PATCH', 'METHOD_DELETE', 'METHOD_GET_DOCUMENT']]] = None
    metadata: Optional[MessageMetaType] = None
    mobile_client: Optional[MobileClientType] = None
    path: Optional[PathType] = None
    query: Optional[str] = None
    web_client: Optional[WebClientType] = None
    web_mobile_client: Optional[WebMobileClientType] = None


class HttpHeaderMatcherList(F5XCBaseModel):
    """Request header name and value pairs"""

    headers: Optional[list[HeaderMatcherType]] = None


class ClientBypassRule(F5XCBaseModel):
    """Client source rule specifies the sources to be trusted"""

    http_header: Optional[HttpHeaderMatcherList] = None
    ip_prefix: Optional[str] = None
    metadata: Optional[MessageMetaType] = None


class CloudflareType(F5XCBaseModel):
    """Bot Defense policy configuration for Cloudflare"""

    continue_mitigation_action_hdr: Optional[str] = None
    disable_js_insert: Optional[Any] = None
    disable_mobile_sdk: Optional[Any] = None
    js_insertion_rules: Optional[JavaScriptInsertType] = None
    loglevel: Optional[Literal['LOG_UNDEFINED', 'LOG_ERROR', 'LOG_WARNING', 'LOG_INFO', 'LOG_DEBUG']] = None
    manual_js_insert: Optional[JavaScriptInsertManualType] = None
    mobile_sdk_config: Optional[MobileSDKConfigType] = None
    protected_endpoints: Optional[list[ProtectedEndpointType]] = None
    timeout: Optional[int] = None
    trusted_clients: Optional[list[ClientBypassRule]] = None


class DistributionIDList(F5XCBaseModel):
    """x-example: 'ABCDEFGHI0JKLM' List of CloudFront distributions"""

    ids: Optional[list[str]] = None


class DistributionTagList(F5XCBaseModel):
    """CloudFront distribution tag list"""

    tags: Optional[dict[str, Any]] = None


class JavaScriptExclusionRule(F5XCBaseModel):
    """Define JavaScript insertion exclusion rule"""

    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None
    metadata: Optional[MessageMetaType] = None
    path: Optional[PathMatcherType] = None


class JavaScriptInsertionRule(F5XCBaseModel):
    """This defines a rule for Bot Defense JavaScript insertion."""

    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None
    exact_path: Optional[str] = None
    glob: Optional[str] = None
    metadata: Optional[MessageMetaType] = None
    prefix: Optional[str] = None


class JavaScriptInsertType(F5XCBaseModel):
    """This defines custom JavaScript insertion rules for Bot Defense Policy."""

    exclude_list: Optional[list[JavaScriptExclusionRule]] = None
    javascript_location: Optional[Literal['JAVA_SCRIPT_LOCATION_UNDEFINED', 'AFTER_HEAD', 'AFTER_TITLE_END', 'BEFORE_SCRIPT']] = None
    javascript_mode: Optional[Literal['ASYNC_JS_NO_CACHING', 'ASYNC_JS_CACHING', 'SYNC_JS_NO_CACHING', 'SYNC_JS_CACHING']] = None
    js_download_path: Optional[str] = None
    rules: Optional[list[JavaScriptInsertionRule]] = None


class JavaScriptInsertManualType(F5XCBaseModel):
    """Insert JavaScript manually"""

    javascript_mode: Optional[Literal['ASYNC_JS_NO_CACHING', 'ASYNC_JS_CACHING', 'SYNC_JS_NO_CACHING', 'SYNC_JS_CACHING']] = None
    js_download_path: Optional[str] = None


class HeaderMatcherType(F5XCBaseModel):
    """Header match is done using the name of the header and its value. The..."""

    exact: Optional[str] = None
    name: Optional[str] = None
    regex: Optional[str] = None


class MobileTrafficIdentifierType(F5XCBaseModel):
    """Mobile traffic identifier type."""

    headers: Optional[list[HeaderMatcherType]] = None


class MobileSDKConfigType(F5XCBaseModel):
    """Mobile SDK configuration."""

    mobile_identifier: Optional[MobileTrafficIdentifierType] = None


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


class BlockMobileMitigationChoiceType(F5XCBaseModel):
    """Block Response."""

    body: Optional[str] = None
    content_type: Optional[str] = None
    status: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None


class ContinueMitigationChoiceType(F5XCBaseModel):
    """Continue mitigation action."""

    add_header: Optional[Any] = None
    no_header: Optional[Any] = None


class MobileClientType(F5XCBaseModel):
    """Mobile client configuration options"""

    block: Optional[BlockMobileMitigationChoiceType] = None
    continue_: Optional[ContinueMitigationChoiceType] = Field(default=None, alias="continue")


class BlockMitigationChoiceType(F5XCBaseModel):
    """Block Response."""

    body: Optional[str] = None
    content_type: Optional[str] = None
    status: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None


class RedirectMitigationChoiceType(F5XCBaseModel):
    """Redirect."""

    location: Optional[str] = None
    status: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None


class WebClientType(F5XCBaseModel):
    """Web client configuration options"""

    block: Optional[BlockMitigationChoiceType] = None
    continue_: Optional[ContinueMitigationChoiceType] = Field(default=None, alias="continue")
    redirect: Optional[RedirectMitigationChoiceType] = None


class WebMobileClientType(F5XCBaseModel):
    """Web and Mobile client configuration options"""

    block_mobile: Optional[BlockMobileMitigationChoiceType] = None
    block_web: Optional[BlockMitigationChoiceType] = None
    continue_mobile: Optional[ContinueMitigationChoiceType] = None
    continue_web: Optional[ContinueMitigationChoiceType] = None
    redirect_web: Optional[RedirectMitigationChoiceType] = None


class ProtectedEndpointType(F5XCBaseModel):
    """Add the name and description for the protected endpoint"""

    any_domain: Optional[Any] = None
    domain: Optional[DomainType] = None
    flow_label: Optional[BotDefenseFlowLabelCategoriesChoiceType] = None
    http_methods: Optional[list[Literal['METHOD_ANY', 'METHOD_GET', 'METHOD_POST', 'METHOD_PUT', 'METHOD_PATCH', 'METHOD_DELETE', 'METHOD_GET_DOCUMENT']]] = None
    metadata: Optional[MessageMetaType] = None
    mobile_client: Optional[MobileClientType] = None
    path: Optional[str] = None
    query: Optional[str] = None
    undefined_flow_label: Optional[Any] = None
    web_client: Optional[WebClientType] = None
    web_mobile_client: Optional[WebMobileClientType] = None


class HttpHeaderMatcherList(F5XCBaseModel):
    """Request header name and value pairs"""

    headers: Optional[list[HeaderMatcherType]] = None


class ClientBypassRule(F5XCBaseModel):
    """Client source rule specifies the sources to be trusted"""

    http_header: Optional[HttpHeaderMatcherList] = None
    ip_prefix: Optional[str] = None
    metadata: Optional[MessageMetaType] = None


class CloudfrontType(F5XCBaseModel):
    """Bot Defense policy configuration for AWS Cloudfront"""

    aws_configuration_id_selector: Optional[DistributionIDList] = None
    aws_configuration_tag_selector: Optional[DistributionTagList] = None
    continue_mitigation_action_hdr: Optional[str] = None
    data_sample: Optional[int] = None
    disable_aws_configuration: Optional[Any] = None
    disable_js_insert: Optional[Any] = None
    disable_mobile_sdk: Optional[Any] = None
    js_insertion_rules: Optional[JavaScriptInsertType] = None
    loglevel: Optional[Literal['LOG_UNDEFINED', 'LOG_ERROR', 'LOG_WARNING', 'LOG_INFO', 'LOG_DEBUG']] = None
    manual_js_insert: Optional[JavaScriptInsertManualType] = None
    mobile_sdk_config: Optional[MobileSDKConfigType] = None
    protected_endpoints: Optional[list[ProtectedEndpointType]] = None
    timeout: Optional[int] = None
    trusted_clients: Optional[list[ClientBypassRule]] = None


class CreateSpecType(F5XCBaseModel):
    """Create applications protected by Bot Defense"""

    adobe_commerce_connector: Optional[Any] = None
    big_ip_iapp: Optional[Any] = None
    cloudflare: Optional[CloudflareType] = None
    cloudfront: Optional[CloudfrontType] = None
    custom_connector: Optional[Any] = None
    f5_big_ip: Optional[Any] = None
    region: Optional[Literal['US', 'EU', 'ASIA', 'CA']] = None
    salesforce_commerce_connector: Optional[Any] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class XCMeshConnector(F5XCBaseModel):
    """Configures HTTP Load Balancer connector"""

    http_load_balancer: Optional[ObjectRefType] = None


class GetSpecType(F5XCBaseModel):
    """Get applications protected by Bot Defense"""

    adobe_commerce_connector: Optional[Any] = None
    app_id: Optional[str] = None
    big_ip_iapp: Optional[Any] = None
    cloudflare: Optional[CloudflareType] = None
    cloudfront: Optional[CloudfrontType] = None
    custom_connector: Optional[Any] = None
    f5_big_ip: Optional[Any] = None
    not_applicable_connector: Optional[Any] = None
    region: Optional[Literal['US', 'EU', 'ASIA', 'CA']] = None
    reload_header_name: Optional[str] = None
    salesforce_commerce_connector: Optional[Any] = None
    status: Optional[str] = None
    xc_mesh: Optional[XCMeshConnector] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace applications protected by Bot Defense"""

    adobe_commerce_connector: Optional[Any] = None
    big_ip_iapp: Optional[Any] = None
    cloudflare: Optional[CloudflareType] = None
    cloudfront: Optional[CloudfrontType] = None
    custom_connector: Optional[Any] = None
    f5_big_ip: Optional[Any] = None
    not_applicable_connector: Optional[Any] = None
    salesforce_commerce_connector: Optional[Any] = None
    xc_mesh: Optional[XCMeshConnector] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ApiEndpoint(F5XCBaseModel):
    telemetry_prefix: Optional[str] = None
    url: Optional[str] = None


class ApiKeyResponse(F5XCBaseModel):
    """Response for getting API key"""

    api_key: Optional[str] = None


class ConnectorConfigResponse(F5XCBaseModel):
    """Connector configuration response."""

    config: Optional[str] = None
    name: Optional[str] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


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
    """By default a summary of protected_application is returned in 'List'. By..."""

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


class Region(F5XCBaseModel):
    """Region for protected application"""

    mobile_endpoint: Optional[ApiEndpoint] = None
    region: Optional[Literal['US', 'EU', 'ASIA', 'CA']] = None
    web_endpoint: Optional[ApiEndpoint] = None


class RegionsListResponse(F5XCBaseModel):
    """Response for getting regions list"""

    regions: Optional[list[Region]] = None


class ReplaceResponse(F5XCBaseModel):
    pass


class TemplateConnectorResponse(F5XCBaseModel):
    """Response for iApp template connector"""

    name: Optional[str] = None
    template: Optional[str] = None


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
