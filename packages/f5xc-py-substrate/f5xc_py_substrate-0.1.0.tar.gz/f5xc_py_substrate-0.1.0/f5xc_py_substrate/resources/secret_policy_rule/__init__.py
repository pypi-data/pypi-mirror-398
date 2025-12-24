"""SecretPolicyRule resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.secret_policy_rule.models import *
    from f5xc_py_substrate.resources.secret_policy_rule.resource import SecretPolicyRuleResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SecretPolicyRuleResource":
        from f5xc_py_substrate.resources.secret_policy_rule.resource import SecretPolicyRuleResource
        return SecretPolicyRuleResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.secret_policy_rule.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.secret_policy_rule' has no attribute '{name}'")


__all__ = [
    "SecretPolicyRuleResource",
    "ObjectRefType",
    "MatcherTypeBasic",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "LabelSelectorType",
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
