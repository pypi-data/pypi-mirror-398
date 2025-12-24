"""DnsLoadBalancer resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.dns_load_balancer.models import *
    from f5xc_py_substrate.resources.dns_load_balancer.resource import DnsLoadBalancerResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "DnsLoadBalancerResource":
        from f5xc_py_substrate.resources.dns_load_balancer.resource import DnsLoadBalancerResource
        return DnsLoadBalancerResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.dns_load_balancer.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.dns_load_balancer' has no attribute '{name}'")


__all__ = [
    "DnsLoadBalancerResource",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "Empty",
    "ResponseCacheParameters",
    "ResponseCache",
    "AsnMatchList",
    "ObjectRefType",
    "AsnMatcherType",
    "LabelSelectorType",
    "PrefixMatchList",
    "IpMatcherType",
    "LoadBalancingRule",
    "LoadBalancingRuleList",
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
    "TrendValue",
    "MetricValue",
    "HealthStatusSummary",
    "DNSLBHealthStatusListResponseItem",
    "DNSLBHealthStatusListResponse",
    "DNSLBPoolHealthStatusListResponseItem",
    "DNSLBHealthStatusResponse",
    "DNSLBPoolMemberHealthStatusListResponseItem",
    "DNSLBPoolHealthStatusResponse",
    "DNSLBPoolMemberHealthStatusEvent",
    "DNSLBPoolMemberHealthStatusListResponse",
    "DNSLBPoolMemberHealthStatusResponse",
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
    "SuggestValuesReq",
    "SuggestedItem",
    "SuggestValuesResp",
    "Spec",
]
