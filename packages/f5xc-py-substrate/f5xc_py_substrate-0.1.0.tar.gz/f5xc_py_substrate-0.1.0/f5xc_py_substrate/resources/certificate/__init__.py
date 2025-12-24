"""Certificate resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.certificate.models import *
    from f5xc_py_substrate.resources.certificate.resource import CertificateResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "CertificateResource":
        from f5xc_py_substrate.resources.certificate.resource import CertificateResource
        return CertificateResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.certificate.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.certificate' has no attribute '{name}'")


__all__ = [
    "CertificateResource",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "HashAlgorithms",
    "Empty",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "CertInfoType",
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
