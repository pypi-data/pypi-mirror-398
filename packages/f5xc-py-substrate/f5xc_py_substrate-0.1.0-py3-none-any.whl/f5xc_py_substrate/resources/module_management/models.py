"""Pydantic models for module_management."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class Response(F5XCBaseModel):
    """Defines settings for module control."""

    glr_configuration: Optional[Literal['MM_NONE', 'ALLOWED', 'NOT_ALLOWED']] = None


# Convenience aliases
