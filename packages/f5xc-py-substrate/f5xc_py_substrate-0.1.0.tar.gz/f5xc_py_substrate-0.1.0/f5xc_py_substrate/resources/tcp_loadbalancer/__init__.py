"""TcpLoadbalancer resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.tcp_loadbalancer.models import *
    from f5xc_py_substrate.resources.tcp_loadbalancer.resource import TcpLoadbalancerResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "TcpLoadbalancerResource":
        from f5xc_py_substrate.resources.tcp_loadbalancer.resource import TcpLoadbalancerResource
        return TcpLoadbalancerResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.tcp_loadbalancer.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.tcp_loadbalancer' has no attribute '{name}'")


__all__ = [
    "TcpLoadbalancerResource",
    "Empty",
    "ObjectRefType",
    "ProtobufAny",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "ConditionType",
    "ErrorType",
    "HashAlgorithms",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "SecretType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "TlsCertificateType",
    "CustomCiphers",
    "TlsConfig",
    "ObjectRefType",
    "XfccHeaderKeys",
    "DownstreamTlsValidationContext",
    "DownstreamTlsParamsType",
    "DnsInfo",
    "GlobalSpecType",
    "ServicePolicyList",
    "AdvertisePublic",
    "WhereSite",
    "WhereVirtualNetwork",
    "WhereVirtualSite",
    "WhereVirtualSiteSpecifiedVIP",
    "WhereVK8SService",
    "WhereType",
    "AdvertiseCustom",
    "OriginPoolWithWeight",
    "DownstreamTLSCertsParams",
    "ProxyTypeTLSTCP",
    "ProxyTypeTLSTCPAutoCerts",
    "CreateSpecType",
    "CreateRequest",
    "DNSRecord",
    "AutoCertInfoType",
    "InternetVIPListenerStatusType",
    "InternetVIPTargetGroupStatusType",
    "InternetVIPStatus",
    "InternetVIPInfo",
    "GetSpecType",
    "CreateResponse",
    "DeleteRequest",
    "GetDnsInfoResponse",
    "ReplaceSpecType",
    "ReplaceRequest",
    "DNSVHostStatusType",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
