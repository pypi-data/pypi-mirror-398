"""BotNetworkPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.bot_network_policy.models import *
    from f5xc_py_substrate.resources.bot_network_policy.resource import BotNetworkPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "BotNetworkPolicyResource":
        from f5xc_py_substrate.resources.bot_network_policy.resource import BotNetworkPolicyResource
        return BotNetworkPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.bot_network_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.bot_network_policy' has no attribute '{name}'")


__all__ = [
    "BotNetworkPolicyResource",
    "Empty",
    "ManualRoutingDetail",
    "ManualRoutings",
    "UpstreamRoutingDetail",
    "UpstreamRoutings",
    "NetworkPolicyContent",
    "PolicyVersion",
    "ReplaceSpecType",
    "CustomReplaceRequest",
    "CustomReplaceResponse",
    "GetContentResponse",
    "Policy",
    "GetPoliciesAndVersionsListResponse",
    "ObjectRefType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "ReplaceRequest",
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
    "PolicyVersionsResponse",
    "ReplaceResponse",
    "Spec",
]
