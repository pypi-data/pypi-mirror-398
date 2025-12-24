"""Pydantic models for bigip_virtual_server."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class BigipVirtualServerListItem(F5XCBaseModel):
    """List item for bigip_virtual_server resources."""


class DiscoveredAPISettings(F5XCBaseModel):
    """x-example: '2' Configure Discovered API Settings."""

    purge_duration_for_inactive_discovered_apis: Optional[int] = None


class BigIPVirtualServerList(F5XCBaseModel):
    bigip_virtual_servers: Optional[list[str]] = None


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


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ApiEndpointDetails(F5XCBaseModel):
    """This defines api endpoint"""

    methods: Optional[list[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']]] = None
    path: Optional[str] = None


class MessageMetaType(F5XCBaseModel):
    """MessageMetaType is metadata (common attributes) of a message that only..."""

    description: Optional[str] = None
    name: Optional[str] = None


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


class ApiCodeRepos(F5XCBaseModel):
    """Select which API repositories represent the LB applications"""

    api_code_repo: Optional[list[str]] = None


class CodeBaseIntegrationSelection(F5XCBaseModel):
    all_repos: Optional[Any] = None
    code_base_integration: Optional[ObjectRefType] = None
    selected_repos: Optional[ApiCodeRepos] = None


class ApiDiscoveryFromCodeScan(F5XCBaseModel):
    """x-required"""

    code_base_integrations: Optional[list[CodeBaseIntegrationSelection]] = None


class ApiDiscoveryAdvancedSettings(F5XCBaseModel):
    """API Discovery Advanced settings"""

    api_discovery_ref: Optional[ObjectRefType] = None


class ApiDiscoverySetting(F5XCBaseModel):
    """Specifies the settings used for API discovery"""

    api_crawler: Optional[ApiCrawler] = None
    api_discovery_from_code_scan: Optional[ApiDiscoveryFromCodeScan] = None
    custom_api_auth_discovery: Optional[ApiDiscoveryAdvancedSettings] = None
    default_api_auth_discovery: Optional[Any] = None
    disable_learn_from_redirect_traffic: Optional[Any] = None
    discovered_api_settings: Optional[DiscoveredAPISettings] = None
    enable_learn_from_redirect_traffic: Optional[Any] = None


class SensitiveDataPolicySettings(F5XCBaseModel):
    """Settings for data type policy"""

    sensitive_data_policy_ref: Optional[ObjectRefType] = None


class ReplaceSpecType(F5XCBaseModel):
    """Shape of the BIG-IP virtual server specification"""

    api_specification: Optional[APISpecificationSettings] = None
    default_sensitive_data_policy: Optional[Any] = None
    disable_api_definition: Optional[Any] = None
    disable_api_discovery: Optional[Any] = None
    enable_api_discovery: Optional[ApiDiscoverySetting] = None
    sensitive_data_policy: Optional[SensitiveDataPolicySettings] = None


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ReplaceSpecType] = None


class GetSpecType(F5XCBaseModel):
    """Shape of the BIG-IP virtual server specification"""

    api_specification: Optional[APISpecificationSettings] = None
    bigip_hostname: Optional[str] = None
    bigip_version: Optional[str] = None
    bigip_vs_description: Optional[str] = None
    default_sensitive_data_policy: Optional[Any] = None
    disable_api_definition: Optional[Any] = None
    disable_api_discovery: Optional[Any] = None
    enable_api_discovery: Optional[ApiDiscoverySetting] = None
    sensitive_data_policy: Optional[SensitiveDataPolicySettings] = None
    server_name: Optional[str] = None
    service_discovery: Optional[ObjectRefType] = None
    type_: Optional[Literal['INVALID_VIRTUAL_SERVER', 'BIGIP_VIRTUAL_SERVER']] = Field(default=None, alias="type")


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


class GetSecurityConfigReq(F5XCBaseModel):
    """Request of GET Security Config Spec API"""

    all_bigip_virtual_servers: Optional[Any] = None
    bigip_virtual_servers_list: Optional[BigIPVirtualServerList] = None
    namespace: Optional[str] = None


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
    """By default a summary of bigip_virtual_server is returned in 'List'. By..."""

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


class GetSecurityConfigRsp(F5XCBaseModel):
    api_protection: Optional[list[str]] = None
    app_firewall: Optional[list[str]] = None
    app_firewall_per_route: Optional[list[str]] = None
    bot_defense: Optional[list[str]] = None
    ddos_detection: Optional[list[str]] = None
    protected: Optional[list[str]] = None


# Convenience aliases
Spec = OpenApiValidationAllSpecEndpointsSettings
Spec = ValidateApiBySpecRule
Spec = APISpecificationSettings
Spec = ReplaceSpecType
Spec = GetSpecType
