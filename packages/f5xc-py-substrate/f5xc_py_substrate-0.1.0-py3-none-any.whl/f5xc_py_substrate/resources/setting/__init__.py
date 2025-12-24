"""Setting resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.setting.models import *
    from f5xc_py_substrate.resources.setting.resource import SettingResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SettingResource":
        from f5xc_py_substrate.resources.setting.resource import SettingResource
        return SettingResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.setting.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.setting' has no attribute '{name}'")


__all__ = [
    "SettingResource",
    "ProtobufAny",
    "HttpBody",
    "InitialAccess",
    "Notification",
    "NotificationList",
    "PersonaPreferences",
    "SetViewPreferenceRequest",
    "UpdateImageRequest",
    "UserSession",
    "UserSessionList",
    "UserSettingsRequest",
    "UserSettingsResponse",
    "ViewPreference",
    "Empty",
    "Spec",
]
