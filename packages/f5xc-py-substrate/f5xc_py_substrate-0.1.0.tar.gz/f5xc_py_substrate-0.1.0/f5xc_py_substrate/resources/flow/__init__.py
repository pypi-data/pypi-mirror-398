"""Flow resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.flow.models import *
    from f5xc_py_substrate.resources.flow.resource import FlowResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "FlowResource":
        from f5xc_py_substrate.resources.flow.resource import FlowResource
        return FlowResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.flow.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.flow' has no attribute '{name}'")


__all__ = [
    "FlowResource",
    "AnomalyData",
    "TrendValue",
    "MetricValue",
    "FieldData",
    "AnomalyData",
    "Data",
    "SortBy",
    "SubscribeRequest",
    "SubscribeResponse",
    "SubscriptionStatusResponse",
    "TopFlowAnomaliesRequest",
    "TopFlowAnomaliesResponse",
    "TopTalkersResponse",
    "UnsubscribeRequest",
    "UnsubscribeResponse",
    "Spec",
]
