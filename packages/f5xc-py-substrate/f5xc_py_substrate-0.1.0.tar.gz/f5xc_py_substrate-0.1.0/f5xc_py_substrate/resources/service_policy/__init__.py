"""ServicePolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.service_policy.models import *
    from f5xc_py_substrate.resources.service_policy.resource import ServicePolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ServicePolicyResource":
        from f5xc_py_substrate.resources.service_policy.resource import ServicePolicyResource
        return ServicePolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.service_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.service_policy' has no attribute '{name}'")


__all__ = [
    "ServicePolicyResource",
    "Empty",
    "ObjectRefType",
    "AppFirewallAttackTypeContext",
    "BotNameContext",
    "AppFirewallSignatureContext",
    "AppFirewallViolationContext",
    "AppFirewallDetectionControl",
    "MatcherType",
    "ArgMatcherType",
    "AsnMatchList",
    "AsnMatcherType",
    "CookieMatcherType",
    "HttpMethodMatcherType",
    "IpMatcherType",
    "JA4TlsFingerprintMatcherType",
    "JWTClaimMatcherType",
    "MatcherTypeBasic",
    "ModifyAction",
    "PrefixMatchList",
    "RequestConstraintType",
    "ObjectRefType",
    "SegmentRefList",
    "SegmentPolicyType",
    "StringMatcherType",
    "TlsFingerprintMatcherType",
    "WafAction",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "LabelMatcherType",
    "LabelSelectorType",
    "MessageMetaType",
    "TrendValue",
    "MetricValue",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "BotAction",
    "HeaderMatcherType",
    "PathMatcherType",
    "PortMatcherType",
    "QueryParameterMatcherType",
    "PrefixStringListType",
    "SourceList",
    "IPThreatCategoryListType",
    "GlobalSpecType",
    "Rule",
    "RuleList",
    "CreateSpecType",
    "LegacyRuleList",
    "GetSpecType",
    "ReplaceSpecType",
    "CreateRequest",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceRequest",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "HitsId",
    "Hits",
    "HitsResponse",
    "Spec",
]
