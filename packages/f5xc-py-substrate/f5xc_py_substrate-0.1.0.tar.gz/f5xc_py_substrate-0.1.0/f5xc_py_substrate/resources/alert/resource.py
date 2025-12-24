"""Alert resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.alert.models import (
    AlertAlertsHistoryAggregationRequest,
    AlertAlertsHistoryAggregationResponse,
    AlertAlertsHistoryResponse,
    AlertAlertsHistoryScrollRequest,
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


class AlertResource:
    """API methods for alert.

    Alert may be generated based on the metrics or based on severity...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.alert.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def alerts_all_namespaces(
        self,
        namespace: str | None = None,
        inactive: bool | None = None,
        silenced: bool | None = None,
        inhibited: bool | None = None,
        unprocessed: bool | None = None,
        filter: str | None = None,
    ) -> Response:
        """Alerts All Namespaces for alert.

        For system namespace, all the alerts for the tenant matching the...
        """
        path = "/api/data/namespaces/system/all_ns_alerts"

        params: dict[str, Any] = {}
        if namespace is not None:
            params["namespace"] = namespace
        if inactive is not None:
            params["inactive"] = inactive
        if silenced is not None:
            params["silenced"] = silenced
        if inhibited is not None:
            params["inhibited"] = inhibited
        if unprocessed is not None:
            params["unprocessed"] = unprocessed
        if filter is not None:
            params["filter"] = filter

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("alert", "alerts_all_namespaces", e, response) from e

    def alerts(
        self,
        namespace: str,
        inactive: bool | None = None,
        silenced: bool | None = None,
        inhibited: bool | None = None,
        unprocessed: bool | None = None,
        filter: str | None = None,
    ) -> Response:
        """Alerts for alert.

        Get alerts matching the filter for the given namespace.
        """
        path = "/api/data/namespaces/{namespace}/alerts"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if inactive is not None:
            params["inactive"] = inactive
        if silenced is not None:
            params["silenced"] = silenced
        if inhibited is not None:
            params["inhibited"] = inhibited
        if unprocessed is not None:
            params["unprocessed"] = unprocessed
        if filter is not None:
            params["filter"] = filter

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("alert", "alerts", e, response) from e

    def alerts_history(
        self,
        namespace: str,
        filter: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> AlertAlertsHistoryResponse:
        """Alerts History for alert.

        Get the history of alert notifications sent to the end-user between...
        """
        path = "/api/data/namespaces/{namespace}/alerts/history"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if filter is not None:
            params["filter"] = filter
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AlertAlertsHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("alert", "alerts_history", e, response) from e

    def alerts_history_aggregation(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AlertAlertsHistoryAggregationResponse:
        """Alerts History Aggregation for alert.

        Get summary/aggregation data for alerts in the given namespace. For...
        """
        path = "/api/data/namespaces/{namespace}/alerts/history/aggregation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AlertAlertsHistoryAggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("alert", "alerts_history_aggregation", e, response) from e

    def alerts_history_scroll(
        self,
        namespace: str,
        scroll_id: str | None = None,
    ) -> AlertAlertsHistoryResponse:
        """Alerts History Scroll for alert.

        Scroll request is used to fetch large number of alert messages in...
        """
        path = "/api/data/namespaces/{namespace}/alerts/history/scroll"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if scroll_id is not None:
            params["scroll_id"] = scroll_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AlertAlertsHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("alert", "alerts_history_scroll", e, response) from e

    def custom_alerts_history_scroll(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AlertAlertsHistoryResponse:
        """Custom Alerts History Scroll for alert.

        Scroll request is used to fetch large number of alert messages in...
        """
        path = "/api/data/namespaces/{namespace}/alerts/history/scroll"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AlertAlertsHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("alert", "custom_alerts_history_scroll", e, response) from e

