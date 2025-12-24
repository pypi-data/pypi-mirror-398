"""ClientSideDefense resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.client_side_defense.models import *
    from f5xc_py_substrate.resources.client_side_defense.resource import ClientSideDefenseResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ClientSideDefenseResource":
        from f5xc_py_substrate.resources.client_side_defense.resource import ClientSideDefenseResource
        return ClientSideDefenseResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.client_side_defense.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.client_side_defense' has no attribute '{name}'")


__all__ = [
    "ClientSideDefenseResource",
    "AddToAllowedDomains",
    "AddToMitigatedDomains",
    "AffectedUser",
    "AffectedUserDeviceIDFilter",
    "AffectedUserGeolocationFilter",
    "AffectedUserIPAddressFilter",
    "AffectedUserFilters",
    "Analysis",
    "BehaviorByScript",
    "DeleteScriptJustificationResponse",
    "DeviceIDFilter",
    "Location",
    "DomainDetails",
    "UpdatedCount",
    "DomainSummary",
    "EnterpriseInfo",
    "Event",
    "IPFilter",
    "RiskLevelFilter",
    "ScriptNameFilter",
    "ScriptStatusFilter",
    "Filters",
    "FormField",
    "FormFieldAnalysisFilter",
    "FormFieldByScript",
    "FormFieldNameFilter",
    "FormFieldsFilters",
    "GetDetectedDomainsResponse",
    "GetDomainDetailsResponse",
    "GetFormFieldResponse",
    "GetJsInjectionConfigurationResponse",
    "Summary",
    "GetScriptOverviewResponse",
    "GetStatusResponse",
    "GetSummaryResponse",
    "InitRequest",
    "InitResponse",
    "Justification",
    "Sort",
    "ListAffectedUsersRequest",
    "ListAffectedUsersResponse",
    "ListBehaviorsByScriptResponse",
    "ListFormFieldsByScriptResponse",
    "ListFormFieldsGetResponse",
    "ListFormFieldsRequest",
    "ListFormFieldsResponse",
    "NetworkInteractionByScript",
    "ListNetworkInteractionsByScriptResponse",
    "ScriptInfo",
    "ListScriptsLegacyResponse",
    "ListScriptsRequest",
    "ListScriptsResponse",
    "TestJSRequest",
    "TestJSResponse",
    "UpdateDomainsRequest",
    "UpdateDomainsResponse",
    "UpdateFieldAnalysisRequest",
    "UpdateFieldAnalysisResponse",
    "UpdateScriptJustificationRequest",
    "UpdateScriptJustificationResponse",
    "UpdateScriptReadStatusRequest",
    "UpdateScriptReadStatusResponse",
    "Spec",
]
