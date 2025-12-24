"""Reporting resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.reporting.models import *
    from f5xc_py_substrate.resources.reporting.resource import ReportingResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "ReportingResource":
        from f5xc_py_substrate.resources.reporting.resource import ReportingResource
        return ReportingResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.reporting.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.reporting' has no attribute '{name}'")


__all__ = [
    "ReportingResource",
    "ReportFreqDaily",
    "ReportFreqMonthly",
    "ReportFreqWeekly",
    "ATBRequest",
    "ATBResponse",
    "ActionData",
    "ActionTakenData",
    "TimeSeriesDataV2",
    "AttackIntentData",
    "AttackIntentTimeSeriesResponse",
    "AttackedBFPData",
    "AttackedEndpointData",
    "DistributionData",
    "AttackedEndpointDataV2",
    "AttackedEndpointDataV4",
    "AutomatedTrafficActionsResponse",
    "AutomationTypeData",
    "CategoriesData",
    "CategoryTimeSeriesData",
    "CategoriesTimeSeriesResponse",
    "ConsumptionData",
    "ConsumptionSummaryResponse",
    "TimeSeriesGraphData",
    "CredentialStuffingAttackResponse",
    "EndpointCategoryData",
    "EndpointCategoryResponse",
    "EndpointLabelsData",
    "EndpointListData",
    "EndpointListResponse",
    "EndpointSummaryResponse",
    "EndpointSummaryResponseV2",
    "ForensicAggregateType",
    "ForensicErrorType",
    "ForensicSuggestType",
    "ForensicData",
    "ForensicSortOption",
    "ForensicField",
    "GlobalFilter",
    "GlobalFilters",
    "ForensicFieldsRequest",
    "ForensicFieldsResponse",
    "HumanBrowserData",
    "HumanDeviceData",
    "HumanGeolocationData",
    "HumanPlatformData",
    "InsightBadBotReductionResponse",
    "InsightPersonalStatsResponse",
    "InsightUnaddressedAutomationsResponse",
    "MaliciousBotASOrgData",
    "MaliciousBotASOrgDataV3",
    "MaliciousBotAppData",
    "MaliciousBotAttackIntentASOrgData",
    "MaliciousBotAttackIntentIPData",
    "MaliciousBotAttackIntentUAData",
    "MaliciousBotIPData",
    "MaliciousBotIPDataV3",
    "MaliciousBotUAData",
    "MaliciousBotUADataV4",
    "MaliciousReportAPPTimeSeries",
    "MaliciousReportAPPData",
    "MaliciousReportAPPTimeSeriesResponse",
    "MaliciousReportEndpointData",
    "MaliciousReportEndpointsResponse",
    "MaliciousReportTransactionsData",
    "MaliciousReportTransactionsResponse",
    "MaliciousTrafficOverviewActionsResponse",
    "MaliciousTrafficOverviewActionsV2Response",
    "MaliciousTrafficOverviewMetricsResponse",
    "MaliciousTrafficTimeseriesActions",
    "MaliciousTrafficTimeseriesActionsResponse",
    "MaliciousTrafficTimeseriesActionsV2",
    "MaliciousTrafficTimeseriesActionsResponseV2",
    "MonthlyUsageSummaryData",
    "Pagination",
    "PeerGroupData",
    "PeerGroupResponse",
    "PeerGroupTrafficOverviewResponse",
    "PeerStatusRequest",
    "PeerStatusResponse",
    "ReportEndpointDataV2",
    "ReportEndpointsResponse",
    "SortOption",
    "TimeSeriesMinimalData",
    "TimeSeriesGraphMinimalData",
    "TopAttackIntentData",
    "TopAttackIntentResponse",
    "TopAttackedBFPResponse",
    "TopAttackedEndpointsResponse",
    "TopAttackedEndpointsResponseV2",
    "TopAttackedEndpointsResponseV4",
    "TopAutomationTypesResponse",
    "TopCategoriesResponse",
    "TopEndpointLabelsResponse",
    "TopGoodBotsData",
    "TopGoodBotsResponse",
    "TopGoodBotsResponseV2",
    "TopHumanBrowserResponse",
    "TopHumanDeviceResponse",
    "TopHumanGeolocationResponse",
    "TopHumanPlatformResponse",
    "TopLatencyOverviewAppsData",
    "TopLatencyOverviewAppsResponse",
    "TopLatencyOverviewResponse",
    "TopMaliciousBotsAttackIntentByASOrgResponse",
    "TopMaliciousBotsAttackIntentByIPResponse",
    "TopMaliciousBotsAttackIntentByUAResponse",
    "TopMaliciousBotsByASOrgResponse",
    "TopMaliciousBotsByASOrgResponseV3",
    "TopMaliciousBotsByAppResponse",
    "TopMaliciousBotsByIPResponse",
    "TopMaliciousBotsByIPResponseV3",
    "TopMaliciousBotsByUAResponse",
    "TopMaliciousBotsByUAResponseV4",
    "TopTransactionsByAppData",
    "TopTransactionsByAppResponse",
    "TotalAutomationResponse",
    "TrafficOverviewData",
    "Transaction",
    "TrafficOverviewExpandedResponse",
    "TrafficOverviewExpandedV5Request",
    "TransactionField",
    "TransactionRecord",
    "TrafficOverviewExpandedV5Response",
    "TrafficOverviewResponse",
    "TrafficOverviewTimeseriesValue",
    "TrafficOverviewTimeseriesResponse",
    "TrafficOverviewTimeseriesV2Value",
    "TrafficOverviewTimeseriesV2Response",
    "TrafficOverviewTimeseriesV3Response",
    "TrafficOverviewV2Request",
    "TrafficOverviewV2Response",
    "TrafficOverviewV3Response",
    "TransactionUsageSummaryResponse",
    "Spec",
]
