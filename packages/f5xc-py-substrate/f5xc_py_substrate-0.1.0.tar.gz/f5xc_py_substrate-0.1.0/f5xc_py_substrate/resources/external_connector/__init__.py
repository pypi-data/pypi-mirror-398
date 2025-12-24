"""ExternalConnector resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.external_connector.models import *
    from f5xc_py_substrate.resources.external_connector.resource import ExternalConnectorResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ExternalConnectorResource":
        from f5xc_py_substrate.resources.external_connector.resource import ExternalConnectorResource
        return ExternalConnectorResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.external_connector.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.external_connector' has no attribute '{name}'")


__all__ = [
    "ExternalConnectorResource",
    "Empty",
    "DpdKeepAliveTimer",
    "ObjectRefType",
    "Ipv4AddressType",
    "Ipv6AddressType",
    "IpAddressType",
    "IkeParameters",
    "ObjectRefType",
    "SegmentRefType",
    "TunnelEndpoint",
    "TunnelParameters",
    "ConnectionTypeIPSec",
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
