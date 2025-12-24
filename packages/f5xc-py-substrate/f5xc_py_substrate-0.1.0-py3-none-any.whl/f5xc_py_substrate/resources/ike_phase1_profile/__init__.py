"""IkePhase1Profile resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.ike_phase1_profile.models import *
    from f5xc_py_substrate.resources.ike_phase1_profile.resource import IkePhase1ProfileResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "IkePhase1ProfileResource":
        from f5xc_py_substrate.resources.ike_phase1_profile.resource import IkePhase1ProfileResource
        return IkePhase1ProfileResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.ike_phase1_profile.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.ike_phase1_profile' has no attribute '{name}'")


__all__ = [
    "IkePhase1ProfileResource",
    "ObjectCreateMetaType",
    "IkePhase1Profileinputhours",
    "IkePhase1Profileinputminutes",
    "Empty",
    "IkePhase1Profileinputdays",
    "IkePhase1Profilecreatespectype",
    "IkePhase1Profilecreaterequest",
    "ObjectGetMetaType",
    "IkePhase1Profilegetspectype",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "IkePhase1Profilecreateresponse",
    "IkePhase1Profiledeleterequest",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "IkePhase1Profilereplacespectype",
    "IkePhase1Profilereplacerequest",
    "ConditionType",
    "StatusMetaType",
    "IkePhase1Profilestatusobject",
    "IkePhase1Profilegetresponse",
    "ProtobufAny",
    "ErrorType",
    "IkePhase1Profilelistresponseitem",
    "IkePhase1Profilelistresponse",
    "IkePhase1Profilereplaceresponse",
    "Spec",
]
