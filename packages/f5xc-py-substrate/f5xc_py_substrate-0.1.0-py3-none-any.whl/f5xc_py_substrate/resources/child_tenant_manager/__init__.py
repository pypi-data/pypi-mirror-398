"""ChildTenantManager resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.child_tenant_manager.models import *
    from f5xc_py_substrate.resources.child_tenant_manager.resource import ChildTenantManagerResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ChildTenantManagerResource":
        from f5xc_py_substrate.resources.child_tenant_manager.resource import ChildTenantManagerResource
        return ChildTenantManagerResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.child_tenant_manager.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.child_tenant_manager' has no attribute '{name}'")


__all__ = [
    "ChildTenantManagerResource",
    "CustomerInfo",
    "DateRange",
    "CTBannerNotification",
    "ObjectRefType",
    "CTGroupAssignmentType",
    "GlobalSpecType",
    "CRMInfo",
    "GetSpecType",
    "ObjectGetMetaType",
    "ViewRefType",
    "ConditionType",
    "StatusMetaType",
    "ObjectRefType",
    "StatusObject",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "SystemObjectGetMetaType",
    "CTListResponseItem",
    "DeleteRequest",
    "ProtobufAny",
    "ErrorType",
    "ListChildTenantsByCTMResp",
    "CTListToCTM",
    "MigrateCTMChildTenantsReq",
    "MigrateCTMChildTenantsResp",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ReplaceResponse",
    "ObjectCreateMetaType",
    "CreateSpecType",
    "CreateRequest",
    "GetSpecType",
    "CreateResponse",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "Spec",
]
