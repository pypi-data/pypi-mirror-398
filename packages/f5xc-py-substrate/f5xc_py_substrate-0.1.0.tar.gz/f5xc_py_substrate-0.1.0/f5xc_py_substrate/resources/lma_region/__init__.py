"""LmaRegion resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.lma_region.models import *
    from f5xc_py_substrate.resources.lma_region.resource import LmaRegionResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "LmaRegionResource":
        from f5xc_py_substrate.resources.lma_region.resource import LmaRegionResource
        return LmaRegionResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.lma_region.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.lma_region' has no attribute '{name}'")


__all__ = [
    "LmaRegionResource",
    "ObjectRefType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "ClickhouseParams",
    "ElasticParams",
    "ObjectGetMetaType",
    "KafkaParams",
    "GetSpecType",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
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
    "Spec",
]
