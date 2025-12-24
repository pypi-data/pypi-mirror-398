"""ApiDefinition resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.api_definition.models import (
    ApiDefinitionListItem,
    ApiOperation,
    APInventoryResp,
    GlobalSpecType,
    ApiGroupSummary,
    ObjectCreateMetaType,
    Empty,
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
    GetReferencingAllLoadbalancersResp,
    GetReferencingLoadbalancersResp,
    ObjectRefType,
    ObjectReplaceMetaType,
    ReplaceSpecType,
    ReplaceRequest,
    ConditionType,
    StatusMetaType,
    StatusObject,
    GetResponse,
    ListAvailableAPIDefinitionsResp,
    ProtobufAny,
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


class ApiDefinitionResource:
    """API methods for api_definition.

    The api_definition construct provides a mechanism to create...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.api_definition.CreateSpecType(...)
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
        spec: ApiOperation | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new api_definition.

        x-required Create API Definition.

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
        path = "/api/config/namespaces/{metadata.namespace}/api_definitions"
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
            raise F5XCValidationError("api_definition", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: ApiOperation | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing api_definition.

        x-required Replace API Definition.

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
        path = "/api/config/namespaces/{metadata.namespace}/api_definitions/{metadata.name}"
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
            raise F5XCValidationError("api_definition", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[ApiDefinitionListItem]:
        """List api_definition resources in a namespace.

        List the set of api_definition in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/config/namespaces/{namespace}/api_definitions"
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
            return [ApiDefinitionListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("api_definition", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a api_definition by name.

        Get API Definition.

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
        path = "/api/config/namespaces/{namespace}/api_definitions/{name}"
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
            raise F5XCValidationError("api_definition", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a api_definition.

        Delete the specified api_definition

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/config/namespaces/{namespace}/api_definitions/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def get_referencing_http_loadbalancers(
        self,
        namespace: str,
        name: str,
    ) -> GetReferencingLoadbalancersResp:
        """Get Referencing Http Loadbalancers for api_definition.

        List Loadbalancer objects referenced by the API Definition...
        """
        path = "/api/config/namespaces/{namespace}/api_definitions/{name}/http_loadbalancers"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetReferencingLoadbalancersResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_definition", "get_referencing_http_loadbalancers", e, response) from e

    def get_referencing_loadbalancers(
        self,
        namespace: str,
        name: str,
    ) -> GetReferencingAllLoadbalancersResp:
        """Get Referencing Loadbalancers for api_definition.

        List Loadbalancers referenced by the API Definition (backrefrences).
        """
        path = "/api/config/namespaces/{namespace}/api_definitions/{name}/loadbalancers"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetReferencingAllLoadbalancersResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_definition", "get_referencing_loadbalancers", e, response) from e

    def mark_as_non_api(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> APInventoryResp:
        """Mark As Non Api for api_definition.

        Update the API Definition's non-API list with the provided API endpoints.
        """
        path = "/api/config/namespaces/{namespace}/api_definitions/{name}/mark_as_non_api"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APInventoryResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_definition", "mark_as_non_api", e, response) from e

    def move_to_ap_inventory(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> APInventoryResp:
        """Move To Ap Inventory for api_definition.

        Update the API Definition's include list with the provided API endpoints.
        """
        path = "/api/config/namespaces/{namespace}/api_definitions/{name}/move_to_inventory"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APInventoryResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_definition", "move_to_ap_inventory", e, response) from e

    def remove_from_ap_inventory(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> APInventoryResp:
        """Remove From Ap Inventory for api_definition.

        Update the API Definition's exclude list with the provided API endpoints.
        """
        path = "/api/config/namespaces/{namespace}/api_definitions/{name}/remove_from_inventory"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APInventoryResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_definition", "remove_from_ap_inventory", e, response) from e

    def unmark_as_non_api(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> APInventoryResp:
        """Unmark As Non Api for api_definition.

        Delete the provided API endpoints from the API Definition's non-API list.
        """
        path = "/api/config/namespaces/{namespace}/api_definitions/{name}/unmark_as_non_api"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APInventoryResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_definition", "unmark_as_non_api", e, response) from e

    def list_available_api_definitions(
        self,
        namespace: str,
    ) -> ListAvailableAPIDefinitionsResp:
        """List Available Api Definitions for api_definition.

        List API definitions suitable for API Inventory management Get all...
        """
        path = "/api/config/namespaces/{namespace}/api_definitions_without_shared"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListAvailableAPIDefinitionsResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_definition", "list_available_api_definitions", e, response) from e

