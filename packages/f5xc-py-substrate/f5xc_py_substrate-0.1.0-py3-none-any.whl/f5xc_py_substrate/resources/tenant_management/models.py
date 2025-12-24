"""Pydantic models for tenant_management."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class SubscribeRequest(F5XCBaseModel):
    """Request to subscribe to Tenant Management Service"""

    pass


class SubscribeResponse(F5XCBaseModel):
    """Response of subscribe to Tenant Management Service"""

    pass


class UnsubscribeRequest(F5XCBaseModel):
    """Request to unsubscribe to Tenant Management Service"""

    pass


class UnsubscribeResponse(F5XCBaseModel):
    """Response of unsubscribe to Tenant Management Service"""

    pass


# Convenience aliases
