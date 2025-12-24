"""Service resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.service.models import *
    from f5xc_py_substrate.resources.service.resource import ServiceResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ServiceResource":
        from f5xc_py_substrate.resources.service.resource import ServiceResource
        return ServiceResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.service.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.service' has no attribute '{name}'")


__all__ = [
    "ServiceResource",
    "APIEPDynExample",
    "AuthenticationTypeLocPair",
    "PDFSpec",
    "PDFStat",
    "APIEPPDFInfo",
    "RiskScore",
    "APIEPInfo",
    "TrendValue",
    "MetricValue",
    "MetricFeatureData",
    "MetricData",
    "EdgeMetricData",
    "EdgeMetricSelector",
    "HealthscoreTypeData",
    "HealthscoreData",
    "HealthscoreSelector",
    "NodeMetricData",
    "NodeMetricSelector",
    "InstanceId",
    "InstanceRequestId",
    "AppTypeInfo",
    "AppTypeListResponse",
    "Id",
    "CdnMetricData",
    "CacheableData",
    "EdgeAPIEPData",
    "EdgeAPIEPSelector",
    "EdgeFieldData",
    "EdgeData",
    "EdgeFieldSelector",
    "RequestId",
    "EdgeRequest",
    "EdgeResponse",
    "NodeFieldData",
    "NodeData",
    "GraphData",
    "InstanceData",
    "NodeFieldSelector",
    "InstanceRequest",
    "InstanceResponse",
    "InstancesData",
    "LabelFilter",
    "InstancesRequest",
    "InstancesResponse",
    "LBCacheContentRequest",
    "LBCacheContentResponse",
    "NodeRequest",
    "NodeResponse",
    "Response",
    "Spec",
]
