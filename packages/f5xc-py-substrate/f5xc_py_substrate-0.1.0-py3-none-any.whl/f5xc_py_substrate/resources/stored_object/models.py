"""Pydantic models for stored_object."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class MobileAppShieldAttributes(F5XCBaseModel):
    """Describes attributes specific to object type - mobile-app-shield"""

    os_type: Optional[Literal['ANDROID', 'IOS']] = None
    release_version: Optional[str] = None


class MobileIntegratorAttributes(F5XCBaseModel):
    """Describes attributes specific to object type - mobile-integrator"""

    os_type: Optional[Literal['ANDROID', 'IOS']] = None
    release_version: Optional[str] = None


class MobileSDKAttributes(F5XCBaseModel):
    """Describes attributes specific to object type - mobile-sdk"""

    os_type: Optional[Literal['ANDROID', 'IOS']] = None
    release_version: Optional[str] = None


class CreateObjectRequest(F5XCBaseModel):
    """Request message for CreateObject API"""

    bytes_value: Optional[str] = None
    content_format: Optional[str] = None
    description: Optional[str] = None
    mobile_app_shield: Optional[MobileAppShieldAttributes] = None
    mobile_integrator: Optional[MobileIntegratorAttributes] = None
    mobile_sdk: Optional[MobileSDKAttributes] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    no_attributes: Optional[Any] = None
    object_type: Optional[str] = None
    string_value: Optional[str] = None


class Descriptor(F5XCBaseModel):
    """Response for Get, Create APIs"""

    creation_timestamp: Optional[str] = None
    description: Optional[str] = None
    mobile_app_shield: Optional[MobileAppShieldAttributes] = None
    mobile_integrator: Optional[MobileIntegratorAttributes] = None
    mobile_sdk: Optional[MobileSDKAttributes] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    no_attributes: Optional[Any] = None
    url: Optional[str] = None
    version: Optional[str] = None


class PresignedUrlData(F5XCBaseModel):
    """Pre signed url data"""

    method: Optional[Literal['ANY', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH', 'COPY']] = None
    url: Optional[str] = None


class PreSignedUrl(F5XCBaseModel):
    """Pre signed url"""

    aws: Optional[PresignedUrlData] = None


class CreateObjectResponse(F5XCBaseModel):
    """Response message for CreateObject API"""

    metadata: Optional[Descriptor] = None
    no_additional_info: Optional[Any] = None
    presigned_url: Optional[PreSignedUrl] = None
    status: Optional[Literal['STORED_OBJECT_STATUS_NONE', 'STORED_OBJECT_STATUS_CREATED', 'STORED_OBJECT_STATUS_UPDATED', 'STORED_OBJECT_STATUS_ALREADY_EXISTS']] = None


class DeleteObjectResponse(F5XCBaseModel):
    """Response for DeleteObjects API"""

    deleted_objects: Optional[list[str]] = None


class GetObjectResponse(F5XCBaseModel):
    """Response message for GetObject API"""

    bytes_value: Optional[str] = None
    content_format: Optional[str] = None
    metadata: Optional[Descriptor] = None
    presigned_url: Optional[PreSignedUrl] = None
    string_value: Optional[str] = None


class VersionDescriptor(F5XCBaseModel):
    """Descriptor for store object version."""

    creation_timestamp: Optional[str] = None
    description: Optional[str] = None
    latest_version: Optional[bool] = None
    url: Optional[str] = None
    version: Optional[str] = None


class ListItemDescriptor(F5XCBaseModel):
    """A descriptor for list response item."""

    mobile_app_shield: Optional[MobileAppShieldAttributes] = None
    mobile_integrator: Optional[MobileIntegratorAttributes] = None
    mobile_sdk: Optional[MobileSDKAttributes] = None
    name: Optional[str] = None
    no_attributes: Optional[Any] = None
    tenant: Optional[str] = None
    versions: Optional[list[VersionDescriptor]] = None


class ListObjectsResponse(F5XCBaseModel):
    """Response for GetListOfObjects API"""

    items: Optional[list[ListItemDescriptor]] = None


# Convenience aliases
