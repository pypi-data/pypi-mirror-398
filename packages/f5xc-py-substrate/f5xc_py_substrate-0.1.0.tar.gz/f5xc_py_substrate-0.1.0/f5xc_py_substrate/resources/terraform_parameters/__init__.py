"""TerraformParameters resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.terraform_parameters.models import *
    from f5xc_py_substrate.resources.terraform_parameters.resource import TerraformParametersResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "TerraformParametersResource":
        from f5xc_py_substrate.resources.terraform_parameters.resource import TerraformParametersResource
        return TerraformParametersResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.terraform_parameters.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.terraform_parameters' has no attribute '{name}'")


__all__ = [
    "TerraformParametersResource",
    "ObjectRefType",
    "ProtobufAny",
    "ConditionType",
    "StatusMetaType",
    "ApplyStatus",
    "ForceDeleteRequest",
    "ForceDeleteResponse",
    "GlobalSpecType",
    "GetResponse",
    "PlanStatus",
    "StatusObject",
    "GetStatusResponse",
    "RunRequest",
    "RunResponse",
    "Spec",
]
