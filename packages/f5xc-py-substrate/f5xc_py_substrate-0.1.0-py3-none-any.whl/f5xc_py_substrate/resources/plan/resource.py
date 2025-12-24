"""Plan resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.plan.models import (
    AddonServiceDetails,
    GlobalSpecType,
    UsagePlanTransitionFlow,
    Internal,
    LocalizedPlan,
    ListUsagePlansRsp,
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


class PlanResource:
    """API methods for plan.

    Usage plan related RPCs. Used for billing and onboarding.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.plan.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_current_plan(
        self,
    ) -> LocalizedPlan:
        """Get Current Plan for plan.

        Endpoint to get current usage plan
        """
        path = "/api/web/namespaces/system/usage_plans/current"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LocalizedPlan(**response)
        except ValidationError as e:
            raise F5XCValidationError("plan", "get_current_plan", e, response) from e

    def list_usage_plans(
        self,
    ) -> ListUsagePlansRsp:
        """List Usage Plans for plan.

        Endpoint to get usage plans
        """
        path = "/api/web/namespaces/system/usage_plans/custom_list"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListUsagePlansRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("plan", "list_usage_plans", e, response) from e

