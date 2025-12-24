"""Apm resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.apm.models import *
    from f5xc_py_substrate.resources.apm.resource import ApmResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ApmResource":
        from f5xc_py_substrate.resources.apm.resource import ApmResource
        return ApmResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.apm.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.apm' has no attribute '{name}'")


__all__ = [
    "ApmResource",
    "Empty",
    "PortRangesType",
    "EndpointServiceReplaceType",
    "APMBigIpAWSReplaceType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "ObjectRefType",
    "F5BigIpAWSTGWSiteType",
    "EndpointServiceType",
    "CloudSubnetParamType",
    "CloudSubnetType",
    "ServiceNodesAWSType",
    "APMBigIpAWSType",
    "AWSMarketPlaceImageTypeAPMaaS",
    "AWSSiteTypeChoice",
    "AWSSiteTypeChoiceReplaceType",
    "ObjectCreateMetaType",
    "BigIqInstanceType",
    "InterfaceDetails",
    "ServiceNodesBareMetalType",
    "F5BigIpAppStackBareMetalType",
    "F5BigIpAppStackBareMetalTypeChoice",
    "AdvertisePublic",
    "HashAlgorithms",
    "TlsCertificateType",
    "CustomCiphers",
    "TlsConfig",
    "XfccHeaderKeys",
    "DownstreamTlsValidationContext",
    "DownstreamTlsParamsType",
    "ServiceHttpsManagementType",
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
    "F5BigIpAppStackBareMetalChoiceReplaceType",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "ApplyStatus",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "TrendValue",
    "MetricValue",
    "MetricTypeData",
    "MetricData",
    "MetricsRequest",
    "MetricsResponse",
    "ReplaceResponse",
    "Spec",
]
