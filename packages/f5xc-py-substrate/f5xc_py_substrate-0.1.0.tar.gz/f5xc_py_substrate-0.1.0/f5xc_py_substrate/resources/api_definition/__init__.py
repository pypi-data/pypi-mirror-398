"""ApiDefinition resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.api_definition.models import *
    from f5xc_py_substrate.resources.api_definition.resource import ApiDefinitionResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ApiDefinitionResource":
        from f5xc_py_substrate.resources.api_definition.resource import ApiDefinitionResource
        return ApiDefinitionResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.api_definition.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.api_definition' has no attribute '{name}'")


__all__ = [
    "ApiDefinitionResource",
    "ApiOperation",
    "APInventoryResp",
    "GlobalSpecType",
    "ApiGroupSummary",
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
    "GetReferencingAllLoadbalancersResp",
    "GetReferencingLoadbalancersResp",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ListAvailableAPIDefinitionsResp",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
