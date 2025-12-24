"""CloudConnect resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.cloud_connect.models import *
    from f5xc_py_substrate.resources.cloud_connect.resource import CloudConnectResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "CloudConnectResource":
        from f5xc_py_substrate.resources.cloud_connect.resource import CloudConnectResource
        return CloudConnectResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.cloud_connect.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.cloud_connect' has no attribute '{name}'")


__all__ = [
    "CloudConnectResource",
    "AWSRouteTableType",
    "AWSRouteTableListType",
    "SubnetStatusType",
    "AWSAttachmentsStatusType",
    "AWSConnectPeerStatusType",
    "AWSConnectAttachmentStatusType",
    "AWSTGWResourceReference",
    "AWSTGWRouteTableStatusType",
    "AWSAttachmentsListStatusType",
    "AWSDefaultRoutesRouteTable",
    "ObjectRefType",
    "Ipv4AddressType",
    "Ipv6AddressType",
    "IpAddressType",
    "NodeType",
    "PeerType",
    "Empty",
    "DefaultRoute",
    "AWSVPCAttachmentType",
    "AWSVPCAttachmentListType",
    "AWSTGWSiteType",
    "AzureRouteTableWithStaticRoute",
    "AzureRouteTableWithStaticRouteListType",
    "AzureAttachmentsStatusType",
    "AzureAttachmentsListStatusType",
    "AzureRouteTables",
    "AzureDefaultRoute",
    "AzureVNETAttachmentType",
    "AzureVnetAttachmentListType",
    "AzureVNETSiteType",
    "TrendValue",
    "MetricValue",
    "MetricData",
    "Data",
    "StatusType",
    "CreateAWSTGWSiteType",
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
    "CredentialsRequest",
    "CredentialsResponse",
    "CustomerEdge",
    "DeleteRequest",
    "ObjectRefType",
    "DiscoverVPCRequest",
    "DiscoveredVPCType",
    "DiscoverVPCResponse",
    "SegmentationData",
    "EdgeData",
    "Coordinates",
    "EdgeSite",
    "EdgeListResponse",
    "FieldData",
    "GetMetricsRequest",
    "GetMetricsResponse",
    "ObjectReplaceMetaType",
    "ReplaceAWSTGWSiteType",
    "ReplaceAzureVNETSiteType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "LabelFilter",
    "ListMetricsRequest",
    "ListMetricsResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ListSegmentMetricsRequest",
    "ListSegmentMetricsResponse",
    "ReApplyVPCAttachmentRequest",
    "ReApplyVPCAttachmentResponse",
    "ReplaceResponse",
    "TopCloudConnectData",
    "TopCloudConnectRequest",
    "TopCloudConnectResponse",
    "Spec",
]
