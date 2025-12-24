"""AppSecurity resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.app_security.models import *
    from f5xc_py_substrate.resources.app_security.resource import AppSecurityResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AppSecurityResource":
        from f5xc_py_substrate.resources.app_security.resource import AppSecurityResource
        return AppSecurityResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.app_security.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.app_security' has no attribute '{name}'")


__all__ = [
    "AppSecurityResource",
    "GetSuggestedAPIEndpointProtectionRuleReq",
    "Empty",
    "APIProtectionRuleAction",
    "HttpMethodMatcherType",
    "AsnMatchList",
    "ObjectRefType",
    "AsnMatcherType",
    "LabelSelectorType",
    "IpMatcherType",
    "PrefixMatchList",
    "IPThreatCategoryListType",
    "TlsFingerprintMatcherType",
    "ClientMatcher",
    "MessageMetaType",
    "MatcherType",
    "CookieMatcherType",
    "HeaderMatcherType",
    "JWTClaimMatcherType",
    "QueryParameterMatcherType",
    "RequestMatcher",
    "APIEndpointProtectionRule",
    "GetSuggestedAPIEndpointProtectionRuleRsp",
    "HeaderMatcherType",
    "HttpHeaderMatcherList",
    "SimpleClientSrcRule",
    "GetSuggestedBlockClientRuleRsp",
    "JA4TlsFingerprintMatcherType",
    "DDoSClientSource",
    "DDoSMitigationRule",
    "GetSuggestedDDoSMitigtionRuleRsp",
    "GetSuggestedOasValidationRuleReq",
    "ApiEndpointDetails",
    "FallThroughRule",
    "CustomFallThroughMode",
    "OpenApiFallThroughMode",
    "ValidationSettingForQueryParameters",
    "ValidationPropertySetting",
    "OpenApiValidationCommonSettings",
    "OpenApiValidationModeActiveResponse",
    "OpenApiValidationModeActive",
    "OpenApiValidationMode",
    "OpenApiValidationAllSpecEndpointsSettings",
    "OpenApiValidationRule",
    "GetSuggestedOasValidationRuleRsp",
    "GetSuggestedRateLimitRuleReq",
    "ObjectRefType",
    "InlineRateLimiter",
    "ApiEndpointRule",
    "GetSuggestedRateLimitRuleRsp",
    "GetSuggestedSensitiveDataRuleReq",
    "BodySectionMaskingOptions",
    "SensitiveDataTypes",
    "GetSuggestedSensitiveDataRuleRsp",
    "GetSuggestedTrustClientRuleRsp",
    "AppFirewallAttackTypeContext",
    "BotNameContext",
    "AppFirewallSignatureContext",
    "AppFirewallViolationContext",
    "AppFirewallDetectionControl",
    "SimpleWafExclusionRule",
    "GetSuggestedWAFExclusionRuleRsp",
    "RequestData",
    "SecurityEventsData",
    "LoadbalancerData",
    "SearchLoadBalancersResponse",
    "SecurityEventsAggregationResponse",
    "SecurityMetricLabelFilter",
    "SecurityEventsCountRequest",
    "SecurityEventsId",
    "SecurityMetricValue",
    "SecurityEventsCounter",
    "SecurityEventsCountResponse",
    "SecurityEventsResponse",
    "SecurityEventsScrollRequest",
    "SecurityIncidentsAggregationRequest",
    "SecurityIncidentsAggregationResponse",
    "SecurityIncidentsRequest",
    "SecurityIncidentsResponse",
    "SecurityIncidentsScrollRequest",
    "SuspiciousUserLogsAggregationRequest",
    "SuspiciousUserLogsAggregationResponse",
    "SuspiciousUserLogsRequest",
    "SuspiciousUserLogsResponse",
    "SuspiciousUserLogsScrollRequest",
    "ThreatCampaign",
    "Spec",
]
