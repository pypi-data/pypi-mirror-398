"""NfvService resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.nfv_service.models import *
    from f5xc_py_substrate.resources.nfv_service.resource import NfvServiceResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NfvServiceResource":
        from f5xc_py_substrate.resources.nfv_service.resource import NfvServiceResource
        return NfvServiceResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.nfv_service.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.nfv_service' has no attribute '{name}'")


__all__ = [
    "NfvServiceResource",
    "Empty",
    "ObjectRefType",
    "ObjectCreateMetaType",
    "SSHManagementNodePorts",
    "SSHManagementType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "ObjectRefType",
    "F5BigIpAWSTGWSiteType",
    "PortRangesType",
    "EndpointServiceType",
    "F5BigIpAWSMarketPlaceImageType",
    "CloudSubnetParamType",
    "CloudSubnetType",
    "ServiceNodesAWSType",
    "F5BigIpAWSType",
    "AdvertisePublic",
    "HashAlgorithms",
    "TlsCertificateType",
    "CustomCiphers",
    "TlsConfig",
    "XfccHeaderKeys",
    "DownstreamTlsValidationContext",
    "DownstreamTlsParamsType",
    "ServiceHttpsManagementType",
    "SSHKeyType",
    "PANAWSAutoSetupType",
    "PanoramaServerType",
    "PaloAltoServiceNodesAWSType",
    "PaloAltoAzNodesAWSType",
    "PaloAltoFWAWSType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "ForwardingServiceType",
    "NodeInfo",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "DeleteRequest",
    "EndpointServiceReplaceType",
    "F5BigIpAWSReplaceType",
    "ForceDeleteNFVServiceRequest",
    "ForceDeleteNFVServiceResponse",
    "ObjectReplaceMetaType",
    "PaloAltoFWAWSReplaceType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "ApplyStatus",
    "Viewsk8sManifestParamsdeploymentstatustype",
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
