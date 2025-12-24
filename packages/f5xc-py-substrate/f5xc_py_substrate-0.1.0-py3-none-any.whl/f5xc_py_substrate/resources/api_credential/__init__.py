"""ApiCredential resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.api_credential.models import *
    from f5xc_py_substrate.resources.api_credential.resource import ApiCredentialResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ApiCredentialResource":
        from f5xc_py_substrate.resources.api_credential.resource import ApiCredentialResource
        return ApiCredentialResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.api_credential.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.api_credential' has no attribute '{name}'")


__all__ = [
    "ApiCredentialResource",
    "ApiCertificateType",
    "BulkRevokeResponse",
    "CustomCreateSpecType",
    "CreateRequest",
    "CreateResponse",
    "Empty",
    "NamespaceRoleType",
    "SiteKubeconfigType",
    "Vk8sKubeconfigType",
    "CreateServiceCredentialsRequest",
    "ObjectMetaType",
    "ObjectRefType",
    "GlobalSpecType",
    "SpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectMetaType",
    "Object",
    "GetResponse",
    "NamespaceAccessType",
    "GetServiceCredentialsResponse",
    "ListResponseItem",
    "ListResponse",
    "ListServiceCredentialsResponseItem",
    "ListServiceCredentialsResponse",
    "RecreateScimTokenRequest",
    "ReplaceServiceCredentialsRequest",
    "ReplaceServiceCredentialsResponse",
    "ScimTokenRequest",
    "StatusResponse",
    "Spec",
]
