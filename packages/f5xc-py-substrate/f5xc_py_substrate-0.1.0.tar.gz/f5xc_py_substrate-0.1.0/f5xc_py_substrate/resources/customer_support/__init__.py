"""CustomerSupport resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.customer_support.models import *
    from f5xc_py_substrate.resources.customer_support.resource import CustomerSupportResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "CustomerSupportResource":
        from f5xc_py_substrate.resources.customer_support.resource import CustomerSupportResource
        return CustomerSupportResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.customer_support.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.customer_support' has no attribute '{name}'")


__all__ = [
    "CustomerSupportResource",
    "AttachmentType",
    "CloseRequest",
    "CloseResponse",
    "CommentRequest",
    "CommentResponse",
    "CommentType",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "EscalationRequest",
    "EscalationResponse",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ListSupportRequest",
    "ListSupportResponse",
    "PriorityRequest",
    "PriorityResponse",
    "RaiseTaxExemptVerificationSupportTicketRequest",
    "RaiseTaxExemptVerificationSupportTicketResponse",
    "ReopenRequest",
    "ReopenResponse",
    "Spec",
]
