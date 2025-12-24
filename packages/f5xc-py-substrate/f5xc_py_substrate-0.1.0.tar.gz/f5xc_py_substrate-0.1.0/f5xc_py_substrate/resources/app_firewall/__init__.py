"""AppFirewall resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.app_firewall.models import *
    from f5xc_py_substrate.resources.app_firewall.resource import AppFirewallResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AppFirewallResource":
        from f5xc_py_substrate.resources.app_firewall.resource import AppFirewallResource
        return AppFirewallResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.app_firewall.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.app_firewall' has no attribute '{name}'")


__all__ = [
    "AppFirewallResource",
    "AiRiskBasedBlocking",
    "AllowedResponseCodes",
    "AnonymizeHttpCookie",
    "AnonymizeHttpHeader",
    "AnonymizeHttpQueryParameter",
    "AnonymizationConfiguration",
    "AnonymizationSetting",
    "AttackTypeSettings",
    "BotProtectionSetting",
    "ObjectCreateMetaType",
    "Empty",
    "CustomBlockingPage",
    "SignatureSelectionSetting",
    "SignaturesStagingSettings",
    "ViolationSettings",
    "DetectionSetting",
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
    "ObjectRefType",
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
    "TrendValue",
    "MetricValue",
    "MetricTypeData",
    "MetricData",
    "MetricsResponse",
    "ReplaceResponse",
    "Spec",
]
