"""Connectivity resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.connectivity.models import *
    from f5xc_py_substrate.resources.connectivity.resource import ConnectivityResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ConnectivityResource":
        from f5xc_py_substrate.resources.connectivity.resource import ConnectivityResource
        return ConnectivityResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.connectivity.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.connectivity' has no attribute '{name}'")


__all__ = [
    "ConnectivityResource",
    "Id",
    "TrendValue",
    "MetricValue",
    "HealthscoreTypeData",
    "HealthscoreData",
    "MetricFeatureData",
    "EdgeMetricData",
    "EdgeData",
    "HealthscoreSelector",
    "EdgeMetricSelector",
    "EdgeFieldSelector",
    "EdgeRequest",
    "EdgeResponse",
    "NodeMetricSelector",
    "NodeFieldSelector",
    "FieldSelector",
    "LabelFilter",
    "NodeInstanceMetricData",
    "NodeInstanceData",
    "NodeInterfaceMetricData",
    "NodeInterfaceData",
    "NodeMetricData",
    "NodeData",
    "NodeRequest",
    "NodeResponse",
    "Request",
    "Response",
    "Spec",
]
