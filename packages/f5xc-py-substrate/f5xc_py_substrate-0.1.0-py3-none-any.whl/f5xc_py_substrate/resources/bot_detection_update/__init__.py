"""BotDetectionUpdate resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.bot_detection_update.models import *
    from f5xc_py_substrate.resources.bot_detection_update.resource import BotDetectionUpdateResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "BotDetectionUpdateResource":
        from f5xc_py_substrate.resources.bot_detection_update.resource import BotDetectionUpdateResource
        return BotDetectionUpdateResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.bot_detection_update.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.bot_detection_update' has no attribute '{name}'")


__all__ = [
    "BotDetectionUpdateResource",
    "BotInfrastructure",
    "TimeRange",
    "DeploymentRange",
    "BotDetectionUpdate",
    "DownloadBotDetectionUpdatesReleaseNotesResponse",
    "GetBotDetectionUpdatesResponse",
    "Spec",
]
