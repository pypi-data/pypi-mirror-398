"""Pydantic models for tenant."""

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


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class AssignDomainOwnerRequest(F5XCBaseModel):
    """Domain owner assignment request"""

    email: Optional[str] = None


class CredentialsExpiry(F5XCBaseModel):
    """CredentialsExpiry is a struct that holds max expiration days setting for..."""

    max_api_certificate_expiry_days: Optional[int] = None
    max_api_token_expiry_days: Optional[int] = None
    max_kube_config_expiry_days: Optional[int] = None


class DeactivateTenantRequest(F5XCBaseModel):
    """Request to deactivate the tenant."""

    feedback: Optional[str] = None
    reason: Optional[Literal['REASON_UNKNOWN', 'REASON_SWITCH_TO_FREE_PLAN', 'REASON_NO_LONGER_NEEDED', 'REASON_NOT_JUSTIFY_COSTS', 'REASON_DIFFICULT_TO_USE']] = None


class DeactivateTenantResponse(F5XCBaseModel):
    job_id: Optional[str] = None


class DeleteTenantRequest(F5XCBaseModel):
    """Request for marking Tenant for deletion."""

    email: Optional[str] = None
    feedback: Optional[str] = None
    name: Optional[str] = None
    reason: Optional[Literal['REASON_UNKNOWN', 'REASON_SWITCH_TO_FREE_PLAN', 'REASON_NO_LONGER_NEEDED', 'REASON_NOT_JUSTIFY_COSTS', 'REASON_DIFFICULT_TO_USE']] = None


class GetLoginEventsInTimeFrameRequest(F5XCBaseModel):
    """Contains fields to retrieve events in timeframe"""

    end: Optional[str] = None
    first: Optional[int] = None
    max: Optional[int] = None
    start: Optional[str] = None


class LastLoginMap(F5XCBaseModel):
    """Last login map"""

    last_login_map: Optional[dict[str, Any]] = None


class LoginEventsMap(F5XCBaseModel):
    """LoginEventsMap is a map from username to list of login events. In can be..."""

    login_events_map: Optional[dict[str, Any]] = None


class PasswordPolicyPublicAccess(F5XCBaseModel):
    """PasswordPolicyPublicAccess contains subset of password policy settings...."""

    digits: Optional[int] = None
    lowercase_characters: Optional[int] = None
    minimum_length: Optional[int] = None
    not_recently_used: Optional[int] = None
    not_username: Optional[bool] = None
    special_characters: Optional[int] = None
    uppercase_characters: Optional[int] = None


class StatusResponse(F5XCBaseModel):
    """LookupCnameResponse sets the response format based on the availability..."""

    pass


class SummaryResponse(F5XCBaseModel):
    """Tenant Summary Response"""

    type_: Optional[str] = Field(default=None, alias="type")
    vip: Optional[str] = None


class SupportInfo(F5XCBaseModel):
    """Support Info contains support information for tenant"""

    support_email_address: Optional[str] = None


class SettingsResponse(F5XCBaseModel):
    """Defines tenant specific settings."""

    active_plan_transition_id: Optional[str] = None
    company_name: Optional[str] = None
    domain: Optional[str] = None
    max_credentials_expiry: Optional[CredentialsExpiry] = None
    name: Optional[str] = None
    original_tenant: Optional[str] = None
    otp_enabled: Optional[bool] = None
    otp_status: Optional[Literal['OTP_DISABLED', 'OTP_ENABLED', 'OTP_PROCESSING', 'OTP_PROCESS_DISABLING']] = None
    scim_enabled: Optional[bool] = None
    sso_enabled: Optional[bool] = None
    state: Optional[Literal['StateUndefined', 'StateCreating', 'StateCreateFailed', 'StateInactive', 'StateActive', 'StateSuspended', 'StateDisabled', 'StateConfiguring', 'StateConfiguringFailed']] = None


class UnassignDomainOwnerRequest(F5XCBaseModel):
    """Domain owner assignment request"""

    email: Optional[str] = None


class UpdateImageRequest(F5XCBaseModel):
    """Update user image request"""

    content_type: Optional[str] = None
    image: Optional[str] = None


class UpdateTenantSettingsRequest(F5XCBaseModel):
    """Request to update tenant settings for specific tenant."""

    max_credentials_expiry: Optional[CredentialsExpiry] = None
    otp_enabled: Optional[bool] = None


class ValidationErrorField(F5XCBaseModel):
    """Contains information on a single validation error"""

    error_field: Optional[str] = None
    error_message: Optional[str] = None


class UpdateTenantSettingsResponse(F5XCBaseModel):
    """Defines tenant specific settings."""

    max_credentials_expiry: Optional[CredentialsExpiry] = None
    otp_enabled: Optional[bool] = None
    otp_status: Optional[Literal['OTP_DISABLED', 'OTP_ENABLED', 'OTP_PROCESSING', 'OTP_PROCESS_DISABLING']] = None
    scim_enabled: Optional[bool] = None
    sso_enabled: Optional[bool] = None
    validation_errors: Optional[list[ValidationErrorField]] = None


class User(F5XCBaseModel):
    """Login user representation. Currently users are identified by their email."""

    email: Optional[str] = None


class UserList(F5XCBaseModel):
    """Collection of users"""

    users: Optional[list[User]] = None


class BasicConfiguration(F5XCBaseModel):
    display_name: Optional[str] = None


class BruteForceDetectionSettings(F5XCBaseModel):
    max_login_failures: Optional[int] = None


class PasswordPolicy(F5XCBaseModel):
    digits: Optional[int] = None
    expire_password: Optional[int] = None
    lowercase_characters: Optional[int] = None
    minimum_length: Optional[int] = None
    not_recently_used: Optional[int] = None
    not_username: Optional[bool] = None
    special_characters: Optional[int] = None
    uppercase_characters: Optional[int] = None


class GlobalSpecType(F5XCBaseModel):
    """Shape of the tenant configuration specification"""

    basic_configuration: Optional[BasicConfiguration] = None
    brute_force_detection_settings: Optional[BruteForceDetectionSettings] = None
    password_policy: Optional[PasswordPolicy] = None


# Convenience aliases
Spec = GlobalSpecType
