"""UdpLoadbalancer resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.udp_loadbalancer.models import *
    from f5xc_py_substrate.resources.udp_loadbalancer.resource import UdpLoadbalancerResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "UdpLoadbalancerResource":
        from f5xc_py_substrate.resources.udp_loadbalancer.resource import UdpLoadbalancerResource
        return UdpLoadbalancerResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.udp_loadbalancer.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.udp_loadbalancer' has no attribute '{name}'")


__all__ = [
    "UdpLoadbalancerResource",
    "Empty",
    "ObjectRefType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "ObjectRefType",
    "DnsInfo",
    "GlobalSpecType",
    "AdvertisePublic",
    "WhereSite",
    "WhereVirtualNetwork",
    "WhereVirtualSite",
    "WhereVirtualSiteSpecifiedVIP",
    "WhereVK8SService",
    "WhereType",
    "AdvertiseCustom",
    "OriginPoolWithWeight",
    "CreateSpecType",
    "CreateRequest",
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
