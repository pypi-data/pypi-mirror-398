"""BigipVirtualServer resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.bigip_virtual_server.models import *
    from f5xc_py_substrate.resources.bigip_virtual_server.resource import BigipVirtualServerResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "BigipVirtualServerResource":
        from f5xc_py_substrate.resources.bigip_virtual_server.resource import BigipVirtualServerResource
        return BigipVirtualServerResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.bigip_virtual_server.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.bigip_virtual_server' has no attribute '{name}'")


__all__ = [
    "BigipVirtualServerResource",
    "DiscoveredAPISettings",
    "BigIPVirtualServerList",
    "ObjectRefType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "ObjectRefType",
    "Empty",
    "ApiEndpointDetails",
    "MessageMetaType",
    "FallThroughRule",
    "CustomFallThroughMode",
    "OpenApiFallThroughMode",
    "ValidationSettingForQueryParameters",
    "ValidationPropertySetting",
    "OpenApiValidationCommonSettings",
    "OpenApiValidationModeActiveResponse",
    "OpenApiValidationModeActive",
    "OpenApiValidationMode",
    "OpenApiValidationAllSpecEndpointsSettings",
    "OpenApiValidationRule",
    "ValidateApiBySpecRule",
    "APISpecificationSettings",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "SimpleLogin",
    "DomainConfiguration",
    "ApiCrawlerConfiguration",
    "ApiCrawler",
    "ApiCodeRepos",
    "CodeBaseIntegrationSelection",
    "ApiDiscoveryFromCodeScan",
    "ApiDiscoveryAdvancedSettings",
    "ApiDiscoverySetting",
    "SensitiveDataPolicySettings",
    "ReplaceSpecType",
    "ReplaceRequest",
    "GetSpecType",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "GetResponse",
    "GetSecurityConfigReq",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "GetSecurityConfigRsp",
    "Spec",
]
