"""Pydantic models for payment_method."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class GlobalSpecType(F5XCBaseModel):
    """Instance of one single contact that can be used to communicate with..."""

    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    contact_type: Optional[Literal['MAILING', 'BILLING', 'PAYMENT']] = None
    country: Optional[str] = None
    county: Optional[str] = None
    phone_number: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    zip_code: Optional[str] = None


class CreatePaymentMethodRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    contact: Optional[GlobalSpecType] = None
    namespace: Optional[str] = None
    role: Optional[Literal['PAYMENT_METHOD_ROLE_UNKNOWN', 'PAYMENT_METHOD_ROLE_PRIMARY', 'PAYMENT_METHOD_ROLE_SECONDARY', 'PAYMENT_METHOD_ROLE_NORMAL']] = None
    token: Optional[str] = None


class CreatePaymentMethodResponse(F5XCBaseModel):
    name: Optional[str] = None


class PrimaryReq(F5XCBaseModel):
    """Changes a payment method role to primary"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class RoleSwapReq(F5XCBaseModel):
    """Changes a payment method role (from/to primary or backup)"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class SecondaryReq(F5XCBaseModel):
    """Changes a payment method role to secondary"""

    name: Optional[str] = None
    namespace: Optional[str] = None


# Convenience aliases
Spec = GlobalSpecType
