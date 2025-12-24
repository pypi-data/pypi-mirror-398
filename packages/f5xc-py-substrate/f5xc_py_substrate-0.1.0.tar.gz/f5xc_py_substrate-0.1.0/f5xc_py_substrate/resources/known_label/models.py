"""Pydantic models for known_label."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class CreateRequest(F5XCBaseModel):
    """Create label request in shared namespace. Only shared namespace supported"""

    description: Optional[str] = None
    key: Optional[str] = None
    namespace: Optional[str] = None
    value: Optional[str] = None


class LabelType(F5XCBaseModel):
    """Generic Label type label.key(label.value)"""

    description: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None


class CreateResponse(F5XCBaseModel):
    """Create Label Response"""

    label: Optional[LabelType] = None


class DeleteRequest(F5XCBaseModel):
    """Deletes Label matching label.key=label.value."""

    key: Optional[str] = None
    namespace: Optional[str] = None
    value: Optional[str] = None


class DeleteResponse(F5XCBaseModel):
    """Response for Delete API"""

    pass


class GetResponse(F5XCBaseModel):
    """Response for Get API"""

    label: Optional[list[LabelType]] = None


# Convenience aliases
