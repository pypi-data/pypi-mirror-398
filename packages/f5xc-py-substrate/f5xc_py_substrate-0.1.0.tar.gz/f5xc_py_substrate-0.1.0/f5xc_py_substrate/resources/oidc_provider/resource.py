"""OidcProvider resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.oidc_provider.models import (
    OidcProviderListItem,
    RecreateScimTokenRequest,
    AzureOIDCSpecType,
    DeleteResponse,
    GoogleOIDCSpecType,
    OIDCMappers,
    OIDCV10SpecType,
    OKTAOIDCSpecType,
    ReplaceResponse,
    ScimSpecType,
    UpdateOIDCMappersRequest,
    UpdateScimIntegrationRequest,
    ProtobufAny,
    ErrorType,
    CreateResponse,
    UpdateScimIntegrationResponse,
    InitializerType,
    StatusType,
    InitializersType,
    ObjectMetaType,
    ObjectRefType,
    ViewRefType,
    SystemObjectMetaType,
    CustomCreateSpecType,
    CreateRequest,
    CreateResponse,
    GlobalSpecType,
    SpecType,
    Object,
    GetResponse,
    ListResponseItem,
    ListResponse,
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


class OidcProviderResource:
    """API methods for oidc_provider.

    F5XC Identity supports identity brokering and third-party identity...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.oidc_provider.CreateSpecType(...)
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get(
        self,
        namespace: str,
        name: str,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a oidc_provider by name.

        Get implements oidc provider query by name. Returns oidc provider...

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
        path = "/api/web/custom/namespaces/{namespace}/oidc_provider/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

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
            return GetResponse(**filtered_response)
        except ValidationError as e:
            raise F5XCValidationError("oidc_provider", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a oidc_provider.

        Delete deletes oidc provider by name. This would also disable SCIM...

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/web/custom/namespaces/{namespace}/oidc_provider/{name}/delete"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def list(
        self,
        namespace: str,
    ) -> list[OidcProviderListItem]:
        """List oidc_provider resources in a namespace.

        List implements oidc provider query. Returns list of oidc provider...

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/web/custom/namespaces/{namespace}/oidc_providers"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

        items = response.get("items", [])
        errors = response.get("errors", [])

        if errors:
            raise F5XCPartialResultsError(items=items, errors=errors)

        try:
            return [OidcProviderListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("oidc_provider", "list", e, response) from e

    def create(
        self,
        namespace: str,
        name: str,
        spec: RecreateScimTokenRequest | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new oidc_provider.

        Create creates an OIDC provider in F5XC Identity. Currently we...

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
        path = "/api/web/custom/namespaces/{namespace}/oidc_providers"
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
            raise F5XCValidationError("oidc_provider", "create", e, response) from e

    def custom_get(
        self,
        namespace: str,
        name: str,
    ) -> GetResponse:
        """Custom Get for oidc_provider.

        Get implements oidc provider query by name. Returns oidc provider...
        """
        path = "/api/web/custom/namespaces/{namespace}/oidc_providers/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("oidc_provider", "custom_get", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: RecreateScimTokenRequest | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing oidc_provider.

        Replace updates OIDC provider parameters for a given provider...

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
        path = "/api/web/custom/namespaces/{namespace}/oidc_providers/{name}"
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
            raise F5XCValidationError("oidc_provider", "replace", e, response) from e

    def custom_replace(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> ReplaceResponse:
        """Custom Replace for oidc_provider.

        Replace updates OIDC provider parameters for a given provider...
        """
        path = "/api/web/custom/namespaces/{namespace}/oidc_providers/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReplaceResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("oidc_provider", "custom_replace", e, response) from e

    def custom_delete(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> DeleteResponse:
        """Custom Delete for oidc_provider.

        Delete deletes oidc provider by name. This would also disable SCIM...
        """
        path = "/api/web/custom/namespaces/{namespace}/oidc_providers/{name}/delete"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeleteResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("oidc_provider", "custom_delete", e, response) from e

    def get_oidc_mappers(
        self,
        namespace: str,
        name: str,
    ) -> OIDCMappers:
        """Get Oidc Mappers for oidc_provider.

        Get OIDC mappers gets OIDC mappers from underlying IDM provider.
        """
        path = "/api/web/custom/namespaces/{namespace}/oidc_providers/{name}/mappers"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return OIDCMappers(**response)
        except ValidationError as e:
            raise F5XCValidationError("oidc_provider", "get_oidc_mappers", e, response) from e

    def update_oidc_mappers(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update Oidc Mappers for oidc_provider.

        Update OIDC mappers updates OIDC mappers in underlying IDM provider.
        """
        path = "/api/web/custom/namespaces/{namespace}/oidc_providers/{name}/mappers"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        return response

    def update_scim_integration(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateScimIntegrationResponse:
        """Update Scim Integration for oidc_provider.

        Enables / Disables the SCIM integration for the OIDC provider.
        """
        path = "/api/web/custom/namespaces/{namespace}/oidc_providers/{name}/scim"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateScimIntegrationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("oidc_provider", "update_scim_integration", e, response) from e

