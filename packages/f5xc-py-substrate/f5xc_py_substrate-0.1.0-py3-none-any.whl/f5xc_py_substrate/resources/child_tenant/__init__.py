"""ChildTenant resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.child_tenant.models import *
    from f5xc_py_substrate.resources.child_tenant.resource import ChildTenantResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ChildTenantResource":
        from f5xc_py_substrate.resources.child_tenant.resource import ChildTenantResource
        return ChildTenantResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.child_tenant.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.child_tenant' has no attribute '{name}'")


__all__ = [
    "ChildTenantResource",
    "CustomerInfo",
    "DeleteRequest",
    "ObjectRefType",
    "GroupAssignmentType",
    "LinkRefType",
    "AllTenantsTicketSummary",
    "CTTicketSummary",
    "SupportTicketInfo",
    "AccessInfo",
    "ListChildTenantsResp",
    "CTListToCTM",
    "MigrateChildTenantsReq",
    "ProtobufAny",
    "ErrorType",
    "MigrateChildTenantsResp",
    "ObjectReplaceMetaType",
    "GlobalSpecType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ReplaceResponse",
    "AttachmentType",
    "CloseResponse",
    "CommentResponse",
    "CommentType",
    "EscalationResponse",
    "PriorityResponse",
    "ReopenResponse",
    "ObjectRefType",
    "CRMInfo",
    "ConditionType",
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
    "ListResponseItem",
    "CommentRequest",
    "PriorityRequest",
    "GetByTpIdResponse",
    "ListSupportTicketResponse",
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
