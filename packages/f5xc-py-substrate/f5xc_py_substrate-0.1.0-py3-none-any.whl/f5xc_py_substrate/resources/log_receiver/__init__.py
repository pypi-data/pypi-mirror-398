"""LogReceiver resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.log_receiver.models import *
    from f5xc_py_substrate.resources.log_receiver.resource import LogReceiverResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "LogReceiverResource":
        from f5xc_py_substrate.resources.log_receiver.resource import LogReceiverResource
        return LogReceiverResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.log_receiver.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.log_receiver' has no attribute '{name}'")


__all__ = [
    "LogReceiverResource",
    "Empty",
    "ObjectRefType",
    "ObjectCreateMetaType",
    "TCPServerConfigType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "TLSClientConfigType",
    "TLSConfigType",
    "UDPServerConfigType",
    "SyslogReceiver",
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
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "TestLogReceiverRequest",
    "TestLogReceiverResponse",
    "Spec",
]
