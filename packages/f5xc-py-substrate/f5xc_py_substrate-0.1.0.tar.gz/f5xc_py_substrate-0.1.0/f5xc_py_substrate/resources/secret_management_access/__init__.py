"""SecretManagementAccess resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.secret_management_access.models import *
    from f5xc_py_substrate.resources.secret_management_access.resource import SecretManagementAccessResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SecretManagementAccessResource":
        from f5xc_py_substrate.resources.secret_management_access.resource import SecretManagementAccessResource
        return SecretManagementAccessResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.secret_management_access.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.secret_management_access' has no attribute '{name}'")


__all__ = [
    "SecretManagementAccessResource",
    "Empty",
    "ProtobufAny",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "AppRoleAuthInfoType",
    "AuthnTypeBasicAuth",
    "AuthnTypeHeaders",
    "AuthnTypeQueryParams",
    "ConditionType",
    "ErrorType",
    "HashAlgorithms",
    "RestAuthInfoType",
    "ObjectRefType",
    "TrustedCAList",
    "TlsValidationParamsType",
    "UpstreamCertificateParamsType",
    "TlsCertificateType",
    "TlsParamsType",
    "UpstreamTlsParamsType",
    "VaultAuthInfoType",
    "HostAccessInfoType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "NetworkRefType",
    "SiteRefType",
    "VSiteRefType",
    "NetworkSiteRefSelector",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateSpecType",
    "CreateRequest",
    "GetSpecType",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceSpecType",
    "ReplaceRequest",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
