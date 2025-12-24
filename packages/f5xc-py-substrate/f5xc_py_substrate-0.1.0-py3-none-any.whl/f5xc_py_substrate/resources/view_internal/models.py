"""Pydantic models for view_internal."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ViewRefType(F5XCBaseModel):
    """ViewRefType represents a reference to a view"""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    """Shape of the view internal specification"""

    allocation_map: Optional[dict[str, Any]] = Field(default=None, alias="allocationMap")
    child_objects: Optional[list[ViewRefType]] = None
    view: Optional[ViewRefType] = None


class GetResponse(F5XCBaseModel):
    """Response for Get API"""

    view_internal: Optional[GlobalSpecType] = None


# Convenience aliases
Spec = GlobalSpecType
