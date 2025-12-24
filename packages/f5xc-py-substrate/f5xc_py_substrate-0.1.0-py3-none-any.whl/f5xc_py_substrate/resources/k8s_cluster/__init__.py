"""K8sCluster resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.k8s_cluster.models import *
    from f5xc_py_substrate.resources.k8s_cluster.resource import K8sClusterResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "K8sClusterResource":
        from f5xc_py_substrate.resources.k8s_cluster.resource import K8sClusterResource
        return K8sClusterResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.k8s_cluster.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.k8s_cluster' has no attribute '{name}'")


__all__ = [
    "K8sClusterResource",
    "Empty",
    "ObjectRefType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "K8sClusterlocalaccessargocdtype",
    "K8sClusterapplicationargocdtype",
    "K8sClusterapplicationdashboardtype",
    "K8sClusterapplicationmetricsservertype",
    "K8sClusterapplicationprometheustype",
    "ObjectRefType",
    "K8sClusterclusterrolebindinglisttype",
    "K8sClusterclusterrolelisttype",
    "K8sClusterclusterwideapptype",
    "K8sClusterclusterwideapplisttype",
    "ObjectCreateMetaType",
    "K8sClusterinsecureregistrylisttype",
    "K8sClusterlocalaccessconfigtype",
    "K8sClusterpodsecuritypolicylisttype",
    "K8sClustercreatespectype",
    "K8sClustercreaterequest",
    "ObjectGetMetaType",
    "K8sClustergetspectype",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "K8sClustercreateresponse",
    "K8sClusterdeleterequest",
    "ObjectReplaceMetaType",
    "K8sClusterreplacespectype",
    "K8sClusterreplacerequest",
    "ConditionType",
    "StatusMetaType",
    "K8sClusterstatusobject",
    "K8sClustergetresponse",
    "ProtobufAny",
    "ErrorType",
    "K8sClusterlistresponseitem",
    "K8sClusterlistresponse",
    "K8sClusterreplaceresponse",
    "Spec",
]
