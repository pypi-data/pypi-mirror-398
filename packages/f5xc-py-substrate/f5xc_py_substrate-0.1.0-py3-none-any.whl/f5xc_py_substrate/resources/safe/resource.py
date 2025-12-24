"""Safe resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.safe.models import (
    GetSafeBlockAuditCsvResponse,
    GetSafeBlockAuditResponse,
    GetSafeBlockDetailsResponse,
    GetSafeBlockTableCsvResponse,
    GetSafeBlockTableResponse,
    GetSafeGeneralResponse,
    GetSafeSummaryResponse,
    GetSafeTransactionDetailsResponse,
    PostFeedbackRequest,
    PostFeedbackResponse,
    PostGeneralFeedbackRequest,
    PostGeneralFeedbackResponse,
    PostSafeBlockFeedbackRequest,
    PostSafeBlockFeedbackResponse,
    PostSafeBlockRuleRequest,
    PostSafeBlockRuleResponse,
    PostSafeEpRequest,
    PostSafeEpResponse,
    PostSafeOverviewRequest,
    PostSafeOverviewResponse,
    PostSafeProvisionRequest,
    PostSafeProvisionResponse,
    PostSafeTransactionDetailsRequest,
    PostSafeTransactionDetailsResponse,
    PostSafeTransactionDeviceHistoryRequest,
    PostSafeTransactionDeviceHistoryResponse,
    PostSafeTransactionLocationsRequest,
    PostSafeTransactionLocationsResponse,
    PostSafeTransactionRelatedSessionsRequest,
    PostSafeTransactionRelatedSessionsResponse,
    PostSafeTransactionTimelineRequest,
    PostSafeTransactionTimelineResponse,
    PostSafeTransactionsCsvRequest,
    PostSafeTransactionsCsvResponse,
    PostSafeTransactionsOverTimeRequest,
    PostSafeTransactionsOverTimeResponse,
    PostSafeTransactionsRequest,
    PostSafeTransactionsResponse,
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


class SafeResource:
    """API methods for safe.

    Use this API to interact with SAFE endpoints.
All calls which not...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.safe.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_safe_block_audit(
        self,
        namespace: str,
        dimt: str | None = None,
        dimv: str | None = None,
        version: str | None = None,
    ) -> GetSafeBlockAuditResponse:
        """Get Safe Block Audit for safe.

        Get SAFE block table list
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/block/audit"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if dimt is not None:
            params["dimt"] = dimt
        if dimv is not None:
            params["dimv"] = dimv
        if version is not None:
            params["version"] = version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeBlockAuditResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_safe_block_audit", e, response) from e

    def get_safe_block_audit_csv(
        self,
        namespace: str,
        dimt: str | None = None,
        dimv: str | None = None,
        version: str | None = None,
    ) -> GetSafeBlockAuditCsvResponse:
        """Get Safe Block Audit Csv for safe.

        Get Safe block audit as csv file
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/block/csv/audit"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if dimt is not None:
            params["dimt"] = dimt
        if dimv is not None:
            params["dimv"] = dimv
        if version is not None:
            params["version"] = version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeBlockAuditCsvResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_safe_block_audit_csv", e, response) from e

    def get_safe_block_table_csv(
        self,
        namespace: str,
        from_: str | None = None,
        to: str | None = None,
        version: str | None = None,
        action: str | None = None,
    ) -> GetSafeBlockTableCsvResponse:
        """Get Safe Block Table Csv for safe.

        Get Safe block table as csv file
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/block/csv/table"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if from_ is not None:
            params["from"] = from_
        if to is not None:
            params["to"] = to
        if version is not None:
            params["version"] = version
        if action is not None:
            params["action"] = action

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeBlockTableCsvResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_safe_block_table_csv", e, response) from e

    def get_safe_block_details(
        self,
        namespace: str,
        account_id: str | None = None,
        device_id: str | None = None,
        version: str | None = None,
    ) -> GetSafeBlockDetailsResponse:
        """Get Safe Block Details for safe.

        Get SAFE block details
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/block/details"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if account_id is not None:
            params["account_id"] = account_id
        if device_id is not None:
            params["device_id"] = device_id
        if version is not None:
            params["version"] = version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeBlockDetailsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_safe_block_details", e, response) from e

    def post_safe_block_feedback(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeBlockFeedbackResponse:
        """Post Safe Block Feedback for safe.

        Post Safe block feedback
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/block/feedback"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeBlockFeedbackResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_block_feedback", e, response) from e

    def post_safe_block_rule(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeBlockRuleResponse:
        """Post Safe Block Rule for safe.

        Edit exising block rule
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/block/rule"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeBlockRuleResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_block_rule", e, response) from e

    def get_safe_block_table(
        self,
        namespace: str,
        from_: str | None = None,
        to: str | None = None,
        version: str | None = None,
        action: str | None = None,
    ) -> GetSafeBlockTableResponse:
        """Get Safe Block Table for safe.

        Get SAFE block table list
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/block/table"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if from_ is not None:
            params["from"] = from_
        if to is not None:
            params["to"] = to
        if version is not None:
            params["version"] = version
        if action is not None:
            params["action"] = action

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeBlockTableResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_safe_block_table", e, response) from e

    def post_safe_ep(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeEpResponse:
        """Post Safe Ep for safe.

        Post Safe Analyst Station ep request
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/ep"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeEpResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_ep", e, response) from e

    def post_feedback(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostFeedbackResponse:
        """Post Feedback for safe.

        Update fraud feedback for a transaction or session
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/feedback"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostFeedbackResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_feedback", e, response) from e

    def post_general_feedback(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostGeneralFeedbackResponse:
        """Post General Feedback for safe.

        Update fraud feedback for a transaction or session
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/general_feedback"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostGeneralFeedbackResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_general_feedback", e, response) from e

    def get_health(
        self,
        namespace: str,
        version: str | None = None,
    ) -> Empty:
        """Get Health for safe.

        returns 200 Ok if the service is health
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/health"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if version is not None:
            params["version"] = version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_health", e, response) from e

    def post_safe_provision(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeProvisionResponse:
        """Post Safe Provision for safe.

        Post Safe Analyst Station provision
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/provision"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeProvisionResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_provision", e, response) from e

    def get_safe_overview(
        self,
        namespace: str,
        from_: str | None = None,
        to: str | None = None,
        version: str | None = None,
    ) -> GetSafeGeneralResponse:
        """Get Safe Overview for safe.

        Get SAFE Analyst Station Dashboard Transaction Breakdown request
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/stats/overview"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if from_ is not None:
            params["from"] = from_
        if to is not None:
            params["to"] = to
        if version is not None:
            params["version"] = version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeGeneralResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_safe_overview", e, response) from e

    def post_safe_overview(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeOverviewResponse:
        """Post Safe Overview for safe.

        Post Safe Analyst Station Dashboard Transaction Breakdown request
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/stats/overview"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeOverviewResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_overview", e, response) from e

    def get_safe_top_locations(
        self,
        namespace: str,
        from_: str | None = None,
        to: str | None = None,
        limit: str | None = None,
        version: str | None = None,
    ) -> GetSafeGeneralResponse:
        """Get Safe Top Locations for safe.

        Get SAFE Analyst Station Dashboard Transaction Breakdown request
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/stats/top_locations"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if from_ is not None:
            params["from"] = from_
        if to is not None:
            params["to"] = to
        if limit is not None:
            params["limit"] = limit
        if version is not None:
            params["version"] = version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeGeneralResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_safe_top_locations", e, response) from e

    def post_safe_top_locations(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetSafeGeneralResponse:
        """Post Safe Top Locations for safe.

        Post SAFE Analyst Station Dashboard Transaction Breakdown request
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/stats/top_locations"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeGeneralResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_top_locations", e, response) from e

    def get_safe_top_sources(
        self,
        namespace: str,
        from_: str | None = None,
        to: str | None = None,
        limit: str | None = None,
        version: str | None = None,
    ) -> GetSafeGeneralResponse:
        """Get Safe Top Sources for safe.

        Get SAFE Analyst Station Dashboard Transaction Breakdown request
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/stats/top_sources"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if from_ is not None:
            params["from"] = from_
        if to is not None:
            params["to"] = to
        if limit is not None:
            params["limit"] = limit
        if version is not None:
            params["version"] = version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeGeneralResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_safe_top_sources", e, response) from e

    def post_safe_top_sources(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetSafeGeneralResponse:
        """Post Safe Top Sources for safe.

        Post SAFE Analyst Station Dashboard Transaction Breakdown request
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/stats/top_sources"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeGeneralResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_top_sources", e, response) from e

    def post_safe_transactions_over_time(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeTransactionsOverTimeResponse:
        """Post Safe Transactions Over Time for safe.

        Post Safe Analyst Station Dashboard Transaction Breakdown request
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/stats/transactions_over_time"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeTransactionsOverTimeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_transactions_over_time", e, response) from e

    def get_safe_summary(
        self,
        namespace: str,
        from_: str | None = None,
        to: str | None = None,
        version: str | None = None,
    ) -> GetSafeSummaryResponse:
        """Get Safe Summary for safe.

        Get SAFE transaction summary for analysts
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/summary"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if from_ is not None:
            params["from"] = from_
        if to is not None:
            params["to"] = to
        if version is not None:
            params["version"] = version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_safe_summary", e, response) from e

    def get_safe_transaction_details(
        self,
        namespace: str,
        transaction_id: str | None = None,
        version: str | None = None,
    ) -> GetSafeTransactionDetailsResponse:
        """Get Safe Transaction Details for safe.

        Get a detailed information about the requested transaction
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/transaction_details"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if transaction_id is not None:
            params["transaction_id"] = transaction_id
        if version is not None:
            params["version"] = version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeTransactionDetailsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "get_safe_transaction_details", e, response) from e

    def post_safe_transaction_details(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeTransactionDetailsResponse:
        """Post Safe Transaction Details for safe.

        Post Safe Analyst Station specific transaction details
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/transaction_details"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeTransactionDetailsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_transaction_details", e, response) from e

    def post_safe_transaction_device_history(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeTransactionDeviceHistoryResponse:
        """Post Safe Transaction Device History for safe.

        Post Safe Analyst Station specific transaction device history
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/transaction_device_history"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeTransactionDeviceHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_transaction_device_history", e, response) from e

    def post_safe_transaction_locations(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeTransactionLocationsResponse:
        """Post Safe Transaction Locations for safe.

        Post Safe Analyst Station specific transaction locations
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/transaction_locations"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeTransactionLocationsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_transaction_locations", e, response) from e

    def post_safe_transaction_related_sessions(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeTransactionRelatedSessionsResponse:
        """Post Safe Transaction Related Sessions for safe.

        Post Safe Analyst Station specific transaction related sessions
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/transaction_related_sessions"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeTransactionRelatedSessionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_transaction_related_sessions", e, response) from e

    def post_safe_transaction_timeline(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeTransactionTimelineResponse:
        """Post Safe Transaction Timeline for safe.

        Post Safe Analyst Station specific transaction timeline
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/transaction_timeline"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeTransactionTimelineResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_transaction_timeline", e, response) from e

    def post_safe_transactions(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeTransactionsResponse:
        """Post Safe Transactions for safe.

        List SAFE transactions for analysts
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/transactions"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_transactions", e, response) from e

    def post_safe_transactions_csv(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> PostSafeTransactionsCsvResponse:
        """Post Safe Transactions Csv for safe.

        Get Safe transactions as csv file
        """
        path = "/api/shape/safe/namespaces/{namespace}/safe/sas/transactions_csv"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PostSafeTransactionsCsvResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safe", "post_safe_transactions_csv", e, response) from e

