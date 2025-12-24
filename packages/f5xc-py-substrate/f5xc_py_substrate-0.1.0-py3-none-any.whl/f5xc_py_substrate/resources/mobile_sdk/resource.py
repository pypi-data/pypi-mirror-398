"""MobileSdk resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.mobile_sdk.models import (
    Empty,
    MobileAppShieldAttributes,
    MobileIntegratorAttributes,
    MobileSDKAttributes,
    StoredObjectDescriptor,
    PresignedUrlData,
    PreSignedUrl,
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


class MobileSdkResource:
    """API methods for mobile_sdk.

    
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.mobile_sdk.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list_mobile_sd_ks(
        self,
        namespace: str,
        object_type: str | None = None,
        name: str | None = None,
        query_type: str | None = None,
        latest_version_only: bool | None = None,
    ) -> ListObjectsResponse:
        """List Mobile Sd Ks for mobile_sdk.

        ListMobileSDKs is an API to list all mobile SDKs available for download.
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/mobile-sdk"
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
            raise F5XCValidationError("mobile_sdk", "list_mobile_sd_ks", e, response) from e

    def get_mobile_sdk(
        self,
        namespace: str,
        name: str,
        version: str,
        object_type: str | None = None,
    ) -> GetObjectResponse:
        """Get Mobile Sdk for mobile_sdk.

        GetMobileSDK is an API to download particular version of SDK
        """
        path = "/api/object_store/namespaces/{namespace}/stored_objects/mobile-sdk/{name}/{version}"
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
            raise F5XCValidationError("mobile_sdk", "get_mobile_sdk", e, response) from e

