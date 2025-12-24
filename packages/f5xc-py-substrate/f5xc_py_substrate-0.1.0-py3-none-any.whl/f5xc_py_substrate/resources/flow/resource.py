"""Flow resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.flow.models import (
    AnomalyData,
    TrendValue,
    MetricValue,
    FieldData,
    AnomalyData,
    Data,
    SortBy,
    SubscribeRequest,
    SubscribeResponse,
    SubscriptionStatusResponse,
    TopFlowAnomaliesRequest,
    TopFlowAnomaliesResponse,
    TopTalkersResponse,
    UnsubscribeRequest,
    UnsubscribeResponse,
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


class FlowResource:
    """API methods for flow.

    APIs to get Flow records and data
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.flow.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def subscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> SubscribeResponse:
        """Subscribe for flow.

        Subscribe to Flow Collection
        """
        path = "/api/config/namespaces/system/flow-collection/addon/subscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("flow", "subscribe", e, response) from e

    def get_subscription_status(
        self,
    ) -> SubscriptionStatusResponse:
        """Get Subscription Status for flow.

        Check subscription status flow Flow Collection
        """
        path = "/api/config/namespaces/system/flow-collection/addon/subscription-status"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SubscriptionStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("flow", "get_subscription_status", e, response) from e

    def unsubscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> UnsubscribeResponse:
        """Unsubscribe for flow.

        Unsubscribe to Flow Collection
        """
        path = "/api/config/namespaces/system/flow-collection/addon/unsubscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UnsubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("flow", "unsubscribe", e, response) from e

    def flow_collection(
        self,
        body: dict[str, Any] | None = None,
    ) -> TopTalkersResponse:
        """Flow Collection for flow.

        Request to get flow collection from the flow records
        """
        path = "/api/data/namespaces/system/flows/flow_collection"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopTalkersResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("flow", "flow_collection", e, response) from e

    def top_flow_anomalies(
        self,
        body: dict[str, Any] | None = None,
    ) -> TopFlowAnomaliesResponse:
        """Top Flow Anomalies for flow.

        Request to get flow anomaly records
        """
        path = "/api/data/namespaces/system/flows/top_flow_anomalies"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopFlowAnomaliesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("flow", "top_flow_anomalies", e, response) from e

    def top_talkers(
        self,
        body: dict[str, Any] | None = None,
    ) -> TopTalkersResponse:
        """Top Talkers for flow.

        Request to get top talkers from the flow records
        """
        path = "/api/data/namespaces/system/flows/top_talkers"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopTalkersResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("flow", "top_talkers", e, response) from e

