"""UserToken resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.user_token.models import *
    from f5xc_py_substrate.resources.user_token.resource import UserTokenResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "UserTokenResource":
        from f5xc_py_substrate.resources.user_token.resource import UserTokenResource
        return UserTokenResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.user_token.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.user_token' has no attribute '{name}'")


__all__ = [
    "UserTokenResource",
    "GetUserTokenResponse",
    "Spec",
]
