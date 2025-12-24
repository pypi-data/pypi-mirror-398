"""Pydantic models for maintenance_status."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class GetUpgradeStatusResponse(F5XCBaseModel):
    """Response message for Upgrade Status Request. Response contain different..."""

    upgrade_in_progress: Optional[Any] = None
    upgrade_in_progress_with_config_downtime: Optional[Any] = None
    upgrade_not_in_progress: Optional[Any] = None


# Convenience aliases
