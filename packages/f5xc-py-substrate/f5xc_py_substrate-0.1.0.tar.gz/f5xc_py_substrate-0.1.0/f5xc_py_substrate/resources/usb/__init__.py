"""Usb resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.usb.models import *
    from f5xc_py_substrate.resources.usb.resource import UsbResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "UsbResource":
        from f5xc_py_substrate.resources.usb.resource import UsbResource
        return UsbResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.usb.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.usb' has no attribute '{name}'")


__all__ = [
    "UsbResource",
    "USBDevice",
    "Rule",
    "AddRulesRequest",
    "AddRulesResponse",
    "Config",
    "DeleteRulesRequest",
    "DeleteRulesResponse",
    "GetConfigResponse",
    "ListResponse",
    "ListRulesResponse",
    "UpdateConfigRequest",
    "UpdateConfigResponse",
    "Spec",
]
