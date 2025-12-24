"""Pydantic models for waf_exclusion_policy."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class WafExclusionPolicyListItem(F5XCBaseModel):
    """List item for waf_exclusion_policy resources."""


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


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


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


class CreateSpecType(F5XCBaseModel):
    """Create a WAF exclusion policy"""

    waf_exclusion_rules: Optional[list[SimpleWafExclusionRule]] = None


class GetSpecType(F5XCBaseModel):
    """Retrieve a WAF exclusion policy"""

    waf_exclusion_rules: Optional[list[SimpleWafExclusionRule]] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replace an existing WAF exclusion policy"""

    waf_exclusion_rules: Optional[list[SimpleWafExclusionRule]] = None


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
    """By default a summary of waf_exclusion_policy is returned in 'List'. By..."""

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
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
