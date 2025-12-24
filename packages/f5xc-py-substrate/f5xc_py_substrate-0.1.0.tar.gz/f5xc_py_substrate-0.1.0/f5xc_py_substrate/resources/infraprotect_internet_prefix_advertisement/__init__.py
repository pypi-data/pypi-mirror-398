"""InfraprotectInternetPrefixAdvertisement resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.infraprotect_internet_prefix_advertisement.models import *
    from f5xc_py_substrate.resources.infraprotect_internet_prefix_advertisement.resource import InfraprotectInternetPrefixAdvertisementResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "InfraprotectInternetPrefixAdvertisementResource":
        from f5xc_py_substrate.resources.infraprotect_internet_prefix_advertisement.resource import InfraprotectInternetPrefixAdvertisementResource
        return InfraprotectInternetPrefixAdvertisementResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.infraprotect_internet_prefix_advertisement.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.infraprotect_internet_prefix_advertisement' has no attribute '{name}'")


__all__ = [
    "InfraprotectInternetPrefixAdvertisementResource",
    "ObjectCreateMetaType",
    "Empty",
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
    "DeleteRequest",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "UpdateInternetPrefixAdvertisementRequest",
    "UpdateInternetPrefixAdvertisementResponse",
    "Spec",
]
