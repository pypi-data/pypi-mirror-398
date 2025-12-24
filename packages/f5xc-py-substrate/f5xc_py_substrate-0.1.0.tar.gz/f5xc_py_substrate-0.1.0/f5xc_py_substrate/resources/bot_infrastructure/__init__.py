"""BotInfrastructure resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.bot_infrastructure.models import *
    from f5xc_py_substrate.resources.bot_infrastructure.resource import BotInfrastructureResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "BotInfrastructureResource":
        from f5xc_py_substrate.resources.bot_infrastructure.resource import BotInfrastructureResource
        return BotInfrastructureResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.bot_infrastructure.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.bot_infrastructure' has no attribute '{name}'")


__all__ = [
    "BotInfrastructureResource",
    "PolicyMetadata",
    "EndpointPolicyMetadata",
    "Egress",
    "Ingress",
    "InfraCloudHosted",
    "IPInfo",
    "Device",
    "InfraF5HostedOnPrem",
    "GetSpecType",
    "ReplaceSpecType",
    "ObjectCreateMetaType",
    "Production",
    "Testing",
    "CreateSpecInfraCloudHosted",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "DeployPolicyMetadata",
    "DeployPoliciesRequest",
    "DeployPoliciesResponse",
    "DeploymentData",
    "DeploymentHistoryData",
    "DeploymentHistoryResponse",
    "DeploymentStatusResponse",
    "ObjectRefType",
    "ObjectReplaceMetaType",
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
    "SuggestValuesReq",
    "ObjectRefType",
    "SuggestedItem",
    "SuggestValuesResp",
    "Spec",
]
