"""Pydantic models for upgrade_status."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class InstallResult(F5XCBaseModel):
    """InstallResult shows the result each application/process."""

    message: Optional[str] = None
    name: Optional[str] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None
    type_: Optional[str] = Field(default=None, alias="type")


class ImageDownload(F5XCBaseModel):
    """ImageDownload shows each the entire image download stage."""

    results: Optional[list[InstallResult]] = None
    start_timestamp: Optional[str] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None


class UpgradeProgressCount(F5XCBaseModel):
    """UpgradeProgressCount counts the total and completed apps that have been upgraded."""

    completed: Optional[int] = None
    total: Optional[int] = None


class Condition(F5XCBaseModel):
    """Condition of object in each phase of installation"""

    message: Optional[str] = None
    result: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class ApplicationObj(F5XCBaseModel):
    """ApplicationObj shows the upgrade status of each object in a application..."""

    conditions: Optional[list[Condition]] = None
    debug: Optional[str] = None
    deploy_strategy: Optional[str] = None
    kind: Optional[str] = None
    name: Optional[str] = None


class StageApplication(F5XCBaseModel):
    """StageApplication shows the upgrade status of each application in either..."""

    name: Optional[str] = None
    objects: Optional[list[ApplicationObj]] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None


class StageUpgradeResults(F5XCBaseModel):
    """SiteLevelStageUpgradeResults shows the upgrade status of each stage and..."""

    applications: Optional[list[StageApplication]] = None
    name: Optional[str] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None


class NodeUpgradeResult(F5XCBaseModel):
    name: Optional[str] = None
    progress: Optional[UpgradeProgressCount] = None
    results: Optional[list[StageUpgradeResults]] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None


class NodeLevelUpgrade(F5XCBaseModel):
    """Node level upgrade shows the upgrades that are happening on a site level..."""

    results: Optional[list[NodeUpgradeResult]] = None
    start_timestamp: Optional[str] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None


class OSNodeResult(F5XCBaseModel):
    """OSNodeResult shows the result of OS upgrade for each node"""

    name: Optional[str] = None
    results: Optional[list[InstallResult]] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None


class OSSetup(F5XCBaseModel):
    """OSSetup shows the OS Setup stage."""

    results: Optional[list[OSNodeResult]] = None
    start_timestamp: Optional[str] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None


class SiteLevelUpgrade(F5XCBaseModel):
    """Site level upgrade shows the upgrades that are happening on a site level..."""

    progress: Optional[UpgradeProgressCount] = None
    results: Optional[list[StageUpgradeResults]] = None
    start_timestamp: Optional[str] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None


class Validation(F5XCBaseModel):
    """Validation represents the last stage in the upgrade phase, checking if..."""

    results: Optional[list[str]] = None
    start_timestamp: Optional[str] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None


class SWUpgradeProgress(F5XCBaseModel):
    """SWStatus stores information about CE Site upgrade status"""

    failure_reason: Optional[str] = None
    image_download: Optional[ImageDownload] = None
    node_level_upgrade: Optional[NodeLevelUpgrade] = None
    os_setup: Optional[OSSetup] = None
    retries: Optional[int] = None
    site: Optional[str] = None
    site_level_upgrade: Optional[SiteLevelUpgrade] = None
    status: Optional[Literal['UNKNOWN', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED']] = None
    validation: Optional[Validation] = None
    version: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    sw_upgrade_progress: Optional[SWUpgradeProgress] = None


class Checklist(F5XCBaseModel):
    item: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[Literal['CHECKLIST_UNKNOWN', 'CHECKLIST_PASSED', 'CHECKLIST_FAILED', 'CHECKLIST_WARNING']] = None


class GetUpgradableSWVersionsResponse(F5XCBaseModel):
    """Response to get the list of upgradable sw versions"""

    sw_versions: Optional[list[str]] = None


class GetUpgradeStatusResponse(F5XCBaseModel):
    """Response to get the upgrade status"""

    upgrade_status: Optional[GlobalSpecType] = None


class PreUpgradeCheckResponse(F5XCBaseModel):
    """Result of pre upgrade checks"""

    checklist: Optional[list[Checklist]] = None


# Convenience aliases
Spec = GlobalSpecType
