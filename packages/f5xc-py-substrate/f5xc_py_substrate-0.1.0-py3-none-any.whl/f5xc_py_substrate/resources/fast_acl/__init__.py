"""FastAcl resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.fast_acl.models import *
    from f5xc_py_substrate.resources.fast_acl.resource import FastAclResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "FastAclResource":
        from f5xc_py_substrate.resources.fast_acl.resource import FastAclResource
        return FastAclResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.fast_acl.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.fast_acl' has no attribute '{name}'")


__all__ = [
    "FastAclResource",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "Empty",
    "ObjectRefType",
    "PolicerRefType",
    "ProtocolPolicerRefType",
    "RuleAction",
    "IpPrefixSetRefType",
    "MessageMetaType",
    "PortValueType",
    "PrefixListType",
    "FastACLRuleType",
    "SelectedTenantVIPsType",
    "ReACLType",
    "SiteACLType",
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
    "FastACLHitsId",
    "TrendValue",
    "MetricValue",
    "FastACLHits",
    "FastACLMetricLabelFilter",
    "FastACLHitsRequest",
    "FastACLHitsResponse",
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
