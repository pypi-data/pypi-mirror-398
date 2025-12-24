"""GeoLocationSet resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.geo_location_set.models import *
    from f5xc_py_substrate.resources.geo_location_set.resource import GeoLocationSetResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "GeoLocationSetResource":
        from f5xc_py_substrate.resources.geo_location_set.resource import GeoLocationSetResource
        return GeoLocationSetResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.geo_location_set.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.geo_location_set' has no attribute '{name}'")


__all__ = [
    "GeoLocationSetResource",
    "ObjectCreateMetaType",
    "LabelSelectorType",
    "Empty",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "ObjectRefType",
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
    "Spec",
]
