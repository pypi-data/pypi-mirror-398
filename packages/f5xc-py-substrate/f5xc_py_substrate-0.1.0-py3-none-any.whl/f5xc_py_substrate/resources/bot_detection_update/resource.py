"""BotDetectionUpdate resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.bot_detection_update.models import (
    BotInfrastructure,
    TimeRange,
    DeploymentRange,
    BotDetectionUpdate,
    DownloadBotDetectionUpdatesReleaseNotesResponse,
    GetBotDetectionUpdatesResponse,
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


class BotDetectionUpdateResource:
    """API methods for bot_detection_update.

    Public Custom API definition for Bot Detection Update
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.bot_detection_update.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_bot_detection_updates(
        self,
        namespace: str,
    ) -> GetBotDetectionUpdatesResponse:
        """Get Bot Detection Updates for bot_detection_update.

        
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_detection_updates"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetBotDetectionUpdatesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_update", "get_bot_detection_updates", e, response) from e

    def download_bot_detection_updates_release_notes(
        self,
        namespace: str,
        deployment_id: str | None = None,
    ) -> DownloadBotDetectionUpdatesReleaseNotesResponse:
        """Download Bot Detection Updates Release Notes for bot_detection_update.

        
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_detection_updates/download_release_notes"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if deployment_id is not None:
            params["deployment_id"] = deployment_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DownloadBotDetectionUpdatesReleaseNotesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_update", "download_bot_detection_updates_release_notes", e, response) from e

