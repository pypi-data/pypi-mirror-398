"""FastAclRule resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.fast_acl_rule.models import *
    from f5xc_py_substrate.resources.fast_acl_rule.resource import FastAclRuleResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "FastAclRuleResource":
        from f5xc_py_substrate.resources.fast_acl_rule.resource import FastAclRuleResource
        return FastAclRuleResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.fast_acl_rule.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.fast_acl_rule' has no attribute '{name}'")


__all__ = [
    "FastAclRuleResource",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "PolicerRefType",
    "ProtocolPolicerRefType",
    "Action",
    "IpPrefixSetRefType",
    "Empty",
    "PortValueType",
    "PrefixListType",
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
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
