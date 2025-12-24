"""Scim resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.scim.models import *
    from f5xc_py_substrate.resources.scim.resource import ScimResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ScimResource":
        from f5xc_py_substrate.resources.scim.resource import ScimResource
        return ScimResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.scim.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.scim' has no attribute '{name}'")


__all__ = [
    "ScimResource",
    "ProtobufAny",
    "HttpBody",
    "GroupMembers",
    "Meta",
    "CreateGroupRequest",
    "Email",
    "UserGroup",
    "Name",
    "CreateUserRequest",
    "Filter",
    "Group",
    "ListGroupResources",
    "User",
    "ListUserResponse",
    "PatchOperation",
    "PatchGroupRequest",
    "PatchUserRequest",
    "ResourceMeta",
    "Resource",
    "ResourceTypesResponse",
    "Support",
    "ServiceProviderConfigResponse",
    "Spec",
]
