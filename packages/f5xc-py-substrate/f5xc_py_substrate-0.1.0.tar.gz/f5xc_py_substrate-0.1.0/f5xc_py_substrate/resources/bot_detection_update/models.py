"""Pydantic models for bot_detection_update."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class BotInfrastructure(F5XCBaseModel):
    """Bot Infrastructure"""

    environment_type: Optional[Literal['PRODUCTION', 'TESTING']] = None
    name: Optional[str] = None


class TimeRange(F5XCBaseModel):
    """Time range holds the start time and end time"""

    end_time: Optional[str] = None
    start_time: Optional[str] = None


class DeploymentRange(F5XCBaseModel):
    """Deployment range holds the different types of deployment timing i.e..."""

    initiated_time: Optional[str] = None
    time_range: Optional[TimeRange] = None


class BotDetectionUpdate(F5XCBaseModel):
    """Bot detection update holds details of a new threat intelligence package..."""

    bot_infrastructures: Optional[list[BotInfrastructure]] = None
    deployment_id: Optional[str] = None
    deployment_range: Optional[DeploymentRange] = None
    deployment_status: Optional[Literal['THREAT_INTELLIGENCE_PACKAGE_DEPLOYMENT_STATUS_UNKNOWN', 'THREAT_INTELLIGENCE_PACKAGE_DEPLOYMENT_STATUS_INITIATED', 'THREAT_INTELLIGENCE_PACKAGE_DEPLOYMENT_STATUS_DEPLOYED', 'THREAT_INTELLIGENCE_PACKAGE_DEPLOYMENT_STATUS_FAILED', 'THREAT_INTELLIGENCE_PACKAGE_DEPLOYMENT_STATUS_PARTIALLY_DEPLOYED', 'THREAT_INTELLIGENCE_PACKAGE_DEPLOYMENT_STATUS_INITIATION_FAILED', 'THREAT_INTELLIGENCE_PACKAGE_DEPLOYMENT_STATUS_PARTIALLY_INITIATED', 'THREAT_INTELLIGENCE_PACKAGE_DEPLOYMENT_STATUS_PENDING_SUBMISSION']] = None
    traffic_type: Optional[Literal['WEB', 'MOBILE']] = None


class DownloadBotDetectionUpdatesReleaseNotesResponse(F5XCBaseModel):
    """Response for download bot detection updates release notes"""

    pre_signed_url: Optional[str] = None


class GetBotDetectionUpdatesResponse(F5XCBaseModel):
    """Response for get bot detection updates"""

    bot_detection_updates: Optional[list[BotDetectionUpdate]] = None


# Convenience aliases
