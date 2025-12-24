"""AppSecurity resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.app_security.models import (
    GetSuggestedAPIEndpointProtectionRuleReq,
    Empty,
    APIProtectionRuleAction,
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
    MessageMetaType,
    MatcherType,
    CookieMatcherType,
    HeaderMatcherType,
    JWTClaimMatcherType,
    QueryParameterMatcherType,
    RequestMatcher,
    APIEndpointProtectionRule,
    GetSuggestedAPIEndpointProtectionRuleRsp,
    HeaderMatcherType,
    HttpHeaderMatcherList,
    SimpleClientSrcRule,
    GetSuggestedBlockClientRuleRsp,
    JA4TlsFingerprintMatcherType,
    DDoSClientSource,
    DDoSMitigationRule,
    GetSuggestedDDoSMitigtionRuleRsp,
    GetSuggestedOasValidationRuleReq,
    ApiEndpointDetails,
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
    GetSuggestedOasValidationRuleRsp,
    GetSuggestedRateLimitRuleReq,
    ObjectRefType,
    InlineRateLimiter,
    ApiEndpointRule,
    GetSuggestedRateLimitRuleRsp,
    GetSuggestedSensitiveDataRuleReq,
    BodySectionMaskingOptions,
    SensitiveDataTypes,
    GetSuggestedSensitiveDataRuleRsp,
    GetSuggestedTrustClientRuleRsp,
    AppFirewallAttackTypeContext,
    BotNameContext,
    AppFirewallSignatureContext,
    AppFirewallViolationContext,
    AppFirewallDetectionControl,
    SimpleWafExclusionRule,
    GetSuggestedWAFExclusionRuleRsp,
    RequestData,
    SecurityEventsData,
    LoadbalancerData,
    SearchLoadBalancersResponse,
    SecurityEventsAggregationResponse,
    SecurityMetricLabelFilter,
    SecurityEventsCountRequest,
    SecurityEventsId,
    SecurityMetricValue,
    SecurityEventsCounter,
    SecurityEventsCountResponse,
    SecurityEventsResponse,
    SecurityEventsScrollRequest,
    SecurityIncidentsAggregationRequest,
    SecurityIncidentsAggregationResponse,
    SecurityIncidentsRequest,
    SecurityIncidentsResponse,
    SecurityIncidentsScrollRequest,
    SuspiciousUserLogsAggregationRequest,
    SuspiciousUserLogsAggregationResponse,
    SuspiciousUserLogsRequest,
    SuspiciousUserLogsResponse,
    SuspiciousUserLogsScrollRequest,
    ThreatCampaign,
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


class AppSecurityResource:
    """API methods for app_security.

    API to create API endpoint protection rule suggestion from App...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.app_security.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def security_events_query_all_namespaces(
        self,
        body: dict[str, Any] | None = None,
    ) -> SecurityEventsResponse:
        """Security Events Query All Namespaces for app_security.

        Get security events for the given namespace. For `system` namespace,...
        """
        path = "/api/data/namespaces/system/app_security/all_ns_events"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityEventsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_events_query_all_namespaces", e, response) from e

    def security_events_aggregation_query_all_namespaces(
        self,
        body: dict[str, Any] | None = None,
    ) -> SecurityEventsAggregationResponse:
        """Security Events Aggregation Query All Namespaces for app_security.

        Get summary/aggregation data for security events in the given...
        """
        path = "/api/data/namespaces/system/app_security/all_ns_events/aggregation"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityEventsAggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_events_aggregation_query_all_namespaces", e, response) from e

    def search_load_balancers_all_namespaces(
        self,
        body: dict[str, Any] | None = None,
    ) -> SearchLoadBalancersResponse:
        """Search Load Balancers All Namespaces for app_security.

        Get list of virtual hosts matching label filter
        """
        path = "/api/data/namespaces/system/app_security/all_ns_search/loadbalancers"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SearchLoadBalancersResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "search_load_balancers_all_namespaces", e, response) from e

    def security_events_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SecurityEventsResponse:
        """Security Events Query for app_security.

        Get security events for the given namespace. For `system` namespace,...
        """
        path = "/api/data/namespaces/{namespace}/app_security/events"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityEventsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_events_query", e, response) from e

    def security_events_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SecurityEventsAggregationResponse:
        """Security Events Aggregation Query for app_security.

        Get summary/aggregation data for security events in the given...
        """
        path = "/api/data/namespaces/{namespace}/app_security/events/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityEventsAggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_events_aggregation_query", e, response) from e

    def security_events_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> SecurityEventsResponse:
        """Security Events Scroll Query for app_security.

        Scroll request is used to fetch large number of security events in...
        """
        path = "/api/data/namespaces/{namespace}/app_security/events/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityEventsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_events_scroll_query", e, response) from e

    def security_events_scroll_query_2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SecurityEventsResponse:
        """Security Events Scroll Query 2 for app_security.

        Scroll request is used to fetch large number of security events in...
        """
        path = "/api/data/namespaces/{namespace}/app_security/events/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityEventsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_events_scroll_query_2", e, response) from e

    def security_incidents_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SecurityIncidentsResponse:
        """Security Incidents Query for app_security.

        Get security incidents for the given namespace. For `system`...
        """
        path = "/api/data/namespaces/{namespace}/app_security/incidents"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityIncidentsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_incidents_query", e, response) from e

    def security_incidents_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SecurityIncidentsAggregationResponse:
        """Security Incidents Aggregation Query for app_security.

        Get summary/aggregation data for security incidents in the given...
        """
        path = "/api/data/namespaces/{namespace}/app_security/incidents/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityIncidentsAggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_incidents_aggregation_query", e, response) from e

    def security_incidents_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> SecurityIncidentsResponse:
        """Security Incidents Scroll Query for app_security.

        Scroll request is used to fetch large number of security incidents...
        """
        path = "/api/data/namespaces/{namespace}/app_security/incidents/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityIncidentsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_incidents_scroll_query", e, response) from e

    def security_incidents_scroll_query_2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SecurityIncidentsResponse:
        """Security Incidents Scroll Query 2 for app_security.

        Scroll request is used to fetch large number of security incidents...
        """
        path = "/api/data/namespaces/{namespace}/app_security/incidents/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityIncidentsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_incidents_scroll_query_2", e, response) from e

    def security_events_metrics(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SecurityEventsCountResponse:
        """Security Events Metrics for app_security.

        Get the number of security events for a given namespace. Security...
        """
        path = "/api/data/namespaces/{namespace}/app_security/metrics"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityEventsCountResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "security_events_metrics", e, response) from e

    def search_load_balancers(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SearchLoadBalancersResponse:
        """Search Load Balancers for app_security.

        Get list of virtual hosts matching label filter
        """
        path = "/api/data/namespaces/{namespace}/app_security/search/loadbalancers"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SearchLoadBalancersResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "search_load_balancers", e, response) from e

    def suspicious_user_logs_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SuspiciousUserLogsResponse:
        """Suspicious User Logs Query for app_security.

        Get suspicious user logs for the given namespace. For `system`...
        """
        path = "/api/data/namespaces/{namespace}/app_security/suspicious_user_logs"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuspiciousUserLogsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "suspicious_user_logs_query", e, response) from e

    def suspicious_user_logs_aggregation_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SuspiciousUserLogsAggregationResponse:
        """Suspicious User Logs Aggregation Query for app_security.

        Get summary/aggregation data for suspicious user logs in the given...
        """
        path = "/api/data/namespaces/{namespace}/app_security/suspicious_user_logs/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuspiciousUserLogsAggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "suspicious_user_logs_aggregation_query", e, response) from e

    def suspicious_user_logs_scroll_query(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> SuspiciousUserLogsResponse:
        """Suspicious User Logs Scroll Query for app_security.

        Scroll request is used to fetch large number of suspicious user logs...
        """
        path = "/api/data/namespaces/{namespace}/app_security/suspicious_user_logs/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuspiciousUserLogsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "suspicious_user_logs_scroll_query", e, response) from e

    def suspicious_user_logs_scroll_query_2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SuspiciousUserLogsResponse:
        """Suspicious User Logs Scroll Query 2 for app_security.

        Scroll request is used to fetch large number of suspicious user logs...
        """
        path = "/api/data/namespaces/{namespace}/app_security/suspicious_user_logs/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuspiciousUserLogsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "suspicious_user_logs_scroll_query_2", e, response) from e

    def get_suggested_block_client_rule_for_cdn(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedBlockClientRuleRsp:
        """Get Suggested Block Client Rule For Cdn for app_security.

        Suggest blocking SimpleClientSrcRule for a given IP/ASN
        """
        path = "/api/config/namespaces/{namespace}/cdn_loadbalancers/{name}/block_client/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedBlockClientRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_block_client_rule_for_cdn", e, response) from e

    def get_suggested_d_do_s_mitigation_rule_for_cdn(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedDDoSMitigtionRuleRsp:
        """Get Suggested D Do S Mitigation Rule For Cdn for app_security.

        Suggest DDoSMitigatonRule to mitigate a given IP/ASN/Region/TLS
        """
        path = "/api/config/namespaces/{namespace}/cdn_loadbalancers/{name}/ddos_mitigation/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedDDoSMitigtionRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_d_do_s_mitigation_rule_for_cdn", e, response) from e

    def get_suggested_trust_client_rule_for_cdn(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedTrustClientRuleRsp:
        """Get Suggested Trust Client Rule For Cdn for app_security.

        Suggest SimpleClientSrcRule to trust a given IP/ASN
        """
        path = "/api/config/namespaces/{namespace}/cdn_loadbalancers/{name}/trust_client/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedTrustClientRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_trust_client_rule_for_cdn", e, response) from e

    def get_suggested_waf_exclusion_rule_for_cdn(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedWAFExclusionRuleRsp:
        """Get Suggested Waf Exclusion Rule For Cdn for app_security.

        Suggest service policy rule to set up WAF exclusion for a given WAF...
        """
        path = "/api/config/namespaces/{namespace}/cdn_loadbalancers/{name}/waf_exclusion/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedWAFExclusionRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_waf_exclusion_rule_for_cdn", e, response) from e

    def get_suggested_api_endpoint_protection_rule(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedAPIEndpointProtectionRuleRsp:
        """Get Suggested Api Endpoint Protection Rule for app_security.

        Suggest API endpoint protection rule for a given path DEPRECATED....
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/api_endpoint_protection/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedAPIEndpointProtectionRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_api_endpoint_protection_rule", e, response) from e

    def get_suggested_block_client_rule(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedBlockClientRuleRsp:
        """Get Suggested Block Client Rule for app_security.

        Suggest blocking SimpleClientSrcRule for a given IP/ASN
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/block_client/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedBlockClientRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_block_client_rule", e, response) from e

    def get_suggested_sensitive_data_rule(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedSensitiveDataRuleRsp:
        """Get Suggested Sensitive Data Rule for app_security.

        Suggest sensitive data rule for a given path DEPRECATED. use...
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/data_exposure/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedSensitiveDataRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_sensitive_data_rule", e, response) from e

    def get_suggested_d_do_s_mitigation_rule(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedDDoSMitigtionRuleRsp:
        """Get Suggested D Do S Mitigation Rule for app_security.

        Suggest DDoSMitigatonRule to mitigate a given IP/ASN/Region/TLS
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/ddos_mitigation/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedDDoSMitigtionRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_d_do_s_mitigation_rule", e, response) from e

    def get_suggested_oas_validation_rule(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedOasValidationRuleRsp:
        """Get Suggested Oas Validation Rule for app_security.

        Suggest Open API specification validation rule for a given path...
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/oas_validation/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedOasValidationRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_oas_validation_rule", e, response) from e

    def get_suggested_rate_limit_rule(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedRateLimitRuleRsp:
        """Get Suggested Rate Limit Rule for app_security.

        Suggest rate limit rule for a given path DEPRECATED. use...
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/rate_limit/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedRateLimitRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_rate_limit_rule", e, response) from e

    def get_suggested_trust_client_rule(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedTrustClientRuleRsp:
        """Get Suggested Trust Client Rule for app_security.

        Suggest SimpleClientSrcRule to trust a given IP/ASN
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/trust_client/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedTrustClientRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_trust_client_rule", e, response) from e

    def get_suggested_waf_exclusion_rule(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedWAFExclusionRuleRsp:
        """Get Suggested Waf Exclusion Rule for app_security.

        Suggest service policy rule to set up WAF exclusion for a given WAF...
        """
        path = "/api/config/namespaces/{namespace}/http_loadbalancers/{name}/waf_exclusion/suggestion"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedWAFExclusionRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_suggested_waf_exclusion_rule", e, response) from e

    def get_threat_campaign_by_id(
        self,
        id: str,
    ) -> ThreatCampaign:
        """Get Threat Campaign By Id for app_security.

        Get Threat Campaign by ID
        """
        path = "/api/waf/threat_campaign/{id}"
        path = path.replace("{id}", id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ThreatCampaign(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_security", "get_threat_campaign_by_id", e, response) from e

