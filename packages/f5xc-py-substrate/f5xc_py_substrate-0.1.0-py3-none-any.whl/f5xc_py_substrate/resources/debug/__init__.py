"""Debug resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.debug.models import *
    from f5xc_py_substrate.resources.debug.resource import DebugResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "DebugResource":
        from f5xc_py_substrate.resources.debug.resource import DebugResource
        return DebugResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.debug.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.debug' has no attribute '{name}'")


__all__ = [
    "DebugResource",
    "ProtobufAny",
    "HttpBody",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "ChangePasswordRequest",
    "CheckDebugInfoCollectionResponse",
    "DiagnosisResponse",
    "ExecLogResponse",
    "ExecResponse",
    "Bios",
    "Board",
    "Chassis",
    "Cpu",
    "GPUDevice",
    "GPU",
    "Kernel",
    "Memory",
    "NetworkDevice",
    "OS",
    "Product",
    "StorageDevice",
    "USBDevice",
    "OsInfo",
    "HealthResponse",
    "HostPingRequest",
    "HostPingResponse",
    "Service",
    "ListServicesResponse",
    "LogResponse",
    "RebootRequest",
    "RebootResponse",
    "SoftRestartRequest",
    "SoftRestartResponse",
    "Status",
    "StatusResponse",
    "Spec",
]
