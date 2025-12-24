"""Pydantic models for user_token."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class GetUserTokenResponse(F5XCBaseModel):
    """Response body of token to connect to the Web App Scanning Service"""

    redirect_url: Optional[str] = None
    token: Optional[str] = None
    user_id: Optional[str] = None


# Convenience aliases
