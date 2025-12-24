"""Proxy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.proxy.models import *
    from f5xc_py_substrate.resources.proxy.resource import ProxyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ProxyResource":
        from f5xc_py_substrate.resources.proxy.resource import ProxyResource
        return ProxyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.proxy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.proxy' has no attribute '{name}'")


__all__ = [
    "ProxyResource",
    "ProtobufAny",
    "HttpBody",
    "BufferConfigType",
    "CompressionType",
    "Empty",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "CookieValueOption",
    "HeaderManipulationOptionType",
    "SetCookieValueOption",
    "AdvancedOptionsType",
    "ObjectRefType",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "ActiveForwardProxyPoliciesType",
    "DynamicHttpProxyType",
    "HashAlgorithms",
    "TlsCertificateType",
    "CustomCiphers",
    "TlsConfig",
    "XfccHeaderKeys",
    "DownstreamTlsValidationContext",
    "DownstreamTlsParamsType",
    "DynamicHttpsProxyType",
    "DynamicSniProxyType",
    "DynamicProxyType",
    "HttpConnectProxyType",
    "WhereSite",
    "WhereVirtualSite",
    "WhereTypeSiteVsite",
    "AdvertiseSiteVsite",
    "DomainType",
    "TlsInterceptionRule",
    "TlsInterceptionPolicy",
    "TlsInterceptionType",
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
