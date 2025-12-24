"""User resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.user.models import *
    from f5xc_py_substrate.resources.user.resource import UserResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "UserResource":
        from f5xc_py_substrate.resources.user.resource import UserResource
        return UserResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.user.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.user' has no attribute '{name}'")


__all__ = [
    "UserResource",
    "Empty",
    "ProtobufAny",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "NamespaceAccessType",
    "NamespaceRoleType",
    "ObjectMetaType",
    "ObjectRefType",
    "ViewRefType",
    "SystemObjectMetaType",
    "Empty",
    "AcceptTOSRequest",
    "AcceptTOSResponse",
    "NamespacesRoleType",
    "AssignRoleRequest",
    "BillingFeatureIndicator",
    "CascadeDeleteItemType",
    "CascadeDeleteRequest",
    "CascadeDeleteResponse",
    "FeatureFlagType",
    "GetTOSResponse",
    "MSPManaged",
    "GetUserRoleResponse",
    "GlobalSpecType",
    "ListUserRoleResponseItem",
    "ListUserRoleResponse",
    "SpecType",
    "Object",
    "ResetPasswordByAdminRequest",
    "SendPasswordEmailRequest",
    "SendPasswordEmailResponse",
    "GroupResponse",
    "Spec",
]
