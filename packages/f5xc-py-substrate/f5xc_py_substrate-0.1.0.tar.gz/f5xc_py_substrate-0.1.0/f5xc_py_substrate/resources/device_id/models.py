"""Pydantic models for device_id."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ApplicationProvisionRequest(F5XCBaseModel):
    """Any payload to be passed on the Application Provision API"""

    body: Optional[str] = None


class ApplicationProvisionResponse(F5XCBaseModel):
    """Any payload to be return by Application Provision API"""

    body: Optional[str] = None


class DeleteApplicationsResponse(F5XCBaseModel):
    """Any payload to be returned by Delete Applications API"""

    body: Optional[str] = None


class EnableRequest(F5XCBaseModel):
    """Any payload to be passed on the Provision API"""

    region: Optional[str] = None


class EnableResponse(F5XCBaseModel):
    """Any payload to be return by Provision API"""

    body: Optional[str] = None
    status: Optional[str] = None


class GetApplicationsResponse(F5XCBaseModel):
    """Any payload to be returned by Applications API"""

    body: Optional[str] = None


class GetBotAssessmentTopAsnRequest(F5XCBaseModel):
    """Any payload to be passed to the Bot Top ASN API"""

    body: Optional[str] = None


class GetBotAssessmentTopAsnResponse(F5XCBaseModel):
    """Any payload to be returned by Bot Top ASN API"""

    body: Optional[str] = None


class GetBotAssessmentTopUrlsRequest(F5XCBaseModel):
    """Any payload to be passed to the Bot Top URLs API"""

    body: Optional[str] = None


class GetBotAssessmentTopUrlsResponse(F5XCBaseModel):
    """Any payload to be returned by Bot Top URLs API"""

    body: Optional[str] = None


class GetBotAssessmentTransactionsRequest(F5XCBaseModel):
    """Any payload to be passed to the Bot Transactions API"""

    body: Optional[str] = None


class GetBotAssessmentTransactionsResponse(F5XCBaseModel):
    """Any payload to be returned by Bot Transactions API"""

    body: Optional[str] = None


class GetDashboardByAgeRequest(F5XCBaseModel):
    """Any payload to be passed on the Dashboard Age API"""

    body: Optional[str] = None


class GetDashboardByAgeResponse(F5XCBaseModel):
    """Any payload to be return by Dashboard Age API"""

    body: Optional[str] = None
    status: Optional[str] = None


class GetDashboardByApplicationsRequest(F5XCBaseModel):
    """Any payload to be passed on the Dashboard Application API"""

    body: Optional[str] = None


class GetDashboardByApplicationsResponse(F5XCBaseModel):
    """Any payload to be return by Dashboard Application API"""

    body: Optional[str] = None
    status: Optional[str] = None


class GetDashboardByAsnRequest(F5XCBaseModel):
    """Any payload to be passed on the Dashboard Asn API"""

    body: Optional[str] = None


class GetDashboardByAsnResponse(F5XCBaseModel):
    """Any payload to be return by Dashboard Asn API"""

    body: Optional[str] = None
    status: Optional[str] = None


class GetDashboardByCountryRequest(F5XCBaseModel):
    """Any payload to be passed on the Dashboard Country API"""

    body: Optional[str] = None


class GetDashboardByCountryResponse(F5XCBaseModel):
    """Any payload to be return by Dashboard Country API"""

    body: Optional[str] = None
    status: Optional[str] = None


class GetDashboardBySessionRequest(F5XCBaseModel):
    """Any payload to be passed on the Dashboard Session API"""

    body: Optional[str] = None


class GetDashboardBySessionResponse(F5XCBaseModel):
    """Any payload to be return by Dashboard Session API"""

    body: Optional[str] = None
    status: Optional[str] = None


class GetDashboardByUaRequest(F5XCBaseModel):
    """Any payload to be passed on the Dashboard UA API"""

    body: Optional[str] = None


class GetDashboardByUaResponse(F5XCBaseModel):
    """Any payload to be return by Dashboard UA API"""

    body: Optional[str] = None
    status: Optional[str] = None


class GetDashboardUniqueAccessRequest(F5XCBaseModel):
    """Any payload to be passed on the Dashboard Unique API"""

    body: Optional[str] = None


class GetDashboardUniqueAccessResponse(F5XCBaseModel):
    """Any payload to be return by Dashboard Unique API"""

    body: Optional[str] = None
    status: Optional[str] = None


class GetRegionsResponse(F5XCBaseModel):
    """Any payload to be return by Get Regions API"""

    body: Optional[str] = None
    status: Optional[str] = None


class GetStatusResponse(F5XCBaseModel):
    """Any payload to be return by Get Provision API"""

    body: Optional[str] = None
    status: Optional[str] = None


class UpdateApplicationRequest(F5XCBaseModel):
    """Any payload to be passed to the Update Application API"""

    body: Optional[str] = None


class UpdateApplicationResponse(F5XCBaseModel):
    """Any payload to be returned by Update Application API"""

    body: Optional[str] = None


class ValidateSrcTagInjectionRequest(F5XCBaseModel):
    """Request to verify shape Application Traffic Insights src tag injection"""

    src: Optional[str] = None
    url: Optional[str] = None


class ValidateSrcTagInjectionResponse(F5XCBaseModel):
    """Response to indicate whether customer webpage has custom script tag to..."""

    message: Optional[str] = None


# Convenience aliases
