"""ImplicitLabel resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.implicit_label.models import *
    from f5xc_py_substrate.resources.implicit_label.resource import ImplicitLabelResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ImplicitLabelResource":
        from f5xc_py_substrate.resources.implicit_label.resource import ImplicitLabelResource
        return ImplicitLabelResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.implicit_label.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.implicit_label' has no attribute '{name}'")


__all__ = [
    "ImplicitLabelResource",
    "LabelType",
    "GetResponse",
    "Spec",
]
