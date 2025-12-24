"""Namespace resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.namespace.models import *
    from f5xc_py_substrate.resources.namespace.resource import NamespaceResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "NamespaceResource":
        from f5xc_py_substrate.resources.namespace.resource import NamespaceResource
        return NamespaceResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.namespace.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.namespace' has no attribute '{name}'")


__all__ = [
    "NamespaceResource",
    "ObjectRefType",
    "AlertPolicyStatus",
    "Empty",
    "ObjectRefType",
    "APIItemReq",
    "APIItemListReq",
    "AccessEnablerAddonService",
    "APIItemResp",
    "APIItemListResp",
    "BIGIPVirtualServerInventoryFilterType",
    "HTTPLoadbalancerInventoryFilterType",
    "NGINXOneServerInventoryFilterType",
    "TCPLoadbalancerInventoryFilterType",
    "ThirdPartyApplicationFilterType",
    "UDPLoadbalancerInventoryFilterType",
    "AllApplicationInventoryRequest",
    "AllApplicationInventoryWafFilterRequest",
    "HTTPLoadbalancerWafFilterResultType",
    "AllApplicationInventoryWafFilterResponse",
    "ApiEndpointsStatsAllNSReq",
    "ApiEndpointsStatsNSReq",
    "ApiEndpointsStatsNSRsp",
    "ApplicationInventoryRequest",
    "BIGIPVirtualServerResultType",
    "BIGIPVirtualServerInventoryType",
    "HTTPLoadbalancerResultType",
    "HTTPLoadbalancerInventoryType",
    "NGINXOneServerResultType",
    "NGINXOneServerInventoryType",
    "TCPLoadbalancerResultType",
    "TCPLoadbalancerInventoryType",
    "ThirdPartyApplicationResultType",
    "ThirdPartyApplicationInventoryType",
    "UDPLoadbalancerResultType",
    "UDPLoadbalancerInventoryType",
    "ApplicationInventoryResponse",
    "CascadeDeleteItemType",
    "CascadeDeleteRequest",
    "CascadeDeleteResponse",
    "ObjectCreateMetaType",
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
    "EvaluateAPIAccessReq",
    "EvaluateAPIAccessResp",
    "APIListReq",
    "EvaluateBatchAPIAccessReq",
    "APIListResp",
    "EvaluateBatchAPIAccessResp",
    "GetActiveAlertPoliciesResponse",
    "GetActiveNetworkPoliciesResponse",
    "GetActiveServicePoliciesResponse",
    "GetFastACLsForInternetVIPsResponse",
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
    "LookupUserRolesReq",
    "LookupUserRolesResp",
    "NetworkingInventoryRequest",
    "NetworkingInventoryResponse",
    "ReplaceResponse",
    "SetActiveAlertPoliciesRequest",
    "SetActiveAlertPoliciesResponse",
    "SetActiveNetworkPoliciesRequest",
    "SetActiveNetworkPoliciesResponse",
    "SetActiveServicePoliciesRequest",
    "SetActiveServicePoliciesResponse",
    "SetFastACLsForInternetVIPsRequest",
    "SetFastACLsForInternetVIPsResponse",
    "UpdateAllowAdvertiseOnPublicReq",
    "UpdateAllowAdvertiseOnPublicResp",
    "ValidateRulesReq",
    "ValidationResult",
    "ValidateRulesResponse",
    "SuggestedItem",
    "SuggestValuesResp",
    "Spec",
]
