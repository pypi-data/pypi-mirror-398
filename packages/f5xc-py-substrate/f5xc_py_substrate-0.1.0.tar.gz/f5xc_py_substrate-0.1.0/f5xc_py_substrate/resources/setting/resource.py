"""Setting resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.setting.models import (
    ProtobufAny,
    HttpBody,
    InitialAccess,
    Notification,
    NotificationList,
    PersonaPreferences,
    SetViewPreferenceRequest,
    UpdateImageRequest,
    UserSession,
    UserSessionList,
    UserSettingsRequest,
    UserSettingsResponse,
    ViewPreference,
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


class SettingResource:
    """API methods for setting.

    Custom API of user settings.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.setting.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_admin_ntfn_preferences(
        self,
    ) -> NotificationList:
        """Get Admin Ntfn Preferences for setting.

        Get admin ntfn preferences gets current admin notification...
        """
        path = "/api/web/namespaces/system/user/admin_notifications"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return NotificationList(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "get_admin_ntfn_preferences", e, response) from e

    def update_admin_ntfn_preferences(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Update Admin Ntfn Preferences for setting.

        Update admin ntfn preferences updates admin notification preferences...
        """
        path = "/api/web/namespaces/system/user/admin_notifications"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "update_admin_ntfn_preferences", e, response) from e

    def unset_admin_ntfn_preference(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Unset Admin Ntfn Preference for setting.

        Unset admin ntfn preference unsets specific admin notification...
        """
        path = "/api/web/namespaces/system/user/admin_notifications/unset"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "unset_admin_ntfn_preference", e, response) from e

    def get_combined_ntfn_preferences(
        self,
    ) -> NotificationList:
        """Get Combined Ntfn Preferences for setting.

        Get combined ntfn preferences gets user-ntfn-preferences and...
        """
        path = "/api/web/namespaces/system/user/combined_notifications"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return NotificationList(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "get_combined_ntfn_preferences", e, response) from e

    def update_combined_ntfn_preferences(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Update Combined Ntfn Preferences for setting.

        Update combined ntfn preferences updates both user-ntfn-preferences...
        """
        path = "/api/web/namespaces/system/user/combined_notifications"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "update_combined_ntfn_preferences", e, response) from e

    def get_ntfn_preferences(
        self,
    ) -> NotificationList:
        """Get Ntfn Preferences for setting.

        Get ntfn preferences gets current notification preferences for user....
        """
        path = "/api/web/namespaces/system/user/notifications"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return NotificationList(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "get_ntfn_preferences", e, response) from e

    def update_ntfn_preferences(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Update Ntfn Preferences for setting.

        Update ntfn preferences updates notification preferences for the...
        """
        path = "/api/web/namespaces/system/user/notifications"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "update_ntfn_preferences", e, response) from e

    def unset_ntfn_preference(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Unset Ntfn Preference for setting.

        Unset ntfn preference unsets specific notification preference for...
        """
        path = "/api/web/namespaces/system/user/notifications/unset"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "unset_ntfn_preference", e, response) from e

    def reset_otp_device_by_admin(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Reset Otp Device By Admin for setting.

        TODO(evg): description
        """
        path = "/api/web/namespaces/system/user/otp/admin_reset"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "reset_otp_device_by_admin", e, response) from e

    def get_user_sessions(
        self,
    ) -> UserSessionList:
        """Get User Sessions for setting.

        GetUserSessions returns a list of user sessions.
        """
        path = "/api/web/namespaces/system/user/sessions"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UserSessionList(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "get_user_sessions", e, response) from e

    def get(
        self,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> UserSettingsResponse:
        """Get a setting by name.

        Retrieves current user settings object defined to the user.

        By default, excludes verbose fields (forms, references, system_metadata).
        Use include_all=True to get the complete response.

        Args:
            exclude: Additional field groups to exclude from response.
                - 'forms': Excludes create_form, replace_form
                - 'references': Excludes referring_objects, deleted/disabled_referred_objects
                - 'system_metadata': Excludes system_metadata
                You can also pass individual field names directly.
            include_all: If True, return all fields without default exclusions.
        """
        path = "/api/web/namespaces/system/user/settings"

        params: dict[str, Any] = {}

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

        # Apply default exclusions unless include_all=True
        if not include_all:
            default_exclude = ["forms", "references", "system_metadata"]
            exclude = (exclude or []) + default_exclude

        if exclude:
            exclude_fields = _resolve_exclude_groups(exclude)
            # Remove excluded fields entirely from response
            filtered_response = {
                k: v for k, v in response.items()
                if k not in exclude_fields
            }
        else:
            filtered_response = response

        try:
            return UserSettingsResponse(**filtered_response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "get", e, response) from e

    def update(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Update for setting.

        Update defined user settings.
        """
        path = "/api/web/namespaces/system/user/settings"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "update", e, response) from e

    def disable_user_in_idm(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Disable User In Idm for setting.

        Disables user in Identity.
        """
        path = "/api/web/namespaces/system/user/settings/idm/disable"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "disable_user_in_idm", e, response) from e

    def enable_user_in_idm(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Enable User In Idm for setting.

        Enables user in Identity. Use this to enable a user which is disabled.
        """
        path = "/api/web/namespaces/system/user/settings/idm/enable"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "enable_user_in_idm", e, response) from e

    def get_user_image(
        self,
    ) -> HttpBody:
        """Get User Image for setting.

        GetUserProfileImage returns user profile picture.
        """
        path = "/api/web/namespaces/system/user/settings/image"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "get_user_image", e, response) from e

    def update_user_image(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Update User Image for setting.

        Updates current user profile picture.
        """
        path = "/api/web/namespaces/system/user/settings/image"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "update_user_image", e, response) from e

    def delete_user_image(
        self,
    ) -> Empty:
        """Delete User Image for setting.

        Deletes current user profile picture.
        """
        path = "/api/web/namespaces/system/user/settings/image"


        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "delete_user_image", e, response) from e

    def request_initial_access(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Request Initial Access for setting.

        Request initial access requests initial access for user within...
        """
        path = "/api/web/namespaces/system/user/settings/request_initial_access"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "request_initial_access", e, response) from e

    def get_view_preference(
        self,
    ) -> ViewPreference:
        """Get View Preference for setting.

        Get view preference gets view preference for specific user.
        """
        path = "/api/web/namespaces/system/user/settings/view_preference"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ViewPreference(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "get_view_preference", e, response) from e

    def set_view_preference(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Set View Preference for setting.

        Set view preference sets view preference for specific user.
        """
        path = "/api/web/namespaces/system/user/settings/view_preference"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("setting", "set_view_preference", e, response) from e

