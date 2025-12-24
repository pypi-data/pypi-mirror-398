"""NetworkPolicyView resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.network_policy_view.models import *
    from f5xc_py_substrate.resources.network_policy_view.resource import NetworkPolicyViewResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NetworkPolicyViewResource":
        from f5xc_py_substrate.resources.network_policy_view.resource import NetworkPolicyViewResource
        return NetworkPolicyViewResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.network_policy_view.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.network_policy_view' has no attribute '{name}'")


__all__ = [
    "NetworkPolicyViewResource",
    "Empty",
    "ObjectRefType",
    "ApplicationsType",
    "LabelSelectorType",
    "PrefixStringListType",
    "EndpointChoiceType",
    "NetworkPolicyRuleAdvancedAction",
    "IpPrefixSetRefType",
    "LabelMatcherType",
    "MessageMetaType",
    "ProtocolPortType",
    "NetworkPolicyRuleType",
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
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "NetworkPolicyHitsId",
    "TrendValue",
    "MetricValue",
    "NetworkPolicyHits",
    "NetworkPolicyMetricLabelFilter",
    "NetworkPolicyHitsRequest",
    "NetworkPolicyHitsResponse",
    "ReplaceResponse",
    "Spec",
]
