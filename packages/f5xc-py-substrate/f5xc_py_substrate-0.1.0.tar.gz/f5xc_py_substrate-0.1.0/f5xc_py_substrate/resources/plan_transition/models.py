"""Pydantic models for plan_transition."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class GetPlanTransitionRsp(F5XCBaseModel):
    """Request body of GetPlanTransition custom api"""

    state: Optional[Literal['STATE_UNSPECIFIED', 'STATE_CREATING', 'STATE_FAILED', 'STATE_FINISHED', 'STATE_WAITING_FOR_APPROVAL']] = None


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


class TransitionPayload(F5XCBaseModel):
    """Payload which is required to execute transition from the current..."""

    billing_address: Optional[GlobalSpecType] = None
    billing_provider_account_id: Optional[str] = None
    create_support_ticket: Optional[bool] = None
    deletion_feedback: Optional[str] = None
    deletion_reason: Optional[Literal['REASON_UNKNOWN', 'REASON_SWITCH_TO_FREE_PLAN', 'REASON_NO_LONGER_NEEDED', 'REASON_NOT_JUSTIFY_COSTS', 'REASON_DIFFICULT_TO_USE']] = None
    domain: Optional[str] = None
    payment_address: Optional[GlobalSpecType] = None
    payment_provider_token: Optional[str] = None
    subscribe_addon_services: Optional[list[str]] = None
    support_ticket_info: Optional[str] = None
    tp_subscription_id: Optional[str] = None
    unsubscribe_addon_services: Optional[list[str]] = None


class InitiatePlanTransitionReq(F5XCBaseModel):
    """Request body of InitiatePlanTransition custom api"""

    namespace: Optional[str] = None
    new_plan: Optional[str] = None
    payload: Optional[TransitionPayload] = None


class InitiatePlanTransitionRsp(F5XCBaseModel):
    """Response body of InitiatePlanTransition custom api"""

    id_: Optional[str] = Field(default=None, alias="id")
    requires_manual_approval: Optional[bool] = None


# Convenience aliases
Spec = GlobalSpecType
