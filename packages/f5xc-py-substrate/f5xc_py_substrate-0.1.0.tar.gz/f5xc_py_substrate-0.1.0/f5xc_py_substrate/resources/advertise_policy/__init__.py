"""AdvertisePolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.advertise_policy.models import *
    from f5xc_py_substrate.resources.advertise_policy.resource import AdvertisePolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AdvertisePolicyResource":
        from f5xc_py_substrate.resources.advertise_policy.resource import AdvertisePolicyResource
        return AdvertisePolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.advertise_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.advertise_policy' has no attribute '{name}'")


__all__ = [
    "AdvertisePolicyResource",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "Empty",
    "HashAlgorithms",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "TlsCertificateType",
    "TrustedCAList",
    "TlsValidationParamsType",
    "TlsParamsType",
    "DownstreamTlsParamsType",
    "SiteRefType",
    "NetworkRefType",
    "VSiteRefType",
    "NetworkSiteRefSelector",
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
    "ListenerConfig",
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
