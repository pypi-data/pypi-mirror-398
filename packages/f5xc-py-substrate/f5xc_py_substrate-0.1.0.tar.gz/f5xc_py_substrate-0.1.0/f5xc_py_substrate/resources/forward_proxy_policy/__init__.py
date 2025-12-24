"""ForwardProxyPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.forward_proxy_policy.models import *
    from f5xc_py_substrate.resources.forward_proxy_policy.resource import ForwardProxyPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ForwardProxyPolicyResource":
        from f5xc_py_substrate.resources.forward_proxy_policy.resource import ForwardProxyPolicyResource
        return ForwardProxyPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.forward_proxy_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.forward_proxy_policy' has no attribute '{name}'")


__all__ = [
    "ForwardProxyPolicyResource",
    "ObjectCreateMetaType",
    "Empty",
    "L4DestType",
    "URLType",
    "DomainType",
    "ForwardProxySimpleRuleType",
    "ObjectRefType",
    "LabelSelectorType",
    "AsnMatchList",
    "PrefixStringListType",
    "URLListType",
    "MessageMetaType",
    "PortMatcherType",
    "DomainListType",
    "URLCategoryListType",
    "ForwardProxyAdvancedRuleType",
    "ForwardProxyRuleListType",
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
    "HitsId",
    "TrendValue",
    "MetricValue",
    "Hits",
    "MetricLabelFilter",
    "HitsRequest",
    "HitsResponse",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
