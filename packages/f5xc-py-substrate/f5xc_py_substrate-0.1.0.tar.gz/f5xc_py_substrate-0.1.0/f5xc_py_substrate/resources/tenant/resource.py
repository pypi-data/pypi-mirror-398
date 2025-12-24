"""Tenant resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.tenant.models import (
    ProtobufAny,
    HttpBody,
    Empty,
    AssignDomainOwnerRequest,
    CredentialsExpiry,
    DeactivateTenantRequest,
    DeactivateTenantResponse,
    DeleteTenantRequest,
    GetLoginEventsInTimeFrameRequest,
    LastLoginMap,
    LoginEventsMap,
    PasswordPolicyPublicAccess,
    StatusResponse,
    SummaryResponse,
    SupportInfo,
    SettingsResponse,
    UnassignDomainOwnerRequest,
    UpdateImageRequest,
    UpdateTenantSettingsRequest,
    ValidationErrorField,
    UpdateTenantSettingsResponse,
    User,
    UserList,
    BasicConfiguration,
    BruteForceDetectionSettings,
    PasswordPolicy,
    GlobalSpecType,
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


class TenantResource:
    """API methods for tenant.

    Package for working with Tenant representation.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.tenant.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def lookup_cname(
        self,
        cname: str | None = None,
        namespace: str | None = None,
    ) -> StatusResponse:
        """Lookup Cname for tenant.

        Checks if a cname is available.
        """
        path = "/no_auth/cname/lookup"

        params: dict[str, Any] = {}
        if cname is not None:
            params["cname"] = cname
        if namespace is not None:
            params["namespace"] = namespace

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "lookup_cname", e, response) from e

    def get_password_policy(
        self,
        realm_id: str | None = None,
    ) -> PasswordPolicyPublicAccess:
        """Get Password Policy for tenant.

        GetPasswordPolicy returns password policy for tenant.
        """
        path = "/no_auth/tenant/idm/settings/password_policy"

        params: dict[str, Any] = {}
        if realm_id is not None:
            params["realm_id"] = realm_id

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PasswordPolicyPublicAccess(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_password_policy", e, response) from e

    def assign_domain_owner(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Assign Domain Owner for tenant.

        Assign domain owner tries to assign domain owner to user in the...
        """
        path = "/api/web/namespaces/system/tenant/domain_owner/assign"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "assign_domain_owner", e, response) from e

    def unassign_domain_owner(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Unassign Domain Owner for tenant.

        Unassign domain owner tries to remove domain owner privilege from...
        """
        path = "/api/web/namespaces/system/tenant/domain_owner/unassign"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "unassign_domain_owner", e, response) from e

    def get_last_login_map(
        self,
    ) -> LastLoginMap:
        """Get Last Login Map for tenant.

        GetLastLoginMap returns last login timestamp for each user within a tenant.
        """
        path = "/api/web/namespaces/system/tenant/idm/events/last_login"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LastLoginMap(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_last_login_map", e, response) from e

    def get_login_events(
        self,
        first: int | None = None,
        max: int | None = None,
    ) -> LoginEventsMap:
        """Get Login Events for tenant.

        GetLoginEvents returns login events for specified in config period...
        """
        path = "/api/web/namespaces/system/tenant/idm/events/login"

        params: dict[str, Any] = {}
        if first is not None:
            params["first"] = first
        if max is not None:
            params["max"] = max

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LoginEventsMap(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_login_events", e, response) from e

    def get_login_events_in_time_frame(
        self,
        body: dict[str, Any] | None = None,
    ) -> LoginEventsMap:
        """Get Login Events In Time Frame for tenant.

        GetLoginEventsInTimeFrame returns login events for specified period...
        """
        path = "/api/web/namespaces/system/tenant/idm/events/login_in_time"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LoginEventsMap(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_login_events_in_time_frame", e, response) from e

    def get_idm_settings(
        self,
    ) -> GlobalSpecType:
        """Get Idm Settings for tenant.

        GetIDMSettings returns IDM settings for tenant. IDM settings...
        """
        path = "/api/web/namespaces/system/tenant/idm/settings"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GlobalSpecType(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_idm_settings", e, response) from e

    def update_idm_settings(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Update Idm Settings for tenant.

        UpdateIDMSettings allows to adjust IDM settings for tenant, like...
        """
        path = "/api/web/namespaces/system/tenant/idm/settings"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "update_idm_settings", e, response) from e

    def list_inactive_users(
        self,
    ) -> UserList:
        """List Inactive Users for tenant.

        Returns list of users for which no login events was found for last...
        """
        path = "/api/web/namespaces/system/tenant/idm/users/inactive"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UserList(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "list_inactive_users", e, response) from e

    def custom_lookup_cname(
        self,
        cname: str | None = None,
        namespace: str | None = None,
    ) -> StatusResponse:
        """Custom Lookup Cname for tenant.

        Checks if a cname is available.
        """
        path = "/api/web/namespaces/system/tenant/lookup"

        params: dict[str, Any] = {}
        if cname is not None:
            params["cname"] = cname
        if namespace is not None:
            params["namespace"] = namespace

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "custom_lookup_cname", e, response) from e

    def delete_tenant(
        self,
        body: dict[str, Any] | None = None,
    ) -> StatusResponse:
        """Delete Tenant for tenant.

        Request to mark Tenant for deletion queue, after approve it will...
        """
        path = "/api/web/namespaces/system/tenant/request-delete"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "delete_tenant", e, response) from e

    def get_tenant_settings(
        self,
    ) -> SettingsResponse:
        """Get Tenant Settings for tenant.

        Receive current tenant settings.
        """
        path = "/api/web/namespaces/system/tenant/settings"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SettingsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_tenant_settings", e, response) from e

    def update_tenant_settings(
        self,
        body: dict[str, Any] | None = None,
    ) -> UpdateTenantSettingsResponse:
        """Update Tenant Settings for tenant.

        Tenant settings
        """
        path = "/api/web/namespaces/system/tenant/settings"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateTenantSettingsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "update_tenant_settings", e, response) from e

    def disable_tenant_level_otp(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Disable Tenant Level Otp for tenant.

        Disable tenant level OTP disables OTP on tenant-level. After it's...
        """
        path = "/api/web/namespaces/system/tenant/settings/otp/disable"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "disable_tenant_level_otp", e, response) from e

    def enable_tenant_level_otp(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Enable Tenant Level Otp for tenant.

        Enable tenant level OTP enables OTP on tenant-level. It enforces...
        """
        path = "/api/web/namespaces/system/tenant/settings/otp/enable"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "enable_tenant_level_otp", e, response) from e

    def get_fav_icon(
        self,
    ) -> HttpBody:
        """Get Fav Icon for tenant.

        Receive current tenant favicon.
        """
        path = "/api/web/namespaces/system/tenant/settings/tenant/favicon"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_fav_icon", e, response) from e

    def get_image(
        self,
    ) -> HttpBody:
        """Get Image for tenant.

        Receive current tenant profile image.
        """
        path = "/api/web/namespaces/system/tenant/settings/tenant/image"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_image", e, response) from e

    def update_image(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Update Image for tenant.

        Uploads new profile image for the tenant entity.
        """
        path = "/api/web/namespaces/system/tenant/settings/tenant/image"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "update_image", e, response) from e

    def delete_image(
        self,
    ) -> Empty:
        """Delete Image for tenant.

        Delete profile image for the tenant entity.
        """
        path = "/api/web/namespaces/system/tenant/settings/tenant/image"


        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "delete_image", e, response) from e

    def get_logo(
        self,
    ) -> HttpBody:
        """Get Logo for tenant.

        Receive current tenant logo.
        """
        path = "/api/web/namespaces/system/tenant/settings/tenant/logo"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_logo", e, response) from e

    def get_support_info(
        self,
    ) -> SupportInfo:
        """Get Support Info for tenant.

        Receive support information for tenant
        """
        path = "/api/web/namespaces/system/tenant/support-info"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SupportInfo(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_support_info", e, response) from e

    def get_tenant_escalation_doc(
        self,
    ) -> HttpBody:
        """Get Tenant Escalation Doc for tenant.

        Receive current tenant escalation document.
        """
        path = "/api/web/namespaces/system/tenant/tenant-escalation-doc"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "get_tenant_escalation_doc", e, response) from e

    def deactivate_tenant(
        self,
        body: dict[str, Any] | None = None,
    ) -> DeactivateTenantResponse:
        """Deactivate Tenant for tenant.

        This API mark tenant for deletion queue, after approve it will...
        """
        path = "/api/saas/namespaces/system/v2/tenant/deactivate"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeactivateTenantResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "deactivate_tenant", e, response) from e

    def custom_get_fav_icon(
        self,
    ) -> HttpBody:
        """Custom Get Fav Icon for tenant.

        Receive current tenant favicon.
        """
        path = "/api/web/static/namespaces/system/tenant/settings/tenant/favicon"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "custom_get_fav_icon", e, response) from e

    def custom_get_image(
        self,
    ) -> HttpBody:
        """Custom Get Image for tenant.

        Receive current tenant profile image.
        """
        path = "/api/web/static/namespaces/system/tenant/settings/tenant/image"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "custom_get_image", e, response) from e

    def summary(
        self,
        tenant: str,
    ) -> SummaryResponse:
        """Summary for tenant.

        This API returns tenant summary
        """
        path = "/api/config/tenants/{tenant}/summary"
        path = path.replace("{tenant}", tenant)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tenant", "summary", e, response) from e

