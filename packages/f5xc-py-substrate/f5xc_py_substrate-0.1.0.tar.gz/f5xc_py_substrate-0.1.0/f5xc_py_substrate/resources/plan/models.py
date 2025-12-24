"""Pydantic models for plan."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AddonServiceDetails(F5XCBaseModel):
    """Details about addon service"""

    display_name: Optional[str] = None
    name: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    """GlobalSpecType defines the shape of the object in database as present in..."""

    api_limits: Optional[dict[str, Any]] = None
    apigw_limits: Optional[dict[str, Any]] = None
    object_limits: Optional[dict[str, Any]] = None
    resource_limits: Optional[dict[str, Any]] = None


class UsagePlanTransitionFlow(F5XCBaseModel):
    """Details for transition flow. Is used as part of UsagePlanInternal"""

    method: Optional[Literal['TRANSITION_METHOD_UNSPECIFIED', 'TRANSITION_METHOD_SUPPORT', 'TRANSITION_METHOD_WIZARD', 'TRANSITION_METHOD_RECREATE']] = None
    required_fields: Optional[list[Literal['TRANSITION_REQUIRED_FIELD_UNSPECIFIED', 'TRANSITION_REQUIRED_FIELD_PAYMENT_TOKEN', 'TRANSITION_REQUIRED_FIELD_DOMAIN', 'TRANSITION_REQUIRED_FIELD_CONTACTS']]] = None
    requires_manual_approval: Optional[bool] = None


class Internal(F5XCBaseModel):
    """Structure that holds all data needed to choose usage plan"""

    allowed_addon_services: Optional[list[AddonServiceDetails]] = None
    billing_disabled: Optional[bool] = None
    current: Optional[bool] = None
    default_quota: Optional[GlobalSpecType] = None
    description: Optional[str] = None
    flat_price: Optional[int] = None
    included_addon_services: Optional[list[AddonServiceDetails]] = None
    name: Optional[str] = None
    renewal_period_unit: Optional[Literal['PERIOD_UNKNOWN', 'PERIOD_DAY', 'PERIOD_WEEK', 'PERIOD_MONTH', 'PERIOD_YEAR']] = None
    state: Optional[Literal['STATE_UNSPECIFIED', 'STATE_READY', 'STATE_TRANSITION_PENDING']] = None
    subtitle: Optional[str] = None
    tenant_type: Optional[Literal['UNKNOWN', 'FREEMIUM', 'ENTERPRISE']] = None
    title: Optional[str] = None
    transition_flow: Optional[UsagePlanTransitionFlow] = None
    trial_period: Optional[int] = None
    trial_period_unit: Optional[Literal['PERIOD_UNKNOWN', 'PERIOD_DAY', 'PERIOD_WEEK', 'PERIOD_MONTH', 'PERIOD_YEAR']] = None
    usage_plan_type: Optional[Literal['FREE', 'INDIVIDUAL', 'TEAM', 'ORGANIZATION', 'PLAN_TYPE_UNSPECIFIED']] = None


class LocalizedPlan(F5XCBaseModel):
    """Localized info of usage plan"""

    locale: Optional[str] = None
    plans: Optional[list[Internal]] = None


class ListUsagePlansRsp(F5XCBaseModel):
    """Response with the usage plans info"""

    usage_plans: Optional[list[LocalizedPlan]] = None


# Convenience aliases
Spec = GlobalSpecType
