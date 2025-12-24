"""NetworkFirewall resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.network_firewall.models import *
    from f5xc_py_substrate.resources.network_firewall.resource import NetworkFirewallResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NetworkFirewallResource":
        from f5xc_py_substrate.resources.network_firewall.resource import NetworkFirewallResource
        return NetworkFirewallResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.network_firewall.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.network_firewall' has no attribute '{name}'")


__all__ = [
    "NetworkFirewallResource",
    "Empty",
    "ObjectRefType",
    "ObjectRefType",
    "ActiveEnhancedFirewallPoliciesType",
    "ActiveFastACLsType",
    "ActiveForwardProxyPoliciesType",
    "ActiveNetworkPoliciesType",
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
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "Status",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
