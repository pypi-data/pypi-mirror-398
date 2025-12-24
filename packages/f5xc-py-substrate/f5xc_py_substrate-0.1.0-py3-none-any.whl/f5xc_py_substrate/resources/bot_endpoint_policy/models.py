"""Pydantic models for bot_endpoint_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class BotEndpointPolicyListItem(F5XCBaseModel):
    """List item for bot_endpoint_policy resources."""


class GenericEmptyType(F5XCBaseModel):
    """This can be used for the choice where no values are needed"""

    pass


class CookieMatcherValue(F5XCBaseModel):
    """Cookie Matcher Value"""

    case_sensitive: Optional[bool] = None
    not_value: Optional[bool] = None
    value: Optional[str] = None


class CookieMatcherType(F5XCBaseModel):
    contains: Optional[CookieMatcherValue] = None
    ends_with: Optional[CookieMatcherValue] = None
    equals: Optional[CookieMatcherValue] = None
    starts_with: Optional[CookieMatcherValue] = None


class CookieMatcher(F5XCBaseModel):
    """Cookie matcher Choice."""

    cookie_match: Optional[list[CookieMatcherType]] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class Cookie(F5XCBaseModel):
    cookie_all: Optional[Any] = None
    cookie_and: Optional[CookieMatcher] = None
    cookie_none: Optional[CookieMatcher] = None
    cookie_or: Optional[CookieMatcher] = None
    name: Optional[str] = None
    not_present_cookie: Optional[Any] = None


class DomainMatcherType(F5XCBaseModel):
    """Matcher"""

    negation: Optional[Literal['NO', 'YES']] = None
    operator: Optional[Literal['EXACT', 'CONTAIN', 'START_WITH', 'END_WITH']] = None
    value: Optional[str] = None


class DomainMatcher(F5XCBaseModel):
    """Domain matcher Choice."""

    domain_match: Optional[list[DomainMatcherType]] = None


class DomainOperator(F5XCBaseModel):
    """Domain Operators"""

    all_domain: Optional[Any] = None
    domain_and: Optional[DomainMatcher] = None
    domain_none: Optional[DomainMatcher] = None
    domain_or: Optional[DomainMatcher] = None


class MatcherValue(F5XCBaseModel):
    """atcher Value"""

    case_insensitive: Optional[bool] = None
    not_: Optional[bool] = Field(default=None, alias="not")
    value: Optional[str] = None


class MatcherType(F5XCBaseModel):
    """Matcher"""

    contain_value: Optional[MatcherValue] = None
    end_with_value: Optional[MatcherValue] = None
    exact_value: Optional[MatcherValue] = None
    start_with_value: Optional[MatcherValue] = None


class HeaderMatcher(F5XCBaseModel):
    """A list of Header Matcher"""

    header_match: Optional[list[MatcherType]] = None


class HeaderNameValuePair(F5XCBaseModel):
    header_name: Optional[str] = None
    header_value: Optional[str] = None


class HeaderOperatorEmptyType(F5XCBaseModel):
    """This can be used for the header operator choice where no values are needed"""

    pass


class HeaderOperator(F5XCBaseModel):
    """Header Operators"""

    all_header: Optional[Any] = None
    header_and: Optional[HeaderMatcher] = None
    header_none: Optional[HeaderMatcher] = None
    header_or: Optional[HeaderMatcher] = None
    name: Optional[str] = None
    not_present_header: Optional[Any] = None


class PathMatcherValue(F5XCBaseModel):
    """Path Matcher Value"""

    case_insensitive: Optional[bool] = None
    not_: Optional[bool] = Field(default=None, alias="not")
    value: Optional[str] = None


class PathMatcherType(F5XCBaseModel):
    """Matcher"""

    contain_value: Optional[PathMatcherValue] = None
    end_with_value: Optional[PathMatcherValue] = None
    exact_value: Optional[PathMatcherValue] = None
    start_with_value: Optional[PathMatcherValue] = None


class PathMatcher(F5XCBaseModel):
    """A list of Path Matcher"""

    path_match: Optional[list[PathMatcherType]] = None


class PathOperator(F5XCBaseModel):
    """Path Operators"""

    all_path: Optional[Any] = None
    path_and: Optional[PathMatcher] = None
    path_none: Optional[PathMatcher] = None
    path_or: Optional[PathMatcher] = None


class PolicyVersion(F5XCBaseModel):
    """Policy version"""

    bot_infras_name: Optional[list[str]] = None
    update_time: Optional[str] = None
    update_user: Optional[str] = None
    version_number: Optional[str] = None
    version_status: Optional[str] = None


class WebClientBlockMitigationActionType(F5XCBaseModel):
    """Web Client Block request and respond with custom content."""

    body: Optional[str] = None
    name_value_pair: Optional[list[HeaderNameValuePair]] = None
    status: Optional[Literal['EmptyStatusCode', 'Continue', 'SwitchingProtocols', 'Processing', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'TeaPot', 'EnhanceYourCalm', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'ReservedforWebDAV', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'NoResponse', 'RetryWith', 'Blockedby', 'UnavailableForLegalReasons', 'ClientClosedRequest', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'BandwidthLimitExceeded', 'NotExtended', 'NetworkAuthenticationRequired', 'NetworkReadRimeoutError', 'NetworkConnectTimeoutError']] = None


class WebClientContinueMitigationHeader(F5XCBaseModel):
    """Append flag mitigation headers to forwarded request."""

    auto_type_header_name: Optional[str] = None


class WebClientContinueMitigationActionType(F5XCBaseModel):
    """Continue mitigation action."""

    append_headers: Optional[WebClientContinueMitigationHeader] = None
    no_headers: Optional[Any] = None


class BotPolicyFlowLabelAccountManagementChoiceType(F5XCBaseModel):
    """Flow Label Account Management Category"""

    change_password: Optional[Any] = None
    check_eligibility: Optional[Any] = None
    create: Optional[Any] = None
    exists: Optional[Any] = None
    password_forgot: Optional[Any] = None
    password_recover: Optional[Any] = None
    password_reset: Optional[Any] = None


class BotPolicyFlowLabelAuthenticationChoiceType(F5XCBaseModel):
    """Flow Label Authentication Category"""

    login: Optional[Any] = None
    login_alexa: Optional[Any] = None
    login_mfa: Optional[Any] = None
    login_partner: Optional[Any] = None
    logout: Optional[Any] = None
    token_refresh: Optional[Any] = None
    token_validate: Optional[Any] = None
    zelle_retrieve_token: Optional[Any] = None


class BotPolicyFlowLabelCreditCardChoiceType(F5XCBaseModel):
    """Flow Label Credit Card Category"""

    activate: Optional[Any] = None
    apply: Optional[Any] = None
    apply_to_account: Optional[Any] = None
    view_history: Optional[Any] = None
    view_list: Optional[Any] = None


class BotPolicyFlowLabelDeliveryServicesChoiceType(F5XCBaseModel):
    """Flow Label Delivery Services Category"""

    hold: Optional[Any] = None
    incorrectly_routed: Optional[Any] = None
    view_items: Optional[Any] = None


class BotPolicyFlowLabelFinancialServicesChoiceType(F5XCBaseModel):
    """Flow Label Financial Services Category"""

    account_apply: Optional[Any] = None
    loan_personal_apply: Optional[Any] = None
    money_send: Optional[Any] = None
    money_transfer: Optional[Any] = None
    ofx: Optional[Any] = None
    request_credit_score: Optional[Any] = None
    student_apply: Optional[Any] = None
    zelle_execute_transaction: Optional[Any] = None


class BotPolicyFlowLabelFlightChoiceType(F5XCBaseModel):
    """Flow Label Flight Category"""

    change_flight: Optional[Any] = None
    checkin: Optional[Any] = None
    flight_status: Optional[Any] = None
    submit_travel_documents: Optional[Any] = None
    time_table: Optional[Any] = None
    view_flight: Optional[Any] = None


class BotPolicyFlowLabelGuestSessionChoiceType(F5XCBaseModel):
    """Flow Label Guest Session Category"""

    create: Optional[Any] = None


class BotPolicyFlowLabelLoyaltyChoiceType(F5XCBaseModel):
    """Flow Label Loyalty Category"""

    conversion: Optional[Any] = None
    reset_miles: Optional[Any] = None
    view_account: Optional[Any] = None


class BotPolicyFlowLabelMailingListChoiceType(F5XCBaseModel):
    """Flow Label Mailing List Category"""

    create_password: Optional[Any] = None
    signup: Optional[Any] = None
    unsubscribe: Optional[Any] = None


class BotPolicyFlowLabelMediaChoiceType(F5XCBaseModel):
    """Flow Label Media Category"""

    content: Optional[Any] = None
    play: Optional[Any] = None
    record: Optional[Any] = None


class BotPolicyFlowLabelMiscellaneousChoiceType(F5XCBaseModel):
    """Flow Label Miscellaneous Category"""

    contact_us: Optional[Any] = None
    ratings: Optional[Any] = None


class BotPolicyFlowLabelProfileManagementChoiceType(F5XCBaseModel):
    """Flow Label Profile Management Category"""

    create: Optional[Any] = None
    update: Optional[Any] = None
    view: Optional[Any] = None


class BotPolicyFlowLabelQuotesChoiceType(F5XCBaseModel):
    """Flow Label Quotes Category"""

    insurance_fire_request: Optional[Any] = None
    request: Optional[Any] = None


class BotPolicyFlowLabelSearchChoiceType(F5XCBaseModel):
    """Flow Label Search Category"""

    fare_search: Optional[Any] = None
    find_user: Optional[Any] = None
    flight_search: Optional[Any] = None
    location_search: Optional[Any] = None
    product_search: Optional[Any] = None
    room_search: Optional[Any] = None
    shipment_search: Optional[Any] = None
    ticket_search: Optional[Any] = None


class BotPolicyFlowLabelShoppingGiftCardsChoiceType(F5XCBaseModel):
    """Flow Label Shopping & Gift Cards Category"""

    gift_card_check_balance: Optional[Any] = None
    gift_card_make_purches_with_card: Optional[Any] = None
    gift_card_purchase_card: Optional[Any] = None
    shop_add_to_cart: Optional[Any] = None
    shop_apply_gift_card: Optional[Any] = None
    shop_apply_promo_code: Optional[Any] = None
    shop_checkout: Optional[Any] = None
    shop_choose_seat: Optional[Any] = None
    shop_enter_drawing_submission: Optional[Any] = None
    shop_hold_inventory: Optional[Any] = None
    shop_make_payment: Optional[Any] = None
    shop_offer: Optional[Any] = None
    shop_order: Optional[Any] = None
    shop_price_inquiry: Optional[Any] = None
    shop_purchase_gift_card: Optional[Any] = None
    shop_return: Optional[Any] = None
    shop_schedule_pickup: Optional[Any] = None
    shop_track_order: Optional[Any] = None
    shop_update_quantity: Optional[Any] = None


class BotPolicyFlowLabelSocialsChoiceType(F5XCBaseModel):
    """Flow Label Socials Category"""

    follow: Optional[Any] = None
    like: Optional[Any] = None
    message: Optional[Any] = None


class BotPolicyFlowLabelCategoriesChoiceType(F5XCBaseModel):
    """Bot Endpoint Policy Flow Label Category allows to associate traffic with..."""

    account_management: Optional[BotPolicyFlowLabelAccountManagementChoiceType] = None
    authentication: Optional[BotPolicyFlowLabelAuthenticationChoiceType] = None
    credit_card: Optional[BotPolicyFlowLabelCreditCardChoiceType] = None
    delivery_services: Optional[BotPolicyFlowLabelDeliveryServicesChoiceType] = None
    financial_services: Optional[BotPolicyFlowLabelFinancialServicesChoiceType] = None
    flight: Optional[BotPolicyFlowLabelFlightChoiceType] = None
    guest_session: Optional[BotPolicyFlowLabelGuestSessionChoiceType] = None
    loyalty: Optional[BotPolicyFlowLabelLoyaltyChoiceType] = None
    mailing_list: Optional[BotPolicyFlowLabelMailingListChoiceType] = None
    media: Optional[BotPolicyFlowLabelMediaChoiceType] = None
    miscellaneous: Optional[BotPolicyFlowLabelMiscellaneousChoiceType] = None
    profile_management: Optional[BotPolicyFlowLabelProfileManagementChoiceType] = None
    quotes: Optional[BotPolicyFlowLabelQuotesChoiceType] = None
    search: Optional[BotPolicyFlowLabelSearchChoiceType] = None
    shopping_gift_cards: Optional[BotPolicyFlowLabelShoppingGiftCardsChoiceType] = None
    socials: Optional[BotPolicyFlowLabelSocialsChoiceType] = None
    undefined_flow_label: Optional[Any] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


class QueryMatcher(F5XCBaseModel):
    """A list of Query  Matcher"""

    query_match: Optional[list[MatcherType]] = None


class QueryOperator(F5XCBaseModel):
    """Query Operators"""

    all_query: Optional[Any] = None
    query_and: Optional[QueryMatcher] = None
    query_none: Optional[QueryMatcher] = None
    query_or: Optional[QueryMatcher] = None


class RequestBodyMatcher(F5XCBaseModel):
    """A list of RequestBody Matcher"""

    request_body_match: Optional[list[MatcherType]] = None


class RequestBodyOperator(F5XCBaseModel):
    """RequestBody Operators"""

    all_request_body: Optional[Any] = None
    request_body_and: Optional[RequestBodyMatcher] = None
    request_body_none: Optional[RequestBodyMatcher] = None
    request_body_or: Optional[RequestBodyMatcher] = None


class ResponseBodyMatcherValue(F5XCBaseModel):
    case_sensitive: Optional[bool] = None
    not_value: Optional[bool] = None
    value: Optional[str] = None


class ResponseBodyMatcherType(F5XCBaseModel):
    contains: Optional[ResponseBodyMatcherValue] = None
    ends_with: Optional[ResponseBodyMatcherValue] = None
    equals: Optional[ResponseBodyMatcherValue] = None
    starts_with: Optional[ResponseBodyMatcherValue] = None


class ResponseBodyMatcher(F5XCBaseModel):
    """Response Body matcher Choice."""

    response_body_match: Optional[list[ResponseBodyMatcherType]] = Field(default=None, alias="responseBody_match")


class ResponseBody(F5XCBaseModel):
    response_body_all: Optional[Any] = Field(default=None, alias="responseBody_all")
    response_body_and: Optional[ResponseBodyMatcher] = Field(default=None, alias="responseBody_and")
    response_body_none: Optional[ResponseBodyMatcher] = Field(default=None, alias="responseBody_none")
    response_body_or: Optional[ResponseBodyMatcher] = Field(default=None, alias="responseBody_or")


class ResponseCodeMatcherType(F5XCBaseModel):
    operator: Optional[Literal['CODE_EQUALS', 'CODE_NOT_EQUAL_TO', 'CODE_LESS_THAN', 'CODE_GREATER_THAN', 'CODE_LESS_THAN_OR_EQUAlS_TO', 'CODE_GREATER_THAN_OR_EQUAlS_TO']] = None
    value: Optional[int] = None


class ResponseCodeMatcher(F5XCBaseModel):
    response_code_match: Optional[list[ResponseCodeMatcherType]] = Field(default=None, alias="responseCode_match")


class ResponseCode(F5XCBaseModel):
    response_code_all: Optional[Any] = Field(default=None, alias="responseCode_all")
    response_code_and: Optional[ResponseCodeMatcher] = Field(default=None, alias="responseCode_and")
    response_code_none: Optional[ResponseCodeMatcher] = Field(default=None, alias="responseCode_none")
    response_code_or: Optional[ResponseCodeMatcher] = Field(default=None, alias="responseCode_or")


class ResponseHeaderMatcherValue(F5XCBaseModel):
    case_sensitive: Optional[bool] = None
    not_value: Optional[bool] = None
    value: Optional[str] = None


class ResponseHeaderMatcherType(F5XCBaseModel):
    contains: Optional[ResponseHeaderMatcherValue] = None
    ends_with: Optional[ResponseHeaderMatcherValue] = None
    equals: Optional[ResponseHeaderMatcherValue] = None
    starts_with: Optional[ResponseHeaderMatcherValue] = None


class ResponseHeaderMatcher(F5XCBaseModel):
    """Response Header matcher Choice."""

    response_header_match: Optional[list[ResponseHeaderMatcherType]] = Field(default=None, alias="responseHeader_match")


class ResponseHeader(F5XCBaseModel):
    """Response Header values"""

    header_all: Optional[Any] = None
    header_and: Optional[ResponseHeaderMatcher] = None
    header_none: Optional[ResponseHeaderMatcher] = None
    header_or: Optional[ResponseHeaderMatcher] = None
    name: Optional[str] = None
    not_present_header: Optional[Any] = None


class TransactionResultType(F5XCBaseModel):
    """Transaction Result Type"""

    cookie: Optional[list[Cookie]] = None
    response_body: Optional[ResponseBody] = Field(default=None, alias="responseBody")
    response_code: Optional[ResponseCode] = Field(default=None, alias="responseCode")
    response_header: Optional[list[ResponseHeader]] = Field(default=None, alias="responseHeader")


class TransactionResult(F5XCBaseModel):
    """Transaction Result"""

    transaction_result_failure: Optional[TransactionResultType] = None
    transaction_result_success: Optional[TransactionResultType] = None


class WebClientAddHeaderToRequest(F5XCBaseModel):
    """Add a header name value pair"""

    name_value_pair: Optional[list[HeaderNameValuePair]] = None


class WebClientTransformMitigationActionChoiceType(F5XCBaseModel):
    """Transform mitigation action."""

    add_headers: Optional[WebClientAddHeaderToRequest] = None
    no_headers: Optional[Any] = None


class UserNameType(F5XCBaseModel):
    username_reporting: Optional[str] = None


class ProtectedMobileEndpoint(F5XCBaseModel):
    """Protected Application Endpoint."""

    block: Optional[WebClientBlockMitigationActionType] = None
    continue_: Optional[WebClientContinueMitigationActionType] = Field(default=None, alias="continue")
    domain: Optional[DomainOperator] = None
    flow_label_choice: Optional[BotPolicyFlowLabelCategoriesChoiceType] = None
    header: Optional[list[HeaderOperator]] = None
    http_methods: Optional[list[Literal['BP_METHOD_GET', 'BP_METHOD_POST', 'BP_METHOD_PUT', 'BP_METHOD_PATCH', 'BP_METHOD_DELETE', 'BP_METHOD_GET_DOCUMENT', 'BP_METHOD_HEAD', 'BP_METHOD_OPTIONS', 'BP_METHOD_TRACE']]] = None
    metadata: Optional[MessageMetaType] = None
    path: Optional[PathOperator] = None
    query: Optional[QueryOperator] = None
    request_body: Optional[RequestBodyOperator] = None
    transaction_result_criteria: Optional[TransactionResult] = None
    transform: Optional[WebClientTransformMitigationActionChoiceType] = None
    usernames: Optional[list[UserNameType]] = None


class ProtectedMobileEndpointList(F5XCBaseModel):
    """Protected Mobile Endpoints List"""

    protected_mobile_endpoints: Optional[list[ProtectedMobileEndpoint]] = None


class WebClientRedirectMitigationActionType(F5XCBaseModel):
    """Web Client Redirect request to a custom URI."""

    status: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None
    uri: Optional[str] = None


class ProtectedWebEndpoint(F5XCBaseModel):
    """Protected Application Endpoint."""

    block: Optional[WebClientBlockMitigationActionType] = None
    continue_: Optional[WebClientContinueMitigationActionType] = Field(default=None, alias="continue")
    domain: Optional[DomainOperator] = None
    flow_label_choice: Optional[BotPolicyFlowLabelCategoriesChoiceType] = None
    header: Optional[list[HeaderOperator]] = None
    http_methods: Optional[list[Literal['BP_METHOD_GET', 'BP_METHOD_POST', 'BP_METHOD_PUT', 'BP_METHOD_PATCH', 'BP_METHOD_DELETE', 'BP_METHOD_GET_DOCUMENT', 'BP_METHOD_HEAD', 'BP_METHOD_OPTIONS', 'BP_METHOD_TRACE']]] = None
    metadata: Optional[MessageMetaType] = None
    path: Optional[PathOperator] = None
    query: Optional[QueryOperator] = None
    redirect: Optional[WebClientRedirectMitigationActionType] = None
    request_body: Optional[RequestBodyOperator] = None
    transaction_result_criteria: Optional[TransactionResult] = None
    transform: Optional[WebClientTransformMitigationActionChoiceType] = None
    usernames: Optional[list[UserNameType]] = None


class ProtectedWebEndpointList(F5XCBaseModel):
    """Protected Web Endpoints List"""

    protected_web_endpoints: Optional[list[ProtectedWebEndpoint]] = None


class ProtectedEndpoints(F5XCBaseModel):
    """Configures Endpoint Policy Content"""

    js_download_path: Optional[str] = None
    protected_mobile_endpoints: Optional[ProtectedMobileEndpointList] = None
    protected_web_endpoints: Optional[ProtectedWebEndpointList] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace Bot Endpoint Policy"""

    endpoint_policy_content: Optional[ProtectedEndpoints] = None


class CustomReplaceRequest(F5XCBaseModel):
    name: Optional[str] = None
    namespace: Optional[str] = None
    spec: Optional[ReplaceSpecType] = None


class CustomReplaceResponse(F5XCBaseModel):
    pass


class GetContentResponse(F5XCBaseModel):
    endpoint_policy_content: Optional[ProtectedEndpoints] = None


class Policy(F5XCBaseModel):
    """Policy name and versions"""

    policy_name: Optional[str] = None
    policy_versions: Optional[list[PolicyVersion]] = None


class GetPoliciesAndVersionsListResponse(F5XCBaseModel):
    """List All Bot Policies And Versions Response"""

    policies: Optional[list[Policy]] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


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


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class GetSpecType(F5XCBaseModel):
    """Get Bot Endpoint Policy"""

    endpoint_policy_content: Optional[ProtectedEndpoints] = None
    latest_version: Optional[str] = None


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


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

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
    """By default a summary of bot_endpoint_policy is returned in 'List'. By..."""

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


class PolicyVersionsResponse(F5XCBaseModel):
    """Policy versions response"""

    policy_versions: Optional[list[PolicyVersion]] = None


class ReplaceResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = ReplaceSpecType
Spec = GetSpecType
