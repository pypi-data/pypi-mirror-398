"""BotDefenseAppInfrastructure resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.bot_defense_app_infrastructure.models import *
    from f5xc_py_substrate.resources.bot_defense_app_infrastructure.resource import BotDefenseAppInfrastructureResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "BotDefenseAppInfrastructureResource":
        from f5xc_py_substrate.resources.bot_defense_app_infrastructure.resource import BotDefenseAppInfrastructureResource
        return BotDefenseAppInfrastructureResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.bot_defense_app_infrastructure.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.bot_defense_app_infrastructure' has no attribute '{name}'")


__all__ = [
    "BotDefenseAppInfrastructureResource",
    "ObjectCreateMetaType",
    "Egress",
    "Ingress",
    "InfraF5Hosted",
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
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
