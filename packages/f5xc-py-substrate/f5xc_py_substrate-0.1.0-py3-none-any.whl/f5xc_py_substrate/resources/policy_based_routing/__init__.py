"""PolicyBasedRouting resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.policy_based_routing.models import *
    from f5xc_py_substrate.resources.policy_based_routing.resource import PolicyBasedRoutingResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "PolicyBasedRoutingResource":
        from f5xc_py_substrate.resources.policy_based_routing.resource import PolicyBasedRoutingResource
        return PolicyBasedRoutingResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.policy_based_routing.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.policy_based_routing' has no attribute '{name}'")


__all__ = [
    "PolicyBasedRoutingResource",
    "DomainType",
    "DomainListType",
    "Empty",
    "URLType",
    "URLListType",
    "ObjectRefType",
    "ApplicationsType",
    "ProtocolPortType",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "LabelSelectorType",
    "MessageMetaType",
    "PrefixStringListType",
    "ForwardProxyPBRRuleType",
    "ForwardProxyPBRType",
    "IpPrefixSetRefType",
    "NetworkPBRRuleType",
    "NetworkPBRType",
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
