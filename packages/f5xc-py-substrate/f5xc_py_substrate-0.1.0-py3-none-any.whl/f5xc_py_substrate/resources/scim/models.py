"""Pydantic models for scim."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class HttpBody(F5XCBaseModel):
    """Message that represents an arbitrary HTTP body. It should only be used..."""

    content_type: Optional[str] = None
    data: Optional[str] = None
    extensions: Optional[list[ProtobufAny]] = None


class GroupMembers(F5XCBaseModel):
    """GroupMembers."""

    ref: Optional[str] = None
    value: Optional[str] = None


class Meta(F5XCBaseModel):
    """x-example: 'Meta' x-required Resource meta information.."""

    created: Optional[str] = None
    last_modified: Optional[str] = Field(default=None, alias="lastModified")
    location: Optional[str] = None
    resource_type: Optional[str] = Field(default=None, alias="resourceType")
    version: Optional[str] = None


class CreateGroupRequest(F5XCBaseModel):
    """Request for creating group."""

    display_name: Optional[str] = Field(default=None, alias="displayName")
    external_id: Optional[str] = Field(default=None, alias="externalId")
    id_: Optional[str] = Field(default=None, alias="id")
    members: Optional[list[GroupMembers]] = None
    meta: Optional[Meta] = None
    schemas: Optional[list[str]] = None


class Email(F5XCBaseModel):
    """Email for user can be primary or secondary"""

    primary: Optional[bool] = None
    type_: Optional[str] = Field(default=None, alias="type")
    value: Optional[str] = None


class UserGroup(F5XCBaseModel):
    """UserGroup."""

    display: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")


class Name(F5XCBaseModel):
    """Name is the name of user."""

    family_name: Optional[str] = Field(default=None, alias="familyName")
    formatted: Optional[str] = None
    given_name: Optional[str] = Field(default=None, alias="givenName")
    honorific_prefix: Optional[str] = Field(default=None, alias="honorificPrefix")
    honorific_suffix: Optional[str] = Field(default=None, alias="honorificSuffix")
    middle_name: Optional[str] = Field(default=None, alias="middleName")


class CreateUserRequest(F5XCBaseModel):
    """CreateUserRequest is the request for creating a user."""

    active: Optional[bool] = None
    display_name: Optional[str] = Field(default=None, alias="displayName")
    emails: Optional[list[Email]] = None
    external_id: Optional[str] = Field(default=None, alias="externalId")
    groups: Optional[list[UserGroup]] = None
    meta: Optional[Meta] = None
    name: Optional[Name] = None
    roles: Optional[list[str]] = None
    schemas: Optional[list[str]] = None
    user_name: Optional[str] = Field(default=None, alias="userName")
    user_type: Optional[Literal['USER', 'SERVICE', 'DEBUG']] = Field(default=None, alias="userType")


class Filter(F5XCBaseModel):
    """Filter."""

    max_results: Optional[str] = Field(default=None, alias="maxResults")
    supported: Optional[bool] = None


class Group(F5XCBaseModel):
    """Group."""

    display_name: Optional[str] = Field(default=None, alias="displayName")
    external_id: Optional[str] = Field(default=None, alias="externalId")
    id_: Optional[str] = Field(default=None, alias="id")
    members: Optional[list[GroupMembers]] = None
    meta: Optional[Meta] = None
    name: Optional[str] = None
    schemas: Optional[list[str]] = None


class ListGroupResources(F5XCBaseModel):
    """List group objects."""

    resources: Optional[list[Group]] = Field(default=None, alias="Resources")
    items_per_page: Optional[str] = Field(default=None, alias="itemsPerPage")
    schemas: Optional[list[str]] = None
    start_index: Optional[str] = Field(default=None, alias="startIndex")
    total_results: Optional[str] = Field(default=None, alias="totalResults")


class User(F5XCBaseModel):
    """User object representing the user created."""

    active: Optional[bool] = None
    display_name: Optional[str] = Field(default=None, alias="displayName")
    emails: Optional[list[Email]] = None
    external_id: Optional[str] = Field(default=None, alias="externalId")
    groups: Optional[list[UserGroup]] = None
    id_: Optional[str] = Field(default=None, alias="id")
    meta: Optional[Meta] = None
    name: Optional[Name] = None
    nick_name: Optional[str] = Field(default=None, alias="nickName")
    roles: Optional[list[str]] = None
    schemas: Optional[list[str]] = None
    user_name: Optional[str] = Field(default=None, alias="userName")
    user_type: Optional[Literal['USER', 'SERVICE', 'DEBUG']] = Field(default=None, alias="userType")


class ListUserResponse(F5XCBaseModel):
    """ListUserResources list all the user objects."""

    resources: Optional[list[User]] = Field(default=None, alias="Resources")
    items_per_page: Optional[str] = Field(default=None, alias="itemsPerPage")
    schemas: Optional[list[str]] = None
    start_index: Optional[str] = Field(default=None, alias="startIndex")
    total_results: Optional[str] = Field(default=None, alias="totalResults")


class PatchOperation(F5XCBaseModel):
    """PatchOperation is the patch operation where user can be  updated..."""

    op: Optional[str] = None
    path: Optional[str] = None
    value: Optional[dict[str, Any]] = None


class PatchGroupRequest(F5XCBaseModel):
    """Patch operation to modify group."""

    operations: Optional[list[PatchOperation]] = Field(default=None, alias="Operations")
    id_: Optional[str] = Field(default=None, alias="id")
    schemas: Optional[list[str]] = None


class PatchUserRequest(F5XCBaseModel):
    """x-example: {     'schemas': [        ..."""

    operations: Optional[list[PatchOperation]] = Field(default=None, alias="Operations")
    id_: Optional[str] = Field(default=None, alias="id")
    schemas: Optional[list[str]] = None


class ResourceMeta(F5XCBaseModel):
    """ResourceMeta."""

    location: Optional[str] = None
    resource_type: Optional[str] = Field(default=None, alias="resourceType")


class Resource(F5XCBaseModel):
    """Resource"""

    endpoint: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    meta: Optional[ResourceMeta] = None
    name: Optional[str] = None
    schema_: Optional[str] = Field(default=None, alias="schema")
    schemas: Optional[list[str]] = None


class ResourceTypesResponse(F5XCBaseModel):
    """ResourceTypesResponse"""

    detail: Optional[str] = None
    resources: Optional[list[Resource]] = None
    schemas: Optional[list[str]] = None
    status: Optional[str] = None
    total_results: Optional[str] = Field(default=None, alias="totalResults")


class Support(F5XCBaseModel):
    """Support."""

    supported: Optional[bool] = None


class ServiceProviderConfigResponse(F5XCBaseModel):
    """ServiceProviderConfigResponse."""

    authentication_schemes: Optional[list[str]] = Field(default=None, alias="authenticationSchemes")
    bulk: Optional[Support] = None
    change_password: Optional[Support] = Field(default=None, alias="changePassword")
    documentation_uri: Optional[str] = Field(default=None, alias="documentationUri")
    etag: Optional[Support] = None
    filter: Optional[Filter] = None
    patch: Optional[Support] = None
    schemas: Optional[list[str]] = None
    sort: Optional[Support] = None


# Convenience aliases
