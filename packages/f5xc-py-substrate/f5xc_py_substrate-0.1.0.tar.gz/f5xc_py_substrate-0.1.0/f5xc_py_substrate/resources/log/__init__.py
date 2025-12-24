"""Log resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.log.models import *
    from f5xc_py_substrate.resources.log.resource import LogResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "LogResource":
        from f5xc_py_substrate.resources.log.resource import LogResource
        return LogResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.log.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.log' has no attribute '{name}'")


__all__ = [
    "LogResource",
    "AccessLogAggregationRequest",
    "AccessLogRequestV2",
    "AuditLogAggregationRequest",
    "AuditLogRequestV2",
    "LabelFilter",
    "ExternalConnectorRequest",
    "FirewallLogAggregationRequest",
    "FirewallLogRequest",
    "K8SAuditLogAggregationRequest",
    "K8SAuditLogRequest",
    "K8SEventsAggregationRequest",
    "K8SEventsRequest",
    "AggregationResponse",
    "Response",
    "PlatformEventAggregationRequest",
    "PlatformEventRequest",
    "VK8SAuditLogAggregationRequest",
    "VK8SAuditLogRequest",
    "VK8SEventsAggregationRequest",
    "VK8SEventsRequest",
    "Spec",
]
