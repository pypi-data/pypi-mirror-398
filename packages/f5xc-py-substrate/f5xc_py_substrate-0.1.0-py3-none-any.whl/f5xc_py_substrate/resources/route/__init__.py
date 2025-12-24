"""Route resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.route.models import *
    from f5xc_py_substrate.resources.route.resource import RouteResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "RouteResource":
        from f5xc_py_substrate.resources.route.resource import RouteResource
        return RouteResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.route.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.route' has no attribute '{name}'")


__all__ = [
    "RouteResource",
    "Ipv4AddressType",
    "Ipv6AddressType",
    "IpAddressType",
    "DcgHop",
    "DropNH",
    "GREHop",
    "GREType",
    "IPSecType",
    "IpSecHop",
    "SslHop",
    "IntermediateHop",
    "IPinIPType",
    "IPinUDPType",
    "LocalNH",
    "MPLSType",
    "Info",
    "Empty",
    "PrefixListType",
    "Request",
    "RouteRoutes",
    "Response",
    "SSLType",
    "SubnetNH",
    "TunnelNH",
    "SimplifiedNexthopType",
    "SimplifiedEcmpNH",
    "SimplifiedRouteInfo",
    "SimplifiedRouteRequest",
    "SimplifiedRoutes",
    "SimplifiedRouteResponse",
    "Spec",
]
