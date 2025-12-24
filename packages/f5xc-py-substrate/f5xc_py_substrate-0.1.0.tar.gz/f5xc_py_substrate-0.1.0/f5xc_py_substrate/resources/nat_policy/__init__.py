"""NatPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.nat_policy.models import *
    from f5xc_py_substrate.resources.nat_policy.resource import NatPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NatPolicyResource":
        from f5xc_py_substrate.resources.nat_policy.resource import NatPolicyResource
        return NatPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.nat_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.nat_policy' has no attribute '{name}'")


__all__ = [
    "NatPolicyResource",
    "Empty",
    "ObjectRefType",
    "CloudElasticIpRefListType",
    "PrefixStringListType",
    "DynamicPool",
    "ActionType",
    "ObjectCreateMetaType",
    "CloudConnectRefType",
    "PortMatcherType",
    "SegmentRefType",
    "PortConfiguration",
    "VirtualNetworkReferenceType",
    "MatchCriteriaType",
    "NetworkInterfaceRefType",
    "RuleType",
    "SiteReferenceType",
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
