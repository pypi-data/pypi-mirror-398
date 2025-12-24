"""CdnLoadbalancer resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.cdn_loadbalancer.models import (
    CdnLoadbalancerListItem,
    DiscoveredAPISettings,
    CDNAccessLogFilter,
    CDNAccessLogAggregationRequest,
    CDNAccessLogRequest,
    Empty,
    CDNTLSConfig,
    CDNHTTPSAutoCertsType,
    ObjectRefType,
    CustomCiphers,
    TlsConfig,
    XfccHeaderKeys,
    DownstreamTlsValidationContext,
    DownstreamTLSCertsParams,
    HashAlgorithms,
    BlindfoldSecretInfoType,
    ClearSecretInfoType,
    SecretType,
    TlsCertificateType,
    DownstreamTlsParamsType,
    TlsCertOptions,
    CDNHTTPSCustomCertsType,
    CDNLoadBalancerList,
    CDNLogAggregationResponse,
    LilacCDNAccessLogsResponseData,
    CDNLogResponse,
    ObjectCreateMetaType,
    ServicePolicyList,
    HttpMethodMatcherType,
    AsnMatchList,
    ObjectRefType,
    AsnMatcherType,
    LabelSelectorType,
    IpMatcherType,
    PrefixMatchList,
    IPThreatCategoryListType,
    TlsFingerprintMatcherType,
    ClientMatcher,
    InlineRateLimiter,
    MatcherType,
    CookieMatcherType,
    HeaderMatcherType,
    JWTClaimMatcherType,
    QueryParameterMatcherType,
    RequestMatcher,
    ApiEndpointRule,
    ApiEndpointDetails,
    APIGroups,
    BypassRateLimitingRule,
    BypassRateLimitingRules,
    CustomIpAllowedList,
    PrefixStringListType,
    ServerUrlRule,
    APIRateLimit,
    MessageMetaType,
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
    HeaderMatcherType,
    HttpHeaderMatcherList,
    SimpleClientSrcRule,
    ShapeJavaScriptInsertAllType,
    DomainType,
    PathMatcherType,
    ShapeJavaScriptExclusionRule,
    ShapeJavaScriptInsertAllWithExceptionsType,
    ShapeJavaScriptInsertionRule,
    ShapeJavaScriptInsertType,
    HeaderMatcherTypeBasic,
    MobileTrafficIdentifierType,
    MobileSDKConfigType,
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
    ShapeBotBlockMitigationActionType,
    ShapeBotFlagMitigationActionType,
    ShapeBotFlagMitigationActionChoiceType,
    ShapeBotRedirectMitigationActionType,
    ShapeBotMitigationAction,
    WebMobileTrafficType,
    AppEndpointType,
    ShapeBotDefensePolicyType,
    ShapeBotDefenseType,
    CaptchaChallengeType,
    CSDJavaScriptInsertAllWithExceptionsType,
    CSDJavaScriptInsertionRule,
    CSDJavaScriptInsertType,
    ClientSideDefensePolicyType,
    ClientSideDefenseType,
    CorsPolicy,
    DomainNameList,
    CsrfPolicy,
    CustomCacheRule,
    SimpleDataGuardRule,
    JA4TlsFingerprintMatcherType,
    DDoSClientSource,
    DDoSMitigationRule,
    DefaultCacheAction,
    SimpleLogin,
    DomainConfiguration,
    ApiCrawlerConfiguration,
    ApiCrawler,
    ApiCodeRepos,
    CodeBaseIntegrationSelection,
    ApiDiscoveryFromCodeScan,
    ApiDiscoveryAdvancedSettings,
    ApiDiscoverySetting,
    JavascriptChallengeType,
    EnableChallenge,
    IPThreatCategoryListType,
    GraphQLSettingsType,
    GraphQLRule,
    ProxyTypeHttp,
    Action,
    JWKS,
    MandatoryClaims,
    Audiences,
    ReservedClaims,
    BasePathsType,
    Target,
    TokenLocation,
    JWTValidation,
    OriginAdvancedConfiguration,
    OriginServerPublicIP,
    OriginServerPublicName,
    CDNOriginServerType,
    TlsCertificatesType,
    UpstreamTlsValidationContext,
    UpstreamTlsParameters,
    CdnOriginPoolType,
    HeaderManipulationOptionType,
    HeaderControlType,
    LogHeaderOptions,
    LoggingOptionsType,
    OtherSettings,
    ArgMatcherType,
    MatcherTypeBasic,
    PathMatcherType,
    ChallengeRuleSpec,
    ChallengeRule,
    ChallengeRuleList,
    TemporaryUserBlockingType,
    PolicyBasedChallenge,
    CookieManipulationOptionType,
    PolicyList,
    InputHours,
    InputMinutes,
    InputSeconds,
    RateLimitBlockAction,
    LeakyBucketRateLimiter,
    TokenBucketRateLimiter,
    RateLimitValue,
    RateLimitConfigType,
    SensitiveDataPolicySettings,
    SlowDDoSMitigation,
    AppFirewallAttackTypeContext,
    BotNameContext,
    AppFirewallSignatureContext,
    AppFirewallViolationContext,
    AppFirewallDetectionControl,
    SimpleWafExclusionRule,
    WafExclusionInlineRules,
    WafExclusion,
    CreateSpecType,
    CreateRequest,
    ObjectGetMetaType,
    DNSRecord,
    AutoCertInfoType,
    DnsInfo,
    ServiceDomain,
    GetSpecType,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    CreateResponse,
    DeleteRequest,
    GetCDNSecurityConfigReq,
    ObjectReplaceMetaType,
    ReplaceSpecType,
    ReplaceRequest,
    CDNSiteStatus,
    CDNControllerStatus,
    ConditionType,
    StatusMetaType,
    DNSVHostStatusType,
    StatusObject,
    GetResponse,
    LilacCDNMetricsFilter,
    LilacCDNMetricsRequest,
    LilacCDNMetricsResponseGroupBy,
    LilacCDNMetricsResponseValue,
    LilacCDNMetricsResponseSeries,
    LilacCDNMetricsResponseData,
    LilacCDNMetricsResponse,
    ProtobufAny,
    ErrorType,
    ListResponseItem,
    ListResponse,
    ReplaceResponse,
    SubscribeRequest,
    SubscribeResponse,
    UnsubscribeRequest,
    UnsubscribeResponse,
    GetServiceOperationReq,
    PurgeOperationItem,
    ServiceOperationItem,
    GetServiceOperationRsp,
    LilacCDNCachePurgeRequest,
    LilacCDNCachePurgeResponse,
    ServiceOperationsTimeRange,
    ListServiceOperationsReq,
    ServiceOperationsItem,
    ListServiceOperationsRsp,
    DeleteDoSAutoMitigationRuleRsp,
    Destination,
    GetSpecType,
    DoSMitigationRuleInfo,
    GetDoSAutoMitigationRulesRsp,
    GetSecurityConfigRsp,
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


class CdnLoadbalancerResource:
    """API methods for cdn_loadbalancer.

    CDN Loadbalancer view defines a required parameters that can be used...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.cdn_loadbalancer.CreateSpecType(...)
    CreateSpecType = CreateSpecType
    GetSpecType = GetSpecType
    ReplaceSpecType = ReplaceSpecType
    GetResponse = GetResponse
    GetSpecType = GetSpecType

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        namespace: str,
        name: str,
        spec: DiscoveredAPISettings | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new cdn_loadbalancer.

        Shape of the CDN loadbalancer specification

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
        path = "/api/config/namespaces/{metadata.namespace}/cdn_loadbalancers"
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
            raise F5XCValidationError("cdn_loadbalancer", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: DiscoveredAPISettings | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing cdn_loadbalancer.

        Shape of the CDN loadbalancer specification

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
        path = "/api/config/namespaces/{metadata.namespace}/cdn_loadbalancers/{metadata.name}"
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
            raise F5XCValidationError("cdn_loadbalancer", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[CdnLoadbalancerListItem]:
        """List cdn_loadbalancer resources in a namespace.

        List the set of cdn_loadbalancer in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/config/namespaces/{namespace}/cdn_loadbalancers"
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
            return [CdnLoadbalancerListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "list", e, response) from e

    def get_cdn_security_config(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetSecurityConfigRsp:
        """Get Cdn Security Config for cdn_loadbalancer.

        Fetch the corresponding Security Config for the given CDN load balancers
        """
        path = "/api/config/namespaces/{namespace}/cdn_loadbalancers/get_security_config"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSecurityConfigRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "get_cdn_security_config", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a cdn_loadbalancer by name.

        Shape of the CDN loadbalancer specification

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
        path = "/api/config/namespaces/{namespace}/cdn_loadbalancers/{name}"
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
            raise F5XCValidationError("cdn_loadbalancer", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a cdn_loadbalancer.

        Delete the specified cdn_loadbalancer

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/config/namespaces/{namespace}/cdn_loadbalancers/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def get_cdn_do_s_auto_mitigation_rules(
        self,
        namespace: str,
        name: str,
    ) -> GetDoSAutoMitigationRulesRsp:
        """Get Cdn Do S Auto Mitigation Rules for cdn_loadbalancer.

        Get the corresponding DoS Auto-Mitigation Rules for the given CDN...
        """
        path = "/api/config/namespaces/{namespace}/cdn_loadbalancers/{name}/dos_automitigation_rules"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDoSAutoMitigationRulesRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "get_cdn_do_s_auto_mitigation_rules", e, response) from e

    def delete_cdn_do_s_auto_mitigation_rule(
        self,
        namespace: str,
        name: str,
        dos_automitigation_rule_name: str,
    ) -> DeleteDoSAutoMitigationRuleRsp:
        """Delete Cdn Do S Auto Mitigation Rule for cdn_loadbalancer.

        Delete the corresponding DoS Auto-Mitigation Rule for the given CDN...
        """
        path = "/api/config/namespaces/{namespace}/cdn_loadbalancers/{name}/dos_automitigation_rules/{dos_automitigation_rule_name}"
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
            raise F5XCValidationError("cdn_loadbalancer", "delete_cdn_do_s_auto_mitigation_rule", e, response) from e

    def subscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> SubscribeResponse:
        """Subscribe for cdn_loadbalancer.

        Subscribe to CDN Loadbalancer
        """
        path = "/api/cdn/namespaces/system/lilac-cdn/addon/subscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "subscribe", e, response) from e

    def unsubscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> UnsubscribeResponse:
        """Unsubscribe for cdn_loadbalancer.

        Unsubscribe to CDN Loadbalancer
        """
        path = "/api/cdn/namespaces/system/lilac-cdn/addon/unsubscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UnsubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "unsubscribe", e, response) from e

    def cdn_access_logs(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> CDNLogResponse:
        """Cdn Access Logs for cdn_loadbalancer.

        Retrieve CDN Load-Balancer Access logs
        """
        path = "/api/cdn/namespaces/{namespace}/cdn_loadbalancer/access_logs"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CDNLogResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "cdn_access_logs", e, response) from e

    def cdn_access_log_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> CDNLogAggregationResponse:
        """Cdn Access Log Aggregation Query for cdn_loadbalancer.

        Request to get summary/analytics data for the cdn access logs that...
        """
        path = "/api/cdn/namespaces/{namespace}/cdn_loadbalancer/access_logs/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CDNLogAggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "cdn_access_log_aggregation_query", e, response) from e

    def get_service_operation(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetServiceOperationRsp:
        """Get Service Operation for cdn_loadbalancer.

        Get status of an operation command for a given CDN Loadbalancer.
        """
        path = "/api/cdn/namespaces/{namespace}/cdn_loadbalancer/get-service-operation-status"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetServiceOperationRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "get_service_operation", e, response) from e

    def list_service_operations(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListServiceOperationsRsp:
        """List Service Operations for cdn_loadbalancer.

        List of service operations for a given CDN LB
        """
        path = "/api/cdn/namespaces/{namespace}/cdn_loadbalancer/list-service-operations-status"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListServiceOperationsRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "list_service_operations", e, response) from e

    def cdn_metrics(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> LilacCDNMetricsResponse:
        """Cdn Metrics for cdn_loadbalancer.

        Initial metrics request for CDN loadbalancers
        """
        path = "/api/cdn/namespaces/{namespace}/cdn_loadbalancer/metrics"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LilacCDNMetricsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "cdn_metrics", e, response) from e

    def cdn_cache_purge(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> LilacCDNCachePurgeResponse:
        """Cdn Cache Purge for cdn_loadbalancer.

        Initiate Purge for Edge CDN Cache
        """
        path = "/api/cdn/namespaces/{namespace}/cdn_loadbalancer/{name}/cache-purge"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LilacCDNCachePurgeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cdn_loadbalancer", "cdn_cache_purge", e, response) from e

