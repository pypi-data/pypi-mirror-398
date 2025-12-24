"""Waf resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.waf.models import *
    from f5xc_py_substrate.resources.waf.resource import WafResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "WafResource":
        from f5xc_py_substrate.resources.waf.resource import WafResource
        return WafResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.waf.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.waf' has no attribute '{name}'")


__all__ = [
    "WafResource",
    "TrendValue",
    "MetricValue",
    "RuleHitsId",
    "RuleHitsCounter",
    "RuleHitsCountResponse",
    "SecurityEventsId",
    "SecurityEventsCounter",
    "SecurityEventsCountResponse",
    "Spec",
]
