"""Pydantic models for invoice."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class DownloadInvoicePdfRsp(F5XCBaseModel):
    """Response for GetInvoicePdf rpc method"""

    pdf: Optional[str] = None


class InvoiceType(F5XCBaseModel):
    """A single invoice representation"""

    active: Optional[bool] = None
    amount: Optional[str] = None
    currency: Optional[str] = None
    name: Optional[str] = None
    period_end: Optional[str] = None
    period_start: Optional[str] = None
    status: Optional[Literal['STATUS_UNKNOWN', 'STATUS_ISSUED', 'STATUS_PENDING', 'STATUS_PAID', 'STATUS_REFUNDED', 'STATUS_CANCELLED', 'OVERDUE']] = None


class ListInvoicesRsp(F5XCBaseModel):
    """Response to list customer's invoices"""

    invoices: Optional[list[InvoiceType]] = None


# Convenience aliases
