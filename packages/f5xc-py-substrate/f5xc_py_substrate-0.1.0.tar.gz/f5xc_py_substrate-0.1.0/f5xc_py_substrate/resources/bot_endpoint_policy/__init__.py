"""BotEndpointPolicy resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.bot_endpoint_policy.models import *
    from f5xc_py_substrate.resources.bot_endpoint_policy.resource import BotEndpointPolicyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "BotEndpointPolicyResource":
        from f5xc_py_substrate.resources.bot_endpoint_policy.resource import BotEndpointPolicyResource
        return BotEndpointPolicyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.bot_endpoint_policy.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.bot_endpoint_policy' has no attribute '{name}'")


__all__ = [
    "BotEndpointPolicyResource",
    "GenericEmptyType",
    "CookieMatcherValue",
    "CookieMatcherType",
    "CookieMatcher",
    "Empty",
    "Cookie",
    "DomainMatcherType",
    "DomainMatcher",
    "DomainOperator",
    "MatcherValue",
    "MatcherType",
    "HeaderMatcher",
    "HeaderNameValuePair",
    "HeaderOperatorEmptyType",
    "HeaderOperator",
    "PathMatcherValue",
    "PathMatcherType",
    "PathMatcher",
    "PathOperator",
    "PolicyVersion",
    "WebClientBlockMitigationActionType",
    "WebClientContinueMitigationHeader",
    "WebClientContinueMitigationActionType",
    "BotPolicyFlowLabelAccountManagementChoiceType",
    "BotPolicyFlowLabelAuthenticationChoiceType",
    "BotPolicyFlowLabelCreditCardChoiceType",
    "BotPolicyFlowLabelDeliveryServicesChoiceType",
    "BotPolicyFlowLabelFinancialServicesChoiceType",
    "BotPolicyFlowLabelFlightChoiceType",
    "BotPolicyFlowLabelGuestSessionChoiceType",
    "BotPolicyFlowLabelLoyaltyChoiceType",
    "BotPolicyFlowLabelMailingListChoiceType",
    "BotPolicyFlowLabelMediaChoiceType",
    "BotPolicyFlowLabelMiscellaneousChoiceType",
    "BotPolicyFlowLabelProfileManagementChoiceType",
    "BotPolicyFlowLabelQuotesChoiceType",
    "BotPolicyFlowLabelSearchChoiceType",
    "BotPolicyFlowLabelShoppingGiftCardsChoiceType",
    "BotPolicyFlowLabelSocialsChoiceType",
    "BotPolicyFlowLabelCategoriesChoiceType",
    "MessageMetaType",
    "QueryMatcher",
    "QueryOperator",
    "RequestBodyMatcher",
    "RequestBodyOperator",
    "ResponseBodyMatcherValue",
    "ResponseBodyMatcherType",
    "ResponseBodyMatcher",
    "ResponseBody",
    "ResponseCodeMatcherType",
    "ResponseCodeMatcher",
    "ResponseCode",
    "ResponseHeaderMatcherValue",
    "ResponseHeaderMatcherType",
    "ResponseHeaderMatcher",
    "ResponseHeader",
    "TransactionResultType",
    "TransactionResult",
    "WebClientAddHeaderToRequest",
    "WebClientTransformMitigationActionChoiceType",
    "UserNameType",
    "ProtectedMobileEndpoint",
    "ProtectedMobileEndpointList",
    "WebClientRedirectMitigationActionType",
    "ProtectedWebEndpoint",
    "ProtectedWebEndpointList",
    "ProtectedEndpoints",
    "ReplaceSpecType",
    "CustomReplaceRequest",
    "CustomReplaceResponse",
    "GetContentResponse",
    "Policy",
    "GetPoliciesAndVersionsListResponse",
    "ObjectRefType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
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
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "PolicyVersionsResponse",
    "ReplaceResponse",
    "Spec",
]
