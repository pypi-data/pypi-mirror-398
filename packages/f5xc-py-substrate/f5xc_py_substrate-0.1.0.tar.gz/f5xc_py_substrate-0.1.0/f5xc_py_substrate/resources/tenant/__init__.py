"""Tenant resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.tenant.models import *
    from f5xc_py_substrate.resources.tenant.resource import TenantResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "TenantResource":
        from f5xc_py_substrate.resources.tenant.resource import TenantResource
        return TenantResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.tenant.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.tenant' has no attribute '{name}'")


__all__ = [
    "TenantResource",
    "ProtobufAny",
    "HttpBody",
    "Empty",
    "AssignDomainOwnerRequest",
    "CredentialsExpiry",
    "DeactivateTenantRequest",
    "DeactivateTenantResponse",
    "DeleteTenantRequest",
    "GetLoginEventsInTimeFrameRequest",
    "LastLoginMap",
    "LoginEventsMap",
    "PasswordPolicyPublicAccess",
    "StatusResponse",
    "SummaryResponse",
    "SupportInfo",
    "SettingsResponse",
    "UnassignDomainOwnerRequest",
    "UpdateImageRequest",
    "UpdateTenantSettingsRequest",
    "ValidationErrorField",
    "UpdateTenantSettingsResponse",
    "User",
    "UserList",
    "BasicConfiguration",
    "BruteForceDetectionSettings",
    "PasswordPolicy",
    "GlobalSpecType",
    "Spec",
]
