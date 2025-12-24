"""Tcpdump resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.tcpdump.models import (
    ProtobufAny,
    HttpBody,
    ErrorType,
    InterfaceOrNetwork,
    InterfaceTcpdumpStatus,
    ListRequest,
    ListResponse,
    StopResponse,
    Request,
    Response,
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


class TcpdumpResource:
    """API methods for tcpdump.

    Proto definitions for tcpdump diagnostic
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.tcpdump.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def fetch_dump(
        self,
        namespace: str,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> HttpBody:
        """Fetch Dump for tcpdump.

        Fetch the captured pcap data from an earlier Tcpdump request
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/ver/fetchdump"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("tcpdump", "fetch_dump", e, response) from e

    def list_tcpdump(
        self,
        namespace: str,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> ListResponse:
        """List Tcpdump for tcpdump.

        List tcpdump capture status on a ver node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/ver/list_tcpdump"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tcpdump", "list_tcpdump", e, response) from e

    def stop_tcpdump(
        self,
        namespace: str,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> StopResponse:
        """Stop Tcpdump for tcpdump.

        Stop tcpdump running on an interface in a ver node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/ver/stop_tcpdump"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StopResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("tcpdump", "stop_tcpdump", e, response) from e

    def tcpdump(
        self,
        namespace: str,
        site: str,
        body: dict[str, Any] | None = None,
    ) -> Response:
        """Tcpdump for tcpdump.

        Run tcpdump on an interface in a ver node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/ver/tcpdump"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("tcpdump", "tcpdump", e, response) from e

