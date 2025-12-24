"""EnhancedFirewallPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.enhanced_firewall_policy.models import *
    from f5xc_py_substrate.resources.enhanced_firewall_policy.resource import EnhancedFirewallPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "EnhancedFirewallPolicyResource":
        from f5xc_py_substrate.resources.enhanced_firewall_policy.resource import EnhancedFirewallPolicyResource
        return EnhancedFirewallPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.enhanced_firewall_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.enhanced_firewall_policy' has no attribute '{name}'")


__all__ = [
    "EnhancedFirewallPolicyResource",
    "ObjectCreateMetaType",
    "Empty",
    "PrefixListType",
    "NetworkPolicyRuleAdvancedAction",
    "ApplicationsType",
    "AwsVpcList",
    "ObjectRefType",
    "IpPrefixSetRefType",
    "LabelSelectorType",
    "PrefixStringListType",
    "ObjectRefType",
    "ServiceActionType",
    "LabelMatcherType",
    "MessageMetaType",
    "ProtocolPortType",
    "RuleType",
    "RuleListType",
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
    "HitsId",
    "TrendValue",
    "MetricValue",
    "Hits",
    "MetricLabelFilter",
    "HitsRequest",
    "HitsResponse",
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
