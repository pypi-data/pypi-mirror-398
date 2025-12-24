"""Pydantic models for catalog."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class CatalogListItem(F5XCBaseModel):
    """List item for catalog resources."""


class ListRequest(F5XCBaseModel):
    """List request message. Includes optional filter."""

    use_case_filter: Optional[str] = None
    workspace_filter: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """Response message for list request."""

    addon_services: Optional[dict[str, Any]] = None
    services: Optional[dict[str, Any]] = None
    system_management: Optional[dict[str, Any]] = None
    use_cases: Optional[dict[str, Any]] = None
    workspaces: Optional[dict[str, Any]] = None


# Convenience aliases
