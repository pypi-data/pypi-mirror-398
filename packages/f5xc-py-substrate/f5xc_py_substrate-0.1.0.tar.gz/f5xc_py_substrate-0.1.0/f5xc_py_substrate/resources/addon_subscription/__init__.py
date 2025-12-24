"""AddonSubscription resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.addon_subscription.models import *
    from f5xc_py_substrate.resources.addon_subscription.resource import AddonSubscriptionResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AddonSubscriptionResource":
        from f5xc_py_substrate.resources.addon_subscription.resource import AddonSubscriptionResource
        return AddonSubscriptionResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.addon_subscription.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.addon_subscription' has no attribute '{name}'")


__all__ = [
    "AddonSubscriptionResource",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "EmailDL",
    "SupportTicketId",
    "NotificationPreference",
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
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
