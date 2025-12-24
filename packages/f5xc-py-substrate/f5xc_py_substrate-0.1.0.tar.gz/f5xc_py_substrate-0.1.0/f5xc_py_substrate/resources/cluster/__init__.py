"""Cluster resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.cluster.models import *
    from f5xc_py_substrate.resources.cluster.resource import ClusterResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ClusterResource":
        from f5xc_py_substrate.resources.cluster.resource import ClusterResource
        return ClusterResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.cluster.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.cluster' has no attribute '{name}'")


__all__ = [
    "ClusterResource",
    "CircuitBreaker",
    "ObjectCreateMetaType",
    "Empty",
    "EndpointSubsetSelectorType",
    "ObjectRefType",
    "HeaderTransformationType",
    "Http1ProtocolOptions",
    "Http2ProtocolOptions",
    "OutlierDetectionType",
    "TrustedCAList",
    "TlsValidationParamsType",
    "UpstreamCertificateParamsType",
    "HashAlgorithms",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "TlsCertificateType",
    "TlsParamsType",
    "UpstreamTlsParamsType",
    "UpstreamConnPoolReuseType",
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
    "Spec",
]
