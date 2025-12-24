"""CloudElasticIp resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.cloud_elastic_ip.models import *
    from f5xc_py_substrate.resources.cloud_elastic_ip.resource import CloudElasticIpResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "CloudElasticIpResource":
        from f5xc_py_substrate.resources.cloud_elastic_ip.resource import CloudElasticIpResource
        return CloudElasticIpResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.cloud_elastic_ip.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.cloud_elastic_ip' has no attribute '{name}'")


__all__ = [
    "CloudElasticIpResource",
    "ObjectCreateMetaType",
    "ObjectRefType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "DeleteRequest",
    "ElasticIPInfoType",
    "ElasticIPStatusType",
    "ForceDeleteCloudElasticIPRequest",
    "ForceDeleteCloudElasticIPResponse",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
