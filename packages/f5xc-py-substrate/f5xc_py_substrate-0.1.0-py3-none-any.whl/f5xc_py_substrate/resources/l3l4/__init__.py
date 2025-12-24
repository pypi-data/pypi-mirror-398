"""L3l4 resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.l3l4.models import *
    from f5xc_py_substrate.resources.l3l4.resource import L3l4Resource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "L3l4Resource":
        from f5xc_py_substrate.resources.l3l4.resource import L3l4Resource
        return L3l4Resource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.l3l4.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.l3l4' has no attribute '{name}'")


__all__ = [
    "L3l4Resource",
    "L3l4ByApplicationRequest",
    "L3l4L3L4GraphValue",
    "L3l4L3L4Metric",
    "L3l4ByApplicationResponse",
    "L3l4ByMitigationRequest",
    "L3l4ByMitigationResponse",
    "L3l4ByNetworkRequest",
    "L3l4ByNetworkResponse",
    "L3l4ByZoneRequest",
    "L3l4ByZoneResponse",
    "L3l4EventCountRequest",
    "L3l4EventDataPoint",
    "L3l4EventCountResponse",
    "L3l4TopTalker",
    "L3l4TopTalkersRequest",
    "L3l4TopTalkersResponse",
    "Spec",
]
