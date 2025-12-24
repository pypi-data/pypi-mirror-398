"""RuleSuggestion resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.rule_suggestion.models import *
    from f5xc_py_substrate.resources.rule_suggestion.resource import RuleSuggestionResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "RuleSuggestionResource":
        from f5xc_py_substrate.resources.rule_suggestion.resource import RuleSuggestionResource
        return RuleSuggestionResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.rule_suggestion.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.rule_suggestion' has no attribute '{name}'")


__all__ = [
    "RuleSuggestionResource",
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
    "ApiEndpointDetails",
    "ObjectRefType",
    "InlineRateLimiter",
    "ApiEndpointRule",
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
    "BodySectionMaskingOptions",
    "SensitiveDataTypes",
    "GetSuggestedAPIEndpointProtectionRuleReq",
    "GetSuggestedAPIEndpointProtectionRuleRsp",
    "GetSuggestedOasValidationRuleReq",
    "GetSuggestedOasValidationRuleRsp",
    "GetSuggestedRateLimitRuleReq",
    "GetSuggestedRateLimitRuleRsp",
    "GetSuggestedSensitiveDataRuleReq",
    "GetSuggestedSensitiveDataRuleRsp",
    "Spec",
]
