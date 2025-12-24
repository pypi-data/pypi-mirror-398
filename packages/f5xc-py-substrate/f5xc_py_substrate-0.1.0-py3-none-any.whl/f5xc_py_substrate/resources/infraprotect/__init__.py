"""Infraprotect resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.infraprotect.models import *
    from f5xc_py_substrate.resources.infraprotect.resource import InfraprotectResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "InfraprotectResource":
        from f5xc_py_substrate.resources.infraprotect.resource import InfraprotectResource
        return InfraprotectResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.infraprotect.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.infraprotect' has no attribute '{name}'")


__all__ = [
    "InfraprotectResource",
    "AccessFlag",
    "AddAlertToEventRequest",
    "AddAlertToEventResponse",
    "Attachment",
    "AddEventDetailRequest",
    "EventDetail",
    "AddEventDetailResponse",
    "Event",
    "Alert",
    "AlertPort",
    "AlertPrefix",
    "Ipv4AddressType",
    "Ipv6AddressType",
    "IpAddressType",
    "Empty",
    "DeviceLocation",
    "BGPPeerStatusItem",
    "BGPPeerStatusRequest",
    "BGPPeerStatusResponse",
    "CustomerAccessResponse",
    "DeleteEventDetailResponse",
    "EditEventDetailRequest",
    "EditEventDetailResponse",
    "EditEventRequest",
    "EditEventResponse",
    "EventSummary",
    "GetAlertResponse",
    "GetEventResponse",
    "GetMitigationResponse",
    "GetReportResponse",
    "ListAlertsRequest",
    "ListAlertsResponse",
    "ListEventAlertsResponse",
    "ListEventAttachmentsResponse",
    "ListEventDetailsResponse",
    "MitigationAnnotation",
    "ListEventMitigationsResponse",
    "ListEventsRequest",
    "ListEventsResponse",
    "ListEventsSummaryResponse",
    "ListMitigationAnnotationsResponse",
    "MitigationIP",
    "ListMitigationIPsResponse",
    "ListMitigationsRequest",
    "Mitigation",
    "ListMitigationsResponse",
    "PrefixListType",
    "Network",
    "ListNetworksResponse",
    "ListReportsRequest",
    "Report",
    "ListReportsResponse",
    "ProtobufAny",
    "SuggestValuesReq",
    "TrendValue",
    "MetricValue",
    "TransitUsageTypeData",
    "TransitUsageData",
    "TransitUsageRequest",
    "TransitUsageResponse",
    "ObjectRefType",
    "SuggestedItem",
    "SuggestValuesResp",
    "Spec",
]
