"""StoredObject resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.stored_object.models import (
    Empty,
    MobileAppShieldAttributes,
    MobileIntegratorAttributes,
    MobileSDKAttributes,
    CreateObjectRequest,
    Descriptor,
    PresignedUrlData,
    PreSignedUrl,
    CreateObjectResponse,
    DeleteObjectResponse,
    GetObjectResponse,
    VersionDescriptor,
    ListItemDescriptor,
    ListObjectsResponse,
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


class StoredObjectResource:
    """API methods for stored_object.

    
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.stored_object.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list_mobile_app_shields(
        self,
        namespace: str,
        object_type: str | None = None,
        name: str | None = None,
        query_type: str | None = None,
        latest_version_only: bool | None = None,
    ) -> ListObjectsResponse:
        """List Mobile App Shields for stored_object.

        ListMobileAppShields is an API to list all mobile app shields...
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/mobile-app-shield"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if object_type is not None:
            params["object_type"] = object_type
        if name is not None:
            params["name"] = name
        if query_type is not None:
            params["query_type"] = query_type
        if latest_version_only is not None:
            params["latest_version_only"] = latest_version_only

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListObjectsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("stored_object", "list_mobile_app_shields", e, response) from e

    def get_mobile_app_shield(
        self,
        namespace: str,
        name: str,
        version: str,
        object_type: str | None = None,
    ) -> GetObjectResponse:
        """Get Mobile App Shield for stored_object.

        GetMobileAppShield is an API to download particular version of...
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/mobile-app-shield/{name}/{version}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)
        path = path.replace("{version}", version)

        params: dict[str, Any] = {}
        if object_type is not None:
            params["object_type"] = object_type

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetObjectResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("stored_object", "get_mobile_app_shield", e, response) from e

    def list_mobile_integrators(
        self,
        namespace: str,
        object_type: str | None = None,
        name: str | None = None,
        query_type: str | None = None,
        latest_version_only: bool | None = None,
    ) -> ListObjectsResponse:
        """List Mobile Integrators for stored_object.

        ListMobileIntegrators is an API to list all mobile integrators...
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/mobile-integrator"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if object_type is not None:
            params["object_type"] = object_type
        if name is not None:
            params["name"] = name
        if query_type is not None:
            params["query_type"] = query_type
        if latest_version_only is not None:
            params["latest_version_only"] = latest_version_only

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListObjectsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("stored_object", "list_mobile_integrators", e, response) from e

    def get_mobile_integrator(
        self,
        namespace: str,
        name: str,
        version: str,
        object_type: str | None = None,
    ) -> GetObjectResponse:
        """Get Mobile Integrator for stored_object.

        GetMobileIntegrator is an API to download particular version of Integrator
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/mobile-integrator/{name}/{version}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)
        path = path.replace("{version}", version)

        params: dict[str, Any] = {}
        if object_type is not None:
            params["object_type"] = object_type

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetObjectResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("stored_object", "get_mobile_integrator", e, response) from e

    def list_objects(
        self,
        namespace: str,
        object_type: str,
        name: str | None = None,
        query_type: str | None = None,
        latest_version_only: bool | None = None,
    ) -> ListObjectsResponse:
        """List Objects for stored_object.

        ListObjects is an API to list objects in object store
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/{object_type}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{object_type}", object_type)

        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if query_type is not None:
            params["query_type"] = query_type
        if latest_version_only is not None:
            params["latest_version_only"] = latest_version_only

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListObjectsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("stored_object", "list_objects", e, response) from e

    def create_object(
        self,
        namespace: str,
        object_type: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> CreateObjectResponse:
        """Create Object for stored_object.

        CreateObject is an API to upload an object to generic object store....
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/{object_type}/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{object_type}", object_type)
        path = path.replace("{name}", name)


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreateObjectResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("stored_object", "create_object", e, response) from e

    def delete_object(
        self,
        namespace: str,
        object_type: str,
        name: str,
        version: str | None = None,
        force_delete: bool | None = None,
    ) -> DeleteObjectResponse:
        """Delete Object for stored_object.

        DeleteObjects is an API to delete object(s) in object store
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/{object_type}/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{object_type}", object_type)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if version is not None:
            params["version"] = version
        if force_delete is not None:
            params["force_delete"] = force_delete

        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeleteObjectResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("stored_object", "delete_object", e, response) from e

    def get_object(
        self,
        namespace: str,
        object_type: str,
        name: str,
        version: str,
    ) -> GetObjectResponse:
        """Get Object for stored_object.

        GetObject is an API to download an object from object store
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/{object_type}/{name}/{version}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{object_type}", object_type)
        path = path.replace("{name}", name)
        path = path.replace("{version}", version)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetObjectResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("stored_object", "get_object", e, response) from e

    def custom_delete_object(
        self,
        namespace: str,
        object_type: str,
        name: str,
        version: str,
        force_delete: bool | None = None,
    ) -> DeleteObjectResponse:
        """Custom Delete Object for stored_object.

        DeleteObjects is an API to delete object(s) in object store
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/{object_type}/{name}/{version}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{object_type}", object_type)
        path = path.replace("{name}", name)
        path = path.replace("{version}", version)

        params: dict[str, Any] = {}
        if force_delete is not None:
            params["force_delete"] = force_delete

        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeleteObjectResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("stored_object", "custom_delete_object", e, response) from e

