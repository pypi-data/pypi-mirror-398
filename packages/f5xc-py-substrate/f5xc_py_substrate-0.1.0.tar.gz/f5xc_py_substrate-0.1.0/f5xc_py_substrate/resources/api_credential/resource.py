"""ApiCredential resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.api_credential.models import (
    ApiCredentialListItem,
    ApiCertificateType,
    BulkRevokeResponse,
    CustomCreateSpecType,
    CreateRequest,
    CreateResponse,
    Empty,
    NamespaceRoleType,
    SiteKubeconfigType,
    Vk8sKubeconfigType,
    CreateServiceCredentialsRequest,
    ObjectMetaType,
    ObjectRefType,
    GlobalSpecType,
    SpecType,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectMetaType,
    Object,
    GetResponse,
    NamespaceAccessType,
    GetServiceCredentialsResponse,
    ListResponseItem,
    ListResponse,
    ListServiceCredentialsResponseItem,
    ListServiceCredentialsResponse,
    RecreateScimTokenRequest,
    ReplaceServiceCredentialsRequest,
    ReplaceServiceCredentialsResponse,
    ScimTokenRequest,
    StatusResponse,
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


class ApiCredentialResource:
    """API methods for api_credential.

    F5XC supports 2 variation of credentials - 
1. My Credentials or API...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.api_credential.CreateSpecType(...)
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def bulk_revoke(
        self,
        body: dict[str, Any] | None = None,
    ) -> BulkRevokeResponse:
        """Bulk Revoke for api_credential.

        It is used to revoke multiple API credentials. This API would...
        """
        path = "/api/web/namespaces/system/bulk_revoke/api_credentials"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return BulkRevokeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "bulk_revoke", e, response) from e

    def bulk_revoke_service_credentials(
        self,
        body: dict[str, Any] | None = None,
    ) -> BulkRevokeResponse:
        """Bulk Revoke Service Credentials for api_credential.

        It is used to revoke multiple service credentials. This API would...
        """
        path = "/api/web/namespaces/system/bulk_revoke/service_credentials"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return BulkRevokeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "bulk_revoke_service_credentials", e, response) from e

    def activate(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> StatusResponse:
        """Activate for api_credential.

        For API credential activation/deactivation.
        """
        path = "/api/web/namespaces/{namespace}/activate/api_credentials"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "activate", e, response) from e

    def activate_service_credentials(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> StatusResponse:
        """Activate Service Credentials for api_credential.

        For Service credential activation/deactivation.
        """
        path = "/api/web/namespaces/{namespace}/activate/service_credentials"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "activate_service_credentials", e, response) from e

    def list(
        self,
        namespace: str,
    ) -> list[ApiCredentialListItem]:
        """List api_credential resources in a namespace.

        Returns list of api credential of all types created by the user....

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/web/namespaces/{namespace}/api_credentials"
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
            return [ApiCredentialListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "list", e, response) from e

    def create(
        self,
        namespace: str,
        name: str,
        spec: ApiCertificateType | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new api_credential.

        user can request 3 types of credential for themselves.  API_TOKEN,...

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
        path = "/api/web/namespaces/{namespace}/api_credentials"
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
            raise F5XCValidationError("api_credential", "create", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a api_credential by name.

        Get implements api credential query by name. Returns api credential...

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
        path = "/api/web/namespaces/{namespace}/api_credentials/{name}"
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
            raise F5XCValidationError("api_credential", "get", e, response) from e

    def renew(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> StatusResponse:
        """Renew for api_credential.

        Renew user's my credential expiry. Renewal is only supported for the...
        """
        path = "/api/web/namespaces/{namespace}/renew/api_credentials"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "renew", e, response) from e

    def renew_service_credentials(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> StatusResponse:
        """Renew Service Credentials for api_credential.

        Renew service credential's expiry. Renewal is only supported for the...
        """
        path = "/api/web/namespaces/{namespace}/renew/service_credentials"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "renew_service_credentials", e, response) from e

    def revoke(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> StatusResponse:
        """Revoke for api_credential.

        For API credential revoke/deletion.
        """
        path = "/api/web/namespaces/{namespace}/revoke/api_credentials"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "revoke", e, response) from e

    def revoke_scim_token(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> StatusResponse:
        """Revoke Scim Token for api_credential.

        For SCIM API credential revoke/deletion.
        """
        path = "/api/web/namespaces/{namespace}/revoke/scim_token"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "revoke_scim_token", e, response) from e

    def revoke_service_credentials(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> StatusResponse:
        """Revoke Service Credentials for api_credential.

        For Service credential revoke/deletion.
        """
        path = "/api/web/namespaces/{namespace}/revoke/service_credentials"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "revoke_service_credentials", e, response) from e

    def get_scim_token(
        self,
        namespace: str,
    ) -> GetResponse:
        """Get Scim Token for api_credential.

        GetScimToken implements querying of scim token. SCIM API token value...
        """
        path = "/api/web/namespaces/{namespace}/scim_token"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "get_scim_token", e, response) from e

    def recreate_scim_token(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> CreateResponse:
        """Recreate Scim Token for api_credential.

        request to create/re-create new SCIM API credential. Note: Only one...
        """
        path = "/api/web/namespaces/{namespace}/scim_token"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreateResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "recreate_scim_token", e, response) from e

    def list_service_credentials(
        self,
        namespace: str,
    ) -> ListServiceCredentialsResponse:
        """List Service Credentials for api_credential.

        request to list service credentials created by user.
        """
        path = "/api/web/namespaces/{namespace}/service_credentials"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListServiceCredentialsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "list_service_credentials", e, response) from e

    def create_service_credentials(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> CreateResponse:
        """Create Service Credentials for api_credential.

        request to create new service credentials. user can specify name,...
        """
        path = "/api/web/namespaces/{namespace}/service_credentials"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreateResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "create_service_credentials", e, response) from e

    def get_service_credentials(
        self,
        namespace: str,
        name: str,
    ) -> GetServiceCredentialsResponse:
        """Get Service Credentials for api_credential.

        Get implements service credential query by name. Returns service...
        """
        path = "/api/web/namespaces/{namespace}/service_credentials/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetServiceCredentialsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "get_service_credentials", e, response) from e

    def replace_service_credentials(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> ReplaceServiceCredentialsResponse:
        """Replace Service Credentials for api_credential.

        request to replace user_groups and roles in service credentials....
        """
        path = "/api/web/namespaces/{namespace}/service_credentials/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReplaceServiceCredentialsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("api_credential", "replace_service_credentials", e, response) from e

