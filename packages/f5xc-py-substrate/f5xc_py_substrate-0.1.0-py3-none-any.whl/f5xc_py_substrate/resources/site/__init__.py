"""Site resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.site.models import *
    from f5xc_py_substrate.resources.site.resource import SiteResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SiteResource":
        from f5xc_py_substrate.resources.site.resource import SiteResource
        return SiteResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.site.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.site' has no attribute '{name}'")


__all__ = [
    "SiteResource",
    "TrendValue",
    "MetricValue",
    "MetricFeatureData",
    "MetricData",
    "EdgeMetricData",
    "EdgeMetricSelector",
    "HealthscoreTypeData",
    "HealthscoreData",
    "HealthscoreSelector",
    "NodeMetricData",
    "NodeMetricSelector",
    "EdgeFieldData",
    "Id",
    "EdgeData",
    "EdgeFieldSelector",
    "EdgeRequest",
    "EdgeResponse",
    "NodeFieldSelector",
    "FieldSelector",
    "NodeFieldData",
    "NodeData",
    "GraphData",
    "LabelFilter",
    "NodeRequest",
    "NodeResponse",
    "Request",
    "Response",
    "Spec",
]
