"""AppSetting resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.app_setting.models import *
    from f5xc_py_substrate.resources.app_setting.resource import AppSettingResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "AppSettingResource":
        from f5xc_py_substrate.resources.app_setting.resource import AppSettingResource
        return AppSettingResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.app_setting.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.app_setting' has no attribute '{name}'")


__all__ = [
    "AppSettingResource",
    "ObjectRefType",
    "Empty",
    "BusinessLogicMarkupSetting",
    "MetricSelector",
    "TimeseriesAnalysesSetting",
    "FailedLoginActivitySetting",
    "ForbiddenActivitySetting",
    "NonexistentUrlAutomaticActivitySetting",
    "NonexistentUrlCustomActivitySetting",
    "MaliciousUserDetectionSetting",
    "UserBehaviorAnalysisSetting",
    "AppTypeSettings",
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
    "DeleteRequest",
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
    "SuspiciousUser",
    "SuspiciousUserStatusRsp",
    "Spec",
]
