"""K8sPodSecurityAdmission resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.k8s_pod_security_admission.models import *
    from f5xc_py_substrate.resources.k8s_pod_security_admission.resource import K8sPodSecurityAdmissionResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "K8sPodSecurityAdmissionResource":
        from f5xc_py_substrate.resources.k8s_pod_security_admission.resource import K8sPodSecurityAdmissionResource
        return K8sPodSecurityAdmissionResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.k8s_pod_security_admission.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.k8s_pod_security_admission' has no attribute '{name}'")


__all__ = [
    "K8sPodSecurityAdmissionResource",
    "Empty",
    "ObjectRefType",
    "ObjectCreateMetaType",
    "K8sPodSecurityAdmissionpodsecurityadmissionspec",
    "K8sPodSecurityAdmissioncreatespectype",
    "K8sPodSecurityAdmissioncreaterequest",
    "ObjectGetMetaType",
    "K8sPodSecurityAdmissiongetspectype",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "K8sPodSecurityAdmissioncreateresponse",
    "K8sPodSecurityAdmissiondeleterequest",
    "ObjectReplaceMetaType",
    "K8sPodSecurityAdmissionreplacespectype",
    "K8sPodSecurityAdmissionreplacerequest",
    "ConditionType",
    "StatusMetaType",
    "K8sPodSecurityAdmissionstatusobject",
    "K8sPodSecurityAdmissiongetresponse",
    "ProtobufAny",
    "ErrorType",
    "K8sPodSecurityAdmissionlistresponseitem",
    "K8sPodSecurityAdmissionlistresponse",
    "K8sPodSecurityAdmissionreplaceresponse",
    "Spec",
]
