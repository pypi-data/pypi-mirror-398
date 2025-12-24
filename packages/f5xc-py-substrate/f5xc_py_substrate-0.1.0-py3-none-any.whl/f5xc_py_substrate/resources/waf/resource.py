"""Waf resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.waf.models import (
    TrendValue,
    MetricValue,
    RuleHitsId,
    RuleHitsCounter,
    RuleHitsCountResponse,
    SecurityEventsId,
    SecurityEventsCounter,
    SecurityEventsCountResponse,
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


class WafResource:
    """API methods for waf.

    APIs to get monitoring information about WAF instances on...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.waf.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def client_rule_hits_metrics(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> RuleHitsCountResponse:
        """Client Rule Hits Metrics for waf.

        Get number of rule hits per client for a given namespace. The rule...
        """
        path = "/api/data/namespaces/{namespace}/wafs/metrics/client/rule_hits"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return RuleHitsCountResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("waf", "client_rule_hits_metrics", e, response) from e

    def client_security_events_metrics(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SecurityEventsCountResponse:
        """Client Security Events Metrics for waf.

        Get number of security events per client for a given namespace. The...
        """
        path = "/api/data/namespaces/{namespace}/wafs/metrics/client/security_events"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityEventsCountResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("waf", "client_security_events_metrics", e, response) from e

    def server_rule_hits_metrics(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> RuleHitsCountResponse:
        """Server Rule Hits Metrics for waf.

        Get number of rule hits per server for a given namespace. The rule...
        """
        path = "/api/data/namespaces/{namespace}/wafs/metrics/server/rule_hits"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return RuleHitsCountResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("waf", "server_rule_hits_metrics", e, response) from e

    def server_security_events_metrics(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SecurityEventsCountResponse:
        """Server Security Events Metrics for waf.

        Get number of security events per server for a given namespace. The...
        """
        path = "/api/data/namespaces/{namespace}/wafs/metrics/server/security_events"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SecurityEventsCountResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("waf", "server_security_events_metrics", e, response) from e

