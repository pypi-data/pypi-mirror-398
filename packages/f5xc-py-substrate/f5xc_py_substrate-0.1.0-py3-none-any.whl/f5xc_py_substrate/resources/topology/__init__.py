"""Topology resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.topology.models import *
    from f5xc_py_substrate.resources.topology.resource import TopologyResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "TopologyResource":
        from f5xc_py_substrate.resources.topology.resource import TopologyResource
        return TopologyResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.topology.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.topology' has no attribute '{name}'")


__all__ = [
    "TopologyResource",
    "Empty",
    "DCClusterGroupMeshType",
    "ObjectRefType",
    "Ipv4SubnetType",
    "Ipv6SubnetType",
    "IpSubnetType",
    "TrendValue",
    "MetricValue",
    "Node",
    "MetricTypeData",
    "DCClusterGroupType",
    "DCClusterGroupSummaryInfo",
    "NodeTypeDCClusterGroup",
    "BondMembersType",
    "InterfaceStatus",
    "AddressInfoType",
    "NetworkInterfaceType",
    "InstanceType",
    "MetricData",
    "NodeTypeInstance",
    "NodeMetaData",
    "LoadBalancer",
    "NetworkType",
    "RouteTableMetaData",
    "NetworkSummaryInfo",
    "NodeTypeNetwork",
    "SiteType",
    "SiteSummaryInfo",
    "NodeTypeSite",
    "FullMeshGroupType",
    "HubFullMeshGroupType",
    "ObjectRefType",
    "SpokeMeshGroupType",
    "SiteMeshGroupType",
    "EdgeInfoSummary",
    "LinkInfoSummary",
    "SiteMeshGroupSummaryInfo",
    "NodeTypeSiteMeshGroup",
    "SubnetType",
    "SubnetSummaryInfo",
    "NodeTypeSubnet",
    "AWSTGWAttachment",
    "TransitGatewayType",
    "NodeTypeTransitGateway",
    "Node",
    "MetaType",
    "AWSNetworkMetaData",
    "AWSTGWAttachmentMetaData",
    "AWSTgwRouteAttributes",
    "AWSRouteAttributes",
    "MetricSelector",
    "DCClusterTopologyRequest",
    "LinkInfo",
    "LinkTypeData",
    "Edge",
    "GCPRouteAttributes",
    "RouteType",
    "RouteTableType",
    "RouteTableData",
    "SubnetMetaData",
    "SubnetData",
    "NetworkRouteTableData",
    "NetworkRouteTableMetaData",
    "NetworkRoutesData",
    "NetworkRouteTablesResponse",
    "NetworkRoutesMetaData",
    "RouteTableResponse",
    "SiteMeshTopologyRequest",
    "SiteNetworksResponse",
    "SiteTopologyRequest",
    "TGWRouteTablesResponse",
    "Response",
    "Spec",
]
