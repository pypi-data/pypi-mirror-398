"""ThirdPartyApplication resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.third_party_application.models import *
    from f5xc_py_substrate.resources.third_party_application.resource import ThirdPartyApplicationResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ThirdPartyApplicationResource":
        from f5xc_py_substrate.resources.third_party_application.resource import ThirdPartyApplicationResource
        return ThirdPartyApplicationResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.third_party_application.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.third_party_application' has no attribute '{name}'")


__all__ = [
    "ThirdPartyApplicationResource",
    "DiscoveredAPISettings",
    "GetSecurityConfigRsp",
    "ObjectRefType",
    "SensitiveDataPolicySettings",
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
    "ApiCodeRepos",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "SimpleLogin",
    "DomainConfiguration",
    "ApiCrawlerConfiguration",
    "ApiCrawler",
    "ApiDiscoveryAdvancedSettings",
    "CodeBaseIntegrationSelection",
    "ApiDiscoveryFromCodeScan",
    "ApiDiscoverySetting",
    "ObjectRefType",
    "ProtobufAny",
    "ConditionType",
    "ErrorType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "GenerateTokenResponse",
    "ReplaceSpecType",
    "ReplaceRequest",
    "GetSpecType",
    "StatusObject",
    "GetResponse",
    "ThirdPartyApplicationList",
    "GetSecurityConfigReq",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
