"""AlertPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.alert_policy.models import *
    from f5xc_py_substrate.resources.alert_policy.resource import AlertPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AlertPolicyResource":
        from f5xc_py_substrate.resources.alert_policy.resource import AlertPolicyResource
        return AlertPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.alert_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.alert_policy' has no attribute '{name}'")


__all__ = [
    "AlertPolicyResource",
    "Match",
    "MatchRequest",
    "MatchResponse",
    "ObjectCreateMetaType",
    "CustomGroupBy",
    "Empty",
    "NotificationParameters",
    "ObjectRefType",
    "LabelMatcher",
    "CustomMatcher",
    "GroupMatcher",
    "SeverityMatcher",
    "Route",
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
