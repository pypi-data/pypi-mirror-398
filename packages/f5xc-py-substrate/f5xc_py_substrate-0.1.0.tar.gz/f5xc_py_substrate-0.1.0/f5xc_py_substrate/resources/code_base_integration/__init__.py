"""CodeBaseIntegration resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.code_base_integration.models import *
    from f5xc_py_substrate.resources.code_base_integration.resource import CodeBaseIntegrationResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "CodeBaseIntegrationResource":
        from f5xc_py_substrate.resources.code_base_integration.resource import CodeBaseIntegrationResource
        return CodeBaseIntegrationResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.code_base_integration.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.code_base_integration' has no attribute '{name}'")


__all__ = [
    "CodeBaseIntegrationResource",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "AzureReposIntegration",
    "BitBucketCloudIntegration",
    "BitBucketServerIntegration",
    "GithubIntegration",
    "GithubEnterpriseIntegration",
    "GitlabCloudIntegration",
    "GitlabEnterpriseIntegration",
    "CodeBaseIntegration",
    "ObjectCreateMetaType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "IntegrationHealth",
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
