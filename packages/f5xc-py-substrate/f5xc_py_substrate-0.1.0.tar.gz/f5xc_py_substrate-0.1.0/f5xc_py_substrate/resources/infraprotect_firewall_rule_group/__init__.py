"""InfraprotectFirewallRuleGroup resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.infraprotect_firewall_rule_group.models import *
    from f5xc_py_substrate.resources.infraprotect_firewall_rule_group.resource import InfraprotectFirewallRuleGroupResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "InfraprotectFirewallRuleGroupResource":
        from f5xc_py_substrate.resources.infraprotect_firewall_rule_group.resource import InfraprotectFirewallRuleGroupResource
        return InfraprotectFirewallRuleGroupResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.infraprotect_firewall_rule_group.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.infraprotect_firewall_rule_group' has no attribute '{name}'")


__all__ = [
    "InfraprotectFirewallRuleGroupResource",
    "ObjectCreateMetaType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "ObjectRefType",
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
