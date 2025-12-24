"""Plan resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.plan.models import *
    from f5xc_py_substrate.resources.plan.resource import PlanResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "PlanResource":
        from f5xc_py_substrate.resources.plan.resource import PlanResource
        return PlanResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.plan.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.plan' has no attribute '{name}'")


__all__ = [
    "PlanResource",
    "AddonServiceDetails",
    "GlobalSpecType",
    "UsagePlanTransitionFlow",
    "Internal",
    "LocalizedPlan",
    "ListUsagePlansRsp",
    "Spec",
]
