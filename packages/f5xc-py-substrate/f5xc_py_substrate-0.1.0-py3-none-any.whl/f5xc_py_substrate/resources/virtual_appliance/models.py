"""Pydantic models for virtual_appliance."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class GetImageRequest(F5XCBaseModel):
    """Request containing the sw_version"""

    uids: Optional[list[str]] = None


class GetImageResponse(F5XCBaseModel):
    """Response containing the OS image mapping data for the requested software..."""

    images: Optional[dict[str, Any]] = None


# Convenience aliases
