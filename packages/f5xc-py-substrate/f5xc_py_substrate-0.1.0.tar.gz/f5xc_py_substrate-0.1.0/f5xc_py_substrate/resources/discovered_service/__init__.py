"""DiscoveredService resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.discovered_service.models import *
    from f5xc_py_substrate.resources.discovered_service.resource import DiscoveredServiceResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "DiscoveredServiceResource":
        from f5xc_py_substrate.resources.discovered_service.resource import DiscoveredServiceResource
        return DiscoveredServiceResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.discovered_service.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.discovered_service' has no attribute '{name}'")


__all__ = [
    "DiscoveredServiceResource",
    "ObjectRefType",
    "PodInfoType",
    "PortInfoType",
    "ConsulService",
    "Empty",
    "ObjectRefType",
    "WhereSite",
    "WhereVirtualSite",
    "ProxyTypeHttp",
    "ProxyTypeHttps",
    "HTTPLBRequest",
    "CreateHTTPLoadBalancerRequest",
    "CreateHTTPLoadBalancerResponse",
    "AdvertisePublic",
    "WhereSite",
    "WhereVirtualNetwork",
    "WhereVirtualSite",
    "WhereVirtualSiteSpecifiedVIP",
    "WhereVK8SService",
    "WhereType",
    "AdvertiseCustom",
    "TCPLBRequest",
    "CreateTCPLoadBalancerRequest",
    "CreateTCPLoadBalancerResponse",
    "DisableVisibilityRequest",
    "DisableVisibilityResponse",
    "TrendValue",
    "MetricValue",
    "VirtualServerPoolHealthStatusListResponseItem",
    "VirtualServerPoolMemberHealth",
    "HealthStatusResponse",
    "EnableVisibilityRequest",
    "EnableVisibilityResponse",
    "ObjectGetMetaType",
    "K8sService",
    "NginxOneDiscoveredServer",
    "ThirdPartyApplicationDiscovery",
    "VirtualServer",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "ListServicesResponseItem",
    "ListServicesResponse",
    "SuggestValuesReq",
    "SuggestedItem",
    "SuggestValuesResp",
    "Spec",
]
