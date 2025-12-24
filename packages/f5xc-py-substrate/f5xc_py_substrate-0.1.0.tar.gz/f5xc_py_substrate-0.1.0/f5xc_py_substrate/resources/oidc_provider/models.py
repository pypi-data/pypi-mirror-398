"""Pydantic models for oidc_provider."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class OidcProviderListItem(F5XCBaseModel):
    """List item for oidc_provider resources."""


class RecreateScimTokenRequest(F5XCBaseModel):
    """RecreateScimTokenRequest is the request format for generating SCIM api..."""

    expiration_days: Optional[int] = None
    namespace: Optional[str] = None


class AzureOIDCSpecType(F5XCBaseModel):
    """AzureOIDCSpecType specifies the attributes required to configure Azure provider"""

    authorization_url: Optional[str] = None
    backchannel_logout: Optional[bool] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    default_scopes: Optional[str] = None
    issuer: Optional[str] = None
    jwks_url: Optional[str] = None
    logout_url: Optional[str] = None
    prompt: Optional[Literal['UNSPECIFIED', 'NONE', 'CONSENT', 'LOGIN', 'SELECT_ACCOUNT']] = None
    token_url: Optional[str] = None
    user_info_url: Optional[str] = None


class DeleteResponse(F5XCBaseModel):
    """Shape of delete response for OIDC provider delete request."""

    err: Optional[Literal['EUNKNOWN', 'EOK', 'EEXISTS', 'EFAILED', 'ENOTFOUND']] = None


class GoogleOIDCSpecType(F5XCBaseModel):
    """GoogleOIDCSpecType specifies the attributes required to configure google provider"""

    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    hosted_domain: Optional[str] = None


class OIDCMappers(F5XCBaseModel):
    """When 3rd party OIDC provider uses non-standard field names, user..."""

    email: Optional[str] = None


class OIDCV10SpecType(F5XCBaseModel):
    """OIDCV10SpecType specifies the attributes required to configure OIDC provider"""

    allowed_clock_skew: Optional[str] = None
    authorization_url: Optional[str] = None
    backchannel_logout: Optional[bool] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    default_scopes: Optional[str] = None
    disable_user_info: Optional[bool] = None
    display_name: Optional[str] = None
    forwarded_query_parameters: Optional[str] = None
    issuer: Optional[str] = None
    jwks_url: Optional[str] = None
    logout_url: Optional[str] = None
    pass_current_locale: Optional[bool] = None
    pass_login_hint: Optional[bool] = None
    prompt: Optional[Literal['UNSPECIFIED', 'NONE', 'CONSENT', 'LOGIN', 'SELECT_ACCOUNT']] = None
    token_url: Optional[str] = None
    user_info_url: Optional[str] = None
    validate_signatures: Optional[bool] = None


class OKTAOIDCSpecType(F5XCBaseModel):
    """OKTAOIDCSpecType specifies the attributes required to configure okta..."""

    authorization_url: Optional[str] = None
    backchannel_logout: Optional[bool] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    default_scopes: Optional[str] = None
    issuer: Optional[str] = None
    jwks_url: Optional[str] = None
    logout_url: Optional[str] = None
    prompt: Optional[Literal['UNSPECIFIED', 'NONE', 'CONSENT', 'LOGIN', 'SELECT_ACCOUNT']] = None
    token_url: Optional[str] = None
    user_info_url: Optional[str] = None


class ReplaceResponse(F5XCBaseModel):
    """ReplaceResponse is the response format for replacing an oidc provider in..."""

    err: Optional[Literal['EUNKNOWN', 'EOK', 'EEXISTS', 'EFAILED', 'ENOTFOUND']] = None


class ScimSpecType(F5XCBaseModel):
    scim_client_uri: Optional[str] = None
    scim_enabled: Optional[bool] = None


class UpdateOIDCMappersRequest(F5XCBaseModel):
    """When 3rd party OIDC provider uses non-standard field names, user..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    oidc_mappers: Optional[OIDCMappers] = None


class UpdateScimIntegrationRequest(F5XCBaseModel):
    """Request for updating the SCIM integration status for an OIDC provider."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    scim_enabled: Optional[bool] = None
    scim_token_meta: Optional[RecreateScimTokenRequest] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class CreateResponse(F5XCBaseModel):
    """CreateResponse is the response format for the credential's create request."""

    active: Optional[bool] = None
    data: Optional[str] = None
    expiration_timestamp: Optional[str] = None
    name: Optional[str] = None


class UpdateScimIntegrationResponse(F5XCBaseModel):
    """Response for the SCIM enablement request for an OIDC provider"""

    error: Optional[ErrorType] = None
    scim_enabled: Optional[bool] = None
    scim_token: Optional[CreateResponse] = None
    url: Optional[str] = None


class InitializerType(F5XCBaseModel):
    """Initializer is information about an initializer that has not yet completed."""

    name: Optional[str] = None


class StatusType(F5XCBaseModel):
    """Status is a return value for calls that don't return other objects."""

    code: Optional[int] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class InitializersType(F5XCBaseModel):
    """Initializers tracks the progress of initialization of a configuration object"""

    pending: Optional[list[InitializerType]] = None
    result: Optional[StatusType] = None


class ObjectMetaType(F5XCBaseModel):
    """ObjectMetaType is metadata(common attributes) of an object that all..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ViewRefType(F5XCBaseModel):
    """ViewRefType represents a reference to a view"""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class SystemObjectMetaType(F5XCBaseModel):
    """SystemObjectMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_cookie: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    direct_ref_hash: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    namespace: Optional[list[ObjectRefType]] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    revision: Optional[str] = None
    sre_disable: Optional[bool] = None
    tenant: Optional[str] = None
    trace_info: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class CustomCreateSpecType(F5XCBaseModel):
    """CustomCreateSpecType is the spec to create oidc provider"""

    azure_oidc_spec_type: Optional[AzureOIDCSpecType] = None
    google_oidc_spec_type: Optional[GoogleOIDCSpecType] = None
    oidc_v10_spec_type: Optional[OIDCV10SpecType] = None
    okta_oidc_spec_type: Optional[OKTAOIDCSpecType] = None
    provider_type: Optional[Literal['DEFAULT', 'GOOGLE', 'AZURE', 'OKTA']] = None


class CreateRequest(F5XCBaseModel):
    """Create request shape for creating an OIDC provider in IAM."""

    namespace: Optional[str] = None
    spec: Optional[CustomCreateSpecType] = None


class CreateResponse(F5XCBaseModel):
    """Create response is the response format for the response of request to..."""

    err: Optional[Literal['EUNKNOWN', 'EOK', 'EEXISTS', 'EFAILED', 'ENOTFOUND']] = None
    post_logout_redirect_uri: Optional[str] = None
    redirect_uri: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    """GlobalSpecType has specification field and values about the oidc provider"""

    azure_oidc_spec_type: Optional[AzureOIDCSpecType] = None
    google_oidc_spec_type: Optional[GoogleOIDCSpecType] = None
    oidc_v10_spec_type: Optional[OIDCV10SpecType] = None
    okta_oidc_spec_type: Optional[OKTAOIDCSpecType] = None
    provider_type: Optional[Literal['DEFAULT', 'GOOGLE', 'AZURE', 'OKTA']] = None
    redirect_uri: Optional[str] = None
    scim_spec: Optional[ScimSpecType] = None


class SpecType(F5XCBaseModel):
    """Shape of the oidc provider specification"""

    gc_spec: Optional[GlobalSpecType] = None


class Object(F5XCBaseModel):
    """OIDC Provider object"""

    metadata: Optional[ObjectMetaType] = None
    spec: Optional[SpecType] = None
    system_metadata: Optional[SystemObjectMetaType] = None


class GetResponse(F5XCBaseModel):
    """GetResponse is the response format for fetching oidc provider information"""

    object_: Optional[Object] = Field(default=None, alias="object")


class ListResponseItem(F5XCBaseModel):
    """Shape of the OIDC provider object in a list request's response body."""

    create_timestamp: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    provider_type: Optional[Literal['DEFAULT', 'GOOGLE', 'AZURE', 'OKTA']] = None
    uid: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """Format of the response body to list OIDC providers configured for the..."""

    items: Optional[list[ListResponseItem]] = None


# Convenience aliases
Spec = AzureOIDCSpecType
Spec = GoogleOIDCSpecType
Spec = OIDCV10SpecType
Spec = OKTAOIDCSpecType
Spec = ScimSpecType
Spec = CustomCreateSpecType
Spec = GlobalSpecType
Spec = SpecType
