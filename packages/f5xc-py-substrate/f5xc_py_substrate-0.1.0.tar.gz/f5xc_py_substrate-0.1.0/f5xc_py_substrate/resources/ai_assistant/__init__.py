"""AiAssistant resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.ai_assistant.models import *
    from f5xc_py_substrate.resources.ai_assistant.resource import AiAssistantResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AiAssistantResource":
        from f5xc_py_substrate.resources.ai_assistant.resource import AiAssistantResource
        return AiAssistantResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.ai_assistant.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.ai_assistant' has no attribute '{name}'")


__all__ = [
    "AiAssistantResource",
    "BotDefenseEventDetails",
    "RequestDetails",
    "SvcPolicyEventDetails",
    "Bot",
    "Signature",
    "ThreatCampaign",
    "Violation",
    "WAFEventDetails",
    "ExplainLogRecordResponse",
    "LogFilter",
    "DashboardLink",
    "GenericLink",
    "Link",
    "GenDashboardFilterResponse",
    "ProtobufAny",
    "ErrorType",
    "GenericResponse",
    "Item",
    "ListList",
    "ListResponse",
    "OverlayData",
    "OverlayContent",
    "Display",
    "FieldProperties",
    "CellProperties",
    "Cell",
    "Row",
    "Table",
    "WidgetView",
    "SiteAnalysisResponse",
    "WidgetResponse",
    "AIAssistantQueryResponse",
    "Empty",
    "Spec",
]
