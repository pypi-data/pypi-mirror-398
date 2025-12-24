"""Reporting resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.reporting.models import (
    ReportFreqDaily,
    ReportFreqMonthly,
    ReportFreqWeekly,
    ATBRequest,
    ATBResponse,
    ActionData,
    ActionTakenData,
    TimeSeriesDataV2,
    AttackIntentData,
    AttackIntentTimeSeriesResponse,
    AttackedBFPData,
    AttackedEndpointData,
    DistributionData,
    AttackedEndpointDataV2,
    AttackedEndpointDataV4,
    AutomatedTrafficActionsResponse,
    AutomationTypeData,
    CategoriesData,
    CategoryTimeSeriesData,
    CategoriesTimeSeriesResponse,
    ConsumptionData,
    ConsumptionSummaryResponse,
    TimeSeriesGraphData,
    CredentialStuffingAttackResponse,
    EndpointCategoryData,
    EndpointCategoryResponse,
    EndpointLabelsData,
    EndpointListData,
    EndpointListResponse,
    EndpointSummaryResponse,
    EndpointSummaryResponseV2,
    ForensicAggregateType,
    ForensicErrorType,
    ForensicSuggestType,
    ForensicData,
    ForensicSortOption,
    ForensicField,
    GlobalFilter,
    GlobalFilters,
    ForensicFieldsRequest,
    ForensicFieldsResponse,
    HumanBrowserData,
    HumanDeviceData,
    HumanGeolocationData,
    HumanPlatformData,
    InsightBadBotReductionResponse,
    InsightPersonalStatsResponse,
    InsightUnaddressedAutomationsResponse,
    MaliciousBotASOrgData,
    MaliciousBotASOrgDataV3,
    MaliciousBotAppData,
    MaliciousBotAttackIntentASOrgData,
    MaliciousBotAttackIntentIPData,
    MaliciousBotAttackIntentUAData,
    MaliciousBotIPData,
    MaliciousBotIPDataV3,
    MaliciousBotUAData,
    MaliciousBotUADataV4,
    MaliciousReportAPPTimeSeries,
    MaliciousReportAPPData,
    MaliciousReportAPPTimeSeriesResponse,
    MaliciousReportEndpointData,
    MaliciousReportEndpointsResponse,
    MaliciousReportTransactionsData,
    MaliciousReportTransactionsResponse,
    MaliciousTrafficOverviewActionsResponse,
    MaliciousTrafficOverviewActionsV2Response,
    MaliciousTrafficOverviewMetricsResponse,
    MaliciousTrafficTimeseriesActions,
    MaliciousTrafficTimeseriesActionsResponse,
    MaliciousTrafficTimeseriesActionsV2,
    MaliciousTrafficTimeseriesActionsResponseV2,
    MonthlyUsageSummaryData,
    Pagination,
    PeerGroupData,
    PeerGroupResponse,
    PeerGroupTrafficOverviewResponse,
    PeerStatusRequest,
    PeerStatusResponse,
    ReportEndpointDataV2,
    ReportEndpointsResponse,
    SortOption,
    TimeSeriesMinimalData,
    TimeSeriesGraphMinimalData,
    TopAttackIntentData,
    TopAttackIntentResponse,
    TopAttackedBFPResponse,
    TopAttackedEndpointsResponse,
    TopAttackedEndpointsResponseV2,
    TopAttackedEndpointsResponseV4,
    TopAutomationTypesResponse,
    TopCategoriesResponse,
    TopEndpointLabelsResponse,
    TopGoodBotsData,
    TopGoodBotsResponse,
    TopGoodBotsResponseV2,
    TopHumanBrowserResponse,
    TopHumanDeviceResponse,
    TopHumanGeolocationResponse,
    TopHumanPlatformResponse,
    TopLatencyOverviewAppsData,
    TopLatencyOverviewAppsResponse,
    TopLatencyOverviewResponse,
    TopMaliciousBotsAttackIntentByASOrgResponse,
    TopMaliciousBotsAttackIntentByIPResponse,
    TopMaliciousBotsAttackIntentByUAResponse,
    TopMaliciousBotsByASOrgResponse,
    TopMaliciousBotsByASOrgResponseV3,
    TopMaliciousBotsByAppResponse,
    TopMaliciousBotsByIPResponse,
    TopMaliciousBotsByIPResponseV3,
    TopMaliciousBotsByUAResponse,
    TopMaliciousBotsByUAResponseV4,
    TopTransactionsByAppData,
    TopTransactionsByAppResponse,
    TotalAutomationResponse,
    TrafficOverviewData,
    Transaction,
    TrafficOverviewExpandedResponse,
    TrafficOverviewExpandedV5Request,
    TransactionField,
    TransactionRecord,
    TrafficOverviewExpandedV5Response,
    TrafficOverviewResponse,
    TrafficOverviewTimeseriesValue,
    TrafficOverviewTimeseriesResponse,
    TrafficOverviewTimeseriesV2Value,
    TrafficOverviewTimeseriesV2Response,
    TrafficOverviewTimeseriesV3Response,
    TrafficOverviewV2Request,
    TrafficOverviewV2Response,
    TrafficOverviewV3Response,
    TransactionUsageSummaryResponse,
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


class ReportingResource:
    """API methods for reporting.

    Use this API to generate reports for Shape Bot Defense
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.reporting.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def peer_status_check(
        self,
        body: dict[str, Any] | None = None,
    ) -> PeerStatusResponse:
        """Peer Status Check for reporting.

         Check if the tenant has the peer or not
        """
        path = "/api/shape/bot/namespaces/system/reporting/peers/check"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PeerStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "peer_status_check", e, response) from e

    def atb_status(
        self,
        namespace: str,
        virtual_host: str | None = None,
    ) -> ATBResponse:
        """Atb Status for reporting.

        ATB Status
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/atb"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if virtual_host is not None:
            params["virtual_host"] = virtual_host

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ATBResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "atb_status", e, response) from e

    def atb(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ATBResponse:
        """Atb for reporting.

        Enable/disable ATB
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/atb"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ATBResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "atb", e, response) from e

    def consumption_summary(
        self,
        namespace: str,
        start: str | None = None,
        end: str | None = None,
    ) -> ConsumptionSummaryResponse:
        """Consumption Summary for reporting.

        Get Consumption summary
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/consumption/summary"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ConsumptionSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "consumption_summary", e, response) from e

    def endpoint_categories(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> EndpointCategoryResponse:
        """Endpoint Categories for reporting.

        Get Endpoint Category Breakdown
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/endpoint/categories"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EndpointCategoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "endpoint_categories", e, response) from e

    def endpoint_categories_label(
        self,
        namespace: str,
        category: str,
        body: dict[str, Any] | None = None,
    ) -> EndpointCategoryResponse:
        """Endpoint Categories Label for reporting.

        Get Endpoint Category Breakdown
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/endpoint/categories/{category}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{category}", category)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EndpointCategoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "endpoint_categories_label", e, response) from e

    def endpoint_list(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> EndpointListResponse:
        """Endpoint List for reporting.

        Get All Protected Endpoints
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/endpoint/list"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EndpointListResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "endpoint_list", e, response) from e

    def endpoint_summary(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> EndpointSummaryResponse:
        """Endpoint Summary for reporting.

        Get Endpoint Summary
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/endpoint/summary"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EndpointSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "endpoint_summary", e, response) from e

    def report_endpoints(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ReportEndpointsResponse:
        """Report Endpoints for reporting.

        Report Endpoints
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/endpoints"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReportEndpointsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "report_endpoints", e, response) from e

    def credential_stuffing_attack(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> CredentialStuffingAttackResponse:
        """Credential Stuffing Attack for reporting.

        Get Insight Credential Stuffing Attack
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/insight/credential-stuffing-attack"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CredentialStuffingAttackResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "credential_stuffing_attack", e, response) from e

    def insight_bad_bot_reduction(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> InsightBadBotReductionResponse:
        """Insight Bad Bot Reduction for reporting.

        Insight Bad Bot Reduction
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/insight/event/bad-bot-reduction"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return InsightBadBotReductionResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "insight_bad_bot_reduction", e, response) from e

    def insight_unaddressed_automations(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> InsightUnaddressedAutomationsResponse:
        """Insight Unaddressed Automations for reporting.

        Insight Unaddressed Automations
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/insight/event/unaddressed-automations"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return InsightUnaddressedAutomationsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "insight_unaddressed_automations", e, response) from e

    def insight_personal_stats(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> InsightPersonalStatsResponse:
        """Insight Personal Stats for reporting.

        Insight Personal Stats
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/insight/personal-stats"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return InsightPersonalStatsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "insight_personal_stats", e, response) from e

    def total_automation(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TotalAutomationResponse:
        """Total Automation for reporting.

        Get Insight Totol Automation data
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/insight/total-automation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TotalAutomationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "total_automation", e, response) from e

    def malicious_report_endpoints(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportEndpointsResponse:
        """Malicious Report Endpoints for reporting.

        Malicious Report Endpoints
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/malicious/endpoints"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportEndpointsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_endpoints", e, response) from e

    def malicious_report_transactions_asn(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportTransactionsResponse:
        """Malicious Report Transactions Asn for reporting.

        Malicious Report Transactions ASN
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/malicious/transactions/asn"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_transactions_asn", e, response) from e

    def malicious_report_transactions_browser(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportTransactionsResponse:
        """Malicious Report Transactions Browser for reporting.

        Malicious Report Transactions Browser
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/malicious/transactions/browser"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_transactions_browser", e, response) from e

    def malicious_report_transactions_ip(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportTransactionsResponse:
        """Malicious Report Transactions Ip for reporting.

        Malicious Report Transactions IP
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/malicious/transactions/ip"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_transactions_ip", e, response) from e

    def malicious_report_transactions_os(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportTransactionsResponse:
        """Malicious Report Transactions Os for reporting.

        Malicious Report Transactions OS
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/malicious/transactions/os"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_transactions_os", e, response) from e

    def malicious_report_transactions_ua(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportTransactionsResponse:
        """Malicious Report Transactions Ua for reporting.

        Malicious Report Transactions UA
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/malicious/transactions/ua"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_transactions_ua", e, response) from e

    def top_attacked_endpoints(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAttackedEndpointsResponse:
        """Top Attacked Endpoints for reporting.

        Get top attacked application endpoints
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/endpoints"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAttackedEndpointsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_attacked_endpoints", e, response) from e

    def top_latency_overview(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopLatencyOverviewResponse:
        """Top Latency Overview for reporting.

        Get top latency overview
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/latency/overview"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopLatencyOverviewResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_latency_overview", e, response) from e

    def top_latency_overview_apps(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopLatencyOverviewAppsResponse:
        """Top Latency Overview Apps for reporting.

        Get top latency overview apps
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/latency/overview/apps"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopLatencyOverviewAppsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_latency_overview_apps", e, response) from e

    def top_malicious_bots_by_as_org(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByASOrgResponse:
        """Top Malicious Bots By As Org for reporting.

        Get top malicious bots by AS Organization
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/malicious/asorg"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByASOrgResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_as_org", e, response) from e

    def top_automation_types(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAutomationTypesResponse:
        """Top Automation Types for reporting.

        Get top malicious bots automation types
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/malicious/automation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAutomationTypesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_automation_types", e, response) from e

    def top_malicious_bots_by_ip(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByIPResponse:
        """Top Malicious Bots By Ip for reporting.

        Get Top Malicious Bots by source IP address
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/malicious/ip"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByIPResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_ip", e, response) from e

    def top_malicious_bots_by_ua(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByUAResponse:
        """Top Malicious Bots By Ua for reporting.

        Get top malicious bots by user agent string
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/malicious/ua"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByUAResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_ua", e, response) from e

    def top_transactions_by_app(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopTransactionsByAppResponse:
        """Top Transactions By App for reporting.

        Get Top Transactions by Application
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/transactions/app"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopTransactionsByAppResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_transactions_by_app", e, response) from e

    def top_categories(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopCategoriesResponse:
        """Top Categories for reporting.

        Get top flow label categories
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/transactions/categories"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopCategoriesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_categories", e, response) from e

    def top_endpoint_labels(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopEndpointLabelsResponse:
        """Top Endpoint Labels for reporting.

        Get top Endpoint labels
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/transactions/endpointlabels"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopEndpointLabelsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_endpoint_labels", e, response) from e

    def top_good_bots(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopGoodBotsResponse:
        """Top Good Bots for reporting.

        Get top good bots
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/good"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopGoodBotsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_good_bots", e, response) from e

    def top_human_browser(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopHumanBrowserResponse:
        """Top Human Browser for reporting.

        Get top human browser
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/human/dimension/browser"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopHumanBrowserResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_human_browser", e, response) from e

    def top_human_device(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopHumanDeviceResponse:
        """Top Human Device for reporting.

        Get top human device
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/human/dimension/device"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopHumanDeviceResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_human_device", e, response) from e

    def top_human_geolocation(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopHumanGeolocationResponse:
        """Top Human Geolocation for reporting.

        Get top human geolocation
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/human/dimension/geolocation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopHumanGeolocationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_human_geolocation", e, response) from e

    def top_human_platform(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopHumanPlatformResponse:
        """Top Human Platform for reporting.

        Get top human platform
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/human/dimension/platform"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopHumanPlatformResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_human_platform", e, response) from e

    def top_malicious_bots_by_app(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByAppResponse:
        """Top Malicious Bots By App for reporting.

        Get Top Malicious Bots by Application
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/app"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByAppResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_app", e, response) from e

    def malicious_report_app_time_series(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportAPPTimeSeriesResponse:
        """Malicious Report App Time Series for reporting.

        Malicious Report APP Time Series
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/apps/timeseries"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportAPPTimeSeriesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_app_time_series", e, response) from e

    def top_malicious_bots_by_as_org_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByASOrgResponse:
        """Top Malicious Bots By As Org V2 for reporting.

        Get top malicious bots by AS Organization v2
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/asorg"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByASOrgResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_as_org_v2", e, response) from e

    def top_malicious_bots_attack_intent_by_as_org(
        self,
        namespace: str,
        attack_type: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsAttackIntentByASOrgResponse:
        """Top Malicious Bots Attack Intent By As Org for reporting.

        Get Top Malicious Bot Event by ASN of Attack Intent Type
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/asorg/{attack_type}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{attack_type}", attack_type)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsAttackIntentByASOrgResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_attack_intent_by_as_org", e, response) from e

    def top_malicious_bot_by_attack_intent(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAttackIntentResponse:
        """Top Malicious Bot By Attack Intent for reporting.

        Top Malicious Bots by Attack Intent
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/attackintent"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAttackIntentResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bot_by_attack_intent", e, response) from e

    def top_automation_types_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAutomationTypesResponse:
        """Top Automation Types V2 for reporting.

        Get top malicious bots automation types v2
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/automation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAutomationTypesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_automation_types_v2", e, response) from e

    def top_attacked_bfp(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAttackedBFPResponse:
        """Top Attacked Bfp for reporting.

        Top Attacked BFP
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/bfp"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAttackedBFPResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_attacked_bfp", e, response) from e

    def top_attacked_endpoints_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAttackedEndpointsResponse:
        """Top Attacked Endpoints V2 for reporting.

        Get top attacked application endpoints v2
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/endpoints"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAttackedEndpointsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_attacked_endpoints_v2", e, response) from e

    def top_malicious_bots_by_ipv2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByIPResponse:
        """Top Malicious Bots By Ipv2 for reporting.

        Get Top Malicious Bots by source IP address v2
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/ip"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByIPResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_ipv2", e, response) from e

    def top_malicious_bots_attack_intent_by_ip(
        self,
        namespace: str,
        attack_type: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsAttackIntentByIPResponse:
        """Top Malicious Bots Attack Intent By Ip for reporting.

        Get Top Malicious Bot Event by Source IP of Attack Intent Type
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/ip/{attack_type}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{attack_type}", attack_type)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsAttackIntentByIPResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_attack_intent_by_ip", e, response) from e

    def top_malicious_bots_by_uav2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByUAResponse:
        """Top Malicious Bots By Uav2 for reporting.

        Get top malicious bots by user agent string v2
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/ua"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByUAResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_uav2", e, response) from e

    def top_malicious_bots_attack_intent_by_ua(
        self,
        namespace: str,
        attack_type: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsAttackIntentByUAResponse:
        """Top Malicious Bots Attack Intent By Ua for reporting.

        Get Top Malicious Bot Event by UA of Attack Intent Type
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/top/type/malicious/dimension/ua/{attack_type}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{attack_type}", attack_type)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsAttackIntentByUAResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_attack_intent_by_ua", e, response) from e

    def attack_intent_time_series(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AttackIntentTimeSeriesResponse:
        """Attack Intent Time Series for reporting.

        Attack Intent Time Series For All Traffic
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/traffic/dimension/attackintent/timeseries"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AttackIntentTimeSeriesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "attack_intent_time_series", e, response) from e

    def categories_time_series(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> CategoriesTimeSeriesResponse:
        """Categories Time Series for reporting.

        Categories Time Series For All Traffic Get TimeSeries data list for...
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/traffic/dimension/categories/timeseries"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CategoriesTimeSeriesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "categories_time_series", e, response) from e

    def malicious_attack_intent_time_series(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AttackIntentTimeSeriesResponse:
        """Malicious Attack Intent Time Series for reporting.

        Malicious Bot Attack Intent Time Series
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/traffic/malicious/dimension/attackintent/timeseries"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AttackIntentTimeSeriesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_attack_intent_time_series", e, response) from e

    def malicious_traffic_overview_actions(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousTrafficOverviewActionsResponse:
        """Malicious Traffic Overview Actions for reporting.

        Get Malicious Traffic Overview in Actions
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/traffic/malicious/overview/actions"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousTrafficOverviewActionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_traffic_overview_actions", e, response) from e

    def malicious_traffic_overview_metrics(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousTrafficOverviewMetricsResponse:
        """Malicious Traffic Overview Metrics for reporting.

        Malicious Traffic Overview Metrics
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/traffic/malicious/overview/metrics"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousTrafficOverviewMetricsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_traffic_overview_metrics", e, response) from e

    def malicious_traffic_timeseries_actions(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousTrafficTimeseriesActionsResponse:
        """Malicious Traffic Timeseries Actions for reporting.

        Get Malicious Traffic Overview Timeseries in Actions
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/traffic/malicious/overview/timeseries/actions"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousTrafficTimeseriesActionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_traffic_timeseries_actions", e, response) from e

    def traffic_overview(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewResponse:
        """Traffic Overview for reporting.

        Get traffic overview
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/traffic/overview"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview", e, response) from e

    def traffic_overview_expanded(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewExpandedResponse:
        """Traffic Overview Expanded for reporting.

        Get expanded traffic overview
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/traffic/overview/expanded"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewExpandedResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_expanded", e, response) from e

    def traffic_overview_timeseries(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewTimeseriesResponse:
        """Traffic Overview Timeseries for reporting.

        Get Traffic Overview Timeseries
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/traffic/overview/timeseries"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewTimeseriesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_timeseries", e, response) from e

    def transaction_usage_summary(
        self,
        namespace: str,
        start: str | None = None,
        end: str | None = None,
    ) -> TransactionUsageSummaryResponse:
        """Transaction Usage Summary for reporting.

        Get transactions usage summary
        """
        path = "/api/shape/bot/namespaces/{namespace}/reporting/usage/summary"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TransactionUsageSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "transaction_usage_summary", e, response) from e

    def forensic_fields(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ForensicFieldsResponse:
        """Forensic Fields for reporting.

        Get
        """
        path = "/api/shape/bot/namespaces/{namespace}/v1/reporting/forensic/fields"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ForensicFieldsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "forensic_fields", e, response) from e

    def automated_traffic_actions(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AutomatedTrafficActionsResponse:
        """Automated Traffic Actions for reporting.

        Get All Automated Traffic Actions
        """
        path = "/api/shape/bot/namespaces/{namespace}/v1/reporting/traffic/automated/overview/actions"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AutomatedTrafficActionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "automated_traffic_actions", e, response) from e

    def endpoint_summary_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> EndpointSummaryResponseV2:
        """Endpoint Summary V2 for reporting.

        Get Endpoint Summary V2 with Unevaluated Transactions
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/endpoint/summary"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EndpointSummaryResponseV2(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "endpoint_summary_v2", e, response) from e

    def malicious_report_endpoints_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportEndpointsResponse:
        """Malicious Report Endpoints V2 for reporting.

        Malicious Report Endpoints V2, with the new definition of malicious...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/malicious/endpoints"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportEndpointsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_endpoints_v2", e, response) from e

    def malicious_report_transactions_asnv2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportTransactionsResponse:
        """Malicious Report Transactions Asnv2 for reporting.

        Malicious Report Transactions ASN V2, with the new definition of...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/malicious/transactions/asn"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_transactions_asnv2", e, response) from e

    def malicious_report_transactions_browser_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportTransactionsResponse:
        """Malicious Report Transactions Browser V2 for reporting.

        Malicious Report Transactions Browser V2, with the new definition of...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/malicious/transactions/browser"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_transactions_browser_v2", e, response) from e

    def malicious_report_transactions_ipv2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportTransactionsResponse:
        """Malicious Report Transactions Ipv2 for reporting.

        Malicious Report Transactions IP V2, with the new definition of...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/malicious/transactions/ip"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_transactions_ipv2", e, response) from e

    def malicious_report_transactions_osv2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportTransactionsResponse:
        """Malicious Report Transactions Osv2 for reporting.

        Malicious Report Transactions OS V2, with the new definition of...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/malicious/transactions/os"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_transactions_osv2", e, response) from e

    def malicious_report_transactions_uav2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportTransactionsResponse:
        """Malicious Report Transactions Uav2 for reporting.

        Malicious Report Transactions UA V2, with the new definition of...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/malicious/transactions/ua"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_transactions_uav2", e, response) from e

    def top_good_bots_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopGoodBotsResponseV2:
        """Top Good Bots V2 for reporting.

        Get top good bots V2
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/good"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopGoodBotsResponseV2(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_good_bots_v2", e, response) from e

    def top_human_browser_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopHumanBrowserResponse:
        """Top Human Browser V2 for reporting.

        Get top human browser v2 with sub-categories
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/human/dimension/browser"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopHumanBrowserResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_human_browser_v2", e, response) from e

    def top_human_device_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopHumanDeviceResponse:
        """Top Human Device V2 for reporting.

        Get top human device v2 with sub-categories
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/human/dimension/device"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopHumanDeviceResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_human_device_v2", e, response) from e

    def top_human_geolocation_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopHumanGeolocationResponse:
        """Top Human Geolocation V2 for reporting.

        Get top human geolocation v2 with sub-categories
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/human/dimension/geolocation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopHumanGeolocationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_human_geolocation_v2", e, response) from e

    def top_human_platform_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopHumanPlatformResponse:
        """Top Human Platform V2 for reporting.

        Get top human platform v2 with sub-categories
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/human/dimension/platform"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopHumanPlatformResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_human_platform_v2", e, response) from e

    def malicious_report_app_time_series_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousReportAPPTimeSeriesResponse:
        """Malicious Report App Time Series V2 for reporting.

        Malicious Report APP Time Series V2, with the new definition of...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/malicious/dimension/apps/timeseries"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousReportAPPTimeSeriesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_report_app_time_series_v2", e, response) from e

    def top_malicious_bots_attack_intent_by_as_org_v2(
        self,
        namespace: str,
        attack_type: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsAttackIntentByASOrgResponse:
        """Top Malicious Bots Attack Intent By As Org V2 for reporting.

        Get Top Malicious Bot Event by ASN of Attack Intent Type V2, with...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/malicious/dimension/asorg/{attack_type}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{attack_type}", attack_type)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsAttackIntentByASOrgResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_attack_intent_by_as_org_v2", e, response) from e

    def top_malicious_bot_by_attack_intent_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAttackIntentResponse:
        """Top Malicious Bot By Attack Intent V2 for reporting.

        Top Malicious Bots by Attack Intent V2, with the new definition of...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/malicious/dimension/attackintent"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAttackIntentResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bot_by_attack_intent_v2", e, response) from e

    def top_attacked_endpoints_v3(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAttackedEndpointsResponseV2:
        """Top Attacked Endpoints V3 for reporting.

        Get top attacked application endpoints v3
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/malicious/dimension/endpoints"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAttackedEndpointsResponseV2(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_attacked_endpoints_v3", e, response) from e

    def top_malicious_bots_attack_intent_by_ipv2(
        self,
        namespace: str,
        attack_type: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsAttackIntentByIPResponse:
        """Top Malicious Bots Attack Intent By Ipv2 for reporting.

        Get Top Malicious Bot Event by Source IP of Attack Intent Type V2,...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/malicious/dimension/ip/{attack_type}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{attack_type}", attack_type)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsAttackIntentByIPResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_attack_intent_by_ipv2", e, response) from e

    def top_malicious_bots_attack_intent_by_uav2(
        self,
        namespace: str,
        attack_type: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsAttackIntentByUAResponse:
        """Top Malicious Bots Attack Intent By Uav2 for reporting.

        Get Top Malicious Bot Event by UA of Attack Intent Type V2, with the...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/top/type/malicious/dimension/ua/{attack_type}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{attack_type}", attack_type)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsAttackIntentByUAResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_attack_intent_by_uav2", e, response) from e

    def malicious_attack_intent_time_series_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AttackIntentTimeSeriesResponse:
        """Malicious Attack Intent Time Series V2 for reporting.

        Malicious Bot Attack Intent Time Series V2, with the new definition...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/traffic/malicious/dimension/attackintent/timeseries"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AttackIntentTimeSeriesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_attack_intent_time_series_v2", e, response) from e

    def malicious_traffic_overview_actions_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousTrafficOverviewActionsV2Response:
        """Malicious Traffic Overview Actions V2 for reporting.

        Get Malicious Traffic Overview in Actions
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/traffic/malicious/overview/actions"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousTrafficOverviewActionsV2Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_traffic_overview_actions_v2", e, response) from e

    def malicious_traffic_overview_metrics_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousTrafficOverviewMetricsResponse:
        """Malicious Traffic Overview Metrics V2 for reporting.

        Malicious Traffic Overview Metrics V2, with the new definition of...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/traffic/malicious/overview/metrics"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousTrafficOverviewMetricsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_traffic_overview_metrics_v2", e, response) from e

    def malicious_traffic_timeseries_actions_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MaliciousTrafficTimeseriesActionsResponseV2:
        """Malicious Traffic Timeseries Actions V2 for reporting.

        Get Malicious Traffic Overview Timeseries in Actions Get the...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/traffic/malicious/overview/timeseries/actions"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MaliciousTrafficTimeseriesActionsResponseV2(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "malicious_traffic_timeseries_actions_v2", e, response) from e

    def traffic_overview_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewV2Response:
        """Traffic Overview V2 for reporting.

        Get traffic overview v2
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/traffic/overview"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewV2Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_v2", e, response) from e

    def traffic_overview_expanded_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewExpandedResponse:
        """Traffic Overview Expanded V2 for reporting.

        Get expanded traffic overview v2
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/traffic/overview/expanded"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewExpandedResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_expanded_v2", e, response) from e

    def traffic_overview_timeseries_v2(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewTimeseriesV2Response:
        """Traffic Overview Timeseries V2 for reporting.

        Get Traffic Overview Timeseries V2
        """
        path = "/api/shape/bot/namespaces/{namespace}/v2/reporting/traffic/overview/timeseries"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewTimeseriesV2Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_timeseries_v2", e, response) from e

    def top_good_bots_v3(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopGoodBotsResponseV2:
        """Top Good Bots V3 for reporting.

        Get top good bots V3, with the new definition of malicious bot for...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v3/reporting/top/type/good"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopGoodBotsResponseV2(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_good_bots_v3", e, response) from e

    def top_malicious_bots_by_as_org_v3(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByASOrgResponseV3:
        """Top Malicious Bots By As Org V3 for reporting.

        Get top malicious bots by AS Organization v3, with the new...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v3/reporting/top/type/malicious/dimension/asorg"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByASOrgResponseV3(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_as_org_v3", e, response) from e

    def top_automation_types_v3(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAutomationTypesResponse:
        """Top Automation Types V3 for reporting.

        Get top malicious bots automation types v3, with the new definition...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v3/reporting/top/type/malicious/dimension/automation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAutomationTypesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_automation_types_v3", e, response) from e

    def top_malicious_bots_by_ipv3(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByIPResponseV3:
        """Top Malicious Bots By Ipv3 for reporting.

        Get Top Malicious Bots by source IP address v3, with the new...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v3/reporting/top/type/malicious/dimension/ip"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByIPResponseV3(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_ipv3", e, response) from e

    def top_malicious_bots_by_uav3(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByUAResponse:
        """Top Malicious Bots By Uav3 for reporting.

        Get top malicious bots by user agent string v3
        """
        path = "/api/shape/bot/namespaces/{namespace}/v3/reporting/top/type/malicious/dimension/ua"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByUAResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_uav3", e, response) from e

    def traffic_overview_v3(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewV3Response:
        """Traffic Overview V3 for reporting.

        Get traffic overview v3, v3response uses a dynamic structure and has...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v3/reporting/traffic/overview"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewV3Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_v3", e, response) from e

    def traffic_overview_expanded_v3(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewExpandedResponse:
        """Traffic Overview Expanded V3 for reporting.

        Get expanded traffic overview v3
        """
        path = "/api/shape/bot/namespaces/{namespace}/v3/reporting/traffic/overview/expanded"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewExpandedResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_expanded_v3", e, response) from e

    def traffic_overview_timeseries_v3(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewTimeseriesV3Response:
        """Traffic Overview Timeseries V3 for reporting.

        Get the traffic count details based on types like 'Humans,...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v3/reporting/traffic/overview/timeseries"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewTimeseriesV3Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_timeseries_v3", e, response) from e

    def top_attacked_endpoints_v4(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAttackedEndpointsResponseV4:
        """Top Attacked Endpoints V4 for reporting.

        Get top attacked application endpoints v4
        """
        path = "/api/shape/bot/namespaces/{namespace}/v4/reporting/top/type/malicious/dimension/endpoints"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAttackedEndpointsResponseV4(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_attacked_endpoints_v4", e, response) from e

    def top_malicious_bots_by_uav4(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopMaliciousBotsByUAResponseV4:
        """Top Malicious Bots By Uav4 for reporting.

        Get top malicious bots by user agent string v4, with the new...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v4/reporting/top/type/malicious/dimension/ua"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopMaliciousBotsByUAResponseV4(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_malicious_bots_by_uav4", e, response) from e

    def traffic_overview_expanded_v4(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewExpandedResponse:
        """Traffic Overview Expanded V4 for reporting.

        Get expanded Traffic overview in Traffic Analyzer. This version adds...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v4/reporting/traffic/overview/expanded"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewExpandedResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_expanded_v4", e, response) from e

    def traffic_overview_timeseries_v4(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewTimeseriesV3Response:
        """Traffic Overview Timeseries V4 for reporting.

        Get the traffic count details based on types like Humans, Automated,...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v4/reporting/traffic/overview/timeseries"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewTimeseriesV3Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_timeseries_v4", e, response) from e

    def top_attacked_endpoints_v5(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TopAttackedEndpointsResponseV4:
        """Top Attacked Endpoints V5 for reporting.

        Get top attacked application endpoints v5, with the new definition...
        """
        path = "/api/shape/bot/namespaces/{namespace}/v5/reporting/top/type/malicious/dimension/endpoints"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopAttackedEndpointsResponseV4(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "top_attacked_endpoints_v5", e, response) from e

    def traffic_overview_expanded_v5(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TrafficOverviewExpandedV5Response:
        """Traffic Overview Expanded V5 for reporting.

        Get expanded traffic overview v5 with global filters supported
        """
        path = "/api/shape/bot/namespaces/{namespace}/v5/reporting/traffic/overview/expanded"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TrafficOverviewExpandedV5Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "traffic_overview_expanded_v5", e, response) from e

    def peers_threat_types(
        self,
        body: dict[str, Any] | None = None,
    ) -> PeerGroupResponse:
        """Peers Threat Types for reporting.

        GetThreat Types traffic count for Peergroup Benchmarking
        """
        path = "/api/shape/bot/reporting/peers/threat-types"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PeerGroupResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "peers_threat_types", e, response) from e

    def peers_top_good_bots(
        self,
        body: dict[str, Any] | None = None,
    ) -> PeerGroupResponse:
        """Peers Top Good Bots for reporting.

        Get Peer Group Top Good Bots
        """
        path = "/api/shape/bot/reporting/peers/top-good-bots"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PeerGroupResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "peers_top_good_bots", e, response) from e

    def peers_top_reason_codes(
        self,
        body: dict[str, Any] | None = None,
    ) -> PeerGroupResponse:
        """Peers Top Reason Codes for reporting.

        Get Top Reason Codes
        """
        path = "/api/shape/bot/reporting/peers/top-reason-codes"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PeerGroupResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "peers_top_reason_codes", e, response) from e

    def peers_traffic_overview(
        self,
        body: dict[str, Any] | None = None,
    ) -> PeerGroupTrafficOverviewResponse:
        """Peers Traffic Overview for reporting.

        Get traffic overview
        """
        path = "/api/shape/bot/reporting/peers/traffic/overview"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PeerGroupTrafficOverviewResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("reporting", "peers_traffic_overview", e, response) from e

