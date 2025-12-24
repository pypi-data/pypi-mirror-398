"""L3l4 resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.l3l4.models import (
    L3l4ByApplicationRequest,
    L3l4L3L4GraphValue,
    L3l4L3L4Metric,
    L3l4ByApplicationResponse,
    L3l4ByMitigationRequest,
    L3l4ByMitigationResponse,
    L3l4ByNetworkRequest,
    L3l4ByNetworkResponse,
    L3l4ByZoneRequest,
    L3l4ByZoneResponse,
    L3l4EventCountRequest,
    L3l4EventDataPoint,
    L3l4EventCountResponse,
    L3l4TopTalker,
    L3l4TopTalkersRequest,
    L3l4TopTalkersResponse,
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


class L3l4Resource:
    """API methods for l3l4.

    l3l4 graph APIs are used to get data for a tenant.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.l3l4.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def by_application(
        self,
        namespace: str,
        network_id: str,
        body: dict[str, Any] | None = None,
    ) -> L3l4ByApplicationResponse:
        """By Application for l3l4.

        Request to get l3l4 Application traffic data.
        """
        path = "/api/infraprotect/namespaces/{namespace}/graph/l3l4/by_application/{network_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{network_id}", network_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return L3l4ByApplicationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("l3l4", "by_application", e, response) from e

    def by_mitigation(
        self,
        namespace: str,
        mitigation_id: str,
        body: dict[str, Any] | None = None,
    ) -> L3l4ByMitigationResponse:
        """By Mitigation for l3l4.

        Request to get l3l4 Mitigation Traffic data.
        """
        path = "/api/infraprotect/namespaces/{namespace}/graph/l3l4/by_mitigation/{mitigation_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{mitigation_id}", mitigation_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return L3l4ByMitigationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("l3l4", "by_mitigation", e, response) from e

    def by_network(
        self,
        namespace: str,
        network_id: str,
        body: dict[str, Any] | None = None,
    ) -> L3l4ByNetworkResponse:
        """By Network for l3l4.

        Request to get l3l4 Network Traffic data.
        """
        path = "/api/infraprotect/namespaces/{namespace}/graph/l3l4/by_network/{network_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{network_id}", network_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return L3l4ByNetworkResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("l3l4", "by_network", e, response) from e

    def by_zone(
        self,
        namespace: str,
        network_id: str,
        body: dict[str, Any] | None = None,
    ) -> L3l4ByZoneResponse:
        """By Zone for l3l4.

        Request to get l3l4 zone destination Traffic data.
        """
        path = "/api/infraprotect/namespaces/{namespace}/graph/l3l4/by_zone/{network_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{network_id}", network_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return L3l4ByZoneResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("l3l4", "by_zone", e, response) from e

    def event_count(
        self,
        namespace: str,
        network_id: str,
        body: dict[str, Any] | None = None,
    ) -> L3l4EventCountResponse:
        """Event Count for l3l4.

        Request to get l3l4 Event counts over a period of time.
        """
        path = "/api/infraprotect/namespaces/{namespace}/graph/l3l4/event_count/{network_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{network_id}", network_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return L3l4EventCountResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("l3l4", "event_count", e, response) from e

    def top_talkers(
        self,
        namespace: str,
        network_id: str,
        body: dict[str, Any] | None = None,
    ) -> L3l4TopTalkersResponse:
        """Top Talkers for l3l4.

        Request to get l3l4 Top talkers Traffic data.
        """
        path = "/api/infraprotect/namespaces/{namespace}/graph/l3l4/top_talkers/{network_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{network_id}", network_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return L3l4TopTalkersResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("l3l4", "top_talkers", e, response) from e

