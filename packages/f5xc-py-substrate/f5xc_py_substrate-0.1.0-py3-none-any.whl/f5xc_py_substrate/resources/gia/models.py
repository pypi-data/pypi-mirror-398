"""Pydantic models for gia."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AllocateIPRequest(F5XCBaseModel):
    """This is the input message of the 'AllocateIP' RPC"""

    context: Optional[str] = None
    use_v6_range: Optional[bool] = None


class AllocateIPResponse(F5XCBaseModel):
    """This is the output message of the 'AllocateIP' RPC"""

    error_message: Optional[str] = None
    ip: Optional[str] = None


class DeallocateIPRequest(F5XCBaseModel):
    """This is the input message of the 'DeAllocateIP' RPC."""

    context: Optional[str] = None
    ip: Optional[str] = None


class DeallocateIPResponse(F5XCBaseModel):
    """This is the output message of the 'DeAllocateIP' RPC."""

    message: Optional[str] = None


# Convenience aliases
