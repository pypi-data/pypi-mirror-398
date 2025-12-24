"""Pydantic models for app_type."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AppTypeListItem(F5XCBaseModel):
    """List item for app_type resources."""


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class HttpBody(F5XCBaseModel):
    """Message that represents an arbitrary HTTP body. It should only be used..."""

    content_type: Optional[str] = None
    data: Optional[str] = None
    extensions: Optional[list[ProtobufAny]] = None


class APIEPDynExample(F5XCBaseModel):
    """List of Examples of expanded URL components for API endpoints that are..."""

    component_examples: Optional[list[str]] = None
    component_identifier: Optional[str] = None


class AuthenticationTypeLocPair(F5XCBaseModel):
    """API Endpoint's Authentication Type and Location."""

    auth_type: Optional[str] = None
    location: Optional[Literal['AUTH_LOCATION_HEADER', 'AUTH_LOCATION_QUERY', 'AUTH_LOCATION_BODY', 'AUTH_LOCATION_COOKIE']] = None
    type_: Optional[Literal['AUTH_TYPE_BASIC', 'AUTH_TYPE_BEARER', 'AUTH_TYPE_JWT', 'AUTH_TYPE_API_KEY', 'AUTH_TYPE_OAUTH2', 'AUTH_TYPE_OPENID', 'AUTH_TYPE_HTTP', 'AUTH_TYPE_OAUTH1', 'AUTH_TYPE_DIGEST', 'AUTH_TYPE_NEGOTIATE']] = Field(default=None, alias="type")


class PDFSpec(F5XCBaseModel):
    """Probability Density point in (PDF(x)) of the metric. x is the value of..."""

    probability: Optional[float] = None
    x: Optional[float] = None


class PDFStat(F5XCBaseModel):
    """Probability Density Function statistics of the metric. pdf_mean is the..."""

    pdf_95: Optional[float] = None
    pdf_mean: Optional[float] = None


class APIEPPDFInfo(F5XCBaseModel):
    """Metrics supported currently are request_size response_size..."""

    creation_timestamp: Optional[str] = None
    error_rate: Optional[list[PDFSpec]] = None
    error_rate_stat: Optional[PDFStat] = None
    latency_no_data: Optional[list[PDFSpec]] = None
    latency_no_data_stat: Optional[PDFStat] = None
    latency_with_data: Optional[list[PDFSpec]] = None
    latency_with_data_stat: Optional[PDFStat] = None
    request_rate: Optional[list[PDFSpec]] = None
    request_rate_stat: Optional[PDFStat] = None
    request_size: Optional[list[PDFSpec]] = None
    request_size_stat: Optional[PDFStat] = None
    response_size: Optional[list[PDFSpec]] = None
    response_size_stat: Optional[PDFStat] = None
    response_throughput: Optional[list[PDFSpec]] = None
    response_throughput_stat: Optional[PDFStat] = None


class RiskScore(F5XCBaseModel):
    """Risk score of the vulnerabilities found for this API Endpoint."""

    score: Optional[float] = None
    severity: Optional[Literal['APIEP_SEC_RISK_NONE', 'APIEP_SEC_RISK_LOW', 'APIEP_SEC_RISK_MED', 'APIEP_SEC_RISK_HIGH', 'APIEP_SEC_RISK_CRITICAL']] = None


class APIEPInfo(F5XCBaseModel):
    """Information about automatically identified API endpoint Each identified..."""

    access_discovery_time: Optional[str] = None
    api_groups: Optional[list[str]] = None
    api_type: Optional[Literal['API_TYPE_UNKNOWN', 'API_TYPE_GRAPHQL', 'API_TYPE_REST', 'API_TYPE_GRPC']] = None
    attributes: Optional[list[str]] = None
    authentication_state: Optional[Literal['AUTH_STATE_UNKNOWN', 'AUTH_STATE_AUTHENTICATED', 'AUTH_STATE_UNAUTHENTICATED']] = None
    authentication_types: Optional[list[AuthenticationTypeLocPair]] = None
    avg_latency: Optional[float] = None
    base_path: Optional[str] = None
    category: Optional[list[Literal['APIEP_CATEGORY_DISCOVERED', 'APIEP_CATEGORY_SWAGGER', 'APIEP_CATEGORY_INVENTORY', 'APIEP_CATEGORY_SHADOW', 'APIEP_CATEGORY_DEPRECATED', 'APIEP_CATEGORY_NON_API']]] = None
    collapsed_url: Optional[str] = None
    compliances: Optional[list[str]] = None
    domains: Optional[list[str]] = None
    dyn_examples: Optional[list[APIEPDynExample]] = None
    engines: Optional[list[str]] = None
    err_rsp_count: Optional[str] = None
    has_learnt_schema: Optional[bool] = None
    last_tested: Optional[str] = None
    max_latency: Optional[float] = None
    method: Optional[str] = None
    pdf_info: Optional[APIEPPDFInfo] = None
    pii_level: Optional[Literal['APIEP_PII_NOT_DETECTED', 'APIEP_PII_DETECTED']] = None
    req_rate: Optional[float] = None
    request_percentage: Optional[float] = None
    requests_count: Optional[int] = None
    risk_score: Optional[RiskScore] = None
    schema_status: Optional[str] = None
    sec_events_count: Optional[int] = None
    security_risk: Optional[Literal['APIEP_SEC_RISK_NONE', 'APIEP_SEC_RISK_LOW', 'APIEP_SEC_RISK_MED', 'APIEP_SEC_RISK_HIGH', 'APIEP_SEC_RISK_CRITICAL']] = None
    sensitive_data: Optional[list[Literal['SENSITIVE_DATA_TYPE_CCN', 'SENSITIVE_DATA_TYPE_SSN', 'SENSITIVE_DATA_TYPE_IP', 'SENSITIVE_DATA_TYPE_EMAIL', 'SENSITIVE_DATA_TYPE_PHONE', 'SENSITIVE_DATA_TYPE_CREDENTIALS', 'SENSITIVE_DATA_TYPE_APP_INFO_LEAKAGE', 'SENSITIVE_DATA_TYPE_MASKED_PII', 'SENSITIVE_DATA_TYPE_LOCATION']]] = None
    sensitive_data_location: Optional[list[str]] = None
    sensitive_data_types: Optional[list[str]] = None


class APIEndpointLearntSchemaReq(F5XCBaseModel):
    """shape of request to get learnt schema request for a given API endpoint."""

    api_endpoint_info_request: Optional[list[Literal['API_ENDPOINT_INFO_NONE', 'API_ENDPOINT_INFO_PDF_SPARKLINES']]] = None
    app_type_name: Optional[str] = None
    collapsed_url: Optional[str] = None
    method: Optional[str] = None
    namespace: Optional[str] = None


class SchemaStruct(F5XCBaseModel):
    """Schema structure for a given API endpoint."""

    examples: Optional[list[str]] = None
    schema_: Optional[str] = Field(default=None, alias="schema")


class RequestSchema(F5XCBaseModel):
    """Request schema for a given API endpoint."""

    body_per_content_type: Optional[dict[str, Any]] = None
    cookies: Optional[SchemaStruct] = None
    headers: Optional[SchemaStruct] = None
    query_params: Optional[SchemaStruct] = None


class DiscoveredSchema(F5XCBaseModel):
    """Discovery schema for request API endpoint."""

    last_updated_time: Optional[str] = None
    request_schema: Optional[RequestSchema] = None
    response_schema_per_rsp_code: Optional[dict[str, Any]] = None


class SensitiveData(F5XCBaseModel):
    """Sensitive data for a given API endpoint."""

    compliances: Optional[list[str]] = None
    examples: Optional[list[str]] = None
    field: Optional[str] = None
    rule_type: Optional[Literal['RULE_TYPE_BUILT_IN', 'RULE_TYPE_CUSTOM']] = None
    section: Optional[str] = None
    sensitive_data_type: Optional[str] = None
    type_: Optional[Literal['SENSITIVE_DATA_TYPE_CCN', 'SENSITIVE_DATA_TYPE_SSN', 'SENSITIVE_DATA_TYPE_IP', 'SENSITIVE_DATA_TYPE_EMAIL', 'SENSITIVE_DATA_TYPE_PHONE', 'SENSITIVE_DATA_TYPE_CREDENTIALS', 'SENSITIVE_DATA_TYPE_APP_INFO_LEAKAGE', 'SENSITIVE_DATA_TYPE_MASKED_PII', 'SENSITIVE_DATA_TYPE_LOCATION']] = Field(default=None, alias="type")


class APIEndpointLearntSchemaRsp(F5XCBaseModel):
    """shape of response to get req body schema for a given API endpoint."""

    api_specs: Optional[dict[str, Any]] = None
    discovered_schema: Optional[DiscoveredSchema] = None
    inventory_openapi_spec: Optional[str] = None
    pdf_info: Optional[APIEPPDFInfo] = None
    sensitive_data: Optional[list[SensitiveData]] = None


class APIEndpointPDFRsp(F5XCBaseModel):
    """shape of response to get PDF for a given API endpoint."""

    pdf_info: Optional[APIEPPDFInfo] = None


class APIEndpointsRsp(F5XCBaseModel):
    """Response shape for GET API endpoints API. It is list of API endpoints discovered"""

    apiep_list: Optional[list[APIEPInfo]] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class DiscoveredAPISettings(F5XCBaseModel):
    """x-example: '2' Configure Discovered API Settings."""

    purge_duration_for_inactive_discovered_apis: Optional[int] = None


class BusinessLogicMarkupSetting(F5XCBaseModel):
    """Settings specifying how API Discovery will be performed"""

    disable: Optional[Any] = None
    discovered_api_settings: Optional[DiscoveredAPISettings] = None
    enable: Optional[Any] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class Feature(F5XCBaseModel):
    """List of features that are to be enabled for this apptype. FeatureType..."""

    type_: Optional[Literal['BUSINESS_LOGIC_MARKUP', 'TIMESERIES_ANOMALY_DETECTION', 'PER_REQ_ANOMALY_DETECTION', 'USER_BEHAVIOR_ANALYSIS']] = Field(default=None, alias="type")


class CreateSpecType(F5XCBaseModel):
    """Create App type will create the configuration in namespace metadata.namespace"""

    business_logic_markup_setting: Optional[BusinessLogicMarkupSetting] = None
    features: Optional[list[Feature]] = None


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
    """Get App type will read the configuration from namespace metadata.namespace"""

    business_logic_markup_setting: Optional[BusinessLogicMarkupSetting] = None
    features: Optional[list[Feature]] = None


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
    """Update the configuration by replacing the existing spec with the..."""

    business_logic_markup_setting: Optional[BusinessLogicMarkupSetting] = None
    features: Optional[list[Feature]] = None


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
    """By default a summary of app_type is returned in 'List'. By setting..."""

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


class OverrideInfo(F5XCBaseModel):
    """Rule to override a given automatic dynamic identifier used to expand or..."""

    component_identifier: Optional[str] = None
    set_dynamic: Optional[bool] = None


class OverridePopReq(F5XCBaseModel):
    """Shape of remove to remove override for API endpoints"""

    app_type_name: Optional[str] = None
    namespace: Optional[str] = None


class OverridePopRsp(F5XCBaseModel):
    """Shape of response to add override for API endpoints"""

    status: Optional[bool] = None
    status_msg: Optional[str] = None


class OverridePushReq(F5XCBaseModel):
    """Shape of request to add override for API endpoints"""

    app_type_name: Optional[str] = None
    namespace: Optional[str] = None
    override_info: Optional[OverrideInfo] = None


class OverridePushRsp(F5XCBaseModel):
    """Shape of response to add override for API endpoints"""

    status: Optional[bool] = None
    status_msg: Optional[str] = None


class OverridesRsp(F5XCBaseModel):
    """shape of response to get override for API endpoints"""

    override_list: Optional[list[OverrideInfo]] = None


class ReplaceResponse(F5XCBaseModel):
    pass


class ServiceAPIEndpointPDFReq(F5XCBaseModel):
    """shape of request to get PDF for a given API endpoint."""

    app_type_name: Optional[str] = None
    collapsed_url: Optional[str] = None
    method: Optional[str] = None
    namespace: Optional[str] = None
    service_name: Optional[str] = None


class ServiceAPIEndpointsReq(F5XCBaseModel):
    """Request shape for GET Service API endpoints API"""

    api_endpoint_info_request: Optional[list[Literal['API_ENDPOINT_INFO_NONE', 'API_ENDPOINT_INFO_PDF_SPARKLINES']]] = None
    app_type_name: Optional[str] = None
    namespace: Optional[str] = None
    service_name: Optional[str] = None


# Convenience aliases
Spec = PDFSpec
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
