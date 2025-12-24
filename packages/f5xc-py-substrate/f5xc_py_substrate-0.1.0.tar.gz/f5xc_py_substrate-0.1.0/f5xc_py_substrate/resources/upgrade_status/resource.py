"""UpgradeStatus resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.upgrade_status.models import (
    InstallResult,
    ImageDownload,
    UpgradeProgressCount,
    Condition,
    ApplicationObj,
    StageApplication,
    StageUpgradeResults,
    NodeUpgradeResult,
    NodeLevelUpgrade,
    OSNodeResult,
    OSSetup,
    SiteLevelUpgrade,
    Validation,
    SWUpgradeProgress,
    GlobalSpecType,
    Checklist,
    GetUpgradableSWVersionsResponse,
    GetUpgradeStatusResponse,
    PreUpgradeCheckResponse,
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


class UpgradeStatusResource:
    """API methods for upgrade_status.

    Upgrade status custom APIs
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.upgrade_status.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def pre_upgrade_check(
        self,
        namespace: str,
        name: str,
        sw_version: str | None = None,
    ) -> PreUpgradeCheckResponse:
        """Pre Upgrade Check for upgrade_status.

        API to check if site is ready for upgrade
        """
        path = "/api/maurice/namespaces/{namespace}/sites/{name}/pre_upgrade_check"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if sw_version is not None:
            params["sw_version"] = sw_version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PreUpgradeCheckResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("upgrade_status", "pre_upgrade_check", e, response) from e

    def get_upgrade_status(
        self,
        namespace: str,
        name: str,
    ) -> GetUpgradeStatusResponse:
        """Get Upgrade Status for upgrade_status.

        API to get upgrade status of a site
        """
        path = "/api/maurice/namespaces/{namespace}/sites/{name}/upgrade_status"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetUpgradeStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("upgrade_status", "get_upgrade_status", e, response) from e

    def get_upgradable_sw_versions(
        self,
        current_os_version: str | None = None,
        current_sw_version: str | None = None,
    ) -> GetUpgradableSWVersionsResponse:
        """Get Upgradable Sw Versions for upgrade_status.

        API to get list of sw versions that can be upgraded to
        """
        path = "/api/maurice/upgradable_sw_versions"

        params: dict[str, Any] = {}
        if current_os_version is not None:
            params["current_os_version"] = current_os_version
        if current_sw_version is not None:
            params["current_sw_version"] = current_sw_version

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetUpgradableSWVersionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("upgrade_status", "get_upgradable_sw_versions", e, response) from e

