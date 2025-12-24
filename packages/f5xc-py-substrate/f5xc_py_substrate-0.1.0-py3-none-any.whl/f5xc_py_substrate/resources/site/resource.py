"""Site resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.site.models import (
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
    EdgeFieldData,
    Id,
    EdgeData,
    EdgeFieldSelector,
    EdgeRequest,
    EdgeResponse,
    NodeFieldSelector,
    FieldSelector,
    NodeFieldData,
    NodeData,
    GraphData,
    LabelFilter,
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


class SiteResource:
    """API methods for site.

    graph/site api is query used to get monitoring information for inter...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.site.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Query for site.

        Request to get inter-site traffic graph for an application.
        """
        path = "/api/data/namespaces/{namespace}/graph/site"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("site", "query", e, response) from e

    def edge_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> EdgeResponse:
        """Edge Query for site.

        Request to get time-series data for an edge returned in the site...
        """
        path = "/api/data/namespaces/{namespace}/graph/site/edge"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EdgeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("site", "edge_query", e, response) from e

    def node_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> NodeResponse:
        """Node Query for site.

        Request to get time-series data for a site returned in the site...
        """
        path = "/api/data/namespaces/{namespace}/graph/site/node"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return NodeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("site", "node_query", e, response) from e

