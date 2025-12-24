"""Authentication resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.authentication.models import *
    from f5xc_py_substrate.resources.authentication.resource import AuthenticationResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AuthenticationResource":
        from f5xc_py_substrate.resources.authentication.resource import AuthenticationResource
        return AuthenticationResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.authentication.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.authentication' has no attribute '{name}'")


__all__ = [
    "AuthenticationResource",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "HMACKeyPair",
    "KMSKeyRefType",
    "CookieParams",
    "ObjectCreateMetaType",
    "OIDCAuthParams",
    "OIDCAuthType",
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
