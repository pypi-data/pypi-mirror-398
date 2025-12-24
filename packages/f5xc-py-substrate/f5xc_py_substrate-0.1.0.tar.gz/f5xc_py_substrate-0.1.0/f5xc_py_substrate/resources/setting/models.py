"""Pydantic models for setting."""

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


class InitialAccess(F5XCBaseModel):
    """User console view preferences"""

    email_sent: Optional[bool] = None
    last_requesting_time: Optional[str] = None
    requested: Optional[bool] = None


class Notification(F5XCBaseModel):
    """Definition of existing notifications created for subscription."""

    code: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    label: Optional[str] = None


class NotificationList(F5XCBaseModel):
    """List of notifications"""

    notifications: Optional[list[Notification]] = None


class PersonaPreferences(F5XCBaseModel):
    """Preferences to display appropriate content to appropriate audience"""

    billing: Optional[bool] = None
    dev_ops: Optional[bool] = None
    developer: Optional[bool] = None
    master: Optional[bool] = None
    net_ops: Optional[bool] = None
    sec_ops: Optional[bool] = None


class SetViewPreferenceRequest(F5XCBaseModel):
    """User console view preferences"""

    advanced_view: Optional[bool] = None
    persona_preferences: Optional[PersonaPreferences] = None


class UpdateImageRequest(F5XCBaseModel):
    """Message contains data for updating user profile image."""

    content_type: Optional[str] = None
    image: Optional[str] = None


class UserSession(F5XCBaseModel):
    """UserSession contains information about active user's sessions in IAM."""

    ip_address: Optional[str] = None
    last_access: Optional[str] = None
    start: Optional[str] = None


class UserSessionList(F5XCBaseModel):
    """UserSessionList contains list of user sessions."""

    user_sessions: Optional[list[UserSession]] = None


class UserSettingsRequest(F5XCBaseModel):
    """Allowed settings for the user to be modified."""

    enabled_notifications: Optional[list[str]] = None
    first_name: Optional[str] = None
    image: Optional[str] = None
    last_name: Optional[str] = None
    otp_enabled: Optional[bool] = None


class UserSettingsResponse(F5XCBaseModel):
    """Response of modified user settings."""

    image: Optional[str] = None
    initial_access: Optional[InitialAccess] = None
    is_next_request_allowed: Optional[bool] = None
    notifications: Optional[list[Notification]] = None
    otp_enabled: Optional[bool] = None
    otp_status: Optional[Literal['OTP_DISABLED', 'OTP_ENABLED', 'OTP_PROCESSING', 'OTP_PROCESS_DISABLING']] = None


class ViewPreference(F5XCBaseModel):
    """Preferences to display appropriate content to appropriate audience"""

    advanced_view: Optional[bool] = None
    initialized: Optional[bool] = None
    persona_preferences: Optional[PersonaPreferences] = None


class Empty(F5XCBaseModel):
    """Empty object definition."""

    pass


# Convenience aliases
