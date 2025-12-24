"""ReportConfig resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.report_config.models import (
    ReportConfigListItem,
    Empty,
    ObjectRefType,
    ProtobufAny,
    TrendValue,
    WaapReportFieldData,
    WaapReportFieldDataList,
    AttackImpactData,
    AttackImpact,
    AttackSourcesData,
    AttackSources,
    ProtectedLBCount,
    ReportDataATB,
    ReportHeader,
    SecurityEventsData,
    SecurityEvents,
    ThreatDetailsData,
    ThreatDetails,
    ReportDataWAAP,
    ReportDeliveryStatus,
    ReportGenerationStatus,
    ObjectCreateMetaType,
    ObjectRefType,
    ReportRecipients,
    ReportFreqDaily,
    ReportFreqMonthly,
    Namespaces,
    ReportFreqWeekly,
    ReportTypeWaap,
    CreateSpecType,
    CreateRequest,
    ObjectGetMetaType,
    GetSpecType,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    CreateResponse,
    GetSpecType,
    ObjectMetaType,
    GlobalSpecType,
    SpecType,
    SystemObjectMetaType,
    Object,
    CustomAPIListResponseItem,
    DeleteRequest,
    GenerateReportRequest,
    GenerateReportResponse,
    ObjectReplaceMetaType,
    ReplaceSpecType,
    ReplaceRequest,
    ConditionType,
    StatusMetaType,
    StatusObject,
    GetResponse,
    ListReportsHistoryResponseItem,
    ListReportsHistoryResponse,
    ErrorType,
    ListResponseItem,
    ListResponse,
    ReplaceResponse,
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


class ReportConfigResource:
    """API methods for report_config.

    Report configuration contains the information like

    List of...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.report_config.CreateSpecType(...)
    CreateSpecType = CreateSpecType
    GetSpecType = GetSpecType
    GetSpecType = GetSpecType
    ReplaceSpecType = ReplaceSpecType
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        namespace: str,
        name: str,
        spec: Empty | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new report_config.

        Report configuration is used to schedule report generation at a...

        Args:
            namespace: The namespace to create the resource in.
            name: The name of the resource.
            spec: The resource specification (typed model).
            body: Raw JSON body (alternative to spec, for advanced use).
            labels: Optional labels for the resource.
            annotations: Optional annotations for the resource.
            description: Optional description.
            disable: Whether to create the resource in disabled state.
        """
        path = "/api/report/namespaces/{metadata.namespace}/report_configs"
        path = path.replace("{metadata.namespace}", namespace)

        if body is not None:
            request_body = body
        else:
            request_body: dict[str, Any] = {
                "metadata": {
                    "name": name,
                    "namespace": namespace,
                },
            }
            if labels:
                request_body["metadata"]["labels"] = labels
            if annotations:
                request_body["metadata"]["annotations"] = annotations
            if description:
                request_body["metadata"]["description"] = description
            if disable is not None:
                request_body["metadata"]["disable"] = disable
            # Always include spec - API requires it even if empty
            if spec is not None:
                request_body["spec"] = spec.model_dump(by_alias=True, exclude_none=True)
            else:
                request_body["spec"] = {}

        try:
            response = self._http.post(path, json=request_body)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreateResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("report_config", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: Empty | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing report_config.

        Update the configuration by replacing the existing spec with the...

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to replace.
            spec: The new resource specification (typed model).
            body: Raw JSON body (alternative to spec, for advanced use).
            labels: Optional labels for the resource.
            annotations: Optional annotations for the resource.
            description: Optional description.
            disable: Whether to disable the resource.
        """
        path = "/api/report/namespaces/{metadata.namespace}/report_configs/{metadata.name}"
        path = path.replace("{metadata.namespace}", namespace)
        path = path.replace("{metadata.name}", name)

        if body is not None:
            request_body = body
        else:
            request_body: dict[str, Any] = {
                "metadata": {
                    "name": name,
                    "namespace": namespace,
                },
            }
            if labels:
                request_body["metadata"]["labels"] = labels
            if annotations:
                request_body["metadata"]["annotations"] = annotations
            if description:
                request_body["metadata"]["description"] = description
            if disable is not None:
                request_body["metadata"]["disable"] = disable
            # Always include spec - API requires it even if empty
            if spec is not None:
                request_body["spec"] = spec.model_dump(by_alias=True, exclude_none=True)
            else:
                request_body["spec"] = {}

        try:
            response = self._http.put(path, json=request_body)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReplaceResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("report_config", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[ReportConfigListItem]:
        """List report_config resources in a namespace.

        List the set of report_config in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/report/namespaces/{namespace}/report_configs"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if label_filter is not None:
            params["label_filter"] = label_filter
        if report_fields is not None:
            params["report_fields"] = report_fields
        if report_status_fields is not None:
            params["report_status_fields"] = report_status_fields

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

        items = response.get("items", [])
        errors = response.get("errors", [])

        if errors:
            raise F5XCPartialResultsError(items=items, errors=errors)

        try:
            return [ReportConfigListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("report_config", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a report_config by name.

        Get Report Configuration will read the configuration

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
        path = "/api/report/namespaces/{namespace}/report_configs/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if response_format is not None:
            params["response_format"] = response_format

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
            return GetResponse(**filtered_response)
        except ValidationError as e:
            raise F5XCValidationError("report_config", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a report_config.

        Delete the specified report_config

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/report/namespaces/{namespace}/report_configs/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def list_reports_history(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListReportsHistoryResponse:
        """List Reports History for report_config.

        List Reports history for the list of report configurations in the...
        """
        path = "/api/report/namespaces/{namespace}/report_configs/list-reports-history"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListReportsHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("report_config", "list_reports_history", e, response) from e

    def list_reports_history_bot_defence(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListReportsHistoryResponse:
        """List Reports History Bot Defence for report_config.

        List Reports history bot defence for the list of report...
        """
        path = "/api/report/namespaces/{namespace}/report_configs/list-reports-history-bot-defence"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListReportsHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("report_config", "list_reports_history_bot_defence", e, response) from e

    def list_reports_history_waap(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListReportsHistoryResponse:
        """List Reports History Waap for report_config.

        List Reports history waap for the list of report configurations in...
        """
        path = "/api/report/namespaces/{namespace}/report_configs/list-reports-history-waap"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListReportsHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("report_config", "list_reports_history_waap", e, response) from e

    def generate_report(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GenerateReportResponse:
        """Generate Report for report_config.

        Generate report now
        """
        path = "/api/report/namespaces/{namespace}/report_configs/{name}/generate"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GenerateReportResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("report_config", "generate_report", e, response) from e

