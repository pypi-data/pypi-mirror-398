"""Fleet resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.fleet.models import *
    from f5xc_py_substrate.resources.fleet.resource import FleetResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "FleetResource":
        from f5xc_py_substrate.resources.fleet.resource import FleetResource
        return FleetResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.fleet.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.fleet' has no attribute '{name}'")


__all__ = [
    "FleetResource",
    "Empty",
    "BlockedServices",
    "BondLacpType",
    "ObjectCreateMetaType",
    "BondDeviceType",
    "BondDevicesListType",
    "ObjectRefType",
    "ObjectRefType",
    "NetworkingDeviceInstanceType",
    "DeviceInstanceType",
    "DeviceListType",
    "VGPUConfiguration",
    "VMConfiguration",
    "InterfaceListType",
    "KubernetesUpgradeDrainConfig",
    "KubernetesUpgradeDrain",
    "L3PerformanceEnhancementType",
    "PerformanceEnhancementModeType",
    "SriovInterface",
    "SriovInterfacesListType",
    "StorageClassCustomType",
    "StorageClassHpeStorageType",
    "StorageClassNetappTridentType",
    "StorageClassPureServiceOrchestratorType",
    "StorageClassType",
    "StorageClassListType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "StorageDeviceHpeStorageType",
    "PrefixStringListType",
    "OntapVolumeDefaults",
    "OntapVirtualStoragePoolType",
    "StorageDeviceNetappBackendOntapNasType",
    "DeviceNetappBackendOntapSanChapType",
    "StorageDeviceNetappBackendOntapSanType",
    "StorageDeviceNetappTridentType",
    "FlashArrayEndpoint",
    "FlashArrayType",
    "FlashBladeEndpoint",
    "FlashBladeType",
    "PsoArrayConfiguration",
    "StorageDevicePureStorageServiceOrchestratorType",
    "StorageDeviceType",
    "StorageDeviceListType",
    "Ipv4AddressType",
    "Ipv6AddressType",
    "IpAddressType",
    "NextHopType",
    "Ipv4SubnetType",
    "Ipv6SubnetType",
    "IpSubnetType",
    "StaticRouteType",
    "StorageStaticRoutesListType",
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
    "Status",
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
    "Spec",
]
