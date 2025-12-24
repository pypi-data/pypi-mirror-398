"""Pydantic models for xc_saas."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class GetRegistrationDetailsResponse(F5XCBaseModel):
    """Response format for returning registration details associated with the..."""

    console_url: Optional[str] = None
    domain: Optional[str] = None
    email: Optional[str] = None
    error_message: Optional[str] = None


class SendEmailResponse(F5XCBaseModel):
    """Response to indicate if the email was sent successfully"""

    message: Optional[str] = None
    success: Optional[bool] = None


class SendSignupEmailRequest(F5XCBaseModel):
    """The request message for SendSignupEmail"""

    token: Optional[str] = None


class XCSaaSSignupRequest(F5XCBaseModel):
    domain: Optional[str] = None
    token: Optional[str] = None


class XCSaaSSignupResponse(F5XCBaseModel):
    pass


# Convenience aliases
