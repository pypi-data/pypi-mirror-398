"""CdnCacheRule resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.cdn_cache_rule.models import *
    from f5xc_py_substrate.resources.cdn_cache_rule.resource import CdnCacheRuleResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "CdnCacheRuleResource":
        from f5xc_py_substrate.resources.cdn_cache_rule.resource import CdnCacheRuleResource
        return CdnCacheRuleResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.cdn_cache_rule.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.cdn_cache_rule' has no attribute '{name}'")


__all__ = [
    "CdnCacheRuleResource",
    "Empty",
    "CacheTTLEnableProps",
    "CacheEligibleOptions",
    "CacheOperator",
    "CacheHeaderMatcherType",
    "CacheCookieMatcherType",
    "CDNPathMatcherType",
    "CacheQueryParameterMatcherType",
    "CDNCacheRuleExpression",
    "CDNCacheRuleExpressionList",
    "CDNCacheRule",
    "ObjectCreateMetaType",
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
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
