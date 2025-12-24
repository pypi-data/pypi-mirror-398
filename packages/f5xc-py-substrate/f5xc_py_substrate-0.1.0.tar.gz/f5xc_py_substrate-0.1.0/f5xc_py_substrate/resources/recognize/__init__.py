"""Recognize resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.recognize.models import *
    from f5xc_py_substrate.resources.recognize.resource import RecognizeResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "RecognizeResource":
        from f5xc_py_substrate.resources.recognize.resource import RecognizeResource
        return RecognizeResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.recognize.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.recognize' has no attribute '{name}'")


__all__ = [
    "RecognizeResource",
    "ChannelMWItem",
    "ChannelItem",
    "ChannelData",
    "ChannelRequest",
    "ChannelResponse",
    "ConversionItem",
    "ConversionData",
    "ConversionRequest",
    "ConversionResponse",
    "EnjoyLoginItem",
    "EnjoyItem",
    "EnjoyData",
    "EnjoyRequest",
    "EnjoyResponse",
    "FrictionAggregationItem",
    "FrictionAggregationData",
    "FrictionAggregationRequest",
    "FrictionAggregationResponse",
    "FrictionHistogramItem",
    "FrictionHistogramData",
    "FrictionHistogramRequest",
    "FrictionHistogramResponse",
    "GetStatusProvisionResponse",
    "GetStatusResponse",
    "HealthResponse",
    "LiftControlItem",
    "LiftItem",
    "LiftData",
    "LiftRequest",
    "LiftResponse",
    "RescueItem",
    "RescueData",
    "RescueRequest",
    "RescueResponse",
    "StateData",
    "StateResponse",
    "SubscribeRequest",
    "SubscribeResponse",
    "TopReasonCodesData",
    "TopReasonCodesRequest",
    "TopReasonCodesResponse",
    "UnsubscribeRequest",
    "UnsubscribeResponse",
    "ValidateSrcTagInjectionRequest",
    "ValidateSrcTagInjectionResponse",
    "Spec",
]
