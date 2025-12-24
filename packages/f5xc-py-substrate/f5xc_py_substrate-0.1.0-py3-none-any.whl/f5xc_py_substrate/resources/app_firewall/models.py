"""Pydantic models for app_firewall."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AppFirewallListItem(F5XCBaseModel):
    """List item for app_firewall resources."""


class AiRiskBasedBlocking(F5XCBaseModel):
    """All Attack Types, including high, medium, and low accuracy signatures,..."""

    high_risk_action: Optional[Literal['AI_BLOCK', 'AI_REPORT']] = None
    low_risk_action: Optional[Literal['AI_BLOCK', 'AI_REPORT']] = None
    medium_risk_action: Optional[Literal['AI_BLOCK', 'AI_REPORT']] = None


class AllowedResponseCodes(F5XCBaseModel):
    """List of HTTP response status codes that are allowed"""

    response_code: Optional[list[int]] = None


class AnonymizeHttpCookie(F5XCBaseModel):
    """Configure anonymization for HTTP Cookies"""

    cookie_name: Optional[str] = None


class AnonymizeHttpHeader(F5XCBaseModel):
    """Configure anonymization for HTTP Headers"""

    header_name: Optional[str] = None


class AnonymizeHttpQueryParameter(F5XCBaseModel):
    """Configure anonymization for HTTP Parameters"""

    query_param_name: Optional[str] = None


class AnonymizationConfiguration(F5XCBaseModel):
    """Configure anonymization for HTTP headers, parameters or cookies which..."""

    cookie: Optional[AnonymizeHttpCookie] = None
    http_header: Optional[AnonymizeHttpHeader] = None
    query_parameter: Optional[AnonymizeHttpQueryParameter] = None


class AnonymizationSetting(F5XCBaseModel):
    """Anonymization settings which is a list of HTTP headers, parameters and cookies"""

    anonymization_config: Optional[list[AnonymizationConfiguration]] = None


class AttackTypeSettings(F5XCBaseModel):
    """Specifies attack-type settings to be used by WAF"""

    disabled_attack_types: Optional[list[Literal['ATTACK_TYPE_NONE', 'ATTACK_TYPE_NON_BROWSER_CLIENT', 'ATTACK_TYPE_OTHER_APPLICATION_ATTACKS', 'ATTACK_TYPE_TROJAN_BACKDOOR_SPYWARE', 'ATTACK_TYPE_DETECTION_EVASION', 'ATTACK_TYPE_VULNERABILITY_SCAN', 'ATTACK_TYPE_ABUSE_OF_FUNCTIONALITY', 'ATTACK_TYPE_AUTHENTICATION_AUTHORIZATION_ATTACKS', 'ATTACK_TYPE_BUFFER_OVERFLOW', 'ATTACK_TYPE_PREDICTABLE_RESOURCE_LOCATION', 'ATTACK_TYPE_INFORMATION_LEAKAGE', 'ATTACK_TYPE_DIRECTORY_INDEXING', 'ATTACK_TYPE_PATH_TRAVERSAL', 'ATTACK_TYPE_XPATH_INJECTION', 'ATTACK_TYPE_LDAP_INJECTION', 'ATTACK_TYPE_SERVER_SIDE_CODE_INJECTION', 'ATTACK_TYPE_COMMAND_EXECUTION', 'ATTACK_TYPE_SQL_INJECTION', 'ATTACK_TYPE_CROSS_SITE_SCRIPTING', 'ATTACK_TYPE_DENIAL_OF_SERVICE', 'ATTACK_TYPE_HTTP_PARSER_ATTACK', 'ATTACK_TYPE_SESSION_HIJACKING', 'ATTACK_TYPE_HTTP_RESPONSE_SPLITTING', 'ATTACK_TYPE_FORCEFUL_BROWSING', 'ATTACK_TYPE_REMOTE_FILE_INCLUDE', 'ATTACK_TYPE_MALICIOUS_FILE_UPLOAD', 'ATTACK_TYPE_GRAPHQL_PARSER_ATTACK']]] = None


class BotProtectionSetting(F5XCBaseModel):
    """Configuration of WAF Bot Protection"""

    good_bot_action: Optional[Literal['BLOCK', 'REPORT', 'IGNORE']] = None
    malicious_bot_action: Optional[Literal['BLOCK', 'REPORT', 'IGNORE']] = None
    suspicious_bot_action: Optional[Literal['BLOCK', 'REPORT', 'IGNORE']] = None


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


class CustomBlockingPage(F5XCBaseModel):
    """Custom blocking response page body"""

    blocking_page: Optional[str] = None
    response_code: Optional[Literal['EmptyStatusCode', 'Continue', 'OK', 'Created', 'Accepted', 'NonAuthoritativeInformation', 'NoContent', 'ResetContent', 'PartialContent', 'MultiStatus', 'AlreadyReported', 'IMUsed', 'MultipleChoices', 'MovedPermanently', 'Found', 'SeeOther', 'NotModified', 'UseProxy', 'TemporaryRedirect', 'PermanentRedirect', 'BadRequest', 'Unauthorized', 'PaymentRequired', 'Forbidden', 'NotFound', 'MethodNotAllowed', 'NotAcceptable', 'ProxyAuthenticationRequired', 'RequestTimeout', 'Conflict', 'Gone', 'LengthRequired', 'PreconditionFailed', 'PayloadTooLarge', 'URITooLong', 'UnsupportedMediaType', 'RangeNotSatisfiable', 'ExpectationFailed', 'MisdirectedRequest', 'UnprocessableEntity', 'Locked', 'FailedDependency', 'UpgradeRequired', 'PreconditionRequired', 'TooManyRequests', 'RequestHeaderFieldsTooLarge', 'InternalServerError', 'NotImplemented', 'BadGateway', 'ServiceUnavailable', 'GatewayTimeout', 'HTTPVersionNotSupported', 'VariantAlsoNegotiates', 'InsufficientStorage', 'LoopDetected', 'NotExtended', 'NetworkAuthenticationRequired']] = None


class SignatureSelectionSetting(F5XCBaseModel):
    """Attack Signatures are patterns that identify attacks on a web..."""

    attack_type_settings: Optional[AttackTypeSettings] = None
    default_attack_type_settings: Optional[Any] = None
    high_medium_accuracy_signatures: Optional[Any] = None
    high_medium_low_accuracy_signatures: Optional[Any] = None
    only_high_accuracy_signatures: Optional[Any] = None


class SignaturesStagingSettings(F5XCBaseModel):
    """Attack Signatures staging configuration."""

    staging_period: Optional[int] = None


class ViolationSettings(F5XCBaseModel):
    """Specifies violation settings to be used by WAF"""

    disabled_violation_types: Optional[list[Literal['VIOL_NONE', 'VIOL_FILETYPE', 'VIOL_METHOD', 'VIOL_MANDATORY_HEADER', 'VIOL_HTTP_RESPONSE_STATUS', 'VIOL_REQUEST_MAX_LENGTH', 'VIOL_FILE_UPLOAD', 'VIOL_FILE_UPLOAD_IN_BODY', 'VIOL_XML_MALFORMED', 'VIOL_JSON_MALFORMED', 'VIOL_ASM_COOKIE_MODIFIED', 'VIOL_HTTP_PROTOCOL_MULTIPLE_HOST_HEADERS', 'VIOL_HTTP_PROTOCOL_BAD_HOST_HEADER_VALUE', 'VIOL_HTTP_PROTOCOL_UNPARSABLE_REQUEST_CONTENT', 'VIOL_HTTP_PROTOCOL_NULL_IN_REQUEST', 'VIOL_HTTP_PROTOCOL_BAD_HTTP_VERSION', 'VIOL_HTTP_PROTOCOL_CRLF_CHARACTERS_BEFORE_REQUEST_START', 'VIOL_HTTP_PROTOCOL_NO_HOST_HEADER_IN_HTTP_1_1_REQUEST', 'VIOL_HTTP_PROTOCOL_BAD_MULTIPART_PARAMETERS_PARSING', 'VIOL_HTTP_PROTOCOL_SEVERAL_CONTENT_LENGTH_HEADERS', 'VIOL_HTTP_PROTOCOL_CONTENT_LENGTH_SHOULD_BE_A_POSITIVE_NUMBER', 'VIOL_EVASION_DIRECTORY_TRAVERSALS', 'VIOL_MALFORMED_REQUEST', 'VIOL_EVASION_MULTIPLE_DECODING', 'VIOL_DATA_GUARD', 'VIOL_EVASION_APACHE_WHITESPACE', 'VIOL_COOKIE_MODIFIED', 'VIOL_EVASION_IIS_UNICODE_CODEPOINTS', 'VIOL_EVASION_IIS_BACKSLASHES', 'VIOL_EVASION_PERCENT_U_DECODING', 'VIOL_EVASION_BARE_BYTE_DECODING', 'VIOL_EVASION_BAD_UNESCAPE', 'VIOL_HTTP_PROTOCOL_BAD_MULTIPART_FORMDATA_REQUEST_PARSING', 'VIOL_HTTP_PROTOCOL_BODY_IN_GET_OR_HEAD_REQUEST', 'VIOL_HTTP_PROTOCOL_HIGH_ASCII_CHARACTERS_IN_HEADERS', 'VIOL_ENCODING', 'VIOL_COOKIE_MALFORMED', 'VIOL_GRAPHQL_FORMAT', 'VIOL_GRAPHQL_MALFORMED', 'VIOL_GRAPHQL_INTROSPECTION_QUERY']]] = None


class DetectionSetting(F5XCBaseModel):
    """Specifies detection settings to be used by WAF"""

    bot_protection_setting: Optional[BotProtectionSetting] = None
    default_bot_setting: Optional[Any] = None
    default_violation_settings: Optional[Any] = None
    disable_staging: Optional[Any] = None
    disable_suppression: Optional[Any] = None
    disable_threat_campaigns: Optional[Any] = None
    enable_suppression: Optional[Any] = None
    enable_threat_campaigns: Optional[Any] = None
    signature_selection_setting: Optional[SignatureSelectionSetting] = None
    stage_new_and_updated_signatures: Optional[SignaturesStagingSettings] = None
    stage_new_signatures: Optional[SignaturesStagingSettings] = None
    violation_settings: Optional[ViolationSettings] = None


class CreateSpecType(F5XCBaseModel):
    """Create Application Firewall"""

    ai_risk_based_blocking: Optional[AiRiskBasedBlocking] = None
    allow_all_response_codes: Optional[Any] = None
    allowed_response_codes: Optional[AllowedResponseCodes] = None
    blocking: Optional[Any] = None
    blocking_page: Optional[CustomBlockingPage] = None
    bot_protection_setting: Optional[BotProtectionSetting] = None
    custom_anonymization: Optional[AnonymizationSetting] = None
    default_anonymization: Optional[Any] = None
    default_bot_setting: Optional[Any] = None
    default_detection_settings: Optional[Any] = None
    detection_settings: Optional[DetectionSetting] = None
    disable_anonymization: Optional[Any] = None
    monitoring: Optional[Any] = None
    use_default_blocking_page: Optional[Any] = None


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
    """Get Application Firewall"""

    ai_risk_based_blocking: Optional[AiRiskBasedBlocking] = None
    allow_all_response_codes: Optional[Any] = None
    allowed_response_codes: Optional[AllowedResponseCodes] = None
    blocking: Optional[Any] = None
    blocking_page: Optional[CustomBlockingPage] = None
    bot_protection_setting: Optional[BotProtectionSetting] = None
    custom_anonymization: Optional[AnonymizationSetting] = None
    default_anonymization: Optional[Any] = None
    default_bot_setting: Optional[Any] = None
    default_detection_settings: Optional[Any] = None
    detection_settings: Optional[DetectionSetting] = None
    disable_anonymization: Optional[Any] = None
    monitoring: Optional[Any] = None
    use_default_blocking_page: Optional[Any] = None


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
    """Replace Application Firewall"""

    ai_risk_based_blocking: Optional[AiRiskBasedBlocking] = None
    allow_all_response_codes: Optional[Any] = None
    allowed_response_codes: Optional[AllowedResponseCodes] = None
    blocking: Optional[Any] = None
    blocking_page: Optional[CustomBlockingPage] = None
    bot_protection_setting: Optional[BotProtectionSetting] = None
    custom_anonymization: Optional[AnonymizationSetting] = None
    default_anonymization: Optional[Any] = None
    default_bot_setting: Optional[Any] = None
    default_detection_settings: Optional[Any] = None
    detection_settings: Optional[DetectionSetting] = None
    disable_anonymization: Optional[Any] = None
    monitoring: Optional[Any] = None
    use_default_blocking_page: Optional[Any] = None


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
    """By default a summary of app_firewall is returned in 'List'. By setting..."""

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


class MetricTypeData(F5XCBaseModel):
    """Metric Type Data contains key/value pair that uniquely identifies the..."""

    key: Optional[dict[str, Any]] = None
    value: Optional[list[MetricValue]] = None


class MetricData(F5XCBaseModel):
    """Metric data contains the metric type and the corresponding metric value"""

    data: Optional[list[MetricTypeData]] = None
    type_: Optional[Literal['BOT_DETECTION', 'ATTACKED_REQUESTS', 'BLOCKED_REQUESTS', 'TOTAL_REQUESTS']] = Field(default=None, alias="type")
    unit: Optional[Literal['UNIT_MILLISECONDS', 'UNIT_SECONDS', 'UNIT_MINUTES', 'UNIT_HOURS', 'UNIT_DAYS', 'UNIT_BYTES', 'UNIT_KBYTES', 'UNIT_MBYTES', 'UNIT_GBYTES', 'UNIT_TBYTES', 'UNIT_KIBIBYTES', 'UNIT_MIBIBYTES', 'UNIT_GIBIBYTES', 'UNIT_TEBIBYTES', 'UNIT_BITS_PER_SECOND', 'UNIT_BYTES_PER_SECOND', 'UNIT_KBITS_PER_SECOND', 'UNIT_KBYTES_PER_SECOND', 'UNIT_MBITS_PER_SECOND', 'UNIT_MBYTES_PER_SECOND', 'UNIT_CONNECTIONS_PER_SECOND', 'UNIT_ERRORS_PER_SECOND', 'UNIT_PACKETS_PER_SECOND', 'UNIT_REQUESTS_PER_SECOND', 'UNIT_PACKETS', 'UNIT_PERCENTAGE', 'UNIT_COUNT']] = None


class MetricsResponse(F5XCBaseModel):
    """Metrics for DC Cluster Groups"""

    data: Optional[list[MetricData]] = None
    step: Optional[str] = None


class ReplaceResponse(F5XCBaseModel):
    pass


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
