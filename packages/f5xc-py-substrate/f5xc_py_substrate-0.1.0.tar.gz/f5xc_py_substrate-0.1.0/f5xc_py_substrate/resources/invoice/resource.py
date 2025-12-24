"""Invoice resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.invoice.models import (
    DownloadInvoicePdfRsp,
    InvoiceType,
    ListInvoicesRsp,
)


# Exclusion group mappings for get() method
_EXCLUDE_GROUPS: dict[str, set[str]] = {
    "forms": {"create_form", "replace_form"},
    "references": {"referring_objects", "deleted_referred_objects", "disabled_referred_objects"},
    "system_metadata": {"system_metadata"},
}


def _resolve_exclude_groups(groups: list[str]) -> set[str]:
    """Resolve exclusion group names to field names."""
    fields: set[str] = set()
    for group in groups:
        if group in _EXCLUDE_GROUPS:
            fields.update(_EXCLUDE_GROUPS[group])
        else:
            # Allow direct field names for flexibility
            fields.add(group)
    return fields


class InvoiceResource:
    """API methods for invoice.

    Invoice listing and downloading APIs
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.invoice.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def download_invoice_pdf(
        self,
        namespace: str,
        name: str | None = None,
    ) -> DownloadInvoicePdfRsp:
        """Download Invoice Pdf for invoice.

        Retrieve pdf for a paid invoice by its name
        """
        path = "/api/web/namespaces/{namespace}/usage/invoice_pdf"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DownloadInvoicePdfRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("invoice", "download_invoice_pdf", e, response) from e

    def list_invoices(
        self,
        namespace: str,
        limit: int | None = None,
    ) -> ListInvoicesRsp:
        """List Invoices for invoice.

        Endpoint to list customer invoices
        """
        path = "/api/web/namespaces/{namespace}/usage/invoices/custom_list"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListInvoicesRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("invoice", "list_invoices", e, response) from e

