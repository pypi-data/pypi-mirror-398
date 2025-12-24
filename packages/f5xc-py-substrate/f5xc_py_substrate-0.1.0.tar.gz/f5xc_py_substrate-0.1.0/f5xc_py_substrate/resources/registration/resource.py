"""Registration resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.registration.models import (
    RegistrationListItem,
    Empty,
    ObjectRefType,
    StatusType,
    ProtobufAny,
    Passport,
    ApprovalReq,
    ConfigReq,
    ConfigResp,
    ObjectCreateMetaType,
    Bios,
    Board,
    Chassis,
    Cpu,
    GPUDevice,
    GPU,
    Kernel,
    Memory,
    NetworkDevice,
    OS,
    Product,
    StorageDevice,
    USBDevice,
    OsInfo,
    InternetProxy,
    SWInfo,
    Infra,
    CreateSpecType,
    CreateRequest,
    ObjectGetMetaType,
    GetSpecType,
    InitializerType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    CreateResponse,
    GetImageDownloadUrlReq,
    GetImageDownloadUrlResp,
    GetRegistrationsBySiteTokenReq,
    GetRegistrationsBySiteTokenResp,
    ObjectMetaType,
    GlobalSpecType,
    SpecType,
    StatusType,
    SystemObjectMetaType,
    Object,
    ObjectReplaceMetaType,
    ReplaceSpecType,
    ReplaceRequest,
    GetResponse,
    ErrorType,
    ListResponseItem,
    ListResponse,
    ListStateReq,
    ObjectChangeResp,
    CreateRequest,
    ReplaceResponse,
    SuggestValuesReq,
    ObjectRefType,
    SuggestedItem,
    SuggestValuesResp,
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


class RegistrationResource:
    """API methods for registration.

    registration API(s) are used by Customer edge site to register...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.registration.CreateSpecType(...)
    CreateSpecType = CreateSpecType
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
        """Create a new registration.

        VPM creates registration using this message, never used by users.

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
        path = "/api/register/namespaces/{metadata.namespace}/registrations"
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
            raise F5XCValidationError("registration", "create", e, response) from e

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
        """Replace an existing registration.

        NO fields are allowed to be replaced

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
        path = "/api/register/namespaces/{metadata.namespace}/registrations/{metadata.name}"
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
            raise F5XCValidationError("registration", "replace", e, response) from e

    def get_image_download_url(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetImageDownloadUrlResp:
        """Get Image Download Url for registration.

        Returns image download url for each provider
        """
        path = "/api/register/namespaces/system/get-image-download-url"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetImageDownloadUrlResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("registration", "get_image_download_url", e, response) from e

    def get_registrations_by_site_token(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetRegistrationsBySiteTokenResp:
        """Get Registrations By Site Token for registration.

        Returns list of registration uids that are using particular site token
        """
        path = "/api/register/namespaces/system/get-registrations-by-token"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetRegistrationsBySiteTokenResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("registration", "get_registrations_by_site_token", e, response) from e

    def suggest_values(
        self,
        body: dict[str, Any] | None = None,
    ) -> SuggestValuesResp:
        """Suggest Values for registration.

        Returns suggested values for the specified field in the given...
        """
        path = "/api/register/namespaces/system/suggest-values"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuggestValuesResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("registration", "suggest_values", e, response) from e

    def list_registrations_by_state(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ListResponse:
        """List Registrations By State for registration.

        API endpoint for returning Registrations by status, e.g APPROVED,...
        """
        path = "/api/register/namespaces/{namespace}/listregistrationsbystate"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("registration", "list_registrations_by_state", e, response) from e

    def registration_approve(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> ObjectChangeResp:
        """Registration Approve for registration.

        RegistrationApprove approved pending registration and it can also...
        """
        path = "/api/register/namespaces/{namespace}/registration/{name}/approve"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ObjectChangeResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("registration", "registration_approve", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[RegistrationListItem]:
        """List registration resources in a namespace.

        List the set of registration in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/register/namespaces/{namespace}/registrations"
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
            return [RegistrationListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("registration", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a registration by name.

        Get registration specification

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
        path = "/api/register/namespaces/{namespace}/registrations/{name}"
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
            raise F5XCValidationError("registration", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a registration.

        Delete the specified registration

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/register/namespaces/{namespace}/registrations/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def list_registrations_by_site(
        self,
        namespace: str,
        site_name: str,
    ) -> ListResponse:
        """List Registrations By Site for registration.

        List all registration in site
        """
        path = "/api/register/namespaces/{namespace}/registrations_by_site/{site_name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site_name}", site_name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("registration", "list_registrations_by_site", e, response) from e

    def registration_create(
        self,
        body: dict[str, Any] | None = None,
    ) -> Object:
        """Registration Create for registration.

        Registration request to create registration is sent by the node on...
        """
        path = "/api/register/registerBootstrap"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Object(**response)
        except ValidationError as e:
            raise F5XCValidationError("registration", "registration_create", e, response) from e

    def registration_config(
        self,
        body: dict[str, Any] | None = None,
    ) -> ConfigResp:
        """Registration Config for registration.

        API endpoint for returning configuration for admitted registrations....
        """
        path = "/api/register/requestConfig"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ConfigResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("registration", "registration_config", e, response) from e

