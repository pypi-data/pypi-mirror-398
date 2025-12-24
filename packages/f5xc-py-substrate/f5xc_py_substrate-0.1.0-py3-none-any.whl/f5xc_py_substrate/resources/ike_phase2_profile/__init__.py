"""IkePhase2Profile resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.ike_phase2_profile.models import *
    from f5xc_py_substrate.resources.ike_phase2_profile.resource import IkePhase2ProfileResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "IkePhase2ProfileResource":
        from f5xc_py_substrate.resources.ike_phase2_profile.resource import IkePhase2ProfileResource
        return IkePhase2ProfileResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.ike_phase2_profile.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.ike_phase2_profile' has no attribute '{name}'")


__all__ = [
    "IkePhase2ProfileResource",
    "IkePhase1Profileinputhours",
    "IkePhase1Profileinputminutes",
    "ObjectCreateMetaType",
    "IkePhase2Profiledhgroups",
    "Empty",
    "ViewsikePhase2Profilecreatespectype",
    "IkePhase2Profilecreaterequest",
    "ObjectGetMetaType",
    "ViewsikePhase2Profilegetspectype",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "IkePhase2Profilecreateresponse",
    "IkePhase2Profiledeleterequest",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ViewsikePhase2Profilereplacespectype",
    "IkePhase2Profilereplacerequest",
    "ConditionType",
    "StatusMetaType",
    "IkePhase2Profilestatusobject",
    "IkePhase2Profilegetresponse",
    "ProtobufAny",
    "ErrorType",
    "IkePhase2Profilelistresponseitem",
    "IkePhase2Profilelistresponse",
    "IkePhase2Profilereplaceresponse",
    "Spec",
]
