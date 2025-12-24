"""NetworkPolicySet resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.network_policy_set.models import *
    from f5xc_py_substrate.resources.network_policy_set.resource import NetworkPolicySetResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NetworkPolicySetResource":
        from f5xc_py_substrate.resources.network_policy_set.resource import NetworkPolicySetResource
        return NetworkPolicySetResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.network_policy_set.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.network_policy_set' has no attribute '{name}'")


__all__ = [
    "NetworkPolicySetResource",
    "ObjectRefType",
    "ObjectGetMetaType",
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
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "Spec",
]
