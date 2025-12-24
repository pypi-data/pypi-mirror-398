"""Pydantic models for bfdp."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class EnableFeatureRequest(F5XCBaseModel):
    """Any payload to be passed on the Get Provision API"""

    pass


class EnableFeatureResponse(F5XCBaseModel):
    """Any payload to be passed on the Get Provision API"""

    pass


class RefreshTokenRequest(F5XCBaseModel):
    """API to refresh token for a given pipeline"""

    product_name: Optional[str] = None


class RefreshTokenResponse(F5XCBaseModel):
    """Referesh token result"""

    result: Optional[str] = None


# Convenience aliases
