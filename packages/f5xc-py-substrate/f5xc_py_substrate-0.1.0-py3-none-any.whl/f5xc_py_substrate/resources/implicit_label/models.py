"""Pydantic models for implicit_label."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class LabelType(F5XCBaseModel):
    """Generic Label type label.key(label.value)"""

    description: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None


class GetResponse(F5XCBaseModel):
    """Get Label Response, list of labels"""

    label: Optional[list[LabelType]] = None


# Convenience aliases
