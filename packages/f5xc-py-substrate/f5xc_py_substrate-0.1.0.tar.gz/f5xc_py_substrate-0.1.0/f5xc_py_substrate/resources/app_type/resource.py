"""AppType resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.app_type.models import (
    AppTypeListItem,
    ProtobufAny,
    HttpBody,
    APIEPDynExample,
    AuthenticationTypeLocPair,
    PDFSpec,
    PDFStat,
    APIEPPDFInfo,
    RiskScore,
    APIEPInfo,
    APIEndpointLearntSchemaReq,
    SchemaStruct,
    RequestSchema,
    DiscoveredSchema,
    SensitiveData,
    APIEndpointLearntSchemaRsp,
    APIEndpointPDFRsp,
    APIEndpointsRsp,
    Empty,
    DiscoveredAPISettings,
    BusinessLogicMarkupSetting,
    ObjectCreateMetaType,
    Feature,
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
    DeleteRequest,
    ObjectRefType,
    ObjectReplaceMetaType,
    ReplaceSpecType,
    ReplaceRequest,
    ConditionType,
    StatusMetaType,
    StatusObject,
    GetResponse,
    ErrorType,
    ListResponseItem,
    ListResponse,
    OverrideInfo,
    OverridePopReq,
    OverridePopRsp,
    OverridePushReq,
    OverridePushRsp,
    OverridesRsp,
    ReplaceResponse,
    ServiceAPIEndpointPDFReq,
    ServiceAPIEndpointsReq,
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


class AppTypeResource:
    """API methods for app_type.

    App Type object defines a application profile type from an advanced...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.app_type.CreateSpecType(...)
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
        spec: ProtobufAny | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new app_type.

        Create App type will create the configuration in namespace metadata.namespace

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
        path = "/api/config/namespaces/{metadata.namespace}/app_types"
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
            raise F5XCValidationError("app_type", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: ProtobufAny | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing app_type.

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
        path = "/api/config/namespaces/{metadata.namespace}/app_types/{metadata.name}"
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
            raise F5XCValidationError("app_type", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[AppTypeListItem]:
        """List app_type resources in a namespace.

        List the set of app_type in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/config/namespaces/{namespace}/app_types"
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
            return [AppTypeListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("app_type", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a app_type by name.

        Get App type will read the configuration from namespace metadata.namespace

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
        path = "/api/config/namespaces/{namespace}/app_types/{name}"
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
            raise F5XCValidationError("app_type", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a app_type.

        Delete the specified app_type

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/config/namespaces/{namespace}/app_types/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def get_api_endpoint_learnt_schema(
        self,
        namespace: str,
        app_type_name: str,
        body: dict[str, Any] | None = None,
    ) -> APIEndpointLearntSchemaRsp:
        """Get Api Endpoint Learnt Schema for app_type.

        Get Learnt Schema per API endpoint for a given auto discovered API...
        """
        path = "/api/ml/data/namespaces/{namespace}/app_types/{app_type_name}/api_endpoint/learnt_schema"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{app_type_name}", app_type_name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APIEndpointLearntSchemaRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_type", "get_api_endpoint_learnt_schema", e, response) from e

    def api_endpoint_pdf(
        self,
        namespace: str,
        app_type_name: str,
        collapsed_url: str | None = None,
        method: str | None = None,
    ) -> APIEndpointPDFRsp:
        """Api Endpoint Pdf for app_type.

        Get PDF of all metrics for a given auto discovered API endpoint for App type
        """
        path = "/api/ml/data/namespaces/{namespace}/app_types/{app_type_name}/api_endpoint/pdf"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{app_type_name}", app_type_name)

        params: dict[str, Any] = {}
        if collapsed_url is not None:
            params["collapsed_url"] = collapsed_url
        if method is not None:
            params["method"] = method

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APIEndpointPDFRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_type", "api_endpoint_pdf", e, response) from e

    def api_endpoints(
        self,
        namespace: str,
        app_type_name: str,
        api_endpoint_info_request: list | None = None,
    ) -> APIEndpointsRsp:
        """Api Endpoints for app_type.

        Get all auto discovered API endpoints for App type
        """
        path = "/api/ml/data/namespaces/{namespace}/app_types/{app_type_name}/api_endpoints"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{app_type_name}", app_type_name)

        params: dict[str, Any] = {}
        if api_endpoint_info_request is not None:
            params["api_endpoint_info_request"] = api_endpoint_info_request

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APIEndpointsRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_type", "api_endpoints", e, response) from e

    def get_swagger_spec(
        self,
        namespace: str,
        app_type_name: str,
    ) -> HttpBody:
        """Get Swagger Spec for app_type.

        Get the corresponding Swagger spec for the given app type
        """
        path = "/api/ml/data/namespaces/{namespace}/app_types/{app_type_name}/api_endpoints/swagger_spec"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{app_type_name}", app_type_name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_type", "get_swagger_spec", e, response) from e

    def override_pop(
        self,
        namespace: str,
        app_type_name: str,
        body: dict[str, Any] | None = None,
    ) -> OverridePopRsp:
        """Override Pop for app_type.

        remove override for dynamic component for API endpoints discovered...
        """
        path = "/api/ml/data/namespaces/{namespace}/app_types/{app_type_name}/override/pop"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{app_type_name}", app_type_name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return OverridePopRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_type", "override_pop", e, response) from e

    def override_push(
        self,
        namespace: str,
        app_type_name: str,
        body: dict[str, Any] | None = None,
    ) -> OverridePushRsp:
        """Override Push for app_type.

        Add override for dynamic component for API endpoints discovered for...
        """
        path = "/api/ml/data/namespaces/{namespace}/app_types/{app_type_name}/override/push"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{app_type_name}", app_type_name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return OverridePushRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_type", "override_push", e, response) from e

    def overrides(
        self,
        namespace: str,
        app_type_name: str,
    ) -> OverridesRsp:
        """Overrides for app_type.

        Get all override for API endpoints configured for this App type
        """
        path = "/api/ml/data/namespaces/{namespace}/app_types/{app_type_name}/overrides"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{app_type_name}", app_type_name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return OverridesRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_type", "overrides", e, response) from e

    def get_service_api_endpoint_pdf(
        self,
        namespace: str,
        app_type_name: str,
        service_name: str,
        body: dict[str, Any] | None = None,
    ) -> APIEndpointPDFRsp:
        """Get Service Api Endpoint Pdf for app_type.

        Get PDF of all metrics for a given auto discovered API endpoint for Service
        """
        path = "/api/ml/data/namespaces/{namespace}/app_types/{app_type_name}/services/{service_name}/api_endpoint/pdf"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{app_type_name}", app_type_name)
        path = path.replace("{service_name}", service_name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APIEndpointPDFRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_type", "get_service_api_endpoint_pdf", e, response) from e

    def get_service_api_endpoints(
        self,
        namespace: str,
        app_type_name: str,
        service_name: str,
        body: dict[str, Any] | None = None,
    ) -> APIEndpointsRsp:
        """Get Service Api Endpoints for app_type.

        Get all autodiscovered API endpoints for Service
        """
        path = "/api/ml/data/namespaces/{namespace}/app_types/{app_type_name}/services/{service_name}/api_endpoints"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{app_type_name}", app_type_name)
        path = path.replace("{service_name}", service_name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APIEndpointsRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("app_type", "get_service_api_endpoints", e, response) from e

