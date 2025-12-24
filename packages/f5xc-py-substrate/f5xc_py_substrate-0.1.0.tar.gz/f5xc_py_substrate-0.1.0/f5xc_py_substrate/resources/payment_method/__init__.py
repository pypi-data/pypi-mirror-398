"""PaymentMethod resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.payment_method.models import *
    from f5xc_py_substrate.resources.payment_method.resource import PaymentMethodResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "PaymentMethodResource":
        from f5xc_py_substrate.resources.payment_method.resource import PaymentMethodResource
        return PaymentMethodResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.payment_method.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.payment_method' has no attribute '{name}'")


__all__ = [
    "PaymentMethodResource",
    "GlobalSpecType",
    "CreatePaymentMethodRequest",
    "CreatePaymentMethodResponse",
    "PrimaryReq",
    "RoleSwapReq",
    "SecondaryReq",
    "Spec",
]
