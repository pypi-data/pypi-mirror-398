"""Pydantic models for waf_signatures_changelog."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ReleaseSignatures(F5XCBaseModel):
    added_signature_ids: Optional[list[str]] = None
    release_date: Optional[str] = None
    updated_signature_ids: Optional[list[str]] = None


class ReleasedSignaturesRsp(F5XCBaseModel):
    """Response to get the list of released signatures"""

    release_signatures: Optional[list[ReleaseSignatures]] = None


class StagedSignature(F5XCBaseModel):
    """Staged signature details"""

    accuracy: Optional[str] = None
    attack_type: Optional[str] = None
    context: Optional[str] = None
    count: Optional[int] = None
    id_: Optional[str] = Field(default=None, alias="id")
    id_name: Optional[str] = None
    matching_info: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None


class StagedSignaturesReq(F5XCBaseModel):
    """Request to get the list of all staged signatures"""

    end_time: Optional[str] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None
    vh_name: Optional[str] = None


class StagedSignaturesRsp(F5XCBaseModel):
    """Response to get the list of all staged signatures"""

    staged_signatures: Optional[list[StagedSignature]] = None


# Convenience aliases
