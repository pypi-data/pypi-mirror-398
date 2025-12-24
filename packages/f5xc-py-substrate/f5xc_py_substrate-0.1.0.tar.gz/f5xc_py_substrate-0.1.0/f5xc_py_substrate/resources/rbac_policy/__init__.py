"""RbacPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.rbac_policy.models import *
    from f5xc_py_substrate.resources.rbac_policy.resource import RbacPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "RbacPolicyResource":
        from f5xc_py_substrate.resources.rbac_policy.resource import RbacPolicyResource
        return RbacPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.rbac_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.rbac_policy' has no attribute '{name}'")


__all__ = [
    "RbacPolicyResource",
    "ObjectRefType",
    "ProtobufAny",
    "ObjectGetMetaType",
    "RBACPolicyRuleType",
    "GetSpecType",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "GetResponse",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "Spec",
]
