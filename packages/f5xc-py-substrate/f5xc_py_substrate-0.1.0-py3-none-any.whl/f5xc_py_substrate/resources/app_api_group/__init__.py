"""AppApiGroup resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.app_api_group.models import *
    from f5xc_py_substrate.resources.app_api_group.resource import AppApiGroupResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AppApiGroupResource":
        from f5xc_py_substrate.resources.app_api_group.resource import AppApiGroupResource
        return AppApiGroupResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.app_api_group.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.app_api_group' has no attribute '{name}'")


__all__ = [
    "AppApiGroupResource",
    "ApiEndpoint",
    "ApiGroupId",
    "ObjectRefType",
    "ApiGroupScopeBIGIPVirtualServer",
    "ApiGroupScopeCDNLoadbalancer",
    "ApiGroupScopeHttpLoadbalancer",
    "ApiGroupStats",
    "ApiGroupsStatsItem",
    "ObjectCreateMetaType",
    "GlobalSpecType",
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
    "GlobalSpecType",
    "EvaluateApiGroupReq",
    "EvaluateApiGroupRsp",
    "GetApiGroupsStatsReq",
    "GetApiGroupsStatsRsp",
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
