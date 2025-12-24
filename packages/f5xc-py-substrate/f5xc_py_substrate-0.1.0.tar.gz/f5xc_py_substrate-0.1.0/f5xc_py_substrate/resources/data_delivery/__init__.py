"""DataDelivery resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.data_delivery.models import *
    from f5xc_py_substrate.resources.data_delivery.resource import DataDeliveryResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "DataDeliveryResource":
        from f5xc_py_substrate.resources.data_delivery.resource import DataDeliveryResource
        return DataDeliveryResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.data_delivery.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.data_delivery' has no attribute '{name}'")


__all__ = [
    "DataDeliveryResource",
    "DataPoint",
    "DataSet",
    "EventsReason",
    "Feature",
    "FlowLabel",
    "GetDataDictionaryResponse",
    "GetDataSetsResponse",
    "Series",
    "LineChartData",
    "ListDataSetsResponse",
    "ListFlowLabelsResponse",
    "LoadExecutiveSummaryRequest",
    "SummaryPanel",
    "LoadExecutiveSummaryResponse",
    "TestReceiverRequest",
    "TestReceiverResponse",
    "UpdateReceiverStatusRequest",
    "UpdateReceiverStatusResponse",
    "ProtobufAny",
    "SuggestValuesReq",
    "ObjectRefType",
    "SuggestedItem",
    "SuggestValuesResp",
    "Empty",
    "Spec",
]
