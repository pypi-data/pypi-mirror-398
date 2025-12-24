"""DeviceId resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.device_id.models import *
    from f5xc_py_substrate.resources.device_id.resource import DeviceIdResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "DeviceIdResource":
        from f5xc_py_substrate.resources.device_id.resource import DeviceIdResource
        return DeviceIdResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.device_id.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.device_id' has no attribute '{name}'")


__all__ = [
    "DeviceIdResource",
    "ApplicationProvisionRequest",
    "ApplicationProvisionResponse",
    "DeleteApplicationsResponse",
    "EnableRequest",
    "EnableResponse",
    "GetApplicationsResponse",
    "GetBotAssessmentTopAsnRequest",
    "GetBotAssessmentTopAsnResponse",
    "GetBotAssessmentTopUrlsRequest",
    "GetBotAssessmentTopUrlsResponse",
    "GetBotAssessmentTransactionsRequest",
    "GetBotAssessmentTransactionsResponse",
    "GetDashboardByAgeRequest",
    "GetDashboardByAgeResponse",
    "GetDashboardByApplicationsRequest",
    "GetDashboardByApplicationsResponse",
    "GetDashboardByAsnRequest",
    "GetDashboardByAsnResponse",
    "GetDashboardByCountryRequest",
    "GetDashboardByCountryResponse",
    "GetDashboardBySessionRequest",
    "GetDashboardBySessionResponse",
    "GetDashboardByUaRequest",
    "GetDashboardByUaResponse",
    "GetDashboardUniqueAccessRequest",
    "GetDashboardUniqueAccessResponse",
    "GetRegionsResponse",
    "GetStatusResponse",
    "UpdateApplicationRequest",
    "UpdateApplicationResponse",
    "ValidateSrcTagInjectionRequest",
    "ValidateSrcTagInjectionResponse",
    "Spec",
]
