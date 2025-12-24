"""K8sClusterRole resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.k8s_cluster_role.models import *
    from f5xc_py_substrate.resources.k8s_cluster_role.resource import K8sClusterRoleResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "K8sClusterRoleResource":
        from f5xc_py_substrate.resources.k8s_cluster_role.resource import K8sClusterRoleResource
        return K8sClusterRoleResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.k8s_cluster_role.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.k8s_cluster_role' has no attribute '{name}'")


__all__ = [
    "K8sClusterRoleResource",
    "ObjectCreateMetaType",
    "LabelSelectorType",
    "K8sClusterRolenonresourceurllisttype",
    "K8sClusterRoleresourcelisttype",
    "K8sClusterRolepolicyruletype",
    "K8sClusterRolepolicyrulelisttype",
    "K8sClusterRolecreatespectype",
    "K8sClusterRolecreaterequest",
    "ObjectGetMetaType",
    "K8sClusterRolegetspectype",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "K8sClusterRolecreateresponse",
    "K8sClusterRoledeleterequest",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "K8sClusterRolereplacespectype",
    "K8sClusterRolereplacerequest",
    "ConditionType",
    "StatusMetaType",
    "K8sClusterRolestatusobject",
    "K8sClusterRolegetresponse",
    "ProtobufAny",
    "ErrorType",
    "K8sClusterRolelistresponseitem",
    "K8sClusterRolelistresponse",
    "K8sClusterRolereplaceresponse",
    "Spec",
]
