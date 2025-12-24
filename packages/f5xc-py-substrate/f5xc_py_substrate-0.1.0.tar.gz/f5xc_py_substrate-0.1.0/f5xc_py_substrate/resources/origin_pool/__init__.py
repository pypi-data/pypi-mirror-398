"""OriginPool resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.origin_pool.models import *
    from f5xc_py_substrate.resources.origin_pool.resource import OriginPoolResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "OriginPoolResource":
        from f5xc_py_substrate.resources.origin_pool.resource import OriginPoolResource
        return OriginPoolResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.origin_pool.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.origin_pool' has no attribute '{name}'")


__all__ = [
    "OriginPoolResource",
    "CircuitBreaker",
    "EndpointSubsetSelectorType",
    "Empty",
    "HeaderTransformationType",
    "Http1ProtocolOptions",
    "Http2ProtocolOptions",
    "OutlierDetectionType",
    "ObjectRefType",
    "ObjectCreateMetaType",
    "DefaultSubset",
    "Subsets",
    "AdvancedOptions",
    "ObjectRefType",
    "OriginServerCBIPService",
    "SiteLocator",
    "PrefixStringListType",
    "SnatPoolConfiguration",
    "OriginServerConsulService",
    "OriginServerCustomEndpoint",
    "OriginServerK8SService",
    "OriginServerPrivateIP",
    "OriginServerPrivateName",
    "OriginServerPublicIP",
    "OriginServerPublicName",
    "OriginServerVirtualNetworkIP",
    "OriginServerVirtualNetworkName",
    "OriginServerType",
    "UpstreamConnPoolReuseType",
    "CustomCiphers",
    "TlsConfig",
    "HashAlgorithms",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "TlsCertificateType",
    "TlsCertificatesType",
    "UpstreamTlsValidationContext",
    "UpstreamTlsParameters",
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
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
