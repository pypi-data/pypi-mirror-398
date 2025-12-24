"""BgpRoutingPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.bgp_routing_policy.models import *
    from f5xc_py_substrate.resources.bgp_routing_policy.resource import BgpRoutingPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "BgpRoutingPolicyResource":
        from f5xc_py_substrate.resources.bgp_routing_policy.resource import BgpRoutingPolicyResource
        return BgpRoutingPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.bgp_routing_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.bgp_routing_policy' has no attribute '{name}'")


__all__ = [
    "BgpRoutingPolicyResource",
    "BgpCommunity",
    "Empty",
    "BgpPrefixMatch",
    "BgpPrefixMatchList",
    "BgpRouteAction",
    "BgpRouteMatch",
    "BgpRoutePolicy",
    "ObjectCreateMetaType",
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
    "ObjectRefType",
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
