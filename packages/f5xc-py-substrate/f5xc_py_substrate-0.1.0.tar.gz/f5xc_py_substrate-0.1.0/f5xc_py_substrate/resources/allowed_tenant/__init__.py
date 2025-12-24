"""AllowedTenant resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.allowed_tenant.models import *
    from f5xc_py_substrate.resources.allowed_tenant.resource import AllowedTenantResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AllowedTenantResource":
        from f5xc_py_substrate.resources.allowed_tenant.resource import AllowedTenantResource
        return AllowedTenantResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.allowed_tenant.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.allowed_tenant' has no attribute '{name}'")


__all__ = [
    "AllowedTenantResource",
    "Empty",
    "NsReadWriteAccess",
    "AllowedAccessConfig",
    "DeleteRequest",
    "GetSupportTenantAccessResp",
    "ObjectReplaceMetaType",
    "ObjectRefType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ReplaceResponse",
    "UpdateSupportTenantAccessReq",
    "UpdateSupportTenantAccessResp",
    "ObjectRefType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateSpecType",
    "CreateRequest",
    "GetSpecType",
    "CreateResponse",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "Spec",
]
