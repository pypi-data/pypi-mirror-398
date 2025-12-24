"""DeviceId resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.device_id.models import (
    ApplicationProvisionRequest,
    ApplicationProvisionResponse,
    DeleteApplicationsResponse,
    EnableRequest,
    EnableResponse,
    GetApplicationsResponse,
    GetBotAssessmentTopAsnRequest,
    GetBotAssessmentTopAsnResponse,
    GetBotAssessmentTopUrlsRequest,
    GetBotAssessmentTopUrlsResponse,
    GetBotAssessmentTransactionsRequest,
    GetBotAssessmentTransactionsResponse,
    GetDashboardByAgeRequest,
    GetDashboardByAgeResponse,
    GetDashboardByApplicationsRequest,
    GetDashboardByApplicationsResponse,
    GetDashboardByAsnRequest,
    GetDashboardByAsnResponse,
    GetDashboardByCountryRequest,
    GetDashboardByCountryResponse,
    GetDashboardBySessionRequest,
    GetDashboardBySessionResponse,
    GetDashboardByUaRequest,
    GetDashboardByUaResponse,
    GetDashboardUniqueAccessRequest,
    GetDashboardUniqueAccessResponse,
    GetRegionsResponse,
    GetStatusResponse,
    UpdateApplicationRequest,
    UpdateApplicationResponse,
    ValidateSrcTagInjectionRequest,
    ValidateSrcTagInjectionResponse,
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


class DeviceIdResource:
    """API methods for device_id.

    Use this API to interact with Application Traffic Insights...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.device_id.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def application_provision(
        self,
        body: dict[str, Any] | None = None,
    ) -> ApplicationProvisionResponse:
        """Application Provision for device_id.

        Provision an application for a tenant
        """
        path = "/api/shape/dip/namespaces/system/app_provision"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ApplicationProvisionResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "application_provision", e, response) from e

    def update_application(
        self,
        body: dict[str, Any] | None = None,
    ) -> UpdateApplicationResponse:
        """Update Application for device_id.

        Update an application's information
        """
        path = "/api/shape/dip/namespaces/system/application"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateApplicationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "update_application", e, response) from e

    def delete_application(
        self,
        app_id: str | None = None,
    ) -> DeleteApplicationsResponse:
        """Delete Application for device_id.

        Delete an application
        """
        path = "/api/shape/dip/namespaces/system/application"

        params: dict[str, Any] = {}
        if app_id is not None:
            params["app_id"] = app_id

        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeleteApplicationsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "delete_application", e, response) from e

    def get_applications(
        self,
    ) -> GetApplicationsResponse:
        """Get Applications for device_id.

        Get Applications Information
        """
        path = "/api/shape/dip/namespaces/system/applications"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetApplicationsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_applications", e, response) from e

    def get_bot_assessment_top_asn(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetBotAssessmentTopAsnResponse:
        """Get Bot Assessment Top Asn for device_id.

        Get Bot Top ASN Information
        """
        path = "/api/shape/dip/namespaces/system/bot/asn"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetBotAssessmentTopAsnResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_bot_assessment_top_asn", e, response) from e

    def get_bot_assessment_transactions(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetBotAssessmentTransactionsResponse:
        """Get Bot Assessment Transactions for device_id.

        Get Bot Transactions Information
        """
        path = "/api/shape/dip/namespaces/system/bot/transactions"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetBotAssessmentTransactionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_bot_assessment_transactions", e, response) from e

    def get_bot_assessment_top_urls(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetBotAssessmentTopUrlsResponse:
        """Get Bot Assessment Top Urls for device_id.

        Get Bot Top URL Information
        """
        path = "/api/shape/dip/namespaces/system/bot/urls"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetBotAssessmentTopUrlsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_bot_assessment_top_urls", e, response) from e

    def get_dashboard_by_age(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetDashboardByAgeResponse:
        """Get Dashboard By Age for device_id.

        Get device age information
        """
        path = "/api/shape/dip/namespaces/system/dashboard/age"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDashboardByAgeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_dashboard_by_age", e, response) from e

    def get_dashboard_by_applications(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetDashboardByApplicationsResponse:
        """Get Dashboard By Applications for device_id.

        Get device applications information
        """
        path = "/api/shape/dip/namespaces/system/dashboard/applications"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDashboardByApplicationsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_dashboard_by_applications", e, response) from e

    def get_dashboard_by_asn(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetDashboardByAsnResponse:
        """Get Dashboard By Asn for device_id.

        Get devices asn information
        """
        path = "/api/shape/dip/namespaces/system/dashboard/asn"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDashboardByAsnResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_dashboard_by_asn", e, response) from e

    def get_dashboard_by_country(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetDashboardByCountryResponse:
        """Get Dashboard By Country for device_id.

        Get devices country information
        """
        path = "/api/shape/dip/namespaces/system/dashboard/country"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDashboardByCountryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_dashboard_by_country", e, response) from e

    def get_dashboard_by_session(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetDashboardBySessionResponse:
        """Get Dashboard By Session for device_id.

        Get devices session information
        """
        path = "/api/shape/dip/namespaces/system/dashboard/session"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDashboardBySessionResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_dashboard_by_session", e, response) from e

    def get_dashboard_by_ua(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetDashboardByUaResponse:
        """Get Dashboard By Ua for device_id.

        Get devices user agent information
        """
        path = "/api/shape/dip/namespaces/system/dashboard/ua"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDashboardByUaResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_dashboard_by_ua", e, response) from e

    def get_dashboard_unique_access(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetDashboardUniqueAccessResponse:
        """Get Dashboard Unique Access for device_id.

        Get devices unique access information
        """
        path = "/api/shape/dip/namespaces/system/dashboard/unique"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDashboardUniqueAccessResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_dashboard_unique_access", e, response) from e

    def enable(
        self,
        body: dict[str, Any] | None = None,
    ) -> EnableResponse:
        """Enable for device_id.

        Enable Application Traffic Insights feature for the tenant
        """
        path = "/api/shape/dip/namespaces/system/enable"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EnableResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "enable", e, response) from e

    def get_regions(
        self,
    ) -> GetRegionsResponse:
        """Get Regions for device_id.

        Returns Application Traffic Insights regions information for the tenant
        """
        path = "/api/shape/dip/namespaces/system/provision/regions"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetRegionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_regions", e, response) from e

    def get_status(
        self,
    ) -> GetStatusResponse:
        """Get Status for device_id.

        Returns Application Traffic Insights information for the tenant
        """
        path = "/api/shape/dip/namespaces/system/status"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "get_status", e, response) from e

    def validate_src_tag_injection(
        self,
        body: dict[str, Any] | None = None,
    ) -> ValidateSrcTagInjectionResponse:
        """Validate Src Tag Injection for device_id.

        Validate js src tag injection in the target url
        """
        path = "/api/shape/dip/namespaces/system/validate/src_tag_injection"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ValidateSrcTagInjectionResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("device_id", "validate_src_tag_injection", e, response) from e

