"""AlertReceiver resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.alert_receiver.models import *
    from f5xc_py_substrate.resources.alert_receiver.resource import AlertReceiverResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AlertReceiverResource":
        from f5xc_py_substrate.resources.alert_receiver.resource import AlertReceiverResource
        return AlertReceiverResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.alert_receiver.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.alert_receiver' has no attribute '{name}'")


__all__ = [
    "AlertReceiverResource",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "AuthToken",
    "ObjectRefType",
    "CACertificateObj",
    "ClientCertificateObj",
    "ConfirmAlertReceiverRequest",
    "ConfirmAlertReceiverResponse",
    "ObjectCreateMetaType",
    "EmailConfig",
    "OpsGenieConfig",
    "PagerDutyConfig",
    "SlackConfig",
    "SMSConfig",
    "HttpBasicAuth",
    "Empty",
    "UpstreamTlsValidationContext",
    "TLSConfig",
    "HTTPConfig",
    "WebhookConfig",
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
    "TestAlertReceiverRequest",
    "TestAlertReceiverResponse",
    "VerifyAlertReceiverRequest",
    "VerifyAlertReceiverResponse",
    "Spec",
]
