"""TenantProfile resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.tenant_profile.models import *
    from f5xc_py_substrate.resources.tenant_profile.resource import TenantProfileResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "TenantProfileResource":
        from f5xc_py_substrate.resources.tenant_profile.resource import TenantProfileResource
        return TenantProfileResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.tenant_profile.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.tenant_profile' has no attribute '{name}'")


__all__ = [
    "TenantProfileResource",
    "Empty",
    "ObjectRefType",
    "ProtobufAny",
    "ErrorType",
    "File",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "ObjectRefType",
    "NamespaceRoleType",
    "GroupObjTmplType",
    "CreateSpecType",
    "CreateRequest",
    "GetSpecType",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceSpecType",
    "ReplaceRequest",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
