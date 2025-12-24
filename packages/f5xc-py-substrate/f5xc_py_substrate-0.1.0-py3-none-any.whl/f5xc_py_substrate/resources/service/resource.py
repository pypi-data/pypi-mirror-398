"""Service resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.service.models import (
    APIEPDynExample,
    AuthenticationTypeLocPair,
    PDFSpec,
    PDFStat,
    APIEPPDFInfo,
    RiskScore,
    APIEPInfo,
    TrendValue,
    MetricValue,
    MetricFeatureData,
    MetricData,
    EdgeMetricData,
    EdgeMetricSelector,
    HealthscoreTypeData,
    HealthscoreData,
    HealthscoreSelector,
    NodeMetricData,
    NodeMetricSelector,
    InstanceId,
    InstanceRequestId,
    AppTypeInfo,
    AppTypeListResponse,
    Id,
    CdnMetricData,
    CacheableData,
    EdgeAPIEPData,
    EdgeAPIEPSelector,
    EdgeFieldData,
    EdgeData,
    EdgeFieldSelector,
    RequestId,
    EdgeRequest,
    EdgeResponse,
    NodeFieldData,
    NodeData,
    GraphData,
    InstanceData,
    NodeFieldSelector,
    InstanceRequest,
    InstanceResponse,
    InstancesData,
    LabelFilter,
    InstancesRequest,
    InstancesResponse,
    LBCacheContentRequest,
    LBCacheContentResponse,
    NodeRequest,
    NodeResponse,
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


class ServiceResource:
    """API methods for service.

    graph/service api is query used to get monitoring information for...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.service.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def query_all_namespaces(
        self,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Query All Namespaces for service.

        Request to get monitoring data for a service mesh of a given application.
        """
        path = "/api/data/namespaces/system/graph/all_ns_service"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("service", "query_all_namespaces", e, response) from e

    def lb_cache_content(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> LBCacheContentResponse:
        """Lb Cache Content for service.

        Request to get time-series cacheable data for HTTP-LBs.
        """
        path = "/api/data/namespaces/{namespace}/graph/lb_cache_content"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LBCacheContentResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("service", "lb_cache_content", e, response) from e

    def query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Query for service.

        Request to get monitoring data for a service mesh of a given application.
        """
        path = "/api/data/namespaces/{namespace}/graph/service"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("service", "query", e, response) from e

    def app_type_list(
        self,
        namespace: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> AppTypeListResponse:
        """App Type List for service.

        Request to get list of application types for a given namespace. For...
        """
        path = "/api/data/namespaces/{namespace}/graph/service/app_types"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AppTypeListResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("service", "app_type_list", e, response) from e

    def edge_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> EdgeResponse:
        """Edge Query for service.

        Request to get time-series data for an edge in the service mesh graph.
        """
        path = "/api/data/namespaces/{namespace}/graph/service/edge"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EdgeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("service", "edge_query", e, response) from e

    def node_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> NodeResponse:
        """Node Query for service.

        Request to get time-series data for a node in the service mesh graph.
        """
        path = "/api/data/namespaces/{namespace}/graph/service/node"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return NodeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("service", "node_query", e, response) from e

    def instance_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> InstanceResponse:
        """Instance Query for service.

        Request to get time-series data for a service instance.
        """
        path = "/api/data/namespaces/{namespace}/graph/service/node/instance"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return InstanceResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("service", "instance_query", e, response) from e

    def instances_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> InstancesResponse:
        """Instances Query for service.

        Request to get monitoring data for all instances of a service in the...
        """
        path = "/api/data/namespaces/{namespace}/graph/service/node/instances"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return InstancesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("service", "instances_query", e, response) from e

