"""WafExclusionPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.waf_exclusion_policy.models import *
    from f5xc_py_substrate.resources.waf_exclusion_policy.resource import WafExclusionPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "WafExclusionPolicyResource":
        from f5xc_py_substrate.resources.waf_exclusion_policy.resource import WafExclusionPolicyResource
        return WafExclusionPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.waf_exclusion_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.waf_exclusion_policy' has no attribute '{name}'")


__all__ = [
    "WafExclusionPolicyResource",
    "Empty",
    "ObjectRefType",
    "AppFirewallAttackTypeContext",
    "BotNameContext",
    "AppFirewallSignatureContext",
    "AppFirewallViolationContext",
    "AppFirewallDetectionControl",
    "MessageMetaType",
    "SimpleWafExclusionRule",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateSpecType",
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
    "Spec",
]
