"""TenantConfiguration resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.tenant_configuration.models import *
    from f5xc_py_substrate.resources.tenant_configuration.resource import TenantConfigurationResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "TenantConfigurationResource":
        from f5xc_py_substrate.resources.tenant_configuration.resource import TenantConfigurationResource
        return TenantConfigurationResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.tenant_configuration.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.tenant_configuration' has no attribute '{name}'")


__all__ = [
    "TenantConfigurationResource",
    "ObjectRefType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectGetMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "BasicConfiguration",
    "BruteForceDetectionSettings",
    "PasswordPolicy",
    "CreateSpecType",
    "CreateRequest",
    "GetSpecType",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceSpecType",
    "ReplaceRequest",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
