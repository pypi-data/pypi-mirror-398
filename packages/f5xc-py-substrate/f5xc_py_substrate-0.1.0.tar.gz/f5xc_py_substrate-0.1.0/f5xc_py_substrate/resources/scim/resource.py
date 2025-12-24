"""Scim resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.scim.models import (
    ProtobufAny,
    HttpBody,
    GroupMembers,
    Meta,
    CreateGroupRequest,
    Email,
    UserGroup,
    Name,
    CreateUserRequest,
    Filter,
    Group,
    ListGroupResources,
    User,
    ListUserResponse,
    PatchOperation,
    PatchGroupRequest,
    PatchUserRequest,
    ResourceMeta,
    Resource,
    ResourceTypesResponse,
    Support,
    ServiceProviderConfigResponse,
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


class ScimResource:
    """API methods for scim.

    This schema specification details Volterra's support for SCIM...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.scim.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list_groups(
        self,
        filter: str | None = None,
        count: str | None = None,
        page: str | None = None,
        excluded_attributes: list | None = None,
    ) -> ListGroupResources:
        """List Groups for scim.

        List groups based on the given filter.
        """
        path = "/api/scim/namespaces/system/v2/Groups"

        params: dict[str, Any] = {}
        if filter is not None:
            params["filter"] = filter
        if count is not None:
            params["count"] = count
        if page is not None:
            params["page"] = page
        if excluded_attributes is not None:
            params["excludedAttributes"] = excluded_attributes

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListGroupResources(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "list_groups", e, response) from e

    def create_group(
        self,
        body: dict[str, Any] | None = None,
    ) -> Group:
        """Create Group for scim.

        Create group with given users.
        """
        path = "/api/scim/namespaces/system/v2/Groups"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Group(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "create_group", e, response) from e

    def get_group_by_id(
        self,
        id: str,
        excluded_attributes: list | None = None,
    ) -> Group:
        """Get Group By Id for scim.

        List group based on the given Id.
        """
        path = "/api/scim/namespaces/system/v2/Groups/{id}"
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if excluded_attributes is not None:
            params["excludedAttributes"] = excluded_attributes

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Group(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "get_group_by_id", e, response) from e

    def replace_group_by_id(
        self,
        id: str,
        body: dict[str, Any] | None = None,
    ) -> Group:
        """Replace Group By Id for scim.

        Replace group based on the given Id.
        """
        path = "/api/scim/namespaces/system/v2/Groups/{id}"
        path = path.replace("{id}", id)


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Group(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "replace_group_by_id", e, response) from e

    def delete_group_by_id(
        self,
        id: str,
        excluded_attributes: list | None = None,
    ) -> HttpBody:
        """Delete Group By Id for scim.

        Delete group based on the given Id.
        """
        path = "/api/scim/namespaces/system/v2/Groups/{id}"
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if excluded_attributes is not None:
            params["excludedAttributes"] = excluded_attributes

        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "delete_group_by_id", e, response) from e

    def patch_group_by_id(
        self,
        id: str,
        body: dict[str, Any] | None = None,
    ) -> Group:
        """Patch Group By Id for scim.

        Patch group based on the given Id.
        """
        path = "/api/scim/namespaces/system/v2/Groups/{id}"
        path = path.replace("{id}", id)


        try:
            response = self._http.patch(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Group(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "patch_group_by_id", e, response) from e

    def list_resource_types(
        self,
    ) -> ResourceTypesResponse:
        """List Resource Types for scim.

        
        """
        path = "/api/scim/namespaces/system/v2/ResourceTypes"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ResourceTypesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "list_resource_types", e, response) from e

    def get_resource_types_by_id(
        self,
        id: str,
        excluded_attributes: list | None = None,
    ) -> Resource:
        """Get Resource Types By Id for scim.

        
        """
        path = "/api/scim/namespaces/system/v2/ResourceTypes/{id}"
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if excluded_attributes is not None:
            params["excludedAttributes"] = excluded_attributes

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Resource(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "get_resource_types_by_id", e, response) from e

    def list_schemas(
        self,
    ) -> HttpBody:
        """List Schemas for scim.

        
        """
        path = "/api/scim/namespaces/system/v2/Schemas"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "list_schemas", e, response) from e

    def get_schema_by_id(
        self,
        id: str,
        excluded_attributes: list | None = None,
    ) -> HttpBody:
        """Get Schema By Id for scim.

        
        """
        path = "/api/scim/namespaces/system/v2/Schemas/{id}"
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if excluded_attributes is not None:
            params["excludedAttributes"] = excluded_attributes

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "get_schema_by_id", e, response) from e

    def list_service_provider_config(
        self,
    ) -> ServiceProviderConfigResponse:
        """List Service Provider Config for scim.

        
        """
        path = "/api/scim/namespaces/system/v2/ServiceProviderConfig"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ServiceProviderConfigResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "list_service_provider_config", e, response) from e

    def list_users(
        self,
        filter: str | None = None,
        count: str | None = None,
        page: str | None = None,
        excluded_attributes: list | None = None,
    ) -> ListUserResponse:
        """List Users for scim.

        Get all users.
        """
        path = "/api/scim/namespaces/system/v2/Users"

        params: dict[str, Any] = {}
        if filter is not None:
            params["filter"] = filter
        if count is not None:
            params["count"] = count
        if page is not None:
            params["page"] = page
        if excluded_attributes is not None:
            params["excludedAttributes"] = excluded_attributes

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListUserResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "list_users", e, response) from e

    def create_user(
        self,
        body: dict[str, Any] | None = None,
    ) -> User:
        """Create User for scim.

        Create creates a user and namespace roles binding for this user
        """
        path = "/api/scim/namespaces/system/v2/Users"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return User(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "create_user", e, response) from e

    def get_user_by_id(
        self,
        id: str,
        excluded_attributes: list | None = None,
    ) -> User:
        """Get User By Id for scim.

        Get user by means of ID
        """
        path = "/api/scim/namespaces/system/v2/Users/{id}"
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if excluded_attributes is not None:
            params["excludedAttributes"] = excluded_attributes

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return User(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "get_user_by_id", e, response) from e

    def replace_user_by_id(
        self,
        id: str,
        body: dict[str, Any] | None = None,
    ) -> User:
        """Replace User By Id for scim.

        Replace updates user and namespace roles for this user
        """
        path = "/api/scim/namespaces/system/v2/Users/{id}"
        path = path.replace("{id}", id)


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return User(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "replace_user_by_id", e, response) from e

    def delete_user_by_id(
        self,
        id: str,
        excluded_attributes: list | None = None,
    ) -> HttpBody:
        """Delete User By Id for scim.

        Delete user by Id.
        """
        path = "/api/scim/namespaces/system/v2/Users/{id}"
        path = path.replace("{id}", id)

        params: dict[str, Any] = {}
        if excluded_attributes is not None:
            params["excludedAttributes"] = excluded_attributes

        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "delete_user_by_id", e, response) from e

    def patch_user_by_id(
        self,
        id: str,
        body: dict[str, Any] | None = None,
    ) -> User:
        """Patch User By Id for scim.

        Patch patches the fields for this user
        """
        path = "/api/scim/namespaces/system/v2/Users/{id}"
        path = path.replace("{id}", id)


        try:
            response = self._http.patch(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return User(**response)
        except ValidationError as e:
            raise F5XCValidationError("scim", "patch_user_by_id", e, response) from e

