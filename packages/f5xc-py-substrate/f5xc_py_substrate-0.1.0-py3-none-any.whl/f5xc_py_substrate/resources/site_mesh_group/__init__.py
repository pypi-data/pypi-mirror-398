"""SiteMeshGroup resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.site_mesh_group.models import *
    from f5xc_py_substrate.resources.site_mesh_group.resource import SiteMeshGroupResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SiteMeshGroupResource":
        from f5xc_py_substrate.resources.site_mesh_group.resource import SiteMeshGroupResource
        return SiteMeshGroupResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.site_mesh_group.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.site_mesh_group' has no attribute '{name}'")


__all__ = [
    "SiteMeshGroupResource",
    "Empty",
    "ObjectRefType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "SiteInfo",
    "Status",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "FullMeshGroupType",
    "HubFullMeshGroupType",
    "ObjectRefType",
    "SpokeMeshGroupType",
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
    "Spec",
]
