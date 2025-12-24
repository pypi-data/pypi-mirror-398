"""Usage resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.usage.models import (
    CalculatedUsageItem,
    Coupon,
    HourlyItem,
    ListCurrentUsageReq,
    ListCurrentUsageResp,
    ListHourlyUsageDetailsReq,
    ListHourlyUsageDetailsResp,
    ListMonthlyUsageReq,
    MonthlyUsageType,
    ListMonthlyUsageResp,
    ListUsageDetailsReq,
    Item,
    ListUsageDetailsResp,
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


class UsageResource:
    """API methods for usage.

    Resource usage and pricing custom APIs
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.usage.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list_current_usage(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListCurrentUsageResp:
        """List Current Usage for usage.

        List current usage details per tenant and namespace. Some usage have...
        """
        path = "/api/web/namespaces/{namespace}/current_usage"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListCurrentUsageResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("usage", "list_current_usage", e, response) from e

    def list_hourly_usage_details(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListHourlyUsageDetailsResp:
        """List Hourly Usage Details for usage.

        List the usage divided by hour. The usage is hourly aggregated, from...
        """
        path = "/api/web/namespaces/{namespace}/hourly_usage_details"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListHourlyUsageDetailsResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("usage", "list_hourly_usage_details", e, response) from e

    def list_monthly_usage(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListMonthlyUsageResp:
        """List Monthly Usage for usage.

        List monthly usage details per tenant and namespace. Some usage have...
        """
        path = "/api/web/namespaces/{namespace}/monthly_usage"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListMonthlyUsageResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("usage", "list_monthly_usage", e, response) from e

    def list_usage_details(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListUsageDetailsResp:
        """List Usage Details for usage.

        List usage details per tenant and namespace. Some usage have only...
        """
        path = "/api/web/namespaces/{namespace}/usage_details"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListUsageDetailsResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("usage", "list_usage_details", e, response) from e

