"""ViewInternal resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.view_internal.models import *
    from f5xc_py_substrate.resources.view_internal.resource import ViewInternalResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ViewInternalResource":
        from f5xc_py_substrate.resources.view_internal.resource import ViewInternalResource
        return ViewInternalResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.view_internal.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.view_internal' has no attribute '{name}'")


__all__ = [
    "ViewInternalResource",
    "ViewRefType",
    "GlobalSpecType",
    "GetResponse",
    "Spec",
]
