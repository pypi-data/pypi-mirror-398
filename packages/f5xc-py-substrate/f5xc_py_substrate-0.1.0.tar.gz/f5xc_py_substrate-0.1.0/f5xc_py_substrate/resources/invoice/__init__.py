"""Invoice resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.invoice.models import *
    from f5xc_py_substrate.resources.invoice.resource import InvoiceResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "InvoiceResource":
        from f5xc_py_substrate.resources.invoice.resource import InvoiceResource
        return InvoiceResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.invoice.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.invoice' has no attribute '{name}'")


__all__ = [
    "InvoiceResource",
    "DownloadInvoicePdfRsp",
    "InvoiceType",
    "ListInvoicesRsp",
    "Spec",
]
