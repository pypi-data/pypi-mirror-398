"""TicketTrackingSystem resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.ticket_tracking_system.models import *
    from f5xc_py_substrate.resources.ticket_tracking_system.resource import TicketTrackingSystemResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "TicketTrackingSystemResource":
        from f5xc_py_substrate.resources.ticket_tracking_system.resource import TicketTrackingSystemResource
        return TicketTrackingSystemResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.ticket_tracking_system.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.ticket_tracking_system' has no attribute '{name}'")


__all__ = [
    "TicketTrackingSystemResource",
    "ProtobufAny",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "JiraIssueType",
    "JiraProject",
    "JiraAdhocRestApiConfigurationType",
    "JiraConfigurationType",
    "CreateSpecType",
    "CreateRequest",
    "GetSpecType",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceSpecType",
    "ReplaceRequest",
    "GetResponse",
    "JiraProjectsIssueTypesRequest",
    "JiraProjectsIssueTypesResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "ValidateTicketTrackingSystemRequest",
    "ValidateTicketTrackingSystemResponse",
    "Spec",
]
