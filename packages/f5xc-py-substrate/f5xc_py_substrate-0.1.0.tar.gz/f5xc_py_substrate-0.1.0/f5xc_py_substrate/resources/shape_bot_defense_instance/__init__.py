"""ShapeBotDefenseInstance resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.shape_bot_defense_instance.models import *
    from f5xc_py_substrate.resources.shape_bot_defense_instance.resource import ShapeBotDefenseInstanceResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ShapeBotDefenseInstanceResource":
        from f5xc_py_substrate.resources.shape_bot_defense_instance.resource import ShapeBotDefenseInstanceResource
        return ShapeBotDefenseInstanceResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.shape_bot_defense_instance.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.shape_bot_defense_instance' has no attribute '{name}'")


__all__ = [
    "ShapeBotDefenseInstanceResource",
    "ObjectRefType",
    "ProtobufAny",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectGetMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "GetSpecType",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "Spec",
]
