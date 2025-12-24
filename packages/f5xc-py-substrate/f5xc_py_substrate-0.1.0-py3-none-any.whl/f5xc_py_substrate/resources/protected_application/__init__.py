"""ProtectedApplication resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.protected_application.models import *
    from f5xc_py_substrate.resources.protected_application.resource import ProtectedApplicationResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ProtectedApplicationResource":
        from f5xc_py_substrate.resources.protected_application.resource import ProtectedApplicationResource
        return ProtectedApplicationResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.protected_application.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.protected_application' has no attribute '{name}'")


__all__ = [
    "ProtectedApplicationResource",
    "Empty",
    "DomainType",
    "MessageMetaType",
    "PathMatcherType",
    "JavaScriptExclusionRule",
    "JavaScriptInsertionRule",
    "JavaScriptInsertType",
    "JavaScriptInsertManualType",
    "HeaderMatcherType",
    "MobileTrafficIdentifierType",
    "MobileSDKConfigType",
    "BlockMobileMitigationChoiceType",
    "ContinueMitigationChoiceType",
    "MobileClientType",
    "PathType",
    "BlockMitigationChoiceType",
    "RedirectMitigationChoiceType",
    "WebClientType",
    "WebMobileClientType",
    "ProtectedEndpointType",
    "HttpHeaderMatcherList",
    "ClientBypassRule",
    "CloudflareType",
    "DistributionIDList",
    "DistributionTagList",
    "JavaScriptExclusionRule",
    "JavaScriptInsertionRule",
    "JavaScriptInsertType",
    "JavaScriptInsertManualType",
    "HeaderMatcherType",
    "MobileTrafficIdentifierType",
    "MobileSDKConfigType",
    "BotDefenseFlowLabelAccountManagementChoiceType",
    "BotDefenseTransactionResultCondition",
    "BotDefenseTransactionResultType",
    "BotDefenseTransactionResult",
    "BotDefenseFlowLabelAuthenticationChoiceType",
    "BotDefenseFlowLabelFinancialServicesChoiceType",
    "BotDefenseFlowLabelFlightChoiceType",
    "BotDefenseFlowLabelProfileManagementChoiceType",
    "BotDefenseFlowLabelSearchChoiceType",
    "BotDefenseFlowLabelShoppingGiftCardsChoiceType",
    "BotDefenseFlowLabelCategoriesChoiceType",
    "BlockMobileMitigationChoiceType",
    "ContinueMitigationChoiceType",
    "MobileClientType",
    "BlockMitigationChoiceType",
    "RedirectMitigationChoiceType",
    "WebClientType",
    "WebMobileClientType",
    "ProtectedEndpointType",
    "HttpHeaderMatcherList",
    "ClientBypassRule",
    "CloudfrontType",
    "CreateSpecType",
    "ObjectRefType",
    "XCMeshConnector",
    "GetSpecType",
    "ReplaceSpecType",
    "ObjectRefType",
    "ApiEndpoint",
    "ApiKeyResponse",
    "ConnectorConfigResponse",
    "ObjectCreateMetaType",
    "CreateRequest",
    "ObjectGetMetaType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "DeleteRequest",
    "ObjectReplaceMetaType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "Region",
    "RegionsListResponse",
    "ReplaceResponse",
    "TemplateConnectorResponse",
    "Spec",
]
