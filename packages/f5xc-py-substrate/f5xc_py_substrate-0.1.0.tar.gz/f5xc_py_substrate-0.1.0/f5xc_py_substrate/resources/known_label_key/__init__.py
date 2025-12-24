"""KnownLabelKey resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.known_label_key.models import *
    from f5xc_py_substrate.resources.known_label_key.resource import KnownLabelKeyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "KnownLabelKeyResource":
        from f5xc_py_substrate.resources.known_label_key.resource import KnownLabelKeyResource
        return KnownLabelKeyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.known_label_key.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.known_label_key' has no attribute '{name}'")


__all__ = [
    "KnownLabelKeyResource",
    "CreateRequest",
    "LabelKeyType",
    "CreateResponse",
    "DeleteRequest",
    "DeleteResponse",
    "GetResponse",
    "Spec",
]
