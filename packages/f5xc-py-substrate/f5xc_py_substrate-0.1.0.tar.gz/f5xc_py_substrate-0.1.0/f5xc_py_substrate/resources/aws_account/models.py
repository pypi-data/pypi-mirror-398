"""Pydantic models for aws_account."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AccountMeta(F5XCBaseModel):
    domain: Optional[str] = None
    locale: Optional[str] = None
    tos_accepted_at: Optional[str] = None
    tos_version: Optional[str] = None


class ContactMeta(F5XCBaseModel):
    """Instance of one single contact that can be used to communicate with..."""

    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    county: Optional[str] = None
    phone_number: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    zip_code: Optional[str] = None


class CompanyMeta(F5XCBaseModel):
    mailing_address: Optional[ContactMeta] = None
    name: Optional[str] = None


class CRMInfo(F5XCBaseModel):
    """CRM Information"""

    pass


class UserMeta(F5XCBaseModel):
    contact_number: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class AWSAccountSignupRequest(F5XCBaseModel):
    account_details: Optional[AccountMeta] = None
    account_id: Optional[str] = None
    company_details: Optional[CompanyMeta] = None
    crm_details: Optional[Any] = None
    user_details: Optional[UserMeta] = None


class AWSAccountSignupResponse(F5XCBaseModel):
    pass


class RegistrationRequest(F5XCBaseModel):
    """Request to register F5XC AWS marketplace product for F5XC service."""

    x_amzn_marketplace_token: Optional[str] = None


class RegistrationResponse(F5XCBaseModel):
    """Response to register F5XC AWS marketplace product"""

    redirect_url: Optional[str] = None


# Convenience aliases
