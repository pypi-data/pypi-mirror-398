"""HttpLoadbalancer resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.http_loadbalancer.models import (
    HttpLoadbalancerListItem,
    ProtobufAny,
    HttpBody,
    DiscoveredAPISettings,
    RiskScore,
    CircuitBreaker,
    EndpointSubsetSelectorType,
    Http2ProtocolOptions,
    OutlierDetectionType,
    ObjectRefType,
    CustomCacheRule,
    CDNControllerStatus,
    CDNSiteStatus,
    GetServiceOperationReq,
    ErrorType,
    PurgeOperationItem,
    ServiceOperationItem,
    GetServiceOperationRsp,
    Empty,
    LilacCDNCachePurgeRequest,
    LilacCDNCachePurgeResponse,
    ServiceOperationsTimeRange,
    ListServiceOperationsReq,
    ServiceOperationsItem,
    ListServiceOperationsRsp,
    DomainType,
    BotDefenseFlowLabelAccountManagementChoiceType,
    BotDefenseTransactionResultCondition,
    BotDefenseTransactionResultType,
    BotDefenseTransactionResult,
    BotDefenseFlowLabelAuthenticationChoiceType,
    BotDefenseFlowLabelFinancialServicesChoiceType,
    BotDefenseFlowLabelFlightChoiceType,
    BotDefenseFlowLabelProfileManagementChoiceType,
    BotDefenseFlowLabelSearchChoiceType,
    BotDefenseFlowLabelShoppingGiftCardsChoiceType,
    BotDefenseFlowLabelCategoriesChoiceType,
    MatcherType,
    HeaderMatcherType,
    MessageMetaType,
    ShapeBotBlockMitigationActionType,
    ShapeBotFlagMitigationActionType,
    ShapeBotFlagMitigationActionChoiceType,
    ShapeBotRedirectMitigationActionType,
    ShapeBotMitigationAction,
    PathMatcherType,
    QueryParameterMatcherType,
    WebMobileTrafficType,
    AppEndpointType,
    HeaderMatcherTypeBasic,
    MobileTrafficIdentifierType,
    BotAdvancedMobileSDKConfigType,
    ShapeJavaScriptInsertAllType,
    ShapeJavaScriptExclusionRule,
    ShapeJavaScriptInsertAllWithExceptionsType,
    ShapeJavaScriptInsertionRule,
    ShapeJavaScriptInsertType,
    BotDefenseAdvancedType,
    CSDJavaScriptInsertAllWithExceptionsType,
    CSDJavaScriptInsertionRule,
    CSDJavaScriptInsertType,
    ClientSideDefensePolicyType,
    ClientSideDefenseType,
    AsnMatchList,
    JA4TlsFingerprintMatcherType,
    TlsFingerprintMatcherType,
    DDoSClientSource,
    PrefixMatchList,
    DDoSMitigationRule,
    DeleteDoSAutoMitigationRuleRsp,
    ObjectRefType,
    Destination,
    GetSpecType,
    DoSMitigationRuleInfo,
    GetDoSAutoMitigationRulesRsp,
    GetSecurityConfigRsp,
    Action,
    DomainMatcherType,
    MalwareProtectionRule,
    MalwareProtectionPolicy,
    MobileSDKConfigType,
    SensitiveDataPolicySettings,
    ShapeBotDefensePolicyType,
    ShapeBotDefenseType,
    APIProtectionRuleAction,
    HttpMethodMatcherType,
    AsnMatcherType,
    LabelSelectorType,
    IpMatcherType,
    IPThreatCategoryListType,
    ClientMatcher,
    CookieMatcherType,
    JWTClaimMatcherType,
    RequestMatcher,
    APIEndpointProtectionRule,
    APIGroupProtectionRule,
    APIGroups,
    APIProtectionRules,
    InlineRateLimiter,
    ApiEndpointRule,
    ApiEndpointDetails,
    BypassRateLimitingRule,
    BypassRateLimitingRules,
    CustomIpAllowedList,
    PrefixStringListType,
    ServerUrlRule,
    APIRateLimit,
    FallThroughRule,
    CustomFallThroughMode,
    OpenApiFallThroughMode,
    ValidationSettingForQueryParameters,
    ValidationPropertySetting,
    OpenApiValidationCommonSettings,
    OpenApiValidationModeActiveResponse,
    OpenApiValidationModeActive,
    OpenApiValidationMode,
    OpenApiValidationAllSpecEndpointsSettings,
    OpenApiValidationRule,
    ValidateApiBySpecRule,
    APISpecificationSettings,
    ApiCodeRepos,
    BlindfoldSecretInfoType,
    ClearSecretInfoType,
    SecretType,
    SimpleLogin,
    DomainConfiguration,
    ApiCrawlerConfiguration,
    ApiCrawler,
    ApiDiscoveryAdvancedSettings,
    CodeBaseIntegrationSelection,
    ApiDiscoveryFromCodeScan,
    ApiDiscoverySetting,
    Audiences,
    BasePathsType,
    ArgMatcherType,
    MatcherTypeBasic,
    PathMatcherType,
    ChallengeRuleSpec,
    ChallengeRule,
    ChallengeRuleList,
    CaptchaChallengeType,
    JavascriptChallengeType,
    EnableChallenge,
    HeaderMatcherType,
    HttpHeaderMatcherList,
    JWKS,
    MandatoryClaims,
    ReservedClaims,
    Target,
    TokenLocation,
    JWTValidation,
    PolicyList,
    InputHours,
    InputMinutes,
    InputSeconds,
    RateLimitBlockAction,
    LeakyBucketRateLimiter,
    TokenBucketRateLimiter,
    RateLimitValue,
    RateLimitConfigType,
    ServicePolicyList,
    SimpleClientSrcRule,
    AppFirewallAttackTypeContext,
    BotNameContext,
    AppFirewallSignatureContext,
    AppFirewallViolationContext,
    AppFirewallDetectionControl,
    SimpleWafExclusionRule,
    WafExclusionInlineRules,
    WafExclusion,
    APIGroupsApiep,
    BufferConfigType,
    CompressionType,
    CookieValueOption,
    HeaderManipulationOptionType,
    SetCookieValueOption,
    AdvancedOptionsType,
    ApiKey,
    BasicAuthentication,
    Bearer,
    LoginEndpoint,
    Credentials,
    DomainConfiguration,
    ApiTesting,
    AssignAPIDefinitionReq,
    AssignAPIDefinitionResp,
    BodySectionMaskingOptions,
    DefaultCacheAction,
    CachingPolicy,
    ObjectCreateMetaType,
    AdvertisePublic,
    WhereSite,
    WhereVirtualNetwork,
    WhereVirtualSite,
    WhereVirtualSiteSpecifiedVIP,
    WhereVK8SService,
    WhereType,
    AdvertiseCustom,
    CookieForHashing,
    CorsPolicy,
    DomainNameList,
    CsrfPolicy,
    SimpleDataGuardRule,
    OriginPoolDefaultSubset,
    OriginPoolSubsets,
    HeaderTransformationType,
    Http1ProtocolOptions,
    OriginPoolAdvancedOptions,
    OriginServerCBIPService,
    SiteLocator,
    SnatPoolConfiguration,
    OriginServerConsulService,
    OriginServerCustomEndpoint,
    OriginServerK8SService,
    OriginServerPrivateIP,
    OriginServerPrivateName,
    OriginServerPublicIP,
    OriginServerPublicName,
    OriginServerVirtualNetworkIP,
    OriginServerVirtualNetworkName,
    OriginServerType,
    UpstreamConnPoolReuseType,
    CustomCiphers,
    TlsConfig,
    HashAlgorithms,
    TlsCertificateType,
    TlsCertificatesType,
    UpstreamTlsValidationContext,
    UpstreamTlsParameters,
    GlobalSpecType,
    OriginPoolWithWeight,
    OriginPoolListType,
    IPThreatCategoryListType,
    ClientIPHeaders,
    GraphQLSettingsType,
    GraphQLRule,
    ProxyTypeHttp,
    TLSCoalescingOptions,
    Http1ProtocolOptions,
    HttpProtocolOptions,
    XfccHeaderKeys,
    DownstreamTlsValidationContext,
    DownstreamTLSCertsParams,
    DownstreamTlsParamsType,
    ProxyTypeHttps,
    ProxyTypeHttpsAutoCerts,
    L7DDoSProtectionSettings,
    OriginServerSubsetRule,
    OriginServerSubsetRuleListType,
    TemporaryUserBlockingType,
    PolicyBasedChallenge,
    CookieManipulationOptionType,
    HashPolicyType,
    HashPolicyListType,
    RouteTypeCustomRoute,
    PortMatcherType,
    RouteDirectResponse,
    RouteTypeDirectResponse,
    RouteRedirect,
    RouteTypeRedirect,
    TagAttribute,
    JavaScriptTag,
    BotDefenseJavascriptInjectionType,
    FractionalPercent,
    MirrorPolicyType,
    RegexMatchRewrite,
    RetryBackOff,
    RetryPolicyType,
    WebsocketConfigType,
    RouteSimpleAdvancedOptions,
    QueryParamsSimpleRoute,
    RouteTypeSimple,
    RouteType,
    SensitiveDataTypes,
    SensitiveDataDisclosureRules,
    SingleLoadBalancerAppSetting,
    SlowDDoSMitigation,
    CreateSpecType,
    CreateRequest,
    ObjectGetMetaType,
    DNSRecord,
    AutoCertInfoType,
    DnsInfo,
    InternetVIPListenerStatusType,
    InternetVIPTargetGroupStatusType,
    InternetVIPStatus,
    InternetVIPInfo,
    GetSpecType,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    CreateResponse,
    DeleteRequest,
    GetAPIEndpointsForGroupsReq,
    GetAPIEndpointsForGroupsRsp,
    ApiOperation,
    GetAPIEndpointsSchemaUpdatesReq,
    ApiEndpointWithSchema,
    GetAPIEndpointsSchemaUpdatesResp,
    GlobalSpecType,
    GetDnsInfoResponse,
    ObjectReplaceMetaType,
    ReplaceSpecType,
    ReplaceRequest,
    ConditionType,
    StatusMetaType,
    DNSVHostStatusType,
    StatusObject,
    GetResponse,
    HTTPLoadBalancerList,
    GetSecurityConfigReq,
    ListAvailableAPIDefinitionsResp,
    ListResponseItem,
    ListResponse,
    ReplaceResponse,
    SetL7DDoSRPSThresholdReq,
    SetL7DDoSRPSThresholdRsp,
    UpdateAPIEndpointsSchemasReq,
    UpdateAPIEndpointsSchemasResp,
)


# Exclusion group mappings for get() method
_EXCLUDE_GROUPS: dict[str, set[str]] = {
    "forms": {"create_form", "replace_form"},
    "references": {"referring_objects", "deleted_referred_objects", "disabled_referred_objects"},
    "system_metadata": {"system_metadata"},
}


def _resolve_exclude_groups(groups: list[str]) -> set[str]:
    """Resolve exclusion group names to field names."""
    fields: set[str] = set()
    for group in groups:
        if group in _EXCLUDE_GROUPS:
            fields.update(_EXCLUDE_GROUPS[group])
        else:
            # Allow direct field names for flexibility
            fields.add(group)
    return fields


class HttpLoadbalancerResource:
    """API methods for http_loadbalancer.

    HTTP Load Balancer view defines a required parameters that can be...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.http_loadbalancer.CreateSpecType(...)
    GetSpecType = GetSpecType
    CreateSpecType = CreateSpecType
    GetSpecType = GetSpecType
    ReplaceSpecType = ReplaceSpecType
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        namespace: str,
        name: str,
        spec: ProtobufAny | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new http_loadbalancer.

        Shape of the HTTP load balancer specification

        Args:
            namespace: The namespace to create the resource in.
            name: The name of the resource.
            spec: The resource specification (typed model).
            body: Raw JSON body (alternative to spec, for advanced use).
            labels: Optional labels for the resource.
            annotations: Optional annotations for the resource.
            description: Optional description.
            disable: Whether to create the resource in disabled state.
        """
        path = "/api/config/namespaces/{metadata.namespace}/http_loadbalancers"
        path = path.replace("{metadata.namespace}", namespace)

        if body is not None:
            request_body = body
        else:
            request_body: dict[str, Any] = {
                "metadata": {
                    "name": name,
                    "namespace": namespace,
                },
            }
            if labels:
                request_body["metadata"]["labels"] = labels
            if annotations:
                request_body["metadata"]["annotations"] = annotations
            if description:
                request_body["metadata"]["description"] = description
            if disable is not None:
                request_body["metadata"]["disable"] = disable
            # Always include spec - API requires it even if empty
            if spec is not None:
                request_body["spec"] = spec.model_dump(by_alias=True, exclude_none=True)
            else:
                request_body["spec"] = {}

        try:
            response = self._http.post(path, json=request_body)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreateResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: ProtobufAny | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing http_loadbalancer.

        Shape of the HTTP load balancer specification

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to replace.
            spec: The new resource specification (typed model).
            body: Raw JSON body (alternative to spec, for advanced use).
            labels: Optional labels for the resource.
            annotations: Optional annotations for the resource.
            description: Optional description.
            disable: Whether to disable the resource.
        """
        path = "/api/config/namespaces/{metadata.namespace}/http_loadbalancers/{metadata.name}"
        path = path.replace("{metadata.namespace}", namespace)
        path = path.replace("{metadata.name}", name)

        if body is not None:
            request_body = body
        else:
            request_body: dict[str, Any] = {
                "metadata": {
                    "name": name,
                    "namespace": namespace,
                },
            }
            if labels:
                request_body["metadata"]["labels"] = labels
            if annotations:
                request_body["metadata"]["annotations"] = annotations
            if description:
                request_body["metadata"]["description"] = description
            if disable is not None:
                request_body["metadata"]["disable"] = disable
            # Always include spec - API requires it even if empty
            if spec is not None:
                request_body["spec"] = spec.model_dump(by_alias=True, exclude_none=True)
            else:
                request_body["spec"] = {}

        try:
            response = self._http.put(path, json=request_body)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReplaceResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[HttpLoadbalancerListItem]:
        """List http_loadbalancer resources in a namespace.

        List the set of http_loadbalancer in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if label_filter is not None:
            params["label_filter"] = label_filter
        if report_fields is not None:
            params["report_fields"] = report_fields
        if report_status_fields is not None:
            params["report_status_fields"] = report_status_fields

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

        items = response.get("items", [])
        errors = response.get("errors", [])

        if errors:
            raise F5XCPartialResultsError(items=items, errors=errors)

        try:
            return [HttpLoadbalancerListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a http_loadbalancer by name.

        Shape of the HTTP load balancer specification

        By default, excludes verbose fields (forms, references, system_metadata).
        Use include_all=True to get the complete response.

        Args:
            exclude: Additional field groups to exclude from response.
                - 'forms': Excludes create_form, replace_form
                - 'references': Excludes referring_objects, deleted/disabled_referred_objects
                - 'system_metadata': Excludes system_metadata
                You can also pass individual field names directly.
            include_all: If True, return all fields without default exclusions.
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if response_format is not None:
            params["response_format"] = response_format

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

        # Apply default exclusions unless include_all=True
        if not include_all:
            default_exclude = ["forms", "references", "system_metadata"]
            exclude = (exclude or []) + default_exclude

        if exclude:
            exclude_fields = _resolve_exclude_groups(exclude)
            # Remove excluded fields entirely from response
            filtered_response = {
                k: v for k, v in response.items()
                if k not in exclude_fields
            }
        else:
            filtered_response = response

        try:
            return GetResponse(**filtered_response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a http_loadbalancer.

        Delete the specified http_loadbalancer

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def get_service_operation_httplb_cache_enabled(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetServiceOperationRsp:
        """Get Service Operation Httplb Cache Enabled for http_loadbalancer.

        Get status of an operation command for a given HTTP LB when caching enabled.
        """
        path = "/api/cdn/namespaces/{namespace}/http_loadbalancer/get-service-operation-status"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetServiceOperationRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "get_service_operation_httplb_cache_enabled", e, response) from e

    def list_service_operations_httplb_cache_enabled(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListServiceOperationsRsp:
        """List Service Operations Httplb Cache Enabled for http_loadbalancer.

        List of service operations for a given HTTP LB when Caching Enabled
        """
        path = "/api/cdn/namespaces/{namespace}/http_loadbalancer/list-service-operations-status"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListServiceOperationsRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "list_service_operations_httplb_cache_enabled", e, response) from e

    def cdn_cache_purge_httplb_cache_enabled(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> LilacCDNCachePurgeResponse:
        """Cdn Cache Purge Httplb Cache Enabled for http_loadbalancer.

        Initiate Purge on the LB Cache
        """
        path = "/api/cdn/namespaces/{namespace}/http_loadbalancer/{name}/cache-purge"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LilacCDNCachePurgeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "cdn_cache_purge_httplb_cache_enabled", e, response) from e

    def get_security_config(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetSecurityConfigRsp:
        """Get Security Config for http_loadbalancer.

        Fetch the corresponding Security Config for the given HTTP load balancers
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/get_security_config"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSecurityConfigRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "get_security_config", e, response) from e

    def assign_api_definition(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> AssignAPIDefinitionResp:
        """Assign Api Definition for http_loadbalancer.

        Set a reference to the API Definition, with an option to create an...
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/api_definitions/assign"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AssignAPIDefinitionResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "assign_api_definition", e, response) from e

    def list_available_api_definitions(
        self,
        namespace: str,
        name: str,
    ) -> ListAvailableAPIDefinitionsResp:
        """List Available Api Definitions for http_loadbalancer.

        List API definitions suitable for API Inventory management API...
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/api_definitions/available"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListAvailableAPIDefinitionsResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "list_available_api_definitions", e, response) from e

    def get_api_endpoints_for_groups(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetAPIEndpointsForGroupsRsp:
        """Get Api Endpoints For Groups for http_loadbalancer.

        Get list of all API Endpoints associated with the HTTP loadbalancer...
        """
        path = "/api/ml/data/namespaces/{namespace}/http_loadbalancers/{name}/api_endpoints"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetAPIEndpointsForGroupsRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "get_api_endpoints_for_groups", e, response) from e

    def get_swagger_spec(
        self,
        namespace: str,
        name: str,
    ) -> HttpBody:
        """Get Swagger Spec for http_loadbalancer.

        Get the corresponding Swagger spec for the given HTTP load balancer
        """
        path = "/api/ml/data/namespaces/{namespace}/http_loadbalancers/{name}/api_endpoints/swagger_spec"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "get_swagger_spec", e, response) from e

    def get_api_endpoints_schema_updates(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetAPIEndpointsSchemaUpdatesResp:
        """Get Api Endpoints Schema Updates for http_loadbalancer.

        Get list of schema pairs, current and updated, for each endpoint in...
        """
        path = "/api/ml/data/namespaces/{namespace}/http_loadbalancers/{name}/api_inventory/api_endpoints/get_schema_updates"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetAPIEndpointsSchemaUpdatesResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "get_api_endpoints_schema_updates", e, response) from e

    def update_api_endpoints_schemas(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateAPIEndpointsSchemasResp:
        """Update Api Endpoints Schemas for http_loadbalancer.

        Update the payload schema for the specified endpoints or all pending...
        """
        path = "/api/ml/data/namespaces/{namespace}/http_loadbalancers/{name}/api_inventory/api_endpoints/update_schemas"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateAPIEndpointsSchemasResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "update_api_endpoints_schemas", e, response) from e

    def get_do_s_auto_mitigation_rules(
        self,
        namespace: str,
        name: str,
    ) -> GetDoSAutoMitigationRulesRsp:
        """Get Do S Auto Mitigation Rules for http_loadbalancer.

        Get the corresponding DoS Auto-Mitigation Rules for the given HTTP...
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/dos_automitigation_rules"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDoSAutoMitigationRulesRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "get_do_s_auto_mitigation_rules", e, response) from e

    def delete_do_s_auto_mitigation_rule(
        self,
        namespace: str,
        name: str,
        dos_automitigation_rule_name: str,
    ) -> DeleteDoSAutoMitigationRuleRsp:
        """Delete Do S Auto Mitigation Rule for http_loadbalancer.

        Delete the corresponding DoS Auto-Mitigation Rule for the given HTTP...
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/dos_automitigation_rules/{dos_automitigation_rule_name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)
        path = path.replace("{dos_automitigation_rule_name}", dos_automitigation_rule_name)


        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeleteDoSAutoMitigationRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "delete_do_s_auto_mitigation_rule", e, response) from e

    def get_dns_info(
        self,
        namespace: str,
        name: str,
    ) -> GetDnsInfoResponse:
        """Get Dns Info for http_loadbalancer.

        GetDnsInfo is an API to get DNS information for a given HTTP load balancer
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/get-dns-info"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDnsInfoResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "get_dns_info", e, response) from e

    def set_l7_d_do_srps_threshold(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> SetL7DDoSRPSThresholdRsp:
        """Set L7 D Do Srps Threshold for http_loadbalancer.

        Sets the L7 DDoS RPS threshold for HTTP load balancer
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/l7ddos_rps_threshold"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SetL7DDoSRPSThresholdRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("http_loadbalancer", "set_l7_d_do_srps_threshold", e, response) from e

