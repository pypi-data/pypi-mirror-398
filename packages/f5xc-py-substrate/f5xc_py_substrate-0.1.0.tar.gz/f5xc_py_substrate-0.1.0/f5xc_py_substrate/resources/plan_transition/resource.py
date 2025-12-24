"""PlanTransition resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.plan_transition.models import (
    GetPlanTransitionRsp,
    GlobalSpecType,
    TransitionPayload,
    InitiatePlanTransitionReq,
    InitiatePlanTransitionRsp,
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


class PlanTransitionResource:
    """API methods for plan_transition.

    Package plan transition is responsible for storing and managing...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.plan_transition.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_plan_transition(
        self,
        id_: str | None = None,
    ) -> GetPlanTransitionRsp:
        """Get Plan Transition for plan_transition.

        API to get plan transition details by a plan transition request uid...
        """
        path = "/no_auth/namespaces/system/billing/plan_transition"

        params: dict[str, Any] = {}
        if id_ is not None:
            params["id"] = id_

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetPlanTransitionRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("plan_transition", "get_plan_transition", e, response) from e

    def initiate_plan_transition(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> InitiatePlanTransitionRsp:
        """Initiate Plan Transition for plan_transition.

        API to create a plan transition request in db.
        """
        path = "/api/web/namespaces/{namespace}/billing/plan_transition"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return InitiatePlanTransitionRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("plan_transition", "initiate_plan_transition", e, response) from e

