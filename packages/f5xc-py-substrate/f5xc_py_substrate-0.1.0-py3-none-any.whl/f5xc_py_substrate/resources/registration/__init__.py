"""Registration resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.registration.models import *
    from f5xc_py_substrate.resources.registration.resource import RegistrationResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "RegistrationResource":
        from f5xc_py_substrate.resources.registration.resource import RegistrationResource
        return RegistrationResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.registration.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.registration' has no attribute '{name}'")


__all__ = [
    "RegistrationResource",
    "Empty",
    "ObjectRefType",
    "StatusType",
    "ProtobufAny",
    "Passport",
    "ApprovalReq",
    "ConfigReq",
    "ConfigResp",
    "ObjectCreateMetaType",
    "Bios",
    "Board",
    "Chassis",
    "Cpu",
    "GPUDevice",
    "GPU",
    "Kernel",
    "Memory",
    "NetworkDevice",
    "OS",
    "Product",
    "StorageDevice",
    "USBDevice",
    "OsInfo",
    "InternetProxy",
    "SWInfo",
    "Infra",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "GetSpecType",
    "InitializerType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "GetImageDownloadUrlReq",
    "GetImageDownloadUrlResp",
    "GetRegistrationsBySiteTokenReq",
    "GetRegistrationsBySiteTokenResp",
    "ObjectMetaType",
    "GlobalSpecType",
    "SpecType",
    "StatusType",
    "SystemObjectMetaType",
    "Object",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "GetResponse",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ListStateReq",
    "ObjectChangeResp",
    "CreateRequest",
    "ReplaceResponse",
    "SuggestValuesReq",
    "ObjectRefType",
    "SuggestedItem",
    "SuggestValuesResp",
    "Spec",
]
