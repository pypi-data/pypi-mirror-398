"""Signup resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.signup.models import *
    from f5xc_py_substrate.resources.signup.resource import SignupResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "SignupResource":
        from f5xc_py_substrate.resources.signup.resource import SignupResource
        return SignupResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.signup.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.signup' has no attribute '{name}'")


__all__ = [
    "SignupResource",
    "Policer",
    "BlindfoldSecretInfoType",
    "CRMInfo",
    "ClearSecretInfoType",
    "ConditionType",
    "Empty",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectMetaType",
    "ObjectRefType",
    "SecretType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectMetaType",
    "GlobalSpecType",
    "GlobalSpecType",
    "GlobalSpecType",
    "GlobalSpecType",
    "CityItem",
    "CountryItem",
    "SpecType",
    "Object",
    "StatusObject",
    "GetResponse",
    "ListCitiesResponse",
    "ListCountriesResponse",
    "StateItem",
    "ListStatesResponse",
    "SendPasswordEmailRequest",
    "SendPasswordEmailResponse",
    "ValidateContactRequest",
    "ValidationErrorField",
    "ValidateContactResponse",
    "ValidateRegistrationRequest",
    "ValidateRegistrationResponse",
    "Spec",
]
