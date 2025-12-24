"""AiAssistant resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.ai_assistant.models import (
    BotDefenseEventDetails,
    RequestDetails,
    SvcPolicyEventDetails,
    Bot,
    Signature,
    ThreatCampaign,
    Violation,
    WAFEventDetails,
    ExplainLogRecordResponse,
    LogFilter,
    DashboardLink,
    GenericLink,
    Link,
    GenDashboardFilterResponse,
    ProtobufAny,
    ErrorType,
    GenericResponse,
    Item,
    ListList,
    ListResponse,
    OverlayData,
    OverlayContent,
    Display,
    FieldProperties,
    CellProperties,
    Cell,
    Row,
    Table,
    WidgetView,
    SiteAnalysisResponse,
    WidgetResponse,
    AIAssistantQueryResponse,
    Empty,
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


class AiAssistantResource:
    """API methods for ai_assistant.

    Custom handler for ai assistant related microservice
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.ai_assistant.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def eval_ai_assistant_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Eval Ai Assistant Query for ai_assistant.

        Temporarily to be used in place of AIAssistantQuery for evaluating...
        """
        path = "/api/gen-ai/namespaces/{namespace}/eval_query"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("ai_assistant", "eval_ai_assistant_query", e, response) from e

    def eval_ai_assistant_feedback(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Eval Ai Assistant Feedback for ai_assistant.

        Temporarily to be used in place of AIAssistantFeedback for...
        """
        path = "/api/gen-ai/namespaces/{namespace}/eval_query_feedback"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("ai_assistant", "eval_ai_assistant_feedback", e, response) from e

    def ai_assistant_query(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AIAssistantQueryResponse:
        """Ai Assistant Query for ai_assistant.

        Enable service by returning service account details
        """
        path = "/api/gen-ai/namespaces/{namespace}/query"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AIAssistantQueryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("ai_assistant", "ai_assistant_query", e, response) from e

    def ai_assistant_feedback(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Ai Assistant Feedback for ai_assistant.

        Enable service by returning service account details
        """
        path = "/api/gen-ai/namespaces/{namespace}/query_feedback"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("ai_assistant", "ai_assistant_feedback", e, response) from e

