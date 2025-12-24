"""Receiver resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.receiver.models import *
    from f5xc_py_substrate.resources.receiver.resource import ReceiverResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ReceiverResource":
        from f5xc_py_substrate.resources.receiver.resource import ReceiverResource
        return ReceiverResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.receiver.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.receiver' has no attribute '{name}'")


__all__ = [
    "ReceiverResource",
    "Empty",
    "ObjectRefType",
    "ProtobufAny",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "AuthToken",
    "BatchOptionType",
    "CompressionType",
    "AzureBlobConfig",
    "ObjectCreateMetaType",
    "TLSClientConfigType",
    "TLSConfigType",
    "DatadogConfig",
    "ObjectRefType",
    "GCPBucketConfig",
    "HttpAuthBasic",
    "HTTPConfig",
    "S3Config",
    "SplunkConfig",
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
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
