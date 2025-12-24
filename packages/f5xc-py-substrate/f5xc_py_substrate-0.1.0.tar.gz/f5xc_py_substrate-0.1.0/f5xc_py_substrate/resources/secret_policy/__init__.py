"""SecretPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.secret_policy.models import *
    from f5xc_py_substrate.resources.secret_policy.resource import SecretPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SecretPolicyResource":
        from f5xc_py_substrate.resources.secret_policy.resource import SecretPolicyResource
        return SecretPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.secret_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.secret_policy' has no attribute '{name}'")


__all__ = [
    "SecretPolicyResource",
    "ObjectRefType",
    "MatcherType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "LabelSelectorType",
    "MessageMetaType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
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
    "ListPolicyResponseItem",
    "ListPolicyResponse",
    "ListResponseItem",
    "ListResponse",
    "RecoverRequest",
    "RecoverResponse",
    "ReplaceResponse",
    "SoftDeleteRequest",
    "SoftDeleteResponse",
    "Spec",
]
