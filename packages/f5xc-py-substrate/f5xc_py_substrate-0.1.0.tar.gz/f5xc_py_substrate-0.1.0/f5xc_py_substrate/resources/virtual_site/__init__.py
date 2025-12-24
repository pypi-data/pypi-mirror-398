"""VirtualSite resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.virtual_site.models import *
    from f5xc_py_substrate.resources.virtual_site.resource import VirtualSiteResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "VirtualSiteResource":
        from f5xc_py_substrate.resources.virtual_site.resource import VirtualSiteResource
        return VirtualSiteResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.virtual_site.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.virtual_site' has no attribute '{name}'")


__all__ = [
    "VirtualSiteResource",
    "ObjectRefType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "LabelSelectorType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateSpecType",
    "GetSpecType",
    "ReplaceSpecType",
    "CreateRequest",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceRequest",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "SelecteeItemType",
    "SelecteeResponse",
    "Spec",
]
