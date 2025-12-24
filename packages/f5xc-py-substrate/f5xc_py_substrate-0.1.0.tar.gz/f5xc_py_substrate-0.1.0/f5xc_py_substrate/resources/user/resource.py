"""User resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.user.models import (
    UserListItem,
    Empty,
    ProtobufAny,
    ErrorType,
    InitializerType,
    StatusType,
    InitializersType,
    NamespaceAccessType,
    NamespaceRoleType,
    ObjectMetaType,
    ObjectRefType,
    ViewRefType,
    SystemObjectMetaType,
    Empty,
    AcceptTOSRequest,
    AcceptTOSResponse,
    NamespacesRoleType,
    AssignRoleRequest,
    BillingFeatureIndicator,
    CascadeDeleteItemType,
    CascadeDeleteRequest,
    CascadeDeleteResponse,
    FeatureFlagType,
    GetTOSResponse,
    MSPManaged,
    GetUserRoleResponse,
    GlobalSpecType,
    ListUserRoleResponseItem,
    ListUserRoleResponse,
    SpecType,
    Object,
    ResetPasswordByAdminRequest,
    SendPasswordEmailRequest,
    SendPasswordEmailResponse,
    GroupResponse,
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


class UserResource:
    """API methods for user.

    This API can be used to manage various attributes of the user...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.user.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def sync_user(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Sync User for user.

        In case when user created initially from identity provider we need...
        """
        path = "/api/web/custom/idm/user/sync"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "sync_user", e, response) from e

    def add_user_to_group(
        self,
        body: dict[str, Any] | None = None,
    ) -> GroupResponse:
        """Add User To Group for user.

        Assign existing user to specific groups.
        """
        path = "/api/web/custom/namespaces/system/users/group_add"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GroupResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "add_user_to_group", e, response) from e

    def remove_user_from_group(
        self,
        body: dict[str, Any] | None = None,
    ) -> GroupResponse:
        """Remove User From Group for user.

        remove existing user from specific groups.
        """
        path = "/api/web/custom/namespaces/system/users/group_remove"


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GroupResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "remove_user_from_group", e, response) from e

    def accept_tos(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> AcceptTOSResponse:
        """Accept Tos for user.

        Accept TOS updates version of accepted terms of service.
        """
        path = "/api/web/custom/namespaces/{namespace}/accept_tos"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AcceptTOSResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "accept_tos", e, response) from e

    def assign_role(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Assign Role for user.

        AssignRole allows customers to assign a namespace/role pair to multiple users
        """
        path = "/api/web/custom/namespaces/{namespace}/role_users"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "assign_role", e, response) from e

    def send_password_email(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SendPasswordEmailResponse:
        """Send Password Email for user.

        SendPasswordEmail allows admin user to trigger send password email...
        """
        path = "/api/web/custom/namespaces/{namespace}/send_password_email"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SendPasswordEmailResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "send_password_email", e, response) from e

    def get_tos(
        self,
        namespace: str,
    ) -> GetTOSResponse:
        """Get Tos for user.

        Get TOS provides TOS version with text
        """
        path = "/api/web/custom/namespaces/{namespace}/tos"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTOSResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "get_tos", e, response) from e

    def list(
        self,
        namespace: str,
    ) -> list[UserListItem]:
        """List user resources in a namespace.

        List enumerates users and their namespace roles for this tenant

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/web/custom/namespaces/{namespace}/user_roles"
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
            return [UserListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("user", "list", e, response) from e

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
    ) -> Object:
        """Create a new user.

        Create creates a user and namespace roles binding for this user

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
        path = "/api/web/custom/namespaces/{namespace}/user_roles"
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
            return Object(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "create", e, response) from e

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
    ) -> Object:
        """Replace an existing user.

        Replace updates user and namespace roles for this user

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
        path = "/api/web/custom/namespaces/{namespace}/user_roles"
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
            return Object(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "replace", e, response) from e

    def custom_replace(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> Object:
        """Custom Replace for user.

        Replace updates user and namespace roles for this user
        """
        path = "/api/web/custom/namespaces/{namespace}/user_roles/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Object(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "custom_replace", e, response) from e

    def cascade_delete(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> CascadeDeleteResponse:
        """Cascade Delete for user.

        CascadeDelete deletes the user and associated namespace roles for...
        """
        path = "/api/web/custom/namespaces/{namespace}/users/cascade_delete"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CascadeDeleteResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "cascade_delete", e, response) from e

    def get(
        self,
        namespace: str,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetUserRoleResponse:
        """Get a user by name.

        Get fetches user information based on the username header from the...

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
        path = "/api/web/custom/namespaces/{namespace}/whoami"
        path = path.replace("{namespace}", namespace)

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
            return GetUserRoleResponse(**filtered_response)
        except ValidationError as e:
            raise F5XCValidationError("user", "get", e, response) from e

    def reset_password_by_admin(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Reset Password By Admin for user.

        Reset password by admin resets password for a user specified in...
        """
        path = "/api/web/custom/password/admin_reset"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "reset_password_by_admin", e, response) from e

    def reset_password(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Reset Password for user.

        Reset password resets password for user who is making this request.
        """
        path = "/api/web/custom/password/reset"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("user", "reset_password", e, response) from e

