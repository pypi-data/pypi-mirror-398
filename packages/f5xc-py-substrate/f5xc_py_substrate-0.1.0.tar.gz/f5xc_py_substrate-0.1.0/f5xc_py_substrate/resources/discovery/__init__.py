"""Discovery resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.discovery.models import *
    from f5xc_py_substrate.resources.discovery.resource import DiscoveryResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "DiscoveryResource":
        from f5xc_py_substrate.resources.discovery.resource import DiscoveryResource
        return DiscoveryResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.discovery.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.discovery' has no attribute '{name}'")


__all__ = [
    "DiscoveryResource",
    "ConditionType",
    "CBIPDeviceStatus",
    "CBIPStatusType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "TLSClientConfigType",
    "RestConfigType",
    "ConsulHttpBasicAuthInfoType",
    "ConsulAccessInfo",
    "Empty",
    "ConsulVipDiscoveryInfoType",
    "ConsulDiscoveryType",
    "ObjectCreateMetaType",
    "K8SAccessInfo",
    "K8SNamespaceMappingItem",
    "K8SNamespaceMapping",
    "K8SDelegationType",
    "K8SPublishType",
    "K8SVipDiscoveryInfoType",
    "K8SDiscoveryType",
    "ObjectRefType",
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
    "PodInfoType",
    "PortInfoType",
    "DiscoveredServiceType",
    "DownloadCertificatesRequest",
    "DownloadCertificatesResponse",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "StatusMetaType",
    "VerStatusType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
