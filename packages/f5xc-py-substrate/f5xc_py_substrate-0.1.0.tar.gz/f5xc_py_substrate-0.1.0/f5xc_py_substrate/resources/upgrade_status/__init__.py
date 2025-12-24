"""UpgradeStatus resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.upgrade_status.models import *
    from f5xc_py_substrate.resources.upgrade_status.resource import UpgradeStatusResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "UpgradeStatusResource":
        from f5xc_py_substrate.resources.upgrade_status.resource import UpgradeStatusResource
        return UpgradeStatusResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.upgrade_status.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.upgrade_status' has no attribute '{name}'")


__all__ = [
    "UpgradeStatusResource",
    "InstallResult",
    "ImageDownload",
    "UpgradeProgressCount",
    "Condition",
    "ApplicationObj",
    "StageApplication",
    "StageUpgradeResults",
    "NodeUpgradeResult",
    "NodeLevelUpgrade",
    "OSNodeResult",
    "OSSetup",
    "SiteLevelUpgrade",
    "Validation",
    "SWUpgradeProgress",
    "GlobalSpecType",
    "Checklist",
    "GetUpgradableSWVersionsResponse",
    "GetUpgradeStatusResponse",
    "PreUpgradeCheckResponse",
    "Spec",
]
