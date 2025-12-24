"""UserGroup resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.user_group.models import *
    from f5xc_py_substrate.resources.user_group.resource import UserGroupResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "UserGroupResource":
        from f5xc_py_substrate.resources.user_group.resource import UserGroupResource
        return UserGroupResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.user_group.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.user_group' has no attribute '{name}'")


__all__ = [
    "UserGroupResource",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "NamespaceRoleType",
    "ObjectGetMetaType",
    "ObjectRefType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "Empty",
    "NamespaceNameIdentifier",
    "AnalyzeForDeletionRequest",
    "AnalyzeForDeletionResponse",
    "GetSpecType",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "Response",
    "ListUserGroupsResponse",
    "Spec",
]
