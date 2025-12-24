"""Pydantic models for crl."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ResyncCRLRequest(F5XCBaseModel):
    """Request to trigger resync of CRL in VER"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    site: Optional[str] = None
    uid: Optional[str] = None


class ResyncCRLResponse(F5XCBaseModel):
    """Response for Resync CRL Request"""

    status: Optional[str] = None


# Convenience aliases
