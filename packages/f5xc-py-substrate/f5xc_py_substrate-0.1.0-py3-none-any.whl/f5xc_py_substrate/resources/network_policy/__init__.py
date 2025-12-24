"""NetworkPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.network_policy.models import *
    from f5xc_py_substrate.resources.network_policy.resource import NetworkPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NetworkPolicyResource":
        from f5xc_py_substrate.resources.network_policy.resource import NetworkPolicyResource
        return NetworkPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.network_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.network_policy' has no attribute '{name}'")


__all__ = [
    "NetworkPolicyResource",
    "Empty",
    "ObjectRefType",
    "ApplicationsType",
    "ObjectCreateMetaType",
    "LabelSelectorType",
    "PrefixStringListType",
    "EndpointChoiceType",
    "RuleAdvancedAction",
    "IpPrefixSetRefType",
    "LabelMatcherType",
    "MessageMetaType",
    "ProtocolPortType",
    "RuleType",
    "RuleChoice",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "LegacyNetworkPolicyRuleChoice",
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
    "HitsId",
    "TrendValue",
    "MetricValue",
    "Hits",
    "MetricLabelFilter",
    "HitsRequest",
    "HitsResponse",
    "ReplaceResponse",
    "Spec",
]
