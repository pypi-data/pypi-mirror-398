"""Pydantic models for usage."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class CalculatedUsageItem(F5XCBaseModel):
    """One line of usage, including pricing details"""

    amount: Optional[str] = None
    currency_code: Optional[str] = None
    end_timestamp: Optional[str] = None
    fixed: Optional[bool] = None
    metric_labels: Optional[list[str]] = None
    quantity: Optional[float] = None
    quantity_billable: Optional[str] = None
    start_timestamp: Optional[str] = None
    status: Optional[Literal['STATUS_UNKNOWN', 'STATUS_NO_DATA', 'STATUS_NOT_MEASURED', 'STATUS_ACTIVE']] = None
    unit_name: Optional[str] = None
    unit_name_billable: Optional[str] = None
    usage_type: Optional[str] = None


class Coupon(F5XCBaseModel):
    """Coupon details, discount type, amount and name"""

    discount_amount: Optional[int] = None
    discount_type: Optional[Literal['DISCOUNT_TYPE_UNKNOWN', 'DISCOUNT_TYPE_FIXED_AMOUNT', 'DISCOUNT_TYPE_PERCENTAGE']] = None
    title: Optional[str] = None


class HourlyItem(F5XCBaseModel):
    """One line of usage by an hour. One hour as the least resolution."""

    container: Optional[str] = None
    deployment: Optional[str] = None
    end_timestamp: Optional[str] = None
    quantity: Optional[float] = None
    start_timestamp: Optional[str] = None
    unit_name: Optional[str] = None


class ListCurrentUsageReq(F5XCBaseModel):
    """Request message to get current usage details"""

    from_: Optional[str] = Field(default=None, alias="from")
    namespace: Optional[str] = None
    to: Optional[str] = None


class ListCurrentUsageResp(F5XCBaseModel):
    """Response message to get current usage details"""

    coupons: Optional[list[Coupon]] = None
    discount: Optional[str] = None
    total_cost: Optional[str] = None
    usage_items: Optional[list[CalculatedUsageItem]] = None


class ListHourlyUsageDetailsReq(F5XCBaseModel):
    """Request body for ListHourlyUsageDetails rpc method"""

    namespace: Optional[str] = None
    query: Optional[str] = None


class ListHourlyUsageDetailsResp(F5XCBaseModel):
    """Response body for ListHourlyUsageDetails rpc method"""

    hourly_usage_items: Optional[list[HourlyItem]] = None


class ListMonthlyUsageReq(F5XCBaseModel):
    """Request message to get mon thly usage details"""

    namespace: Optional[str] = None


class MonthlyUsageType(F5XCBaseModel):
    """One line of usage, including pricing details"""

    amount: Optional[str] = None
    currency_code: Optional[str] = None
    end_timestamp: Optional[str] = None
    start_timestamp: Optional[str] = None


class ListMonthlyUsageResp(F5XCBaseModel):
    """Response message to get monthly usage details"""

    monthly_usage_items: Optional[list[MonthlyUsageType]] = None


class ListUsageDetailsReq(F5XCBaseModel):
    """Request message to get usage details"""

    from_: Optional[str] = Field(default=None, alias="from")
    namespace: Optional[str] = None
    to: Optional[str] = None


class Item(F5XCBaseModel):
    """Usage item represents a line in a usage report, including quantity and..."""

    end_timestamp: Optional[str] = None
    hourly_breakdown: Optional[list[HourlyItem]] = None
    hourly_breakdown_query: Optional[str] = None
    metric_label: Optional[str] = None
    namespace: Optional[str] = None
    object_name: Optional[str] = None
    quantity: Optional[float] = None
    start_timestamp: Optional[str] = None
    unit_name: Optional[str] = None
    usage_type: Optional[str] = None


class ListUsageDetailsResp(F5XCBaseModel):
    """Response message to get usage details"""

    usage_items: Optional[list[Item]] = None


# Convenience aliases
