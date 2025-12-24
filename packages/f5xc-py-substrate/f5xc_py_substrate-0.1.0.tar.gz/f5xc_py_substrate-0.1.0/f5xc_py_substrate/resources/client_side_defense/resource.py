"""ClientSideDefense resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.client_side_defense.models import (
    AddToAllowedDomains,
    AddToMitigatedDomains,
    AffectedUser,
    AffectedUserDeviceIDFilter,
    AffectedUserGeolocationFilter,
    AffectedUserIPAddressFilter,
    AffectedUserFilters,
    Analysis,
    BehaviorByScript,
    DeleteScriptJustificationResponse,
    DeviceIDFilter,
    Location,
    DomainDetails,
    UpdatedCount,
    DomainSummary,
    EnterpriseInfo,
    Event,
    IPFilter,
    RiskLevelFilter,
    ScriptNameFilter,
    ScriptStatusFilter,
    Filters,
    FormField,
    FormFieldAnalysisFilter,
    FormFieldByScript,
    FormFieldNameFilter,
    FormFieldsFilters,
    GetDetectedDomainsResponse,
    GetDomainDetailsResponse,
    GetFormFieldResponse,
    GetJsInjectionConfigurationResponse,
    Summary,
    GetScriptOverviewResponse,
    GetStatusResponse,
    GetSummaryResponse,
    InitRequest,
    InitResponse,
    Justification,
    Sort,
    ListAffectedUsersRequest,
    ListAffectedUsersResponse,
    ListBehaviorsByScriptResponse,
    ListFormFieldsByScriptResponse,
    ListFormFieldsGetResponse,
    ListFormFieldsRequest,
    ListFormFieldsResponse,
    NetworkInteractionByScript,
    ListNetworkInteractionsByScriptResponse,
    ScriptInfo,
    ListScriptsLegacyResponse,
    ListScriptsRequest,
    ListScriptsResponse,
    TestJSRequest,
    TestJSResponse,
    UpdateDomainsRequest,
    UpdateDomainsResponse,
    UpdateFieldAnalysisRequest,
    UpdateFieldAnalysisResponse,
    UpdateScriptJustificationRequest,
    UpdateScriptJustificationResponse,
    UpdateScriptReadStatusRequest,
    UpdateScriptReadStatusResponse,
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


class ClientSideDefenseResource:
    """API methods for client_side_defense.

    Custom handler in Client-Side Defense microservice will forward...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.client_side_defense.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def init(
        self,
        body: dict[str, Any] | None = None,
    ) -> InitResponse:
        """Init for client_side_defense.

        Enable Client-Side Defense feature for the tenant
        """
        path = "/api/shape/csd/namespaces/system/init"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return InitResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "init", e, response) from e

    def get_detected_domains(
        self,
        namespace: str,
        duration: str | None = None,
        locations: str | None = None,
        risk: str | None = None,
    ) -> GetDetectedDomainsResponse:
        """Get Detected Domains for client_side_defense.

        Get the detected domains data for the tenant
        """
        path = "/api/shape/csd/namespaces/{namespace}/detected_domains"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if duration is not None:
            params["duration"] = duration
        if locations is not None:
            params["locations"] = locations
        if risk is not None:
            params["risk"] = risk

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDetectedDomainsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "get_detected_domains", e, response) from e

    def get_domain_details(
        self,
        namespace: str,
        name: str | None = None,
    ) -> GetDomainDetailsResponse:
        """Get Domain Details for client_side_defense.

        Get the details of the domain provided
        """
        path = "/api/shape/csd/namespaces/{namespace}/domain_details"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDomainDetailsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "get_domain_details", e, response) from e

    def list_form_fields_get(
        self,
        namespace: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> ListFormFieldsGetResponse:
        """List Form Fields Get for client_side_defense.

        List form fields for all the scripts depending on start time and end...
        """
        path = "/api/shape/csd/namespaces/{namespace}/formFields"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListFormFieldsGetResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "list_form_fields_get", e, response) from e

    def list_form_fields(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListFormFieldsResponse:
        """List Form Fields for client_side_defense.

        List form fields for all the scripts depending on start time and end time
        """
        path = "/api/shape/csd/namespaces/{namespace}/formFields"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListFormFieldsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "list_form_fields", e, response) from e

    def update_field_analysis(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateFieldAnalysisResponse:
        """Update Field Analysis for client_side_defense.

        Mark / unmark field sensitivity by customer
        """
        path = "/api/shape/csd/namespaces/{namespace}/formFields/analysis"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateFieldAnalysisResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "update_field_analysis", e, response) from e

    def get_form_field(
        self,
        namespace: str,
        id: str,
    ) -> GetFormFieldResponse:
        """Get Form Field for client_side_defense.

        Get form field for the name of the form field
        """
        path = "/api/shape/csd/namespaces/{namespace}/formFields/{id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{id}", id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetFormFieldResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "get_form_field", e, response) from e

    def get_js_injection_configuration(
        self,
        namespace: str,
        name: str | None = None,
    ) -> GetJsInjectionConfigurationResponse:
        """Get Js Injection Configuration for client_side_defense.

        Get JS Injection Configuration for this tenant
        """
        path = "/api/shape/csd/namespaces/{namespace}/js_configuration"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetJsInjectionConfigurationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "get_js_injection_configuration", e, response) from e

    def delete_script_justification(
        self,
        namespace: str,
        justification_id: str,
    ) -> DeleteScriptJustificationResponse:
        """Delete Script Justification for client_side_defense.

        Delete the specified script justification
        """
        path = "/api/shape/csd/namespaces/{namespace}/script/justification/{justification_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{justification_id}", justification_id)


        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeleteScriptJustificationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "delete_script_justification", e, response) from e

    def list_scripts_legacy(
        self,
        namespace: str,
        start_time: str | None = None,
        end_time: str | None = None,
        page_size: int | None = None,
        page_number: int | None = None,
        page_token: str | None = None,
    ) -> ListScriptsLegacyResponse:
        """List Scripts Legacy for client_side_defense.

        List all the scripts for the tenant depending on start time and end time
        """
        path = "/api/shape/csd/namespaces/{namespace}/scripts"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time
        if page_size is not None:
            params["page_size"] = page_size
        if page_number is not None:
            params["page_number"] = page_number
        if page_token is not None:
            params["page_token"] = page_token

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListScriptsLegacyResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "list_scripts_legacy", e, response) from e

    def list_scripts(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListScriptsResponse:
        """List Scripts for client_side_defense.

        List all the scripts for the tenant depending on start time and end time
        """
        path = "/api/shape/csd/namespaces/{namespace}/scripts"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListScriptsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "list_scripts", e, response) from e

    def list_behaviors_by_script(
        self,
        namespace: str,
        id: str,
        type_: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> ListBehaviorsByScriptResponse:
        """List Behaviors By Script for client_side_defense.

        List all the behaviors for a script depending on start time and end time
        """
        path = "/api/shape/csd/namespaces/{namespace}/scripts/{id}/behaviors"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if type_ is not None:
            params["type"] = type_
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListBehaviorsByScriptResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "list_behaviors_by_script", e, response) from e

    def get_script_overview(
        self,
        namespace: str,
        id: str,
        type_: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> GetScriptOverviewResponse:
        """Get Script Overview for client_side_defense.

        Get script overview data for a script depending on start time and end time
        """
        path = "/api/shape/csd/namespaces/{namespace}/scripts/{id}/dashboard"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if type_ is not None:
            params["type"] = type_
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetScriptOverviewResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "get_script_overview", e, response) from e

    def list_form_fields_by_script(
        self,
        namespace: str,
        id: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> ListFormFieldsByScriptResponse:
        """List Form Fields By Script for client_side_defense.

        List all the form fields for a script depending on start time and end time
        """
        path = "/api/shape/csd/namespaces/{namespace}/scripts/{id}/formFields"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListFormFieldsByScriptResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "list_form_fields_by_script", e, response) from e

    def list_network_interactions_by_script(
        self,
        namespace: str,
        id: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> ListNetworkInteractionsByScriptResponse:
        """List Network Interactions By Script for client_side_defense.

        List all the network interactions for a script depending on start...
        """
        path = "/api/shape/csd/namespaces/{namespace}/scripts/{id}/networkInteractions"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListNetworkInteractionsByScriptResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "list_network_interactions_by_script", e, response) from e

    def update_script_read_status(
        self,
        namespace: str,
        id: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateScriptReadStatusResponse:
        """Update Script Read Status for client_side_defense.

        Allow / block script from reading form fields
        """
        path = "/api/shape/csd/namespaces/{namespace}/scripts/{id}/readStatus"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{id}", id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateScriptReadStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "update_script_read_status", e, response) from e

    def list_affected_users(
        self,
        namespace: str,
        script_id: str,
        body: dict[str, Any] | None = None,
    ) -> ListAffectedUsersResponse:
        """List Affected Users for client_side_defense.

        List affected users who have loaded this particular script
        """
        path = "/api/shape/csd/namespaces/{namespace}/scripts/{script_id}/affectedUsers"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{script_id}", script_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListAffectedUsersResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "list_affected_users", e, response) from e

    def update_script_justification(
        self,
        namespace: str,
        script_id: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateScriptJustificationResponse:
        """Update Script Justification for client_side_defense.

        Update justification for script found
        """
        path = "/api/shape/csd/namespaces/{namespace}/scripts/{script_id}/justification"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{script_id}", script_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateScriptJustificationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "update_script_justification", e, response) from e

    def get_status(
        self,
        namespace: str,
    ) -> GetStatusResponse:
        """Get Status for client_side_defense.

        Get Client-Side Defense status for the tenant
        """
        path = "/api/shape/csd/namespaces/{namespace}/status"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "get_status", e, response) from e

    def get_summary(
        self,
        namespace: str,
    ) -> GetSummaryResponse:
        """Get Summary for client_side_defense.

        Get summay details for a given customer
        """
        path = "/api/shape/csd/namespaces/{namespace}/summary"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "get_summary", e, response) from e

    def test_js(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> TestJSResponse:
        """Test Js for client_side_defense.

        Validate JS script tag injection in the target url
        """
        path = "/api/shape/csd/namespaces/{namespace}/testjs"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TestJSResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "test_js", e, response) from e

    def update_domains(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateDomainsResponse:
        """Update Domains for client_side_defense.

        Update domain from mitigated domains to allowed domains and vice versa
        """
        path = "/api/shape/csd/namespaces/{namespace}/update_domains"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateDomainsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("client_side_defense", "update_domains", e, response) from e

