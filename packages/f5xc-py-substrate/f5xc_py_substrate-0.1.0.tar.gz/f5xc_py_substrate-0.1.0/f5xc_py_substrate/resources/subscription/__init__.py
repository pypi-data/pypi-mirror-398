"""Subscription resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.subscription.models import *
    from f5xc_py_substrate.resources.subscription.resource import SubscriptionResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SubscriptionResource":
        from f5xc_py_substrate.resources.subscription.resource import SubscriptionResource
        return SubscriptionResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.subscription.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.subscription' has no attribute '{name}'")


__all__ = [
    "SubscriptionResource",
    "Empty",
    "SubscribeRequest",
    "SubscribeResponse",
    "UnsubscribeRequest",
    "UnsubscribeResponse",
    "Spec",
]
