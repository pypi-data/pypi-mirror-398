"""RateLimiterPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.rate_limiter_policy.models import *
    from f5xc_py_substrate.resources.rate_limiter_policy.resource import RateLimiterPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "RateLimiterPolicyResource":
        from f5xc_py_substrate.resources.rate_limiter_policy.resource import RateLimiterPolicyResource
        return RateLimiterPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.rate_limiter_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.rate_limiter_policy' has no attribute '{name}'")


__all__ = [
    "RateLimiterPolicyResource",
    "Empty",
    "ObjectRefType",
    "AsnMatchList",
    "AsnMatcherType",
    "CountryCodeList",
    "HttpMethodMatcherType",
    "IpMatcherType",
    "MatcherType",
    "MatcherTypeBasic",
    "PrefixMatchList",
    "ProtobufAny",
    "ObjectCreateMetaType",
    "MessageMetaType",
    "ObjectRefType",
    "HeaderMatcherType",
    "PathMatcherType",
    "RateLimiterRuleSpec",
    "RateLimiterRule",
    "LabelSelectorType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "DeleteRequest",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
