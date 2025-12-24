"""Topology resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.topology.models import (
    Empty,
    DCClusterGroupMeshType,
    ObjectRefType,
    Ipv4SubnetType,
    Ipv6SubnetType,
    IpSubnetType,
    TrendValue,
    MetricValue,
    Node,
    MetricTypeData,
    DCClusterGroupType,
    DCClusterGroupSummaryInfo,
    NodeTypeDCClusterGroup,
    BondMembersType,
    InterfaceStatus,
    AddressInfoType,
    NetworkInterfaceType,
    InstanceType,
    MetricData,
    NodeTypeInstance,
    NodeMetaData,
    LoadBalancer,
    NetworkType,
    RouteTableMetaData,
    NetworkSummaryInfo,
    NodeTypeNetwork,
    SiteType,
    SiteSummaryInfo,
    NodeTypeSite,
    FullMeshGroupType,
    HubFullMeshGroupType,
    ObjectRefType,
    SpokeMeshGroupType,
    SiteMeshGroupType,
    EdgeInfoSummary,
    LinkInfoSummary,
    SiteMeshGroupSummaryInfo,
    NodeTypeSiteMeshGroup,
    SubnetType,
    SubnetSummaryInfo,
    NodeTypeSubnet,
    AWSTGWAttachment,
    TransitGatewayType,
    NodeTypeTransitGateway,
    Node,
    MetaType,
    AWSNetworkMetaData,
    AWSTGWAttachmentMetaData,
    AWSTgwRouteAttributes,
    AWSRouteAttributes,
    MetricSelector,
    DCClusterTopologyRequest,
    LinkInfo,
    LinkTypeData,
    Edge,
    GCPRouteAttributes,
    RouteType,
    RouteTableType,
    RouteTableData,
    SubnetMetaData,
    SubnetData,
    NetworkRouteTableData,
    NetworkRouteTableMetaData,
    NetworkRoutesData,
    NetworkRouteTablesResponse,
    NetworkRoutesMetaData,
    RouteTableResponse,
    SiteMeshTopologyRequest,
    SiteNetworksResponse,
    SiteTopologyRequest,
    TGWRouteTablesResponse,
    Response,
)


# Exclusion group mappings for get() method
_EXCLUDE_GROUPS: dict[str, set[str]] = {
    "forms": {"create_form", "replace_form"},
    "references": {"referring_objects", "deleted_referred_objects", "disabled_referred_objects"},
    "system_metadata": {"system_metadata"},
}


def _resolve_exclude_groups(groups: list[str]) -> set[str]:
    """Resolve exclusion group names to field names."""
    fields: set[str] = set()
    for group in groups:
        if group in _EXCLUDE_GROUPS:
            fields.update(_EXCLUDE_GROUPS[group])
        else:
            # Allow direct field names for flexibility
            fields.add(group)
    return fields


class TopologyResource:
    """API methods for topology.

    APIs to get topology of all the resources associated/connected to a...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.topology.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def dc_cluster_topology(
        self,
        dc_cluster_group: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Dc Cluster Topology for topology.

        Get topology of a DC Cluster.
        """
        path = "/api/data/namespaces/system/topology/dc_cluster_group/{dc_cluster_group}"
        path = path.replace("{dc_cluster_group}", dc_cluster_group)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("topology", "dc_cluster_topology", e, response) from e

    def dc_cluster_groups_summary(
        self,
    ) -> Response:
        """Dc Cluster Groups Summary for topology.

        Get summary of all DC Cluster groups.
        """
        path = "/api/data/namespaces/system/topology/dc_cluster_groups"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("topology", "dc_cluster_groups_summary", e, response) from e

    def get_network_route_tables(
        self,
        id: str,
        route_table_ids: list | None = None,
        subnet_ids: list | None = None,
        subnet_cidrs: list | None = None,
        regions: list | None = None,
        site: str | None = None,
    ) -> NetworkRouteTablesResponse:
        """Get Network Route Tables for topology.

        Gets Route Tables Associated with a Network
        """
        path = "/api/data/namespaces/system/topology/network/{id}/route_tables"
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if route_table_ids is not None:
            params["route_table_ids"] = route_table_ids
        if subnet_ids is not None:
            params["subnet_ids"] = subnet_ids
        if subnet_cidrs is not None:
            params["subnet_cidrs"] = subnet_cidrs
        if regions is not None:
            params["regions"] = regions
        if site is not None:
            params["site"] = site

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return NetworkRouteTablesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("topology", "get_network_route_tables", e, response) from e

    def get_route_table(
        self,
        name: str,
    ) -> RouteTableResponse:
        """Get Route Table for topology.

        Get Route Table
        """
        path = "/api/data/namespaces/system/topology/route_table/{name}"
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return RouteTableResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("topology", "get_route_table", e, response) from e

    def get_site_networks(
        self,
        name: str,
    ) -> SiteNetworksResponse:
        """Get Site Networks for topology.

        Gets Networks Associated to Site
        """
        path = "/api/data/namespaces/system/topology/site/{name}/networks"
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SiteNetworksResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("topology", "get_site_networks", e, response) from e

    def site_topology(
        self,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Site Topology for topology.

        Get topology of a site and the resources associated/connected to the...
        """
        path = "/api/data/namespaces/system/topology/site/{site}"
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("topology", "site_topology", e, response) from e

    def site_mesh_topology(
        self,
        site_mesh_group: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Site Mesh Topology for topology.

        Get topology of a site mesh.
        """
        path = "/api/data/namespaces/system/topology/site_mesh_group/{site_mesh_group}"
        path = path.replace("{site_mesh_group}", site_mesh_group)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("topology", "site_mesh_topology", e, response) from e

    def site_mesh_groups_summary(
        self,
    ) -> Response:
        """Site Mesh Groups Summary for topology.

        Get summary of all site mesh groups.
        """
        path = "/api/data/namespaces/system/topology/site_mesh_groups"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("topology", "site_mesh_groups_summary", e, response) from e

    def get_tgw_route_tables(
        self,
        id: str,
        route_table_ids: list | None = None,
        attachment_ids: list | None = None,
    ) -> TGWRouteTablesResponse:
        """Get Tgw Route Tables for topology.

        Gets Route Tables Associated with a TGW
        """
        path = "/api/data/namespaces/system/topology/tgw/{id}/route_tables"
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if route_table_ids is not None:
            params["route_table_ids"] = route_table_ids
        if attachment_ids is not None:
            params["attachment_ids"] = attachment_ids

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TGWRouteTablesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("topology", "get_tgw_route_tables", e, response) from e

