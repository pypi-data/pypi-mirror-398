"""Pydantic models for known_label_key."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class CreateRequest(F5XCBaseModel):
    """Create label Key request in shared namespace. Only shared namespace supported"""

    description: Optional[str] = None
    key: Optional[str] = None
    namespace: Optional[str] = None


class LabelKeyType(F5XCBaseModel):
    """Generic Label key type label.key"""

    description: Optional[str] = None
    key: Optional[str] = None


class CreateResponse(F5XCBaseModel):
    """Create Label Response"""

    label_key: Optional[LabelKeyType] = None


class DeleteRequest(F5XCBaseModel):
    """Deletes Label key matching label.key."""

    key: Optional[str] = None
    namespace: Optional[str] = None


class DeleteResponse(F5XCBaseModel):
    """Response for Delete API"""

    pass


class GetResponse(F5XCBaseModel):
    """Response for Get API"""

    label_key: Optional[list[LabelKeyType]] = None


# Convenience aliases
