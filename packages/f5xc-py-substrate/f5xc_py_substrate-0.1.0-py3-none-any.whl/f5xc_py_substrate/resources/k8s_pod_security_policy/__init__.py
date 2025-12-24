"""K8sPodSecurityPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.k8s_pod_security_policy.models import *
    from f5xc_py_substrate.resources.k8s_pod_security_policy.resource import K8sPodSecurityPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "K8sPodSecurityPolicyResource":
        from f5xc_py_substrate.resources.k8s_pod_security_policy.resource import K8sPodSecurityPolicyResource
        return K8sPodSecurityPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.k8s_pod_security_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.k8s_pod_security_policy' has no attribute '{name}'")


__all__ = [
    "K8sPodSecurityPolicyResource",
    "Empty",
    "K8sPodSecurityPolicycapabilitylisttype",
    "ObjectCreateMetaType",
    "K8sPodSecurityPolicyhostpathtype",
    "K8sPodSecurityPolicyidrangetype",
    "K8sPodSecurityPolicyidstrategyoptionstype",
    "K8sPodSecurityPolicypodsecuritypolicyspectype",
    "K8sPodSecurityPolicycreatespectype",
    "K8sPodSecurityPolicycreaterequest",
    "ObjectGetMetaType",
    "K8sPodSecurityPolicygetspectype",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "K8sPodSecurityPolicycreateresponse",
    "K8sPodSecurityPolicydeleterequest",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "K8sPodSecurityPolicyreplacespectype",
    "K8sPodSecurityPolicyreplacerequest",
    "ConditionType",
    "StatusMetaType",
    "K8sPodSecurityPolicystatusobject",
    "K8sPodSecurityPolicygetresponse",
    "ProtobufAny",
    "ErrorType",
    "K8sPodSecurityPolicylistresponseitem",
    "K8sPodSecurityPolicylistresponse",
    "K8sPodSecurityPolicyreplaceresponse",
    "Spec",
]
