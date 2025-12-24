"""Workload resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.workload.models import *
    from f5xc_py_substrate.resources.workload.resource import WorkloadResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "WorkloadResource":
        from f5xc_py_substrate.resources.workload.resource import WorkloadResource
        return WorkloadResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.workload.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.workload' has no attribute '{name}'")


__all__ = [
    "WorkloadResource",
    "ProxyTypeHttp",
    "Empty",
    "TLSCoalescingOptions",
    "HeaderTransformationType",
    "Http1ProtocolOptions",
    "HttpProtocolOptions",
    "ObjectRefType",
    "CustomCiphers",
    "TlsConfig",
    "XfccHeaderKeys",
    "DownstreamTlsValidationContext",
    "DownstreamTLSCertsParams",
    "HashAlgorithms",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "TlsCertificateType",
    "DownstreamTlsParamsType",
    "ProxyTypeHttps",
    "ProxyTypeHttpsAutoCerts",
    "RouteTypeCustomRoute",
    "HeaderMatcherType",
    "PortMatcherType",
    "PathMatcherType",
    "RouteDirectResponse",
    "RouteTypeDirectResponse",
    "RouteRedirect",
    "RouteTypeRedirect",
    "RouteTypeSimpleWithDefaultOriginPool",
    "ObjectRefType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "KubeRefType",
    "TrendValue",
    "MetricValue",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "WhereSite",
    "WhereVK8SService",
    "WhereVirtualSite",
    "EnvironmentVariableType",
    "VolumeMountType",
    "ConfigurationFileType",
    "ConfigurationParameterType",
    "ConfigurationParametersType",
    "ImageType",
    "ExecHealthCheckType",
    "PortChoiceType",
    "HTTPHealthCheckType",
    "TCPHealthCheckType",
    "HealthCheckType",
    "ContainerType",
    "DeployCESiteType",
    "DeployCEVirtualSiteType",
    "DeployRESiteType",
    "DeployREVirtualSiteType",
    "DeployOptionsType",
    "EmptyDirectoryVolumeType",
    "HostPathVolumeType",
    "PersistentStorageType",
    "PersistentStorageVolumeType",
    "StorageVolumeType",
    "JobType",
    "AdvertiseWhereType",
    "MatchAllRouteType",
    "RouteInfoType",
    "RouteType",
    "HTTPLoadBalancerType",
    "PortInfoType",
    "PortType",
    "TCPLoadBalancerType",
    "AdvertisePortType",
    "AdvertiseCustomType",
    "MultiPortType",
    "SinglePortType",
    "AdvertiseInClusterType",
    "AdvertiseMultiPortType",
    "AdvertiseSinglePortType",
    "AdvertisePublicType",
    "AdvertiseOptionsType",
    "ServiceType",
    "PersistentVolumeType",
    "AdvertiseSimpleServiceType",
    "SimpleServiceType",
    "EphemeralStorageVolumeType",
    "StatefulServiceType",
    "CreateSpecType",
    "GetSpecType",
    "ReplaceSpecType",
    "CreateRequest",
    "CreateResponse",
    "DeleteRequest",
    "ReplaceRequest",
    "StatusObject",
    "GetResponse",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "UsageTypeData",
    "UsageData",
    "UsageRequest",
    "UsageResponse",
    "Spec",
]
