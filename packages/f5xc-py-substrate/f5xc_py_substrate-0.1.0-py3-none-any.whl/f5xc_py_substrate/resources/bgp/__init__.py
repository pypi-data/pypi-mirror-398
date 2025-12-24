"""Bgp resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.bgp.models import *
    from f5xc_py_substrate.resources.bgp.resource import BgpResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "BgpResource":
        from f5xc_py_substrate.resources.bgp.resource import BgpResource
        return BgpResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.bgp.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.bgp' has no attribute '{name}'")


__all__ = [
    "BgpResource",
    "BGPPath",
    "Ipv4AddressType",
    "Ipv6AddressType",
    "IpAddressType",
    "PeerStatusType",
    "VerBGPPeers",
    "BGPPeersResponse",
    "BGPRoute",
    "BGPRouteTable",
    "BGPRoutingInstanceTable",
    "VerBGPRoutes",
    "BGPRoutesResponse",
    "Spec",
]
