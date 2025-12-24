"""Connectivity resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.connectivity.models import (
    Id,
    TrendValue,
    MetricValue,
    HealthscoreTypeData,
    HealthscoreData,
    MetricFeatureData,
    EdgeMetricData,
    EdgeData,
    HealthscoreSelector,
    EdgeMetricSelector,
    EdgeFieldSelector,
    EdgeRequest,
    EdgeResponse,
    NodeMetricSelector,
    NodeFieldSelector,
    FieldSelector,
    LabelFilter,
    NodeInstanceMetricData,
    NodeInstanceData,
    NodeInterfaceMetricData,
    NodeInterfaceData,
    NodeMetricData,
    NodeData,
    NodeRequest,
    NodeResponse,
    Request,
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


class ConnectivityResource:
    """API methods for connectivity.

    Connectivity graph APIs are used to get the connectivity data...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.connectivity.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Query for connectivity.

        Request to get Connectivity data between the sites.
        """
        path = "/api/data/namespaces/{namespace}/graph/connectivity"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("connectivity", "query", e, response) from e

    def edge_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> EdgeResponse:
        """Edge Query for connectivity.

        Request to get Connectivity data for an edge. This query is used to...
        """
        path = "/api/data/namespaces/{namespace}/graph/connectivity/edge"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EdgeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("connectivity", "edge_query", e, response) from e

    def node_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> NodeResponse:
        """Node Query for connectivity.

        Request to get Connectivity data for a site. This query is used to...
        """
        path = "/api/data/namespaces/{namespace}/graph/connectivity/node"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return NodeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("connectivity", "node_query", e, response) from e

